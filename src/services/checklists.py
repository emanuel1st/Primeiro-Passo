"""Leitura dos modelos de checklist (data/checklists.json)."""
import json
from pathlib import Path

import config


def carregar_modelos(pasta=None) -> list:
    """Lista de modelos válidos. Arquivo ausente ou inválido => lista vazia."""
    pasta = Path(pasta) if pasta else config.pasta_dados_conhecimento()
    try:
        with open(pasta / "checklists.json", encoding="utf-8") as arquivo:
            bruto = json.load(arquivo).get("modelos", [])
    except (OSError, ValueError):
        return []
    return [m for m in bruto if m.get("id") and m.get("titulo") and m.get("tarefas")]
