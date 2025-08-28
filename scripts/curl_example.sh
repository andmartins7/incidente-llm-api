#!/usr/bin/env bash
set -euo pipefail

URL=${1:-http://localhost:8000/extract}

read -r -d '' PAYLOAD << 'JSON'
{
  "texto": "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que afetou o sistema de faturamento por 2 horas."
}
JSON

curl -s -X POST "$URL" -H "Content-Type: application/json" -d "$PAYLOAD" | jq .
