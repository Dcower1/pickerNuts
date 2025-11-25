"""
Ajusta sys.path para que los módulos del proyecto se puedan importar en las pruebas
ejecutadas desde el directorio test/.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
