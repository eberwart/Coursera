# Optimización P(W≥2,2M) con piso de cola

## Supuestos

- Medias forward: {'SPY': 0.0805, 'SMH': 0.0955, 'VEA': 0.0705, 'IPSA': 0.0905, 'ORO': 0.0405, 'COMM': 0.0455, 'RF': 0.0385}
- Vol cartera 3 ancla: 13.3%
- Piso r5: -14.99% → $1.70M

## Resultados

| Cartera | E[r] | Vol | P(>2M) | P(≥2,2M) | P5 wealth |
|---|---:|---:|---:|---:|---:|
| base_instagram_tech | 7.7% | 15.0% | 72.5% | 43.1% | $1.73M |
| cartera_3 | 6.9% | 13.3% | 72.8% | 39.5% | $1.76M |
| opt_max_P_meta_con_piso_p5 | 7.7% | 13.8% | 74.2% | 42.4% | $1.76M |
| opt_espiritu_3_motores | 7.4% | 13.6% | 73.8% | 41.1% | $1.76M |
| opt_piso_p5_mas_40k | 7.2% | 12.2% | 75.3% | 39.5% | $1.80M |
| opt_sin_piso_p5 | 9.6% | 28.5% | 65.1% | 49.2% | $1.38M |

## Pesos

### base_instagram_tech
- SPY: 40.0%
- SMH: 25.0%
- VEA: 5.0%
- IPSA: 10.0%
- ORO: 8.0%
- COMM: 5.0%
- RF: 7.0%

### cartera_3
- SPY: 22.5%
- SMH: 10.0%
- VEA: 5.0%
- IPSA: 25.0%
- ORO: 17.5%
- COMM: 5.0%
- RF: 15.0%

### opt_max_P_meta_con_piso_p5
- SPY: 69.0%
- SMH: 3.0%
- VEA: 0.0%
- IPSA: 14.6%
- ORO: 0.0%
- COMM: 0.0%
- RF: 13.4%

### opt_espiritu_3_motores
- SPY: 40.0%
- SMH: 10.7%
- VEA: 12.6%
- IPSA: 16.7%
- ORO: 8.0%
- COMM: 0.0%
- RF: 11.9%

### opt_piso_p5_mas_40k
- SPY: 60.7%
- SMH: 2.1%
- VEA: 0.0%
- IPSA: 12.5%
- ORO: 0.0%
- COMM: 0.0%
- RF: 24.7%

### opt_sin_piso_p5
- SPY: 0.0%
- SMH: 100.0%
- VEA: 0.0%
- IPSA: 0.0%
- ORO: 0.0%
- COMM: 0.0%
- RF: 0.0%
