"""Roles y permisos (los mismos tres roles que usa AccountStore).

El control se hace AQUÍ, en la lógica, y no solo en la interfaz: aunque un
botón esté a la vista, la acción se rechaza si el rol no tiene el permiso.
"""
from logica.errores import PermisoDenegado

ROLES = {
    "ADMIN": "Administrador",
    "SUPERVISOR": "Supervisor",
    "COBRANZA": "Pagos y vencimientos",
}

# Acción -> cómo se describe en el mensaje de error
ACCIONES = {
    "registrar_venta": "registrar ventas",
    "renovar": "renovar suscripciones",
    "dar_de_baja": "dar de baja suscripciones",
    "gestionar_clientes": "registrar o editar clientes",
    "eliminar_cliente": "eliminar clientes",
    "gestionar_cuentas": "agregar o eliminar servicios y cuentas",
    "gestionar_usuarios": "crear o desbloquear usuarios",
}

PERMISOS = {
    "ADMIN": set(ACCIONES),      # el administrador puede hacer todo
    "SUPERVISOR": {"registrar_venta", "renovar", "dar_de_baja", "gestionar_clientes",
                   "eliminar_cliente", "gestionar_cuentas"},
    "COBRANZA": {"registrar_venta", "renovar", "gestionar_clientes"},
}


def tiene_permiso(rol, accion):
    return accion in PERMISOS.get(rol, set())


def exigir_permiso(usuario, accion):
    """Lanza PermisoDenegado si no hay sesión o si el rol no permite la acción."""
    if usuario is None:
        raise PermisoDenegado("Debe iniciar sesión para continuar.")
    if not tiene_permiso(usuario["rol"], accion):
        raise PermisoDenegado(
            f"Su rol «{ROLES[usuario['rol']]}» no tiene permiso para {ACCIONES[accion]}.")
