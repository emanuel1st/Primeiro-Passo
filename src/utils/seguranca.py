"""Proteção de senhas com PBKDF2-HMAC-SHA256 (biblioteca padrão do Python).

Formato guardado no banco:  pbkdf2_sha256$<iterações>$<salt_hex>$<hash_hex>
A senha nunca é armazenada em texto puro.
"""
import hashlib
import hmac
import secrets

ALGORITMO = "pbkdf2_sha256"
ITERACOES = 200_000


def gerar_hash(senha: str, iteracoes: int = ITERACOES) -> str:
    salt = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
    return f"{ALGORITMO}${iteracoes}${salt.hex()}${derivado.hex()}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    """Compara a senha digitada com o hash guardado (tempo constante)."""
    try:
        algoritmo, iteracoes, salt_hex, hash_hex = armazenado.split("$")
        if algoritmo != ALGORITMO:
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes)
        )
        return hmac.compare_digest(derivado.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False
