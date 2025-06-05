import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controlador import app_controller

if __name__ == "__main__":
    app_controller.iniciar_app()