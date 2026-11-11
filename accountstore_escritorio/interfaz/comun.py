"""Herramientas compartidas por todas las pantallas: estilos, tablas,
diálogos y el manejo de errores que evita que el programa se cierre."""
import logging
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from logica.errores import ErrorValidacion, PermisoDenegado

FONDO = "#f4f6f8"
BARRA = "#1f2a44"
ACENTO = "#2563eb"
COLOR_SITUACION = {           # color de fondo de cada fila según su situación
    "ACTIVO": "#e6f4ea",
    "A VENCER": "#fff4d6",
    "VENCIDO": "#fde2e1",
    "BAJA": "#eceff1",
    "LLENA": "#fde2e1",
}


def ejecutar_seguro(ventana, funcion, *argumentos):
    """Ejecuta una operación de la lógica y, si falla, muestra un mensaje claro.

    Devuelve (True, resultado) si salió bien o (False, None) si hubo un error.
    Ningún error cierra el programa: los esperados se explican al usuario y
    los inesperados quedan anotados en errores.log.
    """
    try:
        return True, funcion(*argumentos)
    except ErrorValidacion as error:
        messagebox.showwarning("Dato no válido", str(error), parent=ventana)
    except PermisoDenegado as error:
        messagebox.showerror("Acceso denegado", str(error), parent=ventana)
    except Exception:
        logging.exception("Error inesperado")
        messagebox.showerror(
            "Error inesperado",
            "Ocurrió un error inesperado y la operación no se completó.\n"
            "El detalle quedó guardado en el archivo errores.log.",
            parent=ventana)
    return False, None


def formato_gs(monto):
    return "Gs. " + f"{monto:,}".replace(",", ".")


def etiqueta(situacion):
    """Nombre de etiqueta (tag) del Treeview para una situación: 'A VENCER' -> 'a_vencer'."""
    return situacion.lower().replace(" ", "_")


def configurar_estilos(raiz):
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    base = tkfont.nametofont("TkDefaultFont")
    base.configure(size=10)
    familia = base.actual("family")
    raiz.configure(background=FONDO)

    for nombre in ("TFrame", "TLabel", "TLabelframe", "TNotebook", "TCheckbutton"):
        estilo.configure(nombre, background=FONDO)
    estilo.configure("TLabelframe.Label", background=FONDO, font=(familia, 10, "bold"))
    estilo.configure("Titulo.TLabel", font=(familia, 20, "bold"), background="white")
    estilo.configure("Caja.TFrame", background="white", relief="solid", borderwidth=1)
    estilo.configure("Caja.TLabel", background="white")
    estilo.configure("Nota.TLabel", foreground="#5f6b7a")
    estilo.configure("CajaNota.TLabel", foreground="#5f6b7a", background="white")
    estilo.configure("Seccion.TLabel", font=(familia, 12, "bold"))
    estilo.configure("Resumen.TLabel", font=(familia, 10, "bold"), foreground="#1f2a44")
    estilo.configure("Barra.TFrame", background=BARRA)
    estilo.configure("Barra.TLabel", background=BARRA, foreground="white")
    estilo.configure("BarraTitulo.TLabel", background=BARRA, foreground="white",
                     font=(familia, 14, "bold"))
    estilo.configure("Accion.TButton", background=ACENTO, foreground="white")
    estilo.map("Accion.TButton", background=[("active", "#1d4ed8"), ("pressed", "#1e40af")])
    estilo.configure("TNotebook.Tab", padding=(14, 6))
    estilo.configure("Treeview", rowheight=24)
    estilo.configure("Treeview.Heading", font=(familia, 10, "bold"))


def crear_tabla(padre, columnas, alto=12):
    """Crea un Treeview con barra de desplazamiento.
    columnas: lista de (clave, título, ancho). Devuelve (marco, tabla)."""
    marco = ttk.Frame(padre)
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings",
                         height=alto, selectmode="browse")
    for clave, titulo, ancho in columnas:
        tabla.heading(clave, text=titulo, anchor="w")
        tabla.column(clave, width=ancho, minwidth=40, anchor="w")
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    for situacion, color in COLOR_SITUACION.items():
        tabla.tag_configure(etiqueta(situacion), background=color)
    return marco, tabla


def id_seleccionado(tabla):
    """Devuelve el id (de la base) de la fila elegida, o None si no hay ninguna."""
    seleccion = tabla.selection()
    return int(seleccion[0]) if seleccion else None


def llenar_tabla(tabla, filas):
    """filas: lista de (id, valores, situación o None)."""
    tabla.delete(*tabla.get_children())
    for identificador, valores, situacion in filas:
        etiquetas = (etiqueta(situacion),) if situacion else ()
        tabla.insert("", "end", iid=str(identificador), values=valores, tags=etiquetas)


class Dialogo(tk.Toplevel):
    """Ventana secundaria modal (bloquea la principal hasta cerrarse)."""

    def __init__(self, padre, titulo):
        super().__init__(padre)
        self.title(titulo)
        self.resizable(False, False)
        self.configure(background=FONDO)
        self.transient(padre.winfo_toplevel())
        self.cuerpo = ttk.Frame(self, padding=18)
        self.cuerpo.pack(fill="both", expand=True)
        self.bind("<Escape>", lambda _evento: self.destroy())
        self.after_idle(self._hacer_modal)

    def _hacer_modal(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass  # la ventana todavía no está visible; sigue funcionando igual
