# Ambiente

O hardware faz parte do estudo: os resultados de tempo e a divisão CPU/GPU valem para esta máquina.

## Hardware

| Item | Valor |
| --- | --- |
| CPU | Intel i5-3330, 3ª geração, 4 núcleos, sem AVX2 |
| GPU | NVIDIA GTX 1060 3GB (~2,7GB livres com o Windows) |
| RAM | 12GB |
| Disco | 297GB livres |
| SO | Windows 10 Pro 64 bits |

## Software

| Programa | Versão |
| --- | --- |
| Driver NVIDIA | 582.78 (Security Update Driver, CUDA 13.0) |
| Ollama | 0.40.15 |
| Python | 3.12.10 |
| Git | 2.56 |
| MySQL | 8.4.9 LTS (serviço `MySQL84`, porta 3306, banco `erp_loja`) |

O driver 582.78 é o último que suporta a arquitetura Pascal. Os drivers 59x e 62x não funcionam nessa placa.

## Checklist antes de cada bateria de testes

1. Fechar Chrome, WhatsApp e Assinador Serpro (liberam VRAM e CPU).
2. Conferir a VRAM livre com `nvidia-smi`.
3. Garantir que só um modelo está carregado (`ollama ps`). Descarregar os outros com `ollama stop <modelo>`.
4. Deixar o PC na tomada e sem outras tarefas pesadas rodando.
5. Anotar no CSV a divisão CPU/GPU mostrada pelo `ollama ps`.

## Teste inicial

`llama3.2:3b` com contexto 4096: 2,9GB e divisão 51% CPU / 49% GPU. O modelo não seguiu a instrução "responda apenas: ok".
