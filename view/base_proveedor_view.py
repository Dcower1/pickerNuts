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
from models.DAO.proceso_lote_dao import ProcesoLoteDAO
from view.usuario_views.interfazdoble import InterfazViewDoble
from components.config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN, COL_FONDO, IMG_BANNER

img_path = os.path.join("components", "img", "banner_Nuts.png")


class BaseProveedorView:
    def __init__(self, root, titulo="Proveedores - Diseño Mockup", usuario_activo=None):
        self.root = root
        self.usuario_activo = usuario_activo
        self.supervisor_activo = False
        self.root.title(titulo)
        if FULLSCREEN:
            utils.aplicar_fullscreen(self.root)
        else:
            utils.centrar_ventana(self.root, 600, 480)
        self.root.configure(bg="#FBE9D0")
        self.root.resizable(False, False)
        self.colores = obtener_colores()
        self.crear_widgets()
        self.establecer_foco_inicial()

    def crear_widgets(self):
        # Top frame
        self.top_frame = tk.Frame(self.root, bg=self.colores["fondo"])
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_salir = tk.Button(self.top_frame, text="⏻ Salir", bg=self.colores["boton"],
                                   fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                   command=self.cerrar_aplicacion)
        self.btn_salir.pack(side=tk.RIGHT, padx=5)

        self.btn_config = tk.Button(self.top_frame, text="⚙ Configuración", bg=self.colores["boton"],
                                    fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                    command=self.configurar)
        self.btn_config.pack(side=tk.RIGHT, padx=5)

        self.btn_sup = tk.Button(self.top_frame, text="Modo Supervisor", bg=self.colores["boton"],
                                 fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                 command=self.modo_supervisor)
        self.btn_sup.pack(side=tk.RIGHT, padx=5)

        self.btn_logout = None

        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colores["fondo"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        colores_filas = ["#F2DBBB", "#E8C191", "#F2DABD"]

        # Formulario izquierdo
        form_frame = tk.LabelFrame(main_frame, text="Formulario Proveedores", bg=self.colores["form_bg"],
                                   fg=self.colores["texto"], font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        form_frame.grid_columnconfigure(1, weight=1)

        tk.Label(form_frame, text="Nombre", bg=self.colores["form_bg"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_nombre = tk.Entry(form_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", pady=5)

        tk.Label(form_frame, text="Rut", bg=self.colores["form_bg"]).grid(row=1, column=0, sticky="w", pady=5)
        self.rut_widget = RutEntry(form_frame, bg=self.colores["form_bg"], fg=self.colores["texto"])
        self.rut_widget.grid(row=1, column=1, sticky="ew", pady=5)

        tk.Label(form_frame, text="Contacto", bg=self.colores["form_bg"]).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_contacto = tk.Entry(form_frame)
        self.entry_contacto.grid(row=3, column=1, sticky="ew", pady=5)

        self.btn_registrar = tk.Button(
            form_frame, text="Registrar proveedor", bg=self.colores["boton"],
            fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
            command=self.registrar
        )
        self.btn_registrar.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        if not self.supervisor_activo:
            self._bloquear_formulario()

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
        self.entry_buscar = entry_buscar

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

        # Tabla de proveedores
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

        for i, color in enumerate(colores_filas, start=1):
            self.tree.tag_configure(f"color{i}", background=color)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.actualizar_lista()

    def establecer_foco_inicial(self):
        def _focus():
            try:
                self.entry_nombre.focus_set()
            except tk.TclError:
                pass
        self.root.after_idle(_focus)

    def _bloquear_formulario(self):
        self.entry_nombre.config(state="disabled")
        self.rut_widget.disable()  # <--- ahora correcto
        self.entry_contacto.config(state="disabled")
        self.btn_registrar.config(state="disabled")

    def _habilitar_formulario(self):
        self.entry_nombre.config(state="normal")
        self.rut_widget.enable()   # <--- ahora correcto
        self.entry_contacto.config(state="normal")
        self.btn_registrar.config(state="normal")

    def registrar(self):
        nombre = self.entry_nombre.get().strip()
        rut_limpio = self.rut_widget.get_rut().strip()
        contacto = self.entry_contacto.get().strip()

        if not nombre or not rut_limpio or not contacto:
            self._mostrar_warning("Campos incompletos", "Por favor completa todos los campos.", focus_widget=self.entry_nombre)
            return

        if not utils.validar_rut(rut_limpio):
            self._mostrar_error("Error", "RUT inválido.", focus_widget=self.rut_widget)
            return

        if not utils.validar_contacto(contacto):
            self._mostrar_error("Error", "Contacto inválido. Ej: +569xxxxxxxx", focus_widget=self.entry_contacto)
            return

        if ProveedorDAO.existe_rut(rut_limpio):
            self._mostrar_error("Duplicado", "Ya existe un proveedor con ese RUT.", focus_widget=self.rut_widget)
            return

        if ProveedorDAO.existe_contacto(contacto):
            self._mostrar_error("Duplicado", "Ya existe un proveedor con ese número.", focus_widget=self.entry_contacto)
            return

        if self.supervisor_activo:
            if ProveedorDAO.insertar(nombre, rut_limpio, contacto):
                self._mostrar_info("Éxito", "Proveedor registrado (Supervisor activo).", focus_widget=self.entry_nombre)
                self.entry_nombre.delete(0, tk.END)
                self.rut_widget.set_rut("")
                self.entry_contacto.delete(0, tk.END)
                self.actualizar_lista()
                self.establecer_foco_inicial()
            else:
                self._mostrar_error("Error", "No se pudo registrar el proveedor.", focus_widget=self.entry_nombre)
        else:
            self._mostrar_warning(
                "Autorización requerida",
                "Debe activar el modo supervisor antes de registrar un proveedor.",
                focus_widget=self.btn_sup
            )

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

        for i, p in enumerate(resultados):  # usar resultados aquí
            tag = tags[i % len(tags)]
            self.tree.insert("", tk.END,
                values=(p.id_proveedor, p.nombre, formatear_rut(p.rut), p.contacto),
                tags=(tag,)
            )

    def abrir_interfaz_proveedor(self, event):
        raise NotImplementedError("Este método debe ser implementado por la subclase.")

    def modo_supervisor(self):
        """Solicita credenciales y activa el modo supervisor si son válidas."""
        self.pedir_credenciales_supervisor(
            "Activar Modo Supervisor",
            lambda _user: self.mostrar_modo_supervisor(),
        )

    def cerrar_sesion(self):
        # Marcar que no hay supervisor activo
        self.supervisor_activo = False
        self.usuario_activo = None

        # Ocultar/destruir botón de logout
        if self.btn_logout:
            self.btn_logout.destroy()
            self.btn_logout = None

        # Rehabilitar botón de activar supervisor
        if self.btn_sup:
            self.btn_sup.config(state="normal", text="Modo Supervisor")

        # Limpiar campos del formulario
        self.entry_nombre.delete(0, tk.END)
        self.rut_widget.set_rut("")  # Limpia el RutEntry
        self.entry_contacto.delete(0, tk.END)

        # BLOQUEAR FORMULARIO de registrar proveedor
        self._bloquear_formulario()

        # Actualizar la lista para reflejar cambios
        self.actualizar_lista()

        self._mostrar_info("Sesión cerrada", "Has salido del modo supervisor.", focus_widget=self.entry_nombre)
        self.establecer_foco_inicial()

    def cerrar_aplicacion(self):
        try:
            self.root.quit()
        except tk.TclError:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass



    def more_proveedores(self):
        self.pedir_credenciales_supervisor("Activar Modo Supervisor", lambda user: self.mostrar_modo_supervisor())

    def configurar(self):
        self._mostrar_info("Configuración", "Aquí abrirías las configuraciones del sistema.", focus_widget=self.btn_config if self.btn_config else self.entry_nombre)

    def _forzar_fullscreen_modal(self, window):
        if window is None:
            return
        utils.aplicar_fullscreen(window, fullscreen=FULLSCREEN)

    def _post_popup_focus(self, focus_widget=None):
        def _focus():
            targets = []
            if focus_widget is not None:
                targets.append(focus_widget)
            targets.extend([
                getattr(self, "entry_nombre", None),
                self.root
            ])

            for target in targets:
                if not target:
                    continue
                try:
                    if hasattr(target, "winfo_exists") and not target.winfo_exists():
                        continue
                except tk.TclError:
                    continue

                try:
                    target.focus_force()
                    break
                except tk.TclError:
                    continue

        self.root.after_idle(_focus)

    def _mostrar_mensaje(self, tipo, titulo, mensaje, parent=None, focus_widget=None):
        parent = parent or self.root
        funciones = {
            "info": messagebox.showinfo,
            "warning": messagebox.showwarning,
            "error": messagebox.showerror,
        }
        func = funciones.get(tipo)
        if func is None:
            raise ValueError(f"Tipo de mensaje no soportado: {tipo}")
        func(titulo, mensaje, parent=parent)
        self._post_popup_focus(focus_widget)

    def _mostrar_info(self, titulo, mensaje, parent=None, focus_widget=None):
        self._mostrar_mensaje("info", titulo, mensaje, parent=parent, focus_widget=focus_widget)

    def _mostrar_warning(self, titulo, mensaje, parent=None, focus_widget=None):
        self._mostrar_mensaje("warning", titulo, mensaje, parent=parent, focus_widget=focus_widget)

    def _mostrar_error(self, titulo, mensaje, parent=None, focus_widget=None):
        self._mostrar_mensaje("error", titulo, mensaje, parent=parent, focus_widget=focus_widget)

    def mostrar_modo_supervisor(self):
        self.supervisor_activo = True
        self._habilitar_formulario()  # habilita los campos

        if not self.btn_logout:
            self.btn_logout = tk.Button(self.top_frame, text="⏻ Cerrar Sesión", bg=self.colores["boton"],
                                        fg=self.colores["boton_texto"], font=("Segoe UI", 9, "bold"),
                                        command=self.cerrar_sesion)
            self.btn_logout.pack(side=tk.RIGHT, padx=5)

        if self.btn_sup:
            self.btn_sup.config(state="disabled", text="Supervisor activo")

        self.actualizar_lista()
        self.establecer_foco_inicial()


    def _pedir_autorizacion_supervisor(self, nombre, rut_limpio, contacto):
        def callback(user):
            if ProveedorDAO.insertar(nombre, rut_limpio, contacto):
                self._mostrar_info("Éxito", "Proveedor registrado con autorización de supervisor.", focus_widget=self.entry_nombre)
                self.entry_nombre.delete(0, tk.END)
                self.rut_widget.clear()
                self.entry_contacto.delete(0, tk.END)
                self.actualizar_lista()
                self.mostrar_modo_supervisor()
            else:
                self._mostrar_error("Error", "No se pudo registrar el proveedor.", focus_widget=self.entry_nombre)

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
                self._mostrar_info("Éxito", "Supervisor autenticado.", parent=login_win, focus_widget=rut_entry)
                cerrar_modal()
                callback(user)
            else:
                self._mostrar_error("Error", "Credenciales inválidas.", parent=login_win, focus_widget=rut_entry)

        tk.Button(login_win, text="Ingresar", bg=self.colores["boton"],
                  fg=self.colores["boton_texto"], command=autenticar).pack(pady=10)
        cerrar_modal = self._configurar_modal(login_win, rut_entry, focus_after_close=self.entry_nombre, fullscreen=False)

    def configurar(self):
        self._mostrar_info("Configuración", "Aquí abrirías las configuraciones del sistema.", focus_widget=self.btn_config if self.btn_config else self.entry_nombre)

    def _configurar_modal(self, window, focus_widget=None, focus_after_close=None, fullscreen=True):
        if fullscreen and FULLSCREEN:
            self._forzar_fullscreen_modal(window)

        window.transient(self.root)
        window.grab_set()
        window.focus_force()

        def restaurar_foco():
            try:
                window.grab_release()
            except tk.TclError:
                pass
            if window.winfo_exists():
                window.destroy()
            self._post_popup_focus(focus_after_close)

        def _on_close():
            restaurar_foco()

        window.protocol("WM_DELETE_WINDOW", _on_close)

        if focus_widget is not None:
            window.after_idle(focus_widget.focus_set)

        return restaurar_foco


    def iniciar_proceso_dos_proveedores(self):
        proveedores = ProveedorDAO.obtener_activos()
        if len(proveedores) < 2:
            self._mostrar_warning("Atención", "No hay suficientes proveedores activos.", focus_widget=self.tree)
            return

        # Crear nueva ventana
        win = tk.Toplevel(self.root)
        win.title("Seleccionar 2 proveedores")
        if not FULLSCREEN:
            utils.centrar_ventana(win, 600, 480)
        win.configure(bg=self.colores["form_bg"])
        win.resizable(False, False)

        tk.Label(win, text="Selecciona exactamente 2 proveedores", bg=self.colores["form_bg"],
                 font=("Segoe UI", 10, "bold")).pack(pady=5)

        # Frame con scroll
        frame_scroll = tk.Frame(win, bg=self.colores["form_bg"])
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(frame_scroll, bg=self.colores["form_bg"])
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colores["form_bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Crear checkboxes de proveedores
        var_checks = []
        checkbox_widgets = []
        for p in proveedores:
            var = tk.IntVar()
            cb = tk.Checkbutton(scroll_frame, text=f"{p.nombre} ({formatear_rut(p.rut)})",
                                variable=var, bg=self.colores["form_bg"], anchor="w")
            cb.pack(fill=tk.X, padx=5, pady=2)
            var_checks.append((var, p))
            checkbox_widgets.append(cb)

        # Frame para porcentajes
        frame_porcentajes = tk.Frame(win, bg=self.colores["form_bg"])
        frame_porcentajes.pack(pady=10)

        lbl_p1 = tk.Label(frame_porcentajes, text="Porcentaje Proveedor 1 (%)", bg=self.colores["form_bg"])
        lbl_p1.grid(row=0, column=0, pady=5)
        p1_entry = tk.Entry(frame_porcentajes, width=10)
        p1_entry.grid(row=0, column=1, pady=5, padx=5)

        lbl_p2 = tk.Label(frame_porcentajes, text="Porcentaje Proveedor 2 (%)", bg=self.colores["form_bg"])
        lbl_p2.grid(row=1, column=0, pady=5)
        p2_entry = tk.Entry(frame_porcentajes, width=10)
        p2_entry.grid(row=1, column=1, pady=5, padx=5)

        # Validación solo números
        vcmd = self.root.register(utils.solo_numeros)
        p1_entry.config(validate="key", validatecommand=(vcmd, "%P"))
        p2_entry.config(validate="key", validatecommand=(vcmd, "%P"))

        def actualizar_labels():
            """Actualiza los nombres de los proveedores en los labels de porcentaje."""
            seleccionados = [p for var, p in var_checks if var.get() == 1]
            if len(seleccionados) == 2:
                lbl_p1.config(text=f"Porcentaje {seleccionados[0].nombre} (%)")
                lbl_p2.config(text=f"Porcentaje {seleccionados[1].nombre} (%)")
            else:
                lbl_p1.config(text="Porcentaje Proveedor 1 (%)")
                lbl_p2.config(text="Porcentaje Proveedor 2 (%)")

        # Vincular actualización al cambiar checkboxes
        for var, _ in var_checks:
            var.trace_add("write", lambda *args: actualizar_labels())

        cerrar_win = self._configurar_modal(win, focus_widget=p1_entry, focus_after_close=self.entry_nombre)

        def confirmar():
            seleccionados = [p for var, p in var_checks if var.get() == 1]
            if len(seleccionados) != 2:
                foco_check = checkbox_widgets[0] if checkbox_widgets else win
                self._mostrar_error("Error", "Debes seleccionar exactamente 2 proveedores.", parent=win, focus_widget=foco_check)
                return

            try:
                porc1 = float(p1_entry.get())
                porc2 = float(p2_entry.get())
            except ValueError:
                self._mostrar_error("Error", "Los porcentajes deben ser números.", parent=win, focus_widget=p1_entry)
                return

            if abs(porc1 + porc2 - 100) > 0.01:
                self._mostrar_error("Error", "La suma de los porcentajes debe ser 100%.", parent=win, focus_widget=p1_entry)
                return

            # Guardar proceso en base de datos
            ProcesoLoteDAO.guardar_proceso(seleccionados[0].id_proveedor,
                                           seleccionados[1].id_proveedor,
                                           porc1, porc2)

            self._mostrar_info(
                "Proceso guardado",
                f"Proceso registrado con {seleccionados[0].nombre} ({porc1}%) y {seleccionados[1].nombre} ({porc2}%)",
                parent=win,
                focus_widget=win
            )
            cerrar_win()
            self.abrir_interfaz_clasificacion(seleccionados[0], seleccionados[1], porc1, porc2)

        tk.Button(win, text="Confirmar", bg=self.colores["boton"], fg=self.colores["boton_texto"],
                  font=("Segoe UI", 9, "bold"), command=confirmar).pack(pady=10)

        tk.Button(win, text="Cerrar", bg=self.colores["boton"], fg=self.colores["boton_texto"],
                  font=("Segoe UI", 9, "bold"), command=cerrar_win).pack(pady=(0, 10))

    def abrir_interfaz_clasificacion(self, prov1, prov2, porc1, porc2):
        try:
            # No hace falta importar aquí, ya lo hicimos arriba
            win_clasificacion = tk.Toplevel(self.root)
            win_clasificacion.title("Clasificación Doble Proveedor")
            if not FULLSCREEN:
                utils.centrar_ventana(win_clasificacion, 600, 480)
            win_clasificacion.resizable(False, False)
            self._configurar_modal(win_clasificacion, focus_widget=win_clasificacion, focus_after_close=self.entry_nombre)

            # Instanciar la interfaz con ambos proveedores
            InterfazViewDoble(win_clasificacion, [prov1, prov2], porcentajes=(porc1, porc2))
        except Exception as e:
            self._mostrar_error("Error", f"No se pudo abrir la interfaz: {e}", focus_widget=self.entry_nombre)
