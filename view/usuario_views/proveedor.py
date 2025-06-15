from ..base_proveedor_view import BaseProveedorView
from tkinter import messagebox
from view.usuario_views.interfaz import InterfazProveedorView
from models.DAO.proveedor_dao import ProveedorDAO

class ProveedorView(BaseProveedorView):
    def __init__(self, root, usuario_activo=None):
        super().__init__(root, "Panel de Proveedores", usuario_activo)
        self.tree.bind("<Double-1>", self.abrir_interfaz_proveedor)

    def abrir_interfaz_proveedor(self, event):
        seleccionado = self.tree.selection()
        if seleccionado:
            item = self.tree.item(seleccionado[0])
            proveedor_id = item["values"][0]
            proveedor = ProveedorDAO.obtener_por_id(proveedor_id)
            if proveedor:
                InterfazProveedorView(proveedor)