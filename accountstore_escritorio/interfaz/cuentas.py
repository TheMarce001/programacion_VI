"""Pestaña Cuentas y servicios: plataformas, sus cuentas y la ocupación de perfiles."""
from tkinter import messagebox, ttk

from interfaz.comun import crear_tabla, ejecutar_seguro, formato_gs, llenar_tabla

COLUMNAS_SERVICIOS = [("nombre", "Servicio", 160), ("capacidad", "Perfiles por cuenta", 140),
                      ("precio", "Precio por perfil/mes", 160)]
COLUMNAS_CUENTAS = [("servicio", "Servicio", 140), ("correo", "Cuenta", 240),
                    ("ocupados", "Ocupados", 90), ("libres", "Libres", 80), ("situacion", "Situación", 100)]


class PestanaCuentas(ttk.Frame):
    def __init__(self, padre, gestor):
        super().__init__(padre, padding=12)
        self.gestor = gestor
        self.servicios = []

        # ---- Servicios
        caja_servicios = ttk.LabelFrame(self, text="Servicios", padding=10)
        caja_servicios.pack(fill="x")
        marco, self.tabla_servicios = crear_tabla(caja_servicios, COLUMNAS_SERVICIOS, alto=5)
        marco.pack(fill="x")
        fila = ttk.Frame(caja_servicios)
        fila.pack(fill="x", pady=(8, 0))
        ttk.Label(fila, text="Nombre").pack(side="left")
        self.nombre_servicio = ttk.Entry(fila, width=18)
        self.nombre_servicio.pack(side="left", padx=(4, 12))
        ttk.Label(fila, text="Perfiles por cuenta").pack(side="left")
        self.capacidad = ttk.Spinbox(fila, from_=1, to=20, width=5)
        self.capacidad.set("5")
        self.capacidad.pack(side="left", padx=(4, 12))
        ttk.Label(fila, text="Precio por perfil/mes (Gs.)").pack(side="left")
        self.precio = ttk.Entry(fila, width=10)
        self.precio.pack(side="left", padx=(4, 12))
        ttk.Button(fila, text="Agregar servicio", command=self.agregar_servicio).pack(side="left")

        # ---- Cuentas
        caja_cuentas = ttk.LabelFrame(self, text="Cuentas y ocupación de perfiles", padding=10)
        caja_cuentas.pack(fill="both", expand=True, pady=(12, 0))
        marco, self.tabla_cuentas = crear_tabla(caja_cuentas, COLUMNAS_CUENTAS, alto=8)
        marco.pack(fill="both", expand=True)
        fila = ttk.Frame(caja_cuentas)
        fila.pack(fill="x", pady=(8, 0))
        ttk.Label(fila, text="Servicio").pack(side="left")
        self.servicio = ttk.Combobox(fila, state="readonly", width=16)
        self.servicio.pack(side="left", padx=(4, 12))
        ttk.Label(fila, text="Correo de la cuenta").pack(side="left")
        self.correo = ttk.Entry(fila, width=30)
        self.correo.pack(side="left", padx=(4, 12))
        ttk.Button(fila, text="Agregar cuenta", command=self.agregar_cuenta).pack(side="left")

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
            filas = []
            for c in cuentas:
                situacion = "LLENA" if c["libres"] <= 0 else "Disponible"
                filas.append((c["id"], (c["servicio"], c["correo"], f"{c['ocupados']} de {c['capacidad']}",
                                        c["libres"], situacion),
                              "LLENA" if situacion == "LLENA" else None))
            llenar_tabla(self.tabla_cuentas, filas)

    def agregar_servicio(self):
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_servicio, self.nombre_servicio.get(),
                                self.capacidad.get(), self.precio.get())
        if ok:
            messagebox.showinfo("Servicios", "Servicio agregado.", parent=self)
            self.nombre_servicio.delete(0, "end")
            self.precio.delete(0, "end")
            self.actualizar()

    def agregar_cuenta(self):
        indice = self.servicio.current()
        servicio_id = self.servicios[indice]["id"] if indice >= 0 else None
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_cuenta, servicio_id, self.correo.get())
        if ok:
            messagebox.showinfo("Cuentas", "Cuenta agregada.", parent=self)
            self.correo.delete(0, "end")
            self.actualizar()
