import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from components import utils
from components.utils import formatear_rut
from models.DAO.proveedor_dao import ProveedorDAO
from models.DAO.superusuario_dao import SuperUsuarioDAO
import re
from components.widgets import RutEntry
from components.utils import obtener_colores


img_path = os.path.join("components", "img", "banner_Nuts.png")


class BaseProveedorView:
    def __init__(self, root, titulo="Proveedores - Diseño Mockup", usuario_activo=None):
        self.root = root
        self.usuario_activo = usuario_activo
        self.root.title(titulo)
        utils.centrar_ventana(self.root, 800, 480)
        #self.root.geometry("950x550")
        self.root.configure(bg="#FBE9D0")
        self.root.resizable(False, False)
        #colores 
        self.colores = obtener_colores()

        self.crear_widgets()

    def crear_widgets(self):
       # Top frame
        self.top_frame = tk.Frame(self.root, bg=self.colores["fondo"])
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_config = tk.Button(self.top_frame, text="⚙ Configuración", bg=self.colores["boton"],
                                    fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                    command=self.configurar)
        self.btn_config.pack(side=tk.RIGHT, padx=5)

        self.btn_sup = tk.Button(self.top_frame, text="Modo Supervisor", bg=self.colores["boton"],
                                fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                command=self.modo_supervisor)
        self.btn_sup.pack(side=tk.RIGHT, padx=5)

        # importante: referencia para poder mostrar/ocultar luego
        self.btn_logout = None


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

        # Nombre
        tk.Label(form_frame, text="Nombre", bg=self.colores["form_bg"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_nombre = tk.Entry(form_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", pady=5)

   
        # Rut
        tk.Label(form_frame, text="Rut", bg=self.colores["form_bg"]).grid(row=1, column=0, sticky="w", pady=5)

        # Usar el widget reutilizable
        self.rut_widget = RutEntry(form_frame, bg=self.colores["form_bg"], fg=self.colores["texto"])
        self.rut_widget.grid(row=1, column=1, sticky="ew", pady=5)

        # Contacto
        tk.Label(form_frame, text="Contacto", bg=self.colores["form_bg"]).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_contacto = tk.Entry(form_frame)
        self.entry_contacto.grid(row=3, column=1, sticky="ew", pady=5)

        # Botón Registrar (lo bajamos a la fila 4)
        btn_registrar = tk.Button(form_frame, text="Registrar proveedor", bg=self.colores["boton"],
                                fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                command=self.registrar)
        btn_registrar.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")
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
                resized = original_img.resize((650, 130), Image.Resampling.LANCZOS)
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
        buscador_frame.grid_propagate(False)  

        self.search_var = tk.StringVar()
        entry_buscar = tk.Entry(
            buscador_frame,
            font=("Segoe UI", 10),
            width=50,
            textvariable=self.search_var,
            fg="gray"
        )
        entry_buscar.insert(0, "Buscar...") 
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

        # Tabla de proveedores.
        tabla_frame = tk.LabelFrame(right_frame, text="", bg=self.colores["form_bg"],
                                    fg=self.colores["texto"], font=("Segoe UI", 10, "bold"), padx=5, pady=5)
        tabla_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)


        header_frame = tk.Frame(tabla_frame, bg=self.colores["form_bg"])
        header_frame.pack(fill=tk.X, pady=2)

        lbl_titulo = tk.Label(header_frame, text="Lista de Proveedores",
                            bg=self.colores["form_bg"], fg=self.colores["texto"],
                            font=("Segoe UI", 10, "bold"))
        lbl_titulo.pack(side=tk.LEFT, padx=5)

        btn_sup = tk.Button(header_frame, text="2 Proveedores",
                            bg=self.colores["boton"], fg=self.colores["boton_texto"],
                            font=("Segoe UI", 9, "bold"),
                            command=self.iniciar_proceso_dos_proveedores)
        btn_sup.pack(side=tk.RIGHT, padx=5)


        # Treeview
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
        rut_limpio = self.rut_widget.get_rut().strip()
        contacto = self.entry_contacto.get().strip()

        if not nombre or not rut_limpio or not contacto:
            messagebox.showwarning("Campos incompletos", "Por favor completa todos los campos.")
            return

        if not utils.validar_rut(rut_limpio):
            messagebox.showerror("Error", "RUT inválido.")
            return

        if not utils.validar_contacto(contacto):
            messagebox.showerror("Error", "Contacto inválido. Ej: +569xxxxxxxx")
            return

        if ProveedorDAO.existe_rut(rut_limpio):
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese RUT.")
            return

        if ProveedorDAO.existe_contacto(contacto):
            messagebox.showerror("Duplicado", "Ya existe un proveedor con ese número.")
            return

        if self.usuario_activo and getattr(self.usuario_activo, "es_admin", False):
            if ProveedorDAO.insertar(nombre, rut_limpio, contacto):
                messagebox.showinfo("Éxito", "Proveedor registrado (Supervisor activo).")
                self.entry_nombre.delete(0, tk.END)
                self.rut_widget.set_rut("")  # <-- aquí lo limpias
                self.entry_contacto.delete(0, tk.END)
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo registrar el proveedor.")
        else:
            self._pedir_autorizacion_supervisor(nombre, rut_limpio, contacto)


    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        proveedores = ProveedorDAO.obtener_todos()

        if self.usuario_activo is None or not self.usuario_activo.es_admin:
            proveedores = [p for p in proveedores if p.estado != 2]

        tags = [f"color{i}" for i in range(1, 4)]  # ["color1", "color2", "color3"]

        for i, p in enumerate(proveedores):
            tag = tags[i % len(tags)]
            self.tree.insert("", tk.END, values=(p.id_proveedor, p.nombre, formatear_rut(p.rut), p.contacto), tags=(tag,))


    def buscar_proveedor(self):
        filtro = self.search_var.get().lower()
        proveedores = ProveedorDAO.obtener_todos()

        if self.usuario_activo is None or not self.usuario_activo.es_admin:
            proveedores = [p for p in proveedores if p.estado != 2]

        resultados = utils.filtrar_proveedores(proveedores, filtro)
        self.tree.delete(*self.tree.get_children())

        tags = [f"color{i}" for i in range(1, 4)]

        for i, p in enumerate(resultados):  # ✅ usar resultados aquí
            tag = tags[i % len(tags)]
            self.tree.insert("", tk.END,
                values=(p.id_proveedor, p.nombre, formatear_rut(p.rut), p.contacto),
                tags=(tag,)
            )

    def abrir_interfaz_proveedor(self, event):
        raise NotImplementedError("Este método debe ser implementado por la subclase.")

    def modo_supervisor(self):
        """Abre ventana modal para autenticación de supervisor"""
        login_win = tk.Toplevel(self.root)
        login_win.title("Activar Modo Supervisor")
        utils.centrar_ventana(login_win, 300, 200)
        login_win.configure(bg=self.colores["form_bg"])
        login_win.resizable(False, False)

        tk.Label(login_win, text="RUT:", bg=self.colores["form_bg"]).pack(pady=5)
        rut_entry = RutEntry(login_win)
        rut_entry.pack(pady=5)


        tk.Label(login_win, text="Contraseña:", bg=self.colores["form_bg"]).pack(pady=5)
        entry_pass = tk.Entry(login_win, show="*")
        entry_pass.pack(pady=5)

        def autenticar():
            rut = rut_entry.get_rut().strip()
            password = entry_pass.get().strip()


            user = SuperUsuarioDAO.autenticar(rut, password)

            if user and user.rol == 1:  # 1 = supervisor/admin
                self.usuario_activo = user
                messagebox.showinfo("Éxito", "Modo Supervisor activado.")
                login_win.destroy()
                self.mostrar_modo_supervisor()
            else:
                messagebox.showerror("Error", "Credenciales inválidas.")

        tk.Button(login_win, text="Ingresar", bg=self.colores["boton"],
                fg=self.colores["boton_texto"], command=autenticar).pack(pady=10)

    def cerrar_sesion(self):
        self.usuario_activo = None

        # Ocultar/destruir botón de logout
        if self.btn_logout:
            self.btn_logout.destroy()
            self.btn_logout = None

        # Rehabilitar botón de activar supervisor
        if self.btn_sup:
            self.btn_sup.config(state="normal", text="Modo Supervisor")

        messagebox.showinfo("Sesión cerrada", "Has salido del modo supervisor.")
        self.actualizar_lista()

    def more_proveedores(self):
        self.pedir_credenciales_supervisor("Activar Modo Supervisor", lambda user: self.mostrar_modo_supervisor())

    def configurar(self):
        messagebox.showinfo("Configuración", "Aquí abrirías las configuraciones del sistema.")

  

   #---------------- modo Sup ----------------

    def modo_supervisor(self):
        self.pedir_credenciales_supervisor("Activar Modo Supervisor", lambda user: self.mostrar_modo_supervisor())

    def more_proveedores(self):
        self.pedir_credenciales_supervisor("Activar Modo Supervisor", lambda user: self.mostrar_modo_supervisor())

    def cerrar_sesion(self):
        self.usuario_activo = None
        if self.btn_logout:
            self.btn_logout.destroy()
            self.btn_logout = None
        if self.btn_sup:
            self.btn_sup.config(state="normal", text="Modo Supervisor")
        messagebox.showinfo("Sesión cerrada", "Has salido del modo supervisor.")
        self.actualizar_lista()

    def mostrar_modo_supervisor(self):
        if not self.btn_logout:
            self.btn_logout = tk.Button(self.top_frame, text="⏻ Cerrar Sesión", bg=self.colores["boton"],
                                        fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                        command=self.cerrar_sesion)
            self.btn_logout.pack(side=tk.RIGHT, padx=5)

        if self.btn_sup:
            self.btn_sup.config(state="disabled", text="Supervisor activo")

        self.actualizar_lista()

    def _pedir_autorizacion_supervisor(self, nombre, rut_limpio, contacto):
        def callback(user):
            if ProveedorDAO.insertar(nombre, rut_limpio, contacto):
                messagebox.showinfo("Éxito", "Proveedor registrado con autorización de supervisor.")
                self.entry_nombre.delete(0, tk.END)
                self.rut_widget.clear()
                self.entry_contacto.delete(0, tk.END)
                self.actualizar_lista()
                self.mostrar_modo_supervisor()
            else:
                messagebox.showerror("Error", "No se pudo registrar el proveedor.")

        self.pedir_credenciales_supervisor("Autorización de Supervisor", callback)

    def pedir_credenciales_supervisor(self, titulo, callback):
        login_win = tk.Toplevel(self.root)
        login_win.title(titulo)
        utils.centrar_ventana(login_win, 300, 200)
        login_win.configure(bg=self.colores["form_bg"])
        login_win.resizable(False, False)

        tk.Label(login_win, text="RUT:", bg=self.colores["form_bg"]).pack(pady=5)
        rut_entry = RutEntry(login_win)
        rut_entry.pack(pady=5)

        tk.Label(login_win, text="Contraseña:", bg=self.colores["form_bg"]).pack(pady=5)
        entry_pass = tk.Entry(login_win, show="*")
        entry_pass.pack(pady=5)

        def autenticar():
            rut = rut_entry.get_rut().strip()
            password = entry_pass.get().strip()
            user = SuperUsuarioDAO.autenticar(rut, password)

            if user and user.rol == 1:
                self.usuario_activo = user
                messagebox.showinfo("Éxito", "Supervisor autenticado.")
                login_win.destroy()
                callback(user)
            else:
                messagebox.showerror("Error", "Credenciales inválidas.")

        tk.Button(login_win, text="Ingresar", bg=self.colores["boton"],
                  fg=self.colores["boton_texto"], command=autenticar).pack(pady=10)



