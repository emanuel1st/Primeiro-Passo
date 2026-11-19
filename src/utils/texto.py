"""Normalização de texto para a busca local.

Passos (na ordem): minúsculas -> remove acentos -> troca pontuação por espaço
-> separa em palavras -> remove palavras vazias (stopwords) -> reduz o plural
(estemização simples). Tanto a pergunta quanto a base passam por aqui, então
"Títulos de Eleitor!" e "titulo de eleitor" viram a mesma sequência.
"""
import re
import unicodedata

# Palavras muito comuns que não ajudam a distinguir assuntos.
# Obs.: "das" fica de fora de propósito, porque DAS é o boleto do MEI.
STOPWORDS = frozenset(
    """
    a o as os um uma uns umas de do da dos em no na nos nas por para pra com sem e ou
    que qual quais quem como onde quando quanto quanta quantos quantas eu me meu minha
    meus minhas voce se ao aos ser sou sao foi ha ja mais muito quero preciso precisa
    posso pode devo deve faco fazer faz tenho ter estou esta sobre isso isto esse essa
    este favor funciona vou vai
    """.split()
)

_NAO_ALFANUM = re.compile(r"[^a-z0-9]+")


def remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação, com espaços simples."""
    if not isinstance(texto, str):
        return ""
    sem_acento = remover_acentos(texto.lower())
    return _NAO_ALFANUM.sub(" ", sem_acento).strip()


def estemizar(palavra: str) -> str:
    """Redução bem simples de plural: 'documentos' -> 'documento'.

    Não é um estemizador completo; só junta singular e plural comuns.
    """
    if len(palavra) <= 3:
        return palavra
    if palavra.endswith(("oes", "aes")):
        return palavra[:-3] + "ao"  # declaracoes -> declaracao
    if len(palavra) > 5 and palavra.endswith(("ores", "ares", "eres", "ures")):
        return palavra[:-2]  # eleitores -> eleitor
    if palavra.endswith("s") and not palavra.endswith("ss"):
        return palavra[:-1]
    return palavra


def tokenizar(texto: str, remover_stopwords: bool = True) -> list:
    """Lista de palavras normalizadas e estemizadas, na ordem original."""
    tokens = []
    for palavra in normalizar(texto).split():
        if remover_stopwords and palavra in STOPWORDS:
            continue
        if len(palavra) < 2 and not palavra.isdigit():
            continue
        tokens.append(estemizar(palavra))
    return tokens
