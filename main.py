import sys # Importa el módulo sys, que proporciona acceso a funciones y objetos mantenidos por el intérprete.
import os # Importa el módulo os, que proporciona una forma de usar funcionalidades dependientes del sistema operativo.
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

from controlador import app_controller 

if __name__ == "__main__": # Comprueba si el script se está ejecutando directamente.
    app_controller.iniciar_app() # Inicia la aplicación.