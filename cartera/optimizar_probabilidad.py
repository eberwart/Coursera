#!/usr/bin/env python3
"""
Optimización horizonte 12 meses.

Objetivo principal:
  max P(W1 >= 2.2M)

sujeto a:
  percentil 5% de W1 >= percentil 5% de la cartera 3
  COMM <= 5%, pesos >= 0, suman 1

Insight: si E[r] < 10%, bajar volatilidad *reduce* P(llegar a +10%).
Por eso el óptimo debe empujar retorno/riesgo a lo largo del *borde*
del piso de cola — no minimizar vol.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
from scipy.stats import norm

OUT = Path(__file__).resolve().parent
W0 = 2_000_000.0
TARGET = 2_200_000.0
R_TARGET = TARGET / W0 - 1.0  # 0.10
RNG = np.random.default_rng(7)

TICKERS = {
    "SPY": "SPY",
    "SMH": "SMH",
    "VEA": "VEA",
    "IPSA": "ECH",
    "ORO": "GLD",
    "COMM": "DBC",
    "RF": "BND",
}
ASSETS = list(TICKERS.keys())
N = len(ASSETS)

PORT3 = np.array([0.225, 0.10, 0.05, 0.25, 0.175, 0.05, 0.15])
PORT_BASE = np.array([0.40, 0.25, 0.05, 0.10, 0.08, 0.05, 0.07])

# Forward-looking annual expected returns
MU0 = np.array([0.080, 0.095, 0.070, 0.090, 0.040, 0.045, 0.038])
TARGET_PORT3_VOL = 0.133
Z05 = norm.ppf(0.05)  # ~ -1.645


def download_monthly() -> pd.DataFrame:
    raw = yf.download(
        list(TICKERS.values()), start="2012-01-01", auto_adjust=True, progress=False
    )["Close"]
    inv = {v: k for k, v in TICKERS.items()}
    monthly = raw.rename(columns=inv)[ASSETS].dropna().resample("ME").last().dropna()
    return monthly.pct_change().dropna()


def build_cov(mrets: pd.DataFrame) -> np.ndarray:
    S = mrets.cov().to_numpy() * 12.0
    n = S.shape[0]
    vols = np.sqrt(np.diag(S))
    std = np.outer(vols, vols)
    corr = np.divide(S, std, out=np.eye(n), where=std > 0)
    avg_corr = (corr.sum() - n) / (n * (n - 1))
    target = (avg_corr * (np.ones((n, n)) - np.eye(n)) + np.eye(n)) * std
    cov = 0.65 * S + 0.35 * target
    v3 = float(np.sqrt(PORT3 @ cov @ PORT3))
    return cov * (TARGET_PORT3_VOL / v3) ** 2


def calibrate_mu(cov: np.ndarray) -> np.ndarray:
    """Shift paralelo para que P(W>2M) de cartera 3 ≈ 69.9% bajo normalidad."""
    mu = MU0.copy()
    for _ in range(30):
        m = float(PORT3 @ mu)
        s = float(np.sqrt(PORT3 @ cov @ PORT3))
        p = float(norm.cdf(m / s))
        if abs(p - 0.699) < 0.002:
            break
        # dP/dshift ≈ φ(m/s)/s
        mu += (0.699 - p) * s / max(norm.pdf(m / s), 1e-3) * 0.5
    return mu


def port_stats(w, mu, cov):
    w = np.asarray(w, float)
    w = np.clip(w, 0, None)
    w = w / w.sum()
    m = float(w @ mu)
    s = float(np.sqrt(max(w @ cov @ w, 1e-16)))
    return m, s


def p_meta_normal(m, s):
    return float(norm.cdf((m - R_TARGET) / s))


def p_above0_normal(m, s):
    return float(norm.cdf(m / s))


def p5_wealth_normal(m, s):
    return W0 * (1 + m + Z05 * s)


def mc_metrics(name, w, mu, cov, n=100_000):
    m, s = port_stats(w, mu, cov)
    # Normal + contaminación t para colas
    draws = RNG.multivariate_normal(mu, cov, size=n)
    L = np.linalg.cholesky(cov + 1e-10 * np.eye(N))
    t = RNG.standard_t(5, size=(n, N)) / np.sqrt(5 / 3)
    mixed = 0.85 * draws + 0.15 * (t @ L.T + mu)
    r = mixed @ (np.clip(w, 0, None) / np.clip(w, 0, None).sum())
    wealth = W0 * (1 + r)
    ww = {a: round(float((w / w.sum())[i]), 4) for i, a in enumerate(ASSETS)}
    return {
        "name": name,
        "weights": ww,
        "expected_return": round(m, 4),
        "volatility": round(s, 4),
        "p_finish_above_2m": round(float((wealth > W0).mean()), 4),
        "p_finish_above_2_2m": round(float((wealth >= TARGET).mean()), 4),
        "p_finish_above_2_2m_normal": round(p_meta_normal(m, s), 4),
        "worst_5pct_wealth": round(float(np.quantile(wealth, 0.05)), 0),
        "worst_5pct_wealth_normal": round(p5_wealth_normal(m, s), 0),
        "median_wealth": round(float(np.quantile(wealth, 0.50)), 0),
        "expected_wealth": round(float(wealth.mean()), 0),
        "sharpe_approx": round(m / s, 3),
    }


def optimize_max_p_meta(mu, cov, r5_floor, comm_cap=0.05, extras=None):
    """
    max (μ - 0.10)/σ  ≡ max P(r>=10%) bajo normalidad
    s.t. μ + Z05*σ >= r5_floor
         sum w = 1, w>=0, w_COMM <= comm_cap
         optional extras: dict of bounds
    """
    extras = extras or {}

    def neg_obj(w):
        m, s = port_stats(w, mu, cov)
        return -((m - R_TARGET) / s)

    cons = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {
            "type": "ineq",
            "fun": lambda w: port_stats(w, mu, cov)[0]
            + Z05 * port_stats(w, mu, cov)[1]
            - r5_floor,
        },
    ]
    bounds = [(0.0, 1.0)] * N
    # COMM cap
    bounds[ASSETS.index("COMM")] = (0.0, comm_cap)
    for asset, (lo, hi) in extras.items():
        i = ASSETS.index(asset)
        bounds[i] = (lo, hi)

    seeds = [
        PORT3.copy(),
        PORT_BASE.copy(),
        np.ones(N) / N,
        np.array([0.35, 0.15, 0.05, 0.20, 0.10, 0.05, 0.10]),
        np.array([0.25, 0.20, 0.05, 0.25, 0.10, 0.05, 0.10]),
        np.array([0.30, 0.10, 0.10, 0.15, 0.15, 0.05, 0.15]),
        np.array([0.50, 0.05, 0.05, 0.10, 0.05, 0.05, 0.20]),
        np.array([0.20, 0.15, 0.05, 0.30, 0.15, 0.05, 0.10]),
    ]
    best_w, best_val = None, 1e18
    for s0 in seeds:
        s0 = s0 / s0.sum()
        # proyectar bounds
        for i, (lo, hi) in enumerate(bounds):
            s0[i] = min(max(s0[i], lo), hi)
        s0 = s0 / s0.sum()
        res = minimize(
            neg_obj,
            s0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 400, "ftol": 1e-12},
        )
        if not res.success and res.fun > best_val:
            continue
        val = float(res.fun)
        if val < best_val:
            best_val = val
            best_w = np.clip(res.x, 0, None)
            best_w = best_w / best_w.sum()
    return best_w


def engines(w):
    d = {a: float(w[i]) for i, a in enumerate(ASSETS)}
    return {
        "EEUU": d["SPY"] + d["SMH"],
        "SPY": d["SPY"],
        "SMH": d["SMH"],
        "Chile": d["IPSA"],
        "Diversificadores": d["ORO"] + d["RF"] + d["COMM"],
        "ORO": d["ORO"],
        "RF": d["RF"],
        "COMM": d["COMM"],
        "VEA": d["VEA"],
    }


def main():
    print("Datos…")
    mrets = download_monthly()
    mrets.to_csv(OUT / "retornos_mensuales.csv")
    cov = build_cov(mrets)
    mu = calibrate_mu(cov)

    m3, s3 = port_stats(PORT3, mu, cov)
    r5_floor = m3 + Z05 * s3
    print(f"Cartera 3: E[r]={m3:.3%}, vol={s3:.3%}, P(>0)={p_above0_normal(m3,s3):.1%}, "
          f"P(>=10%)={p_meta_normal(m3,s3):.1%}, r5={r5_floor:.3%}")

    # 1) Óptimo libre con piso de cola
    w_opt = optimize_max_p_meta(mu, cov, r5_floor, comm_cap=0.05)
    # 2) Sin piso
    w_unc = optimize_max_p_meta(mu, cov, r5_floor=-1.0, comm_cap=0.05)
    # 3) Espíritu 3 motores
    w_spirit = optimize_max_p_meta(
        mu,
        cov,
        r5_floor,
        comm_cap=0.05,
        extras={
            "IPSA": (0.15, 0.40),
            "RF": (0.10, 0.35),
            "ORO": (0.08, 0.30),
            "SMH": (0.0, 0.12),
            "SPY": (0.10, 0.40),
            "VEA": (0.0, 0.15),
        },
    )
    # 4) Piso más estricto (+$40k en wealth ≈ +2pp en retorno de cola)
    r5_tight = (p5_wealth_normal(m3, s3) + 40_000) / W0 - 1.0
    w_tight = optimize_max_p_meta(mu, cov, r5_tight, comm_cap=0.05)

    results = [
        mc_metrics("base_instagram_tech", PORT_BASE, mu, cov),
        mc_metrics("cartera_3", PORT3, mu, cov),
        mc_metrics("opt_max_P_meta_con_piso_p5", w_opt, mu, cov),
        mc_metrics("opt_espiritu_3_motores", w_spirit, mu, cov),
        mc_metrics("opt_piso_p5_mas_40k", w_tight, mu, cov),
        mc_metrics("opt_sin_piso_p5", w_unc, mu, cov),
    ]

    payload = {
        "assumptions": {
            "W0": W0,
            "target": TARGET,
            "forward_mu": {a: round(float(mu[i]), 4) for i, a in enumerate(ASSETS)},
            "port3_vol": round(s3, 4),
            "r5_floor_return": round(r5_floor, 4),
            "r5_floor_wealth": round(W0 * (1 + r5_floor), 0),
            "chile_proxy": "ECH",
            "comm_cap": 0.05,
            "sample": f"{mrets.index.min().date()} → {mrets.index.max().date()}",
            "objective": "max P(W>=2.2M) s.t. VaR5% wealth >= cartera 3, COMM<=5%",
            "note": (
                "Con E[r]<10%, minimizar vol reduce P(meta). "
                "El óptimo opera en el borde del piso de cola."
            ),
        },
        "portfolios": results,
        "engines": {
            "opt_libre": engines(w_opt),
            "opt_espiritu": engines(w_spirit),
        },
    }
    (OUT / "resultados_optimizacion.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    m3d = results[1]
    mop = results[2]
    msp = results[3]
    e = engines(w_opt)
    es = engines(w_spirit)

    post = f"""Esto me parece mucho más revelador.

## Mi elección para un horizonte de exactamente un año

Me quedaría con una **versión re-optimizada de la tercera cartera**.

No porque maximice el Sharpe, sino porque el horizonte de 12 meses es corto — y eso cambia la pregunta.

### La pregunta correcta

¿Qué combinación de estos activos maximiza la probabilidad de que mis $2 millones superen **$2,2 millones** dentro de exactamente un año, limitando al mismo tiempo la pérdida del 5% peor?

Eso cambia la función objetivo por completo. El algoritmo elige pesos entre SPY, SMH, VEA, IPSA, oro, commodities y renta fija (con cobre/commodities topeados en 5%).

### Un matiz que importa

Con retorno esperado bajo la meta del +10%, **bajar volatilidad no ayuda a llegar a $2,2M** — ayuda a no perder, pero reduce la probabilidad de alcanzar el +10%. El óptimo tiene que empujar retorno sobre el *borde* del escenario 5% malo, no esconderse en renta fija.

### Resultados (calibrados a vol cartera 3 ≈ 13,3%)

| | Cartera 3 | Óptimo libre* | Óptimo 3 motores** |
|---|---:|---:|---:|
| P(≥ $2,2M) | {100*m3d['p_finish_above_2_2m']:.1f}% | {100*mop['p_finish_above_2_2m']:.1f}% | {100*msp['p_finish_above_2_2m']:.1f}% |
| P(> $2M) | {100*m3d['p_finish_above_2m']:.1f}% | {100*mop['p_finish_above_2m']:.1f}% | {100*msp['p_finish_above_2m']:.1f}% |
| Escenario 5% malo | ${m3d['worst_5pct_wealth']/1e6:.2f}M | ${mop['worst_5pct_wealth']/1e6:.2f}M | ${msp['worst_5pct_wealth']/1e6:.2f}M |
| Vol | {100*m3d['volatility']:.1f}% | {100*mop['volatility']:.1f}% | {100*msp['volatility']:.1f}% |
| E[r] | {100*m3d['expected_return']:.1f}% | {100*mop['expected_return']:.1f}% | {100*msp['expected_return']:.1f}% |

\\* Piso de cola ≥ cartera 3; COMM ≤ 5%.  
\\*\\* Además: Chile ≥ 15%, oro ≥ 8%, RF ≥ 10%, SMH ≤ 12%, SPY ≤ 40%.

### Lo que ejecutaría

Me quedo con el **óptimo de tres motores** — sacrifica poco (o nada) de cola, mejora la probabilidad de meta, y no vuelve a la apuesta Instagram a US technology:

- **{100*es['EEUU']:.1f}% EE.UU.** ({100*es['SPY']:.1f}% SPY + {100*es['SMH']:.1f}% SMH)
- **{100*es['Chile']:.1f}% Chile/IPSA**
- **{100*es['Diversificadores']:.1f}% diversificadores** ({100*es['ORO']:.1f}% oro + {100*es['RF']:.1f}% RF + {100*es['COMM']:.1f}% commodities)
- **{100*es['VEA']:.1f}% VEA**

Pesos detalle (óptimo 3 motores): {', '.join(f"{k} {100*v:.1f}%" for k,v in msp['weights'].items())}.

Si soltara el filtro conceptual, el óptimo libre haría más énfasis en EE.UU. ({100*e['EEUU']:.1f}%: {100*e['SPY']:.1f}% SPY + {100*e['SMH']:.1f}% SMH) y Chile al {100*e['Chile']:.1f}% — con P(meta) {100*mop['p_finish_above_2_2m']:.1f}% — pero se aleja del diseño de tres motores.

### Cobre

No aumentaría el cobre ahora. Sus fundamentos estructurales siguen atractivos —redes eléctricas, data centers, electrificación y restricciones de oferta—, pero el precio ya incorpora bastante optimismo y esta misma semana mostró cuánto puede moverse por una noticia arancelaria. Tope: **5%**.

### Por qué esta formulación

Maximizar Sharpe responde a eficiencia por unidad de volatilidad.  
Con horizonte fijo de 12 meses y capital ya en mano, lo que importa es:

1. la probabilidad de llegar a la meta (+10%), y  
2. no empeorar el escenario malo del 5%.

De las optimizaciones que hemos corrido, esta es la más apropiada para este horizonte.
"""
    (OUT / "post_optimizado.md").write_text(post, encoding="utf-8")

    # Informe técnico corto
    lines = [
        "# Optimización P(W≥2,2M) con piso de cola",
        "",
        "## Supuestos",
        "",
        f"- Medias forward: {payload['assumptions']['forward_mu']}",
        f"- Vol cartera 3 ancla: {100*s3:.1f}%",
        f"- Piso r5: {100*r5_floor:.2f}% → ${W0*(1+r5_floor)/1e6:.2f}M",
        "",
        "## Resultados",
        "",
        "| Cartera | E[r] | Vol | P(>2M) | P(≥2,2M) | P5 wealth |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m in results:
        lines.append(
            f"| {m['name']} | {100*m['expected_return']:.1f}% | {100*m['volatility']:.1f}% | "
            f"{100*m['p_finish_above_2m']:.1f}% | {100*m['p_finish_above_2_2m']:.1f}% | "
            f"${m['worst_5pct_wealth']/1e6:.2f}M |"
        )
    lines += ["", "## Pesos", ""]
    for m in results:
        lines.append(f"### {m['name']}")
        for a, v in m["weights"].items():
            lines.append(f"- {a}: {100*v:.1f}%")
        lines.append("")
    (OUT / "informe_optimizacion.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(results[1], indent=2, ensure_ascii=False))
    print(json.dumps(results[2], indent=2, ensure_ascii=False))
    print(json.dumps(results[3], indent=2, ensure_ascii=False))
    print(json.dumps(results[5], indent=2, ensure_ascii=False))
    print("OK →", OUT / "post_optimizado.md")


if __name__ == "__main__":
    main()
