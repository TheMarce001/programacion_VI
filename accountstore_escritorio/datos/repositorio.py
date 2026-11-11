"""Capa de ACCESO A DATOS.

Aquí están TODAS las consultas SQL del sistema: ninguna otra capa escribe SQL.
Todas son consultas parametrizadas: los datos se envían aparte, en el lugar
de cada "?", y nunca se pegan dentro del texto SQL. Así se evita la
inyección SQL.

"with self.conexion:" abre una transacción: si todo sale bien hace COMMIT
(guarda) y si ocurre un error hace ROLLBACK (no guarda nada).
"""


class Repositorio:
    def __init__(self, conexion):
        self.conexion = conexion

    # ------------------------------------------------------------ usuarios
    def contar_usuarios(self):
        return self.conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    def buscar_usuario(self, usuario):
        sql = """SELECT id, usuario, nombre, rol, clave_hash, clave_sal, activo
                 FROM usuarios
                 WHERE usuario = ?"""
        return self.conexion.execute(sql, (usuario,)).fetchone()

    def listar_usuarios(self):
        sql = "SELECT id, usuario, nombre, rol, activo FROM usuarios ORDER BY usuario"
        return self.conexion.execute(sql).fetchall()

    def insertar_usuario(self, usuario, nombre, rol, clave_hash, clave_sal):
        sql = """INSERT INTO usuarios (usuario, nombre, rol, clave_hash, clave_sal)
                 VALUES (?, ?, ?, ?, ?)"""
        with self.conexion:
            cursor = self.conexion.execute(sql, (usuario, nombre, rol, clave_hash, clave_sal))
        return cursor.lastrowid

    # ----------------------------------------------------------- servicios
    def listar_servicios(self):
        sql = "SELECT id, nombre, capacidad, precio_mensual FROM servicios ORDER BY nombre"
        return self.conexion.execute(sql).fetchall()

    def insertar_servicio(self, nombre, capacidad, precio_mensual):
        sql = "INSERT INTO servicios (nombre, capacidad, precio_mensual) VALUES (?, ?, ?)"
        with self.conexion:
            cursor = self.conexion.execute(sql, (nombre, capacidad, precio_mensual))
        return cursor.lastrowid

    # ------------------------------------------------------------- cuentas
    def listar_cuentas(self, servicio_id=None):
        """Cuentas con sus perfiles ocupados (suma de suscripciones ACTIVAS).
        Si servicio_id es None devuelve las cuentas de todos los servicios."""
        sql = """SELECT c.id, c.correo, c.servicio_id, s.nombre AS servicio,
                        s.capacidad, s.precio_mensual,
                        SUM(CASE WHEN su.estado = 'ACTIVA' THEN su.perfiles ELSE 0 END) AS ocupados
                 FROM cuentas c
                 JOIN servicios s ON s.id = c.servicio_id
                 LEFT JOIN suscripciones su ON su.cuenta_id = c.id
                 WHERE ? IS NULL OR c.servicio_id = ?
                 GROUP BY c.id
                 ORDER BY s.nombre, c.correo"""
        return self.conexion.execute(sql, (servicio_id, servicio_id)).fetchall()

    def obtener_cuenta(self, cuenta_id):
        sql = """SELECT c.id, c.correo, c.servicio_id, s.nombre AS servicio,
                        s.capacidad, s.precio_mensual,
                        SUM(CASE WHEN su.estado = 'ACTIVA' THEN su.perfiles ELSE 0 END) AS ocupados
                 FROM cuentas c
                 JOIN servicios s ON s.id = c.servicio_id
                 LEFT JOIN suscripciones su ON su.cuenta_id = c.id
                 WHERE c.id = ?
                 GROUP BY c.id"""
        return self.conexion.execute(sql, (cuenta_id,)).fetchone()

    def eliminar_servicio(self, servicio_id):
        with self.conexion:
            self.conexion.execute("DELETE FROM servicios WHERE id = ?", (servicio_id,))

    def eliminar_cuenta(self, cuenta_id):
        with self.conexion:
            self.conexion.execute("DELETE FROM cuentas WHERE id = ?", (cuenta_id,))

    def insertar_cuenta(self, servicio_id, correo):
        sql = "INSERT INTO cuentas (servicio_id, correo) VALUES (?, ?)"
        with self.conexion:
            cursor = self.conexion.execute(sql, (servicio_id, correo))
        return cursor.lastrowid

    # ------------------------------------------------------------ clientes
    def listar_clientes(self, texto=""):
        patron = "%" + texto + "%"
        sql = """SELECT id, nombre, telefono, correo
                 FROM clientes
                 WHERE sin_tildes(nombre) LIKE sin_tildes(?) OR telefono LIKE ?
                 ORDER BY nombre"""
        return self.conexion.execute(sql, (patron, patron)).fetchall()

    def insertar_cliente(self, nombre, telefono, correo):
        sql = "INSERT INTO clientes (nombre, telefono, correo) VALUES (?, ?, ?)"
        with self.conexion:
            cursor = self.conexion.execute(sql, (nombre, telefono, correo))
        return cursor.lastrowid

    def eliminar_cliente(self, cliente_id):
        with self.conexion:
            self.conexion.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))

    # ------------------------------------------------------- suscripciones
    def listar_suscripciones(self, texto=""):
        """CONSULTA DE RECUPERACIÓN del demo: une 4 tablas para mostrar cada
        suscripción con el nombre del cliente, el servicio y la cuenta."""
        patron = "%" + texto + "%"
        sql = """SELECT su.id, cl.nombre AS cliente, cl.telefono, se.nombre AS servicio,
                        cu.correo AS cuenta, su.perfiles, su.fecha_inicio,
                        su.vencimiento, su.estado
                 FROM suscripciones su
                 JOIN clientes  cl ON cl.id = su.cliente_id
                 JOIN cuentas   cu ON cu.id = su.cuenta_id
                 JOIN servicios se ON se.id = cu.servicio_id
                 WHERE sin_tildes(cl.nombre) LIKE sin_tildes(?) OR cl.telefono LIKE ?
                       OR se.nombre LIKE ?
                 ORDER BY su.vencimiento"""
        return self.conexion.execute(sql, (patron, patron, patron)).fetchall()

    def obtener_suscripcion(self, suscripcion_id):
        sql = """SELECT su.id, su.perfiles, su.fecha_inicio, su.vencimiento, su.estado,
                        cl.nombre AS cliente, cu.correo AS cuenta,
                        se.nombre AS servicio, se.precio_mensual
                 FROM suscripciones su
                 JOIN clientes  cl ON cl.id = su.cliente_id
                 JOIN cuentas   cu ON cu.id = su.cuenta_id
                 JOIN servicios se ON se.id = cu.servicio_id
                 WHERE su.id = ?"""
        return self.conexion.execute(sql, (suscripcion_id,)).fetchone()

    def insertar_venta(self, cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento,
                       usuario_id, meses, monto, descuento=0):
        """CONSULTA DE INSERCIÓN del demo. Guarda la suscripción y su pago en
        UNA transacción: se guardan las dos filas o ninguna."""
        sql_suscripcion = """INSERT INTO suscripciones
                                 (cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento)
                             VALUES (?, ?, ?, ?, ?)"""
        sql_pago = """INSERT INTO pagos (suscripcion_id, usuario_id, fecha, concepto, meses,
                                         descuento, monto)
                      VALUES (?, ?, ?, 'VENTA', ?, ?, ?)"""
        with self.conexion:
            cursor = self.conexion.execute(
                sql_suscripcion, (cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento))
            suscripcion_id = cursor.lastrowid
            self.conexion.execute(sql_pago, (suscripcion_id, usuario_id, fecha_inicio, meses,
                                             descuento, monto))
        return suscripcion_id

    def registrar_renovacion(self, suscripcion_id, nuevo_vencimiento, usuario_id, fecha, meses, monto,
                             descuento=0):
        sql_suscripcion = "UPDATE suscripciones SET vencimiento = ? WHERE id = ? AND estado = 'ACTIVA'"
        sql_pago = """INSERT INTO pagos (suscripcion_id, usuario_id, fecha, concepto, meses,
                                         descuento, monto)
                      VALUES (?, ?, ?, 'RENOVACION', ?, ?, ?)"""
        with self.conexion:
            self.conexion.execute(sql_suscripcion, (nuevo_vencimiento, suscripcion_id))
            self.conexion.execute(sql_pago, (suscripcion_id, usuario_id, fecha, meses, descuento, monto))

    def dar_de_baja(self, suscripcion_id, fecha_baja):
        sql = """UPDATE suscripciones SET estado = 'BAJA', fecha_baja = ?
                 WHERE id = ? AND estado = 'ACTIVA'"""
        with self.conexion:
            self.conexion.execute(sql, (fecha_baja, suscripcion_id))

    # --------------------------------------------------------------- pagos
    def total_cobrado(self, desde, hasta):
        """Suma de los pagos entre dos fechas (AAAA-MM-DD), ambas incluidas."""
        sql = "SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE fecha BETWEEN ? AND ?"
        return self.conexion.execute(sql, (desde, hasta)).fetchone()[0]

    def listar_pagos(self, suscripcion_id):
        sql = """SELECT p.fecha, p.concepto, p.meses, p.descuento, p.monto, u.nombre AS registrado_por
                 FROM pagos p
                 JOIN usuarios u ON u.id = p.usuario_id
                 WHERE p.suscripcion_id = ?
                 ORDER BY p.id"""
        return self.conexion.execute(sql, (suscripcion_id,)).fetchall()
