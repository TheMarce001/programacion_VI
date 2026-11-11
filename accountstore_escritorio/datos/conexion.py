"""Conexión a la base de datos SQLite.

La base es un único archivo (accountstore.db) en la carpeta del proyecto.
Como queda guardada en el disco, los datos siguen ahí al cerrar y volver a
abrir el programa.
"""
import sqlite3
import unicodedata
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parent
RUTA_BD = CARPETA_DATOS.parent / "accountstore.db"
RUTA_ESQUEMA = CARPETA_DATOS / "esquema.sql"
VERSION_ESQUEMA = 2          # debe coincidir con "PRAGMA user_version" al final de esquema.sql


class BaseIncompatible(Exception):
    """La base accountstore.db fue creada por una versión anterior del sistema."""


def sin_tildes(texto):
    """'Gómez' -> 'gomez'. Se registra como función de SQLite para que el
    buscador encuentre nombres aunque se escriban sin tilde."""
    if texto is None:
        return None
    descompuesto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").lower()


def conectar(ruta=None):
    """Abre la base de datos y activa las claves foráneas.

    IMPORTANTE: SQLite trae las claves foráneas DESACTIVADAS por defecto.
    Sin el PRAGMA de abajo, las restricciones REFERENCES no se controlan.
    """
    conexion = sqlite3.connect(str(ruta or RUTA_BD))
    conexion.row_factory = sqlite3.Row      # permite leer columnas por nombre: fila["nombre"]
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.create_function("sin_tildes", 1, sin_tildes, deterministic=True)
    return conexion


def inicializar(conexion):
    """Crea las tablas si todavía no existen (no borra datos). Si la base ya
    existía pero es de una versión anterior, avisa en lugar de fallar después."""
    version = conexion.execute("PRAGMA user_version").fetchone()[0]
    existe = conexion.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'usuarios'").fetchone()[0]
    if existe and version != VERSION_ESQUEMA:
        raise BaseIncompatible(
            "La base de datos accountstore.db es de una versión anterior del sistema.\n\n"
            "Cierre el programa, borre el archivo accountstore.db de la carpeta del proyecto "
            "y vuelva a abrirlo: se creará solo, con los datos de ejemplo.")
    conexion.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))
