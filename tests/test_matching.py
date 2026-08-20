"""Pruebas del puntaje de café para CRL Coffee."""

from __future__ import annotations

import unittest

from crl_ofertas.matching import (
    filtrar_resumenes_licitacion,
    oferta_desde_compra_agil,
    parece_cafe,
)


class PareceCafeTests(unittest.TestCase):
    def test_acepta_cafe_y_cafeteria(self) -> None:
        self.assertTrue(parece_cafe("COMPRA DE CAFÉ Y ACCESORIOS DE MESA"))
        self.assertTrue(parece_cafe("INSUMOS DE CAFETERIA Y BODEGA"))
        self.assertTrue(parece_cafe("Servicio de Coffe Break CRM"))

    def test_rechaza_falsos_positivos(self) -> None:
        self.assertFalse(parece_cafe("MATERIALES MEJORAMIENTO DE PARED"))
        self.assertFalse(
            parece_cafe(
                "SERVICIOS MEDICOS DE CIRUGIA ESPECIALIDAD TRAUMATOLOGÍA DE CADERA"
            )
        )
        self.assertFalse(parece_cafe("ADQUISICIÓN DE INSUMOS DENTALES"))


class PuntajeTests(unittest.TestCase):
    def test_cafe_especialidad_en_grano_es_excelente(self) -> None:
        oferta = oferta_desde_compra_agil(
            {"codigo": "635-450-COT26", "nombre": "CAFÉ Y CAFETERA"},
            {
                "codigo": "635-450-COT26",
                "nombre": "COTIZACION DE MOLEDOR ELECTRICO, CAFÉ Y CAFETERA",
                "descripcion": "1 kilo de café de especialidad de granos y 1 cafetera",
                "estado": {"glosa": "Publicada", "codigo": "publicada"},
                "institucion": {
                    "organismo_comprador": "SERVICIO DE SALUD DE ARICA",
                    "nombre_region": "Arica y Parinacota",
                },
                "fechas": {"fecha_cierre": "2026-08-21 01:13"},
                "presupuesto": {"monto_disponible_clp": 212940, "moneda": "CLP"},
                "productos_solicitados": [
                    {
                        "codigo_producto": "50201706",
                        "nombre": "Café",
                        "descripcion": "1 KILO DE CAFÉ DE ESPECIALIDAD DE GRANOS SELECTOS, TOSTADOS A LA PERFECCIÓN",
                        "cantidad": 1,
                        "unidad_medida": "KG",
                    }
                ],
            },
        )
        self.assertGreaterEqual(oferta.puntaje, 70)
        self.assertEqual(oferta.categoria, "excelente")
        self.assertTrue(oferta.encaja_producto)

    def test_grano_arabica_con_maquina_es_excelente_o_buena(self) -> None:
        oferta = oferta_desde_compra_agil(
            {"codigo": "530885-30-COT26", "nombre": "Café con Maquina Dispensadora"},
            {
                "codigo": "530885-30-COT26",
                "nombre": "Café con Maquina Dispensadora de Café en comodato",
                "descripcion": "10 kilos de café 100% grano arabico caturra o catuaí",
                "estado": {"codigo": "publicada", "glosa": "Publicada"},
                "productos_solicitados": [
                    {
                        "codigo_producto": "50201706",
                        "nombre": "Café",
                        "descripcion": "10 kilos de café 100% grano arabico",
                        "cantidad": 10,
                        "unidad_medida": "KGM",
                    }
                ],
            },
        )
        self.assertIn(oferta.categoria, {"excelente", "buena"})
        self.assertTrue(oferta.encaja_producto)

    def test_nescafe_es_regular(self) -> None:
        oferta = oferta_desde_compra_agil(
            {"codigo": "1976-93-COT26", "nombre": "TARROS DE CAFE Y VASOS DESECHABLES"},
            {
                "codigo": "1976-93-COT26",
                "nombre": "TARROS DE CAFE Y VASOS DESECHABLES",
                "descripcion": "tarros de café similar a Nescafé 400 gr",
                "estado": {"codigo": "publicada", "glosa": "Publicada"},
                "productos_solicitados": [
                    {
                        "codigo_producto": "50201709",
                        "nombre": "Café instantáneo",
                        "descripcion": "TARRO DE CAFÉ SIMILAR A NESCAFE 400 GR",
                        "cantidad": 10,
                        "unidad_medida": "EA",
                    }
                ],
            },
        )
        self.assertEqual(oferta.categoria, "regular")
        self.assertFalse(oferta.encaja_producto)

    def test_coffee_break_es_servicio(self) -> None:
        oferta = oferta_desde_compra_agil(
            {"codigo": "x", "nombre": "SERVICIO COFFE BREAK ESTUDIANTES"},
            {
                "codigo": "1058758-155-COT26",
                "nombre": "SERVICIO COFFE BREAK ESTUDIANTES POSTGRADOS MBA ARICA",
                "descripcion": "Servicio de Coffe Break para 13 personas",
                "estado": {"codigo": "publicada", "glosa": "Publicada"},
                "productos_solicitados": [
                    {
                        "codigo_producto": "90111603",
                        "nombre": "Salas de reuniones o banquetes",
                        "descripcion": "Servicio de Coffe Break",
                    }
                ],
            },
        )
        self.assertEqual(oferta.categoria, "servicio")

    def test_concesion_se_descarta(self) -> None:
        oferta = oferta_desde_compra_agil(
            {
                "codigo": "1",
                "nombre": "Concesión de Cafetería para El Hospital San José",
                "estado": {"codigo": "publicada", "glosa": "Publicada"},
            }
        )
        self.assertEqual(oferta.categoria, "descartada")

    def test_filtra_licitaciones_de_cafeteria_y_no_especialidad_medica(self) -> None:
        rows = [
            {"CodigoExterno": "a", "Nombre": "INSUMOS DE CAFETERIA PARA HOSPITAL"},
            {"CodigoExterno": "b", "Nombre": "Concesión de Cafetería para El Hospital"},
            {"CodigoExterno": "c", "Nombre": "SERVICIOS MEDICOS ESPECIALIDAD TRAUMATOLOGÍA"},
        ]
        filtradas = filtrar_resumenes_licitacion(rows)
        self.assertEqual([r["CodigoExterno"] for r in filtradas], ["a"])


if __name__ == "__main__":
    unittest.main()
