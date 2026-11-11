"""Muestra el contenido REAL de las tablas de accountstore.db (para la defensa).

    python inspeccionar_bd.py              -> todas las tablas
    python inspeccionar_bd.py usuarios     -> solo una tabla

Sirve para demostrar que:
  - los datos siguen guardados después de cerrar y abrir el sistema;
  - las contraseñas están guardadas como hash, no en texto plano.
"""
import sys

from datos.conexion import RUTA_BD, conectar

# Consultas fijas (los nombres de tabla no se pueden pasar como parámetro "?",
# por eso se eligen de esta lista y nunca se arman con lo que escribe el usuario).
CONSULTAS = {
    "usuarios": "SELECT * FROM usuarios",
    "servicios": "SELECT * FROM servicios",
    "cuentas": "SELECT * FROM cuentas",
    "clientes": "SELECT * FROM clientes",
    "suscripciones": "SELECT * FROM suscripciones",
    "pagos": "SELECT * FROM pagos",
}


def mostrar(conexion, tabla):
    cursor = conexion.execute(CONSULTAS[tabla])
    columnas = [descripcion[0] for descripcion in cursor.description]
    filas = cursor.fetchall()
    print(f"\n=== {tabla} ({len(filas)} filas) ===")
    print(" | ".join(columnas))
    for fila in filas:
        print(" | ".join("" if valor is None else str(valor) for valor in fila))


def main():
    if not RUTA_BD.exists():
        print("Todavía no existe accountstore.db: primero ejecute  python main.py")
        return
    tablas = sys.argv[1:] or list(CONSULTAS)
    conexion = conectar()
    try:
        for tabla in tablas:
            if tabla in CONSULTAS:
                mostrar(conexion, tabla)
            else:
                print(f"Tabla desconocida: {tabla}. Opciones: {', '.join(CONSULTAS)}")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
