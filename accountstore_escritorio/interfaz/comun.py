"""Herramientas compartidas por todas las pantallas: colores de la marca,
estilos, tablas, diálogos y el manejo de errores que evita que el programa
se cierre. Los colores son los mismos de la app AccountStore PY."""
import logging
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from logica.errores import ErrorValidacion, PermisoDenegado

RECURSOS = Path(__file__).resolve().parent / "recursos"

# ---- Paleta de la marca AccountStore PY
MARCA = "#EDB026"           # amarillo de la marca
MARCA_TINTA = "#1F1705"     # texto sobre el amarillo
MARCA_SUAVE = "#FBF0D2"
MARCA_TEXTO = "#8A6100"
PAPEL = "#EEF1EF"           # fondo general
SUPERFICIE = "#FFFFFF"      # tarjetas y tablas
SUPERFICIE_2 = "#F6F8F7"
TINTA = "#16202A"           # texto principal
APAGADO = "#5B6873"         # texto secundario
LINEA = "#DCE2E0"           # bordes
ROJO = "#C2372E"
OSCURO = "#151517"          # menú lateral e inicio de sesión
OSCURO_2 = "#232327"
OSCURO_LINEA = "#2E2E33"
OSCURO_TEXTO = "#EEEAE2"
OSCURO_APAGADO = "#A39E93"
FONDO_LOGIN = "#0B0B0C"

# Situación -> (fondo de la fila, color del texto)
COLOR_SITUACION = {
    "ACTIVO": ("#E1F0E6", "#22613B"),
    "A VENCER": ("#FCEFD3", "#855300"),
    "VENCIDO": ("#FBE4E1", "#9E2920"),
    "BAJA": ("#E8EBEC", "#66727C"),
    "LLENA": ("#FBE4E1", "#9E2920"),
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


def cargar_imagen(nombre):
    """Carga una imagen PNG de interfaz/recursos. Si falta, devuelve None y
    la pantalla se muestra igual, sin la imagen."""
    try:
        return tk.PhotoImage(file=str(RECURSOS / nombre))
    except tk.TclError:
        logging.warning("No se pudo cargar la imagen %s", nombre)
        return None


def _familia_de_letra(raiz):
    disponibles = set(tkfont.families(raiz))
    for familia in ("Segoe UI", "Inter", "Helvetica Neue", "Ubuntu", "DejaVu Sans"):
        if familia in disponibles:
            return familia
    return tkfont.nametofont("TkDefaultFont").actual("family")


def configurar_estilos(raiz):
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    familia = _familia_de_letra(raiz)
    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(nombre).configure(family=familia, size=10)
    raiz.configure(background=PAPEL)
    raiz.option_add("*TCombobox*Listbox.font", (familia, 10))
    raiz.option_add("*TCombobox*Listbox.selectBackground", MARCA)
    raiz.option_add("*TCombobox*Listbox.selectForeground", MARCA_TINTA)

    def letra(tamano, peso="normal"):
        return (familia, tamano, peso)

    # ---- Base
    estilo.configure(".", background=PAPEL, foreground=TINTA, font=letra(10),
                     bordercolor=LINEA, focuscolor=MARCA)
    estilo.configure("TFrame", background=PAPEL)
    estilo.configure("TLabel", background=PAPEL, foreground=TINTA)
    estilo.configure("Titulo.TLabel", font=letra(20, "bold"))
    estilo.configure("Seccion.TLabel", font=letra(13, "bold"))
    estilo.configure("Nota.TLabel", foreground=APAGADO)
    estilo.configure("Resumen.TLabel", font=letra(10, "bold"), background=MARCA_SUAVE,
                     foreground=MARCA_TEXTO, padding=(12, 9))

    # ---- Tarjetas blancas (como en la app)
    estilo.configure("Tarjeta.TFrame", background=SUPERFICIE, relief="solid",
                     borderwidth=1, bordercolor=LINEA)
    estilo.configure("Tarjeta.TLabel", background=SUPERFICIE)
    estilo.configure("TarjetaTitulo.TLabel", background=SUPERFICIE, font=letra(12, "bold"))
    estilo.configure("TarjetaNota.TLabel", background=SUPERFICIE, foreground=APAGADO)
    estilo.configure("KpiTitulo.TLabel", background=SUPERFICIE, foreground=APAGADO, font=letra(9, "bold"))
    for nombre, color in (("Ok", "#1B8A4B"), ("Pronto", "#D4700F"), ("Venc", ROJO),
                          ("Baja", "#66727C"), ("Marca", MARCA_TEXTO)):
        estilo.configure(f"Kpi{nombre}.TLabel", background=SUPERFICIE, foreground=color,
                         font=letra(22, "bold"))

    # ---- Botones
    estilo.configure("TButton", background=SUPERFICIE, foreground=TINTA, bordercolor=LINEA,
                     lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=(14, 7), focusthickness=0)
    estilo.map("TButton", background=[("active", SUPERFICIE_2), ("pressed", LINEA)],
               lightcolor=[("active", SUPERFICIE_2)], darkcolor=[("active", SUPERFICIE_2)])
    estilo.configure("Accion.TButton", background=MARCA, foreground=MARCA_TINTA, bordercolor=MARCA,
                     lightcolor=MARCA, darkcolor=MARCA, font=letra(10, "bold"))
    estilo.map("Accion.TButton", background=[("active", "#E0A41C"), ("pressed", "#C98F12")],
               lightcolor=[("active", "#E0A41C")], darkcolor=[("active", "#E0A41C")])
    estilo.configure("Peligro.TButton", foreground=ROJO)
    estilo.configure("Chip.TButton", padding=(14, 5), bordercolor=LINEA, width=0)
    estilo.configure("ChipActivo.TButton", padding=(14, 5), width=0, background=TINTA, foreground="white",
                     bordercolor=TINTA, lightcolor=TINTA, darkcolor=TINTA)
    estilo.map("ChipActivo.TButton", background=[("active", "#2A3743")],
               lightcolor=[("active", "#2A3743")], darkcolor=[("active", "#2A3743")])

    # ---- Campos de texto
    for nombre in ("TEntry", "TCombobox", "TSpinbox"):
        estilo.configure(nombre, fieldbackground=SUPERFICIE, bordercolor=LINEA, lightcolor=SUPERFICIE,
                         darkcolor=SUPERFICIE, padding=5, arrowcolor=APAGADO, insertcolor=TINTA)
        estilo.map(nombre, bordercolor=[("focus", MARCA)], lightcolor=[("focus", MARCA)])
    estilo.map("TCombobox", fieldbackground=[("readonly", SUPERFICIE)],
               selectbackground=[("readonly", SUPERFICIE)], selectforeground=[("readonly", TINTA)])

    # ---- Tablas
    estilo.configure("Treeview", background=SUPERFICIE, fieldbackground=SUPERFICIE, foreground=TINTA,
                     bordercolor=LINEA, lightcolor=LINEA, darkcolor=LINEA, rowheight=30)
    estilo.map("Treeview", background=[("selected", MARCA)], foreground=[("selected", MARCA_TINTA)])
    estilo.configure("Treeview.Heading", background=SUPERFICIE_2, foreground=APAGADO, relief="flat",
                     bordercolor=LINEA, lightcolor=SUPERFICIE_2, darkcolor=SUPERFICIE_2,
                     font=letra(9, "bold"), padding=(8, 7))
    estilo.map("Treeview.Heading", background=[("active", LINEA)])
    estilo.configure("Vertical.TScrollbar", background=SUPERFICIE_2, troughcolor=SUPERFICIE,
                     bordercolor=SUPERFICIE, lightcolor=SUPERFICIE_2, darkcolor=SUPERFICIE_2,
                     arrowcolor=APAGADO)

    # ---- Menú lateral oscuro
    estilo.configure("Lateral.TFrame", background=OSCURO)
    estilo.configure("Lateral.TLabel", background=OSCURO, foreground=OSCURO_TEXTO)
    estilo.configure("LateralFuerte.TLabel", background=OSCURO, foreground=OSCURO_TEXTO,
                     font=letra(10, "bold"))
    estilo.configure("LateralNota.TLabel", background=OSCURO, foreground=OSCURO_APAGADO, font=letra(9))
    estilo.configure("Nav.TButton", background=OSCURO, foreground=OSCURO_TEXTO, bordercolor=OSCURO,
                     lightcolor=OSCURO, darkcolor=OSCURO, anchor="w", padding=(14, 10), font=letra(10))
    estilo.map("Nav.TButton", background=[("active", OSCURO_2)],
               lightcolor=[("active", OSCURO_2)], darkcolor=[("active", OSCURO_2)])
    estilo.configure("NavActivo.TButton", background=MARCA, foreground=MARCA_TINTA, bordercolor=MARCA,
                     lightcolor=MARCA, darkcolor=MARCA, anchor="w", padding=(14, 10),
                     font=letra(10, "bold"))
    estilo.map("NavActivo.TButton", background=[("active", MARCA)])
    estilo.configure("Salir.TButton", background=OSCURO_2, foreground=OSCURO_TEXTO,
                     bordercolor=OSCURO_LINEA, lightcolor=OSCURO_2, darkcolor=OSCURO_2, padding=(14, 8))
    estilo.map("Salir.TButton", background=[("active", OSCURO_LINEA)],
               lightcolor=[("active", OSCURO_LINEA)], darkcolor=[("active", OSCURO_LINEA)])

    # ---- Inicio de sesión (tarjeta oscura como la pantalla de PIN de la app)
    estilo.configure("Login.TFrame", background=FONDO_LOGIN)
    estilo.configure("LoginTarjeta.TFrame", background=OSCURO, relief="solid", borderwidth=1,
                     bordercolor=OSCURO_LINEA)
    estilo.configure("Login.TLabel", background=OSCURO, foreground=OSCURO_APAGADO)
    estilo.configure("LoginTitulo.TLabel", background=OSCURO, foreground=OSCURO_TEXTO,
                     font=letra(22, "bold"))
    estilo.configure("LoginPie.TLabel", background=OSCURO, foreground="#6E6A62", font=letra(9))
    estilo.configure("Login.TEntry", fieldbackground=OSCURO_2, foreground=OSCURO_TEXTO,
                     insertcolor=OSCURO_TEXTO, bordercolor=OSCURO_LINEA, lightcolor=OSCURO_2,
                     darkcolor=OSCURO_2, padding=9)
    estilo.map("Login.TEntry", bordercolor=[("focus", MARCA)], lightcolor=[("focus", MARCA)])
    estilo.configure("Login.TButton", background=MARCA, foreground=MARCA_TINTA, bordercolor=MARCA,
                     lightcolor=MARCA, darkcolor=MARCA, padding=(14, 12), font=letra(11, "bold"))
    estilo.map("Login.TButton", background=[("active", "#E0A41C")],
               lightcolor=[("active", "#E0A41C")], darkcolor=[("active", "#E0A41C")])


def crear_tabla(padre, columnas, alto=12):
    """Crea un Treeview con barra de desplazamiento.
    columnas: lista de (clave, título, ancho). Devuelve (marco, tabla)."""
    marco = ttk.Frame(padre, style="Tarjeta.TFrame", padding=1)
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings",
                         height=alto, selectmode="browse")
    for clave, titulo, ancho in columnas:
        tabla.heading(clave, text=titulo, anchor="w")
        tabla.column(clave, width=ancho, minwidth=40, anchor="w", stretch=False)

    total = sum(c[2] for c in columnas)
    ultimo = {"ancho": 0}

    def ajustar_columnas(evento):
        """Reparte el ancho disponible entre las columnas, en proporción a su
        ancho original. Así la tabla se adapta a pantallas chicas o grandes."""
        if abs(evento.width - ultimo["ancho"]) < 4:
            return
        ultimo["ancho"] = evento.width
        for clave, _titulo, ancho in columnas:
            tabla.column(clave, width=max(40, int((evento.width - 4) * ancho / total)))

    tabla.bind("<Configure>", ajustar_columnas)
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    for situacion, (fondo, texto) in COLOR_SITUACION.items():
        tabla.tag_configure(etiqueta(situacion), background=fondo, foreground=texto)
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


def tarjeta(padre, titulo=None, padding=16):
    """Marco blanco con borde suave (como las tarjetas de la app)."""
    marco = ttk.Frame(padre, style="Tarjeta.TFrame", padding=padding)
    if titulo:
        ttk.Label(marco, text=titulo, style="TarjetaTitulo.TLabel").pack(anchor="w", pady=(0, 10))
    return marco


def campo(padre, texto, oculto=False, ancho=32):
    """Etiqueta + caja de texto dentro de una tarjeta. Devuelve la caja."""
    ttk.Label(padre, text=texto, style="Tarjeta.TLabel").pack(anchor="w")
    entrada = ttk.Entry(padre, width=ancho, show="•" if oculto else "")
    entrada.pack(fill="x", pady=(3, 10))
    return entrada


class Dialogo(tk.Toplevel):
    """Ventana secundaria modal (bloquea la principal hasta cerrarse)."""

    def __init__(self, padre, titulo):
        super().__init__(padre)
        self.withdraw()          # oculta mientras se arma, para que no aparezca en una esquina
        self.title(titulo)
        self.resizable(False, False)
        self.configure(background=PAPEL)
        self.transient(padre.winfo_toplevel())
        self.cuerpo = ttk.Frame(self, padding=22)
        self.cuerpo.pack(fill="both", expand=True)
        self.bind("<Escape>", lambda _evento: self.destroy())
        self.after_idle(self._mostrar_centrado)   # cuando ya está todo el contenido

    def _mostrar_centrado(self):
        """Ubica el diálogo en el centro de la ventana principal y lo muestra."""
        self.update_idletasks()
        principal = self.master.winfo_toplevel()
        ancho, alto = self.winfo_reqwidth(), self.winfo_reqheight()
        x = principal.winfo_rootx() + (principal.winfo_width() - ancho) // 2
        y = principal.winfo_rooty() + (principal.winfo_height() - alto) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        self.after(50, self._hacer_modal)

    def _hacer_modal(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass  # la ventana todavía no está visible; sigue funcionando igual
