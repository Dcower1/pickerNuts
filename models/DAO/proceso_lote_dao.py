import sqlite3
import datetime
import random

class ProcesoLoteDAO:
    DB_PATH = "nuts_system.db"

    @staticmethod
    def conectar():
        return sqlite3.connect(ProcesoLoteDAO.DB_PATH)

    # ---------------- Guardar un proceso de lote ----------------
    @staticmethod
    def guardar_proceso(proveedor1_id, proveedor2_id, porcentaje1, porcentaje2, fecha=None):
        if fecha is None:
            fecha = datetime.date.today().isoformat()
        conn = ProcesoLoteDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO procesos_lote (proveedor1_id, proveedor2_id, porcentaje1, porcentaje2, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (proveedor1_id, proveedor2_id, porcentaje1, porcentaje2, fecha))
        conn.commit()
        conn.close()
        return True

    # ---------------- Obtener todos los procesos ----------------
    @staticmethod
    def obtener_todos():
        conn = ProcesoLoteDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.proceso_id, s1.name, s2.name, p.porcentaje1, p.porcentaje2, p.fecha
            FROM procesos_lote p
            JOIN suppliers s1 ON p.proveedor1_id = s1.supplier_id
            JOIN suppliers s2 ON p.proveedor2_id = s2.supplier_id
            ORDER BY p.fecha DESC
        ''')
        filas = cursor.fetchall()
        conn.close()
        return filas

    # ---------------- Obtener último proceso ----------------
    @staticmethod
    def obtener_ultimo():
        conn = ProcesoLoteDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.proceso_id, s1.name, s2.name, p.porcentaje1, p.porcentaje2, p.fecha
            FROM procesos_lote p
            JOIN suppliers s1 ON p.proveedor1_id = s1.supplier_id
            JOIN suppliers s2 ON p.proveedor2_id = s2.supplier_id
            ORDER BY p.fecha DESC
            LIMIT 1
        ''')
        fila = cursor.fetchone()
        conn.close()
        return fila

    # ---------------- Totales de clasificación por proveedor ----------------
    @staticmethod
    def obtener_totales_actuales(proveedor_id):
        conn = ProcesoLoteDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT grade, COUNT(*) 
            FROM classification_details cd
            JOIN classifications c ON cd.classification_id = c.classification_id
            WHERE c.supplier_id = ?
            GROUP BY grade
        ''', (proveedor_id,))
        filas = cursor.fetchall()
        conn.close()

        totales = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for grade, cantidad in filas:
            totales[grade] = cantidad
        totales['total'] = sum(totales.values())
        return totales

    # ---------------- Insertar datos de prueba ----------------
    @staticmethod
    def insertar_datos_simulados(proveedor_id):
        conn = ProcesoLoteDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM classifications WHERE supplier_id = ?', (proveedor_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            fechas = [(datetime.date.today() - datetime.timedelta(days=x)).isoformat() for x in range(10)]
            for fecha in fechas:
                cursor.execute('INSERT INTO classifications (supplier_id, date, total_nuts) VALUES (?, ?, ?)',
                               (proveedor_id, fecha, 0))
                clasificacion_id = cursor.lastrowid
                for grade in ['A', 'B', 'C', 'D']:
                    cantidad = random.randint(10, 50)
                    for _ in range(cantidad):
                        cursor.execute('INSERT INTO classification_details (classification_id, grade) VALUES (?, ?)',
                                       (clasificacion_id, grade))
            conn.commit()
        conn.close()


    @staticmethod
    def obtener_historial_fechas(id_proveedor):
        conn = ProcesoLoteDAO.conectar()  # <- aquí estaba el error
        cursor = conn.cursor()

        # Fechas procesos individuales
        cursor.execute("SELECT date FROM classifications WHERE supplier_id = ?", (id_proveedor,))
        fechas_ind = [row[0] for row in cursor.fetchall()]

        # Fechas procesos dobles
        cursor.execute("SELECT fecha FROM procesos_lote WHERE proveedor1_id = ? OR proveedor2_id = ?", (id_proveedor, id_proveedor))
        fechas_dob = [row[0] for row in cursor.fetchall()]

        conn.close()
        return sorted(fechas_ind + fechas_dob)  # Orden cronológico

    @staticmethod
    def registrar_clasificacion(proveedor_id, grade, fecha=None):
        if grade not in ("A", "B", "C", "D"):
            raise ValueError("grade debe ser uno de A, B, C o D")

        if fecha is None:
            fecha = datetime.date.today().isoformat()

        conn = ProcesoLoteDAO.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT classification_id FROM classifications WHERE supplier_id = ? AND date = ?",
                (proveedor_id, fecha),
            )
            row = cursor.fetchone()

            if row:
                classification_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO classifications (supplier_id, date, total_nuts) VALUES (?, ?, ?)",
                    (proveedor_id, fecha, 0),
                )
                classification_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO classification_details (classification_id, grade) VALUES (?, ?)",
                (classification_id, grade),
            )
            cursor.execute(
                "UPDATE classifications SET total_nuts = total_nuts + 1 WHERE classification_id = ?",
                (classification_id,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
