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

## Critérios ainda a definir

- Critérios de nota (escala e quem avalia) para interpretação, resumo e anomalia.
- Número final de rodadas por pergunta (3 a 5).
