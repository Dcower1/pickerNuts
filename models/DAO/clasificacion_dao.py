import sqlite3

class ClasificacionDAO:
    DB_PATH = "sistema_nueces.db"

    @staticmethod
    def conectar():
        return sqlite3.connect(ClasificacionDAO.DB_PATH)

    @staticmethod
    def obtener_totales_actuales(proveedor_id):
        """
        Retorna un diccionario con el conteo total de nueces por clase para el proveedor.
        Ejemplo: {'A': 120, 'B': 80, 'C': 30, 'total': 230}
        """
        conn = ClasificacionDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dc.clase, COUNT(*)
            FROM clasificaciones c
            JOIN detalle_clasificaciones dc ON c.proveedor_id = dc.clasificacion_id
            WHERE c.proveedor_id = ?
            GROUP BY dc.clase
        ''', (proveedor_id,))
        filas = cursor.fetchall()
        conn.close()

        totales = {'A': 0, 'B': 0, 'C': 0}
        for clase, cantidad in filas:
            totales[clase] = cantidad
        totales['total'] = sum(totales.values())
        return totales

    @staticmethod
    def obtener_fechas_historial(proveedor_id, limite=10):
        """
        Obtiene las últimas fechas de clasificaciones para mostrar línea de tiempo.
        Devuelve lista de strings con fechas ordenadas ascendentemente.
        """
        conn = ClasificacionDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fecha FROM clasificaciones
            WHERE proveedor_id = ?
            ORDER BY fecha DESC
            LIMIT ?
        ''', (proveedor_id, limite))
        filas = cursor.fetchall()
        conn.close()

        fechas = [fila[0] for fila in filas]
        return fechas[::-1]  # Ascendente

    @staticmethod
    def obtener_historial_clases(proveedor_id):
        """
        Obtiene datos para graficar evolución histórica de cantidades por clase.
        Devuelve: (fechas, dict_clases) donde:
        - fechas: lista de fechas (str) ordenadas ascendentemente.
        - dict_clases: {'A': [cantidades...], 'B': [...], 'C': [...]}
        """
        conn = ClasificacionDAO.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.fecha, dc.clase, COUNT(*)
            FROM clasificaciones c
            JOIN detalle_clasificaciones dc ON c.proveedor_id = dc.clasificacion_id
            WHERE c.proveedor_id = ?
            GROUP BY c.fecha, dc.clase
            ORDER BY c.fecha ASC
        ''', (proveedor_id,))
        filas = cursor.fetchall()
        conn.close()

        fechas = []
        data = {'A': [], 'B': [], 'C': []}
        fecha_actual = None
        temp = {'A': 0, 'B': 0, 'C': 0}

        for fila in filas:
            fecha, clase, cantidad = fila
            if fecha != fecha_actual:
                if fecha_actual is not None:
                    fechas.append(fecha_actual)
                    for c in ['A','B','C']:
                        data[c].append(temp.get(c, 0))
                fecha_actual = fecha
                temp = {'A': 0, 'B': 0, 'C': 0}
            temp[clase] = cantidad
        # Añadir última fecha
        if fecha_actual is not None:
            fechas.append(fecha_actual)
            for c in ['A','B','C']:
                data[c].append(temp.get(c, 0))

        return fechas, data

    @staticmethod
    def insertar_datos_simulados_si_no_existen(proveedor_id):
        """
        Método para insertar datos de prueba si no existen,
        útil para desarrollo o demo.
        """
        conn = ClasificacionDAO.conectar()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM clasificaciones WHERE proveedor_id = ?', (proveedor_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            import datetime
            import random

            fechas = [(datetime.date.today() - datetime.timedelta(days=x)).isoformat() for x in range(10)][::-1]

            for fecha in fechas:
                # Insertar una clasificación nueva
                cursor.execute('''
                    INSERT INTO clasificaciones (proveedor_id, total, fecha, clase)
                    VALUES (?, ?, ?, ?)
                ''', (proveedor_id, 0, fecha, 'N/A'))  # 'clase' aquí podría ser dummy

                clasificacion_id = cursor.lastrowid

                # Insertar detalle para cada clase con números aleatorios
                for clase in ['A', 'B', 'C']:
                    cantidad = random.randint(10, 50)
                    for _ in range(cantidad):
                        cursor.execute('''
                            INSERT INTO detalle_clasificaciones (clasificacion_id, clase)
                            VALUES (?, ?)
                        ''', (clasificacion_id, clase))

            conn.commit()
        conn.close()

    @staticmethod
    def guardar_historial(proveedor_id, fecha):
        """
        Guarda un registro en el historial de clasificaciones para un proveedor y fecha dada.

        Args:
            proveedor_id (int): ID del proveedor.
            fecha (str): Fecha en formato 'YYYY-MM-DD'.

        Returns:
            bool: True si se guardó correctamente, False si hubo error.
        """
        try:
            conn = ClasificacionDAO.conectar()
            cursor = conn.cursor()

            # Insertar nuevo registro en la tabla historial_clasificaciones
            cursor.execute("""
                INSERT INTO historial_clasificaciones (proveedor_id, fecha)
                VALUES (?, ?)
            """, (proveedor_id, fecha))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al guardar historial: {e}")
            return False