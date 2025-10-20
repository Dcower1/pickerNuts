import importlib.util
import cv2


def _module_available(module_name):
    """Check if a module can be imported without actually importing it."""
    try:
        disponible = importlib.util.find_spec(module_name) is not None
        print(
            f"[Cámara] Verificación módulo '{module_name}': "
            f"{'disponible' if disponible else 'no disponible'}",
            flush=True,
        )
        return disponible
    except (ImportError, AttributeError):
        print(f"[Cámara] Error verificando módulo '{module_name}'", flush=True)
        return False


class BaseCameraBackend:
    """Common interface for camera adapters."""

    color_format = "RGB"

    def __init__(self):
        self.error_message = ""

    def start(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class RPiCamBackend(BaseCameraBackend):
    """Camera backend using rpicam / Picamera2 stack."""

    def __init__(self):
        super().__init__()
        self.picam = None

    def start(self):
        print("[Cámara] Intentando iniciar backend rpicam...", flush=True)
        try:
            from picamera2 import Picamera2
        except ImportError:
            self.error_message = (
                "No se encontró la librería picamera2 necesaria para usar rpicam."
            )
            print(f"[Cámara][rpicam] {self.error_message}", flush=True)
            return False

        try:
            self.picam = Picamera2()
            configuration = self.picam.create_video_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            self.picam.configure(configuration)
            self.picam.start()
            print("[Cámara][rpicam] Cámara iniciada correctamente.", flush=True)
        except Exception as exc:  # pragma: no cover - hardware specific
            self.error_message = f"Error al iniciar la cámara rpicam: {exc}"
            print(f"[Cámara][rpicam] {self.error_message}", flush=True)
            self.stop()
            return False

        self.error_message = ""
        return True

    def read(self):
        if not self.picam:
            self.error_message = "La cámara rpicam no está inicializada."
            print(f"[Cámara][rpicam] {self.error_message}", flush=True)
            return False, None
        try:
            frame = self.picam.capture_array("main")
        except Exception as exc:  # pragma: no cover - hardware specific
            self.error_message = f"Error al capturar imagen con rpicam: {exc}"
            print(f"[Cámara][rpicam] {self.error_message}", flush=True)
            return False, None
        return True, frame

    def stop(self):
        if not self.picam:
            return
        try:
            self.picam.stop()
        except Exception:  # pragma: no cover - hardware specific
            print("[Cámara][rpicam] Error controlado al detener la cámara.", flush=True)
        try:
            self.picam.close()
        except Exception:  # pragma: no cover - hardware specific
            print("[Cámara][rpicam] Error controlado al cerrar la cámara.", flush=True)
        print("[Cámara][rpicam] Cámara detenida.", flush=True)
        self.picam = None


class OpenCVCameraBackend(BaseCameraBackend):
    """Camera backend using OpenCV VideoCapture as a fallback."""

    color_format = "BGR"

    def __init__(self, index=0):
        super().__init__()
        self.index = index
        self.cap = None

    def start(self):
        self.stop()
        print(f"[Cámara] Intentando iniciar backend OpenCV índice {self.index}...", flush=True)
        try:
            if hasattr(cv2, "CAP_V4L2"):
                captura = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
            elif hasattr(cv2, "CAP_DSHOW"):
                captura = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            else:
                captura = cv2.VideoCapture(self.index)
        except Exception as exc:
            self.error_message = f"Error al acceder a la cámara con OpenCV: {exc}"
            print(f"[Cámara][OpenCV] {self.error_message}", flush=True)
            return False

        if not captura or not captura.isOpened():
            self.error_message = (
                "No se pudo acceder a la cámara utilizando la captura de OpenCV."
            )
            print(f"[Cámara][OpenCV] {self.error_message}", flush=True)
            if captura:
                captura.release()
            return False

        self.cap = captura
        self.error_message = ""
        print("[Cámara][OpenCV] Cámara iniciada correctamente.", flush=True)
        return True

    def read(self):
        if not self.cap:
            self.error_message = "La captura de OpenCV no está inicializada."
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.error_message = "No se pudo obtener un frame desde la cámara."
            print(f"[Cámara][OpenCV] {self.error_message}", flush=True)
            return False, None

        return True, frame

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None
            print("[Cámara][OpenCV] Cámara detenida.", flush=True)


def _puede_usar_rpicam():
    """Check if rpicam (picamera2) stack is available in the environment."""
    return _module_available("rpicam") or _module_available("picamera2")


def seleccionar_backend(prefer_rpicam=True, index=0):
    """Return the best available backend and an optional error message."""
    error_messages = []

    if prefer_rpicam and _puede_usar_rpicam():
        print("[Cámara] Se detectó soporte rpicam. Probando backend rpicam...", flush=True)
        backend = RPiCamBackend()
        if backend.start():
            return backend, None
        error_messages.append(backend.error_message)

    backend = OpenCVCameraBackend(index=index)
    print("[Cámara] Probando backend OpenCV como respaldo...", flush=True)
    if backend.start():
        return backend, None
    error_messages.append(backend.error_message)

    error_text = "\n".join(msg for msg in error_messages if msg)
    print(f"[Cámara] Falló la selección de backend. Errores: {error_text}", flush=True)
    return None, error_text


__all__ = [
    "BaseCameraBackend",
    "RPiCamBackend",
    "OpenCVCameraBackend",
    "seleccionar_backend",
]
