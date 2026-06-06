#!/usr/bin/env bash
# Launch the stack with the Anthropic API key pulled from the macOS Keychain
# instead of a plaintext .env file — so the secret never lives in the repo.
#
# One-time store (you'll be prompted to paste the key; it is NOT echoed):
#   security add-generic-password -U -a "$USER" -s forge-anthropic-api-key -w
#
# Then run the app via this script instead of `docker compose`:
#   ./scripts/run.sh up -d --build
#   ./scripts/run.sh logs -f backend
#
# Update the key later: re-run the `security add-generic-password ... -U` command.
# Remove it:           security delete-generic-password -s forge-anthropic-api-key
set -euo pipefail

SERVICE="forge-anthropic-api-key"

# Only fetch from Keychain if not already provided in the environment.
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  if key="$(security find-generic-password -w -s "$SERVICE" 2>/dev/null)"; then
    export ANTHROPIC_API_KEY="$key"
  else
    echo "note: no '$SERVICE' entry in Keychain — AI auto-fill will be disabled." >&2
    echo "      store it with: security add-generic-password -U -a \"\$USER\" -s $SERVICE -w" >&2
  fi
fi

cd "$(dirname "$0")/.."
exec docker compose "$@"
