import sqlite3
from datetime import datetime, timedelta
import random

class ClasificacionDAO:
    @staticmethod
    def obtener_metricas(proveedor_id):
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()

        # Datos básicos del proveedor
        cursor.execute("SELECT rut, contacto FROM proveedores WHERE id = ?", (proveedor_id,))
        proveedor = cursor.fetchone()
        rut = proveedor[0] if proveedor else "Desconocido"
        contacto = proveedor[1] if proveedor else "No disponible"

        # Total clasificaciones
        cursor.execute("SELECT COUNT(*) FROM clasificaciones WHERE proveedor_id = ?", (proveedor_id,))
        total = cursor.fetchone()[0]

        # Conteo por clase
        cursor.execute("""
            SELECT clase, COUNT(*) FROM clasificaciones
            WHERE proveedor_id = ? GROUP BY clase
        """, (proveedor_id,))
        conteo = dict(cursor.fetchall())
        A = conteo.get("A", 0)
        B = conteo.get("B", 0)
        C = conteo.get("C", 0)

        # Última fecha
        cursor.execute("SELECT MAX(fecha) FROM clasificaciones WHERE proveedor_id = ?", (proveedor_id,))
        ultima_fecha = cursor.fetchone()[0] or "Sin registros"

        # Últimos 5 días
        cursor.execute("""
            SELECT DATE(fecha) FROM clasificaciones
            WHERE proveedor_id = ?
            GROUP BY DATE(fecha) ORDER BY DATE(fecha) DESC LIMIT 5
        """, (proveedor_id,))
        ultimas_fechas = [f[0] for f in cursor.fetchall()]
        ultimas_fechas.reverse()

        conn.close()

        return {
            'rut': rut,
            'contacto': contacto,
            'total': total,
            'A': A,
            'B': B,
            'C': C,
            'ultima_fecha': ultima_fecha,
            'ultimas_fechas': ultimas_fechas
        }

    @staticmethod
    def insertar_datos_simulados_si_no_existen(proveedor_id):
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clasificaciones WHERE proveedor_id = ?", (proveedor_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"[INFO] Insertando datos simulados para proveedor {proveedor_id}")
            clases = ['A', 'B', 'C']
            hoy = datetime.now()
            for _ in range(30):
                clase = random.choice(clases)
                fecha = hoy - timedelta(days=random.randint(0, 5))
                total = round(random.uniform(20.0, 100.0), 2)  # gramos simulados
                cursor.execute(
                    "INSERT INTO clasificaciones (proveedor_id, total, fecha, clase) VALUES (?, ?, ?, ?)",
                    (proveedor_id, total, fecha.strftime("%Y-%m-%d %H:%M:%S"), clase)
                )
            conn.commit()
        conn.close()
