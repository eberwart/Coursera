"""Orquesta la búsqueda diaria de licitaciones y compras ágiles de café."""

from __future__ import annotations

from typing import Callable

from crl_ofertas.api import MercadoPublicoAPI, merge_by_codigo
from crl_ofertas.matching import (
    BUSQUEDAS_COMPRA_AGIL,
    Oferta,
    filtrar_resumenes_licitacion,
    oferta_desde_compra_agil,
    oferta_desde_licitacion,
    ordenar,
    parece_cafe,
)


Progress = Callable[[str], None]


def recolectar(api: MercadoPublicoAPI, *, solo_productos: bool = False, log: Progress | None = None) -> list[Oferta]:
    emit = log or (lambda _msg: None)
    ofertas: dict[str, Oferta] = {}

    emit("Buscando compras ágiles abiertas de café...")
    crudas = []
    for query in BUSQUEDAS_COMPRA_AGIL:
        try:
            lote = api.compras_agiles(query=query)
            emit(f"  · «{query}»: {len(lote)} resultados crudos")
            crudas.extend(lote)
        except Exception as exc:  # noqa: BLE001 — una búsqueda no debe tumbar el resto
            emit(f"  · «{query}» falló: {exc}")
    unicas = merge_by_codigo(crudas, key="codigo")
    candidatas = [row for row in unicas if parece_cafe(str(row.get("nombre") or ""))]
    emit(f"  {len(candidatas)} compras ágiles con café en el título (de {len(unicas)})")

    for row in candidatas:
        codigo = str(row.get("codigo") or "")
        detalle = None
        try:
            detalle = api.compra_agil_detalle(codigo)
        except Exception as exc:  # noqa: BLE001
            emit(f"  detalle {codigo} no disponible: {exc}")
        oferta = oferta_desde_compra_agil(row, detalle)
        ofertas[f"compra_agil:{oferta.codigo}"] = oferta

    emit("Revisando licitaciones activas...")
    activas = api.licitaciones_activas()
    resumenes = filtrar_resumenes_licitacion(activas)
    emit(f"  {len(resumenes)} licitaciones con café en el nombre (de {len(activas)} activas)")
    for row in resumenes:
        codigo = str(row.get("CodigoExterno") or "")
        detalle = None
        try:
            detalle = api.licitacion_detalle(codigo) if codigo else None
        except Exception as exc:  # noqa: BLE001
            emit(f"  detalle {codigo} no disponible: {exc}")
        oferta = oferta_desde_licitacion(row, detalle)
        ofertas[f"licitacion:{oferta.codigo}"] = oferta

    lista = ordenar(ofertas.values())
    if solo_productos:
        lista = [o for o in lista if o.categoria in {"excelente", "buena", "regular"}]
    return lista
