"""Pantalla de inicio de sesión."""
from tkinter import ttk

from interfaz.comun import ejecutar_seguro


class PantallaLogin(ttk.Frame):
    def __init__(self, padre, gestor, al_ingresar):
        super().__init__(padre)
        self.gestor = gestor
        self.al_ingresar = al_ingresar

        caja = ttk.Frame(self, padding=32, style="Caja.TFrame")
        caja.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(caja, text="AccountStore", style="Titulo.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(caja, text="Gestión de suscripciones de streaming",
                  style="CajaNota.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 18))

        ttk.Label(caja, text="Usuario", style="Caja.TLabel").grid(row=2, column=0, sticky="w")
        self.usuario = ttk.Entry(caja, width=32)
        self.usuario.grid(row=3, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(caja, text="Contraseña", style="Caja.TLabel").grid(row=4, column=0, sticky="w")
        self.clave = ttk.Entry(caja, width=32, show="•")
        self.clave.grid(row=5, column=0, sticky="ew", pady=(2, 16))

        ttk.Button(caja, text="Ingresar", style="Accion.TButton",
                   command=self.ingresar).grid(row=6, column=0, sticky="ew")

        self.usuario.bind("<Return>", lambda _evento: self.clave.focus_set())
        self.clave.bind("<Return>", self.ingresar)
        self.usuario.focus_set()

    def ingresar(self, _evento=None):
        ok, _ = ejecutar_seguro(self, self.gestor.iniciar_sesion, self.usuario.get(), self.clave.get())
        self.clave.delete(0, "end")          # la contraseña no queda escrita en pantalla
        if ok:
            self.al_ingresar()
