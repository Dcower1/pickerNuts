"""Capa de interpretacion para el modelo TensorFlow Lite de nueces."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import cv2
import numpy as np

try:
    from tflite_runtime.interpreter import Interpreter  # type: ignore
except ImportError:  # pragma: no cover - fallback si no existe tflite-runtime
    try:
        import tensorflow as tf  # type: ignore

        Interpreter = tf.lite.Interpreter  # type: ignore[attr-defined]
    except (ImportError, AttributeError) as exc:  # pragma: no cover
        raise ImportError(
            "Se requiere tflite-runtime o tensorflow para usar ModeloNuecesInterpreter"
        ) from exc


class ModeloNuecesInterpreter:
    """Gestiona la ejecucion del modelo modelo_nueces.tflite sobre frames de camara."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        etiquetas: Optional[Sequence[str]] = None,
        min_intervalo_impresion: float = 0.75,
    ) -> None:
        base = Path(__file__).resolve().parent
        self.model_path = model_path or (base / "modelo_nueces.tflite")
        self.etiquetas: Sequence[str] = etiquetas or (
            "Mariposa",
            "Cuarto",
            "Cuartillo",
            "Desecho",
        )
        self.min_intervalo_impresion = min_intervalo_impresion
        self._ultimo_log = 0.0

        self._interpreter: Optional[Interpreter] = None
        self._entrada_info = None
        self._salida_info = None

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._procesando = False
        self._lock = threading.Lock()

    # --------------------- Ciclo de vida ---------------------
    def cargar(self) -> None:
        if self._interpreter is not None:
            return

        if not self.model_path.exists():
            raise FileNotFoundError(f"No se encontro el modelo en {self.model_path}")

        interpreter = Interpreter(model_path=str(self.model_path))
        interpreter.allocate_tensors()
        self._interpreter = interpreter
        self._entrada_info = interpreter.get_input_details()[0]
        self._salida_info = interpreter.get_output_details()[0]

    def cerrar(self) -> None:
        with self._lock:
            self._procesando = False
        self._executor.shutdown(wait=False)
        self._interpreter = None
        self._entrada_info = None
        self._salida_info = None

    # ------------------ Procesamiento principal ------------------
    def enviar_frame(self, frame_bgr: np.ndarray) -> None:
        """Recibe un frame BGR y agenda la inferencia si no hay otra en curso."""
        if frame_bgr is None:
            return

        try:
            self.cargar()
        except Exception as exc:
            print(f"[ModeloNueces] No se pudo cargar el modelo: {exc}")
            return

        with self._lock:
            if self._procesando:
                return
            self._procesando = True

        self._executor.submit(self._procesar_frame, frame_bgr.copy())

    # ------------------ Helpers privados ------------------
    def _procesar_frame(self, frame_bgr: np.ndarray) -> None:
        try:
            predicciones = self._inferir(frame_bgr)
            ahora = time.time()
            if ahora - self._ultimo_log >= self.min_intervalo_impresion:
                self._ultimo_log = ahora
                self._imprimir_predicciones(predicciones)
        except Exception as exc:
            print(f"[ModeloNueces] Error durante la inferencia: {exc}")
        finally:
            with self._lock:
                self._procesando = False

    def _inferir(self, frame_bgr: np.ndarray) -> List[tuple[str, float]]:
        if self._interpreter is None or self._entrada_info is None or self._salida_info is None:
            raise RuntimeError("Interpreter no inicializado")

        input_shape = self._entrada_info["shape"]
        height, width = int(input_shape[1]), int(input_shape[2])
        frame_resized = cv2.resize(frame_bgr, (width, height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

        entrada = frame_rgb.astype(np.float32)
        if self._entrada_info["dtype"] == np.uint8:
            scale, zero_point = self._entrada_info.get("quantization", (1.0, 0))
            if scale == 0:
                scale = 1.0
            entrada = np.round(entrada / scale + zero_point).clip(0, 255).astype(np.uint8)
        else:
            entrada = entrada / 255.0

        entrada = np.expand_dims(entrada, axis=0)

        self._interpreter.set_tensor(self._entrada_info["index"], entrada)
        self._interpreter.invoke()

        salida = self._interpreter.get_tensor(self._salida_info["index"])
        salida = np.squeeze(salida)

        if self._salida_info["dtype"] == np.uint8:
            scale, zero_point = self._salida_info.get("quantization", (1.0, 0))
            if scale == 0:
                scale = 1.0
            salida = (salida.astype(np.float32) - zero_point) * scale
        else:
            salida = salida.astype(np.float32)

        if salida.ndim == 0:
            salida = np.array([float(salida)])

        salida = self._normalizar_probabilidades(salida)
        return self._ordenar_resultados(salida)

    def _normalizar_probabilidades(self, valores: np.ndarray) -> np.ndarray:
        if valores.size == 0:
            return valores
        if np.all(valores >= 0) and np.isclose(valores.sum(), 1.0, atol=1e-3):
            return valores
        # Softmax como fallback
        exp = np.exp(valores - np.max(valores))
        return exp / np.sum(exp)

    def _ordenar_resultados(self, probs: Iterable[float]) -> List[tuple[str, float]]:
        pares = list(zip(self.etiquetas, probs))
        pares.sort(key=lambda x: x[1], reverse=True)
        return pares

    def _imprimir_predicciones(self, predicciones: Sequence[tuple[str, float]]) -> None:
        if not predicciones:
            print("[ModeloNueces] No se obtuvieron predicciones")
            return
        mensaje = " | ".join(
            f"{nombre}: {prob * 100:.2f}%" for nombre, prob in predicciones
        )
        print(f"[ModeloNueces] {mensaje}")
