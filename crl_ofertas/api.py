"""Clientes de las APIs públicas de Mercado Público."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from crl_ofertas.http import HttpClient, MercadoPublicoError

SANTIAGO = ZoneInfo("America/Santiago")
LICITACIONES_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
COMPRA_AGIL_URL = "https://api2.mercadopublico.cl/v2/compra-agil"

PORTAL_LICITACION = (
    "https://www.mercadopublico.cl/Procurement/Modules/RFB/"
    "DetailsAcquisition.aspx?idlicitacion={codigo}"
)
PORTAL_COMPRA_AGIL = "https://www.mercadopublico.cl/Home/Search?k={codigo}"


def chile_today(now: datetime | None = None) -> date:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(SANTIAGO).date()


def format_mp_date(value: date) -> str:
    return value.strftime("%d%m%Y")


class MercadoPublicoAPI:
    def __init__(self, ticket: str, http: HttpClient | None = None) -> None:
        if not ticket or ticket.strip() in {"", "TU_TICKET_AQUI"}:
            raise MercadoPublicoError(
                "Falta el ticket de Mercado Público. Solicítalo con Clave Única en "
                "https://www.chilecompra.cl/api/ y defínelo en MERCADO_PUBLICO_TICKET."
            )
        self.http = http or HttpClient(ticket)

    def licitaciones_activas(self) -> list[dict[str, Any]]:
        data = self.http.get_json(LICITACIONES_URL, params={"estado": "activas"}, ticket_in="query")
        return list((data or {}).get("Listado") or [])

    def licitaciones_publicadas(self, dia: date) -> list[dict[str, Any]]:
        data = self.http.get_json(
            LICITACIONES_URL,
            params={"fecha": format_mp_date(dia), "estado": "publicada"},
            ticket_in="query",
        )
        return list((data or {}).get("Listado") or [])

    def licitacion_detalle(self, codigo: str) -> dict[str, Any] | None:
        data = self.http.get_json(LICITACIONES_URL, params={"codigo": codigo}, ticket_in="query")
        listado = (data or {}).get("Listado") or []
        return listado[0] if listado else None

    def compras_agiles(
        self,
        *,
        query: str,
        estado: str = "publicada",
        page_size: int = 50,
        max_pages: int = 4,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            data = self.http.get_json(
                COMPRA_AGIL_URL,
                params={
                    "q": query,
                    "estado": estado,
                    "tamano_pagina": page_size,
                    "numero_pagina": page,
                    "ordenar_por": "FechaPublicacion",
                },
                ticket_in="header",
            )
            if not data or data.get("success") != "OK":
                errors = (data or {}).get("errors")
                raise MercadoPublicoError(f"Compra Ágil rechazó q={query!r}: {errors}")
            payload = data.get("payload") or {}
            batch = list(payload.get("items") or [])
            items.extend(batch)
            paginacion = payload.get("paginacion") or {}
            total_pages = int(paginacion.get("total_paginas") or 1)
            if page >= total_pages or not batch:
                break
        return items

    def compra_agil_detalle(self, codigo: str) -> dict[str, Any] | None:
        data = self.http.get_json(f"{COMPRA_AGIL_URL}/{codigo}", ticket_in="header")
        if not data or data.get("success") != "OK":
            return None
        return data.get("payload")


def merge_by_codigo(rows: Iterable[dict[str, Any]], key: str = "codigo") -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        codigo = str(row.get(key) or "").strip()
        if codigo:
            seen[codigo] = row
    return list(seen.values())
