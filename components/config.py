# Resolución de pantalla
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FULLSCREEN = True

# Colores
COL_FONDO = "#FBE9D0"
COL_BOTON = "#A67C52"
COL_BOTON_TEXTO = "#FFFFFF"
COL_FORM_BG = "#FFF2E0"
COL_TEXTO = "#000000"
COL_TABLA_FILA = "#F2DBBB"
COL_TABLA_SELECCION = "#D9A65A"
COL_TABLA_HEADER = "#A67C52"
COL_TEXTO_SELECCION = "#FFFFFF"

# Paths
IMG_BANNER = "components/img/banner_Nuts.png"

# Fuentes
FONT_DEFAULT = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")


def set_fullscreen(enabled: bool) -> None:
    """Permite alternar el modo de vista de toda la aplicación en tiempo de ejecución."""
    global FULLSCREEN
    FULLSCREEN = bool(enabled)
