"""Controles con esquinas redondeadas, dibujados en un Canvas.

Tkinter no tiene cajas de texto ni botones redondeados: se dibuja un
rectángulo redondeado en un Canvas y encima se coloca un Entry sin borde.
"""
import math
import tkinter as tk

from interfaz.comun import MARCA, MARCA_TINTA, OSCURO, OSCURO_2, OSCURO_APAGADO, OSCURO_LINEA, OSCURO_TEXTO

MARCA_HOVER = "#E0A41C"


def mezclar(color_a, color_b, t):
    """Color intermedio entre a y b (t=0 -> a, t=1 -> b). Tkinter no tiene
    transparencias, así que se simulan mezclando con el color de fondo."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def curva_bezier(p0, p1, p2, p3, pasos=40):
    """Puntos de una curva de Bézier cúbica (la misma forma que usa el SVG de la app)."""
    puntos = []
    for i in range(pasos + 1):
        t = i / pasos
        u = 1 - t
        for eje in (0, 1):
            puntos.append(u ** 3 * p0[eje] + 3 * u * u * t * p1[eje] + 3 * u * t * t * p2[eje] + t ** 3 * p3[eje])
    return puntos


def dibujar_textura(lienzo, ancho, alto, fondo):
    """Fondo negro con textura, como la app AccountStore PY: brillo amarillo
    suave arriba, curvas tenues y una trama de puntos que se desvanece."""
    lienzo.delete("textura")

    # 1) Brillo amarillo muy suave arriba al centro (elipses del borde hacia el centro)
    rx, ry = ancho * 0.8 * 0.7, alto * 0.5 * 0.7
    pasos = 30
    for i in range(pasos, 0, -1):
        f = i / pasos
        lienzo.create_oval(ancho / 2 - rx * f, -ry * f, ancho / 2 + rx * f, ry * f, outline="",
                           fill=mezclar(fondo, MARCA, 0.08 * (1 - f)), tags="textura")

    # 2) Curvas del fondo de la app (dibujadas para 1600x900 y escaladas a la ventana)
    escala = max(ancho / 1600, alto / 900)
    dx, dy = (ancho - 1600 * escala) / 2, (alto - 900 * escala) / 2

    def punto(x, y):
        return dx + x * escala, dy + y * escala

    zona, linea = mezclar(fondo, "#FFFFFF", 0.018), mezclar(fondo, "#FFFFFF", 0.07)
    for curva, esquina in ((((560, 0), (820, 260), (1120, 120), (1600, 380)), (1600, 0)),
                           (((980, 900), (1120, 640), (1380, 560), (1600, 600)), (1600, 900)),
                           (((0, 480), (220, 560), (360, 720), (430, 900)), (0, 900))):
        puntos = curva_bezier(*(punto(*p) for p in curva)) + list(punto(*esquina))
        lienzo.create_polygon(puntos, fill=zona, outline="", tags="textura")
    for curva in (((760, 0), (1000, 200), (1260, 80), (1600, 260)),
                  ((1160, 900), (1280, 720), (1440, 680), (1600, 700)),
                  ((0, 120), (160, 180), (260, 300), (300, 420))):
        lienzo.create_line(curva_bezier(*(punto(*p) for p in curva)), fill=linea, width=1.2,
                           tags="textura")

    # 3) Trama de puntos cada 18 px, visible solo en tres zonas que se desvanecen
    color_punto = mezclar(fondo, "#FFFFFF", 0.16)
    zonas = [(0.92, 0.14, 340, 260), (0.18, 0.34, 290, 340), (0.70, 0.96, 310, 240)]
    for y in range(9, alto, 18):
        for x in range(9, ancho, 18):
            intensidad = max(1 - math.hypot((x - cx * ancho) / rx_z, (y - cy * alto) / ry_z) / 0.7
                             for cx, cy, rx_z, ry_z in zonas)
            if intensidad > 0.05:
                lienzo.create_oval(x - 1, y - 1, x + 1, y + 1, outline="", tags="textura",
                                   fill=mezclar(fondo, color_punto, intensidad))


def rectangulo_redondeado(lienzo, x0, y0, x1, y1, radio, **opciones):
    """Dibuja un rectángulo con esquinas redondeadas (polígono suavizado)."""
    puntos = [x0 + radio, y0, x1 - radio, y0, x1, y0, x1, y0 + radio,
              x1, y1 - radio, x1, y1, x1 - radio, y1, x0 + radio, y1,
              x0, y1, x0, y1 - radio, x0, y0 + radio, x0, y0]
    return lienzo.create_polygon(puntos, smooth=True, **opciones)


class CampoRedondeado(tk.Canvas):
    """Caja de texto redondeada. Si oculto=True, muestra puntos y un ojo para ver la contraseña."""

    def __init__(self, padre, fuente, ancho=340, alto=46, oculto=False):
        super().__init__(padre, width=ancho, height=alto, bg=OSCURO, highlightthickness=0, bd=0)
        self.borde = rectangulo_redondeado(self, 1, 1, ancho - 2, alto - 2, 12,
                                           fill=OSCURO_2, outline=OSCURO_LINEA, width=1.5)
        self.entrada = tk.Entry(self, bd=0, relief="flat", highlightthickness=0, font=fuente,
                                bg=OSCURO_2, fg=OSCURO_TEXTO, insertbackground=OSCURO_TEXTO,
                                selectbackground=MARCA, selectforeground=MARCA_TINTA,
                                show="•" if oculto else "")
        margen_derecho = 48 if oculto else 16
        self.create_window(16, alto // 2, window=self.entrada, anchor="w",
                           width=ancho - 16 - margen_derecho)
        # Borde amarillo mientras se escribe en el campo
        self.entrada.bind("<FocusIn>", lambda _e: self.itemconfigure(self.borde, outline=MARCA))
        self.entrada.bind("<FocusOut>", lambda _e: self.itemconfigure(self.borde, outline=OSCURO_LINEA))

        self.visible = False
        if oculto:
            self.cx, self.cy = ancho - 28, alto // 2
            self._dibujar_ojo()
            self.tag_bind("ojo", "<Button-1>", self.alternar_visibilidad)
            self.tag_bind("ojo", "<Enter>", lambda _e: self.configure(cursor="hand2"))
            self.tag_bind("ojo", "<Leave>", lambda _e: self.configure(cursor=""))

    def _dibujar_ojo(self):
        """Ojo abierto = 'mostrar contraseña'; ojo tachado = 'ocultarla'."""
        self.delete("ojo")
        x, y = self.cx, self.cy
        color = MARCA if self.visible else OSCURO_APAGADO
        self.create_rectangle(x - 14, y - 14, x + 14, y + 14, fill=OSCURO_2, outline="", tags="ojo")
        self.create_oval(x - 10, y - 6, x + 10, y + 6, outline=color, width=1.6, tags="ojo")
        self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color, tags="ojo")
        if self.visible:
            self.create_line(x - 10, y + 8, x + 10, y - 8, fill=color, width=1.8, tags="ojo")

    def alternar_visibilidad(self, _evento=None):
        self.visible = not self.visible
        self.entrada.configure(show="" if self.visible else "•")
        self._dibujar_ojo()
        self.entrada.focus_set()


class BotonRedondeado(tk.Canvas):
    """Botón amarillo de la marca con esquinas redondeadas."""

    def __init__(self, padre, texto, comando, fuente, ancho=340, alto=50):
        super().__init__(padre, width=ancho, height=alto, bg=OSCURO, highlightthickness=0, bd=0,
                         cursor="hand2")
        self.fondo = rectangulo_redondeado(self, 1, 1, ancho - 2, alto - 2, 14, fill=MARCA, outline=MARCA)
        self.create_text(ancho // 2, alto // 2, text=texto, fill=MARCA_TINTA, font=fuente)
        self.bind("<Button-1>", lambda _e: comando())
        self.bind("<Enter>", lambda _e: self.itemconfigure(self.fondo, fill=MARCA_HOVER, outline=MARCA_HOVER))
        self.bind("<Leave>", lambda _e: self.itemconfigure(self.fondo, fill=MARCA, outline=MARCA))
