"""Pruebas de que cada campo rechaza datos inválidos y acepta los válidos.   python -m unittest -v"""
import os
import sqlite3
import tempfile
import unittest
from datetime import date

from datos.conexion import BaseIncompatible, conectar, inicializar
from datos.repositorio import Repositorio
from logica import reglas, seguridad
from logica.datos_ejemplo import cargar_si_esta_vacia
from logica.errores import ErrorValidacion
from logica.gestor import Gestor

HOY = date(2026, 11, 12)


class PruebasCampos(unittest.TestCase):
    def rechaza(self, funcion, *valores):
        for valor in valores:
            with self.subTest(valor=valor), self.assertRaises(ErrorValidacion):
                funcion(valor)

    def test_nombres(self):
        self.rechaza(reglas.validar_nombre, "", "Al", "123", "!!!", "@@@ ###", "Ana 2", "<script>", "A" * 61)
        for valido in ("María José Ñañez", "John O'Neil-Smith", "Ana"):
            self.assertEqual(reglas.validar_nombre(valido), valido)

    def test_correos(self):
        self.rechaza(reglas.validar_correo, "sinarroba", "ana@", "@gmail.com", "ana@gmail", "ana@@gmail.com",
                     "ana@gmail..com", "ana gomez@gmail.com", "ana@gmail.c", "ana@.com", "ana@-gmail.com")
        for valido in ("ana@gmail.com", "carla.ruiz+ventas@empresa.com.py", "Ana@Gmail.COM"):
            self.assertEqual(reglas.validar_correo(valido), valido.lower())
        self.assertIsNone(reglas.validar_correo(""))            # el correo del cliente es opcional

    def test_usuarios(self):
        self.rechaza(reglas.validar_usuario, "", "ab", "...", "___", "123", "con espacio", "ñandu", "a" * 21)
        self.assertEqual(reglas.validar_usuario(" Maria.Lopez "), "maria.lopez")

    def test_nombre_de_servicio(self):
        self.rechaza(reglas.validar_nombre_servicio, "", "N", "123", "!!!", "X" * 31)
        for valido in ("Office 365", "Disney+", "HBO Max"):
            self.assertEqual(reglas.validar_nombre_servicio(valido), valido)

    def test_contrasena_muy_larga(self):
        with self.assertRaises(ErrorValidacion):
            reglas.validar_clave_nueva("x1" * 40, "x1" * 40)


class PruebasGestorValidaciones(unittest.TestCase):
    def setUp(self):
        seguridad.ITERACIONES = 1_000
        self.conexion = conectar(":memory:")
        inicializar(self.conexion)
        cargar_si_esta_vacia(Repositorio(self.conexion), hoy=HOY)
        self.gestor = Gestor(Repositorio(self.conexion))
        self.gestor.iniciar_sesion("admin", "Admin2026!")

    def tearDown(self):
        self.conexion.close()
        seguridad.ITERACIONES = 600_000

    def test_venta_con_fecha_de_hace_mas_de_un_anio(self):
        cuenta = next(c for c in self.gestor.listar_cuentas() if c["correo"] == "netflix02@example.com")["id"]
        cliente = self.gestor.listar_clientes("Jorge")[0]["id"]
        for fecha in ("01/01/1900", "01/11/2025"):
            with self.subTest(fecha=fecha), self.assertRaises(ErrorValidacion):
                self.gestor.registrar_venta(cliente, cuenta, "1", "1", fecha, hoy=HOY)
        self.gestor.registrar_venta(cliente, cuenta, "1", "1", "01/12/2025", hoy=HOY)   # menos de un año

    def test_precio_fuera_de_rango(self):
        for precio in ("500", "999999999999"):
            with self.subTest(precio=precio), self.assertRaises(ErrorValidacion):
                self.gestor.registrar_servicio("Prime Video", "5", precio)

    def test_buscar_telefono_con_espacios(self):
        self.assertEqual([c["nombre"] for c in self.gestor.listar_clientes("0981 111-222")], ["Ana Gómez"])

    def test_busqueda_con_caracteres_raros_no_rompe(self):
        for texto in ("' OR 1=1 --", "; DROP TABLE clientes;", '"', "\\"):
            self.assertEqual(self.gestor.listar_clientes(texto), [])
        self.assertEqual(len(self.gestor.listar_clientes("")), 8)       # la tabla sigue intacta


class PruebaBaseVieja(unittest.TestCase):
    def test_base_de_version_anterior_avisa(self):
        carpeta = tempfile.mkdtemp()
        ruta = os.path.join(carpeta, "vieja.db")
        vieja = sqlite3.connect(ruta)                       # una base sin número de versión
        vieja.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY)")
        vieja.commit()
        vieja.close()
        conexion = conectar(ruta)
        with self.assertRaises(BaseIncompatible):
            inicializar(conexion)
        conexion.close()
        os.remove(ruta)
        os.rmdir(carpeta)


if __name__ == "__main__":
    unittest.main()
