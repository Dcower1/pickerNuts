import platform
import shutil
import subprocess
import time
from pathlib import Path

import components.config as app_config
import pytest


OUTPUT_DIR = Path(__file__).parent / "outputs"
MODEL_PATH = app_config.MODEL_PATH
RUN_NAME = "EV_TU02_yolo_cli"
CAPTURE_RAW = OUTPUT_DIR / "EV_TU02_capture_raw.jpg"
CAPTURE_BGR = OUTPUT_DIR / "EV_TU02_capture_bgr.jpg"


def _es_raspberry_pi() -> bool:
    model_path = Path("/sys/firmware/devicetree/base/model")
    if model_path.exists():
        try:
            return "raspberry pi" in model_path.read_text().lower()
        except OSError:
            return False
    return platform.machine().startswith("arm")


@pytest.mark.hardware
def test_yolo_cli_prediccion_en_raspberry():
    """
    Captura un frame real con el backend de cámara del sistema, guarda copia cruda y BGR,
    y lo procesa con YOLO CLI. Falla si no hay detecciones.
    """

    if not _es_raspberry_pi():
        pytest.skip("La validación de YOLO CLI solo aplica en Raspberry Pi.")

    cv2 = pytest.importorskip("cv2")

    if not MODEL_PATH.exists():
        pytest.skip(f"No se encontró el modelo en {MODEL_PATH}")

    if shutil.which("yolo") is None:
        pytest.skip("El comando 'yolo' no está disponible en el sistema/PATH.")

    try:
        from components.camara import seleccionar_backend
    except Exception as exc:
        pytest.skip(f"No se pudo importar el módulo de cámara de la app: {exc}")

    backend, error_message = seleccionar_backend()
    if not backend:
        pytest.skip(f"No hay backend de cámara disponible: {error_message}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in (CAPTURE_RAW, CAPTURE_BGR):
        path.unlink(missing_ok=True)

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

        cv2.imwrite(str(CAPTURE_RAW), frame)

        frame_to_save = frame
        color_format = getattr(backend, "color_format", "BGR").upper()
        if color_format == "RGB":
            frame_to_save = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(CAPTURE_BGR), frame_to_save)
    finally:
        try:
            backend.stop()
        except Exception:
            pass

    assert CAPTURE_RAW.exists(), "No se pudo guardar la captura cruda de la cámara."
    assert CAPTURE_BGR.exists(), "No se pudo guardar la captura BGR."
    assert CAPTURE_BGR.stat().st_size > 0, "La captura BGR está vacía o corrupta."

    run_dir = OUTPUT_DIR / RUN_NAME
    shutil.rmtree(run_dir, ignore_errors=True)

    comando = [
        "yolo",
        "predict",
        f"model={MODEL_PATH}",
        f"source={CAPTURE_BGR}",
        "save_txt=True",
        "save_conf=True",
        "conf=0.05",
        "imgsz=256",
        f"project={OUTPUT_DIR}",
        f"name={RUN_NAME}",
        "exist_ok=True",
        "verbose=False",
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )

    if resultado.returncode != 0:
        pytest.fail(f"YOLO CLI falló: {resultado.stderr or resultado.stdout}")

    assert run_dir.exists(), "La ejecución no creó el directorio de salida."
    image_files = [
        p
        for p in run_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    assert image_files, "YOLO CLI no generó una imagen de salida."
    assert all(f.stat().st_size > 0 for f in image_files), "La imagen generada está vacía o corrupta."

    labels_dir = run_dir / "labels"
    assert labels_dir.exists(), "YOLO CLI no creó directorio de etiquetas."
    label_files = list(labels_dir.glob("*.txt"))
    if not label_files:
        pytest.fail(
            "YOLO CLI no generó archivo de etiquetas. "
            f"Revisa {run_dir} para la imagen anotada y la captura {CAPTURE_BGR}. "
            f"STDOUT: {resultado.stdout} STDERR: {resultado.stderr}"
        )
    total_lines = sum(len(p.read_text().strip().splitlines()) for p in label_files)
    if total_lines == 0:
        pytest.fail(
            "YOLO no detectó ningún objeto en la captura. "
            f"Revisa {run_dir} para la imagen anotada y la captura {CAPTURE_BGR}. "
            f"STDOUT: {resultado.stdout} STDERR: {resultado.stderr}"
        )
