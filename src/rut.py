"""Generador y validador de RUT chileno (módulo 11)."""

from __future__ import annotations

import argparse
import random
import re
from dataclasses import dataclass

MULTIPLICADORES = (2, 3, 4, 5, 6, 7)

PERSONA_MIN = 1_000_000
PERSONA_MAX = 27_000_000
EMPRESA_MIN = 50_000_000
EMPRESA_MAX = 99_999_999
CUALQUIERA_MIN = 1_000_000
CUALQUIERA_MAX = 99_999_999

RANGOS = {
    "persona": (PERSONA_MIN, PERSONA_MAX),
    "empresa": (EMPRESA_MIN, EMPRESA_MAX),
    "cualquiera": (CUALQUIERA_MIN, CUALQUIERA_MAX),
}


@dataclass(frozen=True)
class Rut:
    cuerpo: int
    dv: str

    def formateado(self, con_puntos: bool = True) -> str:
        cuerpo = f"{self.cuerpo:,}".replace(",", ".") if con_puntos else str(self.cuerpo)
        return f"{cuerpo}-{self.dv}"

    def simple(self) -> str:
        return f"{self.cuerpo}-{self.dv}"

    def __str__(self) -> str:
        return self.formateado()


def calcular_dv(cuerpo: int | str) -> str:
    """Calcula el dígito verificador con el algoritmo módulo 11."""
    texto = str(cuerpo).strip()
    if not texto.isdigit():
        raise ValueError("El cuerpo del RUT debe ser numérico.")
    if int(texto) <= 0:
        raise ValueError("El cuerpo del RUT debe ser un entero positivo.")

    suma = 0
    multiplicador = 0
    for digito in reversed(texto):
        suma += int(digito) * MULTIPLICADORES[multiplicador]
        multiplicador = (multiplicador + 1) % len(MULTIPLICADORES)

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def limpiar_rut(valor: str) -> str:
    return re.sub(r"[^0-9kK]", "", valor).upper()


def parsear_rut(valor: str) -> Rut:
    limpio = limpiar_rut(valor)
    if len(limpio) < 2:
        raise ValueError("RUT incompleto.")
    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit() or int(cuerpo) <= 0:
        raise ValueError("El cuerpo del RUT debe ser un entero positivo.")
    if dv not in "0123456789K":
        raise ValueError("Dígito verificador inválido.")
    return Rut(cuerpo=int(cuerpo), dv=dv)


def validar_rut(valor: str) -> bool:
    try:
        rut = parsear_rut(valor)
    except ValueError:
        return False
    return calcular_dv(rut.cuerpo) == rut.dv


def generar_rut(
    minimo: int = CUALQUIERA_MIN,
    maximo: int = CUALQUIERA_MAX,
    rng: random.Random | None = None,
) -> Rut:
    if minimo <= 0 or maximo <= 0 or minimo > maximo:
        raise ValueError("Rango de generación inválido.")
    fuente = rng or random
    cuerpo = fuente.randint(minimo, maximo)
    return Rut(cuerpo=cuerpo, dv=calcular_dv(cuerpo))


def generar_ruts(
    cantidad: int = 1,
    tipo: str = "cualquiera",
    minimo: int | None = None,
    maximo: int | None = None,
    rng: random.Random | None = None,
) -> list[Rut]:
    if cantidad < 1:
        raise ValueError("La cantidad debe ser al menos 1.")
    if tipo not in RANGOS:
        raise ValueError(f"Tipo desconocido: {tipo}")
    rango_min, rango_max = RANGOS[tipo]
    return [
        generar_rut(
            minimo=minimo if minimo is not None else rango_min,
            maximo=maximo if maximo is not None else rango_max,
            rng=rng,
        )
        for _ in range(cantidad)
    ]


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genera o valida RUTs chilenos con dígito verificador módulo 11."
    )
    parser.add_argument(
        "-n",
        "--cantidad",
        type=int,
        default=1,
        help="Cantidad de RUTs a generar (predeterminado: 1).",
    )
    parser.add_argument(
        "--tipo",
        choices=sorted(RANGOS),
        default="cualquiera",
        help="Rango de generación: persona, empresa o cualquiera.",
    )
    parser.add_argument("--min", dest="minimo", type=int, help="Cuerpo mínimo.")
    parser.add_argument("--max", dest="maximo", type=int, help="Cuerpo máximo.")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Imprime sin puntos (12345678-9).",
    )
    parser.add_argument(
        "--validar",
        metavar="RUT",
        help="Valida un RUT y sale con código 0 si es correcto.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)

    if args.validar:
        es_valido = validar_rut(args.validar)
        print("válido" if es_valido else "inválido")
        return 0 if es_valido else 1

    ruts = generar_ruts(
        cantidad=args.cantidad,
        tipo=args.tipo,
        minimo=args.minimo,
        maximo=args.maximo,
    )
    for rut in ruts:
        print(rut.simple() if args.simple else rut.formateado())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
