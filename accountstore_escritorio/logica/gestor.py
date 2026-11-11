"""Capa de LÓGICA: coordina permisos, reglas de negocio y acceso a datos.

La interfaz (Tkinter) solo llama a métodos de esta clase. Cada operación:
  1) verifica que el usuario tenga permiso,
  2) valida los datos y aplica las reglas de negocio,
  3) recién entonces pide al repositorio que guarde.
Si algo falla, lanza ErrorValidacion o PermisoDenegado con un mensaje claro
y NO se guarda nada.
"""
import sqlite3
from datetime import date

from logica import reglas, seguridad
from logica.errores import ErrorValidacion, PermisoDenegado
from logica.permisos import ROLES, exigir_permiso, tiene_permiso


def _error_de_base(error, si_repetido):
    """Traduce un error técnico de SQLite en un mensaje entendible."""
    texto = str(error)
    if "UNIQUE" in texto:
        return ErrorValidacion(si_repetido)
    if "FOREIGN KEY" in texto:
        return ErrorValidacion("Los datos hacen referencia a un registro que no existe.")
    return ErrorValidacion(f"La base de datos rechazó los datos ({texto}).")


class Gestor:
    def __init__(self, repositorio):
        self.repo = repositorio
        self.usuario = None          # usuario con la sesión iniciada, o None

    # =============================================================== sesión
    def iniciar_sesion(self, usuario, clave):
        usuario = (usuario or "").strip().lower()
        if not usuario or not clave:
            raise ErrorValidacion("Ingrese su usuario y su contraseña.")
        fila = self.repo.buscar_usuario(usuario)
        if (fila is None or not fila["activo"]
                or not seguridad.verificar_clave(clave, fila["clave_hash"], fila["clave_sal"])):
            # El mismo mensaje para todos los casos: no revela si el usuario existe.
            raise ErrorValidacion("Usuario o contraseña incorrectos.")
        self.usuario = {"id": fila["id"], "usuario": fila["usuario"],
                        "nombre": fila["nombre"], "rol": fila["rol"]}
        return self.usuario

    def cerrar_sesion(self):
        self.usuario = None

    def puede(self, accion):
        return self.usuario is not None and tiene_permiso(self.usuario["rol"], accion)

    def verificar_permiso(self, accion):
        exigir_permiso(self.usuario, accion)

    def _exigir_sesion(self):
        if self.usuario is None:
            raise PermisoDenegado("Debe iniciar sesión para continuar.")

    # ============================================================= clientes
    def listar_clientes(self, texto=""):
        self._exigir_sesion()
        return [dict(fila) for fila in self.repo.listar_clientes(texto.strip())]

    def registrar_cliente(self, nombre, telefono, correo):
        exigir_permiso(self.usuario, "gestionar_clientes")
        nombre = reglas.validar_nombre(nombre, "El nombre del cliente")
        telefono = reglas.normalizar_telefono(telefono)
        correo = reglas.validar_correo(correo)
        try:
            return self.repo.insertar_cliente(nombre, telefono, correo)
        except sqlite3.IntegrityError as error:
            # La restricción UNIQUE de clientes.telefono impide clientes repetidos.
            raise _error_de_base(error, f"Ya existe un cliente con el teléfono {telefono}.") from error

    def eliminar_cliente(self, cliente_id):
        exigir_permiso(self.usuario, "eliminar_cliente")
        if cliente_id is None:
            raise ErrorValidacion("Seleccione un cliente de la lista.")
        try:
            self.repo.eliminar_cliente(cliente_id)
        except sqlite3.IntegrityError as error:
            # La clave foránea suscripciones.cliente_id (ON DELETE RESTRICT) lo impide.
            raise ErrorValidacion(
                "No se puede eliminar este cliente porque tiene suscripciones registradas: "
                "su historial de ventas y pagos debe conservarse.") from error

    # ==================================================== servicios y cuentas
    def listar_servicios(self):
        self._exigir_sesion()
        return [dict(fila) for fila in self.repo.listar_servicios()]

    def listar_cuentas(self, servicio_id=None):
        self._exigir_sesion()
        cuentas = []
        for fila in self.repo.listar_cuentas(servicio_id):
            cuenta = dict(fila)
            cuenta["libres"] = cuenta["capacidad"] - cuenta["ocupados"]
            cuentas.append(cuenta)
        return cuentas

    def registrar_servicio(self, nombre, capacidad, precio_mensual):
        exigir_permiso(self.usuario, "gestionar_cuentas")
        nombre = " ".join((nombre or "").split())
        if len(nombre) < 2:
            raise ErrorValidacion("Escriba el nombre del servicio.")
        capacidad = reglas.validar_entero(capacidad, "La capacidad (perfiles por cuenta)", 1, 20)
        precio = reglas.validar_entero(str(precio_mensual).replace(".", ""), "El precio mensual", 1000)
        try:
            return self.repo.insertar_servicio(nombre, capacidad, precio)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, f"Ya existe un servicio llamado {nombre}.") from error

    def registrar_cuenta(self, servicio_id, correo):
        exigir_permiso(self.usuario, "gestionar_cuentas")
        if servicio_id is None:
            raise ErrorValidacion("Seleccione el servicio de la cuenta.")
        correo = reglas.validar_correo(correo, obligatorio=True)
        try:
            return self.repo.insertar_cuenta(servicio_id, correo)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, f"La cuenta {correo} ya está registrada en ese servicio.") from error

    def _cuenta(self, cuenta_id):
        fila = self.repo.obtener_cuenta(cuenta_id)
        if fila is None:
            raise ErrorValidacion("La cuenta seleccionada no existe.")
        return dict(fila)

    # ======================================================== suscripciones
    def listar_suscripciones(self, texto="", situacion="Todos", hoy=None):
        """Devuelve las suscripciones con los días que faltan y su situación
        (ACTIVO, A VENCER, VENCIDO o BAJA), calculados con la fecha de hoy."""
        self._exigir_sesion()
        hoy = hoy or date.today()
        resultado = []
        for fila in self.repo.listar_suscripciones(texto.strip()):
            s = dict(fila)
            s["fecha_inicio"] = date.fromisoformat(s["fecha_inicio"])
            s["vencimiento"] = date.fromisoformat(s["vencimiento"])
            if s["estado"] == "BAJA":
                s["dias"] = None
                s["situacion"] = "BAJA"
            else:
                s["dias"] = reglas.dias_restantes(s["vencimiento"], hoy)
                s["situacion"] = reglas.estado_por_dias(s["dias"])
            if situacion in ("", "Todos") or s["situacion"] == situacion:
                resultado.append(s)
        return resultado

    def obtener_suscripcion(self, suscripcion_id):
        self._exigir_sesion()
        if suscripcion_id is None:
            raise ErrorValidacion("Seleccione una suscripción de la lista.")
        fila = self.repo.obtener_suscripcion(suscripcion_id)
        if fila is None:
            raise ErrorValidacion("La suscripción seleccionada no existe.")
        s = dict(fila)
        s["fecha_inicio"] = date.fromisoformat(s["fecha_inicio"])
        s["vencimiento"] = date.fromisoformat(s["vencimiento"])
        return s

    def cotizar_venta(self, cuenta_id, perfiles, meses, fecha_inicio):
        """Calcula vencimiento y monto SIN guardar (para mostrarlos en pantalla)."""
        self._exigir_sesion()
        cuenta = self._cuenta(cuenta_id)
        perfiles = reglas.validar_entero(perfiles, "La cantidad de perfiles", 1)
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        inicio = reglas.convertir_fecha(fecha_inicio)
        return (reglas.sumar_meses(inicio, meses),
                reglas.calcular_monto(cuenta["precio_mensual"], perfiles, meses))

    def registrar_venta(self, cliente_id, cuenta_id, perfiles, meses, fecha_inicio, hoy=None):
        """PROCESO PRINCIPAL: vender perfiles de una cuenta a un cliente."""
        exigir_permiso(self.usuario, "registrar_venta")
        hoy = hoy or date.today()

        # 1) Validar los datos recibidos de la pantalla
        if cliente_id is None:
            raise ErrorValidacion("Seleccione un cliente.")
        if cuenta_id is None:
            raise ErrorValidacion("Seleccione el servicio y la cuenta.")
        perfiles = reglas.validar_entero(perfiles, "La cantidad de perfiles", 1)
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        inicio = reglas.convertir_fecha(fecha_inicio)
        if inicio > hoy:
            raise ErrorValidacion("La fecha de inicio no puede ser posterior a hoy.")

        # 2) Aplicar las reglas de negocio
        cuenta = self._cuenta(cuenta_id)
        reglas.validar_cupo(cuenta["capacidad"], cuenta["ocupados"], perfiles, cuenta["correo"])
        vencimiento = reglas.sumar_meses(inicio, meses)
        monto = reglas.calcular_monto(cuenta["precio_mensual"], perfiles, meses)

        # 3) Guardar la suscripción y su pago (una sola transacción)
        try:
            nuevo_id = self.repo.insertar_venta(
                cliente_id, cuenta_id, perfiles, inicio.isoformat(), vencimiento.isoformat(),
                self.usuario["id"], meses, monto)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, "La venta ya estaba registrada.") from error
        return {"id": nuevo_id, "vencimiento": vencimiento, "monto": monto}

    def cotizar_renovacion(self, suscripcion_id, meses, hoy=None):
        hoy = hoy or date.today()
        s = self.obtener_suscripcion(suscripcion_id)
        if s["estado"] == "BAJA":
            raise ErrorValidacion("Esta suscripción está dada de baja: registre una venta nueva.")
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        desde = reglas.inicio_renovacion(s["vencimiento"], hoy)
        return {"meses": meses,
                "vencimiento": reglas.sumar_meses(desde, meses),
                "monto": reglas.calcular_monto(s["precio_mensual"], s["perfiles"], meses)}

    def renovar(self, suscripcion_id, meses, hoy=None):
        exigir_permiso(self.usuario, "renovar")
        hoy = hoy or date.today()
        datos = self.cotizar_renovacion(suscripcion_id, meses, hoy)
        self.repo.registrar_renovacion(suscripcion_id, datos["vencimiento"].isoformat(),
                                       self.usuario["id"], hoy.isoformat(),
                                       datos["meses"], datos["monto"])
        return datos

    def dar_de_baja(self, suscripcion_id, hoy=None):
        """REGLA: los perfiles de una cuenta solo se liberan al dar de baja."""
        exigir_permiso(self.usuario, "dar_de_baja")
        s = self.obtener_suscripcion(suscripcion_id)
        if s["estado"] == "BAJA":
            raise ErrorValidacion("La suscripción ya estaba dada de baja.")
        self.repo.dar_de_baja(suscripcion_id, (hoy or date.today()).isoformat())
        return s

    def historial_pagos(self, suscripcion_id):
        self._exigir_sesion()
        pagos = []
        for fila in self.repo.listar_pagos(suscripcion_id):
            pago = dict(fila)
            pago["fecha"] = date.fromisoformat(pago["fecha"])
            pagos.append(pago)
        return pagos

    # ============================================================= usuarios
    def listar_usuarios(self):
        self._exigir_sesion()
        usuarios = []
        for fila in self.repo.listar_usuarios():
            usuario = dict(fila)
            usuario["rol_texto"] = ROLES.get(usuario["rol"], usuario["rol"])
            usuarios.append(usuario)
        return usuarios

    def registrar_usuario(self, usuario, nombre, rol, clave, confirmacion):
        exigir_permiso(self.usuario, "gestionar_usuarios")
        usuario = reglas.validar_usuario(usuario)
        nombre = reglas.validar_nombre(nombre, "El nombre")
        if rol not in ROLES:
            raise ErrorValidacion("Seleccione un rol válido.")
        reglas.validar_clave_nueva(clave, confirmacion)
        clave_hash, clave_sal = seguridad.generar_hash(clave)
        try:
            return self.repo.insertar_usuario(usuario, nombre, rol, clave_hash, clave_sal)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, f"El usuario «{usuario}» ya existe.") from error
