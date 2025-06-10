import tkinter as tk # Importa la librería Tkinter para la creación de interfaces gráficas de usuario.
from tkinter import ttk # Importa el módulo ttk de Tkinter para widgets temáticos.
from components import utils # Importa el módulo utils para funciones de utilidad.
from datetime import datetime # Importa la clase datetime para trabajar con fechas y horas.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # Importa FigureCanvasTkAgg para incrustar gráficos de Matplotlib.
import matplotlib.pyplot as plt # Importa pyplot de Matplotlib para la creación de gráficos.

from models.DAO.clasificacion_dao import ClasificacionDAO # Importa la clase ClasificacionDAO.
from models.DTO.proveedor_dto import ProveedorDTO # Importa la clase ProveedorDTO.
from components.utils import crear_boton_toggle # Importa la función crear_boton_toggle.

class InterfazProveedorView: # Representa la interfaz de usuario para la ficha de un proveedor.
    def __init__(self, proveedor_dto: ProveedorDTO): # Inicializa la vista con un objeto ProveedorDTO.
        self.proveedor = proveedor_dto
        self.produccion_activa = False

        # Insertar datos simulados si no existen
        ClasificacionDAO.insertar_datos_simulados_si_no_existen(self.proveedor.id)

        self.datos = ClasificacionDAO.obtener_metricas(self.proveedor.id)

        self.root = tk.Toplevel()
        self.root.title("Ficha Proveedor")
        self.root.configure(bg="white")
        self.root.geometry("950x600")
        utils.centrar_ventana(self.root, 950, 600)

        # Encabezado
        tk.Label(self.root, text="Ficha Proveedor", font=("Arial", 16, "bold"), bg="white").place(x=30, y=20)
        tk.Label(self.root, text=f"Proveedor: {self.proveedor.nombre}", font=("Arial", 12), bg="white").place(x=30, y=60)
        tk.Label(self.root, text=f"Rut: {self.datos['rut']}", font=("Arial", 12), bg="white").place(x=30, y=90)
        tk.Label(self.root, text=f"Contacto: {self.datos['contacto']}", font=("Arial", 12), bg="white").place(x=600, y=60)

        # Botón START reutilizable
        self.boton_produccion = crear_boton_toggle(self.root, self.toggle_produccion)
        self.boton_produccion.place(x=400, y=100)

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

        fechas = self.datos["ultimas_fechas"]
        for i, f in enumerate(fechas):
            tk.Label(self.root, text=f, bg="#eeeeee", font=("Arial", 10), width=15).place(x=30 + i * 130, y=450)

        # Última clasificación
        tk.Label(self.root, text=f"Última clasificación: {self.datos['ultima_fecha']}", font=("Arial", 11), bg="white").place(x=30, y=410)

        # Volver
        tk.Button(self.root, text="Volver", command=self.root.destroy).place(x=30, y=500)

    def toggle_produccion(self, estado): # Alterna el estado de producción y lo imprime en consola.
        self.produccion_activa = estado
        print(f"Producción {'iniciada' if estado else 'detenida'} para {self.proveedor.nombre}")

    def graficar_torta(self, datos): # Crea y muestra un gráfico circular (pastel) de clasificaciones.
        valores = [datos['A'], datos['B'], datos['C']]
        clases = ['A', 'B', 'C']

        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.pie(valores, labels=clases, autopct='%1.0f%%', startangle=90)
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().place(x=600, y=220)