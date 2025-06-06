import tkinter as tk
from tkinter import ttk, messagebox
from controlador import utils
import sqlite3
from datetime import datetime, timedelta
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class InterfazProveedorView:
    def __init__(self, proveedor_id, proveedor_nombre):
        self.proveedor_id = proveedor_id
        self.proveedor_nombre = proveedor_nombre
        self.produccion_activa = False

        self.simulaciones(self.proveedor_id)  # Insertar datos simulados 

        self.root = tk.Toplevel()
        self.root.title("Ficha Proveedor")
        self.root.configure(bg="white")
        self.root.geometry("950x600")
        utils.centrar_ventana(self.root, 950, 600)

        self.datos = self.obtener_metricas()

        # Encabezado: aqui mostramos el nombre del proveedor, el rut, y su contacto datos guardados en la base de datos.
        tk.Label(self.root, text="Ficha Proveedor", font=("Arial", 16, "bold"), bg="white").place(x=30, y=20)
        tk.Label(self.root, text=f"Proveedor: {self.proveedor_nombre}", font=("Arial", 12), bg="white").place(x=30, y=60)
        tk.Label(self.root, text=f"Rut: {self.datos['rut']}", font=("Arial", 12), bg="white").place(x=30, y=90)
        tk.Label(self.root, text=f"Contacto: {self.datos['contacto']}", font=("Arial", 12), bg="white").place(x=600, y=60)

        # Botón START: Recordatorio esta la debo pasar como funcion y luego cambiar a utlidades porque los botones son cosas puedo reutilizar
        self.boton_produccion = tk.Button(self.root, text="START", bg="green", fg="white",
                                          font=("Arial", 14, "bold"), width=10, height=2,
                                          command=self.toggle_produccion)
        self.boton_produccion.place(x=400, y=100)

        #AQUI YA EMPIEZA LAS METRICAS Y SU trazabilidad
        # Total clasificaciones
        tk.Label(self.root, text=f"Total Clasificaciones: {self.datos['total']}", font=("Arial", 12), bg="white").place(x=30, y=180)

        # Conteo por clase
        tk.Label(self.root, text="Conteo por clase", font=("Arial", 12, "bold"), bg="white").place(x=30, y=220)
        clases = ["A", "B", "C"]
        tabla = ttk.Treeview(self.root, columns=clases, show='headings', height=1)
        for col in clases:
            tabla.heading(col, text=col)
            tabla.column(col, width=100, anchor="center")
        tabla.insert("", "end", values=[self.datos['A'], self.datos['B'], self.datos['C']])
        tabla.place(x=30, y=250)

        # Gráfico circular
        self.graficar_torta(self.datos)

        # Tendencia de calidad
        tk.Label(self.root, text="Tendencia de calidad:", font=("Arial", 12, "bold"), bg="white").place(x=30, y=330)



        # Última clasificación
        tk.Label(self.root, text=f"Última clasificación: {self.datos['ultima_fecha']}", font=("Arial", 11), bg="white").place(x=30, y=410)
        fechas = self.datos["ultimas_fechas"]
        for i, f in enumerate(fechas):
            tk.Label(self.root, text=f, bg="#eeeeee", font=("Arial", 10), width=15).place(x=30 + i * 130, y=450)
        # Volver
        tk.Button(self.root, text="Volver", command=self.root.destroy).place(x=30, y=500)

    def toggle_produccion(self):
        self.produccion_activa = not self.produccion_activa
        self.boton_produccion.config(
            text="DETENER" if self.produccion_activa else "START",
            bg="red" if self.produccion_activa else "green"
        )

    def obtener_metricas(self):
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()

        # Datos básicos del proveedor
        cursor.execute("SELECT nombre, rut, contacto FROM proveedores WHERE id = ?", (self.proveedor_id,))
        proveedor = cursor.fetchone()
        rut = proveedor[1]
        contacto = proveedor[2]

        # Total clasificaciones
        cursor.execute("SELECT COUNT(*) FROM clasificaciones WHERE proveedor_id = ?", (self.proveedor_id,))
        total = cursor.fetchone()[0]

        # Conteo por clase
        cursor.execute("""
            SELECT clase, COUNT(*) FROM clasificaciones
            WHERE proveedor_id = ? GROUP BY clase
        """, (self.proveedor_id,))
        conteo = dict(cursor.fetchall())
        A = conteo.get("A", 0)
        B = conteo.get("B", 0)
        C = conteo.get("C", 0)

        # Última fecha
        cursor.execute("""
            SELECT MAX(fecha) FROM clasificaciones
            WHERE proveedor_id = ?
        """, (self.proveedor_id,))
        ultima_fecha = cursor.fetchone()[0] or "Sin registros"

        # Tendencia (últimos 5 días distintos)
        cursor.execute("""
            SELECT DATE(fecha) as dia FROM clasificaciones
            WHERE proveedor_id = ?
            GROUP BY dia ORDER BY dia DESC LIMIT 5
        """, (self.proveedor_id,))
        ultimas_fechas = [f[0] for f in cursor.fetchall()]
        ultimas_fechas.reverse()  # orden cronológico

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

    def graficar_torta(self, datos):
        valores = [datos['A'], datos['B'], datos['C']]
        clases = ['A', 'B', 'C']

        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.pie(valores, labels=clases, autopct='%1.0f%%', startangle=90)
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().place(x=600, y=220)

    def simulaciones(self, proveedor_id):
        conn = sqlite3.connect("sistema_nueces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clasificaciones WHERE proveedor_id = ?", (proveedor_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            print("No hay clasificaciones. Insertando datos simulados...")
            clases = ['A', 'B', 'C']
            hoy = datetime.now()
            for _ in range(30):
                clase = random.choice(clases)
                fecha = hoy - timedelta(days=random.randint(0, 5))
                cursor.execute(
                    "INSERT INTO clasificaciones (proveedor_id, clase, fecha) VALUES (?, ?, ?)",
                    (proveedor_id, clase, fecha.strftime("%Y-%m-%d %H:%M:%S"))
                )
            conn.commit()
        conn.close()