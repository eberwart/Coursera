"""Pruebas del reporte HTML."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crl_ofertas.matching import Oferta
from crl_ofertas.report import render_html, write_reports


class ReportTests(unittest.TestCase):
    def test_html_incluye_oferta_excelente(self) -> None:
        oferta = Oferta(
            fuente="compra_agil",
            codigo="635-450-COT26",
            nombre="Café de especialidad en grano",
            estado="Publicada",
            organismo="Hospital",
            puntaje=90,
            categoria="excelente",
            razones=["Pide café en grano o de especialidad"],
            url="https://www.mercadopublico.cl/Home/Search?k=635-450-COT26",
        )
        page = render_html([oferta])
        self.assertIn("635-450-COT26", page)
        self.assertIn("excelente", page.lower())
        self.assertIn("CRL Coffee", page)

    def test_escribe_archivos_del_dia(self) -> None:
        oferta = Oferta(
            fuente="licitacion",
            codigo="1-1-LE26",
            nombre="Compra de café",
            estado="Publicada",
            categoria="buena",
            puntaje=50,
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reports([oferta], Path(tmp), "2026-08-20")
            self.assertTrue(paths["html"].exists())
            self.assertTrue(paths["csv"].exists())
            self.assertIn("1-1-LE26", paths["json"].read_text(encoding="utf-8"))
            self.assertTrue((Path(tmp) / "ofertas-hoy.html").exists())


if __name__ == "__main__":
    unittest.main()
