"""
Servicio de gestión de puntos.
Acumulación de puntos por compras y consulta de historial.
"""
import math
from app.models.database import obtener_supabase
from app.config import NIVELES, PESOS_POR_PUNTO
from app.services.cliente_service import actualizar_nivel_cliente


def acumular_puntos(cliente_id: str, monto: float, nivel_actual: str) -> dict:
    """
    Acumula puntos por una compra.
    Calcula los puntos base ($10 MXN = 1 punto) y aplica el multiplicador del nivel.
    Retorna un dict con los puntos otorgados y el nuevo total.
    """
    db = obtener_supabase()

    # Calcular puntos base y aplicar multiplicador
    config_nivel = NIVELES.get(nivel_actual, NIVELES['Bronce'])
    multiplicador = config_nivel['multiplicador']
    puntos_base = math.floor(monto / PESOS_POR_PUNTO)
    puntos_otorgados = math.floor(puntos_base * multiplicador)

    if puntos_otorgados <= 0:
        return {'puntos_otorgados': 0, 'mensaje': 'El monto es muy bajo para generar puntos.'}

    # Obtener puntos actuales del cliente
    cliente = db.table('clientes').select('puntos').eq('id', cliente_id).execute()
    puntos_actuales = cliente.data[0]['puntos']
    nuevo_total = puntos_actuales + puntos_otorgados

    # Actualizar puntos del cliente
    db.table('clientes').update({
        'puntos': nuevo_total
    }).eq('id', cliente_id).execute()

    # Registrar la transacción
    db.table('transacciones').insert({
        'cliente_id': cliente_id,
        'tipo': 'compra',
        'monto': monto,
        'puntos': puntos_otorgados,
        'descripcion': f'Compra por ${monto:.2f} MXN (+{puntos_otorgados} pts, x{multiplicador})',
    }).execute()

    # Verificar si subió de nivel
    nuevo_nivel = actualizar_nivel_cliente(cliente_id, nuevo_total)

    return {
        'puntos_otorgados': puntos_otorgados,
        'puntos_base': puntos_base,
        'multiplicador': multiplicador,
        'nuevo_total': nuevo_total,
        'nuevo_nivel': nuevo_nivel,
        'subio_nivel': nuevo_nivel != nivel_actual,
    }


def obtener_historial(cliente_id: str, limite: int = 10) -> list:
    """Obtiene las últimas transacciones del cliente."""
    db = obtener_supabase()
    resultado = (
        db.table('transacciones')
        .select('*')
        .eq('cliente_id', cliente_id)
        .order('fecha', desc=True)
        .limit(limite)
        .execute()
    )
    return resultado.data


def formatear_historial(cliente_nombre: str, transacciones: list) -> str:
    """Formatea el historial de transacciones para enviar por WhatsApp."""
    if not transacciones:
        return "📋 Aún no tienes transacciones registradas."

    lineas = [f"📋 *Historial de {cliente_nombre}*\n━━━━━━━━━━━━━━━━━━"]

    for t in transacciones:
        fecha = t['fecha'][:10]
        tipo = t['tipo'].capitalize()
        puntos = t['puntos']

        if t['tipo'] == 'compra':
            icono = '🛒'
            signo = '+'
        elif t['tipo'] == 'canje':
            icono = '🎁'
            signo = '-'
        else:
            icono = '🎉'
            signo = '+'

        lineas.append(
            f"{icono} {fecha} | {tipo}\n"
            f"   {signo}{puntos} pts - {t['descripcion']}"
        )

    lineas.append("━━━━━━━━━━━━━━━━━━")
    return '\n'.join(lineas)
