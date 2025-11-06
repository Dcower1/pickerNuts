import tkinter as tk

from db.setup_db import create_tables
from view.usuario_views.proveedor import ProveedorView


def iniciar_app():
    """
    Punto de entrada alternativo para lanzar la aplicación sin pasar por main.py.
    Se asegura de crear la base de datos y reutiliza la vista actualizada de Proveedor.
    """
    create_tables()
    root = tk.Tk()
    ProveedorView(root, usuario_activo=None)
    root.mainloop()
