"""Validação de entradas: cadastro e perguntas do assistente."""
import re

from utils.texto import normalizar, tokenizar

LIMITE_PERGUNTA = 500
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def validar_nome(nome: str) -> list:
    erros = []
    nome = (nome or "").strip()
    if len(nome) < 2:
        erros.append("Informe seu nome (pelo menos 2 letras).")
    elif len(nome) > 60:
        erros.append("O nome pode ter no máximo 60 caracteres.")
    elif not any(c.isalpha() for c in nome):
        erros.append("O nome precisa conter letras.")
    return erros


def validar_email(email: str) -> list:
    email = (email or "").strip()
    if not email:
        return ["Informe seu e-mail."]
    if len(email) > 120 or not _EMAIL.match(email):
        return ["Esse e-mail não parece válido. Exemplo: nome@exemplo.com"]
    return []


def validar_senha(senha: str) -> list:
    erros = []
    senha = senha or ""
    if len(senha) < 8:
        erros.append("A senha precisa ter pelo menos 8 caracteres.")
    if not any(c.isalpha() for c in senha) or not any(c.isdigit() for c in senha):
        erros.append("A senha precisa ter letras e números.")
    return erros


def validar_cadastro(nome: str, email: str, senha: str, confirmacao: str) -> list:
    erros = validar_nome(nome) + validar_email(email) + validar_senha(senha)
    if senha != confirmacao:
        erros.append("A confirmação não é igual à senha.")
    return erros


def validar_pergunta(pergunta) -> tuple:
    """Classifica a pergunta antes de buscar.

    Retorna (ok, status, mensagem) com status em {"ok", "vazia", "invalida"}.
    """
    if pergunta is None or not isinstance(pergunta, str) or not pergunta.strip():
        return False, "vazia", "Digite uma pergunta para eu poder ajudar. Exemplo: “Como faço meu CPF?”"
    if len(pergunta) > LIMITE_PERGUNTA:
        return False, "invalida", f"A pergunta está muito longa. Resuma em até {LIMITE_PERGUNTA} caracteres."
    normalizada = normalizar(pergunta)
    if not any(c.isalpha() for c in normalizada):
        return False, "invalida", "Não consegui entender. Escreva sua pergunta com palavras, por exemplo: “Como tiro o título de eleitor?”"
    if not tokenizar(pergunta):
        return False, "invalida", "Sua pergunta tem só palavras muito comuns. Tente dizer o assunto, como “CPF”, “FGTS” ou “aluguel”."
    return True, "ok", ""
