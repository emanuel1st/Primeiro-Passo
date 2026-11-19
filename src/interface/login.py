"""Tela de entrada: login e cadastro. Não coleta CPF nem endereço."""
import customtkinter as ctk

from config import AVISO_NAO_OFICIAL, NOME_APP, SLOGAN
from database.operacoes import ErroDados
from interface.componentes import aviso, botao, cartao, rotulo, transparente
from interface.tema import tema


class TelaLogin(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=tema.cor("fundo"), corner_radius=0)
        self.app = app
        self.ctx = app.ctx

        centro = ctk.CTkScrollableFrame(self, fg_color="transparent")
        centro.pack(fill="both", expand=True)
        miolo = transparente(centro)
        miolo.pack(pady=30)
        rotulo(miolo, f"🧭 {NOME_APP}", 34, True, "link", largura=520).pack(anchor="center")
        rotulo(miolo, SLOGAN, 16, False, "suave", largura=520).pack(anchor="center", pady=(0, 14))

        caixa = cartao(miolo)
        caixa.pack(padx=10)
        abas = ctk.CTkTabview(caixa, width=tema.px(460), height=tema.px(430), fg_color=tema.cor("cartao"),
                              segmented_button_selected_color=tema.cor("primaria"),
                              segmented_button_selected_hover_color=tema.cor("primaria_hover"),
                              text_color=tema.cor("texto_primaria"))
        abas.pack(padx=18, pady=18)
        self._abas = abas
        self._montar_entrar(abas.add("Entrar"))
        self._montar_cadastro(abas.add("Criar conta"))

        aviso(miolo, AVISO_NAO_OFICIAL, "info", largura=520).pack(pady=(16, 0))
        self.after(150, self.e_email.focus_set)

    # --- campos -----------------------------------------------------------
    def _campo(self, pai, texto, senha=False):
        rotulo(pai, texto, 14, True, largura=420).pack(anchor="w", pady=(8, 2))
        campo = ctk.CTkEntry(pai, width=tema.px(400), height=tema.px(40), font=tema.fonte(14),
                             show="•" if senha else "", fg_color=tema.cor("cartao"),
                             text_color=tema.cor("texto"), border_color=tema.cor("borda"))
        campo.pack(anchor="w")
        return campo

    def _mensagem(self, pai):
        rot = rotulo(pai, "", 13, True, "erro_texto", largura=420)
        rot.pack(anchor="w", pady=(8, 0))
        return rot

    def _montar_entrar(self, aba):
        self.e_email = self._campo(aba, "E-mail")
        self.e_senha = self._campo(aba, "Senha", senha=True)
        self.var_ver = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(aba, text="Mostrar senha", variable=self.var_ver, font=tema.fonte(13),
                        text_color=tema.cor("texto"), command=self._alternar_senha).pack(anchor="w", pady=(8, 0))
        self.msg_entrar = self._mensagem(aba)
        botao(aba, "Entrar", self.entrar, width=tema.px(400)).pack(anchor="w", pady=(6, 0))
        for campo in (self.e_email, self.e_senha):
            campo.bind("<Return>", lambda _e: self.entrar())

    def _montar_cadastro(self, aba):
        self.c_nome = self._campo(aba, "Nome")
        self.c_email = self._campo(aba, "E-mail")
        self.c_senha = self._campo(aba, "Senha (mínimo 8 caracteres, com letras e números)", senha=True)
        self.c_conf = self._campo(aba, "Repita a senha", senha=True)
        self.msg_cadastro = self._mensagem(aba)
        botao(aba, "Criar conta", self.cadastrar, width=tema.px(400)).pack(anchor="w", pady=(6, 0))
        rotulo(aba, "Pedimos só nome, e-mail e senha. Não pedimos CPF nem endereço.", 12, False, "suave",
               largura=420).pack(anchor="w", pady=(8, 0))
        for campo in (self.c_nome, self.c_email, self.c_senha, self.c_conf):
            campo.bind("<Return>", lambda _e: self.cadastrar())

    def _alternar_senha(self):
        self.e_senha.configure(show="" if self.var_ver.get() else "•")

    # --- ações ------------------------------------------------------------
    def entrar(self):
        try:
            usuario = self.ctx.repo.autenticar(self.e_email.get(), self.e_senha.get())
        except ErroDados as erro:
            self.msg_entrar.configure(text=f"✖ {erro}")
            return
        self.app.entrar(usuario)

    def cadastrar(self):
        from utils.validacao import validar_cadastro
        erros = validar_cadastro(self.c_nome.get(), self.c_email.get(), self.c_senha.get(), self.c_conf.get())
        if erros:
            self.msg_cadastro.configure(text="✖ " + " ".join(erros))
            return
        try:
            self.ctx.repo.cadastrar_usuario(self.c_nome.get(), self.c_email.get(), self.c_senha.get())
            usuario = self.ctx.repo.autenticar(self.c_email.get(), self.c_senha.get())
        except ErroDados as erro:
            self.msg_cadastro.configure(text=f"✖ {erro}")
            return
        self.app.entrar(usuario)
