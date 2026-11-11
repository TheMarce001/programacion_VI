"""Pruebas del proceso completo (lógica + base de datos).   python -m unittest -v

Cada prueba usa una base en memoria nueva con los datos de ejemplo,
así no se toca accountstore.db.
"""
import os
import tempfile
import unittest
from datetime import date

from datos.conexion import conectar, inicializar
from datos.repositorio import Repositorio
from logica import seguridad
from logica.datos_ejemplo import cargar_si_esta_vacia
from logica.errores import ErrorValidacion, PermisoDenegado
from logica.gestor import Gestor

HOY = date(2026, 11, 12)


def setUpModule():
    # Menos iteraciones solo para que las pruebas sean rápidas (el sistema usa 600 000).
    seguridad.ITERACIONES = 1_000


def tearDownModule():
    seguridad.ITERACIONES = 600_000


class PruebasGestor(unittest.TestCase):
    def setUp(self):
        self.conexion = conectar(":memory:")
        inicializar(self.conexion)
        self.repo = Repositorio(self.conexion)
        cargar_si_esta_vacia(self.repo, hoy=HOY)
        self.gestor = Gestor(self.repo)

    def tearDown(self):
        self.conexion.close()

    def _contar(self, tabla):
        consultas = {"suscripciones": "SELECT COUNT(*) FROM suscripciones",
                     "pagos": "SELECT COUNT(*) FROM pagos",
                     "clientes": "SELECT COUNT(*) FROM clientes"}
        return self.conexion.execute(consultas[tabla]).fetchone()[0]

    def _cuenta(self, correo):
        return next(c for c in self.gestor.listar_cuentas() if c["correo"] == correo)

    def _cliente(self, nombre):
        return next(c for c in self.gestor.listar_clientes() if c["nombre"] == nombre)

    # ---------------------------------------------------------------- sesión
    def test_inicio_de_sesion(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        self.assertEqual(self.gestor.usuario["rol"], "ADMIN")
        self.gestor.cerrar_sesion()
        self.assertIsNone(self.gestor.usuario)

    def test_clave_incorrecta(self):
        with self.assertRaises(ErrorValidacion):
            self.gestor.iniciar_sesion("admin", "otra")
        with self.assertRaises(ErrorValidacion):
            self.gestor.iniciar_sesion("noexiste", "Admin2026!")
        self.assertIsNone(self.gestor.usuario)

    def test_sin_sesion_no_se_puede_operar(self):
        with self.assertRaises(PermisoDenegado):
            self.gestor.listar_suscripciones()

    # ------------------------------------------------------ proceso principal
    def test_venta_valida_se_guarda_y_se_recupera(self):
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!")
        antes = self._contar("pagos")
        cuenta = self._cuenta("netflix02@example.com")
        cliente = self._cliente("Jorge Villalba")
        venta = self.gestor.registrar_venta(cliente["id"], cuenta["id"], "2", "3", "12/11/2026", hoy=HOY)
        self.assertEqual(venta["vencimiento"], date(2027, 2, 12))
        self.assertEqual(venta["monto"], 30000 * 2 * 3)
        self.assertEqual(self._contar("pagos"), antes + 1)
        recuperada = [s for s in self.gestor.listar_suscripciones("Jorge", hoy=HOY)]
        self.assertEqual(len(recuperada), 1)
        self.assertEqual(recuperada[0]["situacion"], "ACTIVO")
        self.assertEqual(self._cuenta("netflix02@example.com")["libres"], 3)

    def test_venta_sobre_cuenta_llena_se_rechaza_sin_guardar(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        antes = self._contar("suscripciones")
        cuenta = self._cuenta("netflix01@example.com")          # 5 de 5 ocupados
        cliente = self._cliente("Jorge Villalba")
        with self.assertRaises(ErrorValidacion):
            self.gestor.registrar_venta(cliente["id"], cuenta["id"], "1", "1", "12/11/2026", hoy=HOY)
        self.assertEqual(self._contar("suscripciones"), antes)

    def test_datos_invalidos_se_rechazan_sin_guardar(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        antes = self._contar("suscripciones")
        cuenta = self._cuenta("netflix02@example.com")["id"]
        cliente = self._cliente("Jorge Villalba")["id"]
        for perfiles, meses, fecha in (("0", "1", "12/11/2026"), ("1", "13", "12/11/2026"),
                                       ("1", "uno", "12/11/2026"), ("1", "1", "31/02/2026"),
                                       ("1", "1", "20/11/2026")):           # fecha futura
            with self.assertRaises(ErrorValidacion):
                self.gestor.registrar_venta(cliente, cuenta, perfiles, meses, fecha, hoy=HOY)
        with self.assertRaises(ErrorValidacion):
            self.gestor.registrar_venta(9999, cuenta, "1", "1", "12/11/2026", hoy=HOY)  # FK
        self.assertEqual(self._contar("suscripciones"), antes)

    def test_resumen_cuenta_estados_y_cobrado_del_mes(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        resumen = self.gestor.resumen(hoy=HOY)
        self.assertEqual(resumen["cantidades"], {"ACTIVO": 2, "A VENCER": 2, "VENCIDO": 1, "BAJA": 1})
        cobrado_antes = resumen["cobrado_mes"]
        cuenta = self._cuenta("netflix02@example.com")["id"]
        cliente = self._cliente("Jorge Villalba")["id"]
        self.gestor.registrar_venta(cliente, cuenta, "1", "1", "12/11/2026", hoy=HOY)
        self.assertEqual(self.gestor.resumen(hoy=HOY)["cobrado_mes"], cobrado_antes + 30000)

    def test_renovar_vencida_cuenta_desde_hoy(self):
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!")
        diego = self.gestor.listar_suscripciones("Diego", hoy=HOY)[0]
        self.assertEqual(diego["situacion"], "VENCIDO")
        datos = self.gestor.renovar(diego["id"], "1", hoy=HOY)
        self.assertEqual(datos["vencimiento"], date(2026, 12, 12))

    def test_baja_libera_perfiles(self):
        self.gestor.iniciar_sesion("supervisor", "Super2026!")
        luis = self.gestor.listar_suscripciones("Luis", hoy=HOY)[0]
        self.gestor.dar_de_baja(luis["id"], hoy=HOY)
        self.assertEqual(self._cuenta("netflix01@example.com")["libres"], 3)

    # --------------------------------------------------------------- permisos
    def test_cobranza_no_puede_dar_de_baja(self):
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!")
        ana = self.gestor.listar_suscripciones("Ana", hoy=HOY)[0]
        with self.assertRaises(PermisoDenegado):
            self.gestor.dar_de_baja(ana["id"], hoy=HOY)
        self.assertEqual(self.gestor.listar_suscripciones("Ana", hoy=HOY)[0]["situacion"], "ACTIVO")

    def test_supervisor_no_puede_crear_usuarios(self):
        self.gestor.iniciar_sesion("supervisor", "Super2026!")
        with self.assertRaises(PermisoDenegado):
            self.gestor.registrar_usuario("nuevo", "Usuario Nuevo", "ADMIN", "Clave2026", "Clave2026")

    # ------------------------------------------------- restricciones de la base
    def test_cliente_extranjero(self):
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!")
        self.gestor.registrar_cliente("Lucía Pereira", "099 555 777", "", "Uruguay")
        self.assertEqual(self._cliente("Lucía Pereira")["telefono"], "+59899555777")

    def test_buscar_telefono_escrito_con_cero(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        encontrados = self.gestor.listar_clientes("0981111222")
        self.assertEqual([c["nombre"] for c in encontrados], ["Ana Gómez"])

    def test_telefono_repetido_lo_rechaza_la_base(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        antes = self._contar("clientes")
        with self.assertRaises(ErrorValidacion):
            self.gestor.registrar_cliente("Otra Persona", "0981 111 222", "")   # ya es de Ana
        self.assertEqual(self._contar("clientes"), antes)

    def test_cliente_con_suscripciones_no_se_elimina(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        with self.assertRaises(ErrorValidacion):
            self.gestor.eliminar_cliente(self._cliente("Ana Gómez")["id"])
        self.gestor.eliminar_cliente(self._cliente("Jorge Villalba")["id"])     # sin suscripciones

    def test_usuario_nuevo_se_guarda_con_hash(self):
        self.gestor.iniciar_sesion("admin", "Admin2026!")
        self.gestor.registrar_usuario("ventas1", "Vendedor Uno", "COBRANZA", "Ventas2026", "Ventas2026")
        fila = self.repo.buscar_usuario("ventas1")
        self.assertNotEqual(fila["clave_hash"], "Ventas2026")
        self.gestor.cerrar_sesion()
        self.gestor.iniciar_sesion("ventas1", "Ventas2026")


class PruebaPersistencia(unittest.TestCase):
    def test_los_datos_permanecen_al_cerrar_y_abrir(self):
        carpeta = tempfile.mkdtemp()
        ruta = os.path.join(carpeta, "prueba.db")
        conexion = conectar(ruta)
        inicializar(conexion)
        repo = Repositorio(conexion)
        cargar_si_esta_vacia(repo, hoy=HOY)
        gestor = Gestor(repo)
        gestor.iniciar_sesion("admin", "Admin2026!")
        gestor.registrar_cliente("Cliente Persistente", "0975000111", "")
        conexion.close()                                    # "se cierra el sistema"

        conexion = conectar(ruta)                           # "se vuelve a abrir"
        inicializar(conexion)                               # no borra nada
        gestor = Gestor(Repositorio(conexion))
        gestor.iniciar_sesion("admin", "Admin2026!")
        nombres = [c["nombre"] for c in gestor.listar_clientes("Persistente")]
        conexion.close()
        os.remove(ruta)
        os.rmdir(carpeta)
        self.assertEqual(nombres, ["Cliente Persistente"])


if __name__ == "__main__":
    unittest.main()
