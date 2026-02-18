# FideliPyme

Sistema de fidelización de clientes para PyMES en México. Bot de WhatsApp que permite a tus clientes acumular puntos, subir de nivel y canjear premios.

## Características

- **Registro automático** de clientes nuevos con puntos de bienvenida
- **Acumulación de puntos** por cada compra ($10 MXN = 1 punto)
- **4 niveles** con multiplicadores de puntos:
  - Bronce (0-99 pts) - x1
  - Plata (100-249 pts) - x1.25
  - Oro (250-499 pts) - x1.5
  - Platino (500+ pts) - x2
- **Catálogo de premios** canjeables
- **Historial de transacciones**
- **Código QR** único por cliente
- **Menú interactivo** por WhatsApp

## Estructura del proyecto

```
FideliPyme/
├── app/
│   ├── __init__.py              # Factory de la app Flask
│   ├── config.py                # Configuración y constantes
│   ├── models/
│   │   └── database.py          # Conexión a Supabase
│   ├── services/
│   │   ├── cliente_service.py   # Gestión de clientes
│   │   ├── puntos_service.py    # Acumulación de puntos
│   │   ├── premio_service.py    # Catálogo y canje de premios
│   │   └── qr_service.py        # Generación de códigos QR
│   ├── handlers/
│   │   └── whatsapp_handler.py  # Lógica del bot de WhatsApp
│   └── routes/
│       └── webhook.py           # Endpoints Flask
├── scripts/
│   └── setup_database.sql       # SQL para crear tablas en Supabase
├── static/
│   └── qr_codes/                # QRs generados por cliente
├── .env.example                 # Plantilla de variables de entorno
├── requirements.txt             # Dependencias de Python
├── run.py                       # Punto de entrada
└── README.md
```

## Requisitos previos

- Python 3.10 o superior
- Cuenta de [Twilio](https://www.twilio.com/) con WhatsApp Sandbox activado
- Proyecto en [Supabase](https://supabase.com/)
- [ngrok](https://ngrok.com/) para pruebas locales

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/diegoemiliog/FideliPyme.git
cd FideliPyme
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```env
TWILIO_ACCOUNT_SID=tu_sid_aqui
TWILIO_AUTH_TOKEN=tu_token_aqui
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_key_aqui
```

### 5. Configurar la base de datos en Supabase

1. Ingresa a tu proyecto en [Supabase](https://supabase.com/dashboard)
2. Ve a **SQL Editor**
3. Copia y pega el contenido de `scripts/setup_database.sql`
4. Ejecuta el script
5. Verifica que se crearon las 3 tablas: `clientes`, `transacciones`, `premios`

**Importante:** Asegúrate de que Row Level Security (RLS) esté deshabilitado en las tablas, o configura las políticas correspondientes para permitir las operaciones del bot.

### 6. Configurar Twilio WhatsApp Sandbox

1. Ingresa a la [consola de Twilio](https://console.twilio.com/)
2. Ve a **Messaging** > **Try it out** > **Send a WhatsApp message**
3. Sigue las instrucciones para unirte al sandbox (envía el código que te dan al número de WhatsApp de Twilio)

### 7. Ejecutar el servidor

```bash
python run.py
```

El servidor iniciará en `http://localhost:5000`.

### 8. Exponer con ngrok

En otra terminal:

```bash
ngrok http 5000
```

ngrok generará una URL pública como `https://xxxx-xx-xx.ngrok-free.app`.

### 9. Configurar el webhook en Twilio

1. Copia la URL de ngrok
2. En la consola de Twilio, ve a la configuración del Sandbox de WhatsApp
3. En **"When a message comes in"**, pega: `https://tu-url-ngrok.ngrok-free.app/webhook`
4. Método: **POST**
5. Guarda los cambios

## Uso del bot

### Primer contacto (registro)

Cuando un cliente nuevo escribe al número de WhatsApp:
1. El bot le da la bienvenida y pide su nombre
2. El cliente escribe su nombre
3. Se registra automáticamente con **10 puntos de bienvenida**

### Menú principal

Después del registro, el bot muestra un menú interactivo:

| Opción | Acción |
|--------|--------|
| 1 | Ver puntos y nivel actual |
| 2 | Ver catálogo de premios |
| 3 | Canjear un premio |
| 4 | Ver historial de movimientos |
| 5 | Ver código QR |
| 6 | Ayuda |

### Catálogo de premios

| Premio | Costo |
|--------|-------|
| Café Gratis | 50 puntos |
| 10% Descuento | 100 puntos |
| Postre Gratis | 150 puntos |
| 2x1 Bebidas | 200 puntos |
| Cena para 2 | 500 puntos |

### Niveles y multiplicadores

| Nivel | Puntos | Multiplicador |
|-------|--------|---------------|
| Bronce | 0-99 | x1.0 |
| Plata | 100-249 | x1.25 |
| Oro | 250-499 | x1.5 |
| Platino | 500+ | x2.0 |

## Registro de compras (para el negocio)

Para registrar una compra y otorgar puntos al cliente, puedes hacer una petición POST:

```bash
curl -X POST http://localhost:5000/registrar-compra \
  -H "Content-Type: application/json" \
  -d '{"telefono": "whatsapp:+521234567890", "monto": 150.00}'
```

## Tecnologías utilizadas

- **Python 3** + **Flask** - Servidor web
- **Twilio** - Integración con WhatsApp
- **Supabase** - Base de datos PostgreSQL en la nube
- **qrcode** - Generación de códigos QR
- **ngrok** - Túnel para pruebas locales

## Solución de problemas

### El bot no responde
- Verifica que el servidor Flask esté corriendo
- Verifica que ngrok esté activo y la URL sea correcta en Twilio
- Revisa los logs del servidor

### Error de conexión a Supabase
- Verifica las credenciales en el archivo `.env`
- Asegúrate de que las tablas estén creadas
- Verifica que RLS esté deshabilitado o con políticas configuradas

### Error de Twilio
- Verifica que el Sandbox de WhatsApp esté activo
- Confirma que el número está unido al sandbox
- Revisa las credenciales de Twilio en `.env`
