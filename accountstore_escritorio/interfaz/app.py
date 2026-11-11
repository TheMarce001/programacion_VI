"""Ventana raíz de Tkinter. Controla la navegación:
Inicio de sesión  ->  Ventana principal (pestañas)  ->  Cerrar sesión  ->  Inicio de sesión
"""
import logging
import tkinter as tk
from tkinter import messagebox

from interfaz.comun import cargar_imagen, configurar_estilos
from interfaz.login import PantallaLogin
from interfaz.principal import PantallaPrincipal


class Aplicacion(tk.Tk):
    def __init__(self, gestor):
        super().__init__()
        self.gestor = gestor
        self.title("AccountStore Escritorio")
        self.geometry("1240x720")
        self.minsize(980, 560)
        try:
            self.state("zoomed")                  # en Windows abre maximizada
        except tk.TclError:
            pass                                  # en Linux no existe "zoomed"
        self.icono = cargar_imagen("icono.png")
        if self.icono:
            self.iconphoto(True, self.icono)     # ícono de la ventana y de la barra de tareas
        configurar_estilos(self)
        # Cualquier error no previsto en un botón se muestra en un mensaje
        # en vez de perderse en la consola.
        self.report_callback_exception = self.error_no_controlado
        self.pantalla = None
        self.mostrar_login()

    def cambiar_pantalla(self, pantalla):
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = pantalla
        pantalla.pack(fill="both", expand=True)

    def mostrar_login(self):
        self.cambiar_pantalla(PantallaLogin(self, self.gestor, al_ingresar=self.mostrar_principal))

    def mostrar_principal(self):
        self.cambiar_pantalla(PantallaPrincipal(self, self.gestor, al_cerrar_sesion=self.cerrar_sesion))

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar la sesión?", parent=self):
            self.gestor.cerrar_sesion()
            self.mostrar_login()

    def error_no_controlado(self, tipo, valor, traza):
        logging.error("Error no controlado", exc_info=(tipo, valor, traza))
        messagebox.showerror("Error inesperado",
                             "Ocurrió un error inesperado. El programa sigue funcionando.\n"
                             "El detalle quedó guardado en errores.log.", parent=self)
