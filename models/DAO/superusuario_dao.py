import hashlib
import sqlite3
from db.setup_db import connect

class SuperUsuarioDAO:
    @staticmethod
    def autenticar(rut, password):
        conn = connect()
        cursor = conn.cursor()

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT user_id, username, rut, role FROM superusers WHERE rut=? AND password_hash=?",
            (rut, password_hash)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return type("SuperUsuario", (), {
                "id_user": row[0],      # Mantenido en español
                "nombre": row[1],       # Mapeado desde 'username'
                "rut": row[2],
                "rol": row[3],          # Mapeado desde 'role'
                "es_admin": (row[3] == 1)
            })()
        return None

    @staticmethod
    def crear_supervisor(nombre, rut, password, role=1):
        if not nombre or not rut or not password:
            return False, "Todos los campos son obligatorios."

        conn = connect()
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        role = 1 if role not in (1, 2) else role
        try:
            cursor.execute(
                "INSERT INTO superusers (username, rut, password_hash, role) VALUES (?, ?, ?, ?)",
                (nombre, rut, password_hash, role),
            )
            conn.commit()
            return True, "Supervisor registrado correctamente."
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "Ya existe un usuario con ese nombre o RUT."
        except Exception as exc:
            conn.rollback()
            return False, f"Ocurrió un error al registrar al supervisor: {exc}"
        finally:
            conn.close()
