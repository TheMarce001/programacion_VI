"""Pruebas de las reglas de negocio y de la seguridad.   python -m unittest -v"""
import unittest
from datetime import date

from logica import reglas, seguridad
from logica.errores import ErrorValidacion


class PruebasFechas(unittest.TestCase):
    def test_sumar_un_mes(self):
        self.assertEqual(reglas.sumar_meses(date(2026, 1, 15), 1), date(2026, 2, 15))

    def test_fin_de_mes_usa_el_ultimo_dia(self):
        self.assertEqual(reglas.sumar_meses(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(reglas.sumar_meses(date(2028, 1, 31), 1), date(2028, 2, 29))  # bisiesto

    def test_cambio_de_anio(self):
        self.assertEqual(reglas.sumar_meses(date(2026, 11, 10), 3), date(2027, 2, 10))

    def test_restar_meses(self):
        self.assertEqual(reglas.sumar_meses(date(2026, 3, 31), -1), date(2026, 2, 28))

    def test_fecha_invalida(self):
        for texto in ("31/02/2026", "2026-11-12", "hoy", ""):
            with self.assertRaises(ErrorValidacion):
                reglas.convertir_fecha(texto)

    def test_estado_por_dias(self):
        self.assertEqual(reglas.estado_por_dias(4), "ACTIVO")
        self.assertEqual(reglas.estado_por_dias(3), "A VENCER")
        self.assertEqual(reglas.estado_por_dias(1), "A VENCER")
        self.assertEqual(reglas.estado_por_dias(0), "VENCIDO")
        self.assertEqual(reglas.estado_por_dias(-10), "VENCIDO")

    def test_renovacion_no_pierde_dias(self):
        hoy = date(2026, 11, 12)
        self.assertEqual(reglas.inicio_renovacion(date(2026, 11, 20), hoy), date(2026, 11, 20))
        self.assertEqual(reglas.inicio_renovacion(date(2026, 11, 1), hoy), hoy)


class PruebasMontosYCupos(unittest.TestCase):
    def test_monto(self):
        self.assertEqual(reglas.calcular_monto(30000, 2, 3), 180000)

    def test_cupo_suficiente(self):
        reglas.validar_cupo(5, 3, 2, "cuenta")      # no lanza error

    def test_cupo_insuficiente(self):
        with self.assertRaises(ErrorValidacion):
            reglas.validar_cupo(5, 3, 3, "cuenta")
        with self.assertRaises(ErrorValidacion):
            reglas.validar_cupo(5, 5, 1, "cuenta")


class PruebasValidaciones(unittest.TestCase):
    def test_telefono_se_normaliza(self):
        for texto in ("0981 123 456", "0981-123-456", "+595 981 123456", "595981123456"):
            self.assertEqual(reglas.normalizar_telefono(texto), "0981123456")

    def test_telefono_invalido(self):
        for texto in ("123", "0981abc456", "", "02112345678"):
            with self.assertRaises(ErrorValidacion):
                reglas.normalizar_telefono(texto)

    def test_entero(self):
        self.assertEqual(reglas.validar_entero(" 3 ", "Meses", 1, 12), 3)
        for texto in ("0", "13", "-1", "dos", "1.5", ""):
            with self.assertRaises(ErrorValidacion):
                reglas.validar_entero(texto, "Meses", 1, 12)

    def test_nombre(self):
        self.assertEqual(reglas.validar_nombre("  Ana   Gómez "), "Ana Gómez")
        for texto in ("Al", "Ana 2"):
            with self.assertRaises(ErrorValidacion):
                reglas.validar_nombre(texto)

    def test_clave_nueva(self):
        reglas.validar_clave_nueva("Clave2026", "Clave2026")
        for clave, repetida in (("corta1", "corta1"), ("sinnumeros", "sinnumeros"),
                                ("Clave2026", "Otra2026")):
            with self.assertRaises(ErrorValidacion):
                reglas.validar_clave_nueva(clave, repetida)


class PruebasSeguridad(unittest.TestCase):
    def test_hash_no_es_la_clave_y_se_verifica(self):
        clave_hash, sal = seguridad.generar_hash("Admin2026!")
        self.assertNotIn("Admin2026!", clave_hash)
        self.assertTrue(seguridad.verificar_clave("Admin2026!", clave_hash, sal))
        self.assertFalse(seguridad.verificar_clave("admin2026!", clave_hash, sal))

    def test_misma_clave_distinta_sal_distinto_hash(self):
        hash1, sal1 = seguridad.generar_hash("Admin2026!")
        hash2, sal2 = seguridad.generar_hash("Admin2026!")
        self.assertNotEqual(sal1, sal2)
        self.assertNotEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
