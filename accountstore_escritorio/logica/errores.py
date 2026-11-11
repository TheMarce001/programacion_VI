"""Errores propios del sistema.

La lógica lanza estos errores con un mensaje claro para el usuario, y la
interfaz los muestra en una ventana de aviso en lugar de cerrarse.
"""


class ErrorValidacion(Exception):
    """Un dato no es válido o se incumple una regla de negocio. No se guarda nada."""


class PermisoDenegado(Exception):
    """El usuario no tiene permiso para la acción que intentó."""
