"""CLI sin ticket debe explicar cómo obtenerlo."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from crl_ofertas.cli import main


class CliTests(unittest.TestCase):
    def test_sin_ticket_explica_clave_unica(self) -> None:
        with patch.dict(os.environ, {"MERCADO_PUBLICO_TICKET": "", "CHILE_PUBLIC_MARKET_TICKET": ""}):
            code = main([])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
