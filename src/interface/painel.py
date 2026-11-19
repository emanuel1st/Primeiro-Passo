"""Tela inicial: resumo do usuário, pergunta rápida e próximos passos sugeridos."""
import customtkinter as ctk

from config import AVISO_NAO_OFICIAL, SLOGAN
from interface.componentes import aviso, botao, cartao, primeiro_nome, rotulo, selo_situacao, titulo_pagina, transparente
from interface.pagina import Pagina
from interface.tema import tema
from services.recomendacoes import recomendar


class PaginaPainel(Pagina):
    def __init__(self, master, app, **params):
        super().__init__(master, app)
        ctx = self.ctx
        titulo_pagina(self, f"Olá, {primeiro_nome(ctx.usuario['nome'])}!", SLOGAN)

        # pergunta rápida
        caixa = cartao(self)
        caixa.pack(fill="x", padx=24, pady=6)
        rotulo(caixa, "Qual é a sua dúvida hoje?", 18, True, largura=700).pack(anchor="w", padx=18, pady=(14, 6))
        linha = transparente(caixa)
        linha.pack(fill="x", padx=18, pady=(0, 16))
        self.entrada = ctk.CTkEntry(linha, height=tema.px(42), font=tema.fonte(15), fg_color=tema.cor("cartao"),
                                    text_color=tema.cor("texto"), border_color=tema.cor("borda"),
                                    placeholder_text="Ex.: Como funciona o FGTS?")
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entrada.bind("<Return>", lambda _e: self.perguntar())
        botao(linha, "Perguntar", self.perguntar).pack(side="right")

        # números
        progresso = ctx.repo.progresso(ctx.usuario_id)
        linha = transparente(self)
        linha.pack(fill="x", padx=24, pady=8)
        for valor, legenda in ((progresso["perguntas"], "perguntas feitas"),
                               (progresso["favoritos"], "assuntos favoritos"),
                               (f"{progresso['percentual']}%", "das tarefas concluídas")):
            cartao_num = cartao(linha)
            cartao_num.pack(side="left", padx=(0, 12), ipadx=10)
            rotulo(cartao_num, str(valor), 28, True, "link", largura=200).pack(padx=16, pady=(10, 0), anchor="w")
            rotulo(cartao_num, legenda, 13, False, "suave", largura=200).pack(padx=16, pady=(0, 10), anchor="w")

        # roteiro
        roteiro = ctx.base.roteiro
        if roteiro:
            caixa = cartao(self)
            caixa.pack(fill="x", padx=24, pady=8)
            rotulo(caixa, f"🎂 {roteiro['titulo']}", 18, True, largura=700).pack(anchor="w", padx=18, pady=(14, 2))
            rotulo(caixa, roteiro["descricao"], 14, False, "suave", largura=700).pack(anchor="w", padx=18)
            botao(caixa, "Ver o roteiro passo a passo",
                  lambda: app.navegar("categorias", aba="Roteiro 18 anos")).pack(anchor="w", padx=18, pady=14)

        # recomendações
        sugestoes = recomendar(ctx.base, ctx.grafo, ctx.repo.ids_do_historico(ctx.usuario_id),
                               ctx.repo.listar_favoritos(ctx.usuario_id))
        if sugestoes:
            rotulo(self, "Sugestões para você", 20, True, largura=700).pack(anchor="w", padx=24, pady=(14, 4))
            for registro, motivo in sugestoes:
                item = cartao(self)
                item.pack(fill="x", padx=24, pady=4)
                topo = transparente(item)
                topo.pack(fill="x", padx=16, pady=(10, 0))
                rotulo(topo, registro["tema"], 16, True, largura=520).pack(anchor="w")
                rotulo(item, motivo, 13, False, "suave", largura=600).pack(anchor="w", padx=16)
                selo_situacao(item, registro).pack(anchor="w", padx=16)
                botao(item, "Abrir", lambda i=registro["id"]: app.navegar("assistente", assunto_id=i),
                      "secundario").pack(anchor="w", padx=16, pady=(6, 12))

        aviso(self, AVISO_NAO_OFICIAL, "info", largura=700).pack(anchor="w", padx=24, pady=(14, 24))
        self.after(150, self.entrada.focus_set)

    def perguntar(self):
        texto = self.entrada.get().strip()
        self.app.navegar("assistente", pergunta=texto) if texto else self.app.navegar("assistente")
