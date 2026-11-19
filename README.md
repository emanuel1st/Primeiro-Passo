# Primeiro Passo — Seu guia para a vida adulta.

Aplicativo de desktop (Python + CustomTkinter) que orienta jovens de 18 a 21 anos sobre os primeiros passos da vida adulta: documentos, primeiro emprego, saúde, faculdade, moradia, impostos e direitos. As respostas vêm de uma base local de conhecimentos montada a partir de páginas oficiais do governo, sempre com fonte, link e data de verificação.

> **Aviso:** o Primeiro Passo é uma plataforma **independente**. **Não é um serviço do Governo Federal** e não substitui o Gov.br nem qualquer serviço público. Ele explica procedimentos e indica os canais oficiais.

Trabalho individual da FIAP (entrega: 19/11/2026).

---

## Identificação (preencher)

| Campo | Valor |
|---|---|
| Integrante | Emanuel Rocha Monteiro |
| RM | `569895` |
| Turma | `1CCOB` |
| Repositório no GitHub | `https://github.com/emanuel1st/Primeiro-Passo` |

---

## 1. Problema identificado

Ao fazer 18 anos, a pessoa precisa resolver sozinha várias coisas ao mesmo tempo (CPF, título de eleitor, alistamento militar para homens, carteira de trabalho, SUS, primeiro emprego, aluguel). A informação existe nos sites oficiais, mas está espalhada, em linguagem técnica, e é difícil saber por onde começar e em que ordem.

## 2. Público-alvo

Jovens de 18 a 21 anos, em especial quem acabou de completar a maioridade e nunca precisou lidar com esses serviços.

## 3. Objetivos

- Responder dúvidas em linguagem simples, **sempre indicando a fonte oficial e a data da conferência**.
- Guiar o usuário por um roteiro ("Completei 18 anos. E agora?") e por trilhas de assuntos relacionados.
- **Nunca inventar**: quando a base não cobre a pergunta, dizer isso e apontar o portal oficial.
- Funcionar offline e sem nenhuma chave de API (IA externa é opcional).
- Ser acessível: fonte ajustável, alto contraste, uso por teclado e linguagem simples.

## 4. Categorias atendidas

| Categoria | Assuntos |
|---|---|
| 💼 Primeiro emprego e direitos trabalhistas | Carteira de Trabalho Digital, FGTS, Sine |
| 💳 Finanças e serviços bancários | Relatório de contas em bancos (Registrato), reclamar pelo Consumidor.gov.br, Pix |
| 🚌 Transporte e mobilidade | Primeira habilitação (CNH do Brasil), curso teórico gratuito e LADV, passe livre estudantil (São Paulo) |
| 🏠 Moradia, aluguel e independência | Lei do Inquilinato, garantias do aluguel (caução, fiador, seguro-fiança), devolver o imóvel antes do fim do contrato |
| 🩺 Saúde e serviços públicos | Meu SUS Digital, carteira de vacinação, Cartão SUS, Cadastro Único |
| 🎓 Faculdade, cursos e bolsas | Enem (inscrição, taxa, isenção), Sisu/ProUni/Fies, Pronatec (cursos técnicos e de qualificação) |
| 🪪 Documentação e identidade | Título de eleitor, CPF, comprovante de CPF, CIN |
| 🧾 Impostos, MEI e empreendedorismo | Abrir um MEI, obrigações do MEI (DAS e declaração anual), Imposto de Renda |
| ⚖️ Direitos e deveres do cidadão | Alistamento militar, voto (obrigatório ou facultativo), Código de Defesa do Consumidor |

Total: **29 assuntos em 9 categorias** (20 verificados, 1 parcial, 8 pendentes de validação). Há ainda o roteiro especial **"Completei 18 anos. E agora?"** (8 passos) e 7 **trilhas** de assuntos.

---

## 5. Organização da base de conhecimento

Tudo fica em arquivos JSON na pasta `data/`. **Dá para editar sem mexer no código** (o app valida os arquivos ao abrir e ignora, avisando, registros com erro).

| Arquivo | Conteúdo |
|---|---|
| `data/conhecimentos.json` | Os 29 conhecimentos |
| `data/categorias.json` | Categorias, roteiro "Completei 18 anos" e trilhas |
| `data/sinonimos.json` | Grupos de termos equivalentes (22 grupos) |
| `data/oportunidades.json` | Oportunidades, ligadas a um conhecimento (fonte, link e data vêm dele) |
| `data/checklists.json` | Modelos de checklist (4 modelos) |

Campos de cada conhecimento:

```json
{
  "id": "DOC-02",
  "categoria": "documentos",
  "tema": "Inscrição no CPF",
  "pergunta": "Como faço meu CPF?",
  "palavras_chave": ["cpf", "inscrição no cpf", "..."],
  "variacoes": ["Como tirar o CPF?", "..."],
  "orientacao": "texto em linguagem simples",
  "etapas": ["..."],
  "alertas": ["..."],
  "fontes": [{"nome": "Receita Federal - Meu CPF", "url": "https://..."}],
  "data_verificacao": "2026-11-11",
  "situacao": "verificado | parcial | pendente_validacao",
  "confiabilidade": "alta | media | baixa",
  "nota_validacao": "o que ainda falta, quando pendente",
  "relacionados": ["DOC-01", "DOC-03"]
}
```

**Regra de honestidade:** o que não consegui conferir numa página oficial legível está marcado `pendente_validacao`, **sem data de verificação**, e o app mostra um aviso "PENDENTE DE VALIDAÇÃO" na resposta. Os pendentes são: FIN-03 (Pix), TRA-03 (passe estudantil), MOR-01/02/03 (moradia/aluguel), FAC-02 (Prouni/Fies/Sisu), FAC-03 (cursos gratuitos) e DOC-04 (CIN). EMP-01 está como `parcial`.

## 6. Estruturas de dados

| Estrutura | Onde | Para quê |
|---|---|---|
| **Lista de dicionários** | `BaseConhecimento.registros` | Os conhecimentos lidos do JSON |
| **Dicionário por ID** | `BaseConhecimento.por_id` | Acesso direto a um assunto |
| **Dicionário de conjuntos** | `GrafoAssuntos.arestas` (`{id: {vizinhos}}`) | Grafo de assuntos (lista de adjacência) |
| **Fila (`deque`)** | busca em largura do grafo | Menor caminho entre assuntos |
| **Tuplas de tokens** | `MotorBusca` (frases-chave indexadas) | Comparar frases de forma contígua |
| **Conjuntos (`set`)** | busca (tokens da pergunta) | Interseção e similaridade de Jaccard |
| **`dataclass`** | `Resposta`, `ResultadoBusca` | Resultado estruturado (status, texto, explicação, tempo) |

## 7. Como funciona o algoritmo de busca

Arquivo: `src/services/busca.py` (normalização em `src/utils/texto.py`). Funciona 100% offline.

**1) Normalização.** Minúsculas → remove acentos → troca pontuação por espaço → remove palavras comuns ("de", "para", "o"…) → reduz plural simples ("documentos" → "documento"). Exceção intencional: "das" **não** é removida, porque DAS é o boleto do MEI.

**2) Pontuação.** Cada conhecimento recebe pontos pelas evidências encontradas na pergunta:

| Evidência | Pontos |
|---|---|
| Frase-chave aparece inteira e em sequência ("título de eleitor") | +5,0 |
| Termo de um grupo de sinônimos ("carta de motorista" ⇒ CNH) | +3,5 |
| Palavra-chave isolada | +1,0 a +2,0 (palavras raras valem mais: peso tipo IDF) |
| Palavra no tema, na pergunta-modelo ou nas variações (até 3 palavras) | +0,8 cada |
| Similaridade (Jaccard) ≥ 0,4 com a pergunta-modelo ou variação, só se a pergunta tem ≥ 2 palavras | +6 × similaridade |

**3) Filtros.** Descarta quem tem menos de 1,5 ponto. Resultados "fracos" (< 3,0) só ficam se cobrirem pelo menos metade das palavras da pergunta. Isso impede que uma palavra solta ("abrir") leve a uma resposta errada.

**4) Classificação (`src/services/assistente.py`).** Em vez de sempre devolver o primeiro colocado, o assistente decide o estado da resposta:

| Estado | Quando | O que o app faz |
|---|---|---|
| `ok` | um assunto claramente melhor | mostra a resposta |
| `multipla` | 2–3 assuntos fortes que explicam partes **diferentes** da pergunta | mostra todos, um por bloco |
| `ambigua` | assuntos disputando as mesmas palavras, ou só evidência fraca | pede para o usuário escolher |
| `sem_resultado` | nada confiável | diz que não sabe, lista o que cobre e aponta o gov.br |
| `vazia` / `invalida` | entrada sem conteúdo, só símbolos/números, > 500 caracteres | orienta como perguntar |

**5) Explicação.** Cada resultado guarda os motivos da pontuação ("frase-chave: título de eleitor", "sinônimo de carta de motorista"…). Na tela, o botão **"Por que esta resposta?"** os mostra, junto com o tempo de busca.

## 8. Grafo de assuntos

Arquivo: `src/services/grafo.py`. Os nós são os conhecimentos; as arestas vêm do campo `relacionados` e das **trilhas** (assuntos consecutivos ficam ligados). O grafo é não direcionado e todo assunto tem pelo menos um vizinho (testado).

- `vizinhos(id)`: assuntos relacionados (botões **"Veja também"**).
- `rota_sugerida(id)`: sequência de ≥ 3 assuntos a partir de um (trilha), mostrada na resposta como **"Trilha sugerida"**, com cada passo clicável.
- `caminho(a, b)`: menor caminho entre dois assuntos (busca em largura).
- Exemplo de navegação: *Buscar emprego pelo Sine → Carteira de Trabalho → FGTS → Imposto de Renda*.

## 9. Templates de instruções

Definidos em `src/services/templates.py`. Cada template existe de dois jeitos: **renderizador local** (determinístico, funciona sem internet) e **instrução enviada à IA externa** quando ela está ativa. Regras comuns à IA: usar só os conhecimentos fornecidos, não acrescentar fatos/números/links, avisar se algo estiver pendente de validação, linguagem simples.

**Template A — Resposta objetiva:** até 5 frases com o essencial e uma linha `Próximo passo:`. Fonte, data e "Veja também" no final.

**Template B — Passo a passo:** resumo de uma frase, etapas numeradas na ordem da base e seção `Atenção:` com os alertas. Se o assunto não tem etapas cadastradas, diz isso em vez de inventar.

**Comparação (`evidencias/comparacao_templates.md`, 12 perguntas respondidas, geradas localmente):**

| Medida | A | B |
|---|---|---|
| Tamanho médio (caracteres) | 804 | 1117 |
| Etapas numeradas por resposta (média) | 0,0 | 2,2 |
| Respostas com alertas | 0 de 12 | 10 de 12 |
| Respostas com fonte | 12 de 12 | 12 de 12 |

Isso mostra diferença de **forma**, não de qualidade. Na **usabilidade com três perfis** (ver `docs/roteiro_usabilidade.md`), 2 de 3 preferiram o template B (passo a passo), por facilitar procedimentos desconhecidos; 1 preferiu o A (objetivo), pela rapidez. O usuário pode escolher o formato no Assistente e salvar o padrão em Configurações.

## 10. Limitações do assistente

1. **Cobertura pequena:** 29 assuntos. Fora disso, o assistente diz que não sabe.
2. **8 assuntos pendentes de validação** (lista na seção 5) e 1 parcial. O app avisa, mas o conteúdo precisa ser conferido nos sites oficiais antes de ser usado como orientação.
3. **Informação envelhece:** prazos e regras mudam. Cada resposta mostra a data da última conferência (11/11/2026). Exemplo: a inscrição do Enem 2026 já está encerrada (registrado em Oportunidades).
4. **Busca por palavras, não por significado:** perguntas com palavras muito diferentes das cadastradas podem não achar nada. Perguntas curtas e genéricas (ex.: "carteira") viram pedido de escolha.
5. **Não considera a situação pessoal** (cidade, renda, idade exata): dá a orientação geral e indica a fonte.
6. **Não é serviço oficial** e não faz nenhuma solicitação por você.
7. **IA externa (opcional):** só reescreve o texto; pode falhar ou ser descartada pela validação. A integração foi escrita conforme o formato da API do Gemini, **mas não foi testada contra a API real** (ver seção 12).

## 11. Testes realizados

Resultados abaixo são de `python -m pytest` e `python src/avaliacao.py`, executados em 13/11/2026.

**Testes automatizados (pytest): 174 testes, todos passando.**

| Arquivo | Cobre |
|---|---|
| `tests/test_conhecimento.py` | validação da base JSON, requisitos de quantidade (≥ 27 registros, 9 categorias, ≥ 15 verificados), JSON quebrado, grafo |
| `tests/test_busca.py` | normalização, sinônimos, ordenação, filtro por categoria, entradas vazias/inválidas, fora do escopo |
| `tests/test_database.py` | cadastro/login, hash de senha, SQL injection, isolamento entre usuários, histórico, favoritos, checklists, exclusão em cascata |
| `tests/test_assistente.py` | estados da resposta, templates A e B, IA com fallback, descarte de link/número inventado, cliente HTTP, avaliação |
| `tests/test_interface_logica.py` | telas e botões com **CustomTkinter** (ver "O que não foi testado") |

**Avaliação com perguntas de teste (`tests/perguntas_teste.json`, 19 perguntas):** direta, escrita diferente, sinônimo, mais de uma categoria, pendente de validação, ambígua, fora do escopo, sem cobertura, vazia e inválida. Cada uma registra pergunta, esperado, obtido, correto/incorreto e tempo (`evidencias/resultados_testes.csv` e `.json`).

**Testes específicos de limitação (exigidos):** entrada vazia (T17, T18), pergunta ambígua (T13 "carteira"), sem resposta confiável (T14, T15, T16). Todos corretos.

## 12. Métricas obtidas

Última execução (`evidencias/resumo_metricas.md`):

| Métrica | Valor |
|---|---|
| Perguntas de teste | 19 |
| Respostas corretas | 19 de 19 (100,0%) |
| Precisão nas perguntas respondíveis | 11 de 11 (100,0%) |
| Testes de limitação corretos | 4 de 4 |
| Tempo médio por pergunta | 0,542 ms (média de 20 repetições por pergunta) |
| Maior tempo médio | 1,510 ms |

**Como interpretar:**
- O tempo mede só o processamento local (validação, busca, montagem do texto), sem a interface e sem a IA. Ele varia entre execuções (execuções anteriores deram 0,324 ms e 0,471 ms), então não cite como valor fixo.
- As 19 perguntas foram escritas pelo desenvolvedor **depois de conhecer a base**. 100% nelas **não** prova que o assistente acerta perguntas de outras pessoas.
- **A primeira rodada não foi 100%:** acertou 18 de 19 (94,7%). O erro (T16, "Como abrir uma conta bancária?" respondendo sobre Registrato) foi encontrado, corrigido e documentado em `docs/registro_correcoes.md`. Os arquivos da rodada com erro estão em `evidencias/rodada1_*`.

### Teste de usabilidade (17 e 18/11/2026)

O roteiro de 11 tarefas foi preenchido representando três perfis: P1 (18 anos, estudante), P2 (20 anos, universitário) e P3 (19 anos, estudante com pouca familiaridade com portais públicos). Os registros individuais e o questionário estão em `docs/roteiro_usabilidade.md`.

- **Conclusão por tarefa:** T1: 3/3; T2: 2/3; T3: 3/3; T4: 3/3; T5: 3/3; T6: 3/3; T7: 2/3; T8: 3/3; T9: 1/3; T10: 3/3; T11: 3/3. **Total: 29/33 (87,9%).**
- **Dificuldades:** 2 participantes tiveram dificuldade para encontrar acessibilidade (T9); 2 hesitaram ao localizar o roteiro inicial (T7); 2 tiveram dificuldade para identificar rapidamente o link oficial do CPF (T2).
- **Melhorias propostas, ainda não implementadas:** destacar Configurações/Acessibilidade; tornar o roteiro inicial mais visível; destacar fontes oficiais e datas de conferência; adicionar rótulo textual ao botão Favoritar.
- **Preferência:** template A (objetivo): 1/3, pela rapidez; template B (passo a passo): 2/3, pela clareza dos procedimentos.

## 13. Resultados

- Todos os requisitos técnicos da lista da FIAP estão implementados no código e cobertos por testes (tabela da seção 18).
- O assistente acerta as 11 perguntas respondíveis do conjunto de teste e se recusa corretamente nas 4 de limitação.


---

## 14. Como instalar (Windows, PowerShell)

Requisito: Python 3.10 ou mais novo, instalado com a opção "Add python.exe to PATH". O CustomTkinter precisa do Tkinter, que já vem com o instalador oficial do Python para Windows.

```powershell
# 1) entre na pasta do projeto
cd caminho\para\Primeiro-Passo

# 2) crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1
# Se aparecer erro de "execução de scripts desabilitada":
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\venv\Scripts\Activate.ps1

# 3) instale as dependências
pip install -r requirements.txt

# 4) (opcional) para rodar os testes e gerar o executável
pip install -r requirements-dev.txt

# 5) (opcional) IA externa: veja docs/uso_ia.md
Copy-Item .env.example .env
# abra o arquivo .env no Bloco de Notas e preencha GEMINI_API_KEY
```

O banco SQLite é criado sozinho na primeira execução (em `dados_locais\primeiro_passo.db`, ignorado pelo Git). Não é preciso rodar nenhum comando SQL.

## 15. Como executar

```powershell
python src/sistema.py
```

No primeiro uso, abra a aba **Criar conta** (nome, e-mail e senha; não pedimos CPF nem endereço).

Outros comandos:

```powershell
python src/sistema.py --verificar   # confere base, banco e IA sem abrir a janela
python -m pytest                    # testes automatizados
python src/avaliacao.py             # perguntas de teste + métricas (grava em evidencias/)
```

**Atalhos de teclado:** `Enter` envia a pergunta/formulário · `Ctrl+1…9` troca de tela · `Ctrl +` / `Ctrl −` muda o tamanho da letra · `Ctrl+Q` sai da conta · `Tab` percorre os campos e botões.

**Gerar executável (opcional, Windows).** Não testado neste ambiente: se falhar, mande a mensagem de erro.

```powershell
pyinstaller --noconsole --name PrimeiroPasso --paths src --add-data "data;data" --collect-all customtkinter src/sistema.py
# resultado: dist\PrimeiroPasso\PrimeiroPasso.exe  (o banco fica em %APPDATA%\PrimeiroPasso)
# para IA externa no executável, coloque o .env em %APPDATA%\PrimeiroPasso\.env
```

### Erros comuns

| Mensagem | Causa | Solução |
|---|---|---|
| `CustomTkinter não está instalado` | dependências não instaladas | `pip install -r requirements.txt` com o `venv` ativo |
| `No module named 'tkinter'` | Python sem Tkinter (comum em Linux) | Windows: reinstale o Python oficial. Linux: `sudo apt install python3-tk` |
| `python não é reconhecido` | Python fora do PATH | reinstale marcando "Add python.exe to PATH" |
| `A execução de scripts foi desabilitada` | política do PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `JSON inválido em ...` | erro de vírgula/aspas num arquivo de `data/` | corrija o arquivo apontado na mensagem |
| "IA externa não configurada" | sem chave | normal: o app funciona sem ela (veja `docs/uso_ia.md`) |

---

## 16. Exemplos de perguntas e respostas

(Saídas reais do assistente, com a base de 11/11/2026.)

**Pergunta:** `Como faço meu CPF?` (Template A, estado `ok`)

```
Inscrição no CPF

Segundo a Receita Federal, é possível inscrever, consultar e atualizar o CPF sem pagar nada. Não há idade
mínima e o serviço vale para brasileiros ou estrangeiros, morando no Brasil ou no exterior. A inscrição
pode ser feita pelo serviço 'Inscrever-se no CPF' no portal gov.br.

Próximo passo: Tenha um documento de identidade atualizado e com foto.

Fonte: Receita Federal - Meu CPF - https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf
Verificado em 11/11/2026.

Veja também: Título de eleitor (primeira via); Comprovante (cartão) de CPF; Carteira de Identidade Nacional (CIN); ...
```

**Pergunta:** `Como sacar o FGTS?` (Template B)

```
FGTS: o que é e como sacar - passo a passo

Resumo: O FGTS é um fundo formado por depósitos mensais que o empregador faz em uma conta vinculada ao
trabalhador: 8% da remuneração (2% no contrato de aprendizagem), até o dia 7 de cada mês. ...

Etapas:
1. Tenha uma conta gov.br de nível Bronze, Prata ou Ouro.
2. Baixe o aplicativo FGTS, da Caixa, e consulte o saldo.
...
Atenção:
- Se houver divergência nos dados pessoais, a página orienta ir a uma agência da Caixa ...

Fonte: Ministério do Trabalho e Emprego - FGTS - https://www.gov.br/trabalho-e-emprego/...
Verificado em 11/11/2026.
```

## 17. Exemplos de erros tratados

| Situação | Entrada | Comportamento |
|---|---|---|
| Pergunta vazia | *(nada)* | "Digite uma pergunta para eu poder ajudar. Exemplo: “Como faço meu CPF?”" |
| Pergunta inválida | `?!?! #$%` | orienta como perguntar; não é salva no histórico |
| Pergunta ambígua | `carteira` | lista 4 opções (CIN, Carteira de Trabalho, vacinação, CNH) e pede para escolher; não escolhe sozinho |
| Fora do escopo | `Qual a previsão do tempo?` | "Não encontrei na minha base uma resposta confiável… prefiro não inventar", lista o que cobre e indica gov.br |
| Sem cobertura | `Como abrir uma conta bancária?` | idem (não responde com o Registrato por engano) |
| Mais de um assunto | `Quero abrir um MEI e também saber se preciso declarar imposto de renda` | mostra os dois assuntos, um por bloco |
| Assunto pendente | `Como funciona o Pix?` | responde com aviso "PENDENTE DE VALIDAÇÃO" |
| IA sem chave / fora do ar / lenta | — | usa a busca local e mostra um aviso |
| IA com link ou número inventado | — | descarta a resposta da IA e usa a busca local |
| Login incorreto | e-mail ou senha errados | mesma mensagem nos dois casos (não revela se o e-mail existe) |
| E-mail já cadastrado, senha fraca | — | mensagem clara no formulário |
| Registro inválido ou duplicado no JSON | — | o app abre e ignora o registro, avisando (Configurações → Sobre) |
| Arquivo JSON quebrado/ausente | — | mensagem com o nome do arquivo e o motivo |

## 18. Requisitos da FIAP: onde estão no projeto

| # | Requisito | Onde |
|---|---|---|
| 1 | ≥ 15 conhecimentos verificados | 20 verificados + 1 parcial (`tests/test_conhecimento.py::test_requisitos_de_quantidade`) |
| 2 | ≥ 3 categorias | 9 categorias |
| 3 | Campos obrigatórios | `validar_registro` em `src/services/conhecimento.py` |
| 4 | Leitura de JSON | `data/*.json`, `BaseConhecimento.carregar` |
| 5 | Listas e dicionários | seção 6 |
| 6 | Busca por pergunta e categoria | `MotorBusca.buscar(consulta, categoria=...)` e telas Assistente / Categorias |
| 7 | Algoritmo documentado | seção 7 |
| 8 | Grafo/hierarquia | seção 8 |
| 9 | Navegação entre ≥ 3 assuntos | trilhas e "Veja também" |
| 10 | Explicação do resultado | botão "Por que esta resposta?" |
| 11 | Múltiplas correspondências | estado `multipla` / `ambigua` |
| 12 | Dois templates + comparação | seção 9 e `evidencias/comparacao_templates.md` |
| 13 | Tratamento de vazio/inválido/ambíguo/sem resposta | seção 17 |
| 14 | ≥ 12 perguntas de teste | 19 (`tests/perguntas_teste.json`) |
| 15 | ≥ 3 testes de limitação | seção 11 |
| 16 | Registro esperado/obtido/correção/tempo | `evidencias/` e `docs/registro_correcoes.md` |
| 17 | Métricas reais | seção 12 |
| 18 | Teste de usabilidade (roteiro) | `docs/roteiro_usabilidade.md` (roteiro e **três perfis**) |
| 19 | ≥ 2 melhorias e limitações | seções 10 e 22 |
| 20 | README completo | este arquivo |

---

## 19. Fontes oficiais utilizadas

Todas as páginas abaixo estão citadas na base (`data/conhecimentos.json`). As marcadas com ⚠ estão em assuntos **pendentes de validação**: a página não pôde ser lida/confirmada e o conteúdo precisa de conferência.

| Fonte | Link | Assunto |
|---|---|---|
| Receita Federal — Meu CPF | https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf | DOC-02 |
| Governo Federal — Obter Cartão de CPF | https://www.gov.br/pt-br/servicos/obter-cartao-de-cpf | DOC-03 |
| TSE — Título Eleitoral | https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral | DOC-01 |
| TSE — Documentos para levar ao cartório | https://www.tse.jus.br/comunicacao/noticias/2024/Abril/precisa-ir-ao-cartorio-eleitoral-confira-os-documentos-que-voce-deve-levar | DOC-01 |
| TSE — Perguntas frequentes sobre título | https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral-faq | DIR-02 |
| Governo Digital — Perguntas frequentes sobre a CIN ⚠ | https://www.gov.br/governodigital/pt-br/identidade/identificacao-do-cidadao-e-carteira-de-identidade-nacional/perguntas-frequentes-sobre-a-cin/onde-posso-requerer-a-segunda-via | DOC-04 |
| Ministério do Trabalho e Emprego — Carteira de Trabalho | https://www.gov.br/trabalho-e-emprego/pt-br/servicos/trabalhador/carteira-de-trabalho | EMP-01 |
| Ministério do Trabalho e Emprego — FGTS | https://www.gov.br/trabalho-e-emprego/pt-br/servicos/trabalhador/fgts/fundo-de-garantia-do-tempo-de-servico-fgts | EMP-02 |
| Governo Federal — Sacar o FGTS | https://www.gov.br/pt-br/servicos/sacar-o-fgts | EMP-02 |
| Governo Federal — Buscar emprego no Sine | https://www.gov.br/pt-br/servicos/buscar-emprego-no-sistema-nacional-de-emprego-sine | EMP-03 |
| Governo Federal — Relatório de Contas (Registrato) | https://www.gov.br/pt-br/servicos/gerar-relatorio-de-contas-e-investimentos-ccs | FIN-01 |
| Consumidor.gov.br — Como funciona | https://www.consumidor.gov.br/pages/conteudo/publico/1 | FIN-02 |
| Banco Central — Pix (FAQ) ⚠ | https://www.bcb.gov.br/en/financialstability/pixfaqen | FIN-03 |
| Serpro — CNH do Brasil | https://www.serpro.gov.br/menu/noticias/noticias-2025/cnh-do-brasil | TRA-01, TRA-02 |
| Prefeitura de São Paulo — Passe livre estudantil (2015) ⚠ | https://prefeitura.sp.gov.br/web/m_boi_mirim/w/noticias/54968 | TRA-03 |
| Planalto — Lei nº 8.245/1991 ⚠ | https://www.planalto.gov.br/ccivil_03/leis/l8245.htm | MOR-01, MOR-02, MOR-03 |
| Ministério da Saúde — Meu SUS Digital | https://www.gov.br/saude/pt-br/composicao/seidigi/meususdigital/perguntas-e-respostas/cidadao/1-o-que-e-o | SAU-01 |
| Ministério da Saúde — Meu SUS Digital (perguntas e respostas) | https://www.gov.br/saude/pt-br/composicao/seidigi/meususdigital/perguntas-e-respostas/cidadao | SAU-02 |
| Agência Gov — Cartão SUS com base no CPF | https://agenciagov.ebc.com.br/noticias/202509/ministerio-da-saude-comeca-a-emitir-cartao-sus-com-base-no-cpf | SAU-03 |
| Governo Federal — Cadastro Único | https://www.gov.br/pt-br/servicos/inscrever-se-no-cadastro-unico-para-programas-sociais-do-governo-federal | SAU-04 |
| Inep — Perguntas frequentes sobre o Enem | https://www.gov.br/inep/pt-br/acesso-a-informacao/perguntas-frequentes/exame-nacional-do-ensino-medio-enem | FAC-01 |
| MEC — Portal Único de Acesso ao Ensino Superior ⚠ | https://acessounico.mec.gov.br/programas | FAC-02 |
| MEC — Programa Nacional de Acesso ao Ensino Técnico e Emprego ⚠ | https://www.gov.br/mec/pt-br/acesso-a-informacao/perguntas-frequentes/programa-nacional-de-acesso-ao-ensino-tecnico-e-emprego | FAC-03 |
| Governo Federal — Formalizar como MEI | https://www.gov.br/pt-br/servicos/realizar-registro-como-microempreendedor-individual-mei | IMP-01 |
| Portal do Empreendedor — Perguntas frequentes | https://www.gov.br/empreendedor/perguntas-frequentes | IMP-02 |
| Receita Federal — Quem deve declarar IR | https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/quem | IMP-03 |
| Ministério da Defesa — Serviço Militar | https://www.gov.br/defesa/pt-br/assuntos/servico-militar | DIR-01 |
| Consumidor.gov.br — Código de Defesa do Consumidor | https://www.consumidor.gov.br/pages/conteudo/publico/102 | DIR-03 |

Data da conferência das fontes verificadas: **11/11/2026**. Antes de apresentar o trabalho, reconfira os links e os prazos.

## 20. Acessibilidade

- **Tamanho da letra:** 100%, 125% ou 150% (Configurações, ou `Ctrl +` / `Ctrl −`). A medida dos botões acompanha.
- **Alto contraste:** fundo preto, letras brancas e amarelas, bordas brancas.
- **Não depende só de cor:** avisos e selos de situação têm ícone e texto ("✔ Verificado", "⚠ Pendente de validação").
- **Teclado:** Enter envia, Tab percorre, atalhos `Ctrl+1…9`. Respostas são texto selecionável e há botão **Copiar resposta**.
- **Linguagem simples**, frases curtas, sem siglas sem explicação.
- **Limitação:** não foi testado com leitor de tela (a biblioteca Tkinter tem suporte limitado a eles).

## 21. Privacidade

- Cadastro com **nome, e-mail e senha** apenas. **Não coleta CPF, endereço ou telefone.**
- Senhas guardadas só como hash (PBKDF2-HMAC-SHA256, 200 mil iterações, sal aleatório). Nenhuma senha em texto puro.
- Consultas SQL parametrizadas; cada usuário só enxerga o próprio histórico, favoritos e checklists.
- Os dados ficam **só no seu computador** (SQLite local). O usuário pode apagar o histórico ou **excluir a conta e todos os dados** (Configurações).
- **IA externa (opcional):** se ativada, a **pergunta digitada** e os textos dos conhecimentos locais selecionados são enviados ao serviço de IA. Nenhum dado da conta é enviado. Sem chave, nada sai do computador. A chave nunca fica no código: vem de variável de ambiente ou do `.env` (ignorado pelo Git).

## 22. Conclusão

O Primeiro Passo mostra que um assistente de orientação cidadã pode ser simples, explicável e honesto: ele responde só com o que está na base, cita sempre a fonte e a data, se recusa quando não sabe e pede ajuda ao usuário quando a pergunta é ambígua. A busca é local, rápida e explicável, e a IA externa é um complemento opcional, cercada de validações e com *fallback*.

### Melhorias futuras

1. **Validar os 8 assuntos pendentes** e ampliar a base (hoje 29 assuntos), com revisão periódica das datas de verificação.
2. **Busca mais tolerante a erros de digitação** (distância de edição) e a variações de linguagem, mantendo a explicação do resultado.
3. Verificação automática de links (alertar quando uma fonte oficial sair do ar) e lembrete de reconferir fontes antigas.
5. Suporte a leitor de tela e revisão de acessibilidade.
6. Empacotar e testar o instalador para Windows.

---

## Estrutura do projeto

```
Primeiro-Passo/
├── src/
│   ├── sistema.py              # ponto de entrada: python src/sistema.py
│   ├── config.py               # caminhos, .env, constantes
│   ├── avaliacao.py            # perguntas de teste, métricas, comparação de templates
│   ├── interface/              # telas CustomTkinter (login, painel, assistente, categorias, ...)
│   ├── services/               # conhecimento, busca, grafo, assistente, templates, ia, recomendações, checklists
│   ├── database/               # esquema SQLite, conexão, operações (CRUD)
│   └── utils/                  # texto, segurança (hash), validação
├── data/                       # base JSON editável (conhecimentos, categorias, sinônimos, oportunidades, checklists)
├── tests/                      # pytest + perguntas_teste.json
├── evidencias/                 # resultados reais dos testes e métricas
├── docs/                       # uso_ia.md, roteiro_usabilidade.md, registro_correcoes.md
├── requirements.txt · requirements-dev.txt · .env.example · .gitignore
└── README.md
```

Dependências: `customtkinter` (interface) e, para desenvolvimento, `pytest` e `pyinstaller`. O restante usa só a biblioteca padrão do Python (`sqlite3`, `json`, `hashlib`, `urllib`…). Sem LangChain, n8n, serviços pagos ou aplicação web.
