from view import login # Importa los módulos login y proveedor de las vistas.
from db.setup_db import crear_tablas# Importa el módulo bd para la base de datos.
import tkinter as tk

from view.usuario_views import proveedor # Importa la librería Tkinter.

def iniciar_app():
    crear_tablas()
    root = tk.Tk()

    def on_login_success():
        root.destroy()  # Cierra la ventana de login
        nuevo_root = tk.Tk()
        proveedor.ProveedorView(nuevo_root)
        nuevo_root.mainloop()

    login.LoginView(root, on_login_success=on_login_success)
    root.mainloop()
