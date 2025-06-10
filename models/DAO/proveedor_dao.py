import sqlite3 # Importa el módulo sqlite3 para interactuar con la base de datos SQLite.
from models.DTO.proveedor_dto import ProveedorDTO # Importa la clase ProveedorDTO.

class ProveedorDAO: # Objeto de Acceso a Datos (DAO) para manejar las operaciones de la tabla 'proveedores'.
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
    def obtener_todos(): # Obtiene una lista de todos los objetos ProveedorDTO de la base de datos.
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto FROM proveedores")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]