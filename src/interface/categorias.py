"""Navegação por categorias, roteiro "Completei 18 anos. E agora?" e trilhas de assuntos."""
import customtkinter as ctk

from interface.componentes import botao, cartao, rotulo, selo_situacao, titulo_pagina, transparente
from interface.pagina import Pagina
from interface.tema import tema

ABAS = ["Categorias", "Roteiro 18 anos", "Trilhas"]


class PaginaCategorias(Pagina):
    def __init__(self, master, app, aba="Categorias", categoria_id=None, **_):
        super().__init__(master, app)
        titulo_pagina(self, "Categorias", "Explore os assuntos por tema, siga o roteiro dos 18 anos ou uma trilha.")
        self.var_aba = ctk.StringVar(value=aba if aba in ABAS else ABAS[0])
        ctk.CTkSegmentedButton(self, values=ABAS, variable=self.var_aba, command=lambda _v: self._desenhar(),
                               font=tema.fonte(14), selected_color=tema.cor("primaria"),
                               selected_hover_color=tema.cor("primaria_hover"),
                               text_color=tema.cor("texto_primaria"), unselected_color=tema.cor("destaque"),
                               unselected_hover_color=tema.cor("borda")).pack(anchor="w", padx=24, pady=(0, 8))
        self.area = transparente(self)
        self.area.pack(fill="x", padx=24, pady=(4, 24))
        self._categoria = categoria_id
        self._desenhar()

    def _desenhar(self):
        self.limpar(self.area)
        aba = self.var_aba.get()
        if aba == "Roteiro 18 anos":
            self._roteiro()
        elif aba == "Trilhas":
            self._trilhas()
        elif self._categoria:
            self._assuntos(self._categoria)
        else:
            self._lista_categorias()

    # --- categorias ---------------------------------------------------------
    def _lista_categorias(self):
        base = self.ctx.base
        for cat in base.categorias:
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            total = len(base.da_categoria(cat["id"]))
            rotulo(quadro, f"{cat.get('icone', '')} {cat['nome']}", 17, True, largura=560).pack(
                anchor="w", padx=16, pady=(12, 0))
            rotulo(quadro, cat.get("descricao", ""), 14, False, "suave", largura=560).pack(anchor="w", padx=16)
            botao(quadro, f"Ver {total} assunto(s)", lambda c=cat["id"]: self._abrir_categoria(c),
                  "secundario").pack(anchor="w", padx=16, pady=(6, 12))

    def _abrir_categoria(self, categoria_id):
        self._categoria = categoria_id
        self._desenhar()

    def _assuntos(self, categoria_id):
        base = self.ctx.base
        botao(self.area, "← Todas as categorias", lambda: self._abrir_categoria(None), "link").pack(anchor="w")
        rotulo(self.area, base.nome_categoria(categoria_id), 20, True, largura=600).pack(anchor="w", pady=(4, 8))
        for reg in base.da_categoria(categoria_id):
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            rotulo(quadro, reg["tema"], 16, True, largura=560).pack(anchor="w", padx=16, pady=(12, 0))
            rotulo(quadro, reg["pergunta"], 14, False, "suave", largura=560).pack(anchor="w", padx=16)
            selo_situacao(quadro, reg).pack(anchor="w", padx=16)
            botao(quadro, "Abrir orientação", lambda i=reg["id"]: self.app.navegar("assistente", assunto_id=i)).pack(
                anchor="w", padx=16, pady=(6, 12))

    # --- roteiro ----------------------------------------------------------------
    def _roteiro(self):
        roteiro, base = self.ctx.base.roteiro, self.ctx.base
        if not roteiro:
            rotulo(self.area, "O roteiro não está disponível na base.", 14).pack(anchor="w")
            return
        rotulo(self.area, f"🎂 {roteiro['titulo']}", 22, True, largura=600).pack(anchor="w")
        rotulo(self.area, roteiro["descricao"], 14, False, "suave", largura=600).pack(anchor="w", pady=(2, 10))
        feitos = set(self.ctx.repo.ids_do_historico(self.ctx.usuario_id, limite=200))
        for passo in sorted(roteiro["passos"], key=lambda p: p["ordem"]):
            reg = base.por_id.get(passo["conhecimento_id"])
            if reg is None:
                continue
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            visto = "  ✔ já consultado" if reg["id"] in feitos else ""
            rotulo(quadro, f"{passo['ordem']}. {passo['titulo']}{visto}", 16, True, largura=560).pack(
                anchor="w", padx=16, pady=(12, 0))
            rotulo(quadro, passo.get("observacao", ""), 14, False, "suave", largura=560).pack(anchor="w", padx=16)
            selo_situacao(quadro, reg).pack(anchor="w", padx=16)
            botao(quadro, "Abrir orientação", lambda i=reg["id"]: self.app.navegar("assistente", assunto_id=i),
                  "secundario").pack(anchor="w", padx=16, pady=(6, 12))

    # --- trilhas --------------------------------------------------------------
    def _trilhas(self):
        base = self.ctx.base
        rotulo(self.area, "Cada trilha reúne assuntos relacionados, em uma ordem sugerida.", 14, False, "suave",
               largura=600).pack(anchor="w", pady=(0, 8))
        for trilha in base.trilhas:
            quadro = cartao(self.area)
            quadro.pack(fill="x", pady=5)
            rotulo(quadro, f"🧩 {trilha['titulo']}", 17, True, largura=560).pack(anchor="w", padx=16, pady=(12, 4))
            for posicao, rid in enumerate(trilha["passos"], start=1):
                reg = base.por_id[rid]
                botao(quadro, f"{posicao}. {reg['tema']}", lambda i=rid: self.app.navegar("assistente", assunto_id=i),
                      "secundario").pack(anchor="w", padx=16, pady=2)
            transparente(quadro, height=8).pack()
