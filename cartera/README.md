# Optimización de cartera — probabilidad de meta a 12 meses

## Pregunta

Maximizar `P(W₁ ≥ $2,2M)` con `W₀ = $2M`, sujeto a no empeorar el escenario 5% malo de la cartera 3, y con commodities/cobre ≤ 5%.

## Cómo correr

```bash
python3 cartera/optimizar_probabilidad.py
```

## Salidas

- `post_optimizado.md` — texto listo para compartir
- `informe_optimizacion.md` — tabla técnica y pesos
- `resultados_optimizacion.json` — números reproducibles
- `retornos_mensuales.csv` — muestra usada para covarianza

## Idea clave

Si el retorno esperado está bajo la meta (+10%), reducir volatilidad **baja** la probabilidad de alcanzarla. El óptimo se mueve sobre el borde del piso de cola, no hacia mínima varianza.
