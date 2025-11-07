from pathlib import Path
from datetime import datetime
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from ultralytics import YOLO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from components import utils
from components.utils import obtener_colores
from components.camara import seleccionar_backend
import components.config as app_config
from models.DAO.proveedor_dao import ProveedorDAO
from models.DAO.classification_session_dao import ClassificationSessionDAO

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "DAO" / "NutPickerModel.pt"
PREVIEW_SIZE = (200, 200)
COLORS = obtener_colores()
CLASS_MAPPING = {
    "mariposa": ("A", "Butterfly"),
    "butterfly": ("A", "Butterfly"),
    "cuarto": ("B", "Quarter"),
    "quarter": ("B", "Quarter"),
    "cuartillo": ("C", "Half-Quarter"),
    "half-quarter": ("C", "Half-Quarter"),
    "half quarter": ("C", "Half-Quarter"),
    "halfquarter": ("C", "Half-Quarter"),
    "desecho": ("D", "Discard"),
    "descarte": ("D", "Discard"),
    "discard": ("D", "Discard"),
}
CATEGORY_CONFIG = {
    "A": {"label": "Butterfly", "color": "#5DADE2"},
    "B": {"label": "Quarter", "color": "#58D68D"},
    "C": {"label": "Half-Quarter", "color": "#F7DC6F"},
    "D": {"label": "Discard", "color": "#EC7063"},
}


class admin_InterfazProveedorView:
    def __init__(self, proveedor_dto, callback_actualizar=None):
        self.proveedor = proveedor_dto
        self.callback_actualizar = callback_actualizar
        self.editando = False
        self.produccion_activa = False

        self.colores = COLORS
        self.root = tk.Toplevel()
        self.root.title("Interfaz Clasificación - ADMIN")
        self.root.configure(bg=self.colores["fondo"])
        if app_config.FULLSCREEN:
            utils.aplicar_fullscreen(self.root)
        else:
            utils.maximizar_ventana(self.root)
        self._preparar_ventana()

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
        self._sesion_clasificacion = None
        self._categoria_orden = ["A", "B", "C", "D"]
        self._chart_info = {}
        self.frame_totales = None
        self.frame_historial = None
        self.historial_tree = None
        self.historial_page = 1
        self.historial_total_pages = 1
        self.historial_page_size = 6
        self.lbl_historial_pagina = None
        self.btn_historial_prev = None
        self.btn_historial_next = None
        self.fps_var = tk.StringVar(value="FPS: --.-")

        self._crear_area_desplazable()
        if not app_config.FULLSCREEN:
            utils.maximizar_ventana(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.construir_interfaz()
        self.root.mainloop()

    def construir_interfaz(self):
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
        frame_ficha = tk.LabelFrame(self.content_frame, text="Ficha Proveedor", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_ficha.place(x=280, y=20, width=460, height=130)

        self.lbl_nombre = tk.Label(frame_ficha, text=f"Proveedor: {self.proveedor.nombre}", bg=self.colores["form_bg"])
        self.lbl_nombre.pack(anchor="w", padx=10, pady=2)

        self.lbl_rut = tk.Label(frame_ficha, text=f"Rut: {self.proveedor.rut}", bg=self.colores["form_bg"])
        self.lbl_rut.pack(anchor="w", padx=10, pady=2)

        self.lbl_contacto = tk.Label(frame_ficha, text=f"Contacto: {self.proveedor.contacto}", bg=self.colores["form_bg"])
        self.lbl_contacto.pack(anchor="w", padx=10, pady=2)

        # --- Botón central START ---
        self.btn_start = tk.Button(
            self.content_frame,
            text="START",
            bg=self.btn_start_bg,
            fg=self.btn_start_fg,
            font=("Segoe UI", 12, "bold"),
            command=self.toggle_camara,
        )
        self.btn_start.place(x=270, y=160, width=180, height=60)

        # --- Botón Reporte ---
        self.btn_reporte = tk.Button(
            self.content_frame,
            text="Reporte",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            font=("Segoe UI", 12, "bold"),
            command=self._mostrar_aviso_reporte,
        )
        self.btn_reporte.place(x=480, y=160, width=180, height=60)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(self.content_frame, text="Total de clasificaciones General: 0",
                                      bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_totales.place(x=20, y=280, width=460, height=170)
        self.frame_totales = frame_totales
        self._crear_graficos_totales(frame_totales)

        # --- Producto Selecto ---
        frame_producto = tk.LabelFrame(self.content_frame, text="Producto Selecto",
                                       bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_producto.place(x=500, y=280, width=240, height=120)

        tk.Label(frame_producto, text="Mariposa", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(frame_producto, text="Cuarto 🔒", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)

        # --- Historial ---
        self._crear_historial_ui()

        # --- Botones ADMIN ---
        self.btn_editar = tk.Button(
            self.content_frame,
            text="✏️ Editar Proveedor",
            bg="orange",
            fg="black",
            command=self.modo_edicion,
        )
        self.btn_editar.place(x=20, y=690, width=150, height=38)

        if self.proveedor.estado == 2:
            self.btn_eliminar = tk.Button(self.content_frame, text="Activar Proveedor", bg="green", fg="white",
                                          command=self.activar_proveedor)
        else:
            self.btn_eliminar = tk.Button(self.content_frame, text="Eliminar Proveedor", bg="red", fg="white",
                                          command=self.eliminar_proveedor)
        self.btn_eliminar.place(x=190, y=690, width=150, height=38)

        self.btn_volver = tk.Button(self.content_frame, text="Volver", command=self.cerrar)
        self.btn_volver.place(x=360, y=690, width=90, height=38)
        self.root.after_idle(self.btn_start.focus_set)
        self.root.after_idle(self._ajustar_altura_contenido)

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

        print("[Cámara][Admin] Solicitando inicio de captura.", flush=True)
        backend, error_message = self._select_camera_backend()
        if not backend:
            messagebox.showerror(
                "Cámara", error_message or "No se encontró un backend de cámara disponible."
            )
            print(f"[Cámara][Admin] No se pudo iniciar la cámara: {error_message}", flush=True)
            self.restaurar_boton_start()
            return

        self.camera_backend = backend
        self._primer_frame_recibido = False
        print(f"[Cámara][Admin] Backend seleccionado: {backend.__class__.__name__}", flush=True)
        if not self._iniciar_sesion_clasificacion():
            self.restaurar_boton_start()
            return
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
            print(f"[Cámara][Admin] Fallo al obtener frame: {mensaje}", flush=True)
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
                print(f"[Detección][Admin] Error ejecutando el modelo YOLO: {exc}", flush=True)
        else:
            self.fps_var.set("FPS: --.-")

        if not self._primer_frame_recibido:
            print("[Cámara][Admin] Primer frame recibido correctamente.", flush=True)
            self._primer_frame_recibido = True

        try:
            preview = cv2.resize(
                frame_to_display,
                self.preview_size,
                interpolation=cv2.INTER_AREA,
            )
        except Exception as exc:
            print(f"[Cámara][Admin] Error al escalar frame: {exc}", flush=True)
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
                print("[Cámara][Admin] Backend detenido.", flush=True)
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
        self._cerrar_sesion_clasificacion()
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

    def _mostrar_aviso_reporte(self):
        messagebox.showinfo("Reporte", "Solicitud de envio de reporte solicitada")

    # ----------------- FUNCIONES ADMIN -----------------
    def eliminar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Eliminar proveedor?"):
            exito = ProveedorDAO.eliminar_logico(self.proveedor.id_proveedor)
            if exito:
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.cerrar()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el proveedor.")

    def activar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Activar proveedor?"):
            exito = ProveedorDAO.activar_proveedor(self.proveedor.id_proveedor)
            if exito:
                messagebox.showinfo("Éxito", "Proveedor activado correctamente.")
                self.proveedor.estado = 1
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.cerrar()
            else:
                messagebox.showerror("Error", "No se pudo activar el proveedor.")

    def modo_edicion(self):
        if self.editando:
            return
        self.editando = True

        self.lbl_nombre.pack_forget()
        self.lbl_contacto.pack_forget()

        self.entry_nombre = tk.Entry(self.lbl_nombre.master, font=("Arial", 12))
        self.entry_nombre.insert(0, self.proveedor.nombre)
        self.entry_nombre.pack(anchor="w", padx=10, pady=2)

        self.entry_contacto = tk.Entry(self.lbl_contacto.master, font=("Arial", 12))
        self.entry_contacto.insert(0, self.proveedor.contacto)
        self.entry_contacto.pack(anchor="w", padx=10, pady=2)
        self.entry_nombre.focus_set()

        self.btn_editar.config(text="💾 Guardar", command=self.guardar_cambios)
        self.btn_cancelar = tk.Button(self.content_frame, text="❌ Cancelar", bg="gray", fg="white",
                                      command=self.cancelar_edicion)
        self.btn_cancelar.place(x=560, y=690, width=100, height=40)

    def guardar_cambios(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        nuevo_contacto = self.entry_contacto.get().strip()
        nuevo_rut = self.proveedor.rut

        if not nuevo_nombre or not nuevo_contacto:
            messagebox.showerror("Error", "Campos vacíos.")
            self.entry_nombre.focus_force()
            return

        actualizado = ProveedorDAO.actualizar(self.proveedor.id_proveedor, nuevo_nombre, nuevo_rut, nuevo_contacto)
        if actualizado:
            messagebox.showinfo("Éxito", "Proveedor actualizado correctamente.")
            self.proveedor.nombre = nuevo_nombre
            self.proveedor.contacto = nuevo_contacto

            self.entry_nombre.destroy()
            self.entry_contacto.destroy()
            self.btn_cancelar.destroy()
            self.editando = False

            self.lbl_nombre.config(text=f"Proveedor: {nuevo_nombre}")
            self.lbl_contacto.config(text=f"Contacto: {nuevo_contacto}")
            self.lbl_nombre.pack(anchor="w", padx=10, pady=2)
            self.lbl_contacto.pack(anchor="w", padx=10, pady=2)

            self.btn_editar.config(text="✏️ Editar Proveedor", command=self.modo_edicion)

            if self.callback_actualizar:
                self.callback_actualizar()
            self.cerrar()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el proveedor.")

    def cancelar_edicion(self):
        self.entry_nombre.destroy()
        self.entry_contacto.destroy()
        self.btn_cancelar.destroy()
        self.editando = False

        self.lbl_nombre.pack(anchor="w", padx=10, pady=2)
        self.lbl_contacto.pack(anchor="w", padx=10, pady=2)
        self.btn_editar.config(text="✏️ Editar Proveedor", command=self.modo_edicion)
        self.btn_start.focus_set()

    def _cargar_modelo(self):
        """Carga el modelo YOLO utilizado en la interfaz de administrador."""
        if not MODEL_PATH.exists():
            self.model_error = f"No se encontró el modelo en {MODEL_PATH}"
            print(f"[Modelo][Admin] {self.model_error}", flush=True)
            return None

        try:
            modelo = YOLO(str(MODEL_PATH))
        except Exception as exc:  # pragma: no cover - carga externa
            self.model_error = f"Error al cargar el modelo YOLO: {exc}"
            print(f"[Modelo][Admin] {self.model_error}", flush=True)
            return None

        self.model_error = None
        print(f"[Modelo][Admin] Modelo cargado correctamente desde {MODEL_PATH}", flush=True)
        return modelo

    def _select_camera_backend(self):
        """Delegar la selección del backend al módulo compartido de cámara."""
        return seleccionar_backend()

    def _preparar_ventana(self):
        parent = getattr(self.root, "master", None)
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

    # ----------------- HISTORIAL -----------------
    def _crear_historial_ui(self):
        self.frame_historial = tk.LabelFrame(
            self.content_frame,
            text="Historial de Clasificaciones",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        self.frame_historial.place(x=20, y=470, width=720, height=230)
        self.frame_historial.grid_columnconfigure(0, weight=1)
        self.frame_historial.grid_rowconfigure(0, weight=1)

        columnas = [
            ("fecha", "Fecha y hora", 150),
            ("total", "Total nueces", 100),
            ("mariposa", "Mariposa", 90),
            ("cuarto", "Cuartos", 80),
            ("cuartillo", "Cuartillos", 90),
            ("descarte", "Descartes", 90),
            ("promedio", "Tamaño promedio", 140),
        ]
        self.historial_tree = ttk.Treeview(
            self.frame_historial,
            columns=[c[0] for c in columnas],
            show="headings",
            height=6,
        )
        for nombre, texto, ancho in columnas:
            self.historial_tree.heading(nombre, text=texto)
            self.historial_tree.column(nombre, width=ancho, anchor="center", stretch=False)
        self.historial_tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)

        scroll_y = ttk.Scrollbar(self.frame_historial, orient="vertical", command=self.historial_tree.yview)
        scroll_x = ttk.Scrollbar(self.frame_historial, orient="horizontal", command=self.historial_tree.xview)
        self.historial_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.grid(row=0, column=1, sticky="ns", pady=5, padx=(0, 5))
        scroll_x.grid(row=1, column=0, sticky="ew", padx=5)

        pag_frame = tk.Frame(self.frame_historial, bg=self.colores["form_bg"])
        pag_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 5))
        pag_frame.columnconfigure(1, weight=1)

        self.btn_historial_prev = tk.Button(
            pag_frame, text="◀", width=4, command=lambda: self._cambiar_pagina_historial(-1)
        )
        self.btn_historial_prev.grid(row=0, column=0, padx=5)

        self.lbl_historial_pagina = tk.Label(
            pag_frame,
            text="Página 1/1",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_historial_pagina.grid(row=0, column=1, padx=5)

        self.btn_historial_next = tk.Button(
            pag_frame, text="▶", width=4, command=lambda: self._cambiar_pagina_historial(1)
        )
        self.btn_historial_next.grid(row=0, column=2, padx=5)

        self._cargar_historial()

    def _cargar_historial(self):
        if not self.historial_tree:
            return
        supplier_id = getattr(self.proveedor, "id_proveedor", 0) or 0
        if not supplier_id:
            self.historial_page = 1
            self.historial_total_pages = 1
            self._render_historial_rows([])
            return

        try:
            datos = ClassificationSessionDAO.obtener_historial_metrics(
                int(supplier_id),
                page=self.historial_page,
                page_size=self.historial_page_size,
            )
        except Exception as exc:
            print(f"[Historial][Admin] Error al consultar la base de datos: {exc}", flush=True)
            datos = {"rows": [], "page": 1, "total_pages": 1}

        self.historial_page = datos.get("page", 1) or 1
        self.historial_total_pages = datos.get("total_pages", 1) or 1
        filas = datos.get("rows") or []
        self._render_historial_rows(filas)

    def _render_historial_rows(self, filas):
        if not self.historial_tree:
            return
        for child in self.historial_tree.get_children():
            self.historial_tree.delete(child)

        if not filas:
            self.historial_tree.insert(
                "",
                "end",
                values=("Sin registros", "", "", "", "", "", ""),
            )
        else:
            for fila in filas:
                fecha = self._formatear_historial_fecha(fila.get("date"))
                avg_size = fila.get("avg_size")
                if isinstance(avg_size, (int, float)):
                    avg_text = f"{avg_size:.2f}"
                else:
                    avg_text = "-"
                self.historial_tree.insert(
                    "",
                    "end",
                    values=(
                        fecha,
                        fila.get("total_nuts", 0),
                        fila.get("count_A", 0),
                        fila.get("count_B", 0),
                        fila.get("count_C", 0),
                        fila.get("count_D", 0),
                        avg_text,
                    ),
                )

        if self.lbl_historial_pagina:
            self.lbl_historial_pagina.config(
                text=f"Página {self.historial_page}/{self.historial_total_pages}"
            )
        self._actualizar_controles_historial()

    def _actualizar_controles_historial(self):
        state_prev = tk.DISABLED if self.historial_page <= 1 else tk.NORMAL
        state_next = (
            tk.DISABLED
            if self.historial_page >= max(self.historial_total_pages, 1)
            else tk.NORMAL
        )
        if self.btn_historial_prev:
            self.btn_historial_prev.config(state=state_prev)
        if self.btn_historial_next:
            self.btn_historial_next.config(state=state_next)

    def _cambiar_pagina_historial(self, desplazamiento):
        total_paginas = max(self.historial_total_pages, 1)
        nueva_pagina = min(max(1, self.historial_page + desplazamiento), total_paginas)
        if nueva_pagina == self.historial_page:
            return
        self.historial_page = nueva_pagina
        self._cargar_historial()

    @staticmethod
    def _formatear_historial_fecha(fecha_str):
        if not fecha_str:
            return "-"
        try:
            return datetime.fromisoformat(str(fecha_str)).strftime("%d-%m-%Y %H:%M")
        except ValueError:
            return str(fecha_str)

    def _crear_graficos_totales(self, frame_totales):
        self._chart_info = {}
        for col in range(len(self._categoria_orden)):
            frame_totales.grid_columnconfigure(col, weight=1)

        for idx, categoria in enumerate(self._categoria_orden):
            config = CATEGORY_CONFIG[categoria]
            fig, ax = plt.subplots(figsize=(1.3, 1.3), dpi=80)
            ax.axis("equal")
            ax.set_title(config["label"], fontsize=8)
            canvas = FigureCanvasTkAgg(fig, master=frame_totales)
            canvas.get_tk_widget().grid(row=0, column=idx, padx=5, pady=10, sticky="n")
            self._chart_info[categoria] = {
                "ax": ax,
                "canvas": canvas,
                "label": config["label"],
                "color": config["color"],
            }

        self._actualizar_totales_general()

    def _render_graficos(self, counts, total, es_sesion):
        if not self.frame_totales or not self._chart_info:
            return

        counts = {clave: int(counts.get(clave, 0) or 0) for clave in self._categoria_orden}
        total_calculado = sum(counts.values())
        if es_sesion and self._sesion_clasificacion is not None:
            total_calculado = max(total_calculado, int(self._sesion_clasificacion.total_nuts))
        total_calculado = max(total_calculado, int(total or 0))

        if es_sesion:
            self.frame_totales.configure(
                text=f"Total de Clasificaciones de sesión actual: {total_calculado}"
            )
        else:
            self.frame_totales.configure(
                text=f"Total de Clasificaciones General: {total_calculado}"
            )

        total_para_grafico = max(total_calculado, 1)

        for categoria in self._categoria_orden:
            info = self._chart_info[categoria]
            ax = info["ax"]
            valor = counts.get(categoria, 0)
            ax.clear()
            ax.axis("equal")

            if total_calculado > 0:
                porcentaje = (valor / total_calculado) * 100 if total_calculado else 0
                restante = max(total_para_grafico - valor, 0)
                datos = [valor, restante]
                if restante == 0:
                    datos[1] = 0.0001
                ax.pie(
                    datos,
                    startangle=90,
                    colors=[info["color"], "#EAECEE"],
                    wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
                )
                titulo = f"{info['label']}: {valor} ({porcentaje:.0f}%)"
            else:
                ax.pie(
                    [1],
                    startangle=90,
                    colors=["#EAECEE"],
                    wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
                )
                titulo = f"{info['label']}: 0"

            ax.set_title(titulo, fontsize=8)
            ax.text(0, 0, str(valor), ha="center", va="center", fontsize=9, color="#333333")
            info["canvas"].draw_idle()

    def _actualizar_graficos_sesion(self):
        if not self._sesion_clasificacion:
            return
        counts = self._sesion_clasificacion.counts
        total = self._sesion_clasificacion.total_nuts
        self._render_graficos(counts, total, es_sesion=True)

    def _actualizar_totales_general(self):
        supplier_id = getattr(self.proveedor, "id_proveedor", 0) or 0
        if supplier_id:
            counts, total = ClassificationSessionDAO.obtener_totales_proveedor(int(supplier_id))
        else:
            counts = {clave: 0 for clave in self._categoria_orden}
            total = 0
        self._render_graficos(counts, total, es_sesion=False)
        self._cargar_historial()

    def _mapear_clase(self, nombre_clase):
        if not nombre_clase:
            return None
        clave = str(nombre_clase).strip().lower()
        return CLASS_MAPPING.get(clave)

    def _iniciar_sesion_clasificacion(self):
        if self._sesion_clasificacion:
            return True
        supplier_id = getattr(self.proveedor, "id_proveedor", 0) or 0
        try:
            self._sesion_clasificacion = ClassificationSessionDAO.iniciar_sesion(int(supplier_id))
            print(
                f"[Clasificación][Admin] Sesión iniciada (ID: {self._sesion_clasificacion.classification_id}) para proveedor {supplier_id}.",
                flush=True,
            )
            self._actualizar_graficos_sesion()
            return True
        except Exception as exc:
            self._sesion_clasificacion = None
            print(f"[Clasificación][Admin] No se pudo iniciar la sesión: {exc}", flush=True)
            messagebox.showerror("Base de datos", f"No se pudo iniciar la sesión de clasificación.\n{exc}")
            self._actualizar_totales_general()
            return False

    def _registrar_detalle_clasificacion(self, categoria, shape):
        if not self._sesion_clasificacion:
            return
        try:
            self._sesion_clasificacion.registrar_detalle(categoria, shape)
            print(
                f"[Clasificación][Admin] Registrada nuez como '{shape}' (categoría {categoria}). Total actual: {self._sesion_clasificacion.total_nuts}",
                flush=True,
            )
            self._actualizar_graficos_sesion()
        except Exception as exc:
            print(f"[Clasificación][Admin] Error al registrar detalle: {exc}", flush=True)

    def _cerrar_sesion_clasificacion(self):
        if not self._sesion_clasificacion:
            return
        try:
            self._sesion_clasificacion.finalizar()
            print(
                f"[Clasificación][Admin] Sesión {self._sesion_clasificacion.classification_id} finalizada con total {self._sesion_clasificacion.total_nuts}.",
                flush=True,
            )
        except Exception as exc:
            print(f"[Clasificación][Admin] Error al finalizar la sesión: {exc}", flush=True)
        finally:
            self._sesion_clasificacion = None
            self._actualizar_totales_general()

    def _reportar_prediccion(self, results, origen="[Clasificación][Admin]"):
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
        mapeo = self._mapear_clase(nombre)
        if mapeo:
            categoria, shape = mapeo
            self._registrar_detalle_clasificacion(categoria, shape)
