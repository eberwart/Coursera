"""Reportes HTML, CSV y JSON para el dueño de CRL Coffee."""

from __future__ import annotations

import csv
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from crl_ofertas.api import SANTIAGO
from crl_ofertas.matching import Oferta

TITULOS = {
    "excelente": "Excelente encaje — café en grano o de especialidad",
    "buena": "Buena — suministro de café o insumos de cafetería",
    "regular": "Regular — instantáneo, Nescafé u oferta mixta",
    "servicio": "Servicio — coffee break o catering (no es solo grano)",
    "descartada": "Descartadas",
}

COLORES = {
    "excelente": "#3b6d11",
    "buena": "#8a5a12",
    "regular": "#6b4f3a",
    "servicio": "#3d5a6c",
    "descartada": "#666666",
}


def _clp(value: float | None) -> str:
    if value is None:
        return "No informado"
    return "$" + f"{int(round(value)):,}".replace(",", ".")


def resumen(ofertas: Iterable[Oferta]) -> dict[str, int]:
    counts = Counter(o.categoria for o in ofertas)
    return {
        "total": sum(counts.values()),
        "excelente": counts.get("excelente", 0),
        "buena": counts.get("buena", 0),
        "regular": counts.get("regular", 0),
        "servicio": counts.get("servicio", 0),
        "descartada": counts.get("descartada", 0),
    }


def ofertas_visibles(ofertas: list[Oferta], incluir_descartadas: bool = False) -> list[Oferta]:
    if incluir_descartadas:
        return ofertas
    return [o for o in ofertas if o.categoria != "descartada"]


def render_html(ofertas: list[Oferta], generado: datetime | None = None) -> str:
    generado = generado or datetime.now(timezone.utc)
    local = generado.astimezone(SANTIAGO)
    stats = resumen(ofertas)
    visibles = ofertas_visibles(ofertas)
    bloques = []
    for categoria in ("excelente", "buena", "regular", "servicio"):
        grupo = [o for o in visibles if o.categoria == categoria]
        if not grupo:
            continue
        tarjetas = "\n".join(_tarjeta(o) for o in grupo)
        bloques.append(
            f"<section><h2>{html.escape(TITULOS[categoria])} "
            f"<span class='count'>{len(grupo)}</span></h2>"
            f"<div class='grid'>{tarjetas}</div></section>"
        )
    body = "\n".join(bloques) or "<p>Hoy no hay ofertas abiertas que encajen con café en grano.</p>"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ofertas Mercado Público — CRL Coffee {local.strftime('%Y-%m-%d')}</title>
  <style>
    :root {{ --ink:#24160f; --paper:#f7f1e8; --accent:#8b4c1f; }}
    body {{ font-family: Georgia, 'Times New Roman', serif; background: var(--paper);
           color: var(--ink); margin: 0; padding: 24px; }}
    header {{ max-width: 1100px; margin: 0 auto 24px; }}
    h1 {{ font-size: 1.8rem; margin: 0 0 8px; }}
    .meta {{ color: #5b4636; }}
    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }}
    .stat {{ background: #fff; border: 1px solid #e0d3c2; border-radius: 12px; padding: 12px 16px; }}
    .stat b {{ display: block; font-size: 1.4rem; }}
    section {{ max-width: 1100px; margin: 0 auto 28px; }}
    h2 {{ font-size: 1.2rem; border-bottom: 2px solid var(--accent); padding-bottom: 6px; }}
    .count {{ background: var(--accent); color: #fff; border-radius: 999px; padding: 1px 8px; font-size: .8rem; }}
    .grid {{ display: grid; gap: 14px; }}
    article {{ background: #fff; border: 1px solid #e0d3c2; border-radius: 14px; padding: 16px 18px; }}
    .badge {{ display: inline-block; color: #fff; border-radius: 999px; padding: 2px 10px; font-size: .75rem; letter-spacing: .04em; }}
    .codigo {{ font-family: ui-monospace, monospace; }}
    ul {{ margin: 8px 0 0; padding-left: 18px; }}
    a {{ color: var(--accent); }}
    footer {{ max-width: 1100px; margin: 32px auto 0; font-size: .85rem; color: #5b4636; }}
  </style>
</head>
<body>
  <header>
    <h1>Ofertas de Mercado Público para CRL Coffee</h1>
    <p class="meta">Café de especialidad en grano · Coffee Roasting Labs ·
    {html.escape(local.strftime('%d-%m-%Y %H:%M'))} hora Chile</p>
    <div class="stats">
      <div class="stat"><b>{stats['excelente']}</b> excelentes</div>
      <div class="stat"><b>{stats['buena']}</b> buenas</div>
      <div class="stat"><b>{stats['regular']}</b> regulares</div>
      <div class="stat"><b>{stats['servicio']}</b> coffee break</div>
      <div class="stat"><b>{len(visibles)}</b> para revisar hoy</div>
    </div>
  </header>
  {body}
  <footer>
    Fuente: Dirección ChileCompra / Mercado Público. Esta lista prioriza café en grano,
    tostado y de especialidad (lo que vende <a href="https://www.crlcoffee.cl">crlcoffee.cl</a>).
    Los coffee break aparecen aparte porque son un servicio, no una compra de grano.
  </footer>
</body>
</html>
"""


def _tarjeta(oferta: Oferta) -> str:
    color = COLORES.get(oferta.categoria, "#666")
    productos = "".join(
        f"<li>{html.escape(p.nombre)}"
        + (f" — {html.escape(p.descripcion[:220])}" if p.descripcion else "")
        + (f" ({p.cantidad:g} {html.escape(p.unidad)})" if p.cantidad is not None else "")
        + "</li>"
        for p in oferta.productos
    ) or "<li>Sin ítems detallados en la ficha pública</li>"
    razones = "".join(f"<li>{html.escape(r)}</li>" for r in oferta.razones)
    fuente = "Compra Ágil" if oferta.fuente == "compra_agil" else "Licitación"
    return f"""
    <article>
      <div><span class="badge" style="background:{color}">{html.escape(oferta.categoria.upper())} · {oferta.puntaje}</span>
           <span>{html.escape(fuente)}</span></div>
      <h3>{html.escape(oferta.nombre)}</h3>
      <p class="codigo">{html.escape(oferta.codigo)} · cierra {html.escape(oferta.fecha_cierre or 's/fecha')}
         · {html.escape(_clp(oferta.monto))}</p>
      <p>{html.escape(oferta.organismo)}{(' · ' + html.escape(oferta.region)) if oferta.region else ''}</p>
      <p><a href="{html.escape(oferta.url)}">Abrir en Mercado Público</a></p>
      <p>{html.escape((oferta.descripcion or '')[:420])}</p>
      <strong>Por qué aparece</strong>
      <ul>{razones}</ul>
      <strong>Productos</strong>
      <ul>{productos}</ul>
    </article>
    """


def write_reports(ofertas: list[Oferta], salida: Path, fecha: str) -> dict[str, Path]:
    salida.mkdir(parents=True, exist_ok=True)
    html_path = salida / f"ofertas-{fecha}.html"
    json_path = salida / f"ofertas-{fecha}.json"
    csv_path = salida / f"ofertas-{fecha}.csv"
    latest_html = salida / "ofertas-hoy.html"
    latest_json = salida / "ofertas-hoy.json"

    visibles = ofertas_visibles(ofertas)
    html_path.write_text(render_html(ofertas), encoding="utf-8")
    latest_html.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")

    payload = {
        "fecha": fecha,
        "fuente": "Dirección ChileCompra / Mercado Público",
        "rubro": "Café de especialidad en grano — Coffee Roasting Labs (CRL Coffee)",
        "resumen": resumen(ofertas),
        "ofertas": [o.to_dict() for o in visibles],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "categoria",
                "puntaje",
                "fuente",
                "codigo",
                "nombre",
                "organismo",
                "region",
                "fecha_cierre",
                "monto",
                "moneda",
                "url",
                "razones",
            ],
        )
        writer.writeheader()
        for oferta in visibles:
            writer.writerow(
                {
                    "categoria": oferta.categoria,
                    "puntaje": oferta.puntaje,
                    "fuente": oferta.fuente,
                    "codigo": oferta.codigo,
                    "nombre": oferta.nombre,
                    "organismo": oferta.organismo,
                    "region": oferta.region,
                    "fecha_cierre": oferta.fecha_cierre,
                    "monto": oferta.monto if oferta.monto is not None else "",
                    "moneda": oferta.moneda,
                    "url": oferta.url,
                    "razones": " | ".join(oferta.razones),
                }
            )
    return {"html": html_path, "json": json_path, "csv": csv_path, "hoy": latest_html}
