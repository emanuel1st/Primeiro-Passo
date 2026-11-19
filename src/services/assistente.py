"""Assistente: valida a pergunta, busca, decide o que mostrar e monta a resposta.

Estados possíveis (`Resposta.status`):
  ok            um assunto claramente melhor que os outros
  multipla      dois ou três assuntos fortes que explicam partes DIFERENTES da pergunta
  ambigua       assuntos concorrendo pelas mesmas palavras (ou evidência fraca):
                o usuário escolhe
  sem_resultado nada confiável na base: o assistente diz isso e NÃO inventa
  vazia / invalida   entrada que não dá para interpretar
"""
import time
from dataclasses import dataclass, field
from itertools import combinations

from services import ia as modulo_ia
from services.busca import LIMIAR_MEDIA, MotorBusca
from services.templates import NOMES, bloco_fontes, renderizar
from utils.validacao import validar_pergunta

RAZAO_CONCORRENTE = 0.6   # quem tem >= 60% da pontuação do topo "concorre"
RAZAO_AMBIGUA = 0.75      # concorrente com >= 75% do topo e termos em comum = ambíguo
PORTAL_OFICIAL = "https://www.gov.br"


@dataclass
class Resposta:
    pergunta: str
    status: str
    texto: str
    template: str = "A"
    principais: list = field(default_factory=list)    # registros apresentados
    alternativas: list = field(default_factory=list)  # registros para escolher (ambigua)
    relacionados: list = field(default_factory=list)  # registros ligados pelo grafo
    resultados: list = field(default_factory=list)    # ResultadoBusca (todos)
    explicacao: list = field(default_factory=list)
    tempo_ms: float = 0.0
    usou_ia: bool = False
    aviso_ia: str = ""

    @property
    def ids_principais(self) -> list:
        return [r["id"] for r in self.principais]

    @property
    def tem_pendencia(self) -> bool:
        return any(r["situacao"] != "verificado" for r in self.principais)


def classificar(resultados) -> tuple:
    """Decide o status a partir dos resultados ordenados. Devolve (status, resultados_a_mostrar)."""
    if not resultados:
        return "sem_resultado", []
    topo = resultados[0]
    if topo.pontuacao < LIMIAR_MEDIA:
        return "ambigua", list(resultados[:4])  # só evidência fraca: pedir confirmação
    concorrentes = [r for r in resultados
                    if r.pontuacao >= LIMIAR_MEDIA and r.pontuacao >= RAZAO_CONCORRENTE * topo.pontuacao]
    if len(concorrentes) == 1:
        return "ok", [topo]
    if all(not (a.termos & b.termos) for a, b in combinations(concorrentes, 2)):
        return "multipla", concorrentes[:3]
    if concorrentes[1].pontuacao >= RAZAO_AMBIGUA * topo.pontuacao:
        return "ambigua", concorrentes[:4]
    return "ok", [topo]


class Assistente:
    def __init__(self, base, motor: MotorBusca, grafo, cliente_ia=None):
        self.base = base
        self.motor = motor
        self.grafo = grafo
        self.cliente_ia = cliente_ia

    @property
    def ia_disponivel(self) -> bool:
        return bool(self.cliente_ia and self.cliente_ia.disponivel())

    # ------------------------------------------------------------------
    def responder(self, pergunta, template="A", categoria=None, usar_ia=False, escolha_id=None) -> Resposta:
        inicio = time.perf_counter()
        ok, status, mensagem = validar_pergunta(pergunta)
        pergunta_txt = pergunta if isinstance(pergunta, str) else ""
        if not ok:
            return self._finalizar(Resposta(pergunta_txt, status, mensagem, template), inicio)

        if escolha_id:  # usuário escolheu uma das alternativas
            reg = self.base.obter(escolha_id)
            if reg is None:
                return self._finalizar(Resposta(pergunta_txt, "invalida", "Esse assunto não existe mais na base.", template), inicio)
            return self._montar_ok(pergunta_txt, [reg], [], template, usar_ia, inicio, [])

        resultados = self.motor.buscar(pergunta_txt, categoria=categoria)
        status, mostrar = classificar(resultados)

        if status == "sem_resultado":
            return self._finalizar(
                Resposta(pergunta_txt, status, self._texto_sem_resultado(categoria), template, resultados=resultados), inicio)
        if status == "ambigua":
            return self._finalizar(self._montar_ambigua(pergunta_txt, mostrar, resultados, template), inicio)
        return self._montar_ok(pergunta_txt, [r.registro for r in mostrar], mostrar, template, usar_ia, inicio, resultados, status)

    def responder_por_id(self, registro_id: str, template="A", usar_ia=False) -> Resposta:
        """Abre um assunto direto (categorias, relacionados, favoritos, roteiro)."""
        reg = self.base.obter(registro_id)
        inicio = time.perf_counter()
        if reg is None:
            return self._finalizar(Resposta("", "invalida", "Esse assunto não existe mais na base.", template), inicio)
        return self._montar_ok(reg["pergunta"], [reg], [], template, usar_ia, inicio, [])

    # ------------------------------------------------------------------
    def _montar_ok(self, pergunta, registros, mostrados, template, usar_ia, inicio, resultados, status="ok"):
        relacionados = self._relacionados(registros)
        if status == "multipla":
            blocos = [renderizar(template, r, relacionados=()) for r in registros]
            cabecalho = "Sua pergunta envolve mais de um assunto. Veja cada um:\n\n"
            texto = cabecalho + "\n\n----------------------------------------\n\n".join(blocos)
            extra = self._linha_relacionados(relacionados)
            if extra:
                texto += "\n\n" + extra
        else:
            texto = renderizar(template, registros[0], relacionados)
        resposta = Resposta(
            pergunta, status, texto, template,
            principais=registros, relacionados=relacionados, resultados=resultados,
            explicacao=self._explicar(mostrados),
        )
        if usar_ia:
            self._tentar_ia(resposta)
        return self._finalizar(resposta, inicio)

    def _tentar_ia(self, resposta: Resposta) -> None:
        """Pede à IA para reescrever. Qualquer falha cai no texto local."""
        if not self.ia_disponivel:
            resposta.aviso_ia = "IA externa não configurada: usei a busca local."
            return
        try:
            texto_ia = self.cliente_ia.reescrever(resposta.pergunta, resposta.principais, resposta.template)
        except modulo_ia.ErroIA as erro:
            resposta.aviso_ia = f"{erro} Usei a busca local."
            return
        except Exception:  # defesa final: nada da IA pode derrubar o app
            resposta.aviso_ia = "Erro inesperado na IA. Usei a busca local."
            return
        valida, motivo = modulo_ia.validar_resposta_ia(texto_ia, resposta.principais)
        if not valida:
            resposta.aviso_ia = f"Descartei a resposta da IA ({motivo}). Usei a busca local."
            return
        # as fontes e datas vêm SEMPRE da base, nunca da IA
        resposta.texto = texto_ia.strip() + "\n\n" + bloco_fontes(resposta.principais)
        extra = self._linha_relacionados(resposta.relacionados)
        if extra:
            resposta.texto += "\n\n" + extra
        resposta.usou_ia = True

    def _montar_ambigua(self, pergunta, mostrar, resultados, template) -> Resposta:
        alternativas = [r.registro for r in mostrar]
        linhas = ["Sua pergunta pode se referir a mais de um assunto. Qual deles você quis dizer?", ""]
        for i, reg in enumerate(alternativas, start=1):
            linhas.append(f"{i}. {reg['tema']} ({self.base.nome_categoria(reg['categoria'])})")
        linhas += ["", "Escolha uma opção ou reescreva a pergunta com mais detalhes."]
        return Resposta(pergunta, "ambigua", "\n".join(linhas), template,
                        alternativas=alternativas, resultados=resultados, explicacao=self._explicar(mostrar))

    def _texto_sem_resultado(self, categoria) -> str:
        nomes = "\n".join(f"- {c['nome']}" for c in self.base.categorias)
        escopo = ""
        if categoria:
            escopo = (f"Você está buscando só em “{self.base.nome_categoria(categoria)}”. "
                      "Tente buscar em todas as categorias.\n\n")
        return (
            "Não encontrei na minha base uma resposta confiável para essa pergunta, e prefiro não "
            "inventar.\n\n" + escopo +
            "Tente usar outras palavras ou o nome do serviço (por exemplo: CPF, FGTS, aluguel, MEI). "
            f"Eu cubro estes assuntos:\n{nomes}\n\n"
            f"Para outros temas, consulte o portal oficial do governo: {PORTAL_OFICIAL}"
        )

    def _relacionados(self, registros) -> list:
        ids_atuais = {r["id"] for r in registros}
        vistos, saida = set(), []
        for reg in registros:
            for vizinho in self.grafo.vizinhos(reg["id"]):
                if vizinho not in ids_atuais and vizinho not in vistos:
                    vistos.add(vizinho)
                    saida.append(self.base.por_id[vizinho])
        return saida[:5]

    @staticmethod
    def _linha_relacionados(relacionados) -> str:
        return ("Veja também: " + "; ".join(r["tema"] for r in relacionados)) if relacionados else ""

    @staticmethod
    def _explicar(mostrados) -> list:
        linhas = []
        for res in mostrados:
            linhas.append(f"{res.registro['tema']} - relevância {res.relevancia}% ({res.confianca})")
            linhas += [f"   • {motivo}" for motivo in res.explicacao]
        return linhas

    @staticmethod
    def _finalizar(resposta: Resposta, inicio: float) -> Resposta:
        resposta.tempo_ms = round((time.perf_counter() - inicio) * 1000, 3)
        return resposta


NOME_TEMPLATES = NOMES
