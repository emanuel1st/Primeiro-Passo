"""Integração OPCIONAL com IA externa (Google Gemini API, via HTTP REST).

Regras do projeto
-----------------
* A chave vem de GEMINI_API_KEY (variável de ambiente ou arquivo .env local).
  Ela nunca fica no código e nunca é escrita em logs ou mensagens de erro.
* Sem chave, ou se a API falhar, o app responde com a busca local.
* A IA só recebe os conhecimentos encontrados na base local e só pode
  reorganizar e simplificar. Depois, `validar_resposta_ia` descarta respostas
  com links ou números que não estejam nos conhecimentos.

ATENÇÃO: este módulo foi testado apenas com respostas simuladas. Não houve
acesso à internet nem chave de API durante o desenvolvimento. Valide com a sua
chave antes da entrega.
"""
import json
import re
import socket
import urllib.error
import urllib.request

import config
from services.templates import INSTRUCOES, data_br

URL_MODELO = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
TIMEOUT_SEGUNDOS = 20


class ErroIA(Exception):
    """Falha da IA externa. A mensagem é segura para mostrar ao usuário."""


def _transporte_urllib(url: str, cabecalhos: dict, corpo: bytes, timeout: int):
    pedido = urllib.request.Request(url, data=corpo, headers=cabecalhos, method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            return resposta.status, resposta.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as erro:
        return erro.code, ""


def montar_conhecimentos(registros) -> str:
    """Texto com os conhecimentos que serão enviados à IA (e nada mais)."""
    blocos = []
    for reg in registros:
        linhas = [f"ID: {reg['id']}", f"Tema: {reg['tema']}", f"Orientação: {reg['orientacao']}"]
        if reg.get("etapas"):
            linhas.append("Etapas: " + " | ".join(reg["etapas"]))
        if reg.get("alertas"):
            linhas.append("Alertas: " + " | ".join(reg["alertas"]))
        for fonte in reg.get("fontes", []):
            linhas.append(f"Fonte: {fonte['nome']} - {fonte['url']}")
        if reg["situacao"] == "verificado":
            linhas.append(f"Situação: verificado em {data_br(reg.get('data_verificacao'))}")
        elif reg["situacao"] == "parcial":
            linhas.append("Situação: PARCIALMENTE VERIFICADO")
        else:
            linhas.append("Situação: PENDENTE DE VALIDAÇÃO")
        blocos.append("\n".join(linhas))
    return "<<<CONHECIMENTOS>>>\n" + "\n---\n".join(blocos) + "\n<<<FIM>>>"


class ClienteIA:
    """Cliente mínimo da API. `transporte` pode ser trocado nos testes."""

    def __init__(self, chave=None, modelo=None, transporte=None, timeout=TIMEOUT_SEGUNDOS):
        self.chave = (chave if chave is not None else config.chave_ia()).strip()
        self.modelo = modelo or config.modelo_ia()
        self._transporte = transporte or _transporte_urllib
        self.timeout = timeout

    def disponivel(self) -> bool:
        return bool(self.chave)

    def reescrever(self, pergunta: str, registros, template: str = "A") -> str:
        if not self.disponivel():
            raise ErroIA("A IA externa não está configurada (falta a chave de API).")
        corpo = {
            "systemInstruction": {"parts": [{"text": INSTRUCOES.get(template, INSTRUCOES["A"])}]},
            "contents": [{
                "role": "user",
                "parts": [{"text": f"Pergunta do usuário: {pergunta}\n\n{montar_conhecimentos(registros)}"}],
            }],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900},
        }
        cabecalhos = {"Content-Type": "application/json", "x-goog-api-key": self.chave}
        url = URL_MODELO.format(modelo=self.modelo)
        try:
            status, texto = self._transporte(url, cabecalhos, json.dumps(corpo).encode("utf-8"), self.timeout)
        except (socket.timeout, TimeoutError):
            raise ErroIA("A IA demorou demais para responder.") from None
        except urllib.error.URLError:
            raise ErroIA("Não consegui conectar à IA. Verifique sua internet.") from None
        except OSError:
            raise ErroIA("Falha de conexão com a IA.") from None
        if status != 200:
            raise ErroIA(_mensagem_http(status))
        return _extrair_texto(texto)


def _mensagem_http(status: int) -> str:
    if status in (400, 401, 403):
        return "A IA recusou o acesso. Confira se a chave de API e o modelo estão corretos."
    if status == 404:
        return "O modelo de IA configurado não foi encontrado (GEMINI_MODEL)."
    if status == 429:
        return "O limite de uso gratuito da IA foi atingido. Tente mais tarde."
    if status >= 500:
        return "O serviço de IA está instável no momento."
    return f"A IA retornou um erro inesperado (código {status})."


def _extrair_texto(corpo: str) -> str:
    try:
        dados = json.loads(corpo)
        partes = dados["candidates"][0]["content"]["parts"]
        texto = "".join(p.get("text", "") for p in partes).strip()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ErroIA("A IA não devolveu uma resposta utilizável.") from None
    if not texto:
        raise ErroIA("A IA devolveu uma resposta vazia.")
    return texto


# --- validação da resposta da IA --------------------------------------------
_URL = re.compile(r"https?://[^\s)>\]\"']+")
_NUMERO = re.compile(r"\d[\d.,]*\d|\d")


def _numeros_relevantes(texto: str) -> set:
    """Números com 2+ dígitos (prazos, valores, anos). Dígitos soltos são ignorados
    porque a IA numera listas (1., 2., 3.)."""
    achados = set()
    for n in _NUMERO.findall(texto):
        n = n.rstrip(".,")
        if len(re.sub(r"\D", "", n)) >= 2:
            achados.add(n)
    return achados


def validar_resposta_ia(texto: str, registros) -> tuple:
    """Confere a resposta da IA com os conhecimentos. Devolve (ok, motivo)."""
    if not texto or not texto.strip():
        return False, "resposta vazia"
    permitidas = {f["url"].rstrip("/.,") for r in registros for f in r.get("fontes", [])}
    for url in _URL.findall(texto):
        if url.rstrip("/.,") not in permitidas:
            return False, f"link fora da base: {url}"
    base = " ".join(
        [r["orientacao"] + " " + " ".join(r.get("etapas", [])) + " " + " ".join(r.get("alertas", []))
         + " " + r.get("data_verificacao", "") for r in registros]
    )
    permitidos = _numeros_relevantes(base)
    permitidos |= {n for n in re.findall(r"\d+", base) if len(n) >= 2}  # 8% -> 8; 81,05 -> 81 e 05
    for numero in _numeros_relevantes(texto):
        partes = re.findall(r"\d+", numero)
        if numero not in permitidos and not all(p in permitidos for p in partes if len(p) >= 2):
            return False, f"número que não está na base: {numero}"
    return True, ""
