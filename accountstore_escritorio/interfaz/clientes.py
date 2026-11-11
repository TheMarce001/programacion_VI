"""Pestaña Clientes: alta, búsqueda y eliminación de clientes."""
from tkinter import messagebox, ttk

from interfaz.comun import crear_tabla, ejecutar_seguro, id_seleccionado, llenar_tabla

COLUMNAS = [("nombre", "Nombre y apellido", 200), ("telefono", "Teléfono", 120),
            ("correo", "Correo", 220)]


class PestanaClientes(ttk.Frame):
    def __init__(self, padre, gestor):
        super().__init__(padre, padding=12)
        self.gestor = gestor

        formulario = ttk.LabelFrame(self, text="Nuevo cliente", padding=14)
        formulario.pack(side="left", fill="y", padx=(0, 12))
        self.nombre = self._campo(formulario, 0, "Nombre y apellido")
        self.telefono = self._campo(formulario, 2, "Teléfono (ej. 0981 123 456)")
        self.correo = self._campo(formulario, 4, "Correo (opcional)")
        ttk.Button(formulario, text="Guardar cliente", style="Accion.TButton",
                   command=self.guardar).grid(row=6, column=0, sticky="ew", pady=(14, 0))

        lista = ttk.Frame(self)
        lista.pack(side="left", fill="both", expand=True)
        busqueda = ttk.Frame(lista)
        busqueda.pack(fill="x")
        ttk.Label(busqueda, text="Buscar por nombre o teléfono:").pack(side="left")
        self.texto = ttk.Entry(busqueda, width=28)
        self.texto.pack(side="left", padx=6)
        self.texto.bind("<Return>", self.actualizar)
        ttk.Button(busqueda, text="Buscar", command=self.actualizar).pack(side="left")
        marco, self.tabla = crear_tabla(lista, COLUMNAS, alto=16)
        marco.pack(fill="both", expand=True, pady=10)
        ttk.Button(lista, text="Eliminar cliente seleccionado",
                   command=self.eliminar).pack(anchor="e")

    @staticmethod
    def _campo(padre, fila, texto):
        ttk.Label(padre, text=texto).grid(row=fila, column=0, sticky="w")
        entrada = ttk.Entry(padre, width=32)
        entrada.grid(row=fila + 1, column=0, sticky="ew", pady=(2, 10))
        return entrada

    def actualizar(self, _evento=None):
        ok, clientes = ejecutar_seguro(self, self.gestor.listar_clientes, self.texto.get())
        if ok:
            llenar_tabla(self.tabla, [
                (c["id"], (c["nombre"], c["telefono"], c["correo"] or "-"), None) for c in clientes])

    def guardar(self):
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_cliente,
                                self.nombre.get(), self.telefono.get(), self.correo.get())
        if ok:
            messagebox.showinfo("Clientes", "Cliente guardado correctamente.", parent=self)
            for entrada in (self.nombre, self.telefono, self.correo):
                entrada.delete(0, "end")
            self.actualizar()

    def eliminar(self):
        cliente_id = id_seleccionado(self.tabla)
        if cliente_id is None:
            messagebox.showinfo("Clientes", "Primero seleccione un cliente de la lista.", parent=self)
            return
        ok, _ = ejecutar_seguro(self, self.gestor.verificar_permiso, "eliminar_cliente")
        if not ok:
            return
        nombre = self.tabla.item(str(cliente_id), "values")[0]
        if messagebox.askyesno("Eliminar cliente", f"¿Eliminar a {nombre}?", parent=self):
            ok, _ = ejecutar_seguro(self, self.gestor.eliminar_cliente, cliente_id)
            if ok:
                messagebox.showinfo("Clientes", "Cliente eliminado.", parent=self)
                self.actualizar()
