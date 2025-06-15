import tkinter as tk
from tkinter import messagebox
from components import utils
import hashlib
import sqlite3
from models.DTO.usuario_dto import Usuario

class LoginView:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("Inicio de sesión")

        utils.centrar_ventana(self.root, 300, 200)

        tk.Label(root, text="Usuario").pack()
        self.entry_user = tk.Entry(root)
        self.entry_user.pack()

        tk.Label(root, text="Contraseña").pack()
        self.entry_pass = tk.Entry(root, show="*")
        self.entry_pass.pack()

        tk.Button(root, text="Iniciar sesión", command=self.login).pack(pady=10)

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
