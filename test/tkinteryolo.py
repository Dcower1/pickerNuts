from pathlib import Path
import tkinter as tk

import cv2
from picamera2 import Picamera2
from PIL import Image, ImageTk
from ultralytics import YOLO

# Initialize Picamera2 with a lower resolution to speed up inference
picam2 = Picamera2()
picam2.preview_configuration.main.size = (256, 256)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Load YOLOv8 model
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "DAO" / "NutPickerModel.pt"
model = YOLO(str(MODEL_PATH))

root = tk.Tk()
root.title("YOLO Camera")

image_label = tk.Label(root)
image_label.pack()

fps_var = tk.StringVar(value="FPS: --.-")
fps_label = tk.Label(root, textvariable=fps_var, font=("Helvetica", 12))
fps_label.pack()

running = True

def update_frame():
    if not running:
        return

    frame = picam2.capture_array()
    results = model(frame, imgsz=256)
    annotated_frame = results[0].plot()

    inference_time = results[0].speed["inference"]
    fps = 1000 / inference_time if inference_time else 0
    fps_var.set(f"FPS: {fps:.1f}")

    preview = cv2.resize(annotated_frame, (200, 200), interpolation=cv2.INTER_AREA)
    preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

    img = Image.fromarray(preview_rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    image_label.configure(image=imgtk)
    image_label.image = imgtk

    root.after(10, update_frame)

def on_close():
    global running
    running = False
    try:
        picam2.stop()
    finally:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

update_frame()
root.mainloop()

try:
    picam2.stop()
except RuntimeError:
    pass

picam2.close()
