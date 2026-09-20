"""LED Matrix control app — live preview plus animation picker."""

from __future__ import annotations

import json
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from matrix_deck import __version__
from matrix_deck.anim import catalog_meta
from matrix_deck.engine import Deck

WEB_ROOT = Path(__file__).resolve().parent / "web"


class DeckHandler(SimpleHTTPRequestHandler):
    deck: Deck
    httpd = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def end_headers(self) -> None:
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        if self.path.startswith("/api/"):
            return
        super().log_message(format, *args)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/api/frame":
            self._json(200, self.deck.snapshot())
            return
        if path == "/api/animations":
            self._json(200, {"animations": catalog_meta()})
            return
        if path == "/api/health":
            self._json(200, {"ok": True, "version": __version__, "animations": len(catalog_meta())})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        payload: dict = {}
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid json"})
                return
        if path == "/api/animation":
            side = str(payload.get("side", "left"))
            anim_id = str(payload.get("id", "flappy"))
            if side not in ("left", "right"):
                self._json(400, {"ok": False, "error": "side must be left or right"})
                return
            self.deck.set_animation(side, anim_id)
            self._json(200, {"ok": True, "side": side, "id": anim_id})
            return
        if path == "/api/click":
            side = str(payload.get("side", "left"))
            if side not in ("left", "right"):
                self._json(400, {"ok": False, "error": "side must be left or right"})
                return
            try:
                x = int(payload.get("x", 0))
                y = int(payload.get("y", 0))
            except (TypeError, ValueError):
                self._json(400, {"ok": False, "error": "invalid coordinates"})
                return
            erase = bool(payload.get("erase", False))
            self.deck.click(side, x, y, erase)
            self._json(200, {"ok": True})
            return
        if path == "/api/stroke":
            side = str(payload.get("side", "left"))
            if side not in ("left", "right"):
                self._json(400, {"ok": False, "error": "side must be left or right"})
                return
            points = payload.get("points") or []
            if not isinstance(points, list) or len(points) > 128:
                self._json(400, {"ok": False, "error": "points must be a list of at most 128 pairs"})
                return
            erase = bool(payload.get("erase", False))
            self.deck.stroke(side, points, erase)
            self._json(200, {"ok": True})
            return
        if path == "/api/key":
            side = str(payload.get("side", "left"))
            if side not in ("left", "right"):
                self._json(400, {"ok": False, "error": "side must be left or right"})
                return
            code = str(payload.get("code", ""))
            self.deck.key(side, code)
            self._json(200, {"ok": True})
            return
        if path == "/api/flap":
            self.deck.flap()
            self._json(200, {"ok": True})
            return
        if path == "/api/brightness":
            try:
                self.deck.set_brightness(int(payload.get("value", self.deck.brightness)))
            except (TypeError, ValueError):
                self._json(400, {"ok": False, "error": "invalid brightness"})
                return
            self._json(200, {"ok": True, "brightness": self.deck.brightness})
            return
        if path == "/api/speed":
            try:
                self.deck.set_speed(float(payload.get("value", self.deck.speed)))
            except (TypeError, ValueError):
                self._json(400, {"ok": False, "error": "invalid speed"})
                return
            self._json(200, {"ok": True, "speed": self.deck.speed})
            return
        if path == "/api/random":
            enabled = bool(payload.get("enabled", True))
            self.deck.set_random(enabled)
            self._json(200, {"ok": True, "random": self.deck.random_mode})
            return
        if path == "/api/text":
            side = str(payload.get("side", "left"))
            if side not in ("left", "right"):
                self._json(400, {"ok": False, "error": "side must be left or right"})
                return
            self.deck.set_text(side, str(payload.get("text", "")))
            self._json(200, {"ok": True, "side": side, "text": self.deck.text[side]})
            return
        if path == "/api/quit":
            threading.Thread(target=self._quit, daemon=True).start()
            self._json(200, {"ok": True})
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

    def _quit(self) -> None:
        time.sleep(0.05)
        try:
            self.deck.stop()
        except Exception:
            pass
        if self.httpd is not None:
            self.httpd.shutdown()


def make_server(deck: Deck, host: str, port: int) -> ThreadingHTTPServer:
    DeckHandler.deck = deck
    handler = partial(DeckHandler)
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    DeckHandler.httpd = httpd
    return httpd
