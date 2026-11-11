"""Sección Usuarios: lista, alta y desbloqueo de usuarios (solo Administrador)."""
from tkinter import messagebox, ttk

from interfaz.comun import campo, crear_tabla, ejecutar_seguro, id_seleccionado, llenar_tabla, tarjeta
from logica.permisos import ROLES

COLUMNAS = [("usuario", "Usuario", 100), ("nombre", "Nombre", 165), ("rol", "Rol", 150),
            ("estado", "Estado", 185)]


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
                  text="Mín. 8 caracteres con letras y números; se guarda como hash con sal. "
                       "3 intentos fallidos seguidos: bloqueo de 5 minutos.").pack(anchor="w")

        lista = ttk.Frame(self)
        lista.pack(side="left", fill="both", expand=True)
        abajo = ttk.Frame(lista)
        abajo.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(abajo, text="Desbloquear usuario seleccionado",
                   command=self.desbloquear).pack(side="right")
        marco, self.tabla = crear_tabla(lista, COLUMNAS, alto=12)
        marco.pack(fill="both", expand=True)

    def actualizar(self, _evento=None):
        ok, usuarios = ejecutar_seguro(self, self.gestor.listar_usuarios)
        if ok:
            llenar_tabla(self.tabla, [
                (u["id"], (u["usuario"], u["nombre"], u["rol_texto"], u["estado_texto"]),
                 "VENCIDO" if u["estado_texto"].startswith("Bloqueado") else None) for u in usuarios])

    def desbloquear(self):
        usuario_id = id_seleccionado(self.tabla)
        if usuario_id is None:
            messagebox.showinfo("Usuarios", "Primero seleccione un usuario de la lista.", parent=self)
            return
        ok, _ = ejecutar_seguro(self, self.gestor.desbloquear_usuario, usuario_id)
        if ok:
            messagebox.showinfo("Usuarios", "El usuario ya puede volver a entrar.", parent=self)
            self.actualizar()

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
