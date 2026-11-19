# Registro de testes, falhas e correções

Os números abaixo vêm das execuções reais registradas em `evidencias/`. Os arquivos da primeira rodada (com falha) foram mantidos em `evidencias/rodada1_*` como prova.

## Falha 1 — "carteira" parecia inequívoca (encontrada antes da rodada oficial)

| Item | Detalhe |
|---|---|
| Pergunta | `carteira` (uma palavra só) |
| Esperado | `ambigua`: o assistente deve pedir para escolher entre CIN, Carteira de Trabalho, vacinação e CNH |
| Obtido | resposta direta (`ok`) sobre um único assunto |
| Causa | o bônus de similaridade (Jaccard) favorecia registros com poucas palavras: uma palavra em comum já dava similaridade alta |
| Correção | o bônus só vale para perguntas com **2 ou mais palavras** (`MIN_TOKENS_SIMILARIDADE = 2` em `src/services/busca.py`) |
| Resultado | `carteira` → `ambigua` com 4 alternativas (DOC-04, EMP-01, SAU-02, TRA-01). Coberto por `test_limitacao_pergunta_ambigua` |

## Falha 2 — conta bancária respondida com o assunto errado (rodada 1)

| Item | Detalhe |
|---|---|
| Pergunta | T16: `Como abrir uma conta bancária?` |
| Esperado | `sem_resultado` (a base não tem como abrir conta; só o relatório de contas Registrato) |
| Obtido | `ok: FIN-01` (Registrato). **Falso positivo.** |
| Resultado da rodada 1 | 18 de 19 corretas (94,7%); limitações 3 de 4; tempo médio 0,329 ms |
| Causa 1 | um grupo em `data/sinonimos.json` tratava "abrir conta" como sinônimo de "conta em banco", e a base tem "contas em bancos" |
| Causa 2 | a palavra solta "abrir" já somava pontos suficientes para passar o filtro mínimo, mesmo sem cobrir o sentido da pergunta |
| Correção 1 | removido o grupo de sinônimos incorreto |
| Correção 2 | resultados com evidência fraca (< 3,0 pontos) só são mantidos se cobrirem **pelo menos metade** das palavras da pergunta (`COBERTURA_MINIMA_FRACA = 0.5`) |
| Resultado da rodada 2 | **19 de 19 corretas**; limitações 4 de 4; tempo médio entre 0,324 ms e 0,542 ms em três execuções (11 e 13/11/2026): o tempo varia entre execuções; o valor da última execução está em `evidencias/resumo_metricas.md` |
| Teste de regressão | `test_palavra_solta_irrelevante_nao_basta` |

## Ressalvas (leia antes de citar "100%")

1. **O conjunto de teste foi escrito pelo desenvolvedor depois de conhecer a base.** Os 100% da rodada 2 mostram que o assistente passa nos casos previstos, **não** que acerta qualquer pergunta de um usuário real.
2. **A correção da Falha 2 foi uma reação ao teste que falhou.** Depois dela, a pergunta T16 passa por construção. Para medir generalização, é preciso um conjunto novo de perguntas, de preferência feitas por outras pessoas (teste de usabilidade).
3. **Métricas de tempo** medem só a busca local e variam de execução para execução; não use como valor fixo.

## Checagens de integridade feitas durante o desenvolvimento

- Fontes que não puderam ser lidas (páginas bloqueadas ou vazias): Pronatec, Planalto Lei 8.245, Prouni/Fies/Sisu (acessounico), CIN, Pix. Os assuntos correspondentes ficaram `pendente_validacao`, sem data de verificação e sem conteúdo inventado.
- Documentação da API do Gemini não pôde ser aberta (site fora da lista de acesso do ambiente). O formato da requisição foi escrito com base no formato conhecido da API `generateContent` e marcado como **não verificado** na documentação.
- Ambiente de desenvolvimento sem `tkinter`/`customtkinter` e sem rede para instalar: a interface foi testada só com simulador (`tests/gui_stub.py`). **Pendente:** abrir o app no Windows e conferir layout, cores, fontes e rolagem.