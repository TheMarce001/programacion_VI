"""Ventana principal: menú lateral oscuro con el logo y el área de contenido.

Navegación: cada botón del menú muestra una sección (Suscripciones, Clientes,
Cuentas y servicios, Usuarios) y vuelve a leer sus datos de la base.
"""
from datetime import date
from tkinter import ttk

from interfaz.clientes import PestanaClientes
from interfaz.comun import cargar_imagen
from interfaz.cuentas import PestanaCuentas
from interfaz.suscripciones import PestanaSuscripciones
from interfaz.usuarios import PestanaUsuarios
from logica.permisos import ROLES
from logica.reglas import fecha_a_texto

SECCIONES = [
    ("suscripciones", "Suscripciones", PestanaSuscripciones),
    ("clientes", "Clientes", PestanaClientes),
    ("cuentas", "Cuentas y servicios", PestanaCuentas),
    ("usuarios", "Usuarios", PestanaUsuarios),
]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


class PantallaPrincipal(ttk.Frame):
    def __init__(self, padre, gestor, al_cerrar_sesion):
        super().__init__(padre)
        usuario = gestor.usuario

        # ---- Menú lateral
        lateral = ttk.Frame(self, style="Lateral.TFrame", padding=(14, 20), width=232)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        self.logo = cargar_imagen("logo_menu.png")
        if self.logo:
            ttk.Label(lateral, image=self.logo, style="Lateral.TLabel").pack(anchor="w", pady=(0, 26))
        ttk.Label(lateral, text="MENÚ", style="LateralNota.TLabel").pack(anchor="w", padx=4, pady=(0, 6))
        self.botones = {}
        for clave, titulo, _clase in SECCIONES:
            boton = ttk.Button(lateral, text=titulo, style="Nav.TButton",
                               command=lambda c=clave: self.mostrar(c))
            boton.pack(fill="x", pady=2)
            self.botones[clave] = boton

        pie = ttk.Frame(lateral, style="Lateral.TFrame")
        pie.pack(side="bottom", fill="x")
        ttk.Label(pie, text=usuario["nombre"], style="LateralFuerte.TLabel").pack(anchor="w", padx=4)
        ttk.Label(pie, text=ROLES[usuario["rol"]], style="LateralNota.TLabel").pack(
            anchor="w", padx=4, pady=(0, 12))
        ttk.Button(pie, text="Cerrar sesión", style="Salir.TButton",
                   command=al_cerrar_sesion).pack(fill="x")

        # ---- Contenido
        contenido = ttk.Frame(self, padding=(26, 20, 26, 18))
        contenido.pack(side="left", fill="both", expand=True)
        cabecera = ttk.Frame(contenido)
        cabecera.pack(fill="x")
        hoy = date.today()
        ttk.Label(cabecera, text=f"Hoy, {DIAS[hoy.weekday()]} {fecha_a_texto(hoy)}",
                  style="Nota.TLabel").pack(side="right", anchor="n", pady=(6, 0))
        self.titulo = ttk.Label(cabecera, style="Titulo.TLabel")
        self.titulo.pack(anchor="w")
        self.descripcion = ttk.Label(cabecera, style="Nota.TLabel")
        self.descripcion.pack(anchor="w")

        self.secciones = {clave: clase(contenido, gestor) for clave, _titulo, clase in SECCIONES}
        self.actual = None
        self.mostrar("suscripciones")

    def mostrar(self, clave):
        if self.actual is not None:
            self.secciones[self.actual].pack_forget()
            self.botones[self.actual].configure(style="Nav.TButton")
        self.actual = clave
        seccion = self.secciones[clave]
        self.botones[clave].configure(style="NavActivo.TButton")
        self.titulo.configure(text=seccion.TITULO)
        self.descripcion.configure(text=seccion.DESCRIPCION)
        seccion.pack(fill="both", expand=True, pady=(16, 0))
        seccion.actualizar()                    # vuelve a leer los datos de la base
