"""Contexto compartilhado pelas telas: base, busca, banco e usuário logado.

Não depende de CustomTkinter, então pode ser criado (e testado) sem janela.
"""
import config
from database.conexao import abrir_conexao
from database.operacoes import Repositorio
from services.assistente import Assistente
from services.busca import MotorBusca
from services.checklists import carregar_modelos
from services.conhecimento import BaseConhecimento, carregar_sinonimos
from services.grafo import GrafoAssuntos
from services.ia import ClienteIA
from services.recomendacoes import carregar_oportunidades


class Contexto:
    def __init__(self, base, assistente, grafo, repo, oportunidades, modelos_checklist):
        self.base = base
        self.assistente = assistente
        self.grafo = grafo
        self.repo = repo
        self.oportunidades = oportunidades
        self.modelos_checklist = modelos_checklist
        self.usuario = None
        self.prefs = {}

    @classmethod
    def criar(cls, caminho_banco=None, cliente_ia=None) -> "Contexto":
        config.carregar_env()
        base = BaseConhecimento.carregar()
        motor = MotorBusca(base.registros, carregar_sinonimos())
        grafo = GrafoAssuntos(base.registros, base.trilhas)
        cliente = cliente_ia if cliente_ia is not None else ClienteIA()
        assistente = Assistente(base, motor, grafo, cliente)
        repo = Repositorio(abrir_conexao(caminho_banco))
        return cls(base, assistente, grafo, repo, carregar_oportunidades(base), carregar_modelos())

    # --- sessão ----------------------------------------------------------
    @property
    def usuario_id(self) -> int:
        return self.usuario["id"]

    def iniciar_sessao(self, usuario: dict) -> None:
        self.usuario = usuario
        self.repo.garantir_checklists(usuario["id"], self.modelos_checklist)
        self.prefs = self.repo.obter_preferencias(usuario["id"])

    def encerrar_sessao(self) -> None:
        self.usuario = None
        self.prefs = {}

    def salvar_pref(self, **campos) -> None:
        self.repo.salvar_preferencias(self.usuario_id, **campos)
        self.prefs = self.repo.obter_preferencias(self.usuario_id)

    @property
    def template_padrao(self) -> str:
        return self.prefs.get("template_padrao", "A")

    def resumo(self) -> dict:
        """Dados para o comando `--verificar` (sem abrir janela)."""
        return {
            "conhecimentos": self.base.estatisticas(),
            "erros_na_base": list(self.base.erros),
            "oportunidades": len(self.oportunidades),
            "checklists_modelo": len(self.modelos_checklist),
            "ia_configurada": self.assistente.ia_disponivel,
        }
