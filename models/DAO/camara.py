"""Control de camara para interfaces Tkinter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union

import cv2
from PIL import Image, ImageTk
from tkinter import messagebox


Color = Tuple[str, str]
FuenteCamara = Union[int, str]


@dataclass
class ConfigBotonCamara:
    texto_inicio: str = "START"
    texto_detener: str = "DETENER"
    color_inicio: Color = ("green", "white")
    color_detener: Color = ("red", "white")


class Camara:
    """Encapsula el manejo de una camara OpenCV para integrarla con Tkinter."""

    def __init__(
        self,
        root: Any,
        etiqueta_video: Any,
        boton_start: Any,
        fuente: FuenteCamara = 0,
        delay_ms: int = 30,
        config_boton: Optional[ConfigBotonCamara] = None,
    ) -> None:
        self.root = root
        self.etiqueta_video = etiqueta_video
        self.boton_start = boton_start
        self.fuente = fuente
        self.delay_ms = delay_ms
        self.cap: Optional[cv2.VideoCapture] = None
        self.job_after: Optional[str] = None
        self.capturando = False
        self.config_boton = config_boton or ConfigBotonCamara(
            texto_inicio=str(boton_start.cget("text")),
            color_inicio=(boton_start.cget("bg"), boton_start.cget("fg")),
        )

        # Ajusta valores faltantes del ConfigBotonCamara
        if not self.config_boton.color_detener[0]:
            self.config_boton = ConfigBotonCamara(
                texto_inicio=self.config_boton.texto_inicio,
                texto_detener=self.config_boton.texto_detener,
                color_inicio=self.config_boton.color_inicio,
                color_detener=("red", "white"),
            )

    # ---------------------- API publica ----------------------
    def toggle(self) -> None:
        if self.capturando:
            self.detener()
        else:
            self.iniciar()

    def iniciar(self) -> None:
        if self.capturando:
            return

        self._liberar_captura()

        try:
            if hasattr(cv2, "CAP_DSHOW") and isinstance(self.fuente, int):
                self.cap = cv2.VideoCapture(self.fuente, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.fuente)
        except Exception:
            self.cap = cv2.VideoCapture(self.fuente)

        if not self.cap or not self.cap.isOpened():
            self._liberar_captura()
            messagebox.showerror("Camara", "No se pudo acceder a la camara.")
            self._actualizar_boton(iniciando=False)
            return

        self.capturando = True
        self._actualizar_boton(iniciando=True)
        self.etiqueta_video.config(text="Conectando...", image="")
        self._programar_siguiente_frame()

    def detener(self) -> None:
        if self.job_after:
            self.root.after_cancel(self.job_after)
            self.job_after = None

        self._liberar_captura()
        self.capturando = False
        self.etiqueta_video.config(image="", text="Camara detenida")
        self.etiqueta_video.image = None
        self._actualizar_boton(iniciando=False)

    def cerrar(self) -> None:
        self.detener()

    def actualizar_fuente(self, nueva_fuente: FuenteCamara) -> None:
        self.fuente = nueva_fuente
        if self.capturando:
            self.detener()
            self.iniciar()

    # ---------------------- Internos ----------------------
    def _programar_siguiente_frame(self) -> None:
        if not self.cap or not self.cap.isOpened():
            self.detener()
            return

        exito, frame = self.cap.read()
        if not exito:
            messagebox.showwarning("Camara", "Se perdio la senal de la camara.")
            self.detener()
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagen = Image.fromarray(frame_rgb)
        ancho = self.etiqueta_video.winfo_width()
        alto = self.etiqueta_video.winfo_height()
        if ancho < 10 or alto < 10:
            ancho, alto = 480, 320
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)
        foto = ImageTk.PhotoImage(image=imagen)
        self.etiqueta_video.configure(image=foto, text="")
        self.etiqueta_video.image = foto

        self.job_after = self.root.after(self.delay_ms, self._programar_siguiente_frame)

    def _actualizar_boton(self, iniciando: bool) -> None:
        if not self.boton_start:
            return
        if iniciando:
            self.boton_start.config(
                text=self.config_boton.texto_detener,
                bg=self.config_boton.color_detener[0],
                fg=self.config_boton.color_detener[1],
            )
        else:
            self.boton_start.config(
                text=self.config_boton.texto_inicio,
                bg=self.config_boton.color_inicio[0],
                fg=self.config_boton.color_inicio[1],
            )

    def _liberar_captura(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None
