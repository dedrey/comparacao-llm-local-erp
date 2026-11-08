"""Análise estatística dos resultados do benchmark.

Lê todos os resultados/brutos/benchmark_*.csv e gera:
    resultados/tabelas/*.csv  e  resultados/tabelas/resumo.md
    resultados/graficos/*.png

Unidade de análise: a pergunta. As 3 rodadas de cada (modelo, pergunta) viram um valor só:
acerto = maioria das rodadas, nota = média, tempo = mediana. Assim os modelos ficam
pareados pela pergunta, como pedem os testes (Cochran/McNemar e Friedman/Wilcoxon).

Uso (precisa da .venv com scipy e matplotlib):
    .venv\\Scripts\\python scripts/analise.py
"""

import csv
import itertools
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "resultados" / "brutos"
TABELAS = RAIZ / "resultados" / "tabelas"
GRAFICOS = RAIZ / "resultados" / "graficos"
ALFA = 0.05
SEMENTE = 2026

# nome curto para tabelas e gráficos
NOMES = {
    "qwen2.5-coder:3b": "qwen2.5-coder 3b",
    "llama3.2:3b": "llama3.2 3b",
    "phi4-mini:3.8b-q4_K_M": "phi4-mini 3.8b",
    "qwen3.5:4b-q4_K_M": "qwen3.5 4b",
    "gemma4:e2b-it-q4_K_M": "gemma4 e2b",
    "qwen3.5:2b-q4_K_M": "qwen3.5 2b",
}
# o Ollama informa errado o gemma4 (271MB, 100% GPU); valor do nvidia-smi: ~1,8GB de 4,6GB na GPU
GPU_MEDIDA = {"gemma4:e2b-it-q4_K_M": 39.0}
# cores fixas por modelo (paleta categórica de referência, slots 1 a 6)
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
NIVEIS = ["facil", "media", "dificil"]
TAREFAS_TEXTO = ["interpretacao", "resumo", "anomalia"]


# ------------------------------------------------------------------ dados
def carregar():
    linhas, vistos = [], set()
    for arq in sorted(BRUTOS.glob("benchmark_*.csv")):
        with arq.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                chave = (r["modelo"], r["rodada"], r["id"])
                if chave in vistos:
                    sys.exit(f"Execução repetida em {arq.name}: {chave}")
                if r["erro"].startswith("INFRA"):
                    continue  # falha de infraestrutura não entra na análise
                vistos.add(chave)
                linhas.append(r)
    return linhas


def por_pergunta(linhas):
    """(modelo, id) -> acerto da maioria, nota média, tempo mediano, rodadas diferentes."""
    grupos = defaultdict(list)
    for r in linhas:
        grupos[(r["modelo"], int(r["id"]))].append(r)
    agreg = {}
    for (modelo, i), rs in grupos.items():
        acertos = [int(float(r["acerto"])) for r in rs]
        agreg[(modelo, i)] = {
            "nivel": rs[0]["nivel"], "tarefa": rs[0]["tarefa"],
            "acerto": int(sum(acertos) * 2 > len(acertos)),
            "acerto_1a": int(sum(int(float(r["acerto_1a"])) for r in rs) * 2 > len(rs)),
            "nota": st.mean(float(r["nota"]) for r in rs),
            "tempo": st.median(float(r["segundos"]) for r in rs),
            "variou": len(set(acertos)) > 1,
        }
    return agreg


# ------------------------------------------------------------------ estatística
def wilson(acertos, n, z=1.96):
    """Intervalo de confiança de 95% de Wilson para uma proporção."""
    if n == 0:
        return (0.0, 0.0)
    p = acertos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margem = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centro - margem, centro + margem)


def ic_bootstrap(valores, funcao=np.median, n=10000):
    """IC de 95% por bootstrap percentil (semente fixa, reproduzível)."""
    rng = np.random.default_rng(SEMENTE)
    v = np.asarray(valores, dtype=float)
    amostras = funcao(rng.choice(v, size=(n, len(v)), replace=True), axis=1)
    return tuple(np.percentile(amostras, [2.5, 97.5]))


def cochran_q(matriz):
    """Q de Cochran. matriz: linhas = perguntas, colunas = modelos, valores 0/1."""
    x = np.asarray(matriz)
    k = x.shape[1]
    col, lin, total = x.sum(axis=0), x.sum(axis=1), x.sum()
    denominador = k * total - (lin ** 2).sum()
    if denominador == 0:
        return 0.0, 1.0
    q = (k - 1) * (k * (col ** 2).sum() - total ** 2) / denominador
    return q, stats.chi2.sf(q, k - 1)


def mcnemar(a, b):
    """McNemar exato (binomial nos pares discordantes)."""
    so_a = sum(1 for x, y in zip(a, b) if x and not y)
    so_b = sum(1 for x, y in zip(a, b) if y and not x)
    if so_a + so_b == 0:
        return so_a, so_b, 1.0
    return so_a, so_b, stats.binomtest(so_a, so_a + so_b, 0.5).pvalue


def wilcoxon(a, b):
    try:
        return stats.wilcoxon(a, b).pvalue
    except ValueError:  # todas as diferenças são zero
        return 1.0


def bonferroni(p, comparacoes):
    return min(1.0, p * comparacoes)


# ------------------------------------------------------------------ saída
def fmt(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def pct(v):
    return f"{100 * v:.1f}%".replace(".", ",")


def p_fmt(p):
    return "< 0,001" if p < 0.001 else fmt(p, 3)


def gravar(nome, cabecalho, linhas, md):
    with (TABELAS / f"{nome}.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas)
    md.append("| " + " | ".join(cabecalho) + " |")
    md.append("|" + " --- |" * len(cabecalho))
    md.extend("| " + " | ".join(str(c) for c in l) + " |" for l in linhas)
    md.append("")


def estilo(ax, titulo, ylabel):
    ax.set_title(titulo, loc="left", fontsize=12, color="#0b0b0b")
    ax.set_ylabel(ylabel, color="#52514e")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#c3c2b7")
    ax.tick_params(colors="#52514e")
    ax.grid(axis="y", color="#e1e0d9", linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    TABELAS.mkdir(parents=True, exist_ok=True)
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    linhas = carregar()
    agreg = por_pergunta(linhas)
    gpu = {}
    for r in linhas:
        gpu[r["modelo"]] = GPU_MEDIDA.get(r["modelo"], float(r["pct_gpu"] or 0))
    ids_sql = sorted({i for (_, i), v in agreg.items() if v["tarefa"] == "texto_sql"})
    ids_texto = sorted({i for (_, i), v in agreg.items() if v["tarefa"] != "texto_sql"})
    ids_todos = ids_sql + ids_texto

    def serie(modelo, campo, ids):
        return [agreg[(modelo, i)][campo] for i in ids]

    # ordem dos modelos: acerto final no SQL (maior primeiro); a cor acompanha o modelo
    modelos = sorted({m for m, _ in agreg},
                     key=lambda m: (-sum(serie(m, "acerto", ids_sql)), st.median(serie(m, "tempo", ids_todos))))
    cor = {m: CORES[i] for i, m in enumerate(sorted(modelos, key=list(NOMES).index))}
    nome = lambda m: NOMES.get(m, m)
    pares = list(itertools.combinations(modelos, 2))
    md = ["# Resultados da análise", "",
          f"Gerado por `scripts/analise.py` a partir de {len(linhas)} execuções "
          f"({len(modelos)} modelos, {len(ids_todos)} perguntas, 3 rodadas). "
          "Unidade de análise: a pergunta (acerto = maioria das rodadas, nota = média, tempo = mediana). "
          "IC = intervalo de confiança de 95% (Wilson para proporções, bootstrap para medianas e médias).", ""]

    # 1. descritiva geral
    md.append("## 1. Visão geral por modelo\n")
    tab = []
    for m in modelos:
        a1, af, n = sum(serie(m, "acerto_1a", ids_sql)), sum(serie(m, "acerto", ids_sql)), len(ids_sql)
        lo, hi = wilson(af, n)
        notas = serie(m, "nota", ids_texto)
        nlo, nhi = ic_bootstrap(notas, np.mean)
        tempos = serie(m, "tempo", ids_todos)
        tlo, thi = ic_bootstrap(tempos)
        tok = st.mean(float(r["tokens_s"]) for r in linhas if r["modelo"] == m and r["tokens_s"])
        tab.append([nome(m), f"{a1}/{n}", f"{af}/{n} ({pct(af / n)})", f"{pct(lo)} a {pct(hi)}",
                    fmt(st.mean(notas)), f"{fmt(nlo)} a {fmt(nhi)}",
                    fmt(st.median(tempos), 1), f"{fmt(tlo, 1)} a {fmt(thi, 1)}", fmt(tok, 1), f"{gpu[m]:.0f}%"])
    gravar("01_visao_geral", ["Modelo", "SQL 1ª tentativa", "SQL final", "IC SQL final", "Nota texto (média)",
                              "IC nota", "Tempo mediano (s)", "IC tempo", "Tokens/s", "GPU"], tab, md)

    # 2. SQL por nível
    md.append("## 2. Acerto no SQL por nível (após autocorreção)\n")
    tab = []
    for m in modelos:
        l = [nome(m)]
        for nv in NIVEIS:
            ids = [i for i in ids_sql if agreg[(m, i)]["nivel"] == nv]
            l.append(f"{sum(serie(m, 'acerto', ids))}/{len(ids)}")
        tab.append(l)
    gravar("02_sql_por_nivel", ["Modelo", "Fácil", "Média", "Difícil"], tab, md)

    # 3. nota por tarefa de texto
    md.append("## 3. Nota média nas tarefas sem SQL\n")
    tab = []
    for m in modelos:
        l = [nome(m)]
        for t in TAREFAS_TEXTO:
            ids = [i for i in ids_texto if agreg[(m, i)]["tarefa"] == t]
            l.append(fmt(st.mean(serie(m, "nota", ids))))
        tab.append(l)
    gravar("03_nota_por_tarefa", ["Modelo", "Interpretação", "Resumo", "Anomalia"], tab, md)

    # 4. testes de acerto no SQL
    md.append("## 4. Acerto no SQL: Q de Cochran e McNemar par a par\n")
    q, p = cochran_q(np.array([serie(m, "acerto", ids_sql) for m in modelos]).T)
    md.append(f"Q de Cochran = {fmt(q)}, gl = {len(modelos) - 1}, p {p_fmt(p) if p < 0.001 else '= ' + p_fmt(p)} "
              f"({'há' if p < ALFA else 'não há'} diferença significativa entre os modelos a 5%).\n")
    tab = []
    for a, b in pares:
        so_a, so_b, pp = mcnemar(serie(a, "acerto", ids_sql), serie(b, "acerto", ids_sql))
        pc = bonferroni(pp, len(pares))
        tab.append([nome(a), nome(b), so_a, so_b, p_fmt(pp), p_fmt(pc), "sim" if pc < ALFA else "não"])
    md.append(f"Só A / só B = perguntas que só um dos dois acertou. Bonferroni: p × {len(pares)}.\n")
    gravar("04_mcnemar_sql", ["Modelo A", "Modelo B", "Só A acertou", "Só B acertou", "p", "p (Bonferroni)",
                              "Significativo"], tab, md)

    # 5 e 6. Friedman + Wilcoxon (tempo nas 45 perguntas; nota nas 15 sem SQL)
    for num, campo, ids, titulo, unidade in [(5, "tempo", ids_todos, "Tempo por pergunta", "s"),
                                             (6, "nota", ids_texto, "Nota nas tarefas sem SQL", "")]:
        md.append(f"## {num}. {titulo}: Friedman e Wilcoxon par a par\n")
        series = {m: serie(m, campo, ids) for m in modelos}
        chi, p = stats.friedmanchisquare(*series.values())
        md.append(f"Friedman: χ² = {fmt(chi)}, gl = {len(modelos) - 1}, p {p_fmt(p) if p < 0.001 else '= ' + p_fmt(p)} "
                  f"({'há' if p < ALFA else 'não há'} diferença significativa a 5%; n = {len(ids)} perguntas).\n")
        tab = []
        for a, b in pares:
            dif = st.median(x - y for x, y in zip(series[a], series[b]))
            pp = wilcoxon(series[a], series[b])
            pc = bonferroni(pp, len(pares))
            tab.append([nome(a), nome(b), fmt(dif, 1 if unidade else 2), p_fmt(pp), p_fmt(pc),
                        "sim" if pc < ALFA else "não"])
        gravar(f"0{num}_wilcoxon_{campo}", ["Modelo A", "Modelo B", f"Mediana de A − B{' (s)' if unidade else ''}",
                                             "p", "p (Bonferroni)", "Significativo"], tab, md)

    # 7. estabilidade entre rodadas
    md.append("## 7. Estabilidade entre rodadas (temperatura 0)\n")
    tab = []
    for m in modelos:
        variaram = [i for i in ids_todos if agreg[(m, i)]["variou"]]
        tab.append([nome(m), len(variaram), ", ".join(map(str, variaram)) or "—"])
    gravar("07_estabilidade", ["Modelo", "Perguntas com resultado diferente entre rodadas", "Ids"], tab, md)

    (TABELAS / "resumo.md").write_text("\n".join(md), encoding="utf-8")

    # ------------------------------------------------------------------ gráficos
    plt.rcParams.update({"font.size": 10, "figure.dpi": 150, "savefig.bbox": "tight",
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    rotulos = [nome(m) for m in modelos]

    # tempo: boxplot das execuções (escala log, por causa dos timeouts de 600 s)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    dados = [[float(r["segundos"]) for r in linhas if r["modelo"] == m] for m in modelos]
    caixas = ax.boxplot(dados, tick_labels=rotulos, patch_artist=True, widths=0.5,
                        medianprops={"color": "#0b0b0b", "linewidth": 1.5},
                        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": "#898781",
                                    "markeredgecolor": "none", "alpha": 0.6})
    for caixa, m in zip(caixas["boxes"], modelos):
        caixa.set(facecolor=cor[m], alpha=0.85, edgecolor="#fcfcfb")
    ax.set_yscale("log")
    ax.set_yticks([2, 5, 10, 30, 60, 120, 300, 600], ["2", "5", "10", "30", "60", "120", "300", "600"])
    estilo(ax, "Tempo de resposta por execução (todas as tarefas, escala log)", "segundos")
    fig.savefig(GRAFICOS / "tempo_boxplot.png")
    plt.close(fig)

    # acerto SQL por nível: barras agrupadas
    fig, ax = plt.subplots(figsize=(9, 4.5))
    largura = 0.8 / len(modelos)
    x = np.arange(len(NIVEIS))
    for k, m in enumerate(modelos):
        vals = []
        for nv in NIVEIS:
            ids = [i for i in ids_sql if agreg[(m, i)]["nivel"] == nv]
            vals.append(100 * sum(serie(m, "acerto", ids)) / len(ids))
        ax.bar(x - 0.4 + largura * (k + 0.5), vals, largura * 0.9, color=cor[m], label=nome(m))
    ax.set_xticks(x, ["Fácil", "Média", "Difícil"])
    ax.set_ylim(0, 105)
    estilo(ax, "Acerto no texto→SQL por nível (após autocorreção, 10 perguntas por nível)", "% de acerto")
    ax.legend(frameon=False, ncol=3, loc="upper right", fontsize=9)
    fig.savefig(GRAFICOS / "sql_por_nivel.png")
    plt.close(fig)

    # nota por tarefa de texto
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(TAREFAS_TEXTO))
    for k, m in enumerate(modelos):
        vals = [st.mean(agreg[(m, i)]["nota"] for i in ids_texto if agreg[(m, i)]["tarefa"] == t)
                for t in TAREFAS_TEXTO]
        ax.bar(x - 0.4 + largura * (k + 0.5), vals, largura * 0.9, color=cor[m], label=nome(m))
    ax.set_xticks(x, ["Interpretação (6)", "Resumo (4)", "Anomalia (5)"])
    ax.set_ylim(0, 1.05)
    estilo(ax, "Nota média nas tarefas sem SQL (0 a 1)", "nota")
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=9)
    fig.savefig(GRAFICOS / "nota_por_tarefa.png")
    plt.close(fig)

    # tempo × acerto, com % na GPU no rótulo
    fig, ax = plt.subplots(figsize=(8, 5))
    pontos = {m: (st.median(serie(m, "tempo", ids_sql)), 100 * sum(serie(m, "acerto", ids_sql)) / len(ids_sql))
              for m in modelos}
    for m, (t, a) in pontos.items():
        ax.scatter(t, a, s=90, color=cor[m], edgecolor="#fcfcfb", linewidth=2, zorder=3)
        # rótulo à esquerda quando há outro ponto logo à direita (evita sobreposição)
        vizinho = any(0 < t2 - t < 4 and abs(a2 - a) < 8 for t2, a2 in pontos.values())
        ax.annotate(f"{nome(m)}\n{gpu[m]:.0f}% na GPU", (t, a), xytext=(-10 if vizinho else 8, -4),
                    textcoords="offset points", ha="right" if vizinho else "left", va="center",
                    fontsize=9, color="#52514e")
    ax.set_xlabel("tempo mediano por pergunta de SQL (s)", color="#52514e")
    ax.set_ylim(0, 100)
    ax.set_xlim(0, max(st.median(serie(m, "tempo", ids_sql)) for m in modelos) * 1.4)
    ax.grid(axis="x", color="#e1e0d9", linewidth=0.8)
    estilo(ax, "Acerto no texto→SQL × tempo (melhor: canto superior esquerdo)", "% de acerto")
    fig.savefig(GRAFICOS / "acerto_x_tempo.png")
    plt.close(fig)

    print("\n".join(md))
    print(f"Tabelas em {TABELAS}\nGráficos em {GRAFICOS}")


if __name__ == "__main__":
    main()
