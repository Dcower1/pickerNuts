
import tkinter as tk  
import re

def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

def crear_boton_toggle(root, callback, estado_inicial=False):
    estado = {'activo': estado_inicial}

    def alternar():
        estado['activo'] = not estado['activo']
        boton.config(
            text="DETENER" if estado['activo'] else "START",
            bg="red" if estado['activo'] else "green"
        )
        callback(estado['activo'])

    boton = tk.Button(root, text="START", bg="green", fg="white",
                      font=("Arial", 14, "bold"), width=10, height=2,
                      command=alternar)
    boton.estado = estado
    return boton



def validar_rut(rut):
    """Valida formato RUT chileno simple (sin puntos, con guión)"""
    rut = rut.upper().replace(".", "").replace("-", "")
    if len(rut) < 2:
        return False
    cuerpo, verificador = rut[:-1], rut[-1]
    try:
        suma = sum(int(cuerpo[-i - 1]) * (2 + i % 6) for i in range(len(cuerpo)))
        digito = 11 - (suma % 11)
        if digito == 11:
            dv = "0"
        elif digito == 10:
            dv = "K"
        else:
            dv = str(digito)
        return dv == verificador
    except:
        return False

def validar_contacto(contacto):
    """Valida formato número chileno: +569XXXXXXXX o 9XXXXXXXX"""
    return bool(re.match(r"^(\+569\d{8}|9\d{8})$", contacto.strip()))