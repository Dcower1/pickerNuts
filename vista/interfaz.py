import tkinter as tk

class InterfazProveedorView:
    def __init__(self, proveedor_id, proveedor_nombre):
        self.proveedor_id = proveedor_id
        self.proveedor_nombre = proveedor_nombre

        self.root = tk.Toplevel()
        self.root.title(f"Proveedor: {proveedor_nombre}")
        self.root.geometry("300x200")

        tk.Label(self.root, text="Proveedor seleccionado:", font=("Arial", 12)).pack(pady=10)
        tk.Label(self.root, text=proveedor_nombre, font=("Arial", 14, "bold")).pack()

        tk.Button(self.root, text="Volver", command=self.root.destroy).pack(pady=20)
