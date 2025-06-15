from ..base_proveedor_view import BaseProveedorView
from tkinter import ttk, messagebox
from models.DAO.proveedor_dao import ProveedorDAO
from view.admin_views.admin_interfaz import admin_InterfazProveedorView

class admin_ProveedorView(BaseProveedorView):
    def __init__(self, root, usuario_activo=None):
        print("✅ Inicio sesión como admin")
        super().__init__(root, "Panel del ADMIN", usuario_activo)
        self.tree.bind("<Double-1>", self.abrir_interfaz_proveedor)

    def abrir_interfaz_proveedor(self, event):
        seleccionado = self.tree.selection()
        if seleccionado:
            item = self.tree.item(seleccionado[0])
            proveedor_id = item["values"][0]
            proveedor = ProveedorDAO.obtener_por_id(proveedor_id)
            if proveedor:
                # Aquí se crea la ventana detalle pasando el callback para actualizar lista
                admin_InterfazProveedorView(proveedor, callback_actualizar=self.actualizar_lista)