import tkinter as tk
from tkinter import messagebox
from components import utils
import hashlib
import sqlite3
from components.utils import obtener_colores
from models.DTO.usuario_dto import Usuario

class LoginView:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("Inicio de sesión")

        # Obtener colores
        colores = obtener_colores()
        bg_color = colores["fondo"]
        btn_color = colores["boton"]
        text_color = colores["texto"]
        entry_bg = colores["form_bg"]
        header_color = colores["tabla_header"]
        

        self.root.configure(bg=bg_color)
        utils.centrar_ventana(self.root, 950, 550)

        
        frame_login = tk.Frame(root, bg=header_color, bd=2, relief="groove")
        frame_login.place(relx=0.5, rely=0.5, anchor="center")

        # login
        tk.Label(frame_login, text="Usuario", bg=header_color, fg=text_color, font=("Segoe UI", 12)).pack(padx=20, pady=(20, 5))
        self.entry_user = tk.Entry(frame_login, bg=entry_bg, fg=text_color)
        self.entry_user.pack(padx=20, pady=5)

        tk.Label(frame_login, text="Contraseña", bg=header_color, fg=text_color, font=("Segoe UI", 12)).pack(padx=20, pady=(10, 5))
        self.entry_pass = tk.Entry(frame_login, show="*", bg=entry_bg, fg=text_color)
        self.entry_pass.pack(padx=20, pady=5)

        tk.Button(
            frame_login,
            text="Iniciar sesión",
            command=self.login,
            bg=btn_color,
            fg="white",
            activebackground=text_color,
            activeforeground="white"
        ).pack(pady=20)



    def login(self):
        usuario = self.entry_user.get()
        clave = self.entry_pass.get()
        password_hash = hashlib.sha256(clave.encode()).hexdigest()

        try:
            conn = sqlite3.connect("sistema_nueces.db")
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM superusuarios WHERE nombre = ? AND contrasena_hash = ?", (usuario, password_hash))
            row = cursor.fetchone()
            conn.close()

            if row:
                id_usuario = row[0]
                nombre = row[1]
                rol = row[3]

                usuario_obj = Usuario(id_usuario, nombre, rol)
                self.on_login_success(usuario_obj)  # <-- ahora se pasa el objeto Usuario

            else:
                messagebox.showerror("Error", "Credenciales incorrectas")

        except sqlite3.Error as e:
            messagebox.showerror("Error de base de datos", f"Error al conectar con base de datos: {e}")
