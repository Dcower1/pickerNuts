import tkinter as tk
from tkinter import ttk, messagebox

from components import utils
import components.config as app_config
from components.widgets import RutEntry
from models.DAO.superusuario_dao import SuperUsuarioDAO


class ConfiguracionView:
    def __init__(
        self,
        parent,
        colores,
        on_close=None,
        puede_gestionar_supervisores=False,
    ):
        self.parent = parent
        self.colores = colores
        self.on_close = on_close
        self.puede_gestionar_supervisores = bool(puede_gestionar_supervisores)
        self.window = tk.Toplevel(parent)
        self.window.title("Configuración")
        self.window.configure(bg=self.colores["fondo"])
        self.window.resizable(False, False)
        self.window.transient(parent)
        self._actualizando_view_mode = False

        self.view_mode_var = tk.StringVar(
            value="Fullscreen" if app_config.FULLSCREEN else "Modo ventana"
        )

        self._crear_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        try:
            self.window.grab_set()
        except tk.TclError:
            pass
        self._ajustar_dimensiones_window(fullscreen=False)
        self.window.after_idle(self.window.focus_force)

    def _crear_ui(self):
        titulo = tk.Label(
            self.window,
            text="Configuración",
            font=("Segoe UI", 22, "bold"),
            bg=self.colores["fondo"],
            fg=self.colores["texto"],
        )
        titulo.pack(anchor="n", pady=(30, 10))

        opciones_frame = tk.Frame(self.window, bg=self.colores["form_bg"])
        opciones_frame.pack(fill=tk.BOTH, expand=True, padx=60, pady=10)

        def crear_fila(texto):
            fila = tk.Frame(opciones_frame, bg=self.colores["form_bg"], pady=15)
            fila.pack(fill=tk.X, padx=30, pady=5)
            etiqueta = tk.Label(
                fila,
                text=texto,
                font=("Segoe UI", 12, "bold"),
                bg=self.colores["form_bg"],
                fg=self.colores["texto"],
                anchor="w",
            )
            etiqueta.pack(side=tk.LEFT, fill=tk.X, expand=True)
            contenedor = tk.Frame(fila, bg=self.colores["form_bg"])
            contenedor.pack(side=tk.RIGHT)
            return contenedor

        fila_vista = crear_fila("Modo de vista")
        self.view_mode_combo = ttk.Combobox(
            fila_vista,
            textvariable=self.view_mode_var,
            values=("Fullscreen", "Modo ventana"),
            state="readonly",
            width=18,
            font=("Segoe UI", 11),
        )
        self.view_mode_combo.pack(side=tk.LEFT, padx=5)
        self.view_mode_combo.bind("<<ComboboxSelected>>", self._on_view_mode_selected)

        fila_supervisor = crear_fila("Ingresar nuevo supervisor")
        btn_dim = {"width": 16, "height": 2, "font": ("Segoe UI", 11, "bold")}
        tk.Button(
            fila_supervisor,
            text="Agregar",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            command=self._abrir_modal_nuevo_supervisor,
            **btn_dim,
        ).pack(side=tk.LEFT, padx=5)

        bottom_frame = tk.Frame(self.window, bg=self.colores["fondo"])
        bottom_frame.pack(fill=tk.X, padx=60, pady=20, side=tk.BOTTOM)
        tk.Button(
            bottom_frame,
            text="Volver",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            font=("Segoe UI", 11, "bold"),
            width=12,
            command=self.cerrar,
        ).pack(side=tk.LEFT)

    def _on_view_mode_selected(self, _event=None):
        if self._actualizando_view_mode:
            return
        seleccion = (self.view_mode_var.get() or "").strip().lower()
        self._cambiar_modo_vista(seleccion == "fullscreen")

    def _cambiar_modo_vista(self, fullscreen: bool):
        app_config.set_fullscreen(bool(fullscreen))
        if fullscreen:
            utils.aplicar_fullscreen(self.parent, fullscreen=True)
            utils.aplicar_fullscreen(self.window, fullscreen=True)
        else:
            utils.aplicar_fullscreen(self.parent, fullscreen=False)
            utils.maximizar_ventana(self.parent)
            self._ajustar_dimensiones_window(fullscreen=False)
        self._sincronizar_dropdown()

    def _sincronizar_dropdown(self):
        valor = "Fullscreen" if app_config.FULLSCREEN else "Modo ventana"
        if self.view_mode_var.get() != valor:
            self._actualizando_view_mode = True
            self.view_mode_var.set(valor)
            self._actualizando_view_mode = False

    def _ajustar_dimensiones_window(self, fullscreen: bool):
        if fullscreen:
            return
        utils.aplicar_fullscreen(self.window, fullscreen=False)
        self.window.update_idletasks()
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        usable_h = max(580, screen_h - 200)
        usable_w = max(880, screen_w - 240)
        x = max(20, (screen_w - usable_w) // 2)
        y = max(80, (screen_h - usable_h) // 2)
        self.window.geometry(f"{int(usable_w)}x{int(usable_h)}+{int(x)}+{int(y)}")

    def _abrir_modal_nuevo_supervisor(self):
        if not self.puede_gestionar_supervisores:
            messagebox.showwarning(
                "Permiso requerido",
                "Debes iniciar sesión como supervisor desde el menú principal antes de ingresar nuevos supervisores.",
                parent=self.window,
            )
            return
        win = tk.Toplevel(self.window)
        win.title("Ingresar nuevo supervisor")
        win.configure(bg=self.colores["form_bg"])
        utils.centrar_ventana(win, 360, 320)
        win.resizable(False, False)
        win.transient(self.window)

        tk.Label(win, text="Nombre de usuario", bg=self.colores["form_bg"], fg=self.colores["texto"]).pack(pady=(15, 5))
        entry_nombre = tk.Entry(win)
        entry_nombre.pack(padx=20, fill=tk.X)

        tk.Label(win, text="RUT", bg=self.colores["form_bg"], fg=self.colores["texto"]).pack(pady=(15, 5))
        rut_entry = RutEntry(win)
        rut_entry.pack(padx=20, fill=tk.X)

        tk.Label(win, text="Contraseña", bg=self.colores["form_bg"], fg=self.colores["texto"]).pack(pady=(15, 5))
        entry_pass = tk.Entry(win, show="*")
        entry_pass.pack(padx=20, fill=tk.X)

        def guardar_supervisor():
            nombre = entry_nombre.get().strip()
            rut = rut_entry.get_rut().strip()
            password = entry_pass.get().strip()

            if not nombre or not rut or not password:
                messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios.", parent=win)
                entry_nombre.focus_force()
                return

            if not utils.validar_rut(rut):
                messagebox.showerror("Rut inválido", "Ingresa un RUT válido (sin puntos, con guion).", parent=win)
                rut_entry.focus_force()
                return

            if len(password) < 10:
                messagebox.showerror("Contraseña inválida", "La contraseña debe tener al menos 10 caracteres.", parent=win)
                entry_pass.focus_force()
                return

            exito, mensaje = SuperUsuarioDAO.crear_supervisor(nombre, rut, password)
            if exito:
                messagebox.showinfo("Éxito", mensaje, parent=win)
                cerrar_modal()
            else:
                messagebox.showerror("Error", mensaje, parent=win)

        tk.Button(
            win,
            text="Guardar",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            font=("Segoe UI", 10, "bold"),
            command=guardar_supervisor,
        ).pack(pady=(20, 5))

        tk.Button(
            win,
            text="Cancelar",
            bg=self.colores["boton"],
            fg=self.colores["boton_texto"],
            command=lambda: cerrar_modal(),
        ).pack(pady=(0, 15))

        def cerrar_modal():
            try:
                win.grab_release()
            except tk.TclError:
                pass
            win.destroy()

        try:
            win.grab_set()
        except tk.TclError:
            pass
        win.protocol("WM_DELETE_WINDOW", cerrar_modal)
        win.after_idle(entry_nombre.focus_force)

    def focus(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()

    def cerrar(self):
        if self.window and self.window.winfo_exists():
            try:
                self.window.grab_release()
            except tk.TclError:
                pass
            self.window.destroy()
        if self.on_close:
            self.on_close()
