import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import cv2

from components.utils import obtener_colores
from components import utils
from models.DAO.proceso_lote_dao import ProcesoLoteDAO  # <- Import necesario

COLORS = obtener_colores()


class InterfazViewDoble:
    def __init__(self, root, proveedores):
        """
        proveedores: lista de dos objetos proveedor
        """
        self.root = root
        self.proveedores = proveedores
        self.colores = COLORS
        self.cap = None
        self.capturando = False
        self.camara_job = None
        self.imagen_camara = None
        self.btn_start_bg = self.colores["boton"]
        self.btn_start_fg = self.colores["boton_texto"]
        self.frame_historial = None
        self.btn_volver = None
        self.construir_interfaz()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    def construir_interfaz(self):
        self.root.title("Interfaz Clasificación - Doble Proveedor")
        self.root.configure(bg=self.colores["fondo"])
        self.root.geometry("800x480")
        utils.centrar_ventana(self.root, 800, 480)

        # --- Cámara ---
        frame_camara = tk.LabelFrame(self.root, text="Cámara", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_camara.place(x=20, y=20, width=470, height=120)
        self.frame_camara = frame_camara

        self.lbl_camara = tk.Label(frame_camara, text="Cámara sin iniciar", bg="black", fg="white")
        self.lbl_camara.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.75)

        # --- Ficha Proveedores ---
        frame_ficha = tk.LabelFrame(self.root, text="Ficha Proveedores", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_ficha.place(x=510, y=20, width=270, height=120)

        for prov in self.proveedores:
            btn = tk.Button(frame_ficha, text=f"{prov.nombre}\n{prov.rut}", bg="white", relief="raised",
                            command=lambda p=prov: self.mostrar_historial_proveedor(p))
            btn.pack(fill=tk.X, padx=10, pady=2)

        # --- Botón central START ---
        self.btn_start = tk.Button(self.root, text="START", bg=self.btn_start_bg, fg=self.btn_start_fg,
                                   font=("Segoe UI", 12, "bold"), command=self.toggle_camara)
        self.btn_start.place(x=340, y=150, width=120, height=45)

        # --- Botón Reporte ---
        btn_reporte = tk.Button(self.root, text="Reporte", bg=self.colores["boton"], fg=self.colores["boton_texto"])
        btn_reporte.place(x=480, y=150, width=100, height=40)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(self.root, text="Total Clasificaciones: XX",
                                      bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_totales.place(x=20, y=210, width=480, height=180)

        datos = [17.5, 27.5, 57.5, 77.5]
        etiquetas = ["Mariposa", "Cuarto", "Cuartillo", "Desecho"]

        for col in range(4):
            frame_totales.grid_columnconfigure(col, weight=1)

        for i, (valor, label) in enumerate(zip(datos, etiquetas)):
            fig, ax = plt.subplots(figsize=(1.5, 1.5), dpi=80)
            ax.pie([valor, 100 - valor],
                   labels=[f"{valor}%", ""],
                   startangle=90,
                   colors=["#5DADE2", "#EAECEE"],
                   wedgeprops={"linewidth": 0.5, "edgecolor": "white"})
            ax.set_title(label, fontsize=8)
            canvas = FigureCanvasTkAgg(fig, master=frame_totales)
            canvas.get_tk_widget().grid(row=0, column=i, padx=5, pady=10, sticky="n")

        # --- Historial ---
        self.frame_historial = tk.LabelFrame(self.root, text="Historial",
                                             bg=self.colores["form_bg"], fg=self.colores["texto"])
        self.frame_historial.place(x=520, y=210, width=250, height=240)

        # --- Botón Volver (solo visible si cámara no está activa) ---
        self.btn_volver = tk.Button(self.root, text="Volver", command=self.cerrar)
        self.actualizar_volver()

    def mostrar_historial_proveedor(self, proveedor):
        for widget in self.frame_historial.winfo_children():
            widget.destroy()

        tk.Label(self.frame_historial, text=f"Historial: {proveedor.nombre}", 
                bg=self.colores["form_bg"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=5, pady=2)

        historial = ProcesoLoteDAO.obtener_historial_fechas(proveedor.id_proveedor)

        if not historial:
            tk.Label(self.frame_historial, text="Sin historial", bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)
        else:
            for fecha in historial:
                tk.Label(self.frame_historial, text=fecha, bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)


    # =================== CÁMARA ===================
    def toggle_camara(self):
        if self.capturando:
            self.detener_camara()
        else:
            self.iniciar_camara()

    def iniciar_camara(self):
        if self.capturando:
            return
        if self.cap:
            self.cap.release()
            self.cap = None
        try:
            if hasattr(cv2, "CAP_DSHOW"):
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(0)
        except Exception:
            self.cap = cv2.VideoCapture(0)
        if not self.cap or not self.cap.isOpened():
            if self.cap:
                self.cap.release()
            self.cap = None
            messagebox.showerror("Cámara", "No se pudo acceder a la cámara.")
            self.restaurar_boton_start()
            self.root.destroy()
            return
        self.capturando = True
        self.btn_start.config(text="DETENER", bg="red", fg="white")
        self.actualizar_volver()
        self.actualizar_frame()

    def actualizar_frame(self):
        if not self.cap or not self.cap.isOpened():
            self.detener_camara()
            return
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showwarning("Cámara", "Se perdió la señal de la cámara.")
            self.detener_camara()
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagen = Image.fromarray(frame)
        ancho = self.lbl_camara.winfo_width()
        alto = self.lbl_camara.winfo_height()
        if ancho < 10 or alto < 10:
            ancho, alto = 480, 320
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)
        foto = ImageTk.PhotoImage(image=imagen)
        self.imagen_camara = foto
        self.lbl_camara.configure(image=foto, text="")
        self.lbl_camara.image = foto
        self.camara_job = self.root.after(30, self.actualizar_frame)

    def detener_camara(self):
        if self.camara_job:
            self.root.after_cancel(self.camara_job)
            self.camara_job = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.capturando = False
        self.lbl_camara.config(image="", text="Cámara detenida")
        self.imagen_camara = None
        self.restaurar_boton_start()
        self.actualizar_volver()

    def restaurar_boton_start(self):
        if hasattr(self, "btn_start"):
            self.btn_start.config(text="START", bg=self.btn_start_bg, fg=self.btn_start_fg)

    def actualizar_volver(self):
        """Muestra u oculta el botón volver según estado de cámara"""
        if self.capturando:
            if self.btn_volver:
                self.btn_volver.place_forget()
        else:
            if self.btn_volver:
                self.btn_volver.place(x=30, y=410, width=80, height=35)

    def cerrar(self):
        self.detener_camara()
        self.root.destroy()
