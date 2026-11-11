"""Conexión a la base de datos SQLite.

La base es un único archivo (accountstore.db) en la carpeta del proyecto.
Como queda guardada en el disco, los datos siguen ahí al cerrar y volver a
abrir el programa.
"""
import sqlite3
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parent
RUTA_BD = CARPETA_DATOS.parent / "accountstore.db"
RUTA_ESQUEMA = CARPETA_DATOS / "esquema.sql"


def conectar(ruta=None):
    """Abre la base de datos y activa las claves foráneas.

    IMPORTANTE: SQLite trae las claves foráneas DESACTIVADAS por defecto.
    Sin el PRAGMA de abajo, las restricciones REFERENCES no se controlan.
    """
    conexion = sqlite3.connect(str(ruta or RUTA_BD))
    conexion.row_factory = sqlite3.Row      # permite leer columnas por nombre: fila["nombre"]
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar(conexion):
    """Crea las tablas si todavía no existen (no borra datos)."""
    conexion.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))
