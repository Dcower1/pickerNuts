import platform
import time
from pathlib import Path

import pytest


OUTPUT_DIR = Path(__file__).parent / "outputs"
IMAGE_FILENAME = "EV_TU01.jpg"


def _es_raspberry_pi() -> bool:
    """Devuelve True si el sistema es una Raspberry Pi."""
    model_path = Path("/sys/firmware/devicetree/base/model")
    if model_path.exists():
        try:
            return "raspberry pi" in model_path.read_text().lower()
        except OSError:
            return False
    return platform.machine().startswith("arm")


@pytest.mark.hardware
def test_captura_con_backend_del_sistema():
    """
    Valida la captura de un frame usando el backend real del sistema (picamera2/rpicam u OpenCV).

    La prueba genera una imagen en test/outputs con el nombre EV_TU01.jpg.
    Se omite en entornos que no sean Raspberry Pi o sin cámara inicializable.
    """

    if not _es_raspberry_pi():
        pytest.skip("La validación de cámara solo aplica en Raspberry Pi.")

    cv2 = pytest.importorskip("cv2")

    try:
        from components.camara import seleccionar_backend
    except Exception as exc:
        pytest.skip(f"No se pudo importar el módulo de cámara de la app: {exc}")

    backend, error_message = seleccionar_backend()
    if not backend:
        pytest.skip(f"No hay backend de cámara disponible: {error_message}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    salida = OUTPUT_DIR / IMAGE_FILENAME
    if salida.exists():
        salida.unlink()

    frame = None
    ok = False
    try:
        for _ in range(5):
            ok, frame = backend.read()
            if ok and frame is not None:
                break
            time.sleep(0.5)

        if not ok or frame is None:
            pytest.fail(
                f"El backend {backend.__class__.__name__} no entregó frames: "
                f"{getattr(backend, 'error_message', '')}"
            )

        frame_to_save = frame
        color_format = getattr(backend, "color_format", "BGR").upper()
        if color_format == "RGB":
            frame_to_save = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(salida), frame_to_save)
    finally:
        try:
            backend.stop()
        except Exception:
            pass

    assert salida.exists(), "No se generó la imagen EV_TU01 en test/outputs."
    assert salida.stat().st_size > 0, "La imagen capturada está vacía o corrupta."
