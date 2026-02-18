"""
Handler principal de mensajes de WhatsApp.
Gestiona el flujo conversacional: registro, menú, consultas y canjes.
"""
from app.services.cliente_service import (
    buscar_cliente_por_telefono,
    registrar_cliente,
    obtener_info_cliente,
)
from app.services.puntos_service import (
    acumular_puntos,
    obtener_historial,
    formatear_historial,
)
from app.services.premio_service import (
    obtener_catalogo,
    formatear_catalogo,
    canjear_premio,
)
from app.services.qr_service import generar_qr_cliente

# Estado temporal para flujos de conversación (registro y canje)
# Formato: { 'whatsapp:+521234567890': {'estado': 'esperando_nombre'} }
_estados_conversacion = {}


def obtener_menu() -> str:
    """Retorna el menú principal del bot."""
    return (
        "📱 *FideliPyme* - Programa de Lealtad\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Elige una opción:\n\n"
        "1️⃣ *Ver mis puntos* y nivel\n"
        "2️⃣ *Ver premios* disponibles\n"
        "3️⃣ *Canjear* un premio\n"
        "4️⃣ *Mi historial* de movimientos\n"
        "5️⃣ *Mi código QR*\n"
        "6️⃣ *Ayuda*\n\n"
        "Escribe el *número* de la opción deseada."
    )


def obtener_ayuda() -> str:
    """Retorna el mensaje de ayuda."""
    return (
        "ℹ️ *Ayuda - FideliPyme*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *¿Cómo funciona?*\n"
        "Por cada $10 MXN de compra ganas puntos.\n"
        "Acumula puntos y canjéalos por premios.\n\n"
        "🔹 *Niveles:*\n"
        "🥉 Bronce (0-99 pts) - x1\n"
        "🥈 Plata (100-249 pts) - x1.25\n"
        "🥇 Oro (250-499 pts) - x1.5\n"
        "👑 Platino (500+ pts) - x2\n\n"
        "🔹 *Multiplicador:*\n"
        "Entre mayor sea tu nivel, más puntos\n"
        "ganas por cada compra.\n\n"
        "🔹 *Comandos:*\n"
        "Escribe *menu* para ver las opciones.\n"
        "Escribe *puntos* para ver tu saldo.\n\n"
        "¿Dudas? Pregunta en el negocio. 😊"
    )


def procesar_mensaje(telefono: str, mensaje: str) -> str:
    """
    Procesa un mensaje entrante de WhatsApp y retorna la respuesta.

    Args:
        telefono: Número en formato 'whatsapp:+521234567890'
        mensaje: Texto del mensaje recibido

    Returns:
        Texto de respuesta para enviar al usuario
    """
    mensaje = mensaje.strip()

    # Verificar si hay un flujo de conversación pendiente
    estado = _estados_conversacion.get(telefono)

    if estado:
        return _procesar_estado(telefono, mensaje, estado)

    # Buscar si el cliente está registrado
    cliente = buscar_cliente_por_telefono(telefono)

    if not cliente:
        # Cliente nuevo: iniciar flujo de registro
        _estados_conversacion[telefono] = {'estado': 'esperando_nombre'}
        return (
            "👋 *¡Bienvenido a FideliPyme!*\n\n"
            "Nuestro programa de lealtad te premia\n"
            "por cada compra que realices.\n\n"
            "Para registrarte, escríbenos tu *nombre completo*:"
        )

    # Cliente registrado: procesar opción del menú
    return _procesar_opcion(telefono, mensaje, cliente)


def _procesar_estado(telefono: str, mensaje: str, estado: dict) -> str:
    """Procesa mensajes cuando hay un flujo activo (registro o canje)."""

    if estado['estado'] == 'esperando_nombre':
        # Validar que el nombre sea razonable
        nombre = mensaje.strip()
        if len(nombre) < 2 or len(nombre) > 100:
            return "Por favor, escribe un nombre válido (entre 2 y 100 caracteres):"

        if nombre.isdigit():
            return "Eso parece un número, no un nombre. 😅\nEscríbenos tu *nombre completo*:"

        # Registrar al cliente
        cliente = registrar_cliente(nombre, telefono)
        del _estados_conversacion[telefono]

        # Generar su código QR
        generar_qr_cliente(cliente['id'], telefono)

        return (
            f"🎉 *¡Registro exitoso!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 Nombre: *{cliente['nombre']}*\n"
            f"⭐ Puntos de bienvenida: *{cliente['puntos']}*\n"
            f"🏅 Nivel: *{cliente['nivel']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{obtener_menu()}"
        )

    elif estado['estado'] == 'esperando_canje':
        # Procesar selección de premio
        cliente = buscar_cliente_por_telefono(telefono)
        del _estados_conversacion[telefono]

        if not cliente:
            return "Error: no se encontró tu cuenta."

        try:
            indice = int(mensaje)
        except ValueError:
            return "❌ Opción inválida. Escribe el *número* del premio.\n\n" + obtener_menu()

        resultado = canjear_premio(cliente['id'], indice)
        return resultado['mensaje'] + "\n\n" + obtener_menu()

    # Estado desconocido: limpiar y mostrar menú
    del _estados_conversacion[telefono]
    return obtener_menu()


def _procesar_opcion(telefono: str, mensaje: str, cliente: dict) -> str:
    """Procesa la opción seleccionada del menú."""
    mensaje_lower = mensaje.lower().strip()

    # Opción 1: Ver puntos
    if mensaje_lower in ('1', 'puntos', 'saldo', 'ver puntos'):
        return obtener_info_cliente(telefono)

    # Opción 2: Ver premios
    if mensaje_lower in ('2', 'premios', 'catalogo', 'ver premios'):
        premios = obtener_catalogo()
        return formatear_catalogo(premios, cliente['puntos'])

    # Opción 3: Canjear premio
    if mensaje_lower in ('3', 'canjear'):
        premios = obtener_catalogo()
        catalogo = formatear_catalogo(premios, cliente['puntos'])
        _estados_conversacion[telefono] = {'estado': 'esperando_canje'}
        return catalogo + "\n\n✏️ Escribe el *número* del premio que deseas canjear:"

    # Opción 4: Historial
    if mensaje_lower in ('4', 'historial', 'mi historial', 'movimientos'):
        transacciones = obtener_historial(cliente['id'])
        return formatear_historial(cliente['nombre'], transacciones)

    # Opción 5: Código QR
    if mensaje_lower in ('5', 'qr', 'codigo qr', 'código qr', 'mi qr'):
        return (
            "📱 *Tu Código QR de FideliPyme*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 {cliente['nombre']}\n"
            f"🆔 ID: {cliente['id'][:8]}...\n\n"
            "Muestra este código en el negocio para\n"
            "acumular puntos en tus compras.\n\n"
            "Tu QR ha sido generado. Solicítalo\n"
            "en el negocio para que lo escaneen. ✅"
        )

    # Opción 6: Ayuda
    if mensaje_lower in ('6', 'ayuda', 'help', 'info'):
        return obtener_ayuda()

    # Comando especial: "menu" para volver al menú
    if mensaje_lower in ('menu', 'menú', 'inicio', 'hola', 'hi', 'hello'):
        return f"¡Hola, *{cliente['nombre']}*! 👋\n\n" + obtener_menu()

    # Mensaje no reconocido: mostrar menú
    return f"¡Hola, *{cliente['nombre']}*! 👋\n\n" + obtener_menu()
