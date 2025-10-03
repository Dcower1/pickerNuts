import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from components.utils import obtener_colores
from components import utils
from models.DAO.camara import Camara, ConfigBotonCamara
from models.DAO.Tensflow import ModeloNuecesInterpreter

COLORS = obtener_colores()


class InterfazView:
    def __init__(self, root, proveedor):
        self.root = root
        self.proveedor = proveedor
        self.colores = COLORS
        self.camara: Camara | None = None
        self.interprete = ModeloNuecesInterpreter()
        self.construir_interfaz()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    def construir_interfaz(self):
        self.root.title("Interfaz Clasificacion")
        self.root.configure(bg=self.colores["fondo"])
        self.root.geometry("1000x650")

        utils.centrar_ventana(self.root, 1000, 650)

        # --- Camara ---
        frame_camara = tk.LabelFrame(self.root, text="Camara", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_camara.place(x=20, y=20, width=500, height=120)
        self.frame_camara = frame_camara

        self.lbl_camara = tk.Label(frame_camara, text="Camara sin iniciar", bg="black", fg="white")
        self.lbl_camara.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.75)

        # --- Ficha Proveedor ---
        frame_ficha = tk.LabelFrame(self.root, text="Ficha Proveedor", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_ficha.place(x=540, y=20, width=420, height=120)

        tk.Label(frame_ficha, text=f"Proveedor: {self.proveedor.nombre}", bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)
        tk.Label(frame_ficha, text=f"Rut: {self.proveedor.rut}", bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)
        tk.Label(frame_ficha, text=f"Contacto: {self.proveedor.contacto}", bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)

        # --- Boton central START ---
        self.btn_start = tk.Button(self.root, text="START", bg=self.colores["boton"], fg=self.colores["boton_texto"],
                                   font=("Segoe UI", 12, "bold"))
        self.btn_start.place(x=420, y=170, width=120, height=50)

        config_boton = ConfigBotonCamara(
            texto_inicio="START",
            texto_detener="DETENER",
            color_inicio=(self.colores["boton"], self.colores["boton_texto"]),
            color_detener=("red", "white"),
        )
        self.camara = Camara(
            self.root,
            self.lbl_camara,
            self.btn_start,
            config_boton=config_boton,
            frame_callback=self.interprete.enviar_frame,
        )
        self.btn_start.config(command=self.camara.toggle)

        # --- Boton Reporte ---
        btn_reporte = tk.Button(self.root, text="Reporte", bg=self.colores["boton"], fg=self.colores["boton_texto"])
        btn_reporte.place(x=600, y=170, width=100, height=40)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(self.root, text="Total Clasificaciones: XX",
                                      bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_totales.place(x=20, y=240, width=600, height=200)

        datos = [17.5, 27.5, 57.5, 77.5]
        etiquetas = ["Mariposa", "Cuarto", "Cuartillo", "Desecho"]

        for col in range(4):
            frame_totales.grid_columnconfigure(col, weight=1)

        for i, (valor, label) in enumerate(zip(datos, etiquetas)):
            fig, ax = plt.subplots(figsize=(1.7, 1.7), dpi=80)
            ax.pie([valor, 100 - valor],
                   labels=[f"{valor}%", ""],
                   startangle=90,
                   colors=["#5DADE2", "#EAECEE"],
                   wedgeprops={"linewidth": 0.5, "edgecolor": "white"})

            ax.set_title(label, fontsize=9)
            canvas = FigureCanvasTkAgg(fig, master=frame_totales)
            canvas.get_tk_widget().grid(row=0, column=i, padx=10, pady=15, sticky="n")

        # --- Producto Selecto ---
        frame_producto = tk.LabelFrame(self.root, text="Producto Selecto", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_producto.place(x=20, y=460, width=250, height=150)

        tk.Label(frame_producto, text="Mariposa", bg="white", relief="solid", width=12, height=5).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(frame_producto, text="Cuarto", bg="white", relief="solid", width=12, height=5).pack(side=tk.LEFT, padx=10, pady=10)

        # --- Historial ---
        frame_historial = tk.LabelFrame(self.root, text="Historial", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_historial.place(x=700, y=240, width=260, height=370)

        fechas = ["06-06-2025", "06-02-2025", "06-03-2025", "06-04-2025", "06-05-2025"]
        for f in fechas:
            tk.Label(frame_historial, text=f, bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=5)

        # --- Boton volver ---
        self.btn_volver = tk.Button(self.root, text="Volver", command=self.cerrar)
        self.btn_volver.place(x=30, y=570)

    def cerrar(self):
        if self.camara:
            self.camara.cerrar()
        if hasattr(self, "interprete") and self.interprete:
            self.interprete.cerrar()
        self.root.destroy()
