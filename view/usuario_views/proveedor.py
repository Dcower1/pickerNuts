from ..base_proveedor_view import BaseProveedorView
from tkinter import messagebox
from view.usuario_views.interfaz import InterfazView
from models.DAO.proveedor_dao import ProveedorDAO
import tkinter as tk

class ProveedorView(BaseProveedorView):
    def __init__(self, root, usuario_activo=None):
        super().__init__(root, "Panel de Proveedores", usuario_activo)
        self.tree.bind("<Double-1>", self.abrir_interfaz_proveedor)
        print("[EV_TU05] Menú principal iniciado correctamente.", flush=True)

    def abrir_interfaz_proveedor(self, event):
        seleccionado = self.tree.selection()
        if seleccionado:
            item = self.tree.item(seleccionado[0])
            proveedor_id = item["values"][0]
            proveedor = ProveedorDAO.obtener_por_id(proveedor_id)
            if proveedor:
                if self.usuario_activo and getattr(self.usuario_activo, "es_admin", False):
                    #  Supervisor/Admin 
                    from view.admin_views.admin_interfaz import admin_InterfazProveedorView
                    admin_InterfazProveedorView(proveedor, callback_actualizar=self.actualizar_lista)
                else:
                    #  Usuario normal 
                    from view.usuario_views.interfaz import InterfazView
                    InterfazView(tk.Toplevel(self.root), proveedor)
