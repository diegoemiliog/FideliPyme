"""
Configuración central de FideliPyme.
Carga las variables de entorno y define constantes del sistema.
"""
import os

# === Twilio ===
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

# === Supabase ===
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# === Niveles de cliente ===
# Cada nivel tiene: nombre, rango mínimo, rango máximo, multiplicador de puntos
NIVELES = {
    'Bronce':  {'min': 0,   'max': 99,   'multiplicador': 1.0},
    'Plata':   {'min': 100, 'max': 249,  'multiplicador': 1.25},
    'Oro':     {'min': 250, 'max': 499,  'multiplicador': 1.5},
    'Platino': {'min': 500, 'max': float('inf'), 'multiplicador': 2.0},
}

# === Puntos ===
# Por cada $10 MXN de compra se otorga 1 punto base
PESOS_POR_PUNTO = 10
PUNTOS_BIENVENIDA = 10
