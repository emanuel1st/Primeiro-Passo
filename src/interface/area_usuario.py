"""Telas do usuário: histórico, favoritos, checklists e progresso."""
import customtkinter as ctk
from tkinter import messagebox

from interface.componentes import (STATUS_ROTULOS, aviso, botao, caixa_texto, cartao, formatar_data, rotulo,
                                   selo_situacao, titulo_pagina, transparente)
from interface.pagina import Pagina
from interface.tema import tema
from services.recomendacoes import recomendar


def _barra(pai, fracao, largura=420):
    barra = ctk.CTkProgressBar(pai, width=tema.px(largura), height=tema.px(14), progress_color=tema.cor("primaria"),
                               fg_color=tema.cor("destaque"), border_width=1, border_color=tema.cor("borda"))
    barra.set(max(0.0, min(1.0, fracao)))
    return barra


# ============================================================================
class PaginaHistorico(Pagina):
    def __init__(self, master, app, **_):
        super().__init__(master, app)
        titulo_pagina(self, "Histórico", "Suas perguntas anteriores. Só você as vê neste computador.")
        linha = transparente(self)
        linha.pack(fill="x", padx=24, pady=(0, 8))
        self.busca = ctk.CTkEntry(linha, height=tema.px(40), font=tema.fonte(14), placeholder_text="Buscar no histórico",
                                  fg_color=tema.cor("cartao"), text_color=tema.cor("texto"),
                                  border_color=tema.cor("borda"), width=tema.px(320))
        self.busca.pack(side="left", padx=(0, 8))
        self.busca.bind("<Return>", lambda _e: self._lista())
        botao(linha, "Buscar", self._lista).pack(side="left", padx=(0, 8))
        botao(linha, "Limpar tudo", self._limpar, "perigo").pack(side="left")
        self.area = transparente(self)
        self.area.pack(fill="x", padx=24, pady=(0, 24))
        self._lista()

    def _lista(self):
        self.limpar(self.area)
        itens = self.ctx.repo.listar_historico(self.ctx.usuario_id, termo=self.busca.get())
        if not itens:
            aviso(self.area, "Nada por aqui ainda. Faça uma pergunta no Assistente.", "info", largura=600).pack(anchor="w")
            return
        for item in itens:
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            ia = "  ·  com IA" if item["usou_ia"] else ""
            rotulo(quadro, f"{formatar_data(item['criado_em'])}  ·  {STATUS_ROTULOS.get(item['status'], item['status'])}{ia}",
                   12, False, "suave", largura=560).pack(anchor="w", padx=16, pady=(10, 0))
            rotulo(quadro, item["pergunta"], 16, True, largura=560).pack(anchor="w", padx=16)
            detalhe = transparente(quadro)
            linha = transparente(quadro)
            linha.pack(anchor="w", padx=10, pady=(4, 10))
            botao(linha, "Ver resposta salva", lambda i=item, d=detalhe: self._alternar(i, d), "secundario").pack(
                side="left", padx=2)
            botao(linha, "Perguntar de novo", lambda p=item["pergunta"]: self.app.navegar("assistente", pergunta=p)).pack(
                side="left", padx=2)
            botao(linha, "Excluir", lambda i=item["id"]: self._excluir(i), "perigo").pack(side="left", padx=2)
            detalhe.pack(fill="x", padx=16, pady=(0, 10))

    def _alternar(self, item, detalhe):
        if detalhe.winfo_children():
            self.limpar(detalhe)
        else:
            caixa_texto(detalhe, item["resposta"], 13).pack(fill="x")

    def _excluir(self, item_id):
        self.ctx.repo.excluir_historico(self.ctx.usuario_id, item_id)
        self._lista()

    def _limpar(self):
        if messagebox.askyesno("Limpar histórico", "Apagar todo o seu histórico de perguntas? Isso não pode ser desfeito."):
            self.ctx.repo.limpar_historico(self.ctx.usuario_id)
            self._lista()


# ============================================================================
class PaginaFavoritos(Pagina):
    def __init__(self, master, app, **_):
        super().__init__(master, app)
        titulo_pagina(self, "Favoritos", "Assuntos que você salvou para consultar depois.")
        self.area = transparente(self)
        self.area.pack(fill="x", padx=24, pady=(0, 24))
        self._lista()

    def _lista(self):
        self.limpar(self.area)
        ids = [i for i in self.ctx.repo.listar_favoritos(self.ctx.usuario_id) if i in self.ctx.base.por_id]
        if not ids:
            aviso(self.area, "Você ainda não favoritou nada. Use ☆ Favoritar nas respostas do Assistente.", "info",
                  largura=600).pack(anchor="w")
            return
        for rid in ids:
            reg = self.ctx.base.por_id[rid]
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            rotulo(quadro, reg["tema"], 16, True, largura=560).pack(anchor="w", padx=16, pady=(12, 0))
            rotulo(quadro, self.ctx.base.nome_categoria(reg["categoria"]), 13, False, "suave", largura=560).pack(
                anchor="w", padx=16)
            selo_situacao(quadro, reg).pack(anchor="w", padx=16)
            linha = transparente(quadro)
            linha.pack(anchor="w", padx=10, pady=(4, 10))
            botao(linha, "Abrir", lambda i=rid: self.app.navegar("assistente", assunto_id=i)).pack(side="left", padx=2)
            botao(linha, "Remover", lambda i=rid: self._remover(i), "secundario").pack(side="left", padx=2)

    def _remover(self, rid):
        self.ctx.repo.remover_favorito(self.ctx.usuario_id, rid)
        self._lista()


# ============================================================================
class PaginaChecklists(Pagina):
    def __init__(self, master, app, checklist_id=None, **_):
        super().__init__(master, app)
        titulo_pagina(self, "Checklists", "Marque o que você já fez. O progresso fica salvo na sua conta.")
        self.listas = self.ctx.repo.listar_checklists(self.ctx.usuario_id)
        self._por_titulo = {l["titulo"]: l["id"] for l in self.listas}
        inicial = next((l["titulo"] for l in self.listas if l["id"] == checklist_id), self.listas[0]["titulo"])
        self.var = ctk.StringVar(value=inicial)
        ctk.CTkOptionMenu(self, values=list(self._por_titulo), variable=self.var, command=lambda _v: self._desenhar(),
                          font=tema.fonte(14), dropdown_font=tema.fonte(14), width=tema.px(420),
                          fg_color=tema.cor("primaria"), button_color=tema.cor("primaria_hover"),
                          text_color=tema.cor("texto_primaria")).pack(anchor="w", padx=24, pady=(0, 8))
        self.area = transparente(self)
        self.area.pack(fill="x", padx=24, pady=(0, 24))
        self._desenhar()

    def _desenhar(self):
        self.limpar(self.area)
        repo, uid = self.ctx.repo, self.ctx.usuario_id
        self.checklist_id = self._por_titulo[self.var.get()]
        tarefas = repo.listar_tarefas(uid, self.checklist_id)
        self.rot_progresso = rotulo(self.area, "", 15, True, largura=500)
        self.rot_progresso.pack(anchor="w")
        self.barra = _barra(self.area, 0)
        self.barra.pack(anchor="w", pady=(2, 10))
        for tarefa in tarefas:
            self._linha_tarefa(tarefa)
        botao(self.area, "Reiniciar esta checklist", self._reiniciar, "secundario").pack(anchor="w", pady=14)
        self._atualizar()

    def _linha_tarefa(self, tarefa):
        quadro = cartao(self.area)
        quadro.pack(fill="x", pady=3)
        var = ctk.BooleanVar(value=bool(tarefa["concluida"]))
        caixa = ctk.CTkCheckBox(quadro, text="", variable=var, width=tema.px(30), checkbox_width=tema.px(26),
                                checkbox_height=tema.px(26), fg_color=tema.cor("primaria"),
                                hover_color=tema.cor("primaria_hover"), border_color=tema.cor("texto"),
                                checkmark_color=tema.cor("texto_primaria"),
                                command=lambda t=tarefa["id"], v=var: self._marcar(t, v.get()))
        caixa.pack(side="left", padx=(14, 4), pady=10)
        texto = rotulo(quadro, tarefa["descricao"], 14, False, largura=470)
        texto.pack(side="left", pady=8)
        texto.bind("<Button-1>", lambda _e, c=caixa: c.toggle())  # toggle() também chama o comando
        if tarefa.get("conhecimento_id") in self.ctx.base.por_id:
            botao(quadro, "Saiba mais", lambda i=tarefa["conhecimento_id"]: self.app.navegar("assistente", assunto_id=i),
                  "link").pack(side="right", padx=8)

    def _marcar(self, tarefa_id, concluida):
        self.ctx.repo.marcar_tarefa(self.ctx.usuario_id, tarefa_id, concluida)
        self._atualizar()

    def _atualizar(self):
        lista = next(l for l in self.ctx.repo.listar_checklists(self.ctx.usuario_id) if l["id"] == self.checklist_id)
        self.rot_progresso.configure(text=f"{lista['concluidas']} de {lista['total']} tarefas concluídas")
        self.barra.set(lista["concluidas"] / lista["total"] if lista["total"] else 0)

    def _reiniciar(self):
        if messagebox.askyesno("Reiniciar checklist", "Desmarcar todas as tarefas desta checklist?"):
            self.ctx.repo.reiniciar_checklist(self.ctx.usuario_id, self.checklist_id)
            self._desenhar()


# ============================================================================
class PaginaProgresso(Pagina):
    def __init__(self, master, app, **_):
        super().__init__(master, app)
        ctx = self.ctx
        titulo_pagina(self, "Seu progresso", "Veja até onde você chegou e o que fazer a seguir.")
        dados = ctx.repo.progresso(ctx.usuario_id)

        geral = cartao(self)
        geral.pack(fill="x", padx=24, pady=6)
        rotulo(geral, f"{dados['percentual']}% das tarefas concluídas", 22, True, "link", largura=560).pack(
            anchor="w", padx=18, pady=(14, 4))
        _barra(geral, dados["percentual"] / 100, 520).pack(anchor="w", padx=18)
        rotulo(geral, f"{dados['concluidas']} de {dados['total_tarefas']} tarefas  ·  {dados['perguntas']} perguntas  ·  "
                      f"{dados['favoritos']} favoritos", 14, False, "suave", largura=560).pack(
            anchor="w", padx=18, pady=(6, 14))

        rotulo(self, "Por checklist", 18, True, largura=500).pack(anchor="w", padx=24, pady=(14, 4))
        for lista in dados["checklists"]:
            quadro = cartao(self)
            quadro.pack(fill="x", padx=24, pady=4)
            rotulo(quadro, lista["titulo"], 15, True, largura=560).pack(anchor="w", padx=16, pady=(10, 2))
            _barra(quadro, lista["concluidas"] / lista["total"] if lista["total"] else 0, 420).pack(anchor="w", padx=16)
            linha = transparente(quadro)
            linha.pack(fill="x", padx=16, pady=(4, 10))
            rotulo(linha, f"{lista['concluidas']}/{lista['total']}", 13, False, "suave", largura=100).pack(side="left")
            botao(linha, "Abrir", lambda i=lista["id"]: app.navegar("checklists", checklist_id=i), "secundario").pack(
                side="right")

        sugestoes = recomendar(ctx.base, ctx.grafo, ctx.repo.ids_do_historico(ctx.usuario_id),
                               ctx.repo.listar_favoritos(ctx.usuario_id))
        if sugestoes:
            rotulo(self, "Próximos assuntos sugeridos", 18, True, largura=500).pack(anchor="w", padx=24, pady=(14, 4))
            for registro, motivo in sugestoes:
                quadro = cartao(self)
                quadro.pack(fill="x", padx=24, pady=4)
                rotulo(quadro, registro["tema"], 15, True, largura=560).pack(anchor="w", padx=16, pady=(10, 0))
                rotulo(quadro, motivo, 13, False, "suave", largura=560).pack(anchor="w", padx=16)
                botao(quadro, "Abrir", lambda i=registro["id"]: app.navegar("assistente", assunto_id=i), "secundario").pack(
                    anchor="w", padx=16, pady=(4, 10))
        transparente(self, height=24).pack()
