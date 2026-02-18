"""
Servicio de gestión de premios.
Consulta del catálogo y canje de premios.
"""
from app.models.database import obtener_supabase
from app.services.cliente_service import actualizar_nivel_cliente


def obtener_catalogo() -> list:
    """Obtiene todos los premios activos ordenados por costo."""
    db = obtener_supabase()
    resultado = (
        db.table('premios')
        .select('*')
        .eq('activo', True)
        .order('costo_puntos', desc=False)
        .execute()
    )
    return resultado.data


def formatear_catalogo(premios: list, puntos_cliente: int) -> str:
    """Formatea el catálogo de premios para enviar por WhatsApp."""
    if not premios:
        return "😅 No hay premios disponibles en este momento."

    lineas = [
        "🎁 *Catálogo de Premios*\n━━━━━━━━━━━━━━━━━━",
        f"💰 Tus puntos: *{puntos_cliente}*\n",
    ]

    for i, premio in enumerate(premios, 1):
        disponible = "✅" if puntos_cliente >= premio['costo_puntos'] else "🔒"
        lineas.append(
            f"{disponible} *{i}. {premio['nombre']}* - {premio['costo_puntos']} pts\n"
            f"   {premio['descripcion']}"
        )

    lineas.append(
        "\n━━━━━━━━━━━━━━━━━━\n"
        "Para canjear, escribe *3* y luego el número del premio."
    )
    return '\n'.join(lineas)


def canjear_premio(cliente_id: str, premio_indice: int) -> dict:
    """
    Canjea un premio para el cliente.
    premio_indice: posición en el catálogo (1-based).
    Retorna un dict con el resultado del canje.
    """
    db = obtener_supabase()

    # Obtener catálogo
    premios = obtener_catalogo()
    if not premios:
        return {'exito': False, 'mensaje': 'No hay premios disponibles.'}

    if premio_indice < 1 or premio_indice > len(premios):
        return {
            'exito': False,
            'mensaje': f'Opción inválida. Elige un número del 1 al {len(premios)}.'
        }

    premio = premios[premio_indice - 1]

    # Verificar puntos del cliente
    cliente = (
        db.table('clientes')
        .select('puntos, nombre')
        .eq('id', cliente_id)
        .execute()
    ).data[0]

    if cliente['puntos'] < premio['costo_puntos']:
        faltan = premio['costo_puntos'] - cliente['puntos']
        return {
            'exito': False,
            'mensaje': (
                f"❌ No tienes suficientes puntos para *{premio['nombre']}*.\n"
                f"Necesitas: {premio['costo_puntos']} pts\n"
                f"Tienes: {cliente['puntos']} pts\n"
                f"Te faltan: {faltan} pts"
            )
        }

    # Descontar puntos
    nuevo_total = cliente['puntos'] - premio['costo_puntos']
    db.table('clientes').update({
        'puntos': nuevo_total
    }).eq('id', cliente_id).execute()

    # Registrar transacción de canje
    db.table('transacciones').insert({
        'cliente_id': cliente_id,
        'tipo': 'canje',
        'monto': 0,
        'puntos': premio['costo_puntos'],
        'descripcion': f"Canje: {premio['nombre']}",
    }).execute()

    # Actualizar nivel por si bajó
    nuevo_nivel = actualizar_nivel_cliente(cliente_id, nuevo_total)

    return {
        'exito': True,
        'mensaje': (
            f"🎉 *¡Premio canjeado exitosamente!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎁 {premio['nombre']}\n"
            f"💰 Puntos usados: {premio['costo_puntos']}\n"
            f"⭐ Puntos restantes: {nuevo_total}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Muestra este mensaje en caja para reclamar tu premio."
        ),
        'premio': premio['nombre'],
        'puntos_restantes': nuevo_total,
    }
