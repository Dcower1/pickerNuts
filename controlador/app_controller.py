from vista import login, proveedor
from modelo import bd
import tkinter as tk

def iniciar_app():
    bd.crear_tablas()
    root = tk.Tk()
    login.LoginView(root, on_login_success=lambda: proveedor.ProveedorView())
    root.mainloop()
