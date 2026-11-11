"""Sección Cuentas y servicios: plataformas, sus cuentas y la ocupación de perfiles."""
from tkinter import messagebox, ttk

from interfaz.comun import (campo, crear_tabla, ejecutar_seguro, formato_gs, id_seleccionado,
                            llenar_tabla, tarjeta)

COLUMNAS_SERVICIOS = [("nombre", "Servicio", 120), ("capacidad", "Perfiles", 75),
                      ("precio", "Precio/mes", 105)]
COLUMNAS_CUENTAS = [("servicio", "Servicio", 110), ("correo", "Cuenta", 210),
                    ("ocupados", "Ocupados", 85), ("libres", "Libres", 60)]


class PestanaCuentas(ttk.Frame):
    TITULO = "Cuentas y servicios"
    DESCRIPCION = "Cada cuenta se comparte hasta su capacidad de perfiles. En rojo: cuentas llenas."

    def __init__(self, padre, gestor):
        super().__init__(padre)
        self.gestor = gestor
        self.servicios = []

        # ---- Servicios (izquierda): formulario abajo y tabla arriba
        caja_servicios = tarjeta(self, "Servicios", padding=16)
        caja_servicios.pack(side="left", fill="both", padx=(0, 16))
        formulario = ttk.Frame(caja_servicios, style="Tarjeta.TFrame", borderwidth=0)
        formulario.pack(side="bottom", fill="x", pady=(14, 0))
        self.nombre_servicio = campo(formulario, "Nombre del servicio", ancho=24)
        fila = ttk.Frame(formulario, style="Tarjeta.TFrame", borderwidth=0)
        fila.pack(fill="x")
        ttk.Label(fila, text="Perfiles por cuenta", style="Tarjeta.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(fila, text="Precio por perfil/mes", style="Tarjeta.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0))
        self.capacidad = ttk.Spinbox(fila, from_=1, to=20, width=6)
        self.capacidad.set("5")
        self.capacidad.grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.precio = ttk.Entry(fila, width=14)
        self.precio.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(3, 0))
        botones = ttk.Frame(formulario, style="Tarjeta.TFrame", borderwidth=0)
        botones.pack(fill="x", pady=(12, 0))
        ttk.Button(botones, text="Agregar servicio",
                   command=self.agregar_servicio).pack(side="left", fill="x", expand=True)
        ttk.Button(botones, text="Eliminar", style="Peligro.TButton",
                   command=self.eliminar_servicio).pack(side="left", padx=(8, 0))
        marco, self.tabla_servicios = crear_tabla(caja_servicios, COLUMNAS_SERVICIOS, alto=6)
        marco.pack(fill="both", expand=True)

        # ---- Cuentas (derecha): formulario abajo y tabla arriba
        caja_cuentas = tarjeta(self, "Cuentas y ocupación de perfiles", padding=16)
        caja_cuentas.pack(side="left", fill="both", expand=True)
        formulario = ttk.Frame(caja_cuentas, style="Tarjeta.TFrame", borderwidth=0)
        formulario.pack(side="bottom", fill="x", pady=(14, 0))
        ttk.Label(formulario, text="Servicio", style="Tarjeta.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(formulario, text="Correo de la cuenta", style="Tarjeta.TLabel").grid(
            row=0, column=1, sticky="w", padx=(10, 0))
        self.servicio = ttk.Combobox(formulario, state="readonly", width=14)
        self.servicio.grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.correo = ttk.Entry(formulario, width=26)
        self.correo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(3, 0))
        formulario.columnconfigure(1, weight=1)
        botones = ttk.Frame(formulario, style="Tarjeta.TFrame", borderwidth=0)
        botones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(botones, text="Agregar cuenta",
                   command=self.agregar_cuenta).pack(side="left", fill="x", expand=True)
        ttk.Button(botones, text="Eliminar", style="Peligro.TButton",
                   command=self.eliminar_cuenta).pack(side="left", padx=(8, 0))
        marco, self.tabla_cuentas = crear_tabla(caja_cuentas, COLUMNAS_CUENTAS, alto=6)
        marco.pack(fill="both", expand=True)

    def actualizar(self, _evento=None):
        ok, servicios = ejecutar_seguro(self, self.gestor.listar_servicios)
        if not ok:
            return
        self.servicios = servicios
        llenar_tabla(self.tabla_servicios, [
            (s["id"], (s["nombre"], s["capacidad"], formato_gs(s["precio_mensual"])), None)
            for s in servicios])
        self.servicio.configure(values=[s["nombre"] for s in servicios])

        ok, cuentas = ejecutar_seguro(self, self.gestor.listar_cuentas)
        if ok:
            llenar_tabla(self.tabla_cuentas, [
                (c["id"],
                 (c["servicio"], c["correo"], f"{c['ocupados']} de {c['capacidad']}",
                  "LLENA" if c["libres"] <= 0 else c["libres"]),
                 "LLENA" if c["libres"] <= 0 else None)
                for c in cuentas])

    def agregar_servicio(self):
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_servicio, self.nombre_servicio.get(),
                                self.capacidad.get(), self.precio.get())
        if ok:
            messagebox.showinfo("Servicios", "Servicio agregado.", parent=self)
            self.nombre_servicio.delete(0, "end")
            self.precio.delete(0, "end")
            self.actualizar()

    def eliminar_servicio(self):
        servicio_id = id_seleccionado(self.tabla_servicios)
        if servicio_id is None:
            messagebox.showinfo("Servicios", "Primero seleccione un servicio de la lista.", parent=self)
            return
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "gestionar_cuentas")
        if not ok:
            return
        nombre = self.tabla_servicios.item(str(servicio_id), "values")[0]
        if messagebox.askyesno("Eliminar servicio", f"¿Eliminar el servicio {nombre}?", parent=self):
            ok, _ = ejecutar_seguro(self, self.gestor.eliminar_servicio, servicio_id)
            if ok:
                messagebox.showinfo("Servicios", "Servicio eliminado.", parent=self)
                self.actualizar()

    def eliminar_cuenta(self):
        cuenta_id = id_seleccionado(self.tabla_cuentas)
        if cuenta_id is None:
            messagebox.showinfo("Cuentas", "Primero seleccione una cuenta de la lista.", parent=self)
            return
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "gestionar_cuentas")
        if not ok:
            return
        correo = self.tabla_cuentas.item(str(cuenta_id), "values")[1]
        if messagebox.askyesno("Eliminar cuenta", f"¿Eliminar la cuenta {correo}?", parent=self):
            ok, _ = ejecutar_seguro(self, self.gestor.eliminar_cuenta, cuenta_id)
            if ok:
                messagebox.showinfo("Cuentas", "Cuenta eliminada.", parent=self)
                self.actualizar()

    def agregar_cuenta(self):
        indice = self.servicio.current()
        servicio_id = self.servicios[indice]["id"] if indice >= 0 else None
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_cuenta, servicio_id, self.correo.get())
        if ok:
            messagebox.showinfo("Cuentas", "Cuenta agregada.", parent=self)
            self.correo.delete(0, "end")
            self.actualizar()
