"""Os dois templates de instrução do assistente.

Cada template existe em duas formas:

1. INSTRUCOES[...]: texto de instrução enviado à IA externa (opcional), que
   diz COMO reescrever os conhecimentos encontrados.
2. renderizar_*(...): versão local e determinística, usada quando não há IA
   (ou quando ela falha). É a que os testes medem, porque dá o mesmo
   resultado a cada execução.

Template A - Resposta objetiva: explicação curta, fonte e próximo passo.
Template B - Orientação passo a passo: etapas numeradas, alertas, fontes e
             assuntos relacionados.
"""

NOMES = {"A": "Resposta objetiva", "B": "Passo a passo"}

REGRAS_COMUNS = (
    "Você é o assistente do aplicativo Primeiro Passo, que orienta jovens de 18 a 21 anos "
    "sobre serviços públicos. Use SOMENTE os conhecimentos fornecidos entre os marcadores "
    "<<<CONHECIMENTOS>>> e <<<FIM>>>. Não acrescente fatos, números, prazos, valores, leis ou "
    "links que não estejam neles. Se a informação não bastar para responder, diga isso "
    "claramente. Se um conhecimento estiver marcado como PENDENTE DE VALIDAÇÃO ou "
    "PARCIALMENTE VERIFICADO, avise que é preciso confirmar na fonte oficial. Escreva em "
    "português do Brasil, com linguagem simples. Não se apresente como serviço do governo."
)

INSTRUCOES = {
    "A": REGRAS_COMUNS
    + " FORMATO (resposta objetiva): no máximo 5 frases explicando o essencial, depois uma "
    "linha 'Próximo passo:' com uma única ação concreta tirada dos conhecimentos.",
    "B": REGRAS_COMUNS
    + " FORMATO (passo a passo): uma frase de resumo, depois as etapas numeradas na ordem dos "
    "conhecimentos, depois a seção 'Atenção:' com os alertas (se houver). Se os conhecimentos "
    "não trouxerem etapas, diga isso em vez de inventá-las.",
}


def data_br(iso: str) -> str:
    """'2026-11-11' -> '11/11/2026'."""
    try:
        ano, mes, dia = iso.split("-")
        return f"{dia}/{mes}/{ano}"
    except (ValueError, AttributeError):
        return str(iso or "")


def linha_situacao(reg: dict) -> str:
    situacao = reg.get("situacao")
    if situacao == "verificado":
        return f"Verificado em {data_br(reg.get('data_verificacao'))}."
    if situacao == "parcial":
        return (f"PARCIALMENTE VERIFICADO em {data_br(reg.get('data_verificacao'))}. "
                f"{reg.get('nota_validacao', '')} Confirme na fonte oficial.").strip()
    return ("PENDENTE DE VALIDAÇÃO: esta informação ainda não foi conferida na fonte oficial. "
            "Confirme na fonte antes de agir.")


def linhas_fontes(reg: dict) -> list:
    return [f"Fonte: {f['nome']} - {f['url']}" for f in reg.get("fontes", [])]


def bloco_fontes(registros) -> str:
    """Fontes + situação de cada registro. Sempre anexado pelo sistema, mesmo com IA."""
    partes = []
    for reg in registros:
        partes.extend(linhas_fontes(reg))
        partes.append(linha_situacao(reg))
    return "\n".join(partes)


def _linha_relacionados(relacionados) -> str:
    if not relacionados:
        return ""
    return "Veja também: " + "; ".join(r["tema"] for r in relacionados)


def renderizar_objetiva(reg: dict, relacionados=()) -> str:
    """Template A."""
    linhas = [reg["tema"], "", reg["orientacao"], ""]
    etapas = reg.get("etapas") or []
    if etapas:
        linhas.append(f"Próximo passo: {etapas[0]}")
    else:
        linhas.append("Próximo passo: confirme os detalhes na fonte oficial abaixo.")
    linhas.append("")
    linhas.append(bloco_fontes([reg]))
    extra = _linha_relacionados(relacionados)
    if extra:
        linhas += ["", extra]
    return "\n".join(linhas)


def renderizar_passo_a_passo(reg: dict, relacionados=()) -> str:
    """Template B."""
    linhas = [f"{reg['tema']} - passo a passo", "", f"Resumo: {reg['orientacao']}", ""]
    etapas = reg.get("etapas") or []
    if etapas:
        linhas.append("Etapas:")
        linhas += [f"{i}. {e}" for i, e in enumerate(etapas, start=1)]
    else:
        linhas.append("Esta orientação não tem etapas cadastradas. Siga a fonte oficial abaixo.")
    alertas = reg.get("alertas") or []
    if alertas:
        linhas += ["", "Atenção:"] + [f"- {a}" for a in alertas]
    linhas += ["", bloco_fontes([reg])]
    extra = _linha_relacionados(relacionados)
    if extra:
        linhas += ["", extra]
    return "\n".join(linhas)


RENDERIZADORES = {"A": renderizar_objetiva, "B": renderizar_passo_a_passo}


def renderizar(template: str, reg: dict, relacionados=()) -> str:
    return RENDERIZADORES.get(template, renderizar_objetiva)(reg, relacionados)
