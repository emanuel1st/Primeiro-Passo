"""Grafo simples de assuntos relacionados.

Como as relações são guardadas
------------------------------
* Cada conhecimento tem em `conhecimentos.json` o campo `relacionados`
  (lista de IDs). Isso vira um dicionário de adjacência:
      {"EMP-01": {"EMP-02", "EMP-03", "DOC-02"}, ...}
* As relações são tratadas como NÃO direcionadas: se A cita B, B também
  enxerga A.
* As "trilhas" de `categorias.json` (ex.: Primeiro emprego -> Carteira de
  Trabalho -> FGTS -> Imposto de Renda) são listas ordenadas de IDs e também
  criam ligações entre passos consecutivos.

Como são usadas
---------------
* `vizinhos(id)`: botões "Assuntos relacionados" na resposta do assistente.
* `trilha_do_assunto(id)`: mostra o caminho "A -> B -> C" com o assunto atual.
* `caminho(a, b)`: busca em largura (BFS) do menor caminho entre dois assuntos.
* `rota_sugerida(id)`: sequência de pelo menos 3 assuntos para o usuário navegar.
"""
from collections import deque


class GrafoAssuntos:
    def __init__(self, registros, trilhas=None):
        self.arestas = {r["id"]: set() for r in registros}
        for reg in registros:
            for outro in reg.get("relacionados", []):
                self._ligar(reg["id"], outro)
        self.trilhas = [t for t in (trilhas or []) if len(t.get("passos", [])) >= 2]
        for trilha in self.trilhas:
            for a, b in zip(trilha["passos"], trilha["passos"][1:]):
                self._ligar(a, b)

    def _ligar(self, a: str, b: str) -> None:
        if a in self.arestas and b in self.arestas and a != b:
            self.arestas[a].add(b)
            self.arestas[b].add(a)

    def vizinhos(self, assunto_id: str) -> list:
        return sorted(self.arestas.get(assunto_id, ()))

    def caminho(self, origem: str, destino: str) -> list:
        """Menor caminho entre dois assuntos (lista de IDs) ou [] se não houver."""
        if origem not in self.arestas or destino not in self.arestas:
            return []
        anterior = {origem: None}
        fila = deque([origem])
        while fila:
            atual = fila.popleft()
            if atual == destino:
                caminho = []
                while atual is not None:
                    caminho.append(atual)
                    atual = anterior[atual]
                return caminho[::-1]
            for vizinho in sorted(self.arestas[atual]):
                if vizinho not in anterior:
                    anterior[vizinho] = atual
                    fila.append(vizinho)
        return []

    def trilha_do_assunto(self, assunto_id: str):
        """Primeira trilha que contém o assunto (dict) ou None."""
        for trilha in self.trilhas:
            if assunto_id in trilha["passos"]:
                return trilha
        return None

    def rota_sugerida(self, assunto_id: str, tamanho: int = 4) -> list:
        """Sequência de assuntos para navegar a partir de `assunto_id`.

        Usa a trilha do assunto quando existe; senão, caminha pelos vizinhos
        ainda não visitados.
        """
        trilha = self.trilha_do_assunto(assunto_id)
        if trilha:
            return list(trilha["passos"])
        rota = [assunto_id] if assunto_id in self.arestas else []
        while rota and len(rota) < tamanho:
            novos = [v for v in self.vizinhos(rota[-1]) if v not in rota]
            if not novos:
                break
            rota.append(novos[0])
        return rota
