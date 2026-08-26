import unittest

from src.rut import calcular_dv, generar_ruts, main, parsear_rut, validar_rut


class TestCalcularDv(unittest.TestCase):
    def test_ruts_conocidos(self):
        conocidos = {
            11111111: "1",
            22222222: "2",
            12345678: "5",
            1000000: "9",
            99999999: "9",
        }
        for cuerpo, dv in conocidos.items():
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(calcular_dv(cuerpo), dv)

    def test_digito_k(self):
        self.assertEqual(calcular_dv(1000005), "K")
        self.assertTrue(validar_rut("1.000.005-K"))
        self.assertTrue(validar_rut("1000005-k"))

    def test_digito_cero(self):
        self.assertEqual(calcular_dv(1000013), "0")
        self.assertTrue(validar_rut("1.000.013-0"))

    def test_rechaza_cuerpo_invalido(self):
        with self.assertRaises(ValueError):
            calcular_dv("abc")
        with self.assertRaises(ValueError):
            calcular_dv(0)
        with self.assertRaises(ValueError):
            calcular_dv(-12)


class TestValidarYParsear(unittest.TestCase):
    def test_acepta_formatos(self):
        variantes = [
            "11.111.111-1",
            "11111111-1",
            "111111111",
            " 11.111.111-1 ",
        ]
        for valor in variantes:
            with self.subTest(valor=valor):
                self.assertTrue(validar_rut(valor))

    def test_rechaza_dv_incorrecto(self):
        self.assertFalse(validar_rut("11.111.111-2"))
        self.assertFalse(validar_rut("12345678-K"))
        self.assertFalse(validar_rut(""))
        self.assertFalse(validar_rut("K"))

    def test_parsear(self):
        rut = parsear_rut("12.345.678-5")
        self.assertEqual(rut.cuerpo, 12345678)
        self.assertEqual(rut.dv, "5")
        self.assertEqual(rut.formateado(), "12.345.678-5")
        self.assertEqual(rut.simple(), "12345678-5")


class TestGenerar(unittest.TestCase):
    def test_generados_cumplen_algoritmo(self):
        for tipo in ("persona", "empresa", "cualquiera"):
            ruts = generar_ruts(cantidad=50, tipo=tipo)
            self.assertEqual(len(ruts), 50)
            for rut in ruts:
                self.assertTrue(validar_rut(str(rut)))
                self.assertEqual(calcular_dv(rut.cuerpo), rut.dv)

    def test_rangos(self):
        personas = generar_ruts(cantidad=20, tipo="persona")
        empresas = generar_ruts(cantidad=20, tipo="empresa")
        self.assertTrue(all(1_000_000 <= r.cuerpo <= 27_000_000 for r in personas))
        self.assertTrue(all(50_000_000 <= r.cuerpo <= 99_999_999 for r in empresas))

    def test_cantidad_invalida(self):
        with self.assertRaises(ValueError):
            generar_ruts(cantidad=0)


class TestCli(unittest.TestCase):
    def test_validar_exit_codes(self):
        import io
        from contextlib import redirect_stdout

        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--validar", "11.111.111-1"]), 0)
            self.assertEqual(main(["--validar", "11.111.111-2"]), 1)

    def test_generar_imprime_ruts(self):
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            codigo = main(["-n", "3", "--simple"])
        lineas = [linea for linea in buffer.getvalue().splitlines() if linea]
        self.assertEqual(codigo, 0)
        self.assertEqual(len(lineas), 3)
        self.assertTrue(all(validar_rut(linea) for linea in lineas))


if __name__ == "__main__":
    unittest.main()
