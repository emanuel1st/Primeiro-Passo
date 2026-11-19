# Resumo das métricas 

Executado em 13/11/2026 20:30 com Python 3.13.18 em Linux 6.18.44-fc-v445.
Base: 29 conhecimentos (20 verificados, 1 parcial, 8 pendentes).

| Métrica | Valor |
|---|---|
| Perguntas de teste | 19 |
| Respostas corretas (todas) | 19 de 19 (100,0%) |
| Precisão nas perguntas respondíveis | 11 de 11 (100,0%) |
| Testes de limitação corretos | 4 de 4 |
| Tempo médio por pergunta | 0.542 ms (média de 20 repetições por pergunta) |
| Maior tempo médio | 1.510 ms |

## Detalhe por pergunta

| ID | Tipo | Pergunta | Esperado | Obtido | Correto | Tempo (ms) |
|---|---|---|---|---|---|---|
| T01 | direta | Como faço minha carteira de trabalho? | ok: EMP-01 | ok: EMP-01 | sim | 1.018 |
| T02 | direta | Onde posso encontrar cursos gratuitos? | ok: FAC-03 | ok: FAC-03 | sim | 1.510 |
| T03 | direta | Quais documentos preciso para tirar meu título de eleitor? | ok: DOC-01 | ok: DOC-01 | sim | 1.181 |
| T04 | direta | Como funciona o cadastro no SUS? | ok: SAU-01 | ok: SAU-01 | sim | 0.498 |
| T05 | direta | Quero começar a morar sozinho. Por onde começo? | ok: MOR-01 | ok: MOR-01 | sim | 0.734 |
| T06 | escrita diferente | como saco o dinheiro do fundo de garantia quando saio da empresa | ok: EMP-02 | ok: EMP-02 | sim | 0.640 |
| T07 | escrita diferente | to com 18 anos e sou homem, preciso me alistar? | ok: DIR-01 | ok: DIR-01 | sim | 0.461 |
| T08 | sinônimo | Como tiro minha carta de motorista? | ok: TRA-01 | ok: TRA-01 | sim | 0.820 |
| T09 | sinônimo | Quanto o microempreendedor paga de imposto por mês? | ok: IMP-02 | ok: IMP-02 | sim | 0.418 |
| T10 | sinônimo | Posso ver minhas vacinas pelo celular? | ok: SAU-02 | ok: SAU-02 | sim | 0.422 |
| T11 | mais de uma categoria | Quero abrir um MEI e também saber se preciso declarar imposto de renda | multipla: IMP-01,IMP-03 | multipla: IMP-03, IMP-01 | sim | 0.884 |
| T12 | pendente de validação | Como funciona o Pix? | ok: FIN-03 | ok: FIN-03 | sim | 0.338 |
| T13 | ambígua | carteira | ambigua: EMP-01,TRA-01,DOC-04,SAU-02 | ambigua: opções DOC-04, EMP-01, SAU-02, TRA-01 | sim | 0.236 |
| T14 | fora do escopo | Qual a previsão do tempo para amanhã? | sem_resultado | sem_resultado | sim | 0.387 |
| T15 | fora do escopo | Quem ganhou o jogo do Corinthians ontem? | sem_resultado | sem_resultado | sim | 0.395 |
| T16 | sem cobertura na base | Como abrir uma conta bancária? | sem_resultado | sem_resultado | sim | 0.359 |
| T17 | vazia | (vazia) | vazia | vazia | sim | 0.001 |
| T18 | vazia | (vazia) | vazia | vazia | sim | 0.001 |
| T19 | inválida | ?!?! #$% | invalida | invalida | sim | 0.003 |

Observação: o tempo mede só o processamento local (validação, busca e montagem da resposta), sem a interface nem a IA externa.
