#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$ROOT/backend/.venv" ]]; then
  python3 -m venv "$ROOT/backend/.venv"
  "$ROOT/backend/.venv/bin/python" -m pip install --upgrade pip
  "$ROOT/backend/.venv/bin/pip" install -r "$ROOT/backend/requirements.txt"
fi
if [[ ! -f "$ROOT/backend/.env" ]]; then cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"; fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi
echo "Starting backend at http://localhost:8000 and frontend at http://localhost:5173"
(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) & BACK_PID=$!
(cd "$ROOT/frontend" && npm run dev -- --host 127.0.0.1) & FRONT_PID=$!
trap 'kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true' EXIT INT TERM
wait
