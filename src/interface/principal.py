"""Janela principal: menu lateral, troca de telas e atalhos de teclado."""
import sys
import traceback
from tkinter import messagebox

import customtkinter as ctk

from config import AVISO_NAO_OFICIAL, NOME_APP, SLOGAN
from interface.area_usuario import PaginaChecklists, PaginaFavoritos, PaginaHistorico, PaginaProgresso
from interface.assistente import PaginaAssistente
from interface.categorias import PaginaCategorias
from interface.componentes import aviso, botao, primeiro_nome
from interface.configuracoes import PaginaConfiguracoes
from interface.login import TelaLogin
from interface.oportunidades import PaginaOportunidades
from interface.painel import PaginaPainel
from interface.tema import ESCALA_MAX, ESCALA_MIN, tema

# (chave, texto do menu, classe da tela). A ordem define os atalhos Ctrl+1 ... Ctrl+9.
TELAS = [
    ("painel", "🏠  Início", PaginaPainel),
    ("assistente", "💬  Assistente", PaginaAssistente),
    ("categorias", "🗂  Categorias", PaginaCategorias),
    ("oportunidades", "🎯  Oportunidades", PaginaOportunidades),
    ("historico", "🕘  Histórico", PaginaHistorico),
    ("favoritos", "⭐  Favoritos", PaginaFavoritos),
    ("checklists", "✅  Checklists", PaginaChecklists),
    ("progresso", "📈  Progresso", PaginaProgresso),
    ("configuracoes", "⚙  Configurações", PaginaConfiguracoes),
]


class Aplicativo(ctk.CTk):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.title(f"{NOME_APP} - {SLOGAN}")
        self.geometry("1180x760")
        self.minsize(960, 620)
        self._raiz = None
        self._conteudo = None
        self._botoes = {}
        self._atual = "painel"
        self.report_callback_exception = self._erro_inesperado
        self._ligar_atalhos()
        self.mostrar_login()

    # --- atalhos ------------------------------------------------------------
    def _ligar_atalhos(self):
        for numero, (chave, *_resto) in enumerate(TELAS, start=1):
            self.bind_all(f"<Control-Key-{numero}>", lambda _e, c=chave: self.navegar(c))
        for sequencia, passo in (("<Control-plus>", 0.25), ("<Control-equal>", 0.25), ("<Control-minus>", -0.25)):
            self.bind_all(sequencia, lambda _e, p=passo: self.ajustar_fonte(p))
        self.bind_all("<Control-q>", lambda _e: self.sair() if self.ctx.usuario else None)

    def ajustar_fonte(self, passo: float):
        if not self.ctx.usuario:
            return
        nova = min(max(tema.escala + passo, ESCALA_MIN), ESCALA_MAX)
        if abs(nova - tema.escala) < 0.01:
            return
        self.ctx.salvar_pref(fonte_escala=nova)
        tema.aplicar(nova, tema.alto_contraste)
        self.montar(self._atual)

    # --- sessão -------------------------------------------------------------
    def mostrar_login(self):
        self._trocar_raiz()
        tema.aplicar(1.0, False)
        self.configure(fg_color=tema.cor("fundo"))
        self._raiz = TelaLogin(self, self)
        self._raiz.pack(fill="both", expand=True)

    def entrar(self, usuario: dict):
        self.ctx.iniciar_sessao(usuario)
        tema.aplicar(self.ctx.prefs.get("fonte_escala", 1.0), bool(self.ctx.prefs.get("alto_contraste", 0)))
        self.montar("painel")

    def sair(self):
        self.ctx.encerrar_sessao()
        self.mostrar_login()

    # --- montagem -----------------------------------------------------------
    def _trocar_raiz(self):
        if self._raiz is not None:
            self._raiz.destroy()
            self._raiz = None
        self._botoes = {}

    def montar(self, tela: str = "painel", **params):
        """(Re)constrói menu e conteúdo. Usado ao entrar e ao mudar fonte/contraste."""
        self._trocar_raiz()
        self.configure(fg_color=tema.cor("fundo"))
        raiz = ctk.CTkFrame(self, fg_color=tema.cor("fundo"), corner_radius=0)
        raiz.pack(fill="both", expand=True)
        raiz.grid_columnconfigure(1, weight=1)
        raiz.grid_rowconfigure(0, weight=1)
        self._raiz = raiz

        lateral = ctk.CTkFrame(raiz, fg_color=tema.cor("lateral"), corner_radius=0, width=tema.px(230))
        lateral.grid(row=0, column=0, sticky="nsw")
        lateral.grid_propagate(False)
        ctk.CTkLabel(lateral, text=f"🧭 {NOME_APP}", font=tema.fonte(20, True),
                     text_color=tema.cor("lateral_texto")).pack(anchor="w", padx=16, pady=(18, 0))
        ctk.CTkLabel(lateral, text=f"Olá, {primeiro_nome(self.ctx.usuario['nome'])}", font=tema.fonte(13),
                     text_color=tema.cor("lateral_texto"), wraplength=tema.px(190), justify="left").pack(
            anchor="w", padx=16, pady=(2, 12))
        for chave, texto, *_resto in TELAS:
            botao_menu = ctk.CTkButton(
                lateral, text=texto, anchor="w", command=lambda c=chave: self.navegar(c),
                font=tema.fonte(14), height=tema.px(38), corner_radius=8, fg_color="transparent",
                text_color=tema.cor("lateral_texto"), hover_color=tema.cor("lateral_ativo"),
                border_width=1 if tema.alto_contraste else 0, border_color=tema.cor("lateral_texto"))
            botao_menu.pack(fill="x", padx=10, pady=2)
            self._botoes[chave] = botao_menu
        ctk.CTkButton(lateral, text="⎋  Sair", anchor="w", command=self.sair, font=tema.fonte(14),
                      height=tema.px(38), corner_radius=8, fg_color=tema.cor("lateral_ativo"),
                      text_color=tema.cor("lateral_texto"), hover_color=tema.cor("primaria_hover")).pack(
            side="bottom", fill="x", padx=10, pady=14)
        ctk.CTkLabel(lateral, text="Atalhos: Ctrl+1…9 trocam de tela\nCtrl + / Ctrl − mudam a fonte",
                     font=tema.fonte(11), text_color=tema.cor("lateral_texto"), justify="left").pack(
            side="bottom", anchor="w", padx=16)

        direita = ctk.CTkFrame(raiz, fg_color=tema.cor("fundo"), corner_radius=0)
        direita.grid(row=0, column=1, sticky="nsew")
        direita.grid_rowconfigure(0, weight=1)
        direita.grid_columnconfigure(0, weight=1)
        self._conteudo = ctk.CTkFrame(direita, fg_color=tema.cor("fundo"), corner_radius=0)
        self._conteudo.grid(row=0, column=0, sticky="nsew")
        rodape = ctk.CTkLabel(direita, text="Plataforma independente. Não é um serviço oficial do Governo Federal.",
                              font=tema.fonte(11), text_color=tema.cor("suave"))
        rodape.grid(row=1, column=0, sticky="ew", pady=4)
        self.navegar(tela, **params)

    def navegar(self, tela: str, **params):
        if not self.ctx.usuario or self._conteudo is None:
            return
        conhecidas = {t[0]: t for t in TELAS}
        if tela not in conhecidas:
            tela = "painel"
        for filho in self._conteudo.winfo_children():
            filho.destroy()
        self._atual = tela
        for chave, botao_menu in self._botoes.items():
            botao_menu.configure(fg_color=tema.cor("lateral_ativo") if chave == tela else "transparent")
        classe = conhecidas[tela][2]
        try:
            pagina = classe(self._conteudo, self, **params)
        except Exception:  # uma tela com defeito não pode derrubar o app inteiro
            traceback.print_exc(file=sys.stderr)
            quadro = ctk.CTkFrame(self._conteudo, fg_color="transparent")
            quadro.pack(fill="both", expand=True, padx=24, pady=24)
            aviso(quadro, "Não consegui abrir esta tela. Tente voltar ao Início. O detalhe técnico foi "
                          "escrito no terminal.", "erro").pack(anchor="w")
            botao(quadro, "Voltar ao Início", lambda: self.navegar("painel")).pack(anchor="w", pady=12)
            return
        pagina.pack(fill="both", expand=True)

    def _erro_inesperado(self, tipo, valor, tb):
        traceback.print_exception(tipo, valor, tb, file=sys.stderr)
        try:
            messagebox.showerror(NOME_APP, "Algo deu errado, mas seus dados estão salvos. "
                                           "Tente de novo ou volte ao Início.")
        except Exception:
            pass
