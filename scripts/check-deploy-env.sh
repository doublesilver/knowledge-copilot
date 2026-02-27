#!/usr/bin/env bash

set -euo pipefail

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "ENV file not found: $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

failures=0

require_var() {
  local name="$1"
  local value="${!name-}"
  if [ -z "${value:-}" ] || [[ "$value" == "\${"* ]]; then
    echo "[MISSING] $name"
    failures=$((failures + 1))
  else
    echo "[OK] $name"
  fi
}

warn_var() {
  local name="$1"
  local value="${!name-}"
  if [ -z "${value:-}" ]; then
    echo "[WARN] $name is empty"
  else
    echo "[SET] $name"
  fi
}

echo "== Backend (Railway) readiness =="
require_var KNOWLEDGE_COPILOT_DATABASE_PATH
warn_var OPENAI_API_KEY
require_var OPENAI_EMBEDDING_MODEL
require_var OPENAI_CHAT_MODEL
require_var OPENAI_REQUEST_TIMEOUT
require_var CORS_ORIGINS

echo
echo "== Frontend (Vercel) readiness =="
require_var NEXT_PUBLIC_API_BASE

echo
echo "== Deployment tooling tokens (local) =="
warn_var VERCEL_TOKEN
warn_var GITHUB_TOKEN

if [ "$failures" -ne 0 ]; then
  echo
  echo "Deployment check failed: $failures required variable(s) missing."
  exit 1
fi

echo
echo "Deployment env check passed."
