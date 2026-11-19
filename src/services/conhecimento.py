"""Leitura e validação da base de conhecimento (JSON).

A base fica em `data/` e pode ser editada sem mexer no código. Registros
inválidos NÃO derrubam o app: são ignorados e listados em `erros`.
"""
import json
import re
from pathlib import Path

import config

SITUACOES = ("verificado", "parcial", "pendente_validacao")
CAMPOS_OBRIGATORIOS = (
    "id", "categoria", "tema", "pergunta", "palavras_chave",
    "orientacao", "fontes", "situacao",
)
_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validar_registro(reg: dict, ids_categorias) -> list:
    """Devolve a lista de problemas do registro (vazia = válido)."""
    if not isinstance(reg, dict):
        return ["registro não é um objeto JSON"]
    erros = []
    for campo in CAMPOS_OBRIGATORIOS:
        if reg.get(campo) in (None, "", []):
            erros.append(f"campo obrigatório ausente: {campo}")
    if erros:
        return erros
    if reg["categoria"] not in ids_categorias:
        erros.append(f"categoria desconhecida: {reg['categoria']}")
    if reg["situacao"] not in SITUACOES:
        erros.append(f"situação inválida: {reg['situacao']}")
    if not isinstance(reg["palavras_chave"], list):
        erros.append("palavras_chave deve ser uma lista")
    for fonte in reg["fontes"] if isinstance(reg["fontes"], list) else []:
        url = str(fonte.get("url", "")) if isinstance(fonte, dict) else ""
        if not fonte.get("nome") or not url.startswith(("http://", "https://")):
            erros.append("fonte precisa de 'nome' e de 'url' começando com http(s)://")
    data = reg.get("data_verificacao")
    if reg["situacao"] == "pendente_validacao":
        if data:
            erros.append("registro pendente de validação não pode ter data de verificação")
    elif not (isinstance(data, str) and _DATA.match(data)):
        erros.append("data_verificacao deve estar no formato AAAA-MM-DD")
    return erros


class BaseConhecimento:
    """Mantém registros, categorias, roteiro e trilhas em memória."""

    def __init__(self, registros, categorias, roteiro=None, trilhas=None, erros=None):
        self.categorias = list(categorias)
        self.categorias_por_id = {c["id"]: c for c in self.categorias}
        self.registros = list(registros)
        self.por_id = {r["id"]: r for r in self.registros}
        self.roteiro = roteiro or {}
        self.trilhas = list(trilhas or [])
        self.erros = list(erros or [])
        self._limpar_relacoes()

    def _limpar_relacoes(self) -> None:
        """Remove referências a IDs que não existem (e avisa)."""
        for reg in self.registros:
            validos = []
            for outro in reg.get("relacionados", []):
                if outro in self.por_id and outro != reg["id"]:
                    validos.append(outro)
                else:
                    self.erros.append(f"{reg['id']}: relacionado inexistente ignorado ({outro})")
            reg["relacionados"] = validos
        for trilha in self.trilhas:
            trilha["passos"] = [p for p in trilha.get("passos", []) if p in self.por_id]

    @classmethod
    def carregar(cls, pasta=None) -> "BaseConhecimento":
        pasta = Path(pasta) if pasta else config.pasta_dados_conhecimento()
        erros = []
        categorias_json = _ler_json(pasta / "categorias.json")
        categorias = categorias_json.get("categorias", [])
        if not categorias:
            raise ValueError("categorias.json não contém categorias.")
        ids_categorias = {c["id"] for c in categorias}

        bruto = _ler_json(pasta / "conhecimentos.json").get("conhecimentos", [])
        registros, vistos = [], set()
        for indice, reg in enumerate(bruto, start=1):
            problemas = validar_registro(reg, ids_categorias)
            rotulo = reg.get("id", f"#{indice}") if isinstance(reg, dict) else f"#{indice}"
            if not problemas and reg["id"] in vistos:
                problemas = ["ID duplicado"]
            if problemas:
                erros.extend(f"{rotulo}: {p}" for p in problemas)
                continue
            vistos.add(reg["id"])
            registros.append(reg)
        if not registros:
            raise ValueError("Nenhum conhecimento válido foi encontrado em conhecimentos.json.")
        return cls(
            registros, categorias,
            roteiro=categorias_json.get("roteiro_18_anos"),
            trilhas=categorias_json.get("trilhas"),
            erros=erros,
        )

    # --- consultas -----------------------------------------------------
    def obter(self, registro_id: str):
        return self.por_id.get(registro_id)

    def da_categoria(self, categoria_id: str) -> list:
        return [r for r in self.registros if r["categoria"] == categoria_id]

    def nome_categoria(self, categoria_id: str) -> str:
        return self.categorias_por_id.get(categoria_id, {}).get("nome", categoria_id)

    def estatisticas(self) -> dict:
        contagem = {s: 0 for s in SITUACOES}
        for reg in self.registros:
            contagem[reg["situacao"]] += 1
        return {"total": len(self.registros), "categorias": len(self.categorias), **contagem}


def carregar_sinonimos(pasta=None) -> list:
    """Lê os grupos de sinônimos. Se o arquivo faltar, a busca segue sem eles."""
    pasta = Path(pasta) if pasta else config.pasta_dados_conhecimento()
    try:
        grupos = _ler_json(pasta / "sinonimos.json").get("grupos", [])
    except (OSError, ValueError):
        return []
    return [g for g in grupos if isinstance(g, list) and len(g) >= 2]


def _ler_json(caminho: Path) -> dict:
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo da base não encontrado: {caminho}") from None
    except json.JSONDecodeError as erro:
        raise ValueError(f"JSON inválido em {caminho.name} (linha {erro.lineno}): {erro.msg}") from None
