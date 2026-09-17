"""Local preview server that mirrors both LED matrices in the browser."""

from __future__ import annotations

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from matrix_deck.engine import Deck

WEB_ROOT = Path(__file__).resolve().parent / "web"


class DeckHandler(SimpleHTTPRequestHandler):
    deck: Deck

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        if self.path.startswith("/api/"):
            return
        super().log_message(format, *args)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/api/frame":
            self._json(200, self.deck.snapshot())
            return
        if self.path.split("?", 1)[0] == "/api/health":
            self._json(200, {"ok": True})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        if path == "/api/flap":
            self.deck.flap()
            self._json(200, {"ok": True, **_score(self.deck)})
            return
        if path == "/api/brightness":
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
                self.deck.set_brightness(int(payload.get("value", self.deck.brightness)))
            except (ValueError, json.JSONDecodeError):
                self._json(400, {"ok": False, "error": "invalid brightness"})
                return
            self._json(200, {"ok": True, "brightness": self.deck.brightness})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _score(deck: Deck) -> dict:
    snap = deck.snapshot()
    return {"score": snap["score"], "best": snap["best"], "alive": snap["alive"]}


def make_server(deck: Deck, host: str, port: int) -> ThreadingHTTPServer:
    DeckHandler.deck = deck
    handler = partial(DeckHandler)
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    return httpd
