#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if command -v python >/dev/null 2>&1; then
    PYTHON="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Hittar varken python eller python3 i PATH." >&2
    exit 1
fi

echo "Bygger sökindex..."
"$PYTHON" "$ROOT/app/build_search_index.py" \
    --root "$ROOT" \
    --output "$ROOT/app/search-index.json"

PORT="$("$PYTHON" - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"

URL="http://127.0.0.1:${PORT}/app/index.html"

echo "Startar lokal server på $URL"
echo "Tryck Ctrl+C för att stoppa servern."

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    open "$URL" >/dev/null 2>&1 &
elif command -v explorer.exe >/dev/null 2>&1; then
    explorer.exe "$URL" >/dev/null 2>&1 &
else
    echo "Öppna sidan manuellt: $URL"
fi

exec "$PYTHON" "$ROOT/app/search_server.py" \
    --root "$ROOT" \
    --port "$PORT" \
    --bind 127.0.0.1
