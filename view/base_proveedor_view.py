import tkinter as tk
from tkinter import ttk, messagebox
from view.usuario_views.interfaz import InterfazProveedorView
from components import utils
from models.DAO.proveedor_dao import ProveedorDAO

class BaseProveedorView:
    def __init__(self, root, titulo, usuario_activo=None):
        self.root = root  # Usar la ventana que te pasan, no crear otra
        self.root.title(titulo)
        utils.centrar_ventana(self.root, 950, 550)
        self.root.geometry("950x550")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        self.usuario_activo = usuario_activo

        # Título y botones superiores
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text=titulo, font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="⚙ Configurar", command=self.configurar).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="⏻ Cerrar sesión", command=self.cerrar_sesion).pack(side=tk.RIGHT)

        # Contenedor principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame izquierdo - Formulario
        form_frame = ttk.LabelFrame(main_frame, text="Formulario de Proveedor", padding=15)
        form_frame.grid(row=0, column=0, sticky="n", padx=10)

        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(form_frame, width=30)
        self.entry_nombre.grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="RUT:").grid(row=1, column=0, sticky="w")
        self.entry_rut = ttk.Entry(form_frame, width=30)
        self.entry_rut.grid(row=1, column=1, pady=5)

        ttk.Label(form_frame, text="Contacto:").grid(row=2, column=0, sticky="w")
        self.entry_contacto = ttk.Entry(form_frame, width=30)
        self.entry_contacto.grid(row=2, column=1, pady=5)

        ttk.Button(form_frame, text="Registrar Proveedor", command=self.registrar).grid(row=3, column=0, columnspan=2, pady=10)

        # Frame derecho - Búsqueda + Lista
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda event: self.buscar_proveedor())
        ttk.Button(search_frame, text="🔍 Buscar", command=self.buscar_proveedor).pack(side=tk.LEFT)

        # Tabla
        lista_frame = ttk.LabelFrame(right_frame, text="Lista de Proveedores", padding=10)
        lista_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(lista_frame, columns=("ID", "Nombre", "RUT", "Contacto"), show="headings", height=15)
        for col in ("ID", "Nombre", "RUT", "Contacto"):
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50)
        self.tree.column("Nombre", width=150)
        self.tree.column("RUT", width=120)
        self.tree.column("Contacto", width=120)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.abrir_interfaz_proveedor)

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.actualizar_lista()
        self.root.mainloop()

    def registrar(self):
        nombre = self.entry_nombre.get().strip()
        rut = self.entry_rut.get().strip()
        contacto = self.entry_contacto.get().strip()

        if not nombre or not rut or not contacto:
            messagebox.showwarning("Campos incompletos", "Por favor completa todos los campos.")
            return

        if not utils.validar_rut(rut):
            messagebox.showerror("Error", "RUT inválido.")
            return

        if not utils.validar_contacto(contacto):
            messagebox.showerror("Error", "Contacto inválido. Ej: +569xxxxxxxx")
            return

        if ProveedorDAO.existe_rut(rut):
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese RUT.")
            return

        if ProveedorDAO.existe_contacto(contacto):
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese número.")
            return

        if ProveedorDAO.insertar(nombre, rut, contacto):
            messagebox.showinfo("Éxito", "Proveedor registrado.")
            self.entry_nombre.delete(0, tk.END)
            self.entry_rut.delete(0, tk.END)
            self.entry_contacto.delete(0, tk.END)
            self.actualizar_lista()
        else:
            messagebox.showerror("Error", "No se pudo registrar.")

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        proveedores = ProveedorDAO.obtener_todos()
        for p in proveedores:
            self.tree.insert("", tk.END, values=(p.id, p.nombre, p.rut, p.contacto))

    def buscar_proveedor(self):
        filtro = self.search_var.get().lower()
        proveedores = ProveedorDAO.obtener_todos()
        resultados = utils.filtrar_proveedores(proveedores, filtro)
        self.tree.delete(*self.tree.get_children())
        for p in resultados:
            self.tree.insert("", tk.END, values=(p.id, p.nombre, p.rut, p.contacto))

    def abrir_interfaz_proveedor(self, event):
        seleccionado = self.tree.selection()
        if seleccionado:
            item = self.tree.item(seleccionado[0])
            proveedor_id = item["values"][0]
            proveedor = ProveedorDAO.obtener_por_id(proveedor_id)
            if proveedor:
                InterfazProveedorView(proveedor)

    def cerrar_sesion(self):
        self.root.destroy()
        messagebox.showinfo("Sesión cerrada", "Has cerrado sesión.")

    def configurar(self):
        messagebox.showinfo("Configuración", "Aquí abrirías las configuraciones del sistema.")