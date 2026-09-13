#!/usr/bin/env bash
# Instalación cron (días hábiles 18:30 hora America/Santiago)
#   crontab -e
#   30 18 * * 1-5 /ruta/al/repo/cartera/monitor/cron_diario.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/reportes"
mkdir -p "$LOG_DIR"
export TZ="${TZ:-America/Santiago}"
# Opcional: descomenta o exporta en tu shell/profile
# export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/XXX"
# export ALERT_EMAIL="tu@correo.com"
{
  echo "==== $(date -Is) ===="
  Rscript "$ROOT/run_diario.R"
  echo "exit=$?"
} >>"$LOG_DIR/cron.log" 2>&1
