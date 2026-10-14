#!/usr/bin/env python3
"""Tiny local server with a same-origin proxy for Sony's PS Plus catalog."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
import json
import time

HOST = "127.0.0.1"
PORT = 4173
ROOT = Path(__file__).resolve().parent
CATALOG_URL = "https://www.playstation.com/bin/imagic/gameslist?locale=en-us&categoryList=plus-games-list"
CACHE_TTL = 60 * 60
cache = {"at": 0.0, "body": None}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/games":
            return self.send_catalog()
        return super().do_GET()

    def send_catalog(self):
        try:
            if cache["body"] is None or time.time() - cache["at"] > CACHE_TTL:
                request = Request(CATALOG_URL, headers={"User-Agent": "Extra-Games/1.0"})
                with urlopen(request, timeout=20) as response:
                    body = response.read()
                json.loads(body)
                cache.update(at=time.time(), body=body)
            body = cache["body"]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(body)
        except Exception as error:
            body = json.dumps({"error": str(error)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    print(f"Extra Games is running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
