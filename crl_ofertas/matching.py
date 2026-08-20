"""Puntaje de ofertas según el rubro de CRL Coffee: café de especialidad en grano."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from crl_ofertas.api import PORTAL_COMPRA_AGIL, PORTAL_LICITACION

UNSPSC_CAFE_GRANO = {"50201706"}
UNSPSC_CAFE_INSTANTANEO = {"50201709", "50201708"}
UNSPSC_EQUIPO_CAFE = {"52141526", "52141529", "48101513", "48101514"}
UNSPSC_SERVICIO_CAFE = {"90101603", "90101701", "90111603", "90101500"}

BUSQUEDAS_COMPRA_AGIL = (
    "café",
    "cafe",
    "coffee",
    "coffe",
    "cafetería",
    "cafeteria",
    "grano",
    "tostado",
    "arábica",
    "arabica",
    "nescafé",
    "nescafe",
)

# Títulos que parecen café pero no son el producto de CRL.
CONCESION = re.compile(r"\bconcesion(es)?\b|\barriendo de (espacio|local)\b")
OBRA = re.compile(r"\b(construccion|arquitectura|especialidades tecnicas|obra publica)\b")
REPARACION = re.compile(r"\breparacion(es)?\b.*\b(maquina|cafetera|equipo)")
ESPECIALIDAD_MEDICA = re.compile(
    r"\b(medico|medica|cirugia|traumatolog|enfermer|clinico|dental|salud)\b"
)

CAFE_TOKEN = re.compile(r"\b(cafe|coffee|coffe|cafeteria|cafetera|espresso|barista|arabica)\b")
GRANO = re.compile(
    r"\b(grano(s)?|en grano|grano entero|grano arabica|grano selecto|cafe de especialidad)\b"
)
TOSTADO = re.compile(r"\b(tostad[oa]s?|tueste|torrefacci)\b")
ORIGEN = re.compile(
    r"\b(especialidad|origen|colombia|brasil|etiopia|guatemala|peru|honduras|rwanda|geisha|arabica|catuai|caturra)\b"
)
INSTANTANEO = re.compile(
    r"\b(nescafe|liofilizad[oa]|instantane[oa]|soluble|tarro(s)? de cafe|cafe en tarro)\b"
)
SERVICIO = re.compile(
    r"\b(coffe(e)? break|coffee break|servicio de (cafe|cafeteria|catering)|catering|brunch)\b"
)
INSUMOS = re.compile(r"\binsumos (de )?(cafeteria|cafe)\b|\bcompra de cafe\b|\badquisicion de cafe\b")
MAQUINA = re.compile(r"\b(maquina|dispensadora|comodato|cafetera|molinillo|moledor)\b")


def fold(text: str | None) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _codes(value: Any) -> set[str]:
    if value is None:
        return set()
    return {str(value).strip()}


@dataclass
class Producto:
    codigo: str = ""
    nombre: str = ""
    descripcion: str = ""
    cantidad: float | None = None
    unidad: str = ""


@dataclass
class Oferta:
    fuente: str
    codigo: str
    nombre: str
    estado: str
    organismo: str = ""
    region: str = ""
    comuna: str = ""
    fecha_cierre: str = ""
    fecha_publicacion: str = ""
    monto: float | None = None
    moneda: str = "CLP"
    puntaje: int = 0
    categoria: str = "descartada"
    razones: list[str] = field(default_factory=list)
    productos: list[Producto] = field(default_factory=list)
    descripcion: str = ""
    url: str = ""
    encaja_producto: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def corpus(oferta: Oferta) -> str:
    parts = [oferta.nombre, oferta.descripcion]
    for producto in oferta.productos:
        parts.extend([producto.nombre, producto.descripcion, producto.codigo])
    return fold(" ".join(part for part in parts if part))


def parece_cafe(texto: str) -> bool:
    normalized = fold(texto)
    if not CAFE_TOKEN.search(normalized):
        return False
    if ESPECIALIDAD_MEDICA.search(normalized) and "cafe" not in normalized and "coffee" not in normalized:
        return False
    if OBRA.search(normalized) and not INSUMOS.search(normalized):
        return False
    return True


def _categoria(puntaje: int, texto: str, encaja_producto: bool) -> str:
    if CONCESION.search(texto) and not INSUMOS.search(texto):
        return "descartada"
    if puntaje < 18:
        return "descartada"
    if encaja_producto and puntaje >= 70:
        return "excelente"
    if encaja_producto and puntaje >= 45:
        return "buena"
    if INSTANTANEO.search(texto):
        return "regular"
    if SERVICIO.search(texto) and not encaja_producto:
        return "servicio"
    if puntaje >= 45:
        return "buena"
    return "regular"


def puntuar(oferta: Oferta) -> Oferta:
    texto = corpus(oferta)
    razones: list[str] = []
    score = 0
    encaja = False

    unspsc = {fold(p.codigo) for p in oferta.productos}
    unspsc |= {str(p.codigo).strip() for p in oferta.productos}

    if not CAFE_TOKEN.search(texto) and not (unspsc & (UNSPSC_CAFE_GRANO | UNSPSC_CAFE_INSTANTANEO)):
        oferta.puntaje = 0
        oferta.categoria = "descartada"
        oferta.razones = ["No menciona café ni códigos UNSPSC de café"]
        return oferta

    if CONCESION.search(texto) and not INSUMOS.search(texto):
        oferta.puntaje = 5
        oferta.categoria = "descartada"
        oferta.razones = ["Es concesión o arriendo de cafetería, no suministro de café"]
        return oferta

    if REPARACION.search(texto) and not GRANO.search(texto) and not (unspsc & UNSPSC_CAFE_GRANO):
        oferta.puntaje = 8
        oferta.categoria = "descartada"
        oferta.razones = ["Es reparación de máquina, no venta de café"]
        return oferta

    if unspsc & UNSPSC_CAFE_GRANO:
        score += 40
        encaja = True
        razones.append("Ítem UNSPSC 50201706 (Café)")
    if GRANO.search(texto):
        score += 35
        encaja = True
        razones.append("Pide café en grano o de especialidad")
    if TOSTADO.search(texto):
        score += 15
        encaja = True
        razones.append("Menciona café tostado")
    if ORIGEN.search(texto) and CAFE_TOKEN.search(texto):
        score += 12
        razones.append("Habla de origen, arábica o especialidad")
    if INSUMOS.search(texto):
        score += 18
        razones.append("Compra de café o insumos de cafetería")
    if INSTANTANEO.search(texto) or unspsc & UNSPSC_CAFE_INSTANTANEO:
        score += 22
        razones.append("Pide café instantáneo o tipo Nescafé (equivalente posible, no es tu fuerte)")
    if SERVICIO.search(texto):
        score += 20
        razones.append("Es un servicio de coffee break o catering")
    if MAQUINA.search(texto) or unspsc & UNSPSC_EQUIPO_CAFE:
        score += 6
        razones.append("Incluye cafetera, molino o máquina en comodato")
    if unspsc & UNSPSC_SERVICIO_CAFE and not encaja:
        score += 6
        razones.append("Código de servicio de cafetería/catering")

    # CRL Coffee envía a todo Chile; no penalizamos región, pero premiamos producto puro.
    if encaja and not SERVICIO.search(texto):
        score += 10
        razones.append("Encaja con suministro de café (tu rubro)")

    oferta.puntaje = max(0, min(100, score))
    oferta.encaja_producto = encaja
    oferta.categoria = _categoria(oferta.puntaje, texto, encaja)
    oferta.razones = razones or ["Mención débil de café"]
    return oferta


def oferta_desde_compra_agil(item: dict[str, Any], detalle: dict[str, Any] | None = None) -> Oferta:
    data = detalle or item
    institucion = data.get("institucion") or item.get("institucion") or {}
    fechas = data.get("fechas") or item.get("fechas") or {}
    montos = data.get("montos") or item.get("montos") or {}
    presupuesto = data.get("presupuesto") or {}
    estado = data.get("estado") or item.get("estado") or {}
    productos_raw = data.get("productos_solicitados") or []
    productos = [
        Producto(
            codigo=str(prod.get("codigo_producto") or ""),
            nombre=str(prod.get("nombre") or ""),
            descripcion=str(prod.get("descripcion") or ""),
            cantidad=_as_float(prod.get("cantidad")),
            unidad=str(prod.get("unidad_medida") or ""),
        )
        for prod in productos_raw
    ]
    codigo = str(data.get("codigo") or item.get("codigo") or "")
    monto = presupuesto.get("monto_disponible_clp")
    if monto is None:
        monto = montos.get("monto_disponible_clp")
    oferta = Oferta(
        fuente="compra_agil",
        codigo=codigo,
        nombre=str(data.get("nombre") or item.get("nombre") or ""),
        estado=str(estado.get("glosa") or estado.get("codigo") or ""),
        organismo=str(institucion.get("organismo_comprador") or ""),
        region=str(institucion.get("nombre_region") or institucion.get("region") or ""),
        fecha_cierre=str(fechas.get("fecha_cierre") or ""),
        fecha_publicacion=str(fechas.get("fecha_publicacion") or ""),
        monto=_as_float(monto),
        moneda=str(presupuesto.get("moneda") or montos.get("moneda") or "CLP"),
        descripcion=str(data.get("descripcion") or ""),
        productos=productos,
        url=PORTAL_COMPRA_AGIL.format(codigo=codigo),
    )
    return puntuar(oferta)


def oferta_desde_licitacion(resumen: dict[str, Any], detalle: dict[str, Any] | None = None) -> Oferta:
    data = detalle or resumen
    comprador = data.get("Comprador") or {}
    fechas = data.get("Fechas") or {}
    items = ((data.get("Items") or {}).get("Listado")) or []
    productos = [
        Producto(
            codigo=str(item.get("CodigoProducto") or ""),
            nombre=str(item.get("NombreProducto") or ""),
            descripcion=str(item.get("Descripcion") or ""),
            cantidad=_as_float(item.get("Cantidad")),
            unidad=str(item.get("UnidadMedida") or ""),
        )
        for item in items
    ]
    codigo = str(data.get("CodigoExterno") or resumen.get("CodigoExterno") or "")
    oferta = Oferta(
        fuente="licitacion",
        codigo=codigo,
        nombre=str(data.get("Nombre") or resumen.get("Nombre") or ""),
        estado=str(data.get("Estado") or resumen.get("CodigoEstado") or ""),
        organismo=str(comprador.get("NombreOrganismo") or ""),
        region=str(comprador.get("RegionUnidad") or ""),
        comuna=str(comprador.get("ComunaUnidad") or ""),
        fecha_cierre=str(fechas.get("FechaCierre") or data.get("FechaCierre") or resumen.get("FechaCierre") or ""),
        fecha_publicacion=str(fechas.get("FechaPublicacion") or ""),
        monto=_as_float(data.get("MontoEstimado")),
        moneda=str(data.get("Moneda") or "CLP"),
        descripcion=str(data.get("Descripcion") or ""),
        productos=productos,
        url=PORTAL_LICITACION.format(codigo=codigo),
    )
    return puntuar(oferta)


def filtrar_resumenes_licitacion(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    utiles = []
    for row in rows:
        nombre = fold(str(row.get("Nombre") or ""))
        if not CAFE_TOKEN.search(nombre):
            continue
        if CONCESION.search(nombre) and not INSUMOS.search(nombre):
            continue
        if ESPECIALIDAD_MEDICA.search(nombre) and "cafe" not in nombre:
            continue
        utiles.append(row)
    return utiles


def ordenar(ofertas: Iterable[Oferta]) -> list[Oferta]:
    orden_categoria = {
        "excelente": 0,
        "buena": 1,
        "regular": 2,
        "servicio": 3,
        "descartada": 4,
    }
    return sorted(
        ofertas,
        key=lambda o: (orden_categoria.get(o.categoria, 9), -o.puntaje, o.fecha_cierre or "9999"),
    )


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
