"""Sección Usuarios: lista de usuarios y alta de usuarios (solo Administrador)."""
from tkinter import messagebox, ttk

from interfaz.comun import campo, crear_tabla, ejecutar_seguro, llenar_tabla, tarjeta
from logica.permisos import ROLES

COLUMNAS = [("usuario", "Usuario", 130), ("nombre", "Nombre", 220), ("rol", "Rol", 190),
            ("estado", "Estado", 90)]


class PestanaUsuarios(ttk.Frame):
    TITULO = "Usuarios"
    DESCRIPCION = "Quién puede entrar al sistema y con qué rol. Solo el Administrador crea usuarios."

    def __init__(self, padre, gestor):
        super().__init__(padre)
        self.gestor = gestor

        formulario = tarjeta(self, "Nuevo usuario", padding=18)
        formulario.pack(side="left", fill="y", padx=(0, 16))
        self.usuario = campo(formulario, "Usuario")
        self.nombre = campo(formulario, "Nombre y apellido")
        ttk.Label(formulario, text="Rol", style="Tarjeta.TLabel").pack(anchor="w")
        self.rol = ttk.Combobox(formulario, values=list(ROLES.values()), state="readonly", width=30)
        self.rol.pack(fill="x", pady=(3, 10))
        self.clave = campo(formulario, "Contraseña", oculto=True)
        self.confirmacion = campo(formulario, "Repetir contraseña", oculto=True)
        ttk.Button(formulario, text="Crear usuario", style="Accion.TButton",
                   command=self.guardar).pack(fill="x", pady=(2, 10))
        ttk.Label(formulario, style="TarjetaNota.TLabel", wraplength=270, justify="left",
                  text="Mínimo 8 caracteres, con letras y números. Se guarda como hash "
                       "PBKDF2 con sal, nunca en texto plano.").pack(anchor="w")

        marco, self.tabla = crear_tabla(self, COLUMNAS, alto=12)
        marco.pack(side="left", fill="both", expand=True)

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
