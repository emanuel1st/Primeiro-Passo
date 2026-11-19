"""Tela do assistente: pergunta, resposta, fontes, explicação, relacionados e trilha."""
import queue
import threading

import customtkinter as ctk

from interface.componentes import (STATUS_ROTULOS, abrir_link, aviso, botao, caixa_texto, cartao, rotulo,
                                   selo_situacao, titulo_pagina, transparente)
from interface.pagina import Pagina
from interface.tema import tema
from services.templates import NOMES

EXEMPLOS = ["Como faço minha carteira de trabalho?", "Quais documentos preciso para o título de eleitor?",
            "Como funciona o FGTS?"]
TODAS = "Todas as categorias"


class PaginaAssistente(Pagina):
    def __init__(self, master, app, pergunta=None, assunto_id=None, resposta=None, **_):
        super().__init__(master, app)
        ctx = self.ctx
        self._fila = queue.Queue()
        self._ocupado = False
        self._por_nome_template = {nome: chave for chave, nome in NOMES.items()}
        self._cat_por_nome = {c["nome"]: c["id"] for c in ctx.base.categorias}

        titulo_pagina(self, "Assistente",
                      "Pergunte com suas palavras. A resposta vem da base local e sempre mostra a fonte oficial.")

        # --- opções ---------------------------------------------------------
        opcoes = transparente(self)
        opcoes.pack(fill="x", padx=24, pady=(0, 6))
        self.var_template = ctk.StringVar(value=NOMES.get(ctx.template_padrao, NOMES["A"]))
        ctk.CTkSegmentedButton(opcoes, values=list(NOMES.values()), variable=self.var_template,
                               font=tema.fonte(13), selected_color=tema.cor("primaria"),
                               selected_hover_color=tema.cor("primaria_hover"),
                               text_color=tema.cor("texto_primaria"), unselected_color=tema.cor("destaque"),
                               unselected_hover_color=tema.cor("borda")).pack(side="left", padx=(0, 12))
        self.var_categoria = ctk.StringVar(value=TODAS)
        ctk.CTkOptionMenu(opcoes, values=[TODAS] + list(self._cat_por_nome), variable=self.var_categoria,
                          font=tema.fonte(13), dropdown_font=tema.fonte(13), width=tema.px(260),
                          fg_color=tema.cor("primaria"), button_color=tema.cor("primaria_hover"),
                          text_color=tema.cor("texto_primaria")).pack(side="left", padx=(0, 12))
        ia_ok = ctx.assistente.ia_disponivel
        self.var_ia = ctk.BooleanVar(value=bool(ctx.prefs.get("usar_ia")) and ia_ok)
        ctk.CTkSwitch(opcoes, text="Usar IA externa" if ia_ok else "IA externa (não configurada)",
                      variable=self.var_ia, state="normal" if ia_ok else "disabled", font=tema.fonte(13),
                      text_color=tema.cor("texto"), progress_color=tema.cor("primaria")).pack(side="left")

        # --- pergunta -------------------------------------------------------
        linha = transparente(self)
        linha.pack(fill="x", padx=24, pady=6)
        self.entrada = ctk.CTkEntry(linha, height=tema.px(44), font=tema.fonte(15), fg_color=tema.cor("cartao"),
                                    text_color=tema.cor("texto"), border_color=tema.cor("borda"),
                                    placeholder_text="Digite sua dúvida e aperte Enter")
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entrada.bind("<Return>", lambda _e: self.perguntar())
        self.botao_perguntar = botao(linha, "Perguntar", self.perguntar)
        self.botao_perguntar.pack(side="right")

        exemplos = transparente(self)
        exemplos.pack(fill="x", padx=24)
        rotulo(exemplos, "Exemplos:", 13, False, "suave", largura=100).pack(side="left", padx=(0, 6))
        for texto in EXEMPLOS:
            botao(exemplos, texto, lambda t=texto: self.usar_exemplo(t), "link").pack(side="left", padx=2)

        self.area = transparente(self)
        self.area.pack(fill="x", padx=24, pady=(10, 24))

        if resposta is not None:
            self.mostrar(resposta)
        elif assunto_id:
            self._concluir(ctx.assistente.responder_por_id(assunto_id, self._template()))
        elif pergunta:
            self.entrada.insert(0, pergunta)
            self.perguntar()
        self.after(150, self.entrada.focus_set)

    # --- leitura das opções ---------------------------------------------------
    def _template(self) -> str:
        return self._por_nome_template.get(self.var_template.get(), "A")

    def _categoria(self):
        return self._cat_por_nome.get(self.var_categoria.get())

    def usar_exemplo(self, texto: str):
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)
        self.perguntar()

    # --- perguntar (com IA em segundo plano) --------------------------------
    def perguntar(self, escolha_id=None):
        if self._ocupado:
            return
        texto = self.entrada.get()
        template, categoria = self._template(), self._categoria()
        usar_ia = bool(self.var_ia.get()) and self.ctx.assistente.ia_disponivel and bool(texto.strip())
        if not usar_ia:
            self._concluir(self.ctx.assistente.responder(texto, template, categoria, False, escolha_id))
            return
        self._ocupado = True
        self.botao_perguntar.configure(state="disabled", text="Pensando…")
        self.limpar(self.area)
        aviso(self.area, "Consultando a IA… se ela demorar ou falhar, uso a busca local.", "info").pack(anchor="w")
        threading.Thread(target=self._trabalhar, args=(texto, template, categoria, escolha_id), daemon=True).start()
        self.after(150, self._checar)

    def _trabalhar(self, texto, template, categoria, escolha_id):
        """Roda fora da thread da tela. Não mexe em widgets nem no banco."""
        try:
            self._fila.put(("ok", self.ctx.assistente.responder(texto, template, categoria, True, escolha_id)))
        except Exception as erro:
            self._fila.put(("erro", erro))

    def _checar(self):
        if not self.winfo_exists():
            return
        try:
            tipo, valor = self._fila.get_nowait()
        except queue.Empty:
            self.after(150, self._checar)
            return
        self._ocupado = False
        self.botao_perguntar.configure(state="normal", text="Perguntar")
        if tipo == "erro":
            self.limpar(self.area)
            aviso(self.area, "Não consegui responder agora. Tente de novo.", "erro").pack(anchor="w")
        else:
            self._concluir(valor)

    def _concluir(self, resposta):
        self._registrar(resposta)
        self.mostrar(resposta)

    def _registrar(self, resposta):
        if resposta.status in ("vazia", "invalida"):
            return
        try:
            self.ctx.repo.registrar_historico(self.ctx.usuario_id, resposta.pergunta, resposta.texto,
                                              resposta.status, resposta.template, resposta.ids_principais,
                                              resposta.usou_ia)
        except Exception:  # histórico é um extra: se falhar, a resposta ainda aparece
            import sys
            import traceback
            traceback.print_exc(file=sys.stderr)

    # --- exibição --------------------------------------------------------------
    def mostrar(self, resposta):
        self.limpar(self.area)
        area = self.area
        tipo = {"ok": "ok", "multipla": "info", "ambigua": "alerta", "sem_resultado": "alerta",
                "vazia": "alerta", "invalida": "alerta"}[resposta.status]
        if resposta.status in ("vazia", "invalida"):
            aviso(area, resposta.texto, "alerta").pack(anchor="w")
            return
        rotulo(area, STATUS_ROTULOS[resposta.status], 13, True, f"{tipo}_texto" if tipo != "alerta" else "alerta_texto",
               largura=500).pack(anchor="w", pady=(0, 4))
        caixa_texto(area, resposta.texto).pack(fill="x")
        if resposta.aviso_ia:
            aviso(area, resposta.aviso_ia, "alerta").pack(anchor="w", pady=(8, 0))
        if resposta.usou_ia:
            aviso(area, "Texto reescrito por IA a partir da base local. Fontes e datas vêm da base. "
                        "Confira sempre na fonte oficial.", "info").pack(anchor="w", pady=(8, 0))
        if resposta.tem_pendencia:
            aviso(area, "Este assunto ainda não foi totalmente validado. Confirme no site oficial antes de agir.",
                  "alerta").pack(anchor="w", pady=(8, 0))

        if resposta.status == "ambigua":
            rotulo(area, "Escolha o assunto:", 15, True, largura=500).pack(anchor="w", pady=(12, 4))
            for reg in resposta.alternativas:
                botao(area, f"{reg['tema']}  ·  {self.ctx.base.nome_categoria(reg['categoria'])}",
                      lambda i=reg["id"]: self.perguntar(escolha_id=i), "secundario").pack(anchor="w", pady=3)

        if resposta.principais:
            self._acoes(area, resposta)
        if resposta.relacionados:
            rotulo(area, "Veja também:", 15, True, largura=500).pack(anchor="w", pady=(14, 4))
            linha = transparente(area)
            linha.pack(anchor="w")
            for reg in resposta.relacionados:
                botao(linha, reg["tema"], lambda i=reg["id"]: self.app.navegar("assistente", assunto_id=i),
                      "secundario").pack(side="left", padx=(0, 6), pady=2)
        if resposta.principais:
            self._trilha(area, resposta.principais[0]["id"])
        if resposta.explicacao:
            self._explicacao(area, resposta)

    def _acoes(self, area, resposta):
        rotulo(area, "Fontes oficiais e ações:", 15, True, largura=500).pack(anchor="w", pady=(14, 4))
        for reg in resposta.principais:
            quadro = cartao(area)
            quadro.pack(fill="x", pady=4)
            rotulo(quadro, reg["tema"], 15, True, largura=560).pack(anchor="w", padx=14, pady=(10, 0))
            selo_situacao(quadro, reg).pack(anchor="w", padx=14)
            botoes = transparente(quadro)
            botoes.pack(anchor="w", padx=10, pady=(4, 10))
            for fonte in reg["fontes"]:
                botao(botoes, f"🔗 {fonte['nome']}", lambda u=fonte["url"]: self._abrir(u), "link").pack(
                    side="left", padx=2)
            self._botao_favorito(botoes, reg["id"]).pack(side="left", padx=2)
        botao(area, "📋 Copiar resposta", lambda: self._copiar(resposta.texto), "secundario").pack(
            anchor="w", pady=(8, 0))
        self.msg_acao = rotulo(area, "", 13, True, "ok_texto", largura=560)
        self.msg_acao.pack(anchor="w")

    def _botao_favorito(self, pai, registro_id):
        repo, uid = self.ctx.repo, self.ctx.usuario_id

        def texto():
            return "★ Remover dos favoritos" if repo.eh_favorito(uid, registro_id) else "☆ Favoritar"

        def alternar():
            repo.alternar_favorito(uid, registro_id)
            botao_fav.configure(text=texto())

        botao_fav = botao(pai, texto(), alternar, "secundario")
        return botao_fav

    def _abrir(self, url):
        if not abrir_link(url):
            self._copiar(url)
            self.msg_acao.configure(text="Não consegui abrir o navegador. Copiei o endereço: " + url)

    def _copiar(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        if hasattr(self, "msg_acao"):
            self.msg_acao.configure(text="Copiado.")

    def _trilha(self, area, registro_id):
        rota = self.ctx.grafo.rota_sugerida(registro_id)
        if len(rota) < 2:
            return
        rotulo(area, "Trilha sugerida (siga em ordem ou escolha):", 15, True, largura=560).pack(anchor="w", pady=(14, 4))
        linha = transparente(area)
        linha.pack(anchor="w")
        for posicao, rid in enumerate(rota, start=1):
            reg = self.ctx.base.por_id.get(rid)
            if reg is None:
                continue
            atual = rid == registro_id
            botao(linha, f"{posicao}. {reg['tema']}" + ("  (você está aqui)" if atual else ""),
                  lambda i=rid: self.app.navegar("assistente", assunto_id=i),
                  "primario" if atual else "secundario").pack(anchor="w", pady=2)

    def _explicacao(self, area, resposta):
        quadro = transparente(area)
        painel = transparente(area)
        estado = {"aberto": False}

        def alternar():
            if estado["aberto"]:
                self.limpar(painel)
                alternar_botao.configure(text="❔ Por que esta resposta?")
            else:
                texto = "\n".join(resposta.explicacao) + f"\n\nTempo de busca: {resposta.tempo_ms:.2f} ms"
                caixa_texto(painel, texto, 13).pack(fill="x", pady=(6, 0))
                alternar_botao.configure(text="▲ Esconder explicação")
            estado["aberto"] = not estado["aberto"]

        alternar_botao = botao(quadro, "❔ Por que esta resposta?", alternar, "secundario")
        alternar_botao.pack(anchor="w", pady=(14, 0))
        quadro.pack(anchor="w")
        painel.pack(fill="x")
