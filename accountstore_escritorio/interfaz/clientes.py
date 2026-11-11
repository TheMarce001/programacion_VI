"""Sección Clientes: alta, búsqueda y eliminación de clientes."""
from tkinter import messagebox, ttk

from interfaz.comun import campo, crear_tabla, ejecutar_seguro, id_seleccionado, llenar_tabla, tarjeta

COLUMNAS = [("nombre", "Nombre y apellido", 220), ("telefono", "Teléfono", 130),
            ("correo", "Correo", 240)]


class PestanaClientes(ttk.Frame):
    TITULO = "Clientes"
    DESCRIPCION = "Personas que compran perfiles. El teléfono no puede repetirse."

    def __init__(self, padre, gestor):
        super().__init__(padre)
        self.gestor = gestor

        formulario = tarjeta(self, "Nuevo cliente", padding=18)
        formulario.pack(side="left", fill="y", padx=(0, 16))
        self.nombre = campo(formulario, "Nombre y apellido")
        self.telefono = campo(formulario, "Teléfono (ej. 0981 123 456)")
        self.correo = campo(formulario, "Correo (opcional)")
        ttk.Button(formulario, text="Guardar cliente", style="Accion.TButton",
                   command=self.guardar).pack(fill="x", pady=(6, 0))

        lista = ttk.Frame(self)
        lista.pack(side="left", fill="both", expand=True)
        busqueda = ttk.Frame(lista)
        busqueda.pack(fill="x", pady=(0, 10))
        ttk.Label(busqueda, text="Buscar por nombre o teléfono", style="Nota.TLabel").pack(side="left")
        self.texto = ttk.Entry(busqueda, width=28)
        self.texto.pack(side="left", padx=8)
        self.texto.bind("<Return>", self.actualizar)
        ttk.Button(busqueda, text="Buscar", command=self.actualizar).pack(side="left")
        ttk.Button(lista, text="Eliminar cliente seleccionado", style="Peligro.TButton",
                   command=self.eliminar).pack(side="bottom", anchor="e", pady=(12, 0))
        marco, self.tabla = crear_tabla(lista, COLUMNAS, alto=12)
        marco.pack(fill="both", expand=True)

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
