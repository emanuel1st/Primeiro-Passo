"""Configuração central: caminhos, variáveis de ambiente e constantes.

Nada aqui cria arquivos ao ser importado (importante para os testes).
A chave da API de IA NUNCA fica no código: vem de variável de ambiente
ou de um arquivo `.env` local, que está no .gitignore.
"""
import os
import sys
from pathlib import Path

NOME_APP = "Primeiro Passo"
SLOGAN = "Seu guia para a vida adulta."
AVISO_NAO_OFICIAL = (
    "O Primeiro Passo é uma plataforma independente. Não é um serviço do Governo "
    "Federal e não substitui o Gov.br nem qualquer serviço público. Ele explica "
    "procedimentos e indica os canais oficiais."
)


def _congelado() -> bool:
    """True quando rodando como executável do PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def raiz_projeto() -> Path:
    """Pasta que contém `data/` (e `.env`, quando rodando do código-fonte)."""
    if _congelado():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def pasta_dados_conhecimento() -> Path:
    return raiz_projeto() / "data"


def pasta_dados_usuario() -> Path:
    """Onde fica o banco SQLite. Criada sob demanda."""
    if _congelado():
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "PrimeiroPasso"
    else:
        base = raiz_projeto() / "dados_locais"
    base.mkdir(parents=True, exist_ok=True)
    return base


def caminho_banco() -> Path:
    """Caminho do banco. Pode ser trocado por PRIMEIRO_PASSO_DB (usado nos testes)."""
    personalizado = os.environ.get("PRIMEIRO_PASSO_DB")
    if personalizado:
        return Path(personalizado)
    return pasta_dados_usuario() / "primeiro_passo.db"


def carregar_env() -> None:
    """Lê arquivos `.env` simples (CHAVE=valor) sem sobrescrever o ambiente.

    Procura na raiz do projeto e na pasta de dados do usuário.
    """
    candidatos = [raiz_projeto() / ".env"]
    if _congelado():
        candidatos.append(Path(os.environ.get("APPDATA", str(Path.home()))) / "PrimeiroPasso" / ".env")
    for arquivo in candidatos:
        try:
            if not arquivo.is_file():
                continue
            for linha in arquivo.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                valor = valor.strip().strip('"').strip("'")
                if chave and chave not in os.environ:
                    os.environ[chave] = valor
        except OSError:
            continue  # .env ilegível: o app segue sem IA


# --- IA externa (opcional) -------------------------------------------------
MODELO_IA_PADRAO = "gemini-3.5-flash-lite"


def chave_ia() -> str:
    return os.environ.get("GEMINI_API_KEY", "").strip()


def modelo_ia() -> str:
    return os.environ.get("GEMINI_MODEL", "").strip() or MODELO_IA_PADRAO


def ia_configurada() -> bool:
    return bool(chave_ia())
