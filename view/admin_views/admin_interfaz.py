import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from components import utils
from components.utils import obtener_colores
from models.DAO.camara import Camara, ConfigBotonCamara
from models.DAO.Tensflow import ModeloNuecesInterpreter
from models.DAO.proveedor_dao import ProveedorDAO

COLORS = obtener_colores()


class admin_InterfazProveedorView:
    def __init__(self, proveedor_dto, callback_actualizar=None):
        self.proveedor = proveedor_dto
        self.callback_actualizar = callback_actualizar
        self.editando = False
        self.produccion_activa = False
        self.camara: Camara | None = None
        self.interprete = ModeloNuecesInterpreter()

        self.colores = COLORS
        self.root = tk.Toplevel()
        self.root.title("Interfaz Clasificación - ADMIN")
        self.root.configure(bg=self.colores["fondo"])
        self.root.geometry("800x480")

        utils.centrar_ventana(self.root, 800, 480)

        self.construir_interfaz()
        self.root.mainloop()

    def construir_interfaz(self):
        # --- Cámara ---
        frame_camara = tk.LabelFrame(self.root, text="Cámara", bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_camara.place(x=20, y=20, width=470, height=120)

        for i in range(5):
            color = "white" if i != 2 else "red"
            borde = 2 if i == 2 else 1
            tk.Label(frame_camara, text=f"Nuez {i+1}", bg=color, width=10, height=4, relief="solid", bd=borde).pack(side=tk.LEFT, padx=5)

        tk.Label(frame_camara, text="Desecho D", fg="red", bg=self.colores["form_bg"]).place(x=200, y=0)

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
        btn_start = tk.Button(self.root, text="START", bg=self.colores["boton"], fg=self.colores["boton_texto"],
                              font=("Segoe UI", 12, "bold"),
                              command=lambda: self.toggle_produccion(True))
        btn_start.place(x=340, y=150, width=120, height=45)

        config_boton = ConfigBotonCamara(
            texto_inicio="START",
            texto_detener="DETENER",
            color_inicio=(self.colores["boton"], self.colores["boton_texto"]),
            color_detener=("red", "white"),
        )
        self.camara = Camara(
            self.root,
            self.lbl_camara,
            self.btn_start,
            config_boton=config_boton,
            frame_callback=self.interprete.enviar_frame,
        )
        self.btn_start.config(command=self.camara.toggle)

        # --- Boton Reporte ---
        btn_reporte = tk.Button(self.root, text="Reporte", bg=self.colores["boton"], fg=self.colores["boton_texto"])
        btn_reporte.place(x=480, y=150, width=100, height=40)

        # --- Total Clasificaciones ---
        frame_totales = tk.LabelFrame(self.root, text="Total Clasificaciones: XX",
                                      bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_totales.place(x=20, y=210, width=480, height=180)

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
        frame_producto.place(x=520, y=210, width=250, height=110)

        tk.Label(frame_producto, text="Mariposa", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(frame_producto, text="Cuarto 🔒", bg="white", relief="solid", width=10, height=4).pack(side=tk.LEFT, padx=10, pady=10)

        # --- Historial ---
        frame_historial = tk.LabelFrame(self.root, text="Historial",
                                        bg=self.colores["form_bg"], fg=self.colores["texto"])
        frame_historial.place(x=520, y=330, width=250, height=120)

        fechas = ["06-06-2025", "06-02-2025", "06-03-2025", "06-04-2025"]
        for f in fechas:
            tk.Label(frame_historial, text=f, bg=self.colores["form_bg"]).pack(anchor="w", padx=10, pady=2)

        # --- Botones ADMIN ---
        self.btn_editar = tk.Button(self.root, text="✏️ Editar Proveedor", bg="orange", fg="black",
                                    command=self.modo_edicion)
        self.btn_editar.place(x=20, y=410, width=160, height=40)

        if self.proveedor.estado == 2:
            self.btn_eliminar = tk.Button(self.root, text="Activar Proveedor", bg="green", fg="white",
                                          command=self.activar_proveedor)
        else:
            self.btn_eliminar = tk.Button(self.root, text="Eliminar Proveedor", bg="red", fg="white",
                                          command=self.eliminar_proveedor)
        self.btn_eliminar.place(x=200, y=410, width=160, height=40)

        self.btn_volver = tk.Button(self.root, text="Volver", command=self.root.destroy)
        self.btn_volver.place(x=380, y=410, width=80, height=40)

    # ----------------- FUNCIONES ADMIN -----------------
    def eliminar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Eliminar proveedor?"):
            exito = ProveedorDAO.eliminar_logico(self.proveedor.id_proveedor)
            if exito:
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.root.destroy()
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
                self.root.destroy()
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
            self.root.destroy()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el proveedor.")

    def cancelar_edicion(self):
        self.entry_nombre.destroy()
        self.entry_contacto.destroy()
        self.btn_cancelar.destroy()
        self.editando = False

        self.lbl_nombre.pack(anchor="w", padx=10, pady=2)
        self.lbl_contacto.pack(anchor="w", padx=10, pady=2)

        # Restauramos boton
        self.btn_editar.config(text="Editar Proveedor", command=self.modo_edicion)

    def cerrar(self):
        if self.camara:
            self.camara.cerrar()
        if hasattr(self, "interprete") and self.interprete:
            self.interprete.cerrar()
        self.root.destroy()
