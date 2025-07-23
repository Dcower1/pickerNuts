import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from components import utils
from models.DAO.proveedor_dao import ProveedorDAO

from components.utils import colores_wit


img_path = os.path.join("components", "img", "banner_Nuts.png")


class BaseProveedorView:
    def __init__(self, root, titulo="Proveedores - Diseño Mockup", usuario_activo=None):
        self.root = root
        self.usuario_activo = usuario_activo
        self.root.title(titulo)
        utils.centrar_ventana(self.root, 950, 550)
        #self.root.geometry("950x550")
        self.root.configure(bg="#FBE9D0")
        self.root.resizable(False, False)
        #colores 
        self.colores = colores_wit()

        self.crear_widgets()

    def crear_widgets(self):
        # Top frame
        top_frame = tk.Frame(self.root, bg=self.colores["fondo"])
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        btn_config = tk.Button(top_frame, text="⚙ Configuración", bg=self.colores["boton"],
                               fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                               command=self.configurar)
        btn_config.pack(side=tk.RIGHT, padx=5)

        btn_logout = tk.Button(top_frame, text="⏻ Cerrar Sesión", bg=self.colores["boton"],
                               fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                               command=self.cerrar_sesion)
        btn_logout.pack(side=tk.RIGHT)

        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colores["fondo"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

         # Define colores para filas intercaladas en una lista
        colores_filas = ["#F2DBBB", "#E8C191", "#F2DABD"]
        # Formulario izquierdo
        form_frame = tk.LabelFrame(main_frame, text="Formulario Proveedores", bg=self.colores["form_bg"],
                                   fg=self.colores["texto"], font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        form_frame.grid_columnconfigure(1, weight=1)

        etiquetas = ["Nombre", "Rut", "Contacto"]
        self.entries = {}
        for i, label in enumerate(etiquetas):
            tk.Label(form_frame, text=label, bg=self.colores["form_bg"]).grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[label.lower()] = entry

        self.entry_nombre = self.entries["nombre"]
        self.entry_rut = self.entries["rut"]
        self.entry_contacto = self.entries["contacto"]

        btn_registrar = tk.Button(form_frame, text="Registrar proveedor", bg=self.colores["boton"],
                                  fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                  command=self.registrar)
        btn_registrar.grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")

        # Panel derecho
        right_frame = tk.Frame(main_frame, bg=self.colores["fondo"])
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=0)
        right_frame.grid_rowconfigure(2, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Banner
        if os.path.isfile(img_path):
            try:
                original_img = Image.open(img_path)
                resized = original_img.resize((600, 130), Image.Resampling.LANCZOS)
                banner_img = ImageTk.PhotoImage(resized)
                label_img = tk.Label(right_frame, image=banner_img, bg=self.colores["fondo"])
                label_img.image = banner_img
                label_img.grid(row=0, column=0, pady=(0, 10), sticky="n")
            except Exception as e:
                print("Error cargando banner:", e)

        # Buscador

    # Buscador
        buscador_frame = tk.Frame(right_frame, bg=self.colores["form_bg"], width=600, height=30)
        buscador_frame.grid(row=1, column=0, pady=(0, 10))
        buscador_frame.grid_propagate(False)  # Fijar tamaño

        self.search_var = tk.StringVar()
        entry_buscar = tk.Entry(
            buscador_frame,
            font=("Segoe UI", 10),
            width=50,
            textvariable=self.search_var,
            fg="gray"
        )
        entry_buscar.insert(0, "Buscar...")  # Texto tipo placeholder
        entry_buscar.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

        # Comportamiento placeholder
        def on_entry_click(event):
            if entry_buscar.get() == "Buscar...":
                entry_buscar.delete(0, tk.END)
                entry_buscar.config(fg="black")

        def on_focus_out(event):
            if entry_buscar.get() == "":
                entry_buscar.insert(0, "Buscar...")
                entry_buscar.config(fg="gray")

        entry_buscar.bind("<FocusIn>", on_entry_click)
        entry_buscar.bind("<FocusOut>", on_focus_out)
        entry_buscar.bind("<KeyRelease>", lambda event: self.buscar_proveedor())

        # Tabla
        tabla_frame = tk.LabelFrame(right_frame, text="Lista de Proveedores", bg=self.colores["form_bg"],
                                    fg=self.colores["texto"], font=("Segoe UI", 10, "bold"), padx=5, pady=5)
        tabla_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        cols = ("ID", "Nombre del Proveedor", "RUT", "Contacto")
        self.tree = ttk.Treeview(tabla_frame, columns=cols, show="headings")

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=120)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background=self.colores["tabla_fila"],
                        foreground=self.colores["texto"],
                        fieldbackground=self.colores["tabla_fila"],
                        rowheight=30,
                        font=("Segoe UI", 9))
        style.map("Treeview",
                  background=[('selected', self.colores["tabla_seleccion"])],
                  foreground=[('selected', self.colores["texto_seleccion"])])

        style.configure("Treeview.Heading",
                        background=self.colores["tabla_header"],
                        foreground="white",
                        font=("Segoe UI", 9, "bold"))

        # Configura los tags con un ciclo para mayor flexibilidad
        for i, color in enumerate(colores_filas, start=1):
            self.tree.tag_configure(f"color{i}", background=color)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.actualizar_lista()
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

        if self.usuario_activo is None or not self.usuario_activo.es_admin:
            proveedores = [p for p in proveedores if p.estado != 2]

        tags = [f"color{i}" for i in range(1, 4)]  # ["color1", "color2", "color3"]

        for i, p in enumerate(proveedores):
            tag = tags[i % len(tags)]
            self.tree.insert("", tk.END, values=(p.id, p.nombre, p.rut, p.contacto), tags=(tag,))


    def buscar_proveedor(self):
        filtro = self.search_var.get().lower()
        proveedores = ProveedorDAO.obtener_todos()

        if self.usuario_activo is None or not self.usuario_activo.es_admin:
            proveedores = [p for p in proveedores if p.estado != 2]

        resultados = utils.filtrar_proveedores(proveedores, filtro)
        self.tree.delete(*self.tree.get_children())

        tags = [f"color{i}" for i in range(1, 4)]  # Usa mismos colores que en actualizar_lista

        for i, p in enumerate(resultados):
            tag = tags[i % len(tags)]
            self.tree.insert("", tk.END, values=(p.id, p.nombre, p.rut, p.contacto), tags=(tag,))

    def abrir_interfaz_proveedor(self, event):
        raise NotImplementedError("Este método debe ser implementado por la subclase.")

    def cerrar_sesion(self):
        self.root.destroy()

        import tkinter as tk
        from view.login import LoginView  # Ajustar ruta según estructura

        login_root = tk.Tk()

        def on_login_success(usuario_obj):
            login_root.destroy()
            nuevo_root = tk.Tk()
            if usuario_obj.rol == 1:
                from view.admin_views import admin_proveedor
                admin_proveedor.admin_ProveedorView(nuevo_root, usuario_activo=usuario_obj)
            else:
                from view.usuario_views import proveedor
                proveedor.ProveedorView(nuevo_root, usuario_activo=usuario_obj)
            nuevo_root.mainloop()

        LoginView(login_root, on_login_success)
        login_root.mainloop()

    def configurar(self):
        messagebox.showinfo("Configuración", "Aquí abrirías las configuraciones del sistema.")