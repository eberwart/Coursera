# Monitor diario de cartera (R)

Notebook + script para seguir el **óptimo 3 motores** a 12 meses, detectar desviaciones y proponer rebalanceos.

## Cartera objetivo

| Activo | Ticker | Peso |
|--------|--------|-----:|
| S&P 500 | SPY | 40% |
| Semiconductores | SMH | 11% |
| Desarrollados ex-US | VEA | 13% |
| Chile / IPSA | ECH | 17% |
| Oro | GLD | 8% |
| Renta fija | BND | 11% |
| Commodities / cobre | — | 0% |

Alertas si un activo se desvía ≥ **5 pp**, o si la suma de |desviaciones| ≥ **10 pp**.

## Uso rápido

1. Edita `holdings.csv` con tus **shares reales**.
2. Abre `monitor_cartera.Rmd` en RStudio y haz Knit, **o** corre:

```bash
Rscript cartera/monitor/run_diario.R
```

Salidas:
- `alertas/ultima_revision.md` — siempre
- `alertas/alerta_YYYY-MM-DD.md` — solo si hay que rebalancear
- `reportes/ultimo_snapshot.json` — machine-readable
- `reportes/monitor_YYYY-MM-DD.html` — notebook renderizado
- `historial_desviaciones.csv` — serie diaria

## Avisos automáticos

```bash
export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/..."  # o Discord
export ALERT_EMAIL="tu@correo.com"  # requiere `mail` en el sistema
Rscript cartera/monitor/run_diario.R
```

También puedes poner `webhook_url` / `email` en `config.yml`.

## Cron (lun–vie 18:30 Chile)

```bash
chmod +x cartera/monitor/cron_diario.sh
crontab -e
# agregar:
30 18 * * 1-5 /ruta/absoluta/al/repo/cartera/monitor/cron_diario.sh
```

El script sale con código `2` si hay que rebalancear (útil para alertas de CI/monitoring).

## Dependencias R

```r
install.packages(c(
  "quantmod", "yaml", "jsonlite", "dplyr", "tidyr",
  "ggplot2", "scales", "httr", "rmarkdown", "knitr"
))
```

## Flujo recomendado

1. Cron corre cada tarde hábil.
2. Si hay ALERTA → llega webhook/email + archivo en `alertas/`.
3. Ejecutas las órdenes propuestas en el broker.
4. Actualizas `holdings.csv` con los nuevos shares.
5. Vuelves a correr `run_diario.R` para confirmar que quedó en banda.
