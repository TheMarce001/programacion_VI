"""Pantalla de inicio de sesión (tarjeta oscura con el logo, como en la app)."""
from tkinter import ttk

from interfaz.comun import cargar_imagen, ejecutar_seguro

VERSION = "1.0 (12/11/2026)"


class PantallaLogin(ttk.Frame):
    def __init__(self, padre, gestor, al_ingresar):
        super().__init__(padre, style="Login.TFrame")
        self.gestor = gestor
        self.al_ingresar = al_ingresar

        caja = ttk.Frame(self, padding=(34, 30), style="LoginTarjeta.TFrame")
        caja.place(relx=0.5, rely=0.5, anchor="center")

        self.logo = cargar_imagen("logo_login.png")      # se guarda para que no se borre
        if self.logo:
            ttk.Label(caja, image=self.logo, style="Login.TLabel").pack(pady=(0, 14))
        ttk.Label(caja, text="Hola de nuevo", style="LoginTitulo.TLabel").pack()
        ttk.Label(caja, text="Ingrese su usuario y contraseña para continuar.",
                  style="Login.TLabel").pack(pady=(2, 20))

        ttk.Label(caja, text="Usuario", style="Login.TLabel").pack(anchor="w")
        self.usuario = ttk.Entry(caja, width=36, style="Login.TEntry")
        self.usuario.pack(fill="x", pady=(4, 12))
        ttk.Label(caja, text="Contraseña", style="Login.TLabel").pack(anchor="w")
        self.clave = ttk.Entry(caja, width=36, show="•", style="Login.TEntry")
        self.clave.pack(fill="x", pady=(4, 6))

        ttk.Button(caja, text="Entrar", style="Login.TButton",
                   command=self.ingresar).pack(fill="x", pady=(16, 14))
        ttk.Label(caja, text=f"AccountStore Escritorio · versión {VERSION}",
                  style="LoginPie.TLabel").pack()

        self.usuario.bind("<Return>", lambda _evento: self.clave.focus_set())
        self.clave.bind("<Return>", self.ingresar)
        self.usuario.focus_set()

    def ingresar(self, _evento=None):
        ok, _ = ejecutar_seguro(self, self.gestor.iniciar_sesion, self.usuario.get(), self.clave.get())
        self.clave.delete(0, "end")          # la contraseña no queda escrita en pantalla
        if ok:
            self.al_ingresar()
