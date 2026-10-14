#!/usr/bin/env bash
# Start backend (uvicorn) and frontend (Next.js) together for local development.
# Reads the project root .env for ports and API URL; Ctrl-C stops both processes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$ROOT/backend"
if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Missing backend/.venv — run: cd backend && python3.12 -m venv .venv && pip install -r requirements.txt" >&2
  exit 1
fi

.venv/bin/python manage.py migrate --noinput

.venv/bin/uvicorn fritts.asgi:app --reload --host "${BACKEND_HOST:-127.0.0.1}" --port "$BACKEND_PORT" &
BACKEND_PID=$!

cd "$ROOT/frontend"
npm run dev -- --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo "Backend: http://${BACKEND_HOST:-127.0.0.1}:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl-C to stop both."

wait "$BACKEND_PID" "$FRONTEND_PID"
