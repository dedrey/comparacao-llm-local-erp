"""Interface web para fazer perguntas ao ERP com modelos locais.

Só usa a biblioteca padrão. Precisa do Ollama e do MySQL rodando.
Uso: python scripts/app.py   e abra http://localhost:8000
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from nucleo import MODELO_PADRAO, ErroSQL, carregar_perguntas, modelos_instalados, perguntar

PORTA = 8000
PAGINA = Path(__file__).with_name("web") / "index.html"
PERGUNTAS = carregar_perguntas()


class Handler(BaseHTTPRequestHandler):
    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path == "/":
            corpo = PAGINA.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        elif self.path == "/api/modelos":
            try:
                self._json({"modelos": modelos_instalados(), "padrao": MODELO_PADRAO})
            except OSError as e:
                self._json({"erro": f"Ollama indisponível: {e}"}, 503)
        elif self.path == "/api/perguntas":
            self._json({"perguntas": [
                {"id": p["id"], "nivel": p["nivel"], "pergunta": p["pergunta"]}
                for p in PERGUNTAS.values() if p["tarefa"] == "texto_sql"]})
        else:
            self._json({"erro": "não encontrado"}, 404)

    def do_POST(self):
        if self.path != "/api/perguntar":
            return self._json({"erro": "não encontrado"}, 404)
        try:
            dados = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            gabarito = PERGUNTAS.get(str(dados.get("id") or ""))
            pergunta = gabarito["pergunta"] if gabarito else (dados.get("pergunta") or "").strip()
            if not pergunta:
                return self._json({"erro": "Digite uma pergunta."}, 400)
            self._json(perguntar(dados.get("modelo") or MODELO_PADRAO, pergunta, gabarito))
        except (OSError, ErroSQL, ValueError) as e:
            self._json({"erro": str(e)}, 500)

    def log_message(self, formato, *args):
        sys.stderr.write("[app] " + (formato % args) + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Interface no ar: http://localhost:{PORTA}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()
