import tkinter as tk
from tkinter import ttk, messagebox

from models.DAO.clasificacion_dao import ClasificacionDAO
from components.utils import obtener_colores
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

COLORS = obtener_colores()

class InterfazProveedorView:
    def __init__(self, root, proveedor):
        self.root = root
        self.proveedor = proveedor
        self.construir_interfaz()

