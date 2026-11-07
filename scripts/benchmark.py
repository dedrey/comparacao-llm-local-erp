"""Roda o benchmark: cada modelo responde às perguntas do CSV várias vezes.

Grava uma linha por (modelo, rodada, pergunta) em resultados/brutos/benchmark_<data>.csv.
O arquivo é escrito linha a linha, então uma execução interrompida não perde o que já rodou.

Uso:
    python scripts/benchmark.py                                   # modelos padrão, 3 rodadas, 45 perguntas
    python scripts/benchmark.py --modelos qwen2.5-coder:3b --rodadas 1 --perguntas 1,31,37

Antes de rodar: feche Chrome, WhatsApp e Assinador Serpro, e não use a interface web.
"""

import argparse
import csv
import re
import sys
import time
import unicodedata
from datetime import datetime

from nucleo import (RAIZ, ErroSQL, carregar_perguntas, descarregar, executar_sql, gerar,
                    percentual_gpu, perguntar)

MODELOS_PADRAO = ["qwen2.5-coder:3b", "llama3.2:3b"]
PROMPT_TABELA = (RAIZ / "prompts" / "analise_tabela.txt").read_text(encoding="utf-8")
CAMPOS = ["data_hora", "modelo", "rodada", "id", "nivel", "tarefa", "acerto_1a", "acerto",
          "nota", "tentativas", "segundos", "tokens_s", "pct_gpu", "erro", "saida"]


# ------------------------------------------------------------------ avaliação de texto
def normalizar_texto(texto):
    """Minúsculo, sem acento e sem separador de milhar/decimal entre dígitos."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"(?<=\d)[.,](?=\d)", "", texto)


def tem_alternativa(texto, alternativa):
    if alternativa.isdigit():
        # número curto (id) precisa estar isolado; número longo só à esquerda (aceita casas decimais)
        fim = r"(?!\d)" if len(alternativa) <= 3 else ""
        return re.search(rf"(?<!\d){alternativa}{fim}", texto) is not None
    return alternativa in texto


def nota_por_pontos(resposta, pontos_chave):
    """Fração dos pontos-chave encontrados na resposta (0 a 1)."""
    itens = [i for i in pontos_chave.split(";") if i]
    texto = normalizar_texto(resposta)
    achados = sum(any(tem_alternativa(texto, a) for a in item.split("|")) for item in itens)
    return achados / len(itens)


def nota_f1_ids(resposta, pontos_chave, candidatos):
    """Anomalias por id: F1 entre os ids citados e os ids anômalos.

    candidatos = ids da 1ª coluna da tabela. Citar linhas normais derruba a precisão,
    então listar a tabela inteira não ganha nota máxima. Ids de 1 dígito são ignorados
    (confundem com numeração de lista).
    """
    texto = normalizar_texto(resposta)
    certos = {i for i in pontos_chave.split(";") if i}
    validos = {c for c in candidatos if c.isdigit() and len(c) >= 2} | certos
    # número seguido de % é percentual, não id
    citados = {c for c in validos if re.search(rf"(?<!\d){c}(?![\d%]|\s%)", texto)}
    acertos = len(citados & certos)
    if not acertos:
        return 0.0
    precisao, revocacao = acertos / len(citados), acertos / len(certos)
    return 2 * precisao * revocacao / (precisao + revocacao)


def tabela_tsv(colunas, linhas):
    return "\n".join("\t".join(l) for l in [colunas] + linhas)


# ------------------------------------------------------------------ execução
def rodar_sql(modelo, p):
    r = perguntar(modelo, p["pergunta"], p)
    return {"acerto_1a": int(r["acerto_1a"]), "acerto": int(r["acerto_final"]),
            "nota": int(r["acerto_final"]), "tentativas": len(r["tentativas"]),
            "segundos": r["segundos_total"], "tokens_s": r["tentativas"][-1]["tokens_s"],
            "erro": r["erro"] or "", "saida": r["sql"] or ""}


def rodar_texto(modelo, p, tabelas):
    if p["id"] not in tabelas:
        tabelas[p["id"]] = executar_sql(p["sql_gabarito"])
    colunas, linhas = tabelas[p["id"]]
    prompt = PROMPT_TABELA.replace("{tabela}", tabela_tsv(colunas, linhas)).replace("{pergunta}", p["pergunta"])
    resposta, segundos, tokens_s = gerar(modelo, prompt)
    chaves = p["pontos_chave"]
    if p["tarefa"] == "anomalia" and all(i.isdigit() for i in chaves.split(";") if i):
        nota = nota_f1_ids(resposta, chaves, [l[0] for l in linhas])
    else:
        nota = nota_por_pontos(resposta, chaves)
    return {"acerto_1a": int(nota == 1), "acerto": int(nota == 1), "nota": round(nota, 3),
            "tentativas": 1, "segundos": round(segundos, 1), "tokens_s": round(tokens_s, 1),
            "erro": "", "saida": resposta.strip()}


def main():
    parser = argparse.ArgumentParser(description="Benchmark de LLMs locais no ERP.")
    parser.add_argument("--modelos", default=",".join(MODELOS_PADRAO))
    parser.add_argument("--rodadas", type=int, default=3)
    parser.add_argument("--perguntas", help="ids separados por vírgula (padrão: todas)")
    args = parser.parse_args()

    perguntas = list(carregar_perguntas().values())
    if args.perguntas:
        ids = set(args.perguntas.split(","))
        perguntas = [p for p in perguntas if p["id"] in ids]
    modelos = [m.strip() for m in args.modelos.split(",") if m.strip()]

    destino = RAIZ / "resultados" / "brutos" / f"benchmark_{datetime.now():%Y%m%d_%H%M}.csv"
    total = len(modelos) * args.rodadas * len(perguntas)
    print(f"{len(modelos)} modelo(s) x {args.rodadas} rodada(s) x {len(perguntas)} pergunta(s) = {total} execuções")
    print(f"Saída: {destino}")

    tabelas, feitas, inicio = {}, 0, time.perf_counter()
    with destino.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, quoting=csv.QUOTE_NONNUMERIC)
        escritor.writeheader()
        for modelo in modelos:
            print(f"\n== {modelo}: carregando (aquecimento, não entra no resultado)")
            gerar(modelo, "Responda apenas: ok")
            pct_gpu = percentual_gpu(modelo)
            for rodada in range(1, args.rodadas + 1):
                for p in perguntas:
                    try:
                        r = rodar_sql(modelo, p) if p["tarefa"] == "texto_sql" else rodar_texto(modelo, p, tabelas)
                    except TimeoutError:  # o modelo não parou de gerar: conta como erro do modelo
                        r = {"acerto_1a": 0, "acerto": 0, "nota": 0, "tentativas": 1, "segundos": 600.0,
                             "tokens_s": "", "erro": "TIMEOUT: o modelo não terminou a resposta em 600 s", "saida": ""}
                    except (OSError, ErroSQL) as e:  # falha de infraestrutura, não do modelo
                        r = {"acerto_1a": "", "acerto": "", "nota": "", "tentativas": 0, "segundos": "",
                             "tokens_s": "", "erro": f"INFRA: {e}", "saida": ""}
                    escritor.writerow({"data_hora": f"{datetime.now():%Y-%m-%d %H:%M:%S}", "modelo": modelo,
                                       "rodada": rodada, "id": int(p["id"]), "nivel": p["nivel"],
                                       "tarefa": p["tarefa"], "pct_gpu": round(pct_gpu or 0, 1), **r})
                    f.flush()
                    feitas += 1
                    restante = (time.perf_counter() - inicio) / feitas * (total - feitas) / 60
                    print(f"[{feitas}/{total}] {modelo} r{rodada} #{p['id']:>2} {p['tarefa']:<13} "
                          f"acerto={r['acerto']} nota={r['nota']} {r['segundos']}s  (faltam ~{restante:.0f} min)")
            descarregar(modelo)
    print(f"\nConcluído em {(time.perf_counter() - inicio) / 60:.1f} min. Arquivo: {destino}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
