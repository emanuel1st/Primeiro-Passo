"""Configurações: acessibilidade, IA, conta e informações sobre o app."""
import customtkinter as ctk
from tkinter import messagebox

import config
from database.operacoes import ErroDados
from interface.componentes import aviso, botao, cartao, rotulo, titulo_pagina, transparente
from interface.pagina import Pagina
from interface.tema import ESCALAS, tema
from services.templates import NOMES
from utils.validacao import validar_nome


def _campo(pai, texto, senha=False, valor=""):
    rotulo(pai, texto, 14, True, largura=420).pack(anchor="w", pady=(8, 2))
    campo = ctk.CTkEntry(pai, width=tema.px(360), height=tema.px(38), font=tema.fonte(14), show="•" if senha else "",
                         fg_color=tema.cor("cartao"), text_color=tema.cor("texto"), border_color=tema.cor("borda"))
    campo.pack(anchor="w")
    if valor:
        campo.insert(0, valor)
    return campo


class PaginaConfiguracoes(Pagina):
    def __init__(self, master, app, **_):
        super().__init__(master, app)
        ctx = self.ctx
        titulo_pagina(self, "Configurações", "Deixe o aplicativo do seu jeito.")
        prefs = ctx.prefs

        # --- aparência e acessibilidade ----------------------------------------
        caixa = self._secao("Aparência e acessibilidade")
        rotulo(caixa, "Tamanho da letra (também: Ctrl + e Ctrl −)", 14, True, largura=500).pack(anchor="w", padx=18)
        atual = min(ESCALAS, key=lambda nome: abs(ESCALAS[nome] - float(prefs.get("fonte_escala", 1.0))))
        self.var_fonte = ctk.StringVar(value=atual)
        ctk.CTkSegmentedButton(caixa, values=list(ESCALAS), variable=self.var_fonte, font=tema.fonte(13),
                               selected_color=tema.cor("primaria"), selected_hover_color=tema.cor("primaria_hover"),
                               text_color=tema.cor("texto_primaria"), unselected_color=tema.cor("destaque"),
                               unselected_hover_color=tema.cor("borda")).pack(anchor="w", padx=18, pady=(4, 10))
        self.var_contraste = ctk.BooleanVar(value=bool(prefs.get("alto_contraste")))
        ctk.CTkSwitch(caixa, text="Alto contraste (fundo preto, letras claras)", variable=self.var_contraste,
                      font=tema.fonte(14), text_color=tema.cor("texto"), progress_color=tema.cor("primaria")).pack(
            anchor="w", padx=18, pady=(0, 10))

        # --- respostas -----------------------------------------------------------
        rotulo(caixa, "Formato padrão das respostas", 14, True, largura=500).pack(anchor="w", padx=18)
        self.var_template = ctk.StringVar(value=NOMES.get(prefs.get("template_padrao", "A"), NOMES["A"]))
        ctk.CTkSegmentedButton(caixa, values=list(NOMES.values()), variable=self.var_template, font=tema.fonte(13),
                               selected_color=tema.cor("primaria"), selected_hover_color=tema.cor("primaria_hover"),
                               text_color=tema.cor("texto_primaria"), unselected_color=tema.cor("destaque"),
                               unselected_hover_color=tema.cor("borda")).pack(anchor="w", padx=18, pady=(4, 10))
        ia_ok = ctx.assistente.ia_disponivel
        self.var_ia = ctk.BooleanVar(value=bool(prefs.get("usar_ia")) and ia_ok)
        ctk.CTkSwitch(caixa, text="Usar IA externa por padrão", variable=self.var_ia,
                      state="normal" if ia_ok else "disabled", font=tema.fonte(14), text_color=tema.cor("texto"),
                      progress_color=tema.cor("primaria")).pack(anchor="w", padx=18, pady=(0, 6))
        if ia_ok:
            rotulo(caixa, f"IA configurada (modelo {config.modelo_ia()}). Ela só reescreve o que está na base local; "
                          "se falhar, o app usa a busca local.", 13, False, "suave", largura=560).pack(anchor="w", padx=18)
        else:
            rotulo(caixa, "IA externa não configurada. O aplicativo funciona normalmente sem ela. Para ativar, "
                          "veja docs/uso_ia.md (chave em variável de ambiente ou no arquivo .env).", 13, False, "suave",
                   largura=560).pack(anchor="w", padx=18)
        botao(caixa, "Salvar e aplicar", self.salvar_preferencias).pack(anchor="w", padx=18, pady=14)

        # --- conta ---------------------------------------------------------------
        conta = self._secao("Minha conta")
        rotulo(conta, f"E-mail: {ctx.usuario['email']}", 14, False, "suave", largura=500).pack(anchor="w", padx=18)
        corpo = transparente(conta)
        corpo.pack(anchor="w", padx=18)
        self.e_nome = _campo(corpo, "Nome", valor=ctx.usuario["nome"])
        botao(corpo, "Salvar nome", self.salvar_nome, "secundario").pack(anchor="w", pady=(8, 0))
        self.e_atual = _campo(corpo, "Senha atual", senha=True)
        self.e_nova = _campo(corpo, "Nova senha (mínimo 8, com letras e números)", senha=True)
        botao(corpo, "Trocar senha", self.trocar_senha, "secundario").pack(anchor="w", pady=(8, 0))
        self.msg = rotulo(corpo, "", 13, True, "ok_texto", largura=500)
        self.msg.pack(anchor="w", pady=(8, 0))
        botao(conta, "Excluir minha conta e todos os meus dados", self.excluir_conta, "perigo").pack(
            anchor="w", padx=18, pady=14)

        # --- sobre ---------------------------------------------------------------
        sobre = self._secao("Sobre")
        est = ctx.base.estatisticas()
        rotulo(sobre, f"Base local: {est['total']} assuntos em {est['categorias']} categorias "
                      f"({est['verificado']} verificados, {est['pendente_validacao']} pendentes de validação).",
               14, False, largura=600).pack(anchor="w", padx=18)
        if ctx.base.erros:
            aviso(sobre, f"{len(ctx.base.erros)} problema(s) na base foram ignorados. Veja o terminal.", "alerta",
                  largura=560).pack(anchor="w", padx=18, pady=6)
        rotulo(sobre, config.AVISO_NAO_OFICIAL, 13, False, "suave", largura=600).pack(anchor="w", padx=18, pady=(6, 14))
        transparente(self, height=20).pack()

    def _secao(self, titulo):
        rotulo(self, titulo, 19, True, largura=500).pack(anchor="w", padx=24, pady=(14, 4))
        caixa = cartao(self)
        caixa.pack(fill="x", padx=24, pady=(0, 4))
        transparente(caixa, height=8).pack()
        return caixa

    # --- ações ---------------------------------------------------------------
    def salvar_preferencias(self):
        por_nome = {nome: chave for chave, nome in NOMES.items()}
        escala = ESCALAS[self.var_fonte.get()]
        contraste = bool(self.var_contraste.get())
        self.ctx.salvar_pref(fonte_escala=escala, alto_contraste=int(contraste), usar_ia=int(bool(self.var_ia.get())),
                             template_padrao=por_nome[self.var_template.get()])
        tema.aplicar(escala, contraste)
        self.app.montar("configuracoes")  # reconstrói tudo com a nova fonte/contraste

    def salvar_nome(self):
        erros = validar_nome(self.e_nome.get())
        if erros:
            self.msg.configure(text="✖ " + " ".join(erros), text_color=tema.cor("erro_texto"))
            return
        try:
            self.ctx.repo.alterar_nome(self.ctx.usuario_id, self.e_nome.get())
        except ErroDados as erro:
            self.msg.configure(text=f"✖ {erro}", text_color=tema.cor("erro_texto"))
            return
        self.ctx.usuario["nome"] = self.e_nome.get().strip()
        self.app.montar("configuracoes")

    def trocar_senha(self):
        try:
            self.ctx.repo.alterar_senha(self.ctx.usuario_id, self.e_atual.get(), self.e_nova.get())
        except ErroDados as erro:
            self.msg.configure(text=f"✖ {erro}", text_color=tema.cor("erro_texto"))
            return
        self.e_atual.delete(0, "end")
        self.e_nova.delete(0, "end")
        self.msg.configure(text="✔ Senha alterada.", text_color=tema.cor("ok_texto"))

    def excluir_conta(self):
        if messagebox.askyesno("Excluir conta", "Isso apaga sua conta, histórico, favoritos e checklists. "
                                                "Não dá para desfazer. Continuar?", icon="warning"):
            self.ctx.repo.excluir_conta(self.ctx.usuario_id)
            self.app.sair()
