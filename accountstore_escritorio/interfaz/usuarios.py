"""Pestaña Usuarios: lista de usuarios y alta de usuarios (solo Administrador)."""
from tkinter import messagebox, ttk

from interfaz.comun import crear_tabla, ejecutar_seguro, llenar_tabla
from logica.permisos import ROLES

COLUMNAS = [("usuario", "Usuario", 120), ("nombre", "Nombre", 200), ("rol", "Rol", 170),
            ("estado", "Estado", 90)]


class PestanaUsuarios(ttk.Frame):
    def __init__(self, padre, gestor):
        super().__init__(padre, padding=12)
        self.gestor = gestor

        formulario = ttk.LabelFrame(self, text="Nuevo usuario", padding=14)
        formulario.pack(side="left", fill="y", padx=(0, 12))
        self.usuario = self._campo(formulario, 0, "Usuario")
        self.nombre = self._campo(formulario, 2, "Nombre y apellido")
        ttk.Label(formulario, text="Rol").grid(row=4, column=0, sticky="w")
        self.rol = ttk.Combobox(formulario, values=list(ROLES.values()), state="readonly", width=30)
        self.rol.grid(row=5, column=0, sticky="ew", pady=(2, 10))
        self.clave = self._campo(formulario, 6, "Contraseña", oculto=True)
        self.confirmacion = self._campo(formulario, 8, "Repetir contraseña", oculto=True)
        ttk.Button(formulario, text="Crear usuario", style="Accion.TButton",
                   command=self.guardar).grid(row=10, column=0, sticky="ew", pady=(6, 10))
        ttk.Label(formulario, style="Nota.TLabel", wraplength=230, justify="left",
                  text="Mínimo 8 caracteres con letras y números. La contraseña se guarda como "
                       "hash PBKDF2-SHA256 con sal: nunca en texto plano.").grid(row=11, column=0, sticky="w")

        marco, self.tabla = crear_tabla(self, COLUMNAS, alto=16)
        marco.pack(side="left", fill="both", expand=True)

    @staticmethod
    def _campo(padre, fila, texto, oculto=False):
        ttk.Label(padre, text=texto).grid(row=fila, column=0, sticky="w")
        entrada = ttk.Entry(padre, width=32, show="•" if oculto else "")
        entrada.grid(row=fila + 1, column=0, sticky="ew", pady=(2, 10))
        return entrada

    def actualizar(self, _evento=None):
        ok, usuarios = ejecutar_seguro(self, self.gestor.listar_usuarios)
        if ok:
            llenar_tabla(self.tabla, [
                (u["id"], (u["usuario"], u["nombre"], u["rol_texto"],
                           "Activo" if u["activo"] else "Inactivo"), None) for u in usuarios])

    def guardar(self):
        codigo_rol = {texto: codigo for codigo, texto in ROLES.items()}.get(self.rol.get())
        ok, _ = ejecutar_seguro(self, self.gestor.registrar_usuario, self.usuario.get(),
                                self.nombre.get(), codigo_rol, self.clave.get(), self.confirmacion.get())
        self.clave.delete(0, "end")
        self.confirmacion.delete(0, "end")
        if ok:
            messagebox.showinfo("Usuarios", "Usuario creado correctamente.", parent=self)
            self.usuario.delete(0, "end")
            self.nombre.delete(0, "end")
            self.rol.set("")
            self.actualizar()
