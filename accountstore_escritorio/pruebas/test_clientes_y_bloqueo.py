"""Pruebas de la edición de clientes y del bloqueo tras intentos fallidos.   python -m unittest -v"""
import unittest
from datetime import date, datetime, timedelta

from datos.conexion import conectar, inicializar
from datos.repositorio import Repositorio
from logica import reglas, seguridad
from logica.datos_ejemplo import cargar_si_esta_vacia
from logica.errores import ErrorValidacion, PermisoDenegado
from logica.gestor import Gestor

AHORA = datetime(2026, 11, 12, 10, 0)


class Base(unittest.TestCase):
    def setUp(self):
        seguridad.ITERACIONES = 1_000
        self.conexion = conectar(":memory:")
        inicializar(self.conexion)
        self.repo = Repositorio(self.conexion)
        cargar_si_esta_vacia(self.repo, hoy=date(2026, 11, 12))
        self.gestor = Gestor(self.repo)

    def tearDown(self):
        self.conexion.close()
        seguridad.ITERACIONES = 600_000

    def fallar(self, usuario, veces, ahora=AHORA):
        for _ in range(veces):
            with self.assertRaises(ErrorValidacion):
                self.gestor.iniciar_sesion(usuario, "incorrecta", ahora=ahora)


class PruebasBloqueo(Base):
    def test_tres_intentos_bloquean_cinco_minutos(self):
        self.fallar("supervisor", 2)
        with self.assertRaisesRegex(ErrorValidacion, "bloqueado"):
            self.gestor.iniciar_sesion("supervisor", "incorrecta", ahora=AHORA)
        # Aunque ahora escriba bien la contraseña, sigue bloqueado
        with self.assertRaisesRegex(ErrorValidacion, "bloqueado"):
            self.gestor.iniciar_sesion("supervisor", "Super2026!", ahora=AHORA + timedelta(minutes=1))
        # Pasados los 5 minutos puede entrar
        self.gestor.iniciar_sesion("supervisor", "Super2026!", ahora=AHORA + timedelta(minutes=6))

    def test_entrar_bien_reinicia_el_contador(self):
        self.fallar("cobranza", 2)
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!", ahora=AHORA)
        self.fallar("cobranza", 2)
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!", ahora=AHORA)    # no quedó bloqueado

    def test_usuario_inexistente_no_rompe(self):
        self.fallar("noexiste", 5)

    def test_el_bloqueo_se_guarda_en_la_base(self):
        self.fallar("supervisor", 3)
        otro_gestor = Gestor(Repositorio(self.conexion))       # como si se reabriera el programa
        with self.assertRaisesRegex(ErrorValidacion, "bloqueado"):
            otro_gestor.iniciar_sesion("supervisor", "Super2026!", ahora=AHORA)

    def test_el_administrador_desbloquea(self):
        self.fallar("supervisor", 3)
        self.gestor.iniciar_sesion("admin", "Admin2026!", ahora=AHORA)
        estado = {u["usuario"]: u["estado_texto"] for u in self.gestor.listar_usuarios(ahora=AHORA)}
        self.assertTrue(estado["supervisor"].startswith("Bloqueado"))
        supervisor = self.repo.buscar_usuario("supervisor")["id"]
        self.gestor.desbloquear_usuario(supervisor)
        self.gestor.iniciar_sesion("supervisor", "Super2026!", ahora=AHORA)

    def test_solo_el_administrador_desbloquea(self):
        self.gestor.iniciar_sesion("supervisor", "Super2026!", ahora=AHORA)
        with self.assertRaises(PermisoDenegado):
            self.gestor.desbloquear_usuario(self.repo.buscar_usuario("cobranza")["id"])


class PruebasEditarCliente(Base):
    def setUp(self):
        super().setUp()
        self.gestor.iniciar_sesion("cobranza", "Cobra2026!", ahora=AHORA)
        self.ana = self.gestor.listar_clientes("Ana Gómez")[0]["id"]

    def test_separar_telefono(self):
        casos = {"+595981111222": ("Paraguay", "981111222"), "+5491123456789": ("Argentina", "91123456789"),
                 "+59899555777": ("Uruguay", "99555777"), "+59171234567": ("Bolivia", "71234567"),
                 "+15551234567": ("Estados Unidos", "5551234567")}
        for telefono, esperado in casos.items():
            self.assertEqual(reglas.separar_telefono(telefono), esperado)

    def test_editar_cliente(self):
        cliente = self.gestor.obtener_cliente(self.ana)
        self.assertEqual((cliente["pais"], cliente["numero"]), ("Paraguay", "981111222"))
        self.gestor.actualizar_cliente(self.ana, "Ana María Gómez", "11 2345-6789", "ana.maria@gmail.com",
                                       "Argentina")
        cliente = self.gestor.obtener_cliente(self.ana)
        self.assertEqual((cliente["nombre"], cliente["telefono"], cliente["correo"]),
                         ("Ana María Gómez", "+541123456789", "ana.maria@gmail.com"))

    def test_guardar_sin_cambios_no_choca_consigo_mismo(self):
        c = self.gestor.obtener_cliente(self.ana)
        self.gestor.actualizar_cliente(self.ana, c["nombre"], c["numero"], c["correo"], c["pais"])

    def test_editar_con_datos_invalidos_no_cambia_nada(self):
        antes = self.gestor.obtener_cliente(self.ana)
        for nombre, telefono, correo in (("123", "0981111222", ""), ("Ana Gómez", "abc", ""),
                                         ("Ana Gómez", "0981111222", "sinarroba"),
                                         ("Ana Gómez", "0982 333 444", "")):     # teléfono de Luis
            with self.subTest(nombre=nombre, telefono=telefono, correo=correo):
                with self.assertRaises(ErrorValidacion):
                    self.gestor.actualizar_cliente(self.ana, nombre, telefono, correo)
        self.assertEqual(self.gestor.obtener_cliente(self.ana), antes)

    def test_editar_cliente_inexistente(self):
        with self.assertRaises(ErrorValidacion):
            self.gestor.actualizar_cliente(9999, "Nadie Nadie", "0981 000 001", "")


if __name__ == "__main__":
    unittest.main()
