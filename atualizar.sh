#!/usr/bin/env bash
# Coleta Meta + HubSpot e gera site/data.json
set -euo pipefail
cd "$(dirname "$0")"
export TZ=America/Sao_Paulo
python3 -u coleta.py
python3 -u build.py
