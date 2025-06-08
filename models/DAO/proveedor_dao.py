import sqlite3
from models.DTO.proveedor_dto import ProveedorDTO

class ProveedorDAO:
    @staticmethod
    def obtener_por_id(proveedor_id):
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto FROM proveedores WHERE id = ?", (proveedor_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ProveedorDTO(*row)
        return None

    @staticmethod
    def obtener_todos():
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto FROM proveedores")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]