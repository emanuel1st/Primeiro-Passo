"""Tema visual (azul e branco), tamanho de fonte e alto contraste.

As cores são lidas por `tema.cor("nome")` na hora de criar cada widget. Quando
o usuário muda fonte ou contraste, a janela é reconstruída (ver principal.py).
"""
import customtkinter as ctk

CLARO = {
    "fundo": "#F3F7FF", "cartao": "#FFFFFF", "borda": "#C7D5F0", "destaque": "#E0EAFF",
    "primaria": "#1D4ED8", "primaria_hover": "#1E40AF", "texto_primaria": "#FFFFFF",
    "texto": "#0F172A", "suave": "#475569", "link": "#1D4ED8",
    "lateral": "#1E3A8A", "lateral_texto": "#FFFFFF", "lateral_ativo": "#2F55C9",
    "ok_fundo": "#DCFCE7", "ok_texto": "#14532D",
    "alerta_fundo": "#FEF3C7", "alerta_texto": "#713F12",
    "erro_fundo": "#FEE2E2", "erro_texto": "#7F1D1D",
    "info_fundo": "#DBEAFE", "info_texto": "#1E3A8A",
    "perigo": "#B91C1C", "perigo_hover": "#991B1B",
}

CONTRASTE = {
    "fundo": "#000000", "cartao": "#000000", "borda": "#FFFFFF", "destaque": "#1F1F1F",
    "primaria": "#FFD400", "primaria_hover": "#FFE866", "texto_primaria": "#000000",
    "texto": "#FFFFFF", "suave": "#F0F0F0", "link": "#FFD400",
    "lateral": "#000000", "lateral_texto": "#FFFFFF", "lateral_ativo": "#3A3A00",
    "ok_fundo": "#000000", "ok_texto": "#7CFC9A",
    "alerta_fundo": "#000000", "alerta_texto": "#FFD400",
    "erro_fundo": "#000000", "erro_texto": "#FF8A8A",
    "info_fundo": "#000000", "info_texto": "#8AD4FF",
    "perigo": "#FF4D4D", "perigo_hover": "#FF8080",
}

ESCALAS = {"Normal (100%)": 1.0, "Grande (125%)": 1.25, "Muito grande (150%)": 1.5}
ESCALA_MIN, ESCALA_MAX = 1.0, 1.5


class _Tema:
    def __init__(self):
        self.escala = 1.0
        self.alto_contraste = False
        self._cores = dict(CLARO)

    def aplicar(self, escala: float = 1.0, alto_contraste: bool = False) -> None:
        self.escala = min(max(float(escala), ESCALA_MIN), ESCALA_MAX)
        self.alto_contraste = bool(alto_contraste)
        self._cores = dict(CONTRASTE if self.alto_contraste else CLARO)
        ctk.set_appearance_mode("dark" if self.alto_contraste else "light")

    def cor(self, nome: str) -> str:
        return self._cores[nome]

    def fonte(self, tamanho: int = 14, negrito: bool = False) -> "ctk.CTkFont":
        return ctk.CTkFont(family="Segoe UI", size=max(10, int(round(tamanho * self.escala))),
                           weight="bold" if negrito else "normal")

    def px(self, valor: int) -> int:
        """Escala uma medida (altura de botão etc.) junto com a fonte."""
        return int(round(valor * self.escala))


tema = _Tema()
