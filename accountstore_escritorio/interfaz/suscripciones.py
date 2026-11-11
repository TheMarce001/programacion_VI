"""Pestaña Suscripciones: el PROCESO PRINCIPAL (vender, renovar, dar de baja)."""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from interfaz.comun import (Dialogo, crear_tabla, ejecutar_seguro, formato_gs,
                            id_seleccionado, llenar_tabla)
from logica.errores import ErrorValidacion
from logica.reglas import MESES_MAXIMOS, fecha_a_texto

SITUACIONES = ["Todos", "ACTIVO", "A VENCER", "VENCIDO", "BAJA"]
COLUMNAS = [
    ("cliente", "Cliente", 150), ("telefono", "Teléfono", 95), ("servicio", "Servicio", 95),
    ("cuenta", "Cuenta", 190), ("perfiles", "Perfiles", 60), ("inicio", "Inicio", 85),
    ("vencimiento", "Vencimiento", 90), ("dias", "Días", 50), ("situacion", "Estado", 85),
]


class PestanaSuscripciones(ttk.Frame):
    def __init__(self, padre, gestor):
        super().__init__(padre, padding=12)
        self.gestor = gestor

        filtros = ttk.Frame(self)
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Buscar (cliente, teléfono o servicio):").pack(side="left")
        self.texto = ttk.Entry(filtros, width=28)
        self.texto.pack(side="left", padx=6)
        self.texto.bind("<Return>", self.actualizar)
        ttk.Label(filtros, text="Estado:").pack(side="left", padx=(10, 4))
        self.situacion = ttk.Combobox(filtros, values=SITUACIONES, state="readonly", width=11)
        self.situacion.set("Todos")
        self.situacion.pack(side="left")
        self.situacion.bind("<<ComboboxSelected>>", self.actualizar)
        ttk.Button(filtros, text="Buscar", command=self.actualizar).pack(side="left", padx=6)
        self.total = ttk.Label(filtros, style="Nota.TLabel")
        self.total.pack(side="right")

        marco, self.tabla = crear_tabla(self, COLUMNAS, alto=15)
        marco.pack(fill="both", expand=True, pady=10)
        self.tabla.bind("<Double-1>", lambda _evento: self.historial())

        botones = ttk.Frame(self)
        botones.pack(fill="x")
        ttk.Button(botones, text="Nueva venta", style="Accion.TButton",
                   command=self.nueva_venta).pack(side="left")
        ttk.Button(botones, text="Renovar", command=self.renovar).pack(side="left", padx=6)
        ttk.Button(botones, text="Dar de baja", command=self.dar_de_baja).pack(side="left")
        ttk.Button(botones, text="Historial de pagos", command=self.historial).pack(side="left", padx=6)
        ttk.Label(botones, text="Verde: activo · Amarillo: vence en 3 días o menos · "
                  "Rojo: vencido · Gris: baja", style="Nota.TLabel").pack(side="right")

    def actualizar(self, _evento=None):
        ok, suscripciones = ejecutar_seguro(self, self.gestor.listar_suscripciones,
                                            self.texto.get(), self.situacion.get())
        if not ok:
            return
        llenar_tabla(self.tabla, [
            (s["id"],
             (s["cliente"], s["telefono"], s["servicio"], s["cuenta"], s["perfiles"],
              fecha_a_texto(s["fecha_inicio"]), fecha_a_texto(s["vencimiento"]),
              "" if s["dias"] is None else s["dias"], s["situacion"]),
             s["situacion"])
            for s in suscripciones])
        self.total.configure(text=f"{len(suscripciones)} suscripción(es)")

    def _seleccion(self):
        suscripcion_id = id_seleccionado(self.tabla)
        if suscripcion_id is None:
            messagebox.showinfo("Suscripciones", "Primero seleccione una suscripción de la lista.",
                                parent=self)
        return suscripcion_id

    def _mostrar(self, suscripcion_id):
        """Después de guardar: recarga la lista y marca la fila afectada."""
        self.texto.delete(0, "end")
        self.situacion.set("Todos")
        self.actualizar()
        if self.tabla.exists(str(suscripcion_id)):
            self.tabla.selection_set(str(suscripcion_id))
            self.tabla.see(str(suscripcion_id))

    def nueva_venta(self):
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "registrar_venta")
        if ok:
            DialogoVenta(self, self.gestor, al_guardar=self._mostrar)

    def renovar(self):
        suscripcion_id = self._seleccion()
        if suscripcion_id is None:
            return
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "renovar")
        if ok:
            ok, _ = ejecutar_seguro(self, self.gestor.cotizar_renovacion, suscripcion_id, 1)
        if ok:
            DialogoRenovar(self, self.gestor, suscripcion_id, al_guardar=self._mostrar)

    def dar_de_baja(self):
        suscripcion_id = self._seleccion()
        if suscripcion_id is None:
            return
        # Primero se consulta el permiso a la LÓGICA (no a la interfaz).
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "dar_de_baja")
        if not ok:
            return
        cliente, _tel, servicio, _cuenta, perfiles = self.tabla.item(str(suscripcion_id), "values")[:5]
        if not messagebox.askyesno(
                "Dar de baja",
                f"¿Dar de baja la suscripción de {cliente} ({servicio})?\n"
                f"Se liberarán {perfiles} perfil(es) de la cuenta.", parent=self):
            return
        ok, _ = ejecutar_seguro(self, self.gestor.dar_de_baja, suscripcion_id)
        if ok:
            messagebox.showinfo("Dar de baja", "La suscripción quedó dada de baja.", parent=self)
            self._mostrar(suscripcion_id)

    def historial(self):
        suscripcion_id = self._seleccion()
        if suscripcion_id is not None:
            ok, pagos = ejecutar_seguro(self, self.gestor.historial_pagos, suscripcion_id)
            if ok:
                VentanaHistorial(self, self.tabla.item(str(suscripcion_id), "values")[0], pagos)


class DialogoVenta(Dialogo):
    """Formulario de una venta nueva (el proceso principal del demo)."""

    def __init__(self, padre, gestor, al_guardar):
        super().__init__(padre, "Nueva venta")
        self.gestor = gestor
        self.al_guardar = al_guardar
        self.clientes = gestor.listar_clientes()
        self.servicios = gestor.listar_servicios()
        self.cuentas = []

        c = self.cuerpo
        ttk.Label(c, text="Registrar venta de perfiles", style="Seccion.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        self.cliente = self._combo(1, "Cliente",
                                   [f"{x['nombre']}  ({x['telefono']})" for x in self.clientes])
        self.servicio = self._combo(2, "Servicio",
                                    [f"{s['nombre']}  —  {formato_gs(s['precio_mensual'])} por perfil/mes"
                                     for s in self.servicios])
        self.cuenta = self._combo(3, "Cuenta", [])
        self.servicio.bind("<<ComboboxSelected>>", self._cargar_cuentas)
        self.cuenta.bind("<<ComboboxSelected>>", self._actualizar_resumen)

        self.perfiles = tk.StringVar(value="1")
        self.meses = tk.StringVar(value="1")
        self.fecha = tk.StringVar(value=fecha_a_texto(date.today()))
        ttk.Label(c, text="Perfiles").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Spinbox(c, from_=1, to=6, textvariable=self.perfiles, width=8).grid(
            row=4, column=1, sticky="w")
        ttk.Label(c, text="Meses").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Spinbox(c, from_=1, to=MESES_MAXIMOS, textvariable=self.meses, width=8).grid(
            row=5, column=1, sticky="w")
        ttk.Label(c, text="Fecha de inicio").grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(c, textvariable=self.fecha, width=12).grid(row=6, column=1, sticky="w")
        ttk.Label(c, text="dd/mm/aaaa", style="Nota.TLabel").grid(row=6, column=2, sticky="w")
        for variable in (self.perfiles, self.meses, self.fecha):
            variable.trace_add("write", self._actualizar_resumen)

        self.resumen = ttk.Label(c, style="Resumen.TLabel")
        self.resumen.grid(row=7, column=0, columnspan=3, sticky="w", pady=(14, 4))

        botones = ttk.Frame(c)
        botones.grid(row=8, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar venta", style="Accion.TButton",
                   command=self.guardar).pack(side="right", padx=6)
        self._actualizar_resumen()

    def _combo(self, fila, texto, valores):
        ttk.Label(self.cuerpo, text=texto).grid(row=fila, column=0, sticky="w", pady=4, padx=(0, 12))
        combo = ttk.Combobox(self.cuerpo, values=valores, state="readonly", width=50)
        combo.grid(row=fila, column=1, columnspan=2, sticky="w", pady=4)
        return combo

    @staticmethod
    def _id_elegido(combo, lista):
        indice = combo.current()
        return lista[indice]["id"] if indice >= 0 else None

    def _cargar_cuentas(self, _evento=None):
        servicio_id = self._id_elegido(self.servicio, self.servicios)
        ok, cuentas = ejecutar_seguro(self, self.gestor.listar_cuentas, servicio_id)
        self.cuentas = cuentas if ok else []
        self.cuenta.configure(values=[
            f"{x['correo']}  —  {x['libres']} libre(s) de {x['capacidad']}" for x in self.cuentas])
        self.cuenta.set("")
        for indice, cuenta in enumerate(self.cuentas):   # propone la primera con lugar
            if cuenta["libres"] > 0:
                self.cuenta.current(indice)
                break
        self._actualizar_resumen()

    def _actualizar_resumen(self, *_):
        cuenta_id = self._id_elegido(self.cuenta, self.cuentas)
        if cuenta_id is None:
            self.resumen.configure(text="Elija el servicio y la cuenta para ver el vencimiento y el monto.")
            return
        try:
            vencimiento, monto = self.gestor.cotizar_venta(
                cuenta_id, self.perfiles.get(), self.meses.get(), self.fecha.get())
            self.resumen.configure(
                text=f"Vence el {fecha_a_texto(vencimiento)}   ·   Monto a cobrar: {formato_gs(monto)}")
        except ErrorValidacion:
            self.resumen.configure(text="Complete perfiles, meses y una fecha válida para ver el resumen.")

    def guardar(self):
        ok, venta = ejecutar_seguro(
            self, self.gestor.registrar_venta,
            self._id_elegido(self.cliente, self.clientes), self._id_elegido(self.cuenta, self.cuentas),
            self.perfiles.get(), self.meses.get(), self.fecha.get())
        if not ok:
            return          # el formulario queda abierto para corregir; no se guardó nada
        messagebox.showinfo("Venta registrada",
                            "La venta se guardó correctamente.\n\n"
                            f"Vence el {fecha_a_texto(venta['vencimiento'])}\n"
                            f"Monto cobrado: {formato_gs(venta['monto'])}", parent=self)
        self.destroy()
        self.al_guardar(venta["id"])


class DialogoRenovar(Dialogo):
    def __init__(self, padre, gestor, suscripcion_id, al_guardar):
        super().__init__(padre, "Renovar suscripción")
        self.gestor = gestor
        self.suscripcion_id = suscripcion_id
        self.al_guardar = al_guardar
        s = gestor.obtener_suscripcion(suscripcion_id)

        c = self.cuerpo
        ttk.Label(c, text="Renovar suscripción", style="Seccion.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        datos = [("Cliente", s["cliente"]), ("Servicio", f"{s['servicio']}  ({s['cuenta']})"),
                 ("Perfiles", s["perfiles"]), ("Vence actualmente", fecha_a_texto(s["vencimiento"]))]
        for fila, (titulo, valor) in enumerate(datos, start=1):
            ttk.Label(c, text=titulo).grid(row=fila, column=0, sticky="w", pady=2, padx=(0, 12))
            ttk.Label(c, text=valor).grid(row=fila, column=1, sticky="w", pady=2)

        self.meses = tk.StringVar(value="1")
        ttk.Label(c, text="Meses a renovar").grid(row=5, column=0, sticky="w", pady=(10, 2))
        ttk.Spinbox(c, from_=1, to=MESES_MAXIMOS, textvariable=self.meses, width=8).grid(
            row=5, column=1, sticky="w", pady=(10, 2))
        self.meses.trace_add("write", self._actualizar_resumen)
        self.resumen = ttk.Label(c, style="Resumen.TLabel")
        self.resumen.grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 4))
        ttk.Label(c, text="Si todavía no venció, se renueva desde su vencimiento; si ya venció, desde hoy.",
                  style="Nota.TLabel").grid(row=7, column=0, columnspan=2, sticky="w")

        botones = ttk.Frame(c)
        botones.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar renovación", style="Accion.TButton",
                   command=self.guardar).pack(side="right", padx=6)
        self._actualizar_resumen()

    def _actualizar_resumen(self, *_):
        try:
            datos = self.gestor.cotizar_renovacion(self.suscripcion_id, self.meses.get())
            self.resumen.configure(text=f"Nuevo vencimiento: {fecha_a_texto(datos['vencimiento'])}   ·   "
                                        f"Monto: {formato_gs(datos['monto'])}")
        except ErrorValidacion as error:
            self.resumen.configure(text=str(error))

    def guardar(self):
        ok, datos = ejecutar_seguro(self, self.gestor.renovar, self.suscripcion_id, self.meses.get())
        if ok:
            messagebox.showinfo("Renovación registrada",
                                f"Nuevo vencimiento: {fecha_a_texto(datos['vencimiento'])}\n"
                                f"Monto cobrado: {formato_gs(datos['monto'])}", parent=self)
            self.destroy()
            self.al_guardar(self.suscripcion_id)


class VentanaHistorial(Dialogo):
    def __init__(self, padre, cliente, pagos):
        super().__init__(padre, "Historial de pagos")
        ttk.Label(self.cuerpo, text=f"Pagos de {cliente}", style="Seccion.TLabel").pack(anchor="w")
        columnas = [("fecha", "Fecha", 90), ("concepto", "Concepto", 100), ("meses", "Meses", 60),
                    ("monto", "Monto", 110), ("usuario", "Registrado por", 160)]
        marco, tabla = crear_tabla(self.cuerpo, columnas, alto=8)
        marco.pack(fill="both", expand=True, pady=10)
        llenar_tabla(tabla, [
            (indice, (fecha_a_texto(p["fecha"]), p["concepto"], p["meses"], formato_gs(p["monto"]),
                      p["registrado_por"]), None)
            for indice, p in enumerate(pagos)])
        total = sum(p["monto"] for p in pagos)
        ttk.Label(self.cuerpo, text=f"Total cobrado: {formato_gs(total)}",
                  style="Resumen.TLabel").pack(anchor="w")
        ttk.Button(self.cuerpo, text="Cerrar", command=self.destroy).pack(anchor="e", pady=(10, 0))
