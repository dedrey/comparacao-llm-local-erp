# Decisões

Registro curto das decisões do estudo e do porquê. Uma por item, a mais nova no fim.

## 1. Rodar os modelos com o Ollama

Ele roda modelos quantizados em GPU modesta, faz offload automático para a CPU e tem uma API HTTP simples (`localhost:11434`). Assim o mesmo script serve para todos os modelos.

## 2. Temperatura 0 e o mesmo prompt para todos

Reduz a aleatoriedade e deixa a comparação justa: a diferença no resultado vem do modelo, não do prompt.

## 3. Modo thinking desligado no qwen3.5

Os outros modelos não têm modo de raciocínio estendido. Com o thinking ligado, o qwen gastaria muito mais tokens e tempo, e a comparação não seria justa.

## 4. Divisão CPU/GPU como variável do estudo

Com 3GB de VRAM, alguns modelos não cabem inteiros na GPU. Em vez de esconder isso, a divisão é medida e analisada junto com o tempo.

## 5. Testes não paramétricos e pareados

Todos os modelos respondem às mesmas perguntas, então os dados são pareados. O acerto é binário (Cochran e McNemar), e tempo e notas não devem ter distribuição normal (Friedman e Wilcoxon, com Bonferroni nas comparações múltiplas).

## 6. Schema real do ERP e dados gerados por script

O banco usa o schema do ERP acadêmico sem alterações (32 tabelas), para o teste ser realista. Os dados são fictícios e gerados por `banco/gerar_dados.py`, só com a biblioteca padrão e semente fixa (2026). Rodar o script de novo gera exatamente o mesmo `dados.sql`.

Volumes: 150 clientes, 40 produtos (229 variações de cor e tamanho), 8 fornecedores, 60 compras, 1.500 vendas (1.416 finalizadas, 77 canceladas e 7 abertas) e 503 parcelas de crediário. O período vai de nov/2025 a out/2026, com pico em dezembro e queda em fevereiro.

Tabelas que ficam vazias por não fazerem parte do estudo: usuarios, transportadoras, veiculos, nfes, nfes_produtos, movimentacoes_estoque (e itens) e contas_pagar.

Regras dos dados que as perguntas e os gabaritos precisam respeitar:

- A data da venda é `vendas.criado_em`. Não existe uma coluna `data_venda`.
- Faturamento considera só vendas com `status_venda = 'FINALIZADA'`.
- `vendas_itens.valor_total` não tem o desconto da venda. O desconto fica em `vendas.valor_desconto`, e o valor líquido é `vendas.valor_total`.
- O custo atual fica em `produto_variacoes.preco_custo` (vindo da última compra). A categoria e a marca ficam em `produtos`.
- Data de referência para "vencida": 07/11/2026.

## 7. Anomalias plantadas (gabarito da tarefa de detecção)

| Anomalia | Onde está |
| --- | --- |
| Semana com vendas fora do padrão | 13 a 19/07/2026: 102 vendas, contra cerca de 20 a 35 nas outras semanas |
| Cliente com compras muito acima da média | cliente 42: R$ 59.619,85 em vendas finalizadas, contra uma média de R$ 5.026,71 por cliente |
| Vendas com desconto acima de 50% | vendas 39 (70%), 265 (70%), 588 (60%) e 951 (55%) |
| Itens vendidos abaixo do custo | (venda, variação): (8, 24), (75, 21), (394, 185), (422, 15), (450, 101) |
| Estoque zerado | variações 53, 144 e 188 |
| Estoque negativo | variações 1 (-5) e 151 (-2) |
| Inadimplência | 55 parcelas de crediário vencidas e em aberto |

## 8. Prompt com caminhos de JOIN, regras e exemplos

Nos primeiros testes livres, o `llama3.2:3b` inventava colunas (`pv.quantidade`, `vendas.categoria_id`), pulava a tabela `produto_variacoes` e chutava o ano (2023). O prompt (`prompts/texto_para_sql.txt`) passou a trazer:

- os caminhos de JOIN;
- onde fica cada medida (estoque, faturamento total ou por item);
- o período dos dados (nov/2025 a out/2026);
- 4 exemplos que não fazem parte das 30 perguntas.

O prompt continua o mesmo para todos os modelos.

## 9. Autocorreção com dica

Quando o MySQL devolve erro, o erro volta para o modelo junto com uma dica gerada a partir do schema (por exemplo, "a coluna cidade é da tabela cidades, que no seu SQL tem o apelido ci"), e ele tem até 2 novas tentativas. Sem a dica, os modelos repetiam o mesmo SQL. No estudo serão registrados os dois números: o acerto na 1ª tentativa e o acerto após a correção.

## 10. qwen2.5-coder:3b como modelo padrão da interface

Foi incluído por ser treinado para código e SQL e caber na GPU (1,9GB). Nas 30 perguntas de texto→SQL (rodada exploratória, prompt da decisão 8, autocorreção ainda sem dica):

| Modelo | 1ª tentativa | Com correção | Fácil | Média | Difícil | tokens/s | CPU/GPU |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.2:3b | 12/30 | 13/30 | 9/10 | 2/10 | 2/10 | ~10 | 51% / 49% |
| qwen2.5-coder:3b | 17/30 | 18/30 | 9/10 | 5/10 | 4/10 | ~15 | 40% / 60% |
| qwen2.5-coder:3b, autocorreção com dica | 17/30 | 20/30 | 9/10 | 6/10 | 5/10 | ~15 | 40% / 60% |

A dica de apelido recuperou as perguntas 17 e 25, que antes falhavam nas 3 tentativas.

O llama rodou com uma versão anterior do prompt, então os números não são diretamente comparáveis. A comparação oficial será feita pelo script de benchmark, com o prompt congelado e 3 a 5 rodadas.
