"""Sección Suscripciones: el PROCESO PRINCIPAL (vender, renovar, dar de baja)."""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from interfaz.comun import (Dialogo, crear_tabla, ejecutar_seguro, formato_gs,
                            id_seleccionado, llenar_tabla, tarjeta)
from logica.errores import ErrorValidacion
from logica.reglas import MESES_MAXIMOS, TIPOS_DESCUENTO, fecha_a_texto

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
# Filtros (chips): valor -> texto del botón
FILTROS = {"Todos": "Todas", "ACTIVO": "Activas", "A VENCER": "A vencer",
           "VENCIDO": "Vencidas", "BAJA": "Bajas"}
COLUMNAS = [
    ("cliente", "Cliente", 150), ("servicio", "Servicio", 100), ("cuenta", "Cuenta", 200),
    ("perfiles", "Perfiles", 75), ("inicio", "Inicio", 95), ("vencimiento", "Vence", 95),
    ("dias", "Días", 55), ("situacion", "Estado", 95),
]


class PestanaSuscripciones(ttk.Frame):
    TITULO = "Suscripciones"
    DESCRIPCION = "Ventas, vencimientos y renovaciones de perfiles."

    def __init__(self, padre, gestor):
        super().__init__(padre)
        self.gestor = gestor
        self.situacion = "Todos"

        # ---- Tarjetas de resumen
        indicadores = ttk.Frame(self)
        indicadores.pack(fill="x")
        self.kpi = {}
        datos = [("ACTIVO", "ACTIVAS", "KpiOk", "más de 3 días", 1),
                 ("A VENCER", "A VENCER", "KpiPronto", "3 días o menos", 1),
                 ("VENCIDO", "VENCIDAS", "KpiVenc", "para renovar", 1),
                 ("COBRADO", f"COBRADO EN {MESES[date.today().month - 1].upper()}", "KpiMarca",
                  "ventas y renovaciones", 2)]
        for columna, (clave, titulo, estilo, nota, peso) in enumerate(datos):
            caja = tarjeta(indicadores, padding=(16, 12))
            caja.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 12, 0))
            indicadores.columnconfigure(columna, weight=peso, uniform="kpi")
            ttk.Label(caja, text=titulo, style="KpiTitulo.TLabel").pack(anchor="w")
            self.kpi[clave] = ttk.Label(caja, text="0", style=f"{estilo}.TLabel")
            self.kpi[clave].pack(anchor="w")
            ttk.Label(caja, text=nota, style="TarjetaNota.TLabel").pack(anchor="w")

        # ---- Filtros (chips) y buscador
        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(16, 10))
        self.chips = {}
        for valor in FILTROS:
            chip = ttk.Button(filtros, style="Chip.TButton", command=lambda v=valor: self.filtrar(v))
            chip.pack(side="left", padx=(0, 6))
            self.chips[valor] = chip
        ttk.Button(filtros, text="Buscar", command=self.actualizar).pack(side="right")
        self.texto = ttk.Entry(filtros, width=22)       # busca por cliente, teléfono o servicio
        self.texto.pack(side="right", padx=6, fill="x", expand=True)
        self.texto.bind("<Return>", self.actualizar)

        # ---- Acciones (se ubican abajo ANTES de la tabla, para que nunca queden tapadas)
        botones = ttk.Frame(self)
        botones.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(botones, text="+  Nueva venta", style="Accion.TButton",
                   command=self.nueva_venta).pack(side="left")
        ttk.Button(botones, text="Renovar", command=self.renovar).pack(side="left", padx=8)
        ttk.Button(botones, text="Historial de pagos", command=self.historial).pack(side="left")
        ttk.Button(botones, text="Dar de baja", style="Peligro.TButton",
                   command=self.dar_de_baja).pack(side="right")

        # ---- Tabla (ocupa el espacio que queda)
        marco, self.tabla = crear_tabla(self, COLUMNAS, alto=9)
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda _evento: self.historial())

    def filtrar(self, situacion):
        self.situacion = situacion
        self.actualizar()

    def actualizar(self, _evento=None):
        ok, resumen = ejecutar_seguro(self, self.gestor.resumen)
        if not ok:
            return
        cantidades = resumen["cantidades"]
        for clave in ("ACTIVO", "A VENCER", "VENCIDO"):
            self.kpi[clave].configure(text=cantidades[clave])
        self.kpi["COBRADO"].configure(text=formato_gs(resumen["cobrado_mes"]))
        for valor, chip in self.chips.items():
            cantidad = resumen["total"] if valor == "Todos" else cantidades[valor]
            chip.configure(text=f"{FILTROS[valor]}  {cantidad}",
                           style="ChipActivo.TButton" if valor == self.situacion else "Chip.TButton")

        ok, suscripciones = ejecutar_seguro(self, self.gestor.listar_suscripciones,
                                            self.texto.get(), self.situacion)
        if ok:
            llenar_tabla(self.tabla, [
                (s["id"],
                 (s["cliente"], s["servicio"], s["cuenta"], s["perfiles"],
                  fecha_a_texto(s["fecha_inicio"]), fecha_a_texto(s["vencimiento"]),
                  "" if s["dias"] is None else s["dias"], s["situacion"]),
                 s["situacion"])
                for s in suscripciones])

    def _seleccion(self):
        suscripcion_id = id_seleccionado(self.tabla)
        if suscripcion_id is None:
            messagebox.showinfo("Suscripciones", "Primero seleccione una suscripción de la lista.",
                                parent=self)
        return suscripcion_id

    def _mostrar(self, suscripcion_id):
        """Después de guardar: recarga la lista y marca la fila afectada."""
        self.texto.delete(0, "end")
        self.situacion = "Todos"
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
        cliente, servicio, _cuenta, perfiles = self.tabla.item(str(suscripcion_id), "values")[:4]
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


def texto_resumen(datos):
    """Texto del recuadro amarillo: vencimiento y lo que se va a cobrar."""
    linea = f"Vence el {fecha_a_texto(datos['vencimiento'])}"
    if datos["descuento"]:
        return (f"{linea}\nSubtotal {formato_gs(datos['subtotal'])}  −  descuento "
                f"{formato_gs(datos['descuento'])}  =  Total a cobrar: {formato_gs(datos['monto'])}")
    return f"{linea}\nTotal a cobrar: {formato_gs(datos['monto'])}"


def dos_lineas(texto):
    """Mantiene el recuadro siempre con dos líneas para que el diálogo no cambie de alto."""
    return texto if "\n" in texto else texto + "\n"


class CampoDescuento(ttk.Frame):
    """Descuento opcional: un número y si es en Gs. o en %, como en la app de ventas."""

    def __init__(self, padre, al_cambiar):
        super().__init__(padre)
        self.tipo = "Gs."
        self.al_cambiar = al_cambiar
        self.valor = tk.StringVar()
        ttk.Entry(self, textvariable=self.valor, width=12).pack(side="left")
        self.botones = {}
        for tipo in TIPOS_DESCUENTO:
            boton = ttk.Button(self, text=tipo, command=lambda t=tipo: self.elegir(t))
            boton.pack(side="left", padx=(6, 0))
            self.botones[tipo] = boton
        ttk.Label(self, text="opcional", style="Nota.TLabel").pack(side="left", padx=(10, 0))
        self._pintar()
        self.valor.trace_add("write", lambda *_: self.al_cambiar())

    def _pintar(self):
        for tipo, boton in self.botones.items():
            boton.configure(style="ChipActivo.TButton" if tipo == self.tipo else "Chip.TButton")

    def elegir(self, tipo):
        self.tipo = tipo
        self._pintar()
        self.al_cambiar()


class DialogoVenta(Dialogo):
    """Formulario de una venta nueva (el proceso principal del demo)."""

    def __init__(self, padre, gestor, al_guardar):
        super().__init__(padre, "Nueva venta")
        self.gestor = gestor
        self.al_guardar = al_guardar
        self.servicios = gestor.listar_servicios()
        self.cuentas = []

        c = self.cuerpo
        ttk.Label(c, text="Nueva venta", style="Seccion.TLabel").grid(row=0, column=0, columnspan=2,
                                                                    sticky="w", pady=(0, 8))

        # ---- Cliente: buscador + lista que se filtra mientras se escribe
        ttk.Label(c, text="Cliente").grid(row=2, column=0, sticky="nw", pady=(10, 5), padx=(0, 14))
        caja = ttk.Frame(c)
        caja.grid(row=2, column=1, sticky="ew", pady=5)
        self.buscar = ttk.Entry(caja)
        self.buscar.pack(fill="x")
        ttk.Label(caja, text="Escriba parte del nombre o del teléfono y elija de la lista.",
                  style="Nota.TLabel").pack(anchor="w", pady=(3, 4))
        marco, self.tabla_clientes = crear_tabla(caja, [("nombre", "Nombre", 240), ("telefono", "Teléfono", 150)],
                                                 alto=3)
        marco.pack(fill="x")
        self.buscar.bind("<KeyRelease>", self._filtrar_clientes)
        self.buscar.bind("<Return>", self._elegir_primero)

        self.servicio = self._combo(3, "Servicio",
                                    [f"{s['nombre']}  —  {formato_gs(s['precio_mensual'])} por perfil/mes"
                                     for s in self.servicios])
        self.cuenta = self._combo(4, "Cuenta", [])
        self.servicio.bind("<<ComboboxSelected>>", self._cargar_cuentas)
        self.cuenta.bind("<<ComboboxSelected>>", self._actualizar_resumen)

        # ---- Perfiles, meses y fecha en una fila
        self.perfiles = tk.StringVar(value="1")
        self.meses = tk.StringVar(value="1")
        self.fecha = tk.StringVar(value=fecha_a_texto(date.today()))
        ttk.Label(c, text="Perfiles").grid(row=5, column=0, sticky="w", pady=5)
        fila = ttk.Frame(c)
        fila.grid(row=5, column=1, sticky="w", pady=5)
        ttk.Spinbox(fila, from_=1, to=6, textvariable=self.perfiles, width=5).pack(side="left")
        ttk.Label(fila, text="Meses").pack(side="left", padx=(16, 6))
        ttk.Spinbox(fila, from_=1, to=MESES_MAXIMOS, textvariable=self.meses, width=5).pack(side="left")
        ttk.Label(fila, text="Inicio").pack(side="left", padx=(16, 6))
        ttk.Entry(fila, textvariable=self.fecha, width=11).pack(side="left")
        ttk.Label(fila, text="dd/mm/aaaa", style="Nota.TLabel").pack(side="left", padx=(6, 0))
        for variable in (self.perfiles, self.meses, self.fecha):
            variable.trace_add("write", self._actualizar_resumen)

        ttk.Label(c, text="Descuento").grid(row=6, column=0, sticky="w", pady=5)
        self.resumen = ttk.Label(c, style="Resumen.TLabel", wraplength=520, justify="left")
        self.descuento = CampoDescuento(c, self._actualizar_resumen)
        self.descuento.grid(row=6, column=1, sticky="w", pady=5)
        self.resumen.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 4))

        botones = ttk.Frame(c)
        botones.grid(row=8, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar venta", style="Accion.TButton",
                   command=self.guardar).pack(side="right", padx=8)
        self._filtrar_clientes()
        self._actualizar_resumen()
        self.buscar.focus_set()

    def _combo(self, fila, texto, valores):
        ttk.Label(self.cuerpo, text=texto).grid(row=fila, column=0, sticky="w", pady=5, padx=(0, 14))
        combo = ttk.Combobox(self.cuerpo, values=valores, state="readonly", width=50)
        combo.grid(row=fila, column=1, sticky="w", pady=5)
        return combo

    @staticmethod
    def _id_elegido(combo, lista):
        indice = combo.current()
        return lista[indice]["id"] if indice >= 0 else None

    def _filtrar_clientes(self, _evento=None):
        """Busca en la base los clientes que coinciden con lo escrito (nombre o teléfono)."""
        elegido = id_seleccionado(self.tabla_clientes)
        ok, clientes = ejecutar_seguro(self, self.gestor.listar_clientes, self.buscar.get())
        if not ok:
            return
        llenar_tabla(self.tabla_clientes, [(x["id"], (x["nombre"], x["telefono"]), None) for x in clientes])
        if elegido is not None and self.tabla_clientes.exists(str(elegido)):
            self.tabla_clientes.selection_set(str(elegido))       # se mantiene el ya elegido
        elif len(clientes) == 1:
            self.tabla_clientes.selection_set(str(clientes[0]["id"]))  # un solo resultado: se elige solo

    def _elegir_primero(self, _evento=None):
        filas = self.tabla_clientes.get_children()
        if filas:
            self.tabla_clientes.selection_set(filas[0])
            self.tabla_clientes.see(filas[0])

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
            self.resumen.configure(text=dos_lineas("Elija el servicio y la cuenta para ver el vencimiento y el monto."))
            return
        try:
            datos = self.gestor.cotizar_venta(cuenta_id, self.perfiles.get(), self.meses.get(), self.fecha.get(),
                                              self.descuento.valor.get(), self.descuento.tipo)
            self.resumen.configure(text=texto_resumen(datos))
        except ErrorValidacion as error:
            self.resumen.configure(text=dos_lineas(str(error)))

    def guardar(self):
        ok, venta = ejecutar_seguro(
            self, self.gestor.registrar_venta,
            id_seleccionado(self.tabla_clientes), self._id_elegido(self.cuenta, self.cuentas),
            self.perfiles.get(), self.meses.get(), self.fecha.get(),
            self.descuento.valor.get(), self.descuento.tipo)
        if not ok:
            return          # el formulario queda abierto para corregir; no se guardó nada
        detalle = f"Vence el {fecha_a_texto(venta['vencimiento'])}\n"
        if venta["descuento"]:
            detalle += f"Descuento: {formato_gs(venta['descuento'])}\n"
        detalle += f"Monto cobrado: {formato_gs(venta['monto'])}"
        messagebox.showinfo("Venta registrada", "La venta se guardó correctamente.\n\n" + detalle, parent=self)
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
            ttk.Label(c, text=titulo, style="Nota.TLabel").grid(row=fila, column=0, sticky="w",
                                                               pady=2, padx=(0, 14))
            ttk.Label(c, text=valor).grid(row=fila, column=1, sticky="w", pady=2)

        self.meses = tk.StringVar(value="1")
        ttk.Label(c, text="Meses a renovar").grid(row=5, column=0, sticky="w", pady=(12, 2))
        ttk.Spinbox(c, from_=1, to=MESES_MAXIMOS, textvariable=self.meses, width=8).grid(
            row=5, column=1, sticky="w", pady=(12, 2))
        self.meses.trace_add("write", self._actualizar_resumen)
        ttk.Label(c, text="Descuento").grid(row=6, column=0, sticky="w", pady=5)
        self.resumen = ttk.Label(c, style="Resumen.TLabel", wraplength=480, justify="left")
        self.descuento = CampoDescuento(c, self._actualizar_resumen)
        self.descuento.grid(row=6, column=1, sticky="w", pady=5)
        self.resumen.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 6))
        ttk.Label(c, text="Si todavía no venció, se renueva desde su vencimiento; si ya venció, desde hoy.",
                  style="Nota.TLabel").grid(row=8, column=0, columnspan=2, sticky="w")

        botones = ttk.Frame(c)
        botones.grid(row=9, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar renovación", style="Accion.TButton",
                   command=self.guardar).pack(side="right", padx=8)
        self._actualizar_resumen()

    def _actualizar_resumen(self, *_):
        try:
            datos = self.gestor.cotizar_renovacion(self.suscripcion_id, self.meses.get(),
                                                   self.descuento.valor.get(), self.descuento.tipo)
            self.resumen.configure(text=texto_resumen(datos).replace("Vence el", "Nuevo vencimiento:"))
        except ErrorValidacion as error:
            self.resumen.configure(text=dos_lineas(str(error)))

    def guardar(self):
        ok, datos = ejecutar_seguro(self, self.gestor.renovar, self.suscripcion_id, self.meses.get(),
                                    self.descuento.valor.get(), self.descuento.tipo)
        if ok:
            detalle = f"Nuevo vencimiento: {fecha_a_texto(datos['vencimiento'])}\n"
            if datos["descuento"]:
                detalle += f"Descuento: {formato_gs(datos['descuento'])}\n"
            detalle += f"Monto cobrado: {formato_gs(datos['monto'])}"
            messagebox.showinfo("Renovación registrada", detalle, parent=self)
            self.destroy()
            self.al_guardar(self.suscripcion_id)


class VentanaHistorial(Dialogo):
    def __init__(self, padre, cliente, pagos):
        super().__init__(padre, "Historial de pagos")
        ttk.Label(self.cuerpo, text=f"Pagos de {cliente}", style="Seccion.TLabel").pack(anchor="w")
        columnas = [("fecha", "Fecha", 95), ("concepto", "Concepto", 105), ("meses", "Meses", 60),
                    ("descuento", "Descuento", 105), ("monto", "Cobrado", 115), ("usuario", "Registrado por", 160)]
        marco, tabla = crear_tabla(self.cuerpo, columnas, alto=7)
        marco.pack(fill="both", expand=True, pady=12)
        llenar_tabla(tabla, [
            (indice, (fecha_a_texto(p["fecha"]), p["concepto"], p["meses"],
                      formato_gs(p["descuento"]) if p["descuento"] else "-",
                      formato_gs(p["monto"]), p["registrado_por"]), None)
            for indice, p in enumerate(pagos)])
        total = sum(p["monto"] for p in pagos)
        ttk.Label(self.cuerpo, text=f"Total cobrado: {formato_gs(total)}",
                  style="Resumen.TLabel").pack(fill="x")
        ttk.Button(self.cuerpo, text="Cerrar", command=self.destroy).pack(anchor="e", pady=(12, 0))
