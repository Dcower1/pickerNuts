import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageTk

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from components.camara import RPiCamBackend


class RPiCamTkDemo:
    """Ventana sencilla que muestra el flujo de rpicam dentro de Tkinter."""

    def __init__(self, root):
        self.root = root
        self.backend = RPiCamBackend()
        self.frame_job = None
        self.imagen = None
        self._configurar_ui()
        self._iniciar_camara()

    def _configurar_ui(self):
        self.root.title("Demo rpicam + Tkinter")
        self.root.geometry("800x480")
        self.root.configure(bg="#11171a")

        self.lbl_estado = tk.Label(
            self.root,
            text="Iniciando cámara...",
            bg="#11171a",
            fg="#f5f6f7",
            font=("Segoe UI", 14, "bold"),
        )
        self.lbl_estado.pack(pady=10)

        self.lbl_video = tk.Label(self.root, bg="#000000")
        self.lbl_video.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.btn_detener = tk.Button(
            self.root,
            text="Detener",
            command=self.detener,
            bg="#c0392b",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        )
        self.btn_detener.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _iniciar_camara(self):
        if not self.backend.start():
            mensaje = (
                self.backend.error_message
                or "No se pudo iniciar la cámara rpicam."
            )
            print(f"[Demo] {mensaje}", file=sys.stderr)
            messagebox.showerror("rpicam", mensaje)
            self.lbl_estado.config(text=mensaje)
            self.btn_detener.config(state=tk.DISABLED)
            return

        self.lbl_estado.config(text="Cámara en vivo")
        self._programar_siguiente_frame()

    def _programar_siguiente_frame(self):
        self.frame_job = self.root.after(10, self._actualizar_frame)

    def _actualizar_frame(self):
        exito, frame = self.backend.read()
        if not exito:
            mensaje = (
                self.backend.error_message
                or "No se pudo obtener un frame de la cámara."
            )
            print(f"[Demo] {mensaje}", file=sys.stderr)
            messagebox.showwarning("rpicam", mensaje)
            self.detener()
            self.lbl_estado.config(text=mensaje)
            return

        imagen = Image.fromarray(frame)
        ancho = self.lbl_video.winfo_width() or 800
        alto = self.lbl_video.winfo_height() or 480
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)

        foto = ImageTk.PhotoImage(imagen)
        self.imagen = foto
        self.lbl_video.configure(image=foto)
        self.lbl_video.image = foto

        self._programar_siguiente_frame()

    def detener(self):
        if self.frame_job:
            self.root.after_cancel(self.frame_job)
            self.frame_job = None

        if self.backend:
            self.backend.stop()

        self.lbl_estado.config(text="Cámara detenida")
        self.lbl_video.configure(image="")
        self.lbl_video.image = None
        self.imagen = None

    def _cerrar(self):
        self.detener()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = RPiCamTkDemo(root)
    root.mainloop()


if __name__ == "__main__":
    main()
