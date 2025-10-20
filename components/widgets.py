import tkinter as tk
import re

class RutEntry(tk.Frame):
    """
    Widget compuesto que incluye:
    - Entry para ingresar solo números (sin puntos ni guiones).
    - Label debajo que muestra el RUT formateado en tiempo real.
    """

    def __init__(self, master=None, bg="#E8C191", fg="black", *args, **kwargs):
        super().__init__(master, bg=bg, *args, **kwargs)

        self.rut_var = tk.StringVar()

        # Entry con validación (solo dígitos)
        vcmd = (self.register(self._only_digits), '%P')
        self.entry = tk.Entry(self, textvariable=self.rut_var,
                              validate='key', validatecommand=vcmd,
                              bg="white", fg=fg)
        self.entry.pack(fill="x", pady=(0, 2))

        # Label que muestra el RUT formateado
        self.lbl_formato = tk.Label(self, text="", bg=bg, fg="gray", font=("Segoe UI", 8, "italic"))
        self.lbl_formato.pack(anchor="w")

        # Vincular actualización
        self.rut_var.trace_add("write", self._actualizar_formato)

    def _only_digits(self, proposed_value):
        """Validar que solo entren dígitos"""
        if proposed_value == "":
            return True
        return proposed_value.isdigit()

    def _actualizar_formato(self, *args):
        rut = ''.join(filter(str.isdigit, self.rut_var.get()))
        if not rut:
            self.lbl_formato.config(text="")
            return

        cuerpo, dv = rut[:-1], rut[-1]
        cuerpo_con_puntos = re.sub(r"(?<=\d)(?=(\d{3})+$)", ".", cuerpo) if cuerpo else ""
        rut_formateado = f"{cuerpo_con_puntos}-{dv}" if cuerpo else dv
        self.lbl_formato.config(text=rut_formateado)

    def get_rut(self):
        """Devuelve el RUT solo con números"""
        return ''.join(filter(str.isdigit, self.rut_var.get()))

    def set_rut(self, rut):
        """Setea el RUT (como números)"""
        rut_limpio = ''.join(filter(str.isdigit, rut))
        self.rut_var.set(rut_limpio)

    def clear(self):
        """Limpia el RUT ingresado y el label de formato"""
        self.rut_var.set("")
        self.lbl_formato.config(text="")

    def disable(self):
        self.entry.config(state="disabled")

    def enable(self):
        self.entry.config(state="normal")
