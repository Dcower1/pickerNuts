from pathlib import Path
import time
import tkinter as tk
from tkinter import messagebox

import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import random

from components import utils
from components.camara import seleccionar_backend
from components.utils import obtener_colores
import components.config as app_config
from models.DAO.proceso_lote_dao import ProcesoLoteDAO

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "DAO" / "NutPickerModel.pt"
PREVIEW_SIZE = (200, 200)
COLORS = obtener_colores()


class InterfazViewDoble:
    def __init__(self, root, proveedores, porcentajes=None):
        if not proveedores or len(proveedores) != 2:
            raise ValueError("InterfazViewDoble requiere exactamente dos proveedores.")

        self.root = root
        self.proveedores = proveedores
        self.colores = COLORS
        self.porcentajes = self._normalizar_porcentajes(porcentajes)

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
        self.totales_labels = {}
        self._totales_job = None

        self._preparar_ventana()
        self._crear_area_desplazable()
        self.construir_interfaz()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    def construir_interfaz(self):
        self.root.title("Interfaz Clasificación - Doble Proveedor")
        self.root.configure(bg=self.colores["fondo"])
        if app_config.FULLSCREEN:
            utils.aplicar_fullscreen(self.root)
        else:
            utils.maximizar_ventana(self.root)

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

        frame_ficha = tk.LabelFrame(
            self.content_frame,
            text="Ficha Proveedores",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_ficha.place(x=280, y=20, width=460, height=140)

        for prov in self.proveedores:
            card = tk.Frame(frame_ficha, bg=self.colores["form_bg"])
            card.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(card, text=f"Proveedor: {prov.nombre}", bg=self.colores["form_bg"]).pack(anchor="w")
            tk.Label(card, text=f"RUT: {prov.rut}", bg=self.colores["form_bg"]).pack(anchor="w")
            tk.Label(card, text=f"Contacto: {prov.contacto}", bg=self.colores["form_bg"]).pack(anchor="w")
            tk.Button(
                card,
                text="Ver Historial",
                bg=self.colores["boton"],
                fg=self.colores["boton_texto"],
                command=lambda p=prov: self.mostrar_historial_proveedor(p),
            ).pack(anchor="e", pady=2)

        self.btn_start = tk.Button(
            self.content_frame,
            text="START",
            bg=self.btn_start_bg,
            fg=self.btn_start_fg,
            font=("Segoe UI", 12, "bold"),
            command=self.toggle_camara,
        )
        self.btn_start.place(x=270, y=160, width=180, height=60)

        self.btn_reporte = tk.Button(
            self.content_frame,
            text="Reporte",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            font=("Segoe UI", 12, "bold"),
            command=self._mostrar_aviso_reporte,
        )
        self.btn_reporte.place(x=480, y=160, width=180, height=60)

        frame_totales = tk.LabelFrame(
            self.content_frame,
            text="Totales de Clasificación",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_totales.place(x=20, y=280, width=460, height=170)

        grades = ("A", "B", "C", "D", "total")
        for idx, prov in enumerate(self.proveedores):
            sub = tk.LabelFrame(
                frame_totales,
                text=prov.nombre,
                bg=self.colores["form_bg"],
                fg=self.colores["texto"],
            )
            sub.grid(row=0, column=idx, padx=8, pady=10, sticky="nsew")
            frame_totales.grid_columnconfigure(idx, weight=1)

            labels = {}
            for grade in grades:
                label = tk.Label(
                    sub,
                    text=f"{grade}: --",
                    bg=self.colores["form_bg"],
                    fg=self.colores["texto"],
                    anchor="w",
                )
                label.pack(anchor="w", padx=8, pady=2)
                labels[grade] = label
            self.totales_labels[prov.id_proveedor] = labels

        self.frame_historial = tk.LabelFrame(
            self.content_frame,
            text="Historial",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        self.frame_historial.place(x=500, y=280, width=240, height=200)

        self.btn_volver = tk.Button(
            self.content_frame,
            text="Volver",
            command=self.cerrar,
        )
        self.btn_volver.place(x=30, y=500, width=80, height=35)

        self.root.after_idle(self.btn_start.focus_set)
        self.root.after_idle(self._ajustar_altura_contenido)
        self.mostrar_historial_proveedor(self.proveedores[0])
        self.actualizar_totales()
        self._programar_actualizacion_totales()

    def mostrar_historial_proveedor(self, proveedor):
        for widget in self.frame_historial.winfo_children():
            widget.destroy()

        tk.Label(
            self.frame_historial,
            text=f"Historial de {proveedor.nombre}",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=10, pady=5)

        try:
            historial = ProcesoLoteDAO.obtener_historial_fechas(proveedor.id_proveedor)
        except Exception as exc:
            historial = []
            print(f"[Historial][Doble] Error obteniendo historial: {exc}", flush=True)

        if not historial:
            tk.Label(
                self.frame_historial,
                text="Sin historial registrado.",
                bg=self.colores["form_bg"],
                fg=self.colores["texto"],
            ).pack(anchor="w", padx=10, pady=2)
            return

        for fecha in historial:
            tk.Label(
                self.frame_historial,
                text=fecha,
                bg=self.colores["form_bg"],
                fg=self.colores["texto"],
            ).pack(anchor="w", padx=15, pady=2)

    def _programar_actualizacion_totales(self):
        self.actualizar_totales()
        self._totales_job = self.root.after(10000, self._programar_actualizacion_totales)

    def actualizar_totales(self):
        for prov in self.proveedores:
            labels = self.totales_labels.get(prov.id_proveedor)
            if not labels:
                continue
            try:
                totales = ProcesoLoteDAO.obtener_totales_actuales(prov.id_proveedor)
            except Exception as exc:
                totales = None
                print(f"[Totales][Doble] Error consultando totales: {exc}", flush=True)

            if not totales:
                totales = {"A": 0, "B": 0, "C": 0, "D": 0, "total": 0}

            for clave, label in labels.items():
                valor = totales.get(clave, 0)
                label.config(text=f"{clave}: {valor}")

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

        backend, error_message = self._select_camera_backend()
        if not backend:
            messagebox.showerror(
                "Cámara",
                error_message or "No se encontró un backend de cámara disponible.",
            )
            self.restaurar_boton_start()
            return

        self.camera_backend = backend
        self._primer_frame_recibido = False
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
            messagebox.showwarning("Cámara", mensaje)
            self.detener_camara()
            return

        annotated = False
        frame_to_display = frame

        if self.model:
            try:
                results = self.model(frame, imgsz=256, verbose=False)
                clase_detectada = self._reportar_prediccion(results, origen="[Clasificación][Doble]")
                if clase_detectada:
                    self._procesar_deteccion(clase_detectada)
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
                print(f"[Detección][Doble] Error ejecutando YOLO: {exc}", flush=True)
        else:
            self.fps_var.set("FPS: --.-")

        if not self._primer_frame_recibido:
            self._primer_frame_recibido = True
            print("[Cámara][Doble] Primer frame recibido correctamente.", flush=True)

        try:
            preview = cv2.resize(
                frame_to_display,
                self.preview_size,
                interpolation=cv2.INTER_AREA,
            )
        except Exception as exc:
            print(f"[Cámara][Doble] Error al escalar frame: {exc}", flush=True)
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
        if self._totales_job:
            self.root.after_cancel(self._totales_job)
            self._totales_job = None
        self.detener_camara()
        self.root.destroy()

    def _mostrar_aviso_reporte(self):
        messagebox.showinfo("Reporte", "Solicitud de envio de reporte solicitada")

    def _procesar_deteccion(self, etiqueta_modelo):
        grade = self._mapear_grade(etiqueta_modelo)
        if not grade:
            return

        indice = self._seleccionar_proveedor_destino()
        proveedor_destino = self.proveedores[indice]
        try:
            ProcesoLoteDAO.registrar_clasificacion(proveedor_destino.id_proveedor, grade)
        except Exception as exc:
            print(f"[Clasificación][Doble] Error registrando resultado: {exc}", flush=True)
            return

        print(
            f"[Clasificación][Doble] Registro asignado a {proveedor_destino.nombre} con grado {grade}.",
            flush=True,
        )
        self.actualizar_totales()

    def _normalizar_porcentajes(self, porcentajes):
        if not porcentajes:
            return [0.5, 0.5]

        try:
            valores = [max(float(p), 0.0) for p in porcentajes[:2]]
        except (TypeError, ValueError):
            return [0.5, 0.5]

        while len(valores) < 2:
            valores.append(0.0)

        total = sum(valores)
        if total <= 0:
            return [0.5, 0.5]

        return [v / total for v in valores[:2]]

    def _seleccionar_proveedor_destino(self):
        if not self.porcentajes:
            return 0

        acumulado = 0.0
        objetivo = random.random()
        for idx, prob in enumerate(self.porcentajes):
            acumulado += prob
            if objetivo <= acumulado:
                return idx
        return min(len(self.proveedores) - 1, len(self.porcentajes) - 1)

    def _mapear_grade(self, etiqueta_modelo):
        if not etiqueta_modelo:
            return None

        etiqueta_normalizada = etiqueta_modelo.strip().lower()
        mapeo = {
            "a": "A",
            "b": "B",
            "c": "C",
            "d": "D",
            "mariposa": "A",
            "cuarto": "B",
            "cuartillo": "C",
            "desecho": "D",
        }
        return mapeo.get(etiqueta_normalizada)

    def _reportar_prediccion(self, results, origen="[Clasificación][Doble]"):
        if not results:
            return None

        result = results[0]
        nombre = None
        confianza = None

        def _nombre_clase(resultado, indice):
            nombres = getattr(resultado, "names", {}) or {}
            indice_entero = int(indice)
            if isinstance(nombres, dict):
                return nombres.get(indice_entero, str(indice_entero))
            if isinstance(nombres, (list, tuple)) and 0 <= indice_entero < len(nombres):
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
            return None

        registro = (nombre, round(confianza, 4))
        now = time.time()

        if self._ultima_prediccion == registro and now - self._ultima_prediccion_ts < 2.0:
            return None

        if now - self._ultima_prediccion_ts < 2.0:
            return None

        self._ultima_prediccion = registro
        self._ultima_prediccion_ts = now
        print(f"{origen} Resultado más probable: {nombre} ({confianza:.1%})", flush=True)
        return nombre

    def _cargar_modelo(self):
        if not MODEL_PATH.exists():
            self.model_error = f"No se encontró el modelo en {MODEL_PATH}"
            print(f"[Modelo][Doble] {self.model_error}", flush=True)
            return None

        try:
            modelo = YOLO(str(MODEL_PATH))
        except Exception as exc:
            self.model_error = f"Error al cargar el modelo YOLO: {exc}"
            print(f"[Modelo][Doble] {self.model_error}", flush=True)
            return None

        self.model_error = None
        print(f"[Modelo][Doble] Modelo cargado correctamente desde {MODEL_PATH}", flush=True)
        return modelo

    def _select_camera_backend(self):
        return seleccionar_backend()

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
