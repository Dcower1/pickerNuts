import tkinter as tk
import re 


# Centra una ventana de Tkinter en la pantalla.
def centrar_ventana(ventana, ancho, alto): 
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# Crea un botón de alternancia (START/DETENER) que ejecuta un callback.
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

def formatear_rut(rut: str) -> str:
    """Formatea un RUT sin puntos ni guión -> XX.XXX.XXX-X"""
    if not rut.isdigit():
        return rut  # si viene raro, lo dejo como está
    
    cuerpo = rut[:-1]
    dv = rut[-1]
    cuerpo_con_puntos = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_con_puntos}-{dv}"





def validar_rut(rut): # Valida el formato de un RUT chileno (sin puntos, con guión) gracias CHATGPT.
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
    

# Valida el formato de un número de contacto chileno (+569XXXXXXXX o 9XXXXXXXX).
def validar_contacto(contacto): 
    """Valida formato número chileno: +569XXXXXXXX o 9XXXXXXXX"""
    return bool(re.match(r"^(\+569\d{8}|9\d{8})$", contacto.strip()))


def filtrar_proveedores(lista_proveedores, termino):

    termino = termino.lower()
    resultado = []

    for p in lista_proveedores:
        if (termino in str(p.id_proveedor).lower() or
            termino in p.nombre.lower() or
            termino in p.rut.lower() or
            termino in p.contacto.lower()):
            resultado.append(p)

    return resultado



def obtener_colores():
    return {
        "fondo": "#FBE9D0",
        "form_bg": "#E8C192",
        "boton": "#8A4B25",
        "boton_texto": "#FFFFFF",
        "tabla_header": "#A26C34",
        "tabla_fila": "#E8C191",
        "texto": "#27160A",
        "tabla_seleccion": "#D6A86D",
        "texto_seleccion": "#000000",
    }



def solo_numeros(P):
    """Valida que el valor sea numérico (float) o vacío."""
    if P == "":
        return True
    try:
        float(P)
        return True
    except ValueError:
        return False


def aplicar_fullscreen(ventana, fullscreen=True):
    """
    Intenta poner una ventana en modo fullscreen de manera segura, con fallbacks.
    Si fullscreen=False, revierte el modo fullscreen cuando es posible.
    """
    if ventana is None:
        return

    try:
        ventana.update_idletasks()
    except tk.TclError:
        return

    if fullscreen:
        aplicado = False
        try:
            ventana.attributes("-fullscreen", True)
            aplicado = True
        except tk.TclError:
            aplicado = False

        if not aplicado:
            try:
                ventana.state("zoomed")
                aplicado = True
            except tk.TclError:
                aplicado = False

        if not aplicado:
            try:
                screen_w = ventana.winfo_screenwidth()
                screen_h = ventana.winfo_screenheight()
                ventana.geometry(f"{screen_w}x{screen_h}+0+0")
                aplicado = True
            except tk.TclError:
                aplicado = False

        if aplicado:
            try:
                ventana.focus_force()
            except tk.TclError:
                pass
    else:
        try:
            ventana.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            ventana.state("normal")
        except tk.TclError:
            pass


def maximizar_ventana(ventana, offset_top=0, offset_bottom=0, offset_lr=0):
    """Intenta maximizar una ventana respetando los bordes y dejando espacio para la barra de tareas."""
    if ventana is None:
        return
    try:
        ventana.update_idletasks()
    except tk.TclError:
        return

    try:
        ventana.state("zoomed")
        return
    except tk.TclError:
        pass

    try:
        screen_w = ventana.winfo_screenwidth()
        screen_h = ventana.winfo_screenheight()
        offset_top = max(0, int(offset_top))
        offset_bottom = max(0, int(offset_bottom))
        offset_lr = max(0, int(offset_lr))
        ancho = max(600, screen_w - offset_lr * 2)
        alto = max(400, screen_h - offset_top - offset_bottom)
        ventana.geometry(f"{int(ancho)}x{int(alto)}+{offset_lr}+{offset_top}")
    except tk.TclError:
        pass
