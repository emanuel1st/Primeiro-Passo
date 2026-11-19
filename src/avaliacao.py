"""Avaliação do assistente: roda as perguntas de teste e calcula métricas REAIS.

Uso (a partir da raiz do projeto):
    python src/avaliacao.py                      # grava em evidencias/
    python src/avaliacao.py --rotulo rodada1     # prefixo nos arquivos gerados

Saídas em evidencias/:
    <rotulo>resultados_testes.csv|json   pergunta, esperado, obtido, correto, tempo
    <rotulo>resumo_metricas.md           acerto, precisão, tempo médio
    <rotulo>comparacao_templates.md      Template A x Template B (medidas objetivas)

Nada é inventado: todo número vem da execução desta mesma rodada.
"""
import argparse
import csv
import json
import platform
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import config  # noqa: E402
from services.assistente import Assistente  # noqa: E402
from services.busca import MotorBusca  # noqa: E402
from services.conhecimento import BaseConhecimento, carregar_sinonimos  # noqa: E402
from services.grafo import GrafoAssuntos  # noqa: E402
from services.templates import NOMES  # noqa: E402

REPETICOES_TEMPO = 20
ARQUIVO_PERGUNTAS = config.raiz_projeto() / "tests" / "perguntas_teste.json"
PASTA_EVIDENCIAS = config.raiz_projeto() / "evidencias"


def montar_assistente() -> Assistente:
    base = BaseConhecimento.carregar()
    return Assistente(base, MotorBusca(base.registros, carregar_sinonimos()), GrafoAssuntos(base.registros, base.trilhas))


def carregar_perguntas(caminho=ARQUIVO_PERGUNTAS) -> list:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)["perguntas"]


def julgar(caso: dict, resposta) -> tuple:
    """Compara a resposta com o esperado. Devolve (correto, motivo)."""
    if resposta.status != caso["status_esperado"]:
        return False, f"status obtido '{resposta.status}' em vez de '{caso['status_esperado']}'"
    esperados = caso.get("ids_esperados", [])
    if caso["status_esperado"] == "ok" and esperados:
        if resposta.ids_principais != esperados:
            return False, f"principal obtido {resposta.ids_principais} em vez de {esperados}"
    elif esperados:
        presentes = set(resposta.ids_principais) | {r["id"] for r in resposta.alternativas}
        faltando = [i for i in esperados if i not in presentes]
        if faltando:
            return False, f"faltaram {faltando} entre as opções apresentadas"
    for trecho in caso.get("deve_conter", []):
        if trecho not in resposta.texto:
            return False, f"a resposta não contém '{trecho}'"
    return True, ""


def resumo_obtido(resposta) -> str:
    if resposta.status in ("ok", "multipla"):
        return f"{resposta.status}: " + ", ".join(resposta.ids_principais)
    if resposta.status == "ambigua":
        return "ambigua: opções " + ", ".join(r["id"] for r in resposta.alternativas)
    return resposta.status


def executar(assistente: Assistente, perguntas: list, template: str = "A") -> list:
    linhas = []
    for caso in perguntas:
        resposta = assistente.responder(caso["pergunta"], template=template)
        # tempo médio de várias repetições (uma só medida é instável em ms)
        amostras = [assistente.responder(caso["pergunta"], template=template).tempo_ms for _ in range(REPETICOES_TEMPO)]
        correto, motivo = julgar(caso, resposta)
        linhas.append({
            "id": caso["id"], "tipo": caso["tipo"], "limitacao": bool(caso.get("limitacao")),
            "pergunta": caso["pergunta"], "resposta_esperada": caso["resposta_esperada"],
            "status_esperado": caso["status_esperado"], "ids_esperados": ",".join(caso.get("ids_esperados", [])),
            "resposta_obtida": resumo_obtido(resposta), "correto": correto,
            "motivo_falha": motivo, "tempo_ms": round(statistics.mean(amostras), 3),
            "tempo_primeira_execucao_ms": resposta.tempo_ms,
        })
    return linhas


def calcular_metricas(linhas: list) -> dict:
    total = len(linhas)
    acertos = sum(1 for l in linhas if l["correto"])
    respondiveis = [l for l in linhas if l["status_esperado"] == "ok"]
    acertos_resp = sum(1 for l in respondiveis if l["correto"])
    limitacoes = [l for l in linhas if l["limitacao"]]
    tempos = [l["tempo_ms"] for l in linhas]
    return {
        "total": total, "acertos": acertos,
        "acerto_geral": acertos / total if total else 0.0,
        "respondiveis": len(respondiveis), "acertos_respondiveis": acertos_resp,
        "precisao_respondiveis": acertos_resp / len(respondiveis) if respondiveis else 0.0,
        "limitacoes": len(limitacoes), "limitacoes_corretas": sum(1 for l in limitacoes if l["correto"]),
        "tempo_medio_ms": statistics.mean(tempos) if tempos else 0.0,
        "tempo_maximo_ms": max(tempos) if tempos else 0.0,
    }


def comparar_templates(assistente: Assistente, perguntas: list) -> list:
    """Medidas objetivas dos dois templates nas perguntas que geram resposta."""
    saida = []
    for caso in perguntas:
        a = assistente.responder(caso["pergunta"], template="A")
        if a.status not in ("ok", "multipla"):
            continue
        b = assistente.responder(caso["pergunta"], template="B")
        linha = {"id": caso["id"], "pergunta": caso["pergunta"]}
        for rotulo, resp in (("A", a), ("B", b)):
            texto = resp.texto
            linha[f"{rotulo}_caracteres"] = len(texto)
            linha[f"{rotulo}_etapas"] = sum(1 for l in texto.splitlines() if l[:2].rstrip(".").isdigit() and l[1:3].startswith(". ") or l[:3].rstrip(".").isdigit() and ". " in l[:4])
            linha[f"{rotulo}_alertas"] = "Atenção:" in texto
            linha[f"{rotulo}_fonte"] = "Fonte:" in texto
            linha[f"{rotulo}_data_ou_pendencia"] = ("Verificado em" in texto) or ("PENDENTE" in texto) or ("PARCIALMENTE" in texto)
            linha[f"{rotulo}_relacionados"] = "Veja também:" in texto
        saida.append(linha)
    return saida


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%".replace(".", ",")


def gravar(linhas, metricas, comparacao, pasta: Path, rotulo: str, stats_base: dict) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    prefixo = f"{rotulo}_" if rotulo else ""
    with open(pasta / f"{prefixo}resultados_testes.csv", "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    with open(pasta / f"{prefixo}resultados_testes.json", "w", encoding="utf-8") as f:
        json.dump({"metricas": metricas, "resultados": linhas}, f, ensure_ascii=False, indent=2)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    md = [
        f"# Resumo das métricas {('(' + rotulo + ')') if rotulo else ''}",
        "",
        f"Executado em {agora} com Python {platform.python_version()} em {platform.system()} {platform.release()}.",
        f"Base: {stats_base['total']} conhecimentos ({stats_base['verificado']} verificados, "
        f"{stats_base['parcial']} parcial, {stats_base['pendente_validacao']} pendentes).",
        "",
        "| Métrica | Valor |", "|---|---|",
        f"| Perguntas de teste | {metricas['total']} |",
        f"| Respostas corretas (todas) | {metricas['acertos']} de {metricas['total']} ({_pct(metricas['acerto_geral'])}) |",
        f"| Precisão nas perguntas respondíveis | {metricas['acertos_respondiveis']} de {metricas['respondiveis']} ({_pct(metricas['precisao_respondiveis'])}) |",
        f"| Testes de limitação corretos | {metricas['limitacoes_corretas']} de {metricas['limitacoes']} |",
        f"| Tempo médio por pergunta | {metricas['tempo_medio_ms']:.3f} ms (média de {REPETICOES_TEMPO} repetições por pergunta) |",
        f"| Maior tempo médio | {metricas['tempo_maximo_ms']:.3f} ms |",
        "",
        "## Detalhe por pergunta", "",
        "| ID | Tipo | Pergunta | Esperado | Obtido | Correto | Tempo (ms) |", "|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        esperado = l["status_esperado"] + (": " + l["ids_esperados"] if l["ids_esperados"] else "")
        pergunta = (l["pergunta"].strip() or "(vazia)").replace("|", "/")
        md.append(f"| {l['id']} | {l['tipo']} | {pergunta} | {esperado} | {l['resposta_obtida']} | "
                  f"{'sim' if l['correto'] else '**NÃO** - ' + l['motivo_falha']} | {l['tempo_ms']:.3f} |")
    md += ["", "Observação: o tempo mede só o processamento local (validação, busca e montagem da resposta), sem a interface nem a IA externa."]
    (pasta / f"{prefixo}resumo_metricas.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if comparacao:
        n = len(comparacao)
        def media(chave): return statistics.mean(c[chave] for c in comparacao)
        def conta(chave): return sum(1 for c in comparacao if c[chave])
        cmp = [
            "# Comparação dos templates A e B", "",
            f"Medidas objetivas em {n} perguntas que geraram resposta (rodada: {rotulo or 'final'}). "
            "As respostas vêm dos renderizadores locais (sem IA), então o resultado é reproduzível.", "",
            f"- **Template A**: {NOMES['A']}", f"- **Template B**: {NOMES['B']}", "",
            "| Medida | Template A | Template B |", "|---|---|---|",
            f"| Tamanho médio (caracteres) | {media('A_caracteres'):.0f} | {media('B_caracteres'):.0f} |",
            f"| Etapas numeradas por resposta (média) | {media('A_etapas'):.1f} | {media('B_etapas'):.1f} |",
            f"| Respostas com alertas | {conta('A_alertas')} de {n} | {conta('B_alertas')} de {n} |",
            f"| Respostas com fonte | {conta('A_fonte')} de {n} | {conta('B_fonte')} de {n} |",
            f"| Respostas com data de verificação ou aviso de pendência | {conta('A_data_ou_pendencia')} de {n} | {conta('B_data_ou_pendencia')} de {n} |",
            f"| Respostas com assuntos relacionados | {conta('A_relacionados')} de {n} | {conta('B_relacionados')} de {n} |",
            "", "## Por pergunta", "",
            "| ID | Pergunta | A: caracteres | B: caracteres | B: etapas |", "|---|---|---|---|---|",
        ]
        for c in comparacao:
            cmp.append(f"| {c['id']} | {c['pergunta']} | {c['A_caracteres']} | {c['B_caracteres']} | {c['B_etapas']} |")
        cmp += ["", "## Como ler", "",
                "Essas medidas mostram diferenças de **forma** (tamanho, presença de etapas e alertas). "
                "Elas NÃO provam que um template é melhor para o usuário: isso depende de leitura e "
                "preferência, e exigiria o teste de usabilidade com pessoas reais."]
        (pasta / f"{prefixo}comparacao_templates.md").write_text("\n".join(cmp) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    analisador = argparse.ArgumentParser(description="Avalia o assistente do Primeiro Passo.")
    analisador.add_argument("--rotulo", default="", help="prefixo dos arquivos de saída (ex.: rodada1)")
    args = analisador.parse_args(argv)

    assistente = montar_assistente()
    perguntas = carregar_perguntas()
    linhas = executar(assistente, perguntas, template="A")
    metricas = calcular_metricas(linhas)
    comparacao = comparar_templates(assistente, perguntas)
    gravar(linhas, metricas, comparacao, PASTA_EVIDENCIAS, args.rotulo, assistente.base.estatisticas())

    print(f"Perguntas: {metricas['total']} | corretas: {metricas['acertos']} ({_pct(metricas['acerto_geral'])})")
    print(f"Precisão nas respondíveis: {metricas['acertos_respondiveis']}/{metricas['respondiveis']} ({_pct(metricas['precisao_respondiveis'])})")
    print(f"Limitações corretas: {metricas['limitacoes_corretas']}/{metricas['limitacoes']}")
    print(f"Tempo médio: {metricas['tempo_medio_ms']:.3f} ms")
    for l in linhas:
        if not l["correto"]:
            print(f"  FALHA {l['id']} {l['pergunta']!r}: {l['motivo_falha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
