import hashlib
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