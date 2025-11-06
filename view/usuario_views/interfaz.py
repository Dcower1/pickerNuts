from pathlib import Path
import time
import tkinter as tk
from tkinter import messagebox

import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from ultralytics import YOLO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from components.utils import obtener_colores
from components import utils
from components.camara import seleccionar_backend
from components.config import FULLSCREEN

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "DAO" / "NutPickerModel.pt"
PREVIEW_SIZE = (200, 200)
COLORS = obtener_colores()

class InterfazView:
    def __init__(self, root, proveedor):
        self.root = root
        self.proveedor = proveedor
        self.colores = COLORS
        self.camera_backend = None
        self.capturando = False
        self.camara_job = None
        self.imagen_camara = None
        self._primer_frame_recibido = False
        self.btn_start_bg = self.colores["boton"]
        self.btn_start_fg = self.colores["boton_texto"]
        self.preview_size = PREVIEW_SIZE
        self.model_error = None
        self.model = self._cargar_modelo()
        self._ultima_prediccion = None
        self._ultima_prediccion_ts = 0.0
        self.fps_var = tk.StringVar(value="FPS: --.-")
        self._preparar_ventana()
        self._crear_area_desplazable()
        self.construir_interfaz()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    def construir_interfaz(self):
        self.root.title("Interfaz Clasificación")
        self.root.configure(bg=self.colores["fondo"])
        if FULLSCREEN:
            utils.aplicar_fullscreen(self.root)
        else:
            self.root.geometry("780x560")
            utils.centrar_ventana(self.root, 780, 560)

        # --- Cámara ---
        frame_camara = tk.LabelFrame(
            self.content_frame,
            text="Cámara",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_camara.place(x=20, y=20, width=240, height=240)
        self.frame_camara = frame_camara

        self.lbl_camara = tk.Label(
            frame_camara,
            text="Cámara sin iniciar",
            bg="black",
            fg="white",
        )
        self.lbl_camara.place(
            relx=0.5,
            rely=0.43,
            anchor="center",
            width=self.preview_size[0],
            height=self.preview_size[1],
        )

        self.lbl_fps = tk.Label(
            frame_camara,
            textvariable=self.fps_var,
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_fps.place(relx=0.5, rely=0.9, anchor="center")

        # --- Ficha Proveedor ---
        frame_ficha = tk.LabelFrame(
            self.content_frame,
            text="Ficha Proveedor",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_ficha.place(x=280, y=20, width=460, height=130)

        tk.Label(
            frame_ficha,
            text=f"Proveedor: {self.proveedor.nombre}",
            bg=self.colores["form_bg"],
        ).pack(anchor="w", padx=10, pady=2)
        tk.Label(
            frame_ficha,
            text=f"Rut: {self.proveedor.rut}",
            bg=self.colores["form_bg"],
        ).pack(anchor="w", padx=10, pady=2)
        tk.Label(
            frame_ficha,
            text=f"Contacto: {self.proveedor.contacto}",
            bg=self.colores["form_bg"],
        ).pack(anchor="w", padx=10, pady=2)

        # --- Botón central START ---
        self.btn_start = tk.Button(
            self.content_frame,
            text="START",
            bg=self.btn_start_bg,
            fg=self.btn_start_fg,
            font=("Segoe UI", 12, "bold"),
            command=self.toggle_camara,
        )
        self.btn_start.place(x=280, y=170, width=120, height=45)

        # --- Botón Reporte ---
        btn_reporte = tk.Button(
            self.content_frame,
            text="Reporte",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
        )
        btn_reporte.place(x=420, y=170, width=100, height=40)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(
            self.content_frame,
            text="Total Clasificaciones: XX",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_totales.place(x=20, y=280, width=460, height=170)

        datos = [17.5, 27.5, 57.5, 77.5]
        etiquetas = ["Mariposa", "Cuarto", "Cuartillo", "Desecho"]

        for col in range(4):
            frame_totales.grid_columnconfigure(col, weight=1)

        for i, (valor, label) in enumerate(zip(datos, etiquetas)):
            fig, ax = plt.subplots(figsize=(1.3, 1.3), dpi=80)
            ax.pie(
                [valor, 100 - valor],
                labels=[f"{valor}%", ""],
                startangle=90,
                colors=["#5DADE2", "#EAECEE"],
                wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
            )
            ax.set_title(label, fontsize=8)
            canvas = FigureCanvasTkAgg(fig, master=frame_totales)
            canvas.get_tk_widget().grid(row=0, column=i, padx=5, pady=10, sticky="n")

        # --- Producto Selecto ---
        frame_producto = tk.LabelFrame(
            self.content_frame,
            text="Producto Selecto",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_producto.place(x=500, y=280, width=240, height=120)

        tk.Label(
            frame_producto,
            text="Mariposa",
            bg="white",
            relief="solid",
            width=10,
            height=4,
        ).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(
            frame_producto,
            text="Cuarto",
            bg="white",
            relief="solid",
            width=10,
            height=4,
        ).pack(side=tk.LEFT, padx=10, pady=10)

        # --- Historial ---
        frame_historial = tk.LabelFrame(
            self.content_frame,
            text="Historial",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_historial.place(x=500, y=420, width=240, height=120)

        fechas = ["06-06-2025", "06-02-2025", "06-03-2025", "06-04-2025"]
        for f in fechas:
            tk.Label(frame_historial, text=f, bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)

        # --- Botón Volver ---
        self.btn_volver = tk.Button(self.content_frame, text="Volver", command=self.cerrar)
        self.btn_volver.place(x=30, y=500, width=80, height=35)
        self.root.after_idle(self.btn_start.focus_set)
        self.root.after_idle(self._ajustar_altura_contenido)

    def _preparar_ventana(self):
        parent = getattr(self.root, "master", None)
        if isinstance(self.root, tk.Toplevel):
            if parent is not None:
                self.root.transient(parent)
            try:
                self.root.grab_set()
            except tk.TclError:
                pass
        self.root.focus_force()

    def _crear_area_desplazable(self):
        self.canvas = tk.Canvas(self.root, bg=self.colores["fondo"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.content_frame = tk.Frame(self.canvas, bg=self.colores["fondo"])
        self._canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", self._actualizar_scrollregion)
        self.canvas.bind("<Configure>", self._sincronizar_ancho_contenido)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    def _actualizar_scrollregion(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sincronizar_ancho_contenido(self, event):
        self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        delta = getattr(event, "delta", 0)
        if delta:
            pasos = int(-1 * (delta / 120))
            if pasos != 0:
                self.canvas.yview_scroll(pasos, "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def _ajustar_altura_contenido(self):
        if not hasattr(self, "content_frame"):
            return
        self.content_frame.update_idletasks()
        widgets = self.content_frame.winfo_children()
        if not widgets:
            return
        max_y = max(widget.winfo_y() + widget.winfo_height() for widget in widgets)
        self.content_frame.configure(height=max_y + 40)

    def _reportar_prediccion(self, results, origen="[Clasificación][Usuario]"):
        if not results:
            return

        result = results[0]
        nombre = None
        confianza = None

        def _nombre_clase(resultado, indice):
            nombres = getattr(resultado, "names", {}) or {}
            indice_entero = int(indice)
            if isinstance(nombres, dict):
                return nombres.get(indice_entero, str(indice_entero))
            if isinstance(nombres, (list, tuple)):
                if 0 <= indice_entero < len(nombres):
                    return nombres[indice_entero]
            return str(indice_entero)

        probs = getattr(result, "probs", None)
        if probs is not None and getattr(probs, "top1", None) is not None:
            nombre = _nombre_clase(result, probs.top1)
            top_conf = getattr(probs, "top1conf", None)
            if top_conf is not None:
                confianza = float(top_conf)
        else:
            boxes = getattr(result, "boxes", None)
            conf_tensor = getattr(boxes, "conf", None) if boxes is not None else None
            cls_tensor = getattr(boxes, "cls", None) if boxes is not None else None
            if conf_tensor is not None and cls_tensor is not None:
                try:
                    conf_list = conf_tensor.tolist()
                    cls_list = cls_tensor.tolist()
                except AttributeError:
                    conf_list = list(conf_tensor)
                    cls_list = list(cls_tensor)
                if conf_list:
                    idx_max = max(range(len(conf_list)), key=lambda i: conf_list[i])
                    confianza = float(conf_list[idx_max])
                    nombre = _nombre_clase(result, cls_list[idx_max])

        if nombre is None or confianza is None:
            return

        registro = (nombre, round(confianza, 4))
        now = time.time()

        if self._ultima_prediccion == registro and now - self._ultima_prediccion_ts < 2.0:
            return

        if now - self._ultima_prediccion_ts < 2.0:
            return

        self._ultima_prediccion = registro
        self._ultima_prediccion_ts = now
        print(f"{origen} Resultado más probable: {nombre} ({confianza:.1%})", flush=True)

    # =================== CÁMARA ===================
    def toggle_camara(self):
        if self.capturando:
            self.detener_camara()
        else:
            self.iniciar_camara()

    def iniciar_camara(self):
        if self.capturando:
            return

        if not self.model:
            messagebox.showerror(
                "Modelo",
                self.model_error
                or "No se pudo cargar el modelo NutPickerModel.pt. Verifique la ruta del archivo.",
            )
            self.restaurar_boton_start()
            return

        print("[Cámara] Solicitando inicio de captura desde la interfaz.", flush=True)
        backend, error_message = self._select_camera_backend()
        if not backend:
            messagebox.showerror(
                "Cámara", error_message or "No se encontró un backend de cámara disponible."
            )
            print(f"[Cámara] No se pudo iniciar la cámara: {error_message}", flush=True)
            self.restaurar_boton_start()
            return

        self.camera_backend = backend
        self._primer_frame_recibido = False
        print(f"[Cámara] Backend seleccionado: {backend.__class__.__name__}", flush=True)
        self.capturando = True
        self.btn_start.config(text="DETENER", bg="red", fg="white")
        self.lbl_camara.config(text="Conectando...", image="")
        self.actualizar_frame()

    def actualizar_frame(self):
        if not self.camera_backend:
            self.detener_camara()
            return

        ret, frame = self.camera_backend.read()
        if not ret:
            mensaje = (
                getattr(self.camera_backend, "error_message", "")
                or "Se perdió la señal de la cámara."
            )
            print(f"[Cámara] Fallo al obtener frame: {mensaje}", flush=True)
            messagebox.showwarning("Cámara", mensaje)
            self.detener_camara()
            return

        annotated = False
        frame_to_display = frame

        if self.model:
            try:
                results = self.model(frame, imgsz=256, verbose=False)
                self._reportar_prediccion(results)
                annotated_frame = results[0].plot()
                frame_to_display = annotated_frame
                annotated = True
                inference_time = results[0].speed.get("inference", 0)
                if inference_time:
                    fps = 1000 / inference_time
                    self.fps_var.set(f"FPS: {fps:.1f}")
                else:
                    self.fps_var.set("FPS: --.-")
            except Exception as exc:
                self.fps_var.set("FPS: --.-")
                print(f"[Detección] Error ejecutando el modelo YOLO: {exc}", flush=True)
        else:
            self.fps_var.set("FPS: --.-")

        if not self._primer_frame_recibido:
            print("[Cámara] Primer frame recibido correctamente.", flush=True)
            self._primer_frame_recibido = True

        try:
            preview = cv2.resize(
                frame_to_display,
                self.preview_size,
                interpolation=cv2.INTER_AREA,
            )
        except Exception as exc:
            print(f"[Cámara] Error al escalar frame: {exc}", flush=True)
            preview = frame_to_display

        needs_rgb = annotated or getattr(self.camera_backend, "color_format", "RGB") == "BGR"
        if needs_rgb:
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

        imagen = Image.fromarray(preview)
        foto = ImageTk.PhotoImage(image=imagen)
        self.imagen_camara = foto
        self.lbl_camara.configure(image=foto, text="")
        self.lbl_camara.image = foto
        self.camara_job = self.root.after(30, self.actualizar_frame)

    def detener_camara(self):
        if self.camara_job:
            self.root.after_cancel(self.camara_job)
            self.camara_job = None
        if self.camera_backend:
            try:
                self.camera_backend.stop()
                print("[Cámara] Backend detenido desde la interfaz.", flush=True)
            finally:
                self.camera_backend = None
        self.capturando = False
        self._primer_frame_recibido = False
        self.lbl_camara.config(image="", text="Cámara detenida")
        self.lbl_camara.image = None
        self.imagen_camara = None
        self.fps_var.set("FPS: --.-")
        self._ultima_prediccion = None
        self._ultima_prediccion_ts = 0.0
        self.restaurar_boton_start()

    def restaurar_boton_start(self):
        if hasattr(self, "btn_start"):
            self.btn_start.config(text="START", bg=self.btn_start_bg, fg=self.btn_start_fg)

    def cerrar(self):
        self.detener_camara()
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        self.root.destroy()

    def _cargar_modelo(self):
        """Carga el modelo YOLO utilizado para la clasificación."""
        if not MODEL_PATH.exists():
            self.model_error = f"No se encontró el modelo en {MODEL_PATH}"
            print(f"[Modelo] {self.model_error}", flush=True)
            return None

        try:
            modelo = YOLO(str(MODEL_PATH))
        except Exception as exc:  # pragma: no cover - carga externa
            self.model_error = f"Error al cargar el modelo YOLO: {exc}"
            print(f"[Modelo] {self.model_error}", flush=True)
            return None

        self.model_error = None
        print(f"[Modelo] Modelo cargado correctamente desde {MODEL_PATH}", flush=True)
        return modelo


    def _select_camera_backend(self):
        """Delegar la selección del backend al módulo de cámara compartido."""
        return seleccionar_backend()
