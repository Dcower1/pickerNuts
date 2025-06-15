import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.DAO.clasificacion_dao import ClasificacionDAO
from models.DAO.proveedor_dao import ProveedorDAO
from components.utils import centrar_ventana, crear_boton_toggle

class admin_InterfazProveedorView:
    def __init__(self, proveedor_dto, callback_actualizar=None):
        self.proveedor = proveedor_dto
        self.callback_actualizar = callback_actualizar
        self.produccion_activa = False
        self.editando = False  # Control de modo edición

        ClasificacionDAO.insertar_datos_simulados_si_no_existen(self.proveedor.id)
        self.datos = ClasificacionDAO.obtener_metricas(self.proveedor.id)

        self.root = tk.Toplevel()
        self.root.title("Ficha Proveedor")
        self.root.configure(bg="white")
        self.root.geometry("950x600")
        centrar_ventana(self.root, 950, 600)

        self.crear_widgets()
        self.root.mainloop()

    def crear_widgets(self):
        tk.Label(self.root, text="Ficha Proveedor", font=("Arial", 16, "bold"), bg="white").place(x=30, y=20)

        # Labels modo lectura
        self.lbl_nombre = tk.Label(self.root, text=f"Proveedor: {self.proveedor.nombre}", font=("Arial", 12), bg="white")
        self.lbl_nombre.place(x=30, y=60)

        self.lbl_rut = tk.Label(self.root, text=f"Rut: {self.datos['rut']}", font=("Arial", 12), bg="white")
        self.lbl_rut.place(x=30, y=90)

        self.lbl_contacto = tk.Label(self.root, text=f"Contacto: {self.datos['contacto']}", font=("Arial", 12), bg="white")
        self.lbl_contacto.place(x=600, y=60)

        self.boton_produccion = crear_boton_toggle(self.root, self.toggle_produccion)
        self.boton_produccion.place(x=400, y=100)

        tk.Label(self.root, text=f"Total Clasificaciones: {self.datos['total']}", font=("Arial", 12), bg="white").place(x=30, y=180)
        tk.Label(self.root, text="Conteo por clase", font=("Arial", 12, "bold"), bg="white").place(x=30, y=220)

        clases = ["A", "B", "C"]
        tabla = ttk.Treeview(self.root, columns=clases, show='headings', height=1)
        for col in clases:
            tabla.heading(col, text=col)
            tabla.column(col, width=100, anchor="center")
        tabla.insert("", "end", values=[self.datos['A'], self.datos['B'], self.datos['C']])
        tabla.place(x=30, y=250)

        self.graficar_torta(self.datos)

        tk.Label(self.root, text="Tendencia de calidad:", font=("Arial", 12, "bold"), bg="white").place(x=30, y=330)
        tk.Label(self.root, text=f"Última clasificación: {self.datos['ultima_fecha']}", font=("Arial", 11), bg="white").place(x=30, y=410)

        fechas = self.datos["ultimas_fechas"]
        for i, f in enumerate(fechas):
            tk.Label(self.root, text=f, bg="#eeeeee", font=("Arial", 10), width=15).place(x=30 + i * 130, y=450)

        # Botones
        self.btn_volver = tk.Button(self.root, text="Volver", command=self.root.destroy)
        self.btn_volver.place(x=30, y=500)

        self.btn_editar = tk.Button(self.root, text="✏️ Editar Proveedor", bg="orange", fg="black", command=self.modo_edicion)
        self.btn_editar.place(x=600, y=500)

        if self.proveedor.estado == 2:  # Proveedor inactivo
            self.btn_eliminar = tk.Button(self.root, text="🔄 Activar Proveedor", bg="green", fg="white", command=self.activar_proveedor)
        else:  # Proveedor activo
            self.btn_eliminar = tk.Button(self.root, text="🗑 Eliminar Proveedor", bg="red", fg="white", command=self.eliminar_proveedor)

        self.btn_eliminar.place(x=750, y=500)


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
        self.btn_cancelar.place(x=720, y=500)

    def guardar_cambios(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        nuevo_contacto = self.entry_contacto.get().strip()
        nuevo_rut = self.proveedor.rut  # No editable, pero si quieres, habilita edición arriba

        if not nuevo_nombre or not nuevo_contacto:
            messagebox.showerror("Error", "Nombre y contacto no pueden estar vacíos.")
            return

        actualizado = ProveedorDAO.actualizar(self.proveedor.id, nuevo_nombre, nuevo_rut, nuevo_contacto)
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

    def graficar_torta(self, datos):
        valores = [datos['A'], datos['B'], datos['C']]
        clases = ['A', 'B', 'C']

        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.pie(valores, labels=clases, autopct='%1.0f%%', startangle=90)
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().place(x=600, y=220)

    def eliminar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro que deseas eliminar este proveedor?"):
            exito = ProveedorDAO.eliminar_logico(self.proveedor.id)
            if exito:
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.root.destroy()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el proveedor.")

    def activar_proveedor(self):
        if messagebox.askyesno("Confirmar", "¿Deseas activar este proveedor?"):
            exito = ProveedorDAO.activar_proveedor(self.proveedor.id)
            if exito:
                messagebox.showinfo("Éxito", "Proveedor activado correctamente.")
                self.proveedor.estado = 1
                if self.callback_actualizar:
                    self.callback_actualizar()
                self.root.destroy()
            else:
                messagebox.showerror("Error", "No se pudo activar el proveedor.")
