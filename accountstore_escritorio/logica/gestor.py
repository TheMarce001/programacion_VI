"""Capa de LÓGICA: coordina permisos, reglas de negocio y acceso a datos.

La interfaz (Tkinter) solo llama a métodos de esta clase. Cada operación:
  1) verifica que el usuario tenga permiso,
  2) valida los datos y aplica las reglas de negocio,
  3) recién entonces pide al repositorio que guarde.
Si algo falla, lanza ErrorValidacion o PermisoDenegado con un mensaje claro
y NO se guarda nada.
"""
import math
import sqlite3
from datetime import date, datetime, timedelta

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


def _texto_busqueda(texto):
    """Si se busca un teléfono (0981 111-222), se dejan solo los números y se quita
    el 0 inicial, para que coincida con el guardado en formato internacional (+595981...)."""
    texto = (texto or "").strip()
    if texto and all(c.isdigit() or c in " -+()" for c in texto) and any(c.isdigit() for c in texto):
        return "".join(c for c in texto if c.isdigit()).lstrip("0")
    return texto


class Gestor:
    def __init__(self, repositorio):
        self.repo = repositorio
        self.usuario = None          # usuario con la sesión iniciada, o None

    # =============================================================== sesión
    def iniciar_sesion(self, usuario, clave, ahora=None):
        """REGLA DE SEGURIDAD: tras 3 intentos fallidos seguidos, el usuario queda
        bloqueado 5 minutos. El bloqueo se guarda en la base: cerrar el programa no lo evita."""
        ahora = ahora or datetime.now()
        usuario = (usuario or "").strip().lower()
        if not usuario or not clave:
            raise ErrorValidacion("Ingrese su usuario y su contraseña.")
        fila = self.repo.buscar_usuario(usuario)

        # 1) ¿Está bloqueado? (se controla ANTES de mirar la contraseña)
        if fila is not None and fila["bloqueado_hasta"]:
            hasta = datetime.fromisoformat(fila["bloqueado_hasta"])
            if ahora < hasta:
                minutos = math.ceil((hasta - ahora).total_seconds() / 60)
                raise ErrorValidacion(
                    f"Usuario bloqueado por {reglas.MAX_INTENTOS} intentos fallidos. Intente de nuevo "
                    f"en {minutos} minuto(s) o pida al administrador que lo desbloquee.")

        # 2) ¿Usuario y contraseña correctos?
        if (fila is None or not fila["activo"]
                or not seguridad.verificar_clave(clave, fila["clave_hash"], fila["clave_sal"])):
            if fila is not None:
                self._sumar_intento_fallido(fila, ahora)
            # El mismo mensaje para todos los casos: no revela si el usuario existe.
            raise ErrorValidacion("Usuario o contraseña incorrectos.")

        # 3) Entró bien: se reinicia el contador de intentos
        self.repo.guardar_intentos(fila["id"], 0, None)
        self.usuario = {"id": fila["id"], "usuario": fila["usuario"],
                        "nombre": fila["nombre"], "rol": fila["rol"]}
        return self.usuario

    def _sumar_intento_fallido(self, fila, ahora):
        intentos = fila["intentos_fallidos"] + 1
        if intentos >= reglas.MAX_INTENTOS:
            hasta = ahora + timedelta(minutes=reglas.MINUTOS_BLOQUEO)
            self.repo.guardar_intentos(fila["id"], 0, hasta.isoformat(timespec="seconds"))
            raise ErrorValidacion(
                f"Contraseña incorrecta por {reglas.MAX_INTENTOS}.ª vez: el usuario quedó bloqueado "
                f"{reglas.MINUTOS_BLOQUEO} minutos.")
        self.repo.guardar_intentos(fila["id"], intentos, None)

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
        return [dict(fila) for fila in self.repo.listar_clientes(_texto_busqueda(texto))]

    def registrar_cliente(self, nombre, telefono, correo, pais=reglas.PAIS_POR_DEFECTO):
        exigir_permiso(self.usuario, "gestionar_clientes")
        nombre = reglas.validar_nombre(nombre, "El nombre del cliente")
        telefono = reglas.normalizar_telefono(telefono, pais)
        correo = reglas.validar_correo(correo)
        try:
            return self.repo.insertar_cliente(nombre, telefono, correo)
        except sqlite3.IntegrityError as error:
            # La restricción UNIQUE de clientes.telefono impide clientes repetidos.
            raise _error_de_base(error, f"Ya existe un cliente con el teléfono {telefono}.") from error

    def obtener_cliente(self, cliente_id):
        self._exigir_sesion()
        fila = self.repo.obtener_cliente(cliente_id) if cliente_id is not None else None
        if fila is None:
            raise ErrorValidacion("Seleccione un cliente de la lista.")
        cliente = dict(fila)
        cliente["pais"], cliente["numero"] = reglas.separar_telefono(cliente["telefono"])
        return cliente

    def actualizar_cliente(self, cliente_id, nombre, telefono, correo, pais=reglas.PAIS_POR_DEFECTO):
        """Editar un cliente: mismas validaciones que al crearlo."""
        exigir_permiso(self.usuario, "gestionar_clientes")
        if cliente_id is None:
            raise ErrorValidacion("Seleccione un cliente de la lista.")
        nombre = reglas.validar_nombre(nombre, "El nombre del cliente")
        telefono = reglas.normalizar_telefono(telefono, pais)
        correo = reglas.validar_correo(correo)
        try:
            cambiados = self.repo.actualizar_cliente(cliente_id, nombre, telefono, correo)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, f"Ya existe otro cliente con el teléfono {telefono}.") from error
        if cambiados == 0:
            raise ErrorValidacion("El cliente ya no existe.")

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
        nombre = reglas.validar_nombre_servicio(nombre)
        capacidad = reglas.validar_entero(capacidad, "La capacidad (perfiles por cuenta)", 1, 20)
        precio = reglas.validar_entero(str(precio_mensual).replace(".", ""), "El precio mensual",
                                       1000, 10_000_000)
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

    def eliminar_servicio(self, servicio_id):
        exigir_permiso(self.usuario, "gestionar_cuentas")
        if servicio_id is None:
            raise ErrorValidacion("Seleccione un servicio de la lista.")
        try:
            self.repo.eliminar_servicio(servicio_id)
        except sqlite3.IntegrityError as error:
            # La clave foránea cuentas.servicio_id (ON DELETE RESTRICT) lo impide.
            raise ErrorValidacion(
                "No se puede eliminar este servicio porque tiene cuentas registradas. "
                "Primero elimine sus cuentas.") from error

    def eliminar_cuenta(self, cuenta_id):
        exigir_permiso(self.usuario, "gestionar_cuentas")
        if cuenta_id is None:
            raise ErrorValidacion("Seleccione una cuenta de la lista.")
        try:
            self.repo.eliminar_cuenta(cuenta_id)
        except sqlite3.IntegrityError as error:
            # La clave foránea suscripciones.cuenta_id (ON DELETE RESTRICT) lo impide.
            raise ErrorValidacion(
                "No se puede eliminar esta cuenta porque tiene suscripciones registradas: "
                "su historial debe conservarse.") from error

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
        for fila in self.repo.listar_suscripciones(_texto_busqueda(texto)):
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

    def resumen(self, hoy=None):
        """Datos de las tarjetas de resumen: cantidad de suscripciones en cada
        situación y lo cobrado desde el día 1 del mes actual hasta hoy."""
        hoy = hoy or date.today()
        cantidades = {"ACTIVO": 0, "A VENCER": 0, "VENCIDO": 0, "BAJA": 0}
        for s in self.listar_suscripciones(hoy=hoy):
            cantidades[s["situacion"]] += 1
        cobrado = self.repo.total_cobrado(hoy.replace(day=1).isoformat(), hoy.isoformat())
        return {"cantidades": cantidades, "total": sum(cantidades.values()), "cobrado_mes": cobrado}

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

    def cotizar_venta(self, cuenta_id, perfiles, meses, fecha_inicio, descuento="", tipo_descuento="Gs."):
        """Calcula vencimiento, subtotal, descuento y total SIN guardar (para la pantalla)."""
        self._exigir_sesion()
        cuenta = self._cuenta(cuenta_id)
        perfiles = reglas.validar_entero(perfiles, "La cantidad de perfiles", 1)
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        inicio = reglas.convertir_fecha(fecha_inicio)
        subtotal = reglas.calcular_monto(cuenta["precio_mensual"], perfiles, meses)
        rebaja = reglas.calcular_descuento(subtotal, descuento, tipo_descuento)
        return {"vencimiento": reglas.sumar_meses(inicio, meses), "subtotal": subtotal,
                "descuento": rebaja, "monto": subtotal - rebaja}

    def registrar_venta(self, cliente_id, cuenta_id, perfiles, meses, fecha_inicio,
                        descuento="", tipo_descuento="Gs.", hoy=None):
        """PROCESO PRINCIPAL: vender perfiles de una cuenta a un cliente."""
        exigir_permiso(self.usuario, "registrar_venta")
        hoy = hoy or date.today()

        # 1) Validar los datos recibidos de la pantalla
        if cliente_id is None:
            raise ErrorValidacion("Busque y seleccione un cliente de la lista.")
        if cuenta_id is None:
            raise ErrorValidacion("Seleccione el servicio y la cuenta.")
        perfiles = reglas.validar_entero(perfiles, "La cantidad de perfiles", 1)
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        inicio = reglas.convertir_fecha(fecha_inicio)
        if inicio > hoy:
            raise ErrorValidacion("La fecha de inicio no puede ser posterior a hoy.")
        if (hoy - inicio).days > reglas.DIAS_ATRAS_MAXIMO:
            raise ErrorValidacion("La fecha de inicio no puede ser de hace más de un año.")

        # 2) Aplicar las reglas de negocio
        cuenta = self._cuenta(cuenta_id)
        reglas.validar_cupo(cuenta["capacidad"], cuenta["ocupados"], perfiles, cuenta["correo"])
        vencimiento = reglas.sumar_meses(inicio, meses)
        subtotal = reglas.calcular_monto(cuenta["precio_mensual"], perfiles, meses)
        rebaja = reglas.calcular_descuento(subtotal, descuento, tipo_descuento)
        monto = subtotal - rebaja

        # 3) Guardar la suscripción y su pago (una sola transacción)
        try:
            nuevo_id = self.repo.insertar_venta(
                cliente_id, cuenta_id, perfiles, inicio.isoformat(), vencimiento.isoformat(),
                self.usuario["id"], meses, monto, rebaja)
        except sqlite3.IntegrityError as error:
            raise _error_de_base(error, "La venta ya estaba registrada.") from error
        return {"id": nuevo_id, "vencimiento": vencimiento, "subtotal": subtotal,
                "descuento": rebaja, "monto": monto}

    def cotizar_renovacion(self, suscripcion_id, meses, descuento="", tipo_descuento="Gs.", hoy=None):
        hoy = hoy or date.today()
        s = self.obtener_suscripcion(suscripcion_id)
        if s["estado"] == "BAJA":
            raise ErrorValidacion("Esta suscripción está dada de baja: registre una venta nueva.")
        meses = reglas.validar_entero(meses, "La cantidad de meses", 1, reglas.MESES_MAXIMOS)
        desde = reglas.inicio_renovacion(s["vencimiento"], hoy)
        subtotal = reglas.calcular_monto(s["precio_mensual"], s["perfiles"], meses)
        rebaja = reglas.calcular_descuento(subtotal, descuento, tipo_descuento)
        return {"meses": meses, "vencimiento": reglas.sumar_meses(desde, meses),
                "subtotal": subtotal, "descuento": rebaja, "monto": subtotal - rebaja}

    def renovar(self, suscripcion_id, meses, descuento="", tipo_descuento="Gs.", hoy=None):
        exigir_permiso(self.usuario, "renovar")
        hoy = hoy or date.today()
        datos = self.cotizar_renovacion(suscripcion_id, meses, descuento, tipo_descuento, hoy)
        self.repo.registrar_renovacion(suscripcion_id, datos["vencimiento"].isoformat(),
                                       self.usuario["id"], hoy.isoformat(),
                                       datos["meses"], datos["monto"], datos["descuento"])
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
    def listar_usuarios(self, ahora=None):
        self._exigir_sesion()
        ahora = ahora or datetime.now()
        usuarios = []
        for fila in self.repo.listar_usuarios():
            usuario = dict(fila)
            usuario["rol_texto"] = ROLES.get(usuario["rol"], usuario["rol"])
            hasta = usuario["bloqueado_hasta"]
            if hasta and ahora < datetime.fromisoformat(hasta):
                usuario["estado_texto"] = f"Bloqueado ({datetime.fromisoformat(hasta).strftime('%H:%M')})"
            else:
                usuario["estado_texto"] = "Activo" if usuario["activo"] else "Inactivo"
            usuarios.append(usuario)
        return usuarios

    def desbloquear_usuario(self, usuario_id):
        exigir_permiso(self.usuario, "gestionar_usuarios")
        if usuario_id is None:
            raise ErrorValidacion("Seleccione un usuario de la lista.")
        self.repo.guardar_intentos(usuario_id, 0, None)

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
