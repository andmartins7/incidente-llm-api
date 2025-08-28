#!/usr/bin/env bash
set -euo pipefail

curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
sleep 2
ollama pull tinyllama || true
