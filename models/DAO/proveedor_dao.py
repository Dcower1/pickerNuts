from db.setup_db import conectar
from models.DTO.proveedor_dto import ProveedorDTO  # Importa la clase ProveedorDTO.

class ProveedorDAO:
    @staticmethod
    def obtener_por_id(proveedor_id):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto, estado FROM proveedores WHERE id = ?", (proveedor_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ProveedorDTO(*row)
        return None

    @staticmethod
    def obtener_todos():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto, estado FROM proveedores")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]

    @staticmethod
    def insertar(nombre, rut, contacto):
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO proveedores (nombre, rut, contacto, estado) VALUES (?, ?, ?, 1)",  # Estado activo por defecto
                (nombre, rut, contacto)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Insertar proveedor: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def actualizar(proveedor_id, nombre, rut, contacto):
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE proveedores SET nombre = ?, rut = ?, contacto = ? WHERE id = ?",
                (nombre, rut, contacto, proveedor_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Actualizar proveedor: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def actualizar_estado(proveedor_id, nuevo_estado):
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE proveedores SET estado = ? WHERE id = ?",
                (nuevo_estado, proveedor_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Actualizar estado: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def eliminar_logico(proveedor_id):
        # Cambia el estado a inactivo (2)
        return ProveedorDAO.actualizar_estado(proveedor_id, 2)

    @staticmethod
    def activar_proveedor(proveedor_id):
        # Cambia el estado a activo (1)
        return ProveedorDAO.actualizar_estado(proveedor_id, 1)

    @staticmethod
    def existe_rut(rut):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM proveedores WHERE rut = ?", (rut,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    def existe_contacto(contacto):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM proveedores WHERE contacto = ?", (contacto,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    def obtener_activos():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto, estado FROM proveedores WHERE estado = 1")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]

    @staticmethod
    def obtener_inactivos():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut, contacto, estado FROM proveedores WHERE estado = 2")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]
