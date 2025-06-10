from view import login, proveedor # Importa los módulos login y proveedor de las vistas.
from models import bd # Importa el módulo bd para la base de datos.
import tkinter as tk # Importa la librería Tkinter.

def iniciar_app(): # Inicializa la aplicación, creando las tablas de la base de datos y mostrando la ventana de login.
    bd.crear_tablas()
    root = tk.Tk()
    login.LoginView(root, on_login_success=lambda: proveedor.ProveedorView())
    root.mainloop()
