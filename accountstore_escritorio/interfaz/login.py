"""Pantalla de inicio de sesión: tarjeta oscura redondeada con el logo, como
la pantalla de PIN de la app AccountStore PY."""
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import messagebox
from urllib.parse import quote

from interfaz.comun import (FONDO_LOGIN, MARCA, OSCURO, OSCURO_APAGADO,
                            OSCURO_TEXTO, cargar_imagen)
from interfaz.widgets import BotonRedondeado, CampoRedondeado, dibujar_textura, rectangulo_redondeado
from logica.errores import ErrorValidacion

VERSION = "1.0 (12/11/2026)"
# WhatsApp del administrador (el mismo que usa la app AccountStore PY para pedir el PIN).
WHATSAPP_ADMIN = "595983404727"
ROJO_ERROR = "#E0584E"


def enlace_whatsapp(numero, mensaje):
    """Arma el enlace wa.me que abre un chat con el mensaje ya escrito."""
    return f"https://wa.me/{numero}?text={quote(mensaje)}"


class PantallaLogin(tk.Frame):
    def __init__(self, padre, gestor, al_ingresar):
        super().__init__(padre, bg=FONDO_LOGIN)
        self.gestor = gestor
        self.al_ingresar = al_ingresar

        familia = tkfont.nametofont("TkDefaultFont").actual("family")
        f_titulo = tkfont.Font(family=familia, size=22, weight="bold")
        f_texto = tkfont.Font(family=familia, size=10)
        f_campo = tkfont.Font(family=familia, size=11)
        f_boton = tkfont.Font(family=familia, size=11, weight="bold")
        f_enlace = tkfont.Font(family=familia, size=10, underline=True)
        f_pie = tkfont.Font(family=familia, size=9)

        # El fondo y la tarjeta redondeada se dibujan en un Canvas
        self.lienzo = tk.Canvas(self, bg=FONDO_LOGIN, highlightthickness=0, bd=0)
        self.lienzo.pack(fill="both", expand=True)
        self.tarjeta = tk.Frame(self.lienzo, bg=OSCURO)
        self.ventana_tarjeta = self.lienzo.create_window(0, 0, window=self.tarjeta)

        def texto(contenido, color=OSCURO_APAGADO, fuente=f_texto):
            return tk.Label(self.tarjeta, text=contenido, bg=OSCURO, fg=color, font=fuente)

        self.logo = cargar_imagen("logo_login.png")      # se guarda para que no se borre
        if self.logo:
            tk.Label(self.tarjeta, image=self.logo, bg=OSCURO).pack(pady=(0, 14))
        texto("Hola de nuevo", OSCURO_TEXTO, f_titulo).pack()
        texto("Ingrese su usuario y contraseña para continuar.").pack(pady=(2, 20))

        texto("Usuario").pack(anchor="w", pady=(0, 5))
        self.campo_usuario = CampoRedondeado(self.tarjeta, f_campo)
        self.campo_usuario.pack(pady=(0, 14))
        texto("Contraseña").pack(anchor="w", pady=(0, 5))
        self.campo_clave = CampoRedondeado(self.tarjeta, f_campo, oculto=True)
        self.campo_clave.pack()
        self.usuario = self.campo_usuario.entrada
        self.clave = self.campo_clave.entrada

        self.error = texto("", ROJO_ERROR)            # aquí aparece "Usuario o contraseña incorrectos"
        self.error.configure(wraplength=340, justify="center")
        self.error.pack(pady=(10, 0))

        ayuda = tk.Frame(self.tarjeta, bg=OSCURO)
        ayuda.pack(pady=(4, 16))
        tk.Label(ayuda, text="¿Olvidó su contraseña?", bg=OSCURO, fg=OSCURO_APAGADO,
                 font=f_texto).pack(side="left")
        enlace = tk.Label(ayuda, text="Pídasela al administrador", bg=OSCURO, fg=MARCA,
                          font=f_enlace, cursor="hand2")
        enlace.pack(side="left", padx=(5, 0))
        enlace.bind("<Button-1>", self.pedir_contrasena)

        BotonRedondeado(self.tarjeta, "Entrar", self.ingresar, f_boton).pack()
        texto(f"AccountStore Escritorio · versión {VERSION}", "#6E6A62", f_pie).pack(pady=(16, 0))

        self.tamano = None
        self.lienzo.bind("<Configure>", self._dibujar_tarjeta)
        self.usuario.bind("<Return>", lambda _e: self.clave.focus_set())
        self.clave.bind("<Return>", self.ingresar)
        for entrada in (self.usuario, self.clave):
            entrada.bind("<Key>", lambda _e: self.error.configure(text=""), add="+")
        self.usuario.focus_set()

    def _dibujar_tarjeta(self, _evento=None):
        """Dibuja el fondo con textura, centra la tarjeta y dibuja detrás su fondo redondeado."""
        ancho, alto = self.lienzo.winfo_width(), self.lienzo.winfo_height()
        if (ancho, alto) == self.tamano:
            return
        self.tamano = (ancho, alto)
        dibujar_textura(self.lienzo, ancho, alto, FONDO_LOGIN)
        self.tarjeta.update_idletasks()
        t_ancho, t_alto = self.tarjeta.winfo_reqwidth(), self.tarjeta.winfo_reqheight()
        margen = 36
        x0 = (ancho - t_ancho) // 2 - margen
        y0 = (alto - t_alto) // 2 - margen
        self.lienzo.delete("fondo")
        rectangulo_redondeado(self.lienzo, x0, y0, x0 + t_ancho + 2 * margen, y0 + t_alto + 2 * margen,
                              28, fill=OSCURO, outline="#242427", width=1, tags="fondo")
        self.lienzo.tag_raise("fondo")                 # la tarjeta queda sobre la textura
        self.lienzo.coords(self.ventana_tarjeta, ancho // 2, alto // 2)

    def ingresar(self, _evento=None):
        try:
            self.gestor.iniciar_sesion(self.usuario.get(), self.clave.get())
        except ErrorValidacion as error:
            # Usuario o contraseña incorrectos: se avisa dentro de la tarjeta, como en la app
            self.error.configure(text=str(error))
            self.clave.delete(0, "end")
            self.clave.focus_set()
            return
        self.al_ingresar()

    def pedir_contrasena(self, _evento=None):
        """Abre WhatsApp con un mensaje para pedirle la contraseña al administrador."""
        usuario = self.usuario.get().strip()
        mensaje = "Hola, olvidé mi contraseña de AccountStore Escritorio."
        if usuario:
            mensaje += f" Mi usuario es: {usuario}."
        try:
            webbrowser.open(enlace_whatsapp(WHATSAPP_ADMIN, mensaje))
        except Exception:
            messagebox.showinfo("Olvidé mi contraseña",
                                f"Escríbale al administrador por WhatsApp al +{WHATSAPP_ADMIN}.",
                                parent=self)
