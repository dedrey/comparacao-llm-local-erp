# Metodologia

## Objetivo

Comparar LLMs locais em tarefas de análise de dados comerciais de um ERP, medindo acerto, tempo e uso de hardware num PC de entrada.

## Base de dados

Schema do ERP acadêmico de uma loja de roupas, em MySQL, com dados fictícios. Os arquivos ficam em `banco/`.

## Perguntas

- De 30 a 50 perguntas em linguagem natural, em `perguntas/perguntas.csv`.
- Cada uma tem: id, nível (fácil, média, difícil), tipo de tarefa, texto da pergunta e SQL-gabarito.
- Tipos de tarefa:
  - **texto→SQL** (principal): o modelo gera o SQL e o script executa e compara com o gabarito;
  - **interpretação de tabela**: o modelo recebe um resultado e responde uma pergunta sobre ele;
  - **resumo executivo**: o modelo resume os números para um gestor;
  - **detecção de anomalias simples**: o modelo aponta valores fora do padrão.

### Formato de `perguntas/perguntas.csv`

São 45 perguntas, em UTF-8, com todos os campos entre aspas.

| Coluna | Conteúdo |
| --- | --- |
| `id` | número da pergunta |
| `nivel` | `facil`, `media` ou `dificil` |
| `tarefa` | `texto_sql`, `interpretacao`, `resumo` ou `anomalia` |
| `pergunta` | texto enviado ao modelo |
| `sql_gabarito` | SQL de referência |
| `ordem_importa` | `1` se a ordem das linhas faz parte da resposta |
| `resposta_esperada` | só nas tarefas sem SQL: a resposta ou os pontos que o texto deve conter |

Distribuição:

| Tarefa | Fácil | Média | Difícil | Total |
| --- | --- | --- | --- | --- |
| texto→SQL | 10 | 10 | 10 | 30 |
| interpretação de tabela | 3 | 2 | 1 | 6 |
| resumo executivo | 0 | 3 | 1 | 4 |
| detecção de anomalia | 1 | 3 | 1 | 5 |

Como cada tarefa usa o gabarito:

- **texto→SQL**: o modelo recebe o schema das 15 tabelas e a pergunta, e devolve um SQL. O script executa os dois SQLs e compara os resultados: os valores (não os nomes das colunas), números arredondados para 2 casas, e a ordem das linhas só quando `ordem_importa = 1`.
- **interpretação, resumo e anomalia**: o script executa o `sql_gabarito` e envia ao modelo só a **tabela resultante** com a pergunta. O modelo nunca vê o SQL. A resposta é comparada com `resposta_esperada`.
- Nas anomalias, o SQL monta uma amostra de cerca de 20 a 60 linhas que mistura linhas normais com as anomalias plantadas, para a tabela caber no contexto. Os `IN (...)` do SQL servem só para garantir que as anomalias entrem na amostra.

Os gabaritos foram conferidos no banco: todos executam, nenhum volta vazio e os "top N" não têm empate no limite.

## Execução

- O script `scripts/benchmark.py` chama cada modelo pela API do Ollama (`http://localhost:11434`).
- Temperatura 0 e o mesmo prompt (`prompts/`) para todos os modelos.
- Cada pergunta é executada de 3 a 5 vezes por modelo (rodadas), para medir a variação de tempo.
- O SQL gerado é executado no MySQL e o resultado é comparado com o do gabarito.
- Cada rodada vira uma linha no CSV em `resultados/brutos/`, com: modelo, pergunta, rodada, acerto (0/1), tempo, tokens/s, divisão CPU/GPU, tipo de erro e alucinação.

## Análise estatística

| O quê | Teste | Por quê |
| --- | --- | --- |
| Visão geral | Estatística descritiva com intervalo de confiança | média e incerteza por modelo |
| Acerto (0/1) | Q de Cochran + McNemar par a par | variável binária, mesmas perguntas para todos (dados pareados) |
| Tempo e notas | Friedman + Wilcoxon com correção de Bonferroni | dados pareados, sem supor normalidade |
| Dificuldade | Mesmas medidas separadas por nível | ver onde cada modelo cai |

Os gráficos principais são boxplots de tempo por modelo e barras de acerto por nível. Tudo é gerado por `scripts/analise.py` em `resultados/tabelas/` e `resultados/graficos/`.

- **Unidade de análise: a pergunta.** As 3 rodadas de cada par (modelo, pergunta) viram um valor só: o acerto é o da maioria das rodadas, a nota é a média e o tempo é a mediana. Assim os modelos ficam pareados pela pergunta.
- **Acerto**: Cochran e McNemar usam as 30 perguntas de texto→SQL, com o acerto após a autocorreção. O McNemar é exato (binomial nos pares discordantes).
- **Tempo**: Friedman e Wilcoxon usam as 45 perguntas. **Notas**: usam as 15 perguntas sem SQL.
- **Intervalos de confiança de 95%**: Wilson para proporções e bootstrap percentil (10.000 reamostragens, semente 2026) para médias e medianas.
- **Bonferroni**: o p de cada comparação par a par é multiplicado por 15 (6 modelos, 15 pares).
- O `% na GPU` do gemma4 vem do nvidia-smi (~1,8GB de 4,6GB), porque o `ollama ps` informa errado para esse modelo.

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts/analise.py
```

## Nota das tarefas sem SQL

A nota é automática e reproduzível, calculada a partir da coluna `pontos_chave` do CSV:

- `;` separa os itens que a resposta precisa conter, e `|` separa as formas aceitas de cada item.
- Antes de comparar, a resposta é normalizada: fica em minúsculo, sem acento e sem separadores entre dígitos. Assim, "R$ 99.079,88" vira "9907988".
- Ids curtos (até 3 dígitos) precisam aparecer isolados. Números longos são aceitos com casas decimais depois.
- **Interpretação e resumo**: a nota é a fração dos itens encontrados (0 a 1).
- **Anomalia com ids** (perguntas 43, 44 e 45): a nota é o F1 entre os ids citados e os ids anômalos. Os candidatos são os ids da 1ª coluna da tabela, e números seguidos de "%" não contam. Quem lista a tabela inteira cita muitos ids normais e tira nota baixa (no teste, 0,15 em vez de 1).
- **Acerto (0/1)**: só quando a nota é 1.

Limitação: a checagem por palavras-chave não avalia a qualidade do texto. Se der tempo, uma amostra das respostas pode ser avaliada à mão para conferir.

## Como rodar o benchmark

```bash
python scripts/benchmark.py                       # qwen2.5-coder:3b e llama3.2:3b, 3 rodadas, 45 perguntas
python scripts/benchmark.py --modelos phi4-mini --rodadas 5
python scripts/benchmark.py --perguntas 1,13,31 --rodadas 1   # teste rápido
```

- Cada modelo é aquecido com uma chamada que não entra no resultado. Depois roda as rodadas e é descarregado da memória antes do próximo.
- Cada execução vira uma linha em `resultados/brutos/benchmark_<data>.csv`, gravada na hora. Se o benchmark for interrompido, o que já rodou fica salvo.
- Colunas: `data_hora, modelo, rodada, id, nivel, tarefa, acerto_1a, acerto, nota, tentativas, segundos, tokens_s, pct_gpu, erro, saida`.
- Erros de infraestrutura (Ollama ou MySQL fora do ar) ficam marcados como `INFRA:` e não contam como erro do modelo.
- Se o modelo não terminar a resposta em 600 s, a execução fica marcada como `TIMEOUT:` e conta como erro do modelo (nota 0, tempo 600 s). Ver decisão 11.
- Tempo medido: ~1h no qwen2.5-coder:3b e ~1h10 no llama3.2:3b, com 3 rodadas.

## Critérios ainda a definir

- Número final de rodadas por pergunta (3 a 5).
