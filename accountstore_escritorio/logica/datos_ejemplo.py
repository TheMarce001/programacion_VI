"""Datos de ejemplo que se cargan la PRIMERA vez que se abre el sistema
(cuando la base todavía no tiene usuarios). Los clientes son ficticios.

Las fechas se calculan a partir de hoy, para que siempre haya suscripciones
en todos los estados: ACTIVO, A VENCER, VENCIDO y BAJA.
"""
from datetime import date, timedelta

from logica import reglas, seguridad

USUARIOS = [
    # usuario, nombre, rol, contraseña inicial
    ("admin", "Marcelo Benitez", "ADMIN", "Admin2026!"),
    ("supervisor", "Usuario Supervisor", "SUPERVISOR", "Super2026!"),
    ("cobranza", "Usuario Cobranza", "COBRANZA", "Cobra2026!"),
]

SERVICIOS = [
    # nombre, perfiles por cuenta, precio por perfil y mes (Gs., de ejemplo)
    ("Netflix", 5, 30000),
    ("Disney+", 6, 25000),
    ("HBO Max", 5, 25000),
    ("Crunchyroll", 5, 20000),
    ("Paramount+", 4, 20000),
    ("Spotify", 6, 25000),
]

CUENTAS = [
    ("Netflix", "netflix01@example.com"),
    ("Netflix", "netflix02@example.com"),
    ("Disney+", "disney01@example.com"),
    ("HBO Max", "hbomax01@example.com"),
    ("Crunchyroll", "crunchyroll01@example.com"),
    ("Paramount+", "paramount01@example.com"),
    ("Spotify", "spotify01@example.com"),
]

CLIENTES = [
    ("Ana Gómez", "0981111222", "ana.gomez@example.com"),
    ("Luis Martínez", "0982333444", None),
    ("Carmen Ortiz", "0971555666", None),
    ("Diego Ramírez", "0991777888", "diego.ramirez@example.com"),
    ("Sofía Acosta", "0961999000", None),
    ("Rosa Cáceres", "0983246810", None),
    ("Jorge Villalba", "0985123456", None),
]

VENTAS = [
    # cliente, cuenta, perfiles, meses, días que faltan para vencer, ¿dada de baja?
    ("Ana Gómez", "netflix01@example.com", 2, 1, 12, False),
    ("Luis Martínez", "netflix01@example.com", 3, 1, 2, False),     # netflix01 queda LLENA (5/5)
    ("Carmen Ortiz", "disney01@example.com", 1, 3, 40, False),
    ("Diego Ramírez", "hbomax01@example.com", 1, 1, -5, False),     # vencida hace 5 días
    ("Sofía Acosta", "crunchyroll01@example.com", 2, 1, 1, False),
    ("Rosa Cáceres", "paramount01@example.com", 1, 1, -20, True),   # dada de baja
]


def cargar_si_esta_vacia(repo, hoy=None):
    """Carga los datos de ejemplo solo si no hay usuarios. Devuelve True si cargó."""
    if repo.contar_usuarios() > 0:
        return False
    hoy = hoy or date.today()

    ids_usuarios = {}
    for usuario, nombre, rol, clave in USUARIOS:
        clave_hash, clave_sal = seguridad.generar_hash(clave)
        ids_usuarios[usuario] = repo.insertar_usuario(usuario, nombre, rol, clave_hash, clave_sal)

    ids_servicios, precios = {}, {}
    for nombre, capacidad, precio in SERVICIOS:
        ids_servicios[nombre] = repo.insertar_servicio(nombre, capacidad, precio)
        precios[nombre] = precio

    ids_cuentas, precio_cuenta = {}, {}
    for servicio, correo in CUENTAS:
        ids_cuentas[correo] = repo.insertar_cuenta(ids_servicios[servicio], correo)
        precio_cuenta[correo] = precios[servicio]

    ids_clientes = {}
    for nombre, telefono, correo in CLIENTES:
        ids_clientes[nombre] = repo.insertar_cliente(nombre, telefono, correo)

    for cliente, cuenta, perfiles, meses, faltan, baja in VENTAS:
        inicio = reglas.sumar_meses(hoy + timedelta(days=faltan), -meses)
        vencimiento = reglas.sumar_meses(inicio, meses)
        monto = reglas.calcular_monto(precio_cuenta[cuenta], perfiles, meses)
        suscripcion_id = repo.insertar_venta(
            ids_clientes[cliente], ids_cuentas[cuenta], perfiles, inicio.isoformat(),
            vencimiento.isoformat(), ids_usuarios["admin"], meses, monto)
        if baja:
            repo.dar_de_baja(suscripcion_id, (vencimiento + timedelta(days=2)).isoformat())
    return True
