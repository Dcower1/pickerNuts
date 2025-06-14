from view import login
from db.setup_db import crear_tablas
import tkinter as tk
from view.usuario_views import proveedor
from view.admin_views import admin_proveedor

def iniciar_app():
    crear_tablas()
    root = tk.Tk()

    def on_login_success(rol, usuario_activo=None):
        # Cuando login es exitoso, cerramos la ventana login
        root.destroy()
        # Creamos la ventana principal según el rol
        nuevo_root = tk.Tk()
        if rol == 1:
           
            admin_proveedor.BaseProveedorView(nuevo_root, "Gestión de Proveedores", usuario_activo=usuario_activo)

        else:
            proveedor.ProveedorView(nuevo_root, usuario_activo=usuario_activo)
        # Ejecutamos el loop de la ventana principal
        nuevo_root.mainloop()

    # Lanzamos ventana login, pasamos callback on_login_success
    login.LoginView(root, on_login_success=on_login_success)
    root.mainloop()

if __name__ == "__main__":
    iniciar_app()