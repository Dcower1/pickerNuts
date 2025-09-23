from db.setup_db import crear_tablas
import tkinter as tk
from view.usuario_views import proveedor


def iniciar_app():
    crear_tablas()
    root = tk.Tk()

    proveedor.ProveedorView(root, usuario_activo=None)

    root.mainloop()

if __name__ == "__main__":
    iniciar_app()
