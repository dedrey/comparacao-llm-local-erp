# Comparação de LLMs locais para análise de dados de um ERP

Estudo que compara modelos de IA rodando localmente (via [Ollama](https://ollama.com)) em tarefas de análise de dados comerciais de um ERP de loja de roupas. A tarefa principal é transformar uma pergunta em linguagem natural em SQL. O resultado é um relatório estatístico.

Projeto acadêmico do curso de Sistemas de Informação.

> Em andamento: base de dados, perguntas, interface e script de benchmark prontos; rodadas completas e análise estatística em desenvolvimento.

## O que o estudo mede

- **Acerto**: o SQL gerado pelo modelo devolve o mesmo resultado que o SQL-gabarito?
- **Tempo** de resposta e **tokens por segundo**.
- **Divisão CPU/GPU** de cada modelo (`ollama ps`), já que o hardware é limitado.
- **Erros e alucinações**: SQL inválido, tabela ou coluna inventada, resposta fora do formato.

Tarefas avaliadas: texto→SQL, interpretação de tabela, resumo executivo e detecção de anomalias simples. As perguntas têm três níveis de dificuldade: fácil, média e difícil.

## Modelos

| Modelo | Papel |
| --- | --- |
| `qwen2.5-coder:3b` | especializado em código; padrão da interface |
| `llama3.2:3b` | baseline |
| `phi4-mini` | raciocínio e saída estruturada |
| `qwen3.5:4b` | maior que a VRAM, roda com offload (modo thinking desligado) |
| `gemma4:e2b` | modelo do Google |
| `qwen3.5:2b-q4_K_M` | opcional, efeito do tamanho na mesma família |

Todos rodam com temperatura 0 e o mesmo prompt.

## Hardware

Intel i5-3330 (sem AVX2), GTX 1060 3GB, 12GB de RAM, Windows 10. Os detalhes e o checklist antes dos testes estão em [docs/ambiente.md](docs/ambiente.md).

## Como reproduzir

> Os passos serão completados conforme as etapas forem concluídas.

1. Instale Python 3.12, Ollama e MySQL.
2. Baixe os modelos: `ollama pull qwen2.5-coder:3b` e `ollama pull llama3.2:3b` (e os demais da tabela).
3. Crie o banco: `mysql -u root -p --default-character-set=utf8mb4 < banco/schema.sql` e depois o mesmo com `banco/dados.sql` (para gerar de novo: `python banco/gerar_dados.py`).
4. Copie `.env.example` para `.env` e preencha.
5. Rode o benchmark: `python scripts/benchmark.py` (detalhes em [docs/metodologia.md](docs/metodologia.md)). A análise (`scripts/analise.py`) vem na próxima etapa.

O `.env` fica fora do repositório. Nunca faça commit dele.

## Interface web

```bash
python scripts/app.py
```

Abra http://localhost:8000. Escreva uma pergunta em português, escolha o modelo e veja o resultado em tabela e gráfico, o SQL gerado, o tempo, a velocidade (tokens/s) e a divisão CPU/GPU. Clique numa das 30 perguntas do estudo para comparar com o gabarito.

Pelo terminal: `python scripts/perguntar.py` (ou `--modelo llama3.2:3b`).

Como funciona:

1. O modelo recebe o schema das 15 tabelas comerciais, os caminhos de JOIN, as regras do negócio e 4 exemplos (`prompts/texto_para_sql.txt`).
2. O SQL gerado é executado no MySQL. Só `SELECT` é aceito.
3. Se o MySQL der erro, o erro volta para o modelo com uma dica (por exemplo, em qual tabela e com qual apelido está a coluna), e ele tenta de novo até 2 vezes.

Modelos de 3B ainda erram a lógica em parte das perguntas (o SQL roda, mas responde outra coisa). Por isso a interface sempre mostra o SQL usado.

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `docs/` | metodologia, ambiente e decisões do estudo |
| `banco/` | schema do ERP e dados fictícios |
| `perguntas/` | perguntas com SQL-gabarito e nível de dificuldade |
| `prompts/` | prompt, schema resumido e prompt de correção |
| `scripts/` | interface web (`app.py`), terminal (`perguntar.py`), benchmark (`benchmark.py`) e núcleo compartilhado (`nucleo.py`) |
| `resultados/` | CSVs brutos de cada rodada, tabelas e gráficos |
| `relatorio/` | relatório final |

