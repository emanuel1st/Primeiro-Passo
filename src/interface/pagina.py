"""Classe-base das telas internas (área rolável com acesso ao app e ao contexto)."""
import customtkinter as ctk

from interface.tema import tema


class Pagina(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_params):
        super().__init__(master, fg_color=tema.cor("fundo"), corner_radius=0)
        self.app = app
        self.ctx = app.ctx

    def limpar(self, quadro) -> None:
        for filho in quadro.winfo_children():
            filho.destroy()
