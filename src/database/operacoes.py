"""Operações de banco: cadastro/login, histórico, favoritos, checklists, preferências.

Todas as consultas usam parâmetros (`?`), nunca texto concatenado, e todas as
operações sobre dados do usuário filtram por `usuario_id`, para que um usuário
nunca enxergue ou altere dados de outro.
"""
import sqlite3
from datetime import datetime

from utils.seguranca import gerar_hash, verificar_senha
from utils.validacao import validar_email, validar_nome, validar_senha


class ErroDados(Exception):
    """Erro de regra de negócio com mensagem pronta para o usuário."""


class ErroValidacao(ErroDados):
    def __init__(self, erros):
        self.erros = list(erros)
        super().__init__(" ".join(self.erros))


class UsuarioDuplicado(ErroDados):
    pass


class CredenciaisInvalidas(ErroDados):
    pass


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _dict(linha):
    return dict(linha) if linha is not None else None


CAMPOS_PREFERENCIAS = {"fonte_escala", "alto_contraste", "usar_ia", "template_padrao"}


class Repositorio:
    def __init__(self, conexao: sqlite3.Connection):
        self.c = conexao

    # --- usuários -------------------------------------------------------
    def cadastrar_usuario(self, nome: str, email: str, senha: str) -> int:
        erros = validar_nome(nome) + validar_email(email) + validar_senha(senha)
        if erros:
            raise ErroValidacao(erros)
        try:
            cur = self.c.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                (nome.strip(), email.strip().lower(), gerar_hash(senha), _agora()),
            )
        except sqlite3.IntegrityError:
            raise UsuarioDuplicado("Já existe uma conta com esse e-mail. Tente entrar.") from None
        usuario_id = cur.lastrowid
        self.c.execute("INSERT INTO preferencias (usuario_id) VALUES (?)", (usuario_id,))
        self.c.commit()
        return usuario_id

    def autenticar(self, email: str, senha: str) -> dict:
        linha = self.c.execute(
            "SELECT * FROM usuarios WHERE email = ?", ((email or "").strip().lower(),)
        ).fetchone()
        if linha is None or not verificar_senha(senha or "", linha["senha_hash"]):
            raise CredenciaisInvalidas("E-mail ou senha incorretos.")
        usuario = dict(linha)
        usuario.pop("senha_hash")
        return usuario

    def alterar_nome(self, usuario_id: int, novo_nome: str) -> None:
        erros = validar_nome(novo_nome)
        if erros:
            raise ErroValidacao(erros)
        self.c.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (novo_nome.strip(), usuario_id))
        self.c.commit()

    def alterar_senha(self, usuario_id: int, senha_atual: str, nova_senha: str) -> None:
        linha = self.c.execute("SELECT senha_hash FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        if linha is None or not verificar_senha(senha_atual or "", linha["senha_hash"]):
            raise CredenciaisInvalidas("A senha atual está incorreta.")
        erros = validar_senha(nova_senha)
        if erros:
            raise ErroValidacao(erros)
        self.c.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (gerar_hash(nova_senha), usuario_id))
        self.c.commit()

    def excluir_conta(self, usuario_id: int) -> None:
        """Apaga o usuário e, em cascata, todos os dados dele."""
        self.c.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        self.c.commit()

    # --- preferências ---------------------------------------------------
    def obter_preferencias(self, usuario_id: int) -> dict:
        linha = self.c.execute("SELECT * FROM preferencias WHERE usuario_id = ?", (usuario_id,)).fetchone()
        if linha is None:
            self.c.execute("INSERT OR IGNORE INTO preferencias (usuario_id) VALUES (?)", (usuario_id,))
            self.c.commit()
            linha = self.c.execute("SELECT * FROM preferencias WHERE usuario_id = ?", (usuario_id,)).fetchone()
        return dict(linha)

    def salvar_preferencias(self, usuario_id: int, **campos) -> None:
        campos = {k: v for k, v in campos.items() if k in CAMPOS_PREFERENCIAS}
        if not campos:
            return
        self.obter_preferencias(usuario_id)
        colunas = ", ".join(f"{k} = ?" for k in campos)  # nomes vêm da lista fixa acima
        self.c.execute(f"UPDATE preferencias SET {colunas} WHERE usuario_id = ?", (*campos.values(), usuario_id))
        self.c.commit()

    # --- histórico ------------------------------------------------------
    def registrar_historico(self, usuario_id, pergunta, resposta, status, template, ids_conhecimento=(), usou_ia=False) -> int:
        cur = self.c.execute(
            "INSERT INTO historico (usuario_id, pergunta, resposta, status, template, ids_conhecimento, usou_ia, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (usuario_id, pergunta, resposta, status, template, ",".join(ids_conhecimento), int(usou_ia), _agora()),
        )
        self.c.commit()
        return cur.lastrowid

    def listar_historico(self, usuario_id: int, limite: int = 200, termo: str = "") -> list:
        sql = "SELECT * FROM historico WHERE usuario_id = ?"
        params = [usuario_id]
        if termo.strip():
            sql += " AND pergunta LIKE ?"
            params.append(f"%{termo.strip()}%")
        sql += " ORDER BY criado_em DESC, id DESC LIMIT ?"
        params.append(limite)
        return [dict(l) for l in self.c.execute(sql, params).fetchall()]

    def obter_historico(self, usuario_id: int, item_id: int):
        return _dict(self.c.execute(
            "SELECT * FROM historico WHERE id = ? AND usuario_id = ?", (item_id, usuario_id)).fetchone())

    def excluir_historico(self, usuario_id: int, item_id: int) -> bool:
        cur = self.c.execute("DELETE FROM historico WHERE id = ? AND usuario_id = ?", (item_id, usuario_id))
        self.c.commit()
        return cur.rowcount > 0

    def limpar_historico(self, usuario_id: int) -> int:
        cur = self.c.execute("DELETE FROM historico WHERE usuario_id = ?", (usuario_id,))
        self.c.commit()
        return cur.rowcount

    def contar_perguntas(self, usuario_id: int) -> int:
        return self.c.execute("SELECT COUNT(*) FROM historico WHERE usuario_id = ?", (usuario_id,)).fetchone()[0]

    def ids_do_historico(self, usuario_id: int, limite: int = 30) -> list:
        """IDs de conhecimento já consultados (mais recentes primeiro, sem repetir)."""
        ids = []
        for linha in self.c.execute(
            "SELECT ids_conhecimento FROM historico WHERE usuario_id = ? AND ids_conhecimento != ''"
            " ORDER BY criado_em DESC, id DESC LIMIT ?", (usuario_id, limite)):
            for cid in linha["ids_conhecimento"].split(","):
                if cid and cid not in ids:
                    ids.append(cid)
        return ids

    # --- favoritos ------------------------------------------------------
    def adicionar_favorito(self, usuario_id: int, conhecimento_id: str) -> bool:
        cur = self.c.execute(
            "INSERT OR IGNORE INTO favoritos (usuario_id, conhecimento_id, criado_em) VALUES (?, ?, ?)",
            (usuario_id, conhecimento_id, _agora()))
        self.c.commit()
        return cur.rowcount > 0

    def remover_favorito(self, usuario_id: int, conhecimento_id: str) -> bool:
        cur = self.c.execute(
            "DELETE FROM favoritos WHERE usuario_id = ? AND conhecimento_id = ?", (usuario_id, conhecimento_id))
        self.c.commit()
        return cur.rowcount > 0

    def eh_favorito(self, usuario_id: int, conhecimento_id: str) -> bool:
        return self.c.execute(
            "SELECT 1 FROM favoritos WHERE usuario_id = ? AND conhecimento_id = ?",
            (usuario_id, conhecimento_id)).fetchone() is not None

    def alternar_favorito(self, usuario_id: int, conhecimento_id: str) -> bool:
        """Liga/desliga. Devolve True se ficou favoritado."""
        if self.eh_favorito(usuario_id, conhecimento_id):
            self.remover_favorito(usuario_id, conhecimento_id)
            return False
        self.adicionar_favorito(usuario_id, conhecimento_id)
        return True

    def listar_favoritos(self, usuario_id: int) -> list:
        """IDs de conhecimento favoritados, do mais recente para o mais antigo."""
        return [l["conhecimento_id"] for l in self.c.execute(
            "SELECT conhecimento_id FROM favoritos WHERE usuario_id = ? ORDER BY criado_em DESC, id DESC",
            (usuario_id,))]

    # --- checklists -----------------------------------------------------
    def garantir_checklists(self, usuario_id: int, modelos: list) -> None:
        """Cria para o usuário as checklists dos modelos que ele ainda não tem."""
        for modelo in modelos:
            existe = self.c.execute(
                "SELECT 1 FROM checklists WHERE usuario_id = ? AND modelo_id = ?",
                (usuario_id, modelo["id"])).fetchone()
            if existe:
                continue
            cur = self.c.execute(
                "INSERT INTO checklists (usuario_id, modelo_id, titulo, criado_em) VALUES (?, ?, ?, ?)",
                (usuario_id, modelo["id"], modelo["titulo"], _agora()))
            for ordem, tarefa in enumerate(modelo["tarefas"], start=1):
                self.c.execute(
                    "INSERT INTO tarefas_checklist (checklist_id, ordem, descricao, conhecimento_id) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, ordem, tarefa["descricao"], tarefa.get("conhecimento_id")))
        self.c.commit()

    def listar_checklists(self, usuario_id: int) -> list:
        linhas = self.c.execute(
            "SELECT c.id, c.modelo_id, c.titulo,"
            " COUNT(t.id) AS total, COALESCE(SUM(t.concluida), 0) AS concluidas"
            " FROM checklists c LEFT JOIN tarefas_checklist t ON t.checklist_id = c.id"
            " WHERE c.usuario_id = ? GROUP BY c.id ORDER BY c.id", (usuario_id,)).fetchall()
        return [dict(l) for l in linhas]

    def listar_tarefas(self, usuario_id: int, checklist_id: int) -> list:
        linhas = self.c.execute(
            "SELECT t.* FROM tarefas_checklist t JOIN checklists c ON c.id = t.checklist_id"
            " WHERE c.id = ? AND c.usuario_id = ? ORDER BY t.ordem", (checklist_id, usuario_id)).fetchall()
        return [dict(l) for l in linhas]

    def marcar_tarefa(self, usuario_id: int, tarefa_id: int, concluida: bool) -> bool:
        cur = self.c.execute(
            "UPDATE tarefas_checklist SET concluida = ?, concluida_em = ?"
            " WHERE id = ? AND checklist_id IN (SELECT id FROM checklists WHERE usuario_id = ?)",
            (int(concluida), _agora() if concluida else None, tarefa_id, usuario_id))
        self.c.commit()
        return cur.rowcount > 0

    def reiniciar_checklist(self, usuario_id: int, checklist_id: int) -> int:
        cur = self.c.execute(
            "UPDATE tarefas_checklist SET concluida = 0, concluida_em = NULL"
            " WHERE checklist_id IN (SELECT id FROM checklists WHERE id = ? AND usuario_id = ?)",
            (checklist_id, usuario_id))
        self.c.commit()
        return cur.rowcount

    def progresso(self, usuario_id: int) -> dict:
        listas = self.listar_checklists(usuario_id)
        total = sum(l["total"] for l in listas)
        feitas = sum(l["concluidas"] for l in listas)
        return {
            "total_tarefas": total,
            "concluidas": feitas,
            "percentual": round(100 * feitas / total) if total else 0,
            "checklists": listas,
            "perguntas": self.contar_perguntas(usuario_id),
            "favoritos": len(self.listar_favoritos(usuario_id)),
        }
