"""Busca local por relevância (funciona sem internet e sem API).

ALGORITMO
=========
1. A pergunta é normalizada e reduzida a "tokens" (ver utils/texto.py):
   "Quais documentos preciso para o título de eleitor?" -> [documento, titulo, eleitor]
2. Cada conhecimento recebe uma pontuação somando evidências:

   +5,0  Frase: uma palavra-chave inteira (ex.: "titulo de eleitor") aparece
         na pergunta, com as palavras na mesma ordem.
   +3,5  Sinônimo: um termo do grupo de sinônimos (data/sinonimos.json) leva a
         uma palavra-chave do registro (ex.: "habilitacao" -> "cnh").
   +1,0 a +2,0  Palavra solta: uma palavra da pergunta aparece nas
         palavras-chave. O peso é maior para palavras raras (estilo IDF):
         peso = 1 + log(N / df) / log(N), em que df é o número de registros
         que contêm a palavra e N o total de registros.
   +0,8  Texto: palavra da pergunta aparece no tema, na pergunta principal ou
         nas variações (no máximo 3 palavras por registro).
   +6 x s  Similaridade: s = Jaccard entre a pergunta do usuário e a pergunta
         principal/variação mais parecida; só conta se s >= 0,4 e a pergunta
         tem pelo menos 2 palavras (consulta de 1 palavra seria favorecida
         injustamente em registros curtos).

3. Registros com pontuação < 1,5 são descartados. Resultados FRACOS (< 3,0) só
   são mantidos se as palavras que casaram cobrirem pelo menos 50% das palavras
   da pergunta (`cobertura`): uma palavra solta, como "abrir", não basta para
   propor um assunto quando o resto da pergunta não tem relação com ele.
4. Relevância (0 a 100) = pontuação / 10, limitada a 100.
   Confiança: forte (>= 5), média (>= 3), fraca (< 3).
5. Cada resultado carrega a lista de motivos (`explicacao`) para o usuário
   entender por que ele apareceu.

As constantes abaixo podem ser ajustadas; os testes mostram o efeito.
"""
import math
from dataclasses import dataclass, field

from utils.texto import tokenizar

PESO_FRASE = 5.0
PESO_SINONIMO = 3.5
PESO_TOKEN_BASE = 1.0
PESO_TEXTO = 0.8
MAX_TOKENS_TEXTO = 3
PESO_SIMILARIDADE = 6.0
LIMIAR_SIMILARIDADE = 0.4
MIN_TOKENS_SIMILARIDADE = 2
MINIMO = 1.5
COBERTURA_MINIMA_FRACA = 0.5
LIMIAR_FORTE = 5.0
LIMIAR_MEDIA = 3.0
REFERENCIA_RELEVANCIA = 10.0


@dataclass
class ResultadoBusca:
    registro: dict
    pontuacao: float
    relevancia: int
    confianca: str
    termos: frozenset = field(default_factory=frozenset)
    cobertura: float = 0.0
    explicacao: list = field(default_factory=list)


def _contem(sequencia, trecho) -> bool:
    """True se `trecho` aparece em `sequencia` de forma contígua."""
    n, m = len(sequencia), len(trecho)
    if m == 0 or m > n:
        return False
    trecho = tuple(trecho)
    return any(tuple(sequencia[i:i + m]) == trecho for i in range(n - m + 1))


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


class _RegistroIndexado:
    """Versão pré-processada de um conhecimento (feita uma vez só)."""

    def __init__(self, registro: dict):
        self.registro = registro
        self.frases = []  # (texto original, tupla de tokens)
        tokens_chave = set()
        for palavra in registro.get("palavras_chave", []):
            tokens = tuple(tokenizar(palavra))
            if tokens:
                self.frases.append((palavra, tokens))
                tokens_chave.update(tokens)
        self.tokens_chave = tokens_chave
        textos = [registro.get("pergunta", "")] + list(registro.get("variacoes", []))
        self.comparacao = [set(tokenizar(t)) for t in textos]
        self.tokens_texto = set(tokenizar(registro.get("tema", ""))).union(*self.comparacao)


class MotorBusca:
    def __init__(self, registros, grupos_sinonimos=None):
        self._indice = [_RegistroIndexado(r) for r in registros]
        self._total = max(len(self._indice), 2)
        self._df = {}
        for item in self._indice:
            for token in item.tokens_chave:
                self._df[token] = self._df.get(token, 0) + 1
        # sinônimos: tupla de tokens -> (texto original, índice do grupo)
        self._membros = {}
        self._grupos = []
        for i, grupo in enumerate(grupos_sinonimos or []):
            membros = []
            for termo in grupo:
                tokens = tuple(tokenizar(termo))
                if tokens:
                    membros.append((termo, tokens))
                    self._membros[tokens] = i
            self._grupos.append(membros)

    # ------------------------------------------------------------------
    def buscar(self, consulta: str, categoria=None, limite: int = 5) -> list:
        """Devolve até `limite` resultados ordenados por pontuação.

        `categoria` (id) restringe a busca a uma categoria.
        """
        tokens = tokenizar(consulta)
        if not tokens:
            return []
        alternativas = self._expandir_sinonimos(tokens)
        resultados = []
        for item in self._indice:
            if categoria and item.registro["categoria"] != categoria:
                continue
            resultado = self._pontuar(item, tokens, alternativas)
            if resultado.pontuacao >= MINIMO and (
                resultado.pontuacao >= LIMIAR_MEDIA or resultado.cobertura >= COBERTURA_MINIMA_FRACA
            ):
                resultados.append(resultado)
        resultados.sort(key=lambda r: (-r.pontuacao, r.registro["id"]))
        return resultados[:limite]

    def similares(self, registro_id: str, limite: int = 3) -> list:
        """Registros parecidos com um registro dado (palavras em comum)."""
        base = next((i for i in self._indice if i.registro["id"] == registro_id), None)
        if base is None:
            return []
        alvo = base.tokens_chave | base.tokens_texto
        pares = []
        for item in self._indice:
            if item is base:
                continue
            nota = _jaccard(alvo, item.tokens_chave | item.tokens_texto)
            if nota > 0:
                pares.append((nota, item.registro))
        pares.sort(key=lambda p: (-p[0], p[1]["id"]))
        return [r for _, r in pares[:limite]]

    # ------------------------------------------------------------------
    def _expandir_sinonimos(self, tokens) -> list:
        """Para cada termo de grupo achado na pergunta, lista os outros membros."""
        alternativas = []
        usados = set()
        for tokens_membro, indice in self._membros.items():
            if _contem(tokens, tokens_membro):
                origem = next(t for t, k in self._grupos[indice] if k == tokens_membro)
                for texto, tokens_alt in self._grupos[indice]:
                    if tokens_alt != tokens_membro and (tokens_alt, tokens_membro) not in usados:
                        usados.add((tokens_alt, tokens_membro))
                        alternativas.append((tokens_alt, texto, tokens_membro, origem))
        return alternativas

    def _pontuar(self, item: _RegistroIndexado, tokens: list, alternativas: list) -> ResultadoBusca:
        pontos = 0.0
        explicacao = []
        termos = set()
        cobertos = set()
        frases_ja_usadas = set()
        conjunto = set(tokens)

        # 1) frases inteiras
        for texto, frase in item.frases:
            if _contem(tokens, frase):
                pontos += PESO_FRASE
                cobertos.update(frase)
                termos.update(frase)
                frases_ja_usadas.add(frase)
                explicacao.append(f"A palavra-chave «{texto}» aparece na pergunta (+{PESO_FRASE:.1f})")

        # 2) sinônimos
        for tokens_alt, texto_alt, tokens_origem, texto_origem in alternativas:
            for texto, frase in item.frases:
                if frase in frases_ja_usadas:
                    continue
                if frase == tokens_alt or _contem(frase, tokens_alt):
                    pontos += PESO_SINONIMO
                    frases_ja_usadas.add(frase)
                    cobertos.update(tokens_origem)
                    termos.update(tokens_origem)
                    explicacao.append(
                        f"«{texto_origem}» é sinônimo de «{texto_alt}», que aparece em «{texto}» (+{PESO_SINONIMO:.1f})"
                    )
                    break

        # 3) palavras soltas nas palavras-chave (palavras raras valem mais)
        for token in sorted(conjunto - cobertos):
            if token in item.tokens_chave:
                peso = PESO_TOKEN_BASE + math.log(self._total / self._df[token]) / math.log(self._total)
                pontos += peso
                cobertos.add(token)
                termos.add(token)
                explicacao.append(f"A palavra «{token}» aparece nas palavras-chave (+{peso:.1f})")

        # 4) palavras no tema / pergunta / variações
        restantes = sorted(t for t in conjunto - cobertos if t in item.tokens_texto)
        if restantes:
            usados = restantes[:MAX_TOKENS_TEXTO]
            pontos += PESO_TEXTO * len(usados)
            termos.update(usados)
            explicacao.append(f"As palavras {', '.join('«' + t + '»' for t in usados)} aparecem no texto do assunto (+{PESO_TEXTO * len(usados):.1f})")

        # 5) pergunta parecida com a pergunta principal ou uma variação
        melhor = max((_jaccard(conjunto, c) for c in item.comparacao), default=0.0)
        if melhor >= LIMIAR_SIMILARIDADE and len(conjunto) >= MIN_TOKENS_SIMILARIDADE:
            extra = PESO_SIMILARIDADE * melhor
            pontos += extra
            explicacao.append(f"Pergunta parecida com uma já cadastrada ({melhor:.0%} de semelhança, +{extra:.1f})")

        if pontos >= LIMIAR_FORTE:
            confianca = "forte"
        elif pontos >= LIMIAR_MEDIA:
            confianca = "média"
        else:
            confianca = "fraca"
        return ResultadoBusca(
            registro=item.registro,
            pontuacao=round(pontos, 2),
            relevancia=min(100, round(100 * pontos / REFERENCIA_RELEVANCIA)),
            confianca=confianca,
            termos=frozenset(termos),
            cobertura=len(termos & conjunto) / len(conjunto) if conjunto else 0.0,
            explicacao=explicacao,
        )
