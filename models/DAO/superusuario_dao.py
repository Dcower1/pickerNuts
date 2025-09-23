import hashlib
from db.setup_db import conectar

class SuperUsuarioDAO:
    @staticmethod
    def autenticar(rut, password):
        conn = conectar()
        cursor = conn.cursor()

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT id_user, nombre, rut, rol FROM superusuarios WHERE rut=? AND contrasena_hash=?",
                       (rut, password_hash))
        row = cursor.fetchone()
        conn.close()

        if row:
            return type("SuperUsuario", (), {
                "id_user": row[0],
                "nombre": row[1],
                "rut": row[2],
                "rol": row[3],
                "es_admin": (row[3] == 1)
            })()
        return None
