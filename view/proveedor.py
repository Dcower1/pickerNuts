import tkinter as tk
from tkinter import messagebox
from models import bd
from view.interfaz import InterfazProveedorView
from components import utils
from models.DAO.proveedor_dao import ProveedorDAO 

class ProveedorView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gestión de Proveedores")
        #self.root.geometry("400x400")

        utils.centrar_ventana(self.root, 400, 400)

        tk.Label(self.root, text="Nombre").pack()
        self.entry_nombre = tk.Entry(self.root)
        self.entry_nombre.pack()

        tk.Label(self.root, text="RUT").pack()
        self.entry_rut = tk.Entry(self.root)
        self.entry_rut.pack()

        tk.Label(self.root, text="Contacto").pack()
        self.entry_contacto = tk.Entry(self.root)
        self.entry_contacto.pack()

        tk.Button(self.root, text="Registrar proveedor", command=self.registrar).pack(pady=10)

        self.lista = tk.Listbox(self.root, width=50)
        self.lista.pack(pady=10)
        self.actualizar_lista()
        self.lista.bind("<Double-1>", self.abrir_interfaz_proveedor)
        self.root.mainloop()

    def registrar(self):
        nombre = self.entry_nombre.get().strip()
        rut = self.entry_rut.get().strip()
        contacto = self.entry_contacto.get().strip()

        # Validaciones básicas
        if not nombre or not rut or not contacto:
            messagebox.showwarning("Datos incompletos", "Todos los campos son obligatorios.")
            return

        # Validación de formato de RUT
        if not utils.validar_rut(rut):
            messagebox.showerror("RUT inválido", "El RUT ingresado no es válido.")
            return

        # Validación de formato de contacto
        if not utils.validar_contacto(contacto):
            messagebox.showerror("Número inválido", "El número debe ser formato chileno: +569XXXXXXXX o 9XXXXXXXX.")
            return

        # Verificar si RUT o contacto ya existen
        conn = bd.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM proveedores WHERE rut = ?", (rut,))
        if cursor.fetchone():
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese RUT.")
            conn.close()
            return

        cursor.execute("SELECT id FROM proveedores WHERE contacto = ?", (contacto,))
        if cursor.fetchone():
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese número de contacto.")
            conn.close()
            return

        try:
            cursor.execute("INSERT INTO proveedores (nombre, rut, contacto) VALUES (?, ?, ?)", (nombre, rut, contacto))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Proveedor registrado.")
            self.entry_nombre.delete(0, tk.END)
            self.entry_rut.delete(0, tk.END)
            self.entry_contacto.delete(0, tk.END)
            self.actualizar_lista()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el proveedor.\n{e}")

    def actualizar_lista(self):
        self.lista.delete(0, tk.END)
        conn = bd.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rut FROM proveedores")
        self.proveedores = cursor.fetchall()
        for p in self.proveedores:
            self.lista.insert(tk.END, f"{p[1]} - RUT: {p[2]}")
        conn.close()
    def abrir_interfaz_proveedor(self, event):
        seleccion = self.lista.curselection()
        if not seleccion:
            return
        proveedor = self.proveedores[seleccion[0]]
        proveedor_id = proveedor[0]

        proveedor_dto = ProveedorDAO.obtener_por_id(proveedor_id)
        if proveedor_dto:
            InterfazProveedorView(proveedor_dto)