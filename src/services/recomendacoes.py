"""Recomendações de conteúdo e lista de oportunidades.

Nada aqui inventa conteúdo: tudo vem da base de conhecimento e do grafo.
"""
import json
from pathlib import Path

import config


def recomendar(base, grafo, ids_historico, ids_favoritos, limite: int = 4) -> list:
    """Sugere assuntos ainda não vistos. Devolve lista de (registro, motivo).

    Ordem de prioridade: vizinhos dos favoritos, vizinhos do histórico e,
    por fim, os passos do roteiro "Completei 18 anos. E agora?".
    """
    vistos = set(ids_historico) | set(ids_favoritos)
    candidatos = {}  # id -> motivo (dicionário mantém a ordem de inserção)
    for origem in list(ids_favoritos) + list(ids_historico):
        if origem not in base.por_id:
            continue
        for vizinho in grafo.vizinhos(origem):
            if vizinho not in vistos and vizinho not in candidatos:
                candidatos[vizinho] = f"Relacionado a “{base.por_id[origem]['tema']}”"
    for passo in base.roteiro.get("passos", []):
        cid = passo["conhecimento_id"]
        if cid in base.por_id and cid not in vistos and cid not in candidatos:
            candidatos[cid] = f"Do roteiro “{base.roteiro.get('titulo', '')}”"
    return [(base.por_id[cid], motivo) for cid, motivo in list(candidatos.items())[:limite]]


def carregar_oportunidades(base, pasta=None) -> list:
    """Junta data/oportunidades.json com os dados oficiais do registro ligado.

    Fonte, link e data de verificação vêm do conhecimento (`conhecimento_id`),
    nunca são digitados à mão aqui. Se o registro não existir, a oportunidade
    é ignorada.
    """
    pasta = Path(pasta) if pasta else config.pasta_dados_conhecimento()
    try:
        with open(pasta / "oportunidades.json", encoding="utf-8") as arquivo:
            bruto = json.load(arquivo).get("oportunidades", [])
    except (OSError, ValueError):
        return []
    saida = []
    for item in bruto:
        reg = base.por_id.get(item.get("conhecimento_id"))
        if reg is None:
            continue
        saida.append({
            "titulo": item["titulo"],
            "tipo": item["tipo"],
            "descricao": item["descricao"],
            "status": item["status"],
            "conhecimento_id": reg["id"],
            "fontes": reg["fontes"],
            "data_verificacao": reg.get("data_verificacao"),
            "situacao": reg["situacao"],
        })
    return saida


PORTAIS_OFICIAIS = [
    ("Portal gov.br (serviços do Governo Federal)", "https://www.gov.br"),
    ("Consumidor.gov.br", "https://www.consumidor.gov.br"),
    ("Portal Único de Acesso ao Ensino Superior (MEC)", "https://acessounico.mec.gov.br/programas"),
]
