"""Funções compartilhadas: chamar o modelo no Ollama, extrair e executar o SQL.

Só usa a biblioteca padrão. Usado por perguntar.py (terminal) e app.py (interface web).
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MYSQL_PADRAO = r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"
MAX_CORRECOES = 2
MODELO_PADRAO = "qwen2.5-coder:3b"  # melhor resultado em texto→SQL nos testes


def _ler_env():
    arquivo = RAIZ / ".env"
    if not arquivo.exists():
        sys.exit("Arquivo .env não encontrado. Copie o .env.example para .env e preencha a senha.")
    env = {}
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            env[chave.strip()] = valor.strip()
    return env


ENV = _ler_env()
OLLAMA = ENV.get("OLLAMA_URL", "http://localhost:11434")
SCHEMA = (RAIZ / "prompts" / "schema.txt").read_text(encoding="utf-8").strip()
PROMPT = (RAIZ / "prompts" / "texto_para_sql.txt").read_text(encoding="utf-8")
PROMPT_CORRECAO = (RAIZ / "prompts" / "corrigir_sql.txt").read_text(encoding="utf-8")


# coluna -> tabelas onde ela existe (lido do schema do prompt)
COLUNAS = {}
for _linha in SCHEMA.splitlines():
    _tabela, _resto = _linha.split("(", 1)
    for _col in _resto.rstrip(")").split(", "):
        COLUNAS.setdefault(_col.split()[0], []).append(_tabela)


class ErroSQL(RuntimeError):
    pass


def dica_do_erro(erro, sql, sql_anterior):
    """Transforma o erro do MySQL numa dica concreta para a correção."""
    dicas = []
    achado = re.search(r"Unknown column '(?:(\w+)\.)?(\w+)'", erro)
    if achado:
        errado, coluna = achado.group(1), achado.group(2)
        tabelas = COLUNAS.get(coluna)
        # apelidos usados no SQL: FROM/JOIN tabela [AS] apelido
        apelidos = {t: a for t, a in re.findall(
            r"\b(?:FROM|JOIN)\s+(\w+)(?:\s+AS)?\s+(?!ON\b|JOIN\b|WHERE\b|GROUP\b|ORDER\b|LEFT\b|INNER\b)(\w+)",
            sql or "", flags=re.IGNORECASE)}
        ja_tem = [t for t in (tabelas or []) if t in apelidos]
        if ja_tem:
            certo = apelidos[ja_tem[0]]
            dicas.append(f"A coluna {coluna} é da tabela {ja_tem[0]}, que no seu SQL tem o apelido {certo}. "
                         f"Troque {errado + '.' if errado else ''}{coluna} por {certo}.{coluna}.")
        elif tabelas:
            dicas.append(f"A coluna {coluna} existe só na(s) tabela(s): {', '.join(tabelas)}. "
                         f"Faça o JOIN com essa tabela (veja 'Como ligar as tabelas') e use o apelido dela.")
        else:
            dicas.append(f"A coluna {coluna} não existe em nenhuma tabela. Use outra coluna da lista.")
    if sql and sql == sql_anterior:
        dicas.append("Você repetiu o mesmo SQL. Escreva uma consulta diferente.")
    return " ".join(dicas)


# ------------------------------------------------------------------ Ollama
def _post(caminho, corpo, timeout=600):
    req = urllib.request.Request(f"{OLLAMA}{caminho}", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def gerar(modelo, prompt):
    """Chama o modelo com temperatura 0. Devolve (texto, segundos, tokens_s)."""
    inicio = time.perf_counter()
    dados = _post("/api/generate", {
        "model": modelo, "prompt": prompt, "stream": False,
        "think": False,  # desliga o modo thinking (qwen3.5); ignorado pelos outros
        "options": {"temperature": 0, "num_ctx": 4096},
    })
    segundos = time.perf_counter() - inicio
    tokens_s = dados.get("eval_count", 0) / max(dados.get("eval_duration", 1) / 1e9, 1e-9)
    return dados.get("response", ""), segundos, tokens_s


def modelos_instalados():
    with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=10) as resp:
        return sorted(m["name"] for m in json.load(resp).get("models", []))


def divisao_cpu_gpu(modelo):
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/ps", timeout=10) as resp:
            for m in json.load(resp).get("models", []):
                if modelo in (m.get("name"), m.get("model")):
                    gpu = 100 * m.get("size_vram", 0) / m["size"]
                    return f"{100 - gpu:.0f}% CPU / {gpu:.0f}% GPU"
    except OSError:
        pass
    return "desconhecida"


# ------------------------------------------------------------------ SQL
def extrair_sql(texto):
    texto = re.sub(r"```(?:sql)?", "", texto, flags=re.IGNORECASE)
    achado = re.search(r"\b(WITH|SELECT)\b.*", texto, flags=re.IGNORECASE | re.DOTALL)
    if not achado:
        return None
    return " ".join(achado.group(0).split(";")[0].split())


def executar_sql(sql):
    """Executa só SELECT/WITH. Devolve (colunas, linhas). Levanta ErroSQL."""
    if not re.match(r"^\s*(SELECT|WITH)\b", sql or "", flags=re.IGNORECASE):
        raise ErroSQL("Só consultas SELECT são executadas.")
    env = dict(os.environ, MYSQL_PWD=ENV.get("MYSQL_PASSWORD", ""))
    cmd = [ENV.get("MYSQL_BIN", MYSQL_PADRAO), "-h", ENV.get("MYSQL_HOST", "localhost"),
           "-P", ENV.get("MYSQL_PORT", "3306"), "-u", ENV.get("MYSQL_USER", "root"),
           "--default-character-set=utf8mb4", "-B", ENV.get("MYSQL_DATABASE", "erp_loja"),
           "-e", sql]
    try:
        r = subprocess.run(cmd, capture_output=True, env=env, timeout=60)
    except subprocess.TimeoutExpired:
        raise ErroSQL("A consulta passou de 60 segundos.")
    if r.returncode != 0:
        erro = r.stderr.decode("utf-8", "replace").strip().splitlines()
        erro = [e for e in erro if "Using a password" not in e]
        raise ErroSQL(re.sub(r"^ERROR \d+ \(\w+\) at line \d+: ", "", erro[-1]) if erro else "erro no MySQL")
    linhas = [l.split("\t") for l in r.stdout.decode("utf-8").splitlines()]
    return (linhas[0], linhas[1:]) if linhas else ([], [])


def normalizar(linhas, ordem_importa):
    def valor(v):
        try:
            return str(Decimal(v).quantize(Decimal("0.01")))
        except InvalidOperation:
            return v.strip().lower()
    norm = [tuple(valor(v) for v in l) for l in linhas]
    return norm if ordem_importa else sorted(norm)


def carregar_perguntas():
    with open(RAIZ / "perguntas" / "perguntas.csv", encoding="utf-8", newline="") as f:
        return {p["id"]: p for p in csv.DictReader(f)}


# ------------------------------------------------------------------ fluxo completo
def perguntar(modelo, pergunta, gabarito=None, max_correcoes=MAX_CORRECOES):
    """Gera o SQL, executa e, se der erro, devolve o erro ao modelo para corrigir.

    Devolve um dicionário com as tentativas, o resultado final e, se houver
    gabarito, se acertou na 1ª tentativa e no final.
    """
    prompt = PROMPT.replace("{schema}", SCHEMA).replace("{pergunta}", pergunta)
    tentativas, resultado = [], None
    for n in range(max_correcoes + 1):
        texto, segundos, tokens_s = gerar(modelo, prompt)
        sql = extrair_sql(texto)
        t = {"n": n + 1, "sql": sql, "bruto": texto, "segundos": round(segundos, 1),
             "tokens_s": round(tokens_s, 1), "erro": None}
        tentativas.append(t)
        try:
            if not sql:
                raise ErroSQL("o modelo não devolveu uma consulta SELECT")
            resultado = executar_sql(sql)
            break
        except ErroSQL as e:
            t["erro"] = str(e)
            anterior = tentativas[-2]["sql"] if len(tentativas) > 1 else None
            prompt = prompt + (texto.strip() if sql else "") + PROMPT_CORRECAO.replace(
                "{sql}", sql or texto.strip()[:300]).replace("{erro}", str(e)).replace(
                "{dica}", dica_do_erro(str(e), sql, anterior))

    saida = {"modelo": modelo, "pergunta": pergunta, "tentativas": tentativas,
             "divisao": divisao_cpu_gpu(modelo),
             "segundos_total": round(sum(t["segundos"] for t in tentativas), 1),
             "sql": tentativas[-1]["sql"], "erro": tentativas[-1]["erro"],
             "colunas": resultado[0] if resultado else [],
             "linhas": resultado[1] if resultado else []}

    if gabarito:
        _, esperadas = executar_sql(gabarito["sql_gabarito"])
        ordem = gabarito["ordem_importa"] == "1"
        alvo = normalizar(esperadas, ordem)
        saida["gabarito"] = gabarito["sql_gabarito"]
        saida["acerto_final"] = bool(resultado) and normalizar(resultado[1], ordem) == alvo
        # sem erro na 1ª tentativa, ela já é a final
        saida["acerto_1a"] = len(tentativas) == 1 and saida["acerto_final"]
    return saida
