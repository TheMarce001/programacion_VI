"""Ventana principal: barra superior con el usuario y pestañas por módulo."""
from tkinter import ttk

from interfaz.clientes import PestanaClientes
from interfaz.cuentas import PestanaCuentas
from interfaz.suscripciones import PestanaSuscripciones
from interfaz.usuarios import PestanaUsuarios
from logica.permisos import ROLES


class PantallaPrincipal(ttk.Frame):
    def __init__(self, padre, gestor, al_cerrar_sesion):
        super().__init__(padre)
        usuario = gestor.usuario

        barra = ttk.Frame(self, padding=(16, 10), style="Barra.TFrame")
        barra.pack(fill="x")
        ttk.Label(barra, text="AccountStore", style="BarraTitulo.TLabel").pack(side="left")
        ttk.Button(barra, text="Cerrar sesión", command=al_cerrar_sesion).pack(side="right")
        ttk.Label(barra, text=f"{usuario['nombre']}  ·  {ROLES[usuario['rol']]}",
                  style="Barra.TLabel").pack(side="right", padx=14)

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=10, pady=10)
        self.pestanas.add(PestanaSuscripciones(self.pestanas, gestor), text="Suscripciones")
        self.pestanas.add(PestanaClientes(self.pestanas, gestor), text="Clientes")
        self.pestanas.add(PestanaCuentas(self.pestanas, gestor), text="Cuentas y servicios")
        self.pestanas.add(PestanaUsuarios(self.pestanas, gestor), text="Usuarios")
        # Cada vez que se abre una pestaña se vuelven a leer sus datos de la base.
        self.pestanas.bind("<<NotebookTabChanged>>", self.al_cambiar_pestana)

    def al_cambiar_pestana(self, _evento):
        pestana = self.nametowidget(self.pestanas.select())
        pestana.actualizar()
