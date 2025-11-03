from db.setup_db import connect
from models.DTO.proveedor_dto import ProveedorDTO  
class ProveedorDAO:
    @staticmethod
    def obtener_por_id(proveedor_id):
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT supplier_id, name, rut, contact, status FROM suppliers WHERE supplier_id = ?",
            (proveedor_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return ProveedorDTO(*row)
        return None

    @staticmethod
    def obtener_todos():
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_id, name, rut, contact, status FROM suppliers")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]

    @staticmethod
    def insertar(nombre, rut, contacto):
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO suppliers (name, rut, contact, status) VALUES (?, ?, ?, 1)",  # status activo por defecto
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
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE suppliers SET name = ?, rut = ?, contact = ? WHERE supplier_id = ?",
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
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE suppliers SET status = ? WHERE supplier_id = ?",
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
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers WHERE rut = ?", (rut,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    def existe_contacto(contacto):
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers WHERE contact = ?", (contacto,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    def obtener_activos():
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_id, name, rut, contact, status FROM suppliers WHERE status = 1")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]

    @staticmethod
    def obtener_inactivos():
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_id, name, rut, contact, status FROM suppliers WHERE status = 2")
        rows = cursor.fetchall()
        conn.close()
        return [ProveedorDTO(*r) for r in rows]