"""
Servicio de gestión de clientes.
Registro, consulta y actualización de nivel de clientes.
"""
from datetime import datetime
from app.models.database import obtener_supabase
from app.config import NIVELES, PUNTOS_BIENVENIDA


def buscar_cliente_por_telefono(telefono: str) -> dict | None:
    """Busca un cliente por su número de teléfono."""
    db = obtener_supabase()
    resultado = (
        db.table('clientes')
        .select('*')
        .eq('telefono', telefono)
        .execute()
    )
    if resultado.data:
        return resultado.data[0]
    return None


def registrar_cliente(nombre: str, telefono: str) -> dict:
    """
    Registra un nuevo cliente con puntos de bienvenida.
    Retorna el cliente creado.
    """
    db = obtener_supabase()

    # Crear el cliente con puntos de bienvenida
    nuevo_cliente = {
        'nombre': nombre.strip().title(),
        'telefono': telefono,
        'puntos': PUNTOS_BIENVENIDA,
        'nivel': 'Bronce',
    }

    resultado = (
        db.table('clientes')
        .insert(nuevo_cliente)
        .execute()
    )
    cliente = resultado.data[0]

    # Registrar la transacción de bienvenida
    db.table('transacciones').insert({
        'cliente_id': cliente['id'],
        'tipo': 'bienvenida',
        'monto': 0,
        'puntos': PUNTOS_BIENVENIDA,
        'descripcion': f'Bienvenida a FideliPyme - {PUNTOS_BIENVENIDA} puntos de regalo',
    }).execute()

    return cliente


def calcular_nivel(puntos: int) -> str:
    """Determina el nivel del cliente según sus puntos acumulados."""
    for nombre_nivel, config in NIVELES.items():
        if config['min'] <= puntos <= config['max']:
            return nombre_nivel
    return 'Bronce'


def actualizar_nivel_cliente(cliente_id: str, puntos_actuales: int) -> str:
    """Actualiza el nivel del cliente si corresponde. Retorna el nivel nuevo."""
    nuevo_nivel = calcular_nivel(puntos_actuales)
    db = obtener_supabase()
    db.table('clientes').update({
        'nivel': nuevo_nivel
    }).eq('id', cliente_id).execute()
    return nuevo_nivel


def obtener_info_cliente(telefono: str) -> str:
    """Genera un mensaje con la información del cliente."""
    cliente = buscar_cliente_por_telefono(telefono)
    if not cliente:
        return "No se encontró tu cuenta. Escribe cualquier cosa para registrarte."

    nivel = cliente['nivel']
    config_nivel = NIVELES.get(nivel, NIVELES['Bronce'])
    multiplicador = config_nivel['multiplicador']

    # Calcular puntos para el siguiente nivel
    siguiente_nivel = ''
    if nivel == 'Bronce':
        faltan = 100 - cliente['puntos']
        siguiente_nivel = f"\n📈 Te faltan *{faltan} puntos* para subir a *Plata*"
    elif nivel == 'Plata':
        faltan = 250 - cliente['puntos']
        siguiente_nivel = f"\n📈 Te faltan *{faltan} puntos* para subir a *Oro*"
    elif nivel == 'Oro':
        faltan = 500 - cliente['puntos']
        siguiente_nivel = f"\n📈 Te faltan *{faltan} puntos* para subir a *Platino*"
    elif nivel == 'Platino':
        siguiente_nivel = "\n👑 ¡Estás en el nivel máximo!"

    return (
        f"👤 *{cliente['nombre']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Puntos: *{cliente['puntos']}*\n"
        f"🏅 Nivel: *{nivel}*\n"
        f"✖️ Multiplicador: *x{multiplicador}*\n"
        f"{siguiente_nivel}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Cliente desde: {cliente['fecha_registro'][:10]}"
    )
