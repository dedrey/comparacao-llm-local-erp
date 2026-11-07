"""Faz perguntas em linguagem natural a um modelo local pelo terminal.

Uso:
    python scripts/perguntar.py                      # modo interativo com o modelo padrão
    python scripts/perguntar.py --modelo phi4-mini   # outro modelo
    python scripts/perguntar.py --pergunta "Quantos clientes existem?"

No modo interativo, digite uma pergunta, o número de uma pergunta de
perguntas/perguntas.csv (1 a 30) para comparar com o gabarito, ou "sair".
"""

import argparse
import sys

from nucleo import MODELO_PADRAO, ErroSQL, carregar_perguntas, perguntar

MAX_LINHAS = 20


def mostrar_tabela(colunas, linhas):
    if not colunas:
        print("  (sem resultado)")
        return
    largura = [min(30, max(len(str(x)) for x in [c] + [l[i] for l in linhas[:MAX_LINHAS]]))
               for i, c in enumerate(colunas)]
    print("  " + " | ".join(c[:30].ljust(w) for c, w in zip(colunas, largura)))
    print("  " + "-+-".join("-" * w for w in largura))
    for l in linhas[:MAX_LINHAS]:
        print("  " + " | ".join(v[:30].ljust(w) for v, w in zip(l, largura)))
    if len(linhas) > MAX_LINHAS:
        print(f"  ... ({len(linhas)} linhas no total)")


def responder(modelo, pergunta, gabarito=None):
    print("\nPensando...")
    try:
        r = perguntar(modelo, pergunta, gabarito)
    except (OSError, ErroSQL) as e:
        print(f"Erro: {e}")
        return
    for t in r["tentativas"]:
        print(f"\nTentativa {t['n']} ({t['segundos']}s, {t['tokens_s']} tokens/s):\n  {t['sql']}")
        if t["erro"]:
            print(f"  -> erro: {t['erro']}")
    print(f"\nTempo total: {r['segundos_total']}s | divisão: {r['divisao']}")
    if r["erro"]:
        print("Não consegui gerar um SQL válido para essa pergunta.")
    else:
        print("\nResultado:")
        mostrar_tabela(r["colunas"], r["linhas"])
    if gabarito:
        print(f"\nComparação com o gabarito: {'ACERTOU' if r['acerto_final'] else 'ERROU'}")
        if not r["acerto_final"]:
            print(f"Gabarito:\n  {r['gabarito']}")


def main():
    parser = argparse.ArgumentParser(description="Pergunte ao ERP em linguagem natural.")
    parser.add_argument("--modelo", default=MODELO_PADRAO)
    parser.add_argument("--pergunta", help="faz uma pergunta e sai")
    args = parser.parse_args()
    perguntas = carregar_perguntas()

    if args.pergunta:
        p = perguntas.get(args.pergunta.strip())
        responder(args.modelo, p["pergunta"] if p else args.pergunta, p)
        return

    print(f"Modelo: {args.modelo}. Digite uma pergunta, o número de uma pergunta do CSV (1-30) ou 'sair'.")
    while True:
        try:
            entrada = input("\nPergunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if entrada.lower() in ("sair", "exit", "q"):
            break
        if not entrada:
            continue
        p = perguntas.get(entrada)
        if p and p["tarefa"] != "texto_sql":
            print("Esse número é de uma tarefa sem SQL. Use 1 a 30.")
            continue
        if p:
            print(f"[{p['nivel']}] {p['pergunta']}")
        responder(args.modelo, p["pergunta"] if p else entrada, p)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
