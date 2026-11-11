"""Demuestra que la BASE DE DATOS por sí misma rechaza datos inconsistentes,
aunque alguien intente saltarse la interfaz y la lógica.

    python demo_restricciones.py

Cada intento se hace dentro de una transacción: como todos fallan, no se
guarda nada en accountstore.db.
"""
import sqlite3

from datos.conexion import RUTA_BD, conectar

INTENTOS = [
    ("Suscripción de un cliente que no existe (clave foránea)",
     "INSERT INTO suscripciones (cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento) "
     "VALUES (?, ?, ?, ?, ?)", (9999, 1, 1, "2026-11-01", "2026-12-01")),
    ("Suscripción con 0 perfiles (CHECK perfiles >= 1)",
     "INSERT INTO suscripciones (cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento) "
     "VALUES (?, ?, ?, ?, ?)", (1, 1, 0, "2026-11-01", "2026-12-01")),
    ("Vencimiento anterior al inicio (CHECK vencimiento > fecha_inicio)",
     "INSERT INTO suscripciones (cliente_id, cuenta_id, perfiles, fecha_inicio, vencimiento) "
     "VALUES (?, ?, ?, ?, ?)", (1, 1, 1, "2026-11-01", "2026-10-01")),
    ("Cliente con un teléfono que ya existe (UNIQUE)",
     "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)", ("Cliente Repetido", "+595981111222")),
    ("Teléfono sin el código de país (CHECK telefono GLOB '+[0-9]*')",
     "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)", ("Cliente Sin Codigo", "0981999999")),
    ("Pago con monto negativo (CHECK monto > 0)",
     "INSERT INTO pagos (suscripcion_id, usuario_id, fecha, concepto, meses, monto) "
     "VALUES (?, ?, ?, ?, ?, ?)", (1, 1, "2026-11-01", "VENTA", 1, -5000)),
    ("Usuario con un rol inexistente (CHECK rol IN ...)",
     "INSERT INTO usuarios (usuario, nombre, rol, clave_hash, clave_sal) VALUES (?, ?, ?, ?, ?)",
     ("intruso", "Intruso", "DUENO", "x", "x")),
    ("Eliminar un cliente que tiene suscripciones (ON DELETE RESTRICT)",
     "DELETE FROM clientes WHERE id = ?", (1,)),
]


def main():
    if not RUTA_BD.exists():
        print("Todavía no existe accountstore.db: primero ejecute  python main.py")
        return
    conexion = conectar()
    try:
        for descripcion, sql, parametros in INTENTOS:
            try:
                with conexion:
                    conexion.execute(sql, parametros)
                print(f"[ACEPTADO]  {descripcion}  <- esto NO debería pasar")
            except sqlite3.IntegrityError as error:
                print(f"[RECHAZADO] {descripcion}\n            SQLite: {error}")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
