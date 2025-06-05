import tkinter as tk
from tkinter import messagebox

class LoginView:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("Inicio de sesión")
        self.root.geometry("300x200")

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

        if usuario == "admin" and clave == "1234":
            self.root.destroy()
            self.on_login_success()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")
