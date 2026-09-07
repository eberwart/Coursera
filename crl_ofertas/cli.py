"""CLI: python -m crl_ofertas --ticket ... """

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

from crl_ofertas.api import MercadoPublicoAPI, chile_today
from crl_ofertas.http import MercadoPublicoError
from crl_ofertas.pipeline import recolectar
from crl_ofertas.report import render_html, write_reports


def _ticket(explicit: str | None) -> str:
    return (explicit or os.environ.get("MERCADO_PUBLICO_TICKET") or os.environ.get("CHILE_PUBLIC_MARKET_TICKET") or "").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lista diaria de licitaciones y compras ágiles de Mercado Público "
            "que encajan con café en grano de especialidad (CRL Coffee)."
        )
    )
    parser.add_argument("--ticket", help="Ticket de api.mercadopublico.cl (o env MERCADO_PUBLICO_TICKET)")
    parser.add_argument("--salida", default="reportes", help="Carpeta de reportes HTML/CSV/JSON")
    parser.add_argument("--solo-productos", action="store_true", help="Oculta coffee break y catering")
    parser.add_argument("--email", help="Correo de destino para el resumen del día")
    parser.add_argument("--smtp-host", default=os.environ.get("SMTP_HOST", ""))
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("SMTP_PORT", "587")))
    parser.add_argument("--smtp-user", default=os.environ.get("SMTP_USER", ""))
    parser.add_argument("--smtp-password", default=os.environ.get("SMTP_PASSWORD", ""))
    return parser


def enviar_email(html_body: str, destino: str, smtp_host: str, smtp_port: int, user: str, password: str, fecha: str) -> None:
    if not smtp_host:
        raise MercadoPublicoError("Para enviar correo define --smtp-host o SMTP_HOST")
    message = EmailMessage()
    message["Subject"] = f"CRL Coffee · ofertas Mercado Público {fecha}"
    message["From"] = user or destino
    message["To"] = destino
    message.set_content("Abre este correo en HTML para ver las ofertas del día.")
    message.add_alternative(html_body, subtype="html")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(message)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ticket = _ticket(args.ticket)
    if not ticket:
        print(
            "Falta el ticket de Mercado Público.\n"
            "1. Entra a https://www.chilecompra.cl/api/ con Clave Única\n"
            "2. Pide tu ticket (llega por correo)\n"
            "3. Ejecuta: MERCADO_PUBLICO_TICKET=tu-ticket python3 -m crl_ofertas",
            file=sys.stderr,
        )
        return 2

    try:
        api = MercadoPublicoAPI(ticket)
        ofertas = recolectar(api, solo_productos=args.solo_productos, log=lambda msg: print(msg, flush=True))
    except MercadoPublicoError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    fecha = chile_today().isoformat()
    paths = write_reports(ofertas, Path(args.salida), fecha)
    visibles = [o for o in ofertas if o.categoria != "descartada"]
    print(f"\n{len(visibles)} ofertas para revisar. Reportes:")
    for label, path in paths.items():
        print(f"  {label}: {path}")

    for oferta in visibles[:15]:
        monto = f"${oferta.monto:,.0f}" if oferta.monto is not None else "s/monto"
        print(
            f"[{oferta.categoria:10} {oferta.puntaje:3}] {oferta.codigo}  "
            f"{oferta.nombre[:70]}  {monto}  cierra {oferta.fecha_cierre}"
        )

    if args.email:
        try:
            enviar_email(
                render_html(ofertas),
                args.email,
                args.smtp_host,
                args.smtp_port,
                args.smtp_user,
                args.smtp_password,
                fecha,
            )
            print(f"Correo enviado a {args.email}")
        except Exception as exc:  # noqa: BLE001
            print(f"No se pudo enviar el correo: {exc}", file=sys.stderr)
            return 1
    return 0
