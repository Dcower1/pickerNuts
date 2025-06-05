import tkinter as tk
from tkinter import messagebox
from modelo import bd
from vista.interfaz import InterfazProveedorView


class ProveedorView:
    def __init__(self):
        self.lista.bind("<Double-1>", self.abrir_interfaz_proveedor)
        self.root = tk.Tk()
        self.root.title("Gestión de Proveedores")
        self.root.geometry("400x400")

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

        self.root.mainloop()

    def registrar(self):
        nombre = self.entry_nombre.get()
        rut = self.entry_rut.get()
        contacto = self.entry_contacto.get()

        if not nombre or not rut:
            messagebox.showwarning("Datos incompletos", "Nombre y RUT son obligatorios.")
            return

        try:
            conn = bd.conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO proveedores (nombre, rut, contacto) VALUES (?, ?, ?)", (nombre, rut, contacto))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Proveedor registrado.")
            self.entry_nombre.delete(0, tk.END)
            self.entry_rut.delete(0, tk.END)
            self.entry_contacto.delete(0, tk.END)
            self.actualizar_lista()
        except:
            messagebox.showerror("Error", "RUT ya registrado.")

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
        proveedor_nombre = proveedor[1]

        InterfazProveedorView(proveedor_id, proveedor_nombre)
