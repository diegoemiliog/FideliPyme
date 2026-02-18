"""
FideliPyme - Sistema de Fidelización para PyMES
Punto de entrada principal de la aplicación.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar la app
load_dotenv()

from app import crear_app

app = crear_app()

if __name__ == '__main__':
    puerto = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=puerto, debug=debug)
