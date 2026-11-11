"""AccountStore Escritorio — punto de entrada.

Ejecutar desde esta carpeta con:   python main.py

Capas del sistema:
  interfaz/  -> pantallas Tkinter (solo muestran datos y llaman a la lógica)
  logica/    -> reglas de negocio, validaciones, permisos y seguridad
  datos/     -> conexión a SQLite y todas las consultas SQL
"""
import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from datos.conexion import BaseIncompatible, conectar, inicializar
from datos.repositorio import Repositorio
from interfaz.app import Aplicacion
from logica.datos_ejemplo import cargar_si_esta_vacia
from logica.gestor import Gestor


def main():
    logging.basicConfig(filename=str(Path(__file__).with_name("errores.log")), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    conexion = conectar()
    try:
        try:
            inicializar(conexion)
        except BaseIncompatible as error:
            ventana = tk.Tk()
            ventana.withdraw()
            messagebox.showerror("Base de datos de una versión anterior", str(error))
            ventana.destroy()
            return
        repositorio = Repositorio(conexion)
        if cargar_si_esta_vacia(repositorio):
            logging.info("Base nueva: se cargaron los datos de ejemplo.")
        aplicacion = Aplicacion(Gestor(repositorio))
        aplicacion.mainloop()
    finally:
        conexion.close()          # se cierra la base al salir del programa


if __name__ == "__main__":
    main()
