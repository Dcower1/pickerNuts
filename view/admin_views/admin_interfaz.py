from pathlib import Path
import tkinter as tk
from tkinter import messagebox

import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from ultralytics import YOLO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from components import utils
from components.utils import obtener_colores
from components.camara import seleccionar_backend
from models.DAO.proveedor_dao import ProveedorDAO

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "DAO" / "NutPickerModel.pt"
PREVIEW_SIZE = (200, 200)
COLORS = obtener_colores()


class admin_InterfazProveedorView:
    def __init__(self, proveedor_dto, callback_actualizar=None):
        self.proveedor = proveedor_dto
        self.callback_actualizar = callback_actualizar
        self.editando = False

        self.colores = COLORS
        self.root = tk.Toplevel()
        self.root.title("Interfaz Clasificación - ADMIN")
        self.root.configure(bg=self.colores["fondo"])
        self.root.geometry("800x600")
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
        self.fps_var = tk.StringVar(value="FPS: --.-")

        utils.centrar_ventana(self.root, 800, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.construir_interfaz()
        self.root.mainloop()

    def construir_interfaz(self):
        # --- Cámara ---
        frame_camara = tk.LabelFrame(
            self.root,
            text="Cámara",
            bg=self.colores["form_bg"],
            fg=self.colores["texto"],
        )
        frame_camara.place(x=20, y=20, width=260, height=260)
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
        frame_ficha = tk.LabelFrame(self.root, text="Ficha Proveedor", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_ficha.place(x=510, y=20, width=270, height=120)

        self.lbl_nombre = tk.Label(frame_ficha, text=f"Proveedor: {self.proveedor.nombre}", bg=self.colores["form_bg"])
        self.lbl_nombre.pack(anchor="w", padx=10, pady=2)

        self.lbl_rut = tk.Label(frame_ficha, text=f"Rut: {self.proveedor.rut}", bg=self.colores["form_bg"])
        self.lbl_rut.pack(anchor="w", padx=10, pady=2)

        self.lbl_contacto = tk.Label(frame_ficha, text=f"Contacto: {self.proveedor.contacto}", bg=self.colores["form_bg"])
        self.lbl_contacto.pack(anchor="w", padx=10, pady=2)

        # --- Botón central START ---
        self.btn_start = tk.Button(
            self.root,
            text="START",
            bg=self.btn_start_bg,
            fg=self.btn_start_fg,
            font=("Segoe UI", 12, "bold"),
            command=self.toggle_camara,
        )
        self.btn_start.place(x=320, y=170, width=120, height=45)

        # --- Botón Reporte ---
        btn_reporte = tk.Button(self.root, text="Reporte", bg=self.colores["boton"], fg=self.colores["boton_texto"])
        btn_reporte.place(x=480, y=150, width=100, height=40)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(self.root, text="Total Clasificaciones: XX",
                                      bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_totales.place(x=20, y=300, width=480, height=180)

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

        # --- Producto Selecto ---
        frame_producto = tk.LabelFrame(self.root, text="Producto Selecto",
                                       bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_producto.place(x=520, y=300, width=250, height=120)

        tk.Label(frame_producto, text="Mariposa", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(frame_producto, text="Cuarto 🔒", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)

        # --- Historial ---
        frame_historial = tk.LabelFrame(self.root, text="Historial",
                                        bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_historial.place(x=520, y=440, width=250, height=120)

        fechas = ["06-06-2025", "06-02-2025", "06-03-2025", "06-04-2025"]
        for f in fechas:
            tk.Label(frame_historial, text=f, bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)

        # --- Botones ADMIN ---
        self.btn_editar = tk.Button(
            self.root,
            text="✏️ Editar Proveedor",
            bg="orange",
            fg="black",
            command=self.modo_edicion,
        )
        self.btn_editar.place(x=20, y=540, width=160, height=40)

        if self.proveedor.estado == 2:
            self.btn_eliminar = tk.Button(self.root, text="Activar Proveedor", bg="green", fg="white",
                                          command=self.activar_proveedor)
        else:
            self.btn_eliminar = tk.Button(self.root, text="Eliminar Proveedor", bg="red", fg="white",
                                          command=self.eliminar_proveedor)
        self.btn_eliminar.place(x=200, y=540, width=160, height=40)

        self.btn_volver = tk.Button(self.root, text="Volver", command=self.cerrar)
        self.btn_volver.place(x=380, y=540, width=80, height=40)
        self.root.after_idle(self.btn_start.focus_set)

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
        self.btn_cancelar = tk.Button(self.root, text="❌ Cancelar", bg="gray", fg="white",
                                      command=self.cancelar_edicion)
        self.btn_cancelar.place(x=560, y=410, width=100, height=40)

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
