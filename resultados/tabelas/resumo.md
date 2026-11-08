# Resultados da análise

Gerado por `scripts/analise.py` a partir de 810 execuções (6 modelos, 45 perguntas, 3 rodadas). Unidade de análise: a pergunta (acerto = maioria das rodadas, nota = média, tempo = mediana). IC = intervalo de confiança de 95% (Wilson para proporções, bootstrap para medianas e médias).

## 1. Visão geral por modelo

| Modelo | SQL 1ª tentativa | SQL final | IC SQL final | Nota texto (média) | IC nota | Tempo mediano (s) | IC tempo | Tokens/s | GPU |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4 e2b | 17/30 | 21/30 (70,0%) | 52,1% a 83,3% | 0,67 | 0,50 a 0,83 | 10,8 | 8,5 a 14,3 | 12,2 | 39% |
| qwen2.5-coder 3b | 17/30 | 20/30 (66,7%) | 48,8% a 80,8% | 0,45 | 0,22 a 0,70 | 7,2 | 5,8 a 8,2 | 13,6 | 60% |
| llama3.2 3b | 15/30 | 17/30 (56,7%) | 39,2% a 72,6% | 0,61 | 0,42 a 0,79 | 14,0 | 10,7 a 17,8 | 9,0 | 49% |
| qwen3.5 4b | 13/30 | 15/30 (50,0%) | 33,2% a 66,8% | 0,79 | 0,63 a 0,93 | 23,5 | 20,0 a 35,1 | 4,6 | 27% |
| phi4-mini 3.8b | 11/30 | 13/30 (43,3%) | 27,4% a 60,8% | 0,63 | 0,42 a 0,82 | 16,1 | 13,2 a 19,0 | 6,7 | 40% |
| qwen3.5 2b | 9/30 | 10/30 (33,3%) | 19,2% a 51,2% | 0,43 | 0,23 a 0,64 | 11,1 | 9,6 a 13,9 | 15,7 | 49% |

## 2. Acerto no SQL por nível (após autocorreção)

| Modelo | Fácil | Média | Difícil |
| --- | --- | --- | --- |
| gemma4 e2b | 10/10 | 5/10 | 6/10 |
| qwen2.5-coder 3b | 9/10 | 6/10 | 5/10 |
| llama3.2 3b | 10/10 | 5/10 | 2/10 |
| qwen3.5 4b | 7/10 | 5/10 | 3/10 |
| phi4-mini 3.8b | 7/10 | 5/10 | 1/10 |
| qwen3.5 2b | 6/10 | 4/10 | 0/10 |

## 3. Nota média nas tarefas sem SQL

| Modelo | Interpretação | Resumo | Anomalia |
| --- | --- | --- | --- |
| gemma4 e2b | 0,64 | 0,67 | 0,72 |
| qwen2.5-coder 3b | 0,33 | 0,67 | 0,43 |
| llama3.2 3b | 0,75 | 0,58 | 0,46 |
| qwen3.5 4b | 0,75 | 0,75 | 0,88 |
| phi4-mini 3.8b | 0,64 | 0,76 | 0,50 |
| qwen3.5 2b | 0,42 | 0,35 | 0,52 |

## 4. Acerto no SQL: Q de Cochran e McNemar par a par

Q de Cochran = 17,14, gl = 5, p = 0,004 (há diferença significativa entre os modelos a 5%).

Só A / só B = perguntas que só um dos dois acertou. Bonferroni: p × 15.

| Modelo A | Modelo B | Só A acertou | Só B acertou | p | p (Bonferroni) | Significativo |
| --- | --- | --- | --- | --- | --- | --- |
| gemma4 e2b | qwen2.5-coder 3b | 5 | 4 | 1,000 | 1,000 | não |
| gemma4 e2b | llama3.2 3b | 6 | 2 | 0,289 | 1,000 | não |
| gemma4 e2b | qwen3.5 4b | 9 | 3 | 0,146 | 1,000 | não |
| gemma4 e2b | phi4-mini 3.8b | 9 | 1 | 0,021 | 0,322 | não |
| gemma4 e2b | qwen3.5 2b | 12 | 1 | 0,003 | 0,051 | não |
| qwen2.5-coder 3b | llama3.2 3b | 6 | 3 | 0,508 | 1,000 | não |
| qwen2.5-coder 3b | qwen3.5 4b | 7 | 2 | 0,180 | 1,000 | não |
| qwen2.5-coder 3b | phi4-mini 3.8b | 8 | 1 | 0,039 | 0,586 | não |
| qwen2.5-coder 3b | qwen3.5 2b | 11 | 1 | 0,006 | 0,095 | não |
| llama3.2 3b | qwen3.5 4b | 7 | 5 | 0,774 | 1,000 | não |
| llama3.2 3b | phi4-mini 3.8b | 7 | 3 | 0,344 | 1,000 | não |
| llama3.2 3b | qwen3.5 2b | 9 | 2 | 0,065 | 0,981 | não |
| qwen3.5 4b | phi4-mini 3.8b | 5 | 3 | 0,727 | 1,000 | não |
| qwen3.5 4b | qwen3.5 2b | 9 | 4 | 0,267 | 1,000 | não |
| phi4-mini 3.8b | qwen3.5 2b | 6 | 3 | 0,508 | 1,000 | não |

## 5. Tempo por pergunta: Friedman e Wilcoxon par a par

Friedman: χ² = 94,90, gl = 5, p < 0,001 (há diferença significativa a 5%; n = 45 perguntas).

| Modelo A | Modelo B | Mediana de A − B (s) | p | p (Bonferroni) | Significativo |
| --- | --- | --- | --- | --- | --- |
| gemma4 e2b | qwen2.5-coder 3b | 1,3 | 0,008 | 0,123 | não |
| gemma4 e2b | llama3.2 3b | -1,3 | 0,014 | 0,208 | não |
| gemma4 e2b | qwen3.5 4b | -13,3 | < 0,001 | < 0,001 | sim |
| gemma4 e2b | phi4-mini 3.8b | -5,6 | < 0,001 | 0,010 | sim |
| gemma4 e2b | qwen3.5 2b | -0,4 | 0,929 | 1,000 | não |
| qwen2.5-coder 3b | llama3.2 3b | -2,8 | < 0,001 | < 0,001 | sim |
| qwen2.5-coder 3b | qwen3.5 4b | -12,7 | < 0,001 | < 0,001 | sim |
| qwen2.5-coder 3b | phi4-mini 3.8b | -6,4 | < 0,001 | < 0,001 | sim |
| qwen2.5-coder 3b | qwen3.5 2b | -2,2 | 0,013 | 0,192 | não |
| llama3.2 3b | qwen3.5 4b | -10,3 | < 0,001 | 0,002 | sim |
| llama3.2 3b | phi4-mini 3.8b | -2,1 | 0,352 | 1,000 | não |
| llama3.2 3b | qwen3.5 2b | 1,4 | 0,129 | 1,000 | não |
| qwen3.5 4b | phi4-mini 3.8b | 5,5 | < 0,001 | < 0,001 | sim |
| qwen3.5 4b | qwen3.5 2b | 13,7 | < 0,001 | < 0,001 | sim |
| phi4-mini 3.8b | qwen3.5 2b | 3,9 | 0,013 | 0,202 | não |

## 6. Nota nas tarefas sem SQL: Friedman e Wilcoxon par a par

Friedman: χ² = 14,53, gl = 5, p = 0,013 (há diferença significativa a 5%; n = 15 perguntas).

| Modelo A | Modelo B | Mediana de A − B | p | p (Bonferroni) | Significativo |
| --- | --- | --- | --- | --- | --- |
| gemma4 e2b | qwen2.5-coder 3b | 0,15 | 0,053 | 0,789 | não |
| gemma4 e2b | llama3.2 3b | 0,00 | 0,260 | 1,000 | não |
| gemma4 e2b | qwen3.5 4b | 0,00 | 0,173 | 1,000 | não |
| gemma4 e2b | phi4-mini 3.8b | 0,00 | 0,767 | 1,000 | não |
| gemma4 e2b | qwen3.5 2b | 0,20 | 0,029 | 0,440 | não |
| qwen2.5-coder 3b | llama3.2 3b | 0,00 | 0,241 | 1,000 | não |
| qwen2.5-coder 3b | qwen3.5 4b | -0,33 | 0,013 | 0,190 | não |
| qwen2.5-coder 3b | phi4-mini 3.8b | 0,00 | 0,283 | 1,000 | não |
| qwen2.5-coder 3b | qwen3.5 2b | 0,00 | 0,932 | 1,000 | não |
| llama3.2 3b | qwen3.5 4b | 0,00 | 0,018 | 0,269 | não |
| llama3.2 3b | phi4-mini 3.8b | 0,00 | 0,859 | 1,000 | não |
| llama3.2 3b | qwen3.5 2b | 0,00 | 0,109 | 1,000 | não |
| qwen3.5 4b | phi4-mini 3.8b | 0,00 | 0,201 | 1,000 | não |
| qwen3.5 4b | qwen3.5 2b | 0,33 | 0,005 | 0,075 | não |
| phi4-mini 3.8b | qwen3.5 2b | 0,00 | 0,139 | 1,000 | não |

## 7. Estabilidade entre rodadas (temperatura 0)

| Modelo | Perguntas com resultado diferente entre rodadas | Ids |
| --- | --- | --- |
| gemma4 e2b | 2 | 35, 45 |
| qwen2.5-coder 3b | 0 | — |
| llama3.2 3b | 2 | 39, 42 |
| qwen3.5 4b | 1 | 18 |
| phi4-mini 3.8b | 2 | 33, 39 |
| qwen3.5 2b | 0 | — |
