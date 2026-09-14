Esto me parece mucho más revelador.

## Mi elección para un horizonte de exactamente un año

Me quedaría con una **versión re-optimizada de la tercera cartera**.

No porque maximice el Sharpe, sino porque el horizonte de 12 meses es corto — y eso cambia la pregunta.

### La pregunta correcta

¿Qué combinación maximiza la probabilidad de que mis $2 millones superen **$2,2 millones** en exactamente un año, limitando al mismo tiempo el escenario 5% malo?

Eso cambia la función objetivo por completo. Dejamos que el algoritmo elija entre SPY, SMH, VEA, IPSA, oro, commodities y renta fija — con cobre/commodities topeados en 5%.

### Un matiz que importa

Con retorno esperado bajo el +10%, **bajar volatilidad no ayuda a llegar a $2,2M**. Ayuda a no perder, pero reduce la probabilidad de alcanzar la meta. El óptimo tiene que empujar retorno sobre el *borde* del escenario 5% malo, no esconderse en renta fija.

Sin ese piso de cola, el algoritmo se va a **100% SMH**: sube P(meta) a ~49%, pero el 5% malo cae a ~$1,38M. Por eso la restricción no es cosmética.

### Resultados

Calibrado para que la cartera 3 tenga vol ≈ 13,3% y P(> $2M) ≈ 70%, como en el análisis previo.

| | Cartera 3 | Óptimo libre* | Óptimo 3 motores** |
|---|---:|---:|---:|
| P(≥ $2,2M) | 39,5% | 42,4% | 41,1% |
| P(> $2M) | 72,8% | 74,2% | 73,8% |
| Escenario 5% malo | $1,76M | $1,76M | $1,76M |
| Vol | 13,3% | 13,8% | 13,6% |
| E[r] | 6,9% | 7,7% | 7,4% |

\* Piso de cola ≥ cartera 3; COMM ≤ 5%.  
\*\* Además: Chile ≥ 15%, oro ≥ 8%, RF ≥ 10%, SMH ≤ 12%, SPY ≤ 40%.

Sacrificamos poco (o nada) de cola frente a la cartera 3, y ganamos ~1,5–3 puntos de probabilidad de meta.

### Lo que ejecutaría

El **óptimo de tres motores** — mejora la meta, no empeora el 5% malo, y no vuelve a la apuesta Instagram a US technology:

- **50,7% EE.UU.** → 40% SPY + 10,7% SMH  
- **16,7% Chile/IPSA**  
- **19,9% diversificadores** → 8% oro + 11,9% RF + **0% commodities**  
- **12,6% VEA**

Redondeado para operar:

| Activo | Peso |
|---|---:|
| SPY | 40% |
| SMH | 11% |
| VEA | 13% |
| IPSA (ECH) | 17% |
| Oro (GLD) | 8% |
| Commodities | 0% |
| RF (BND) | 11% |

Si soltara el filtro conceptual, el óptimo libre pondría ~72% en EE.UU. (casi todo SPY, poco SMH) y Chile al ~15%, con P(meta) 42,4%. Gana un poco más de probabilidad, pero se aleja del diseño de tres motores.

### Cobre

No aumentaría el cobre ahora — y el algoritmo, de hecho, lo **apaga**. Sus fundamentos estructurales siguen atractivos (redes eléctricas, data centers, electrificación, oferta restringida), pero el precio ya incorpora bastante optimismo y esta misma semana mostró cuánto puede moverse por una noticia arancelaria.

### Por qué esta formulación

Maximizar Sharpe responde a otra pregunta: eficiencia por unidad de volatilidad.

Con horizonte fijo de 12 meses y capital ya en mano, lo que importa es:

1. la probabilidad de llegar a la meta (+10%), y  
2. no empeorar el escenario malo del 5%.

De las que hemos corrido, esta es la optimización más apropiada para este horizonte.
