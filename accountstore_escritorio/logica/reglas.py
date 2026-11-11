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
# usuario@dominio.ext : letras, números y . _ % + - antes de la @; el dominio por partes separadas por
# un solo punto (no admite "..") y una terminación de al menos 2 letras (.com, .py, .com.py)
PATRON_CORREO = re.compile(r"[a-z0-9._%+-]+@[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}")
LARGO_MAXIMO = {"nombre": 60, "correo": 100, "servicio": 30, "clave": 64}
DIAS_ATRAS_MAXIMO = 366       # una venta puede registrarse con fecha de inicio de hasta un año atrás
MAX_INTENTOS = 3              # intentos fallidos seguidos antes de bloquear al usuario
MINUTOS_BLOQUEO = 5           # minutos que dura el bloqueo


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


TIPOS_DESCUENTO = ("Gs.", "%")


def calcular_descuento(subtotal, valor, tipo="Gs."):
    """REGLA: el descuento puede ser un monto en Gs. o un porcentaje, como en la
    app de ventas. No puede ser negativo, el porcentaje no pasa de 100 y el
    total a cobrar tiene que quedar mayor a cero. Devuelve los Gs. a descontar."""
    texto = str(valor or "").strip()
    if texto in ("", "0"):
        return 0
    if tipo == "%":
        porcentaje = validar_entero(texto, "El porcentaje de descuento", 0, 100)
        descuento = round(subtotal * porcentaje / 100)
    elif tipo == "Gs.":
        descuento = validar_entero(texto.replace(".", ""), "El descuento", 0)
    else:
        raise ErrorValidacion("Elija si el descuento es en Gs. o en %.")
    if descuento >= subtotal:
        total = f"Gs. {subtotal:,}".replace(",", ".")
        raise ErrorValidacion(f"El descuento no puede ser igual o mayor que el total ({total}).")
    return descuento


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
def _miles(numero):
    return f"{numero:,}".replace(",", ".")


def validar_entero(texto, campo, minimo, maximo=None):
    texto = str(texto).strip()
    if not texto.isdigit():
        raise ErrorValidacion(f"{campo} debe ser un número entero (sin letras ni signos).")
    valor = int(texto)
    if valor < minimo or (maximo is not None and valor > maximo):
        if maximo is None:
            raise ErrorValidacion(f"{campo} debe ser como mínimo {_miles(minimo)}.")
        raise ErrorValidacion(f"{campo} debe estar entre {_miles(minimo)} y {_miles(maximo)}.")
    return valor


def validar_nombre(texto, campo="El nombre"):
    """Nombre de persona: solo letras (con tildes y ñ), espacios, apóstrofo, punto o guion."""
    nombre = " ".join((texto or "").split())        # quita espacios de más
    if any(caracter.isdigit() for caracter in nombre):
        raise ErrorValidacion(f"{campo} no puede contener números.")
    if any(not (c.isalpha() or c in " '.-") for c in nombre):
        raise ErrorValidacion(f"{campo} solo puede tener letras y espacios.")
    if sum(c.isalpha() for c in nombre) < 3:
        raise ErrorValidacion(f"{campo} debe tener al menos 3 letras.")
    if len(nombre) > LARGO_MAXIMO["nombre"]:
        raise ErrorValidacion(f"{campo} no puede tener más de {LARGO_MAXIMO['nombre']} caracteres.")
    return nombre


def validar_nombre_servicio(texto):
    """Nombre de servicio: letras, números y + . & - (ej. "Disney+", "Office 365"), con al menos una letra."""
    nombre = " ".join((texto or "").split())
    if len(nombre) < 2:
        raise ErrorValidacion("Escriba el nombre del servicio (al menos 2 caracteres).")
    if not any(c.isalpha() for c in nombre) or any(not (c.isalnum() or c in " +.&-") for c in nombre):
        raise ErrorValidacion("El nombre del servicio debe tener letras y solo puede usar números y + . & -")
    if len(nombre) > LARGO_MAXIMO["servicio"]:
        raise ErrorValidacion(f"El nombre del servicio no puede tener más de {LARGO_MAXIMO['servicio']} caracteres.")
    return nombre


# País -> (código internacional, mínimo y máximo de dígitos del número SIN el código ni el 0 inicial).
# Mismo orden que los países principales de la app de ventas de AccountStore PY.
PAISES = {
    "Paraguay": ("595", 9, 9),
    "Argentina": ("54", 10, 11),
    "Brasil": ("55", 10, 11),
    "Bolivia": ("591", 8, 8),
    "Chile": ("56", 9, 9),
    "Uruguay": ("598", 8, 8),
    "Perú": ("51", 9, 9),
    "Colombia": ("57", 10, 10),
    "Ecuador": ("593", 9, 9),
    "Venezuela": ("58", 10, 10),
    "México": ("52", 10, 10),
    "Estados Unidos": ("1", 10, 10),
    "España": ("34", 9, 9),
}
PAIS_POR_DEFECTO = "Paraguay"


def normalizar_telefono(texto, pais=PAIS_POR_DEFECTO):
    """REGLA: el teléfono se guarda en formato internacional, con el código del
    país: '0981 123 456' (Paraguay) -> '+595981123456'. Así sirve para WhatsApp
    y el mismo número no se carga dos veces aunque se escriba distinto."""
    if pais not in PAISES:
        raise ErrorValidacion("Seleccione el país del teléfono.")
    codigo, minimo, maximo = PAISES[pais]
    texto = (texto or "").strip()
    if re.search(r"[^\d\s\-+()]", texto):
        raise ErrorValidacion("El teléfono solo puede contener números, espacios o guiones.")
    digitos = re.sub(r"\D", "", texto)
    # Si ya viene con el código del país (+595 981..., 595981...), se le quita.
    if texto.startswith("+") or (digitos.startswith(codigo) and len(digitos) > maximo):
        if not digitos.startswith(codigo):
            raise ErrorValidacion(
                f"El número tiene un código de país distinto de {pais} (+{codigo}). Elija el país correcto.")
        digitos = digitos[len(codigo):]
    digitos = digitos.lstrip("0")          # el 0 inicial (0981...) no se usa con el código de país
    if not minimo <= len(digitos) <= maximo:
        cantidad = str(minimo) if minimo == maximo else f"{minimo} u {maximo}"
        raise ErrorValidacion(
            f"Un teléfono de {pais} debe tener {cantidad} dígitos, sin el 0 inicial ni el +{codigo}.")
    if pais == "Paraguay" and not digitos.startswith("9"):
        raise ErrorValidacion("El celular de Paraguay debe empezar con 09, por ejemplo 0981 123 456.")
    return "+" + codigo + digitos


def separar_telefono(telefono):
    """'+595981123456' -> ('Paraguay', '981123456'). Sirve para mostrar el teléfono
    guardado en el formulario de edición, con su país elegido."""
    digitos = re.sub(r"\D", "", telefono or "")
    # Se prueba primero el código más largo: +591 (Bolivia) antes que +59..., +1 al final
    for pais, (codigo, _minimo, _maximo) in sorted(PAISES.items(), key=lambda p: -len(p[1][0])):
        if digitos.startswith(codigo):
            return pais, digitos[len(codigo):]
    return PAIS_POR_DEFECTO, digitos


def validar_correo(texto, obligatorio=False):
    correo = (texto or "").strip().lower()
    if not correo:
        if obligatorio:
            raise ErrorValidacion("El correo es obligatorio.")
        return None
    if len(correo) > LARGO_MAXIMO["correo"] or not PATRON_CORREO.fullmatch(correo):
        raise ErrorValidacion(f"El correo «{correo[:40]}» no es válido. Ejemplo: nombre@gmail.com")
    return correo


def validar_usuario(texto):
    usuario = (texto or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_.]{2,19}", usuario):
        raise ErrorValidacion(
            "El usuario debe empezar con una letra y tener de 3 a 20 caracteres: letras sin tilde, "
            "números, punto o guion bajo.")
    return usuario


def validar_clave_nueva(clave, confirmacion):
    if not 8 <= len(clave) <= LARGO_MAXIMO["clave"]:
        raise ErrorValidacion(f"La contraseña debe tener entre 8 y {LARGO_MAXIMO['clave']} caracteres.")
    if not re.search(r"[A-Za-z]", clave) or not re.search(r"\d", clave):
        raise ErrorValidacion("La contraseña debe combinar letras y números.")
    if clave != confirmacion:
        raise ErrorValidacion("Las dos contraseñas no coinciden.")
