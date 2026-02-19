-- ============================================
-- FideliPyme - Script de configuración de base de datos
-- Ejecutar en el SQL Editor de Supabase
-- ============================================

-- 1. Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(30) UNIQUE NOT NULL,
    puntos INTEGER DEFAULT 0,
    nivel VARCHAR(20) DEFAULT 'Bronce',
    codigo_qr TEXT,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabla de transacciones
CREATE TABLE IF NOT EXISTS transacciones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,         -- 'compra', 'canje', 'bienvenida'
    monto DECIMAL(10,2) DEFAULT 0,
    puntos INTEGER NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla de premios
CREATE TABLE IF NOT EXISTS premios (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    costo_puntos INTEGER NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- 4. Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_clientes_telefono ON clientes(telefono);
CREATE INDEX IF NOT EXISTS idx_transacciones_cliente ON transacciones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON transacciones(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_premios_activo ON premios(activo);

-- 5. Datos iniciales: catálogo de premios
INSERT INTO premios (nombre, costo_puntos, descripcion, activo) VALUES
    ('Café Gratis', 50, 'Un café de la casa totalmente gratis', true),
    ('10% Descuento', 100, '10% de descuento en tu próxima compra', true),
    ('Postre Gratis', 150, 'Un postre de la casa totalmente gratis', true),
    ('2x1 Bebidas', 200, '2x1 en todas las bebidas', true),
    ('Cena para 2', 500, 'Una cena completa para 2 personas', true);

-- 6. Habilitar Row Level Security (RLS) - opcional
-- Descomenta las siguientes líneas si deseas habilitar RLS:
-- ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transacciones ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE premios ENABLE ROW LEVEL SECURITY;

-- Verificar que las tablas se crearon correctamente
SELECT 'clientes' AS tabla, COUNT(*) AS registros FROM clientes
UNION ALL
SELECT 'transacciones', COUNT(*) FROM transacciones
UNION ALL
SELECT 'premios', COUNT(*) FROM premios;
