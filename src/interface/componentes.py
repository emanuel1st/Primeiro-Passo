"""Peças reutilizáveis da interface (rótulos, botões, cartões, avisos)."""
import math
import webbrowser
from datetime import datetime

import customtkinter as ctk

from interface.tema import tema

LARGURA_TEXTO = 640  # largura (px) usada para quebrar linhas: leitura confortável

STATUS_ROTULOS = {
    "ok": "Resposta encontrada", "multipla": "Mais de um assunto", "ambigua": "Pergunta ampla",
    "sem_resultado": "Sem resposta confiável", "vazia": "Pergunta vazia", "invalida": "Pergunta inválida",
}
SITUACAO_ROTULOS = {
    "verificado": "✔ Verificado em fonte oficial",
    "parcial": "◐ Verificado em parte",
    "pendente_validacao": "⚠ Pendente de validação",
}


def rotulo(master, texto="", tam=14, negrito=False, cor="texto", largura=LARGURA_TEXTO, **kw):
    return ctk.CTkLabel(master, text=texto, font=tema.fonte(tam, negrito), text_color=tema.cor(cor),
                        justify="left", anchor="w", wraplength=largura, **kw)


def botao(master, texto, comando, estilo="primario", **kw):
    cores = {
        "primario": dict(fg_color=tema.cor("primaria"), hover_color=tema.cor("primaria_hover"),
                         text_color=tema.cor("texto_primaria"), border_width=0),
        "secundario": dict(fg_color=tema.cor("destaque"), hover_color=tema.cor("borda"),
                           text_color=tema.cor("texto"), border_width=1, border_color=tema.cor("borda")),
        "perigo": dict(fg_color=tema.cor("perigo"), hover_color=tema.cor("perigo_hover"),
                       text_color="#FFFFFF" if not tema.alto_contraste else "#000000", border_width=0),
        "link": dict(fg_color="transparent", hover_color=tema.cor("destaque"),
                     text_color=tema.cor("link"), border_width=0),
    }[estilo]
    return ctk.CTkButton(master, text=texto, command=comando, font=tema.fonte(14, estilo == "primario"),
                         height=tema.px(38), corner_radius=8, **cores, **kw)


def cartao(master, **kw):
    return ctk.CTkFrame(master, fg_color=tema.cor("cartao"), border_width=1,
                        border_color=tema.cor("borda"), corner_radius=12, **kw)


def transparente(master, **kw):
    return ctk.CTkFrame(master, fg_color="transparent", **kw)


def titulo_pagina(master, titulo, subtitulo=""):
    quadro = transparente(master)
    quadro.pack(fill="x", padx=24, pady=(22, 10))
    rotulo(quadro, titulo, 26, True, "texto").pack(anchor="w")
    if subtitulo:
        rotulo(quadro, subtitulo, 14, False, "suave", largura=LARGURA_TEXTO + 100).pack(anchor="w", pady=(4, 0))
    return quadro


def aviso(master, texto, tipo="info", largura=LARGURA_TEXTO):
    """Faixa colorida. O tipo também aparece como prefixo, não só pela cor."""
    prefixos = {"info": "ℹ ", "alerta": "⚠ ", "erro": "✖ ", "ok": "✔ "}
    quadro = ctk.CTkFrame(master, fg_color=tema.cor(f"{tipo}_fundo"), corner_radius=10,
                          border_width=1, border_color=tema.cor(f"{tipo}_texto"))
    rotulo(quadro, prefixos[tipo] + texto, 14, False, f"{tipo}_texto", largura=largura).pack(
        padx=14, pady=10, anchor="w")
    return quadro


def selo_situacao(master, registro):
    situacao = registro["situacao"]
    cor = {"verificado": "ok_texto", "parcial": "alerta_texto", "pendente_validacao": "erro_texto"}[situacao]
    return rotulo(master, SITUACAO_ROTULOS[situacao], 12, True, cor)


def caixa_texto(master, texto, tam=14):
    """Texto selecionável (somente leitura), com altura ajustada ao conteúdo."""
    por_linha = max(30, int(78 / tema.escala))
    linhas = sum(max(1, math.ceil(len(l) / por_linha)) for l in texto.splitlines() or [""])
    altura = min(max(int(linhas * tam * tema.escala * 1.65) + 24, 80), 1100)
    caixa = ctk.CTkTextbox(master, height=altura, wrap="word", font=tema.fonte(tam),
                           fg_color=tema.cor("cartao"), text_color=tema.cor("texto"),
                           border_width=1, border_color=tema.cor("borda"), corner_radius=10)
    caixa.insert("1.0", texto)
    caixa.configure(state="disabled")
    return caixa


def abrir_link(url: str) -> bool:
    try:
        return bool(webbrowser.open(url))
    except Exception:  # sem navegador padrão: o chamador mostra o endereço
        return False


def formatar_data(texto: str) -> str:
    try:
        return datetime.fromisoformat(texto).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return texto or ""


def primeiro_nome(nome: str) -> str:
    return (nome or "").split(" ")[0] or "você"
