"""Reglas de negocio y validaciones de AccountStore.

Son funciones "puras": no usan Tkinter ni la base de datos, solo reciben
datos y devuelven un resultado (o lanzan ErrorValidacion). Por eso se
pueden probar fácilmente (ver pruebas/test_reglas.py).
"""
import calendar
import re
from datetime import date, datetime

from logica.errores import ErrorValidacion

DIAS_AVISO = 3          # con 3 días o menos para vencer, la suscripción está "A VENCER"
MESES_MAXIMOS = 12      # una venta o renovación es de 1 a 12 meses
FORMATO_FECHA = "%d/%m/%Y"
PATRON_CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}")


# ------------------------------------------------------------------ fechas
def convertir_fecha(texto):
    """Convierte 'dd/mm/aaaa' en una fecha. Rechaza fechas que no existen (31/02)."""
    texto = (texto or "").strip()
    try:
        return datetime.strptime(texto, FORMATO_FECHA).date()
    except ValueError:
        raise ErrorValidacion(
            f"La fecha «{texto}» no es válida. Use el formato dd/mm/aaaa, por ejemplo 15/11/2026."
        ) from None


def fecha_a_texto(fecha):
    return fecha.strftime(FORMATO_FECHA)


def sumar_meses(fecha, meses):
    """REGLA: el vencimiento es la fecha de inicio más los meses pagados,
    igual que FECHA.MES (EDATE) en la planilla. Si ese día no existe en el
    mes de destino se usa el último día del mes: 31/01 + 1 mes = 28/02."""
    indice = fecha.month - 1 + meses
    anio = fecha.year + indice // 12
    mes = indice % 12 + 1
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, min(fecha.day, ultimo_dia))


def dias_restantes(vencimiento, hoy):
    return (vencimiento - hoy).days


def estado_por_dias(dias):
    """REGLA (la misma de la planilla de AccountStore):
    más de 3 días -> ACTIVO, de 1 a 3 días -> A VENCER, 0 o menos -> VENCIDO."""
    if dias > DIAS_AVISO:
        return "ACTIVO"
    if dias >= 1:
        return "A VENCER"
    return "VENCIDO"


def inicio_renovacion(vencimiento_actual, hoy):
    """REGLA: si la suscripción todavía no venció, se renueva desde su
    vencimiento (el cliente no pierde días). Si ya venció, desde hoy."""
    if vencimiento_actual >= hoy:
        return vencimiento_actual
    return hoy


# ------------------------------------------------------- montos y cupos
def calcular_monto(precio_mensual, perfiles, meses):
    """REGLA: se cobra el precio mensual por cada perfil y por cada mes."""
    return precio_mensual * perfiles * meses


def validar_cupo(capacidad, ocupados, perfiles, cuenta):
    """REGLA PRINCIPAL: una cuenta no puede tener más perfiles vendidos que su
    capacidad (Netflix 5, Disney+ 6, ...). Evita la sobreventa."""
    libres = capacidad - ocupados
    if perfiles > libres:
        if libres <= 0:
            raise ErrorValidacion(
                f"La cuenta {cuenta} está llena ({ocupados} de {capacidad} perfiles ocupados). "
                "Elija otra cuenta.")
        raise ErrorValidacion(
            f"La cuenta {cuenta} solo tiene {libres} perfil(es) libre(s) "
            f"y se pidieron {perfiles}.")


# ----------------------------------------------------------- validaciones
def validar_entero(texto, campo, minimo, maximo=None):
    texto = str(texto).strip()
    if not texto.isdigit():
        raise ErrorValidacion(f"{campo} debe ser un número entero (sin letras ni signos).")
    valor = int(texto)
    if valor < minimo or (maximo is not None and valor > maximo):
        if maximo is None:
            raise ErrorValidacion(f"{campo} debe ser como mínimo {minimo}.")
        raise ErrorValidacion(f"{campo} debe estar entre {minimo} y {maximo}.")
    return valor


def validar_nombre(texto, campo="El nombre"):
    nombre = " ".join((texto or "").split())        # quita espacios de más
    if len(nombre) < 3:
        raise ErrorValidacion(f"{campo} debe tener al menos 3 letras.")
    if any(caracter.isdigit() for caracter in nombre):
        raise ErrorValidacion(f"{campo} no puede contener números.")
    return nombre


def normalizar_telefono(texto):
    """Acepta '0981 123 456', '0981-123-456' o '+595 981 123456' y siempre
    devuelve el mismo formato: '0981123456'. Así un número no se carga dos veces."""
    texto = (texto or "").strip()
    if re.search(r"[^\d\s\-+()]", texto):
        raise ErrorValidacion("El teléfono solo puede contener números, espacios o guiones.")
    digitos = re.sub(r"\D", "", texto)
    if digitos.startswith("595"):
        digitos = "0" + digitos[3:]
    if not re.fullmatch(r"09\d{8}", digitos):
        raise ErrorValidacion("El teléfono debe ser un celular de Paraguay, por ejemplo 0981 123 456.")
    return digitos


def validar_correo(texto, obligatorio=False):
    correo = (texto or "").strip().lower()
    if not correo:
        if obligatorio:
            raise ErrorValidacion("El correo es obligatorio.")
        return None
    if not PATRON_CORREO.fullmatch(correo):
        raise ErrorValidacion(f"El correo «{correo}» no es válido.")
    return correo


def validar_usuario(texto):
    usuario = (texto or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_.]{3,20}", usuario):
        raise ErrorValidacion(
            "El usuario debe tener de 3 a 20 caracteres: letras sin tilde, números, punto o guion bajo.")
    return usuario


def validar_clave_nueva(clave, confirmacion):
    if len(clave) < 8:
        raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Za-z]", clave) or not re.search(r"\d", clave):
        raise ErrorValidacion("La contraseña debe combinar letras y números.")
    if clave != confirmacion:
        raise ErrorValidacion("Las dos contraseñas no coinciden.")
