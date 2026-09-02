"""Orquesta la búsqueda diaria de licitaciones y compras ágiles de café."""

from __future__ import annotations

from typing import Callable

from crl_ofertas.api import MercadoPublicoAPI, chile_today, merge_by_codigo
from crl_ofertas.matching import (
    BUSQUEDAS_COMPRA_AGIL,
    SERVICIO,
    Oferta,
    filtrar_resumenes_licitacion,
    fold,
    oferta_desde_compra_agil,
    oferta_desde_licitacion,
    ordenar,
    parece_cafe,
    sigue_vigente,
)


Progress = Callable[[str], None]


def _necesita_detalle(nombre: str) -> bool:
    texto = fold(nombre)
    if SERVICIO.search(texto):
        return False
    return True


def recolectar(
    api: MercadoPublicoAPI,
    *,
    solo_productos: bool = False,
    max_detalles: int = 35,
    log: Progress | None = None,
) -> list[Oferta]:
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

    detalles_usados = 0
    for row in candidatas:
        codigo = str(row.get("codigo") or "")
        detalle = None
        if codigo and _necesita_detalle(str(row.get("nombre") or "")) and detalles_usados < max_detalles:
            try:
                detalle = api.compra_agil_detalle(codigo)
                detalles_usados += 1
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
        if codigo and detalles_usados < max_detalles:
            try:
                detalle = api.licitacion_detalle(codigo)
                detalles_usados += 1
            except Exception as exc:  # noqa: BLE001
                emit(f"  detalle {codigo} no disponible: {exc}")
        oferta = oferta_desde_licitacion(row, detalle)
        ofertas[f"licitacion:{oferta.codigo}"] = oferta

    lista = [o for o in ordenar(ofertas.values()) if sigue_vigente(o, chile_today())]
    if solo_productos:
        lista = [o for o in lista if o.categoria in {"excelente", "buena", "regular"}]
    return lista
