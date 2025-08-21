import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.DAO.clasificacion_dao import ClasificacionDAO
from models.DAO.proveedor_dao import ProveedorDAO
from components.utils import centrar_ventana, crear_boton_toggle, obtener_colores
from simulacion import simular_clasificacion
from components.control_produccion import ControlProduccion

class admin_InterfazProveedorView:
    def __init__(self, proveedor_dto, callback_actualizar=None):
        self.proveedor = proveedor_dto
        self.callback_actualizar = callback_actualizar
        self.produccion_activa = False
        self.editando = False
        self.control_produccion = ControlProduccion(self.proveedor)

        self.totales_actuales = ClasificacionDAO.obtener_totales_actuales(self.proveedor.id_proveedor)
        self.fechas_historial = ClasificacionDAO.obtener_fechas_historial(self.proveedor.id_proveedor)
        self.fechas, self.historial_clases = ClasificacionDAO.obtener_historial_clases(self.proveedor.id_proveedor)

        self.simulacion_activa = False
        self.simulacion_job = None
        self.proveedor_id = self.proveedor.id_proveedor

        self.colores = obtener_colores()

        self.root = tk.Toplevel()
        self.root.title("Ficha Proveedor")
        self.root.configure(bg=self.colores["fondo"])
        self.root.geometry("1000x650")
        centrar_ventana(self.root, 1000, 650)

        self.crear_widgets()
        self.root.mainloop()

    def crear_widgets(self):
        tk.Label(self.root, text="Ficha Proveedor", font=("Arial", 16, "bold"), bg=self.colores["fondo"], fg=self.colores["texto"]).place(x=30, y=20)


        # Frame de fondo para la ficha con color 'tabla_header'
        frame_ficha = tk.Frame(self.root, bg=self.colores["tabla_header"], bd=2, relief="groove")
        frame_ficha.place(x=20, y=50, width=940, height=70)  # Ajusta el tamaño y posición para que abarque los 3 labels

        self.lbl_nombre = tk.Label(self.root, text=f"Proveedor: {self.proveedor.nombre}", font=("Arial", 12), bg=self.colores["tabla_header"], fg=self.colores["texto"])
        self.lbl_nombre.place(x=30, y=60)

        self.lbl_rut = tk.Label(self.root, text=f"Rut: {self.proveedor.rut}", font=("Arial", 12), bg=self.colores["tabla_header"], fg=self.colores["texto"])
        self.lbl_rut.place(x=30, y=90)

        self.lbl_contacto = tk.Label(self.root, text=f"Contacto: {self.proveedor.contacto}", font=("Arial", 12), bg=self.colores["tabla_header"], fg=self.colores["texto"])
        self.lbl_contacto.place(x=600, y=60)

        self.boton_produccion = crear_boton_toggle(self.root, self.toggle_produccion)
        self.boton_produccion.place(x=400, y=100)

        tk.Label(self.root, text=f"Total Clasificaciones: {self.totales_actuales['total']}", font=("Arial", 12), bg=self.colores["fondo"], fg=self.colores["texto"]).place(x=30, y=140)
        tk.Label(self.root, text="Conteo por clase", font=("Arial", 12, "bold"), bg=self.colores["fondo"], fg=self.colores["texto"]).place(x=30, y=170)

        clases = ["A", "B", "C"]
        tabla = ttk.Treeview(self.root, columns=clases, show='headings', height=1)
        for col in clases:
            tabla.heading(col, text=col)
            tabla.column(col, width=100, anchor="center")
        tabla.insert("", "end", values=[self.totales_actuales['A'], self.totales_actuales['B'], self.totales_actuales['C']])
        tabla.place(x=30, y=200)

        self.graficar_lineas(self.fechas, self.historial_clases)

        # Poner título a la derecha, junto a la gráfica
        tk.Label(self.root, text="Historial de Clasificaciones:", font=("Arial", 12, "bold"), bg=self.colores["fondo"], fg=self.colores["texto"]).place(x=770, y=270)

        # Mostrar fechas en columnas verticales justo debajo del título
        for i, f in enumerate(self.fechas_historial):
            tk.Label(self.root, text=f, bg="#eeeeee", font=("Arial", 10), width=15).place(x=770, y=300 + i * 25)

        #al guardar se debe guardar los datos con fecha en el historial historicos ponlo en la esquina superioir derecha
        self.btn_nueva = tk.Button(self.root, text="Guardar en historial", bg=self.colores["boton"], fg=self.colores["boton_texto"])
        self.btn_nueva.place(relx=0.85, rely=0.05)

        #mostrar mensaje de advertencia 
        self.btn_volver = tk.Button(self.root, text="Volver", command=self.root.destroy)
        self.btn_volver.place(x=30, y=570)

        #pon el boton de edicion y el de eliminar en la esquina inferioir derecha
        self.btn_editar = tk.Button(self.root, text="✏️ Editar Proveedor", bg="orange", fg="black", command=self.modo_edicion)
        self.btn_editar.place(relx=0.65, rely=0.9)

        if self.proveedor.estado == 2:
            self.btn_eliminar = tk.Button(self.root, text="Activar Proveedor", bg="green", fg="white", command=self.activar_proveedor)
        else:
            self.btn_eliminar = tk.Button(self.root, text="Eliminar Proveedor", bg="red", fg="white", command=self.eliminar_proveedor)
        self.btn_eliminar.place(relx=0.8, rely=0.9)

    def graficar_lineas(self, fechas, data):
        fig, ax = plt.subplots(figsize=(7, 3), dpi=100)
        ax.clear()
        ax.set_title("Tendencia de calidad por clase")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Cantidad")
        ax.grid(True)

        for clase, valores in data.items():
            ax.plot(fechas, valores, marker='o', label=clase)

        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.get_tk_widget().place(x=30, y=270)
        self.canvas.draw()

    #agrega tabien una grafica de torta


    def actualizar_historial(self):
        self.totales_actuales = ClasificacionDAO.obtener_totales_actuales(self.proveedor.id_proveedor)
        self.fechas, self.historial_clases = ClasificacionDAO.obtener_historial_clases(self.proveedor.id_proveedor)
        self.graficar_lineas(self.fechas, self.historial_clases)


    def eliminar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro que deseas eliminar este proveedor?"):
            exito = ProveedorDAO.eliminar_logico(self.proveedor.id_proveedor)
            if exito:
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.root.destroy()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el proveedor.")

    def activar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Deseas activar este proveedor?"):
            exito = ProveedorDAO.activar_proveedor(self.proveedor.id_proveedor)
            if exito:
                messagebox.showinfo("Éxito", "Proveedor activado correctamente.")
                self.proveedor.estado = 1
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.root.destroy()
            else:
                messagebox.showerror("Error", "No se pudo activar el proveedor.")

    def graficar_torta(self, datos):
        valores = [datos['A'], datos['B'], datos['C']]
        clases = ['A', 'B', 'C']

        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.pie(valores, labels=clases, autopct='%1.0f%%', startangle=90)
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().place(x=600, y=220)

    def modo_edicion(self):
        if self.editando:
            return  # Ya en modo edición

        self.editando = True
        # Ocultar labels
        self.lbl_nombre.place_forget()
        self.lbl_rut.place_forget()
        self.lbl_contacto.place_forget()

        # Crear campos Entry con valores actuales
        self.entry_nombre = tk.Entry(self.root, font=("Arial", 12))
        self.entry_nombre.insert(0, self.proveedor.nombre)
        self.entry_nombre.place(x=30, y=60)

        # El RUT normalmente no se edita, si quieres hacerlo, habilita este entry:
        # self.entry_rut = tk.Entry(self.root, font=("Arial", 12))
        # self.entry_rut.insert(0, self.proveedor.rut)
        # self.entry_rut.place(x=30, y=90)

        self.entry_contacto = tk.Entry(self.root, font=("Arial", 12))
        self.entry_contacto.insert(0, self.proveedor.contacto)
        self.entry_contacto.place(x=600, y=60)

        # Cambiar botón editar a Guardar y crear botón Cancelar
        self.btn_editar.config(text="💾 Guardar", command=self.guardar_cambios)
        self.btn_cancelar = tk.Button(self.root, text="❌ Cancelar", bg="gray", fg="white", command=self.cancelar_edicion)
        self.btn_cancelar.place(relx=0.72, rely=0.9)
        

    def guardar_cambios(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        nuevo_contacto = self.entry_contacto.get().strip()
        nuevo_rut = self.proveedor.rut  # No editable, pero si quieres, habilita edición arriba

        if not nuevo_nombre or not nuevo_contacto:
            messagebox.showerror("Error", "Nombre y contacto no pueden estar vacíos.")
            return

        actualizado = ProveedorDAO.actualizar(self.proveedor.id_proveedor, nuevo_nombre, nuevo_rut, nuevo_contacto)
        if actualizado:
            messagebox.showinfo("Éxito", "Proveedor actualizado correctamente.")
            self.proveedor.nombre = nuevo_nombre
            self.proveedor.contacto = nuevo_contacto
            # Volver a modo lectura
            self.entry_nombre.destroy()
            self.entry_contacto.destroy()
            self.btn_cancelar.destroy()
            self.editando = False

            self.lbl_nombre.config(text=f"Proveedor: {nuevo_nombre}")
            self.lbl_contacto.config(text=f"Contacto: {nuevo_contacto}")

            self.lbl_nombre.place(x=30, y=60)
            self.lbl_rut.place(x=30, y=90)
            self.lbl_contacto.place(x=600, y=60)

            self.btn_editar.config(text="✏️ Editar Proveedor", command=self.modo_edicion)

            if self.callback_actualizar:
                self.callback_actualizar()

        else:
            messagebox.showerror("Error", "No se pudo actualizar el proveedor.")

    def cancelar_edicion(self):
        self.entry_nombre.destroy()
        self.entry_contacto.destroy()
        self.btn_cancelar.destroy()
        self.editando = False

        self.lbl_nombre.place(x=30, y=60)
        self.lbl_rut.place(x=30, y=90)
        self.lbl_contacto.place(x=600, y=60)

        self.btn_editar.config(text="✏️ Editar Proveedor", command=self.modo_edicion)

    def toggle_produccion(self, estado):
        self.produccion_activa = estado
        print(f"Producción {'iniciada' if estado else 'detenida'} para {self.proveedor.nombre}")

    def guardar_en_historial(self):
        from datetime import datetime

        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        guardado = ClasificacionDAO.guardar_historial(self.proveedor.id, fecha_actual)

        if guardado:
            messagebox.showinfo("Éxito", f"Datos guardados en historial con fecha {fecha_actual}.")
            self.actualizar_historial()
        else:
            messagebox.showerror("Error", "No se pudo guardar en el historial.")