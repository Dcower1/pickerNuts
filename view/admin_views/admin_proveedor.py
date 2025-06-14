from ..base_proveedor_view import BaseProveedorView
from tkinter import ttk, messagebox
from models.DAO.proveedor_dao import ProveedorDAO

class admin_ProveedorView(BaseProveedorView):
    def __init__(self, root, usuario_activo=None):
        super().__init__(root, "Panel del ADMIN", usuario_activo)

        self.boton_eliminar = ttk.Button(self.root, text="Eliminar Proveedor", command=self.eliminar_proveedor)
        self.boton_eliminar.pack(pady=10)

    def eliminar_proveedor(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccionar", "Por favor, selecciona un proveedor para eliminar.")
            return
        item = self.tree.item(seleccionado[0])
        proveedor_id = item["values"][0]

        confirm = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de eliminar este proveedor?")
        if confirm:
            if ProveedorDAO.eliminar(proveedor_id):
                messagebox.showinfo("Eliminado", "Proveedor eliminado correctamente.")
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el proveedor.")