"""Oportunidades: só o que está na base validada, sempre com fonte, link e data."""
import customtkinter as ctk

from interface.componentes import (abrir_link, aviso, botao, cartao, rotulo, selo_situacao, titulo_pagina,
                                   transparente)
from interface.pagina import Pagina
from interface.tema import tema
from services.recomendacoes import PORTAIS_OFICIAIS

TODOS = "Todos os tipos"


class PaginaOportunidades(Pagina):
    def __init__(self, master, app, **_):
        super().__init__(master, app)
        titulo_pagina(self, "Oportunidades",
                      "Programas e serviços públicos que ajudam no começo da vida adulta.")
        aviso(self, "Mostro apenas o que consegui conferir em fontes oficiais, com a data da conferência. "
                    "Não listo vagas, bolsas ou prazos que eu não possa comprovar. Para ofertas atuais, "
                    "use os portais oficiais no fim da página.", "info", largura=700).pack(anchor="w", padx=24)

        self.itens = self.ctx.oportunidades
        tipos = sorted({o["tipo"] for o in self.itens})
        self.var_tipo = ctk.StringVar(value=TODOS)
        if tipos:
            ctk.CTkOptionMenu(self, values=[TODOS] + tipos, variable=self.var_tipo, command=lambda _v: self._lista(),
                              font=tema.fonte(13), dropdown_font=tema.fonte(13), width=tema.px(260),
                              fg_color=tema.cor("primaria"), button_color=tema.cor("primaria_hover"),
                              text_color=tema.cor("texto_primaria")).pack(anchor="w", padx=24, pady=10)
        self.area = transparente(self)
        self.area.pack(fill="x", padx=24)
        self._lista()
        self._portais()

    def _lista(self):
        self.limpar(self.area)
        filtro = self.var_tipo.get()
        mostrados = [o for o in self.itens if filtro in (TODOS, o["tipo"])]
        if not mostrados:
            aviso(self.area, "Não há oportunidades validadas para este filtro. Consulte os portais oficiais abaixo.",
                  "alerta", largura=600).pack(anchor="w", pady=8)
            return
        for item in mostrados:
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=6)
            rotulo(quadro, item["titulo"], 17, True, largura=560).pack(anchor="w", padx=16, pady=(12, 0))
            rotulo(quadro, f"{item['tipo']}  ·  {item['status']}", 13, True, "suave", largura=560).pack(
                anchor="w", padx=16)
            rotulo(quadro, item["descricao"], 14, False, largura=560).pack(anchor="w", padx=16, pady=(4, 0))
            data = "/".join(reversed(item["data_verificacao"].split("-"))) if item["data_verificacao"] else None
            registro = self.ctx.base.por_id[item["conhecimento_id"]]
            selo_situacao(quadro, registro).pack(anchor="w", padx=16, pady=(4, 0))
            rotulo(quadro, f"Verificado em {data}" if data else "Data de verificação: pendente", 12, False, "suave",
                   largura=560).pack(anchor="w", padx=16)
            linha = transparente(quadro)
            linha.pack(anchor="w", padx=10, pady=(4, 12))
            for fonte in item["fontes"]:
                botao(linha, f"🔗 {fonte['nome']}", lambda u=fonte["url"]: abrir_link(u), "link").pack(
                    side="left", padx=2)
            botao(linha, "Ver orientação", lambda i=item["conhecimento_id"]: self.app.navegar(
                "assistente", assunto_id=i), "secundario").pack(side="left", padx=2)

    def _portais(self):
        rotulo(self, "Portais oficiais para ofertas atuais", 18, True, largura=600).pack(anchor="w", padx=24, pady=(18, 4))
        for nome, url in PORTAIS_OFICIAIS:
            botao(self, f"🔗 {nome}", lambda u=url: abrir_link(u), "link").pack(anchor="w", padx=20)
        transparente(self, height=24).pack()
