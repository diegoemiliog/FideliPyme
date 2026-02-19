"""
Rutas del webhook de Twilio para WhatsApp.
Recibe los mensajes entrantes y envía las respuestas.
"""
from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from app.handlers.whatsapp_handler import procesar_mensaje
from app.services.cliente_service import buscar_cliente_por_telefono
from app.services.puntos_service import acumular_puntos

webhook_bp = Blueprint('webhook', __name__)


@webhook_bp.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Endpoint que recibe los mensajes de WhatsApp vía Twilio.
    Twilio envía un POST con los datos del mensaje.
    """
    # Obtener datos del mensaje entrante
    mensaje_entrante = request.form.get('Body', '').strip()
    telefono_remitente = request.form.get('From', '')

    # Procesar el mensaje y obtener respuesta
    respuesta_texto = procesar_mensaje(telefono_remitente, mensaje_entrante)

    # Crear respuesta TwiML para Twilio
    respuesta = MessagingResponse()
    respuesta.message(respuesta_texto)

    return str(respuesta), 200, {'Content-Type': 'text/xml'}


@webhook_bp.route('/registrar-compra', methods=['POST'])
def registrar_compra():
    """
    Endpoint para que el negocio registre compras y otorgue puntos.
    Recibe JSON con: telefono (str) y monto (float).

    Ejemplo:
        POST /registrar-compra
        {"telefono": "whatsapp:+521234567890", "monto": 150.00}
    """
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Se requiere JSON con telefono y monto'}), 400

    telefono = datos.get('telefono', '')
    monto = datos.get('monto', 0)

    if not telefono or not monto:
        return jsonify({'error': 'Campos telefono y monto son requeridos'}), 400

    try:
        monto = float(monto)
    except (ValueError, TypeError):
        return jsonify({'error': 'El monto debe ser un número válido'}), 400

    if monto <= 0:
        return jsonify({'error': 'El monto debe ser mayor a 0'}), 400

    # Buscar al cliente
    cliente = buscar_cliente_por_telefono(telefono)
    if not cliente:
        return jsonify({'error': f'No se encontró cliente con teléfono {telefono}'}), 404

    # Acumular puntos
    resultado = acumular_puntos(cliente['id'], monto, cliente['nivel'])

    return jsonify({
        'exito': True,
        'cliente': cliente['nombre'],
        'monto': monto,
        'puntos_otorgados': resultado['puntos_otorgados'],
        'multiplicador': resultado['multiplicador'],
        'nuevo_total': resultado['nuevo_total'],
        'nivel': resultado['nuevo_nivel'],
        'subio_nivel': resultado['subio_nivel'],
    }), 200


@webhook_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para verificar que el servidor está activo."""
    return {'status': 'ok', 'servicio': 'FideliPyme WhatsApp Bot'}, 200


@webhook_bp.route('/', methods=['GET'])
def inicio():
    """Página principal con información básica."""
    return (
        '<h1>FideliPyme</h1>'
        '<p>Sistema de Fidelización para PyMES</p>'
        '<p>Bot de WhatsApp activo.</p>'
        '<p><a href="/health">Estado del servicio</a></p>'
    ), 200
