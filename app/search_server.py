#!/usr/bin/env python3
"""Local server for the document search app.

It serves the static app and exposes a small rebuild endpoint used by
index.html. Keep this local-only; it is intended for 127.0.0.1.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_DIR = "app"
INDEX_FILE = "search-index.json"


class SearchRequestHandler(SimpleHTTPRequestHandler):
    root: Path
    builder: Path
    rebuild_lock: threading.Lock

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/rebuild":
            self.send_json(404, {"ok": False, "error": "Okänd endpoint."})
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length:
            self.rfile.read(content_length)

        if not self.rebuild_lock.acquire(blocking=False):
            self.send_json(
                409,
                {"ok": False, "error": "Indexering körs redan."},
            )
            return

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.builder),
                    "--root",
                    str(self.root),
                    "--output",
                    str(self.root / APP_DIR / INDEX_FILE),
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode != 0:
                self.send_json(
                    500,
                    {
                        "ok": False,
                        "error": "Indexbyggaren misslyckades.",
                        "output": result.stdout,
                        "stderr": result.stderr,
                    },
                )
                return

            index = read_index_summary(self.root / APP_DIR / INDEX_FILE)
            self.send_json(
                200,
                {
                    "ok": True,
                    "documents": index.get("documents", 0),
                    "warnings": index.get("warnings", []),
                    "output": result.stdout,
                },
            )
        finally:
            self.rebuild_lock.release()


def read_index_summary(path: Path) -> dict[str, Any]:
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"documents": 0, "warnings": []}
    return {
        "documents": len(index.get("documents", [])),
        "warnings": index.get("warnings", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the local document search app.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    root = args.root.resolve()
    builder = root / APP_DIR / "build_search_index.py"
    if not builder.exists():
        print(f"Hittar inte {builder}", file=sys.stderr)
        return 1

    SearchRequestHandler.root = root
    SearchRequestHandler.builder = builder
    SearchRequestHandler.rebuild_lock = threading.Lock()
    handler_class = partial(SearchRequestHandler, directory=str(root))

    server = ThreadingHTTPServer((args.bind, args.port), handler_class)
    url = f"http://{args.bind}:{args.port}/{APP_DIR}/index.html"
    print(f"Server körs på {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStoppar servern.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
