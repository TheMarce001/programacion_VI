-- =====================================================================
-- Esquema de la base de datos de AccountStore Escritorio (SQLite)
-- Se ejecuta cada vez que inicia el programa. "IF NOT EXISTS" hace que
-- las tablas se creen solo la primera vez: los datos existentes no se borran.
-- =====================================================================

-- Personas que usan el sistema (el dueño y sus colaboradores).
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT    NOT NULL UNIQUE,
    nombre      TEXT    NOT NULL,
    rol         TEXT    NOT NULL CHECK (rol IN ('ADMIN', 'SUPERVISOR', 'COBRANZA')),
    clave_hash  TEXT    NOT NULL,          -- hash PBKDF2 de la contraseña (nunca la contraseña)
    clave_sal   TEXT    NOT NULL,          -- sal aleatoria, distinta para cada usuario
    activo      INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- Plataformas que se venden (Netflix, Disney+, ...).
CREATE TABLE IF NOT EXISTS servicios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE COLLATE NOCASE,   -- "netflix" = "Netflix" (no se repite)
    capacidad       INTEGER NOT NULL CHECK (capacidad > 0),       -- perfiles por cuenta
    precio_mensual  INTEGER NOT NULL CHECK (precio_mensual > 0)   -- Gs. por perfil y por mes
);

-- Cada cuenta (correo) de una plataforma, que se comparte entre varios clientes.
CREATE TABLE IF NOT EXISTS cuentas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    servicio_id  INTEGER NOT NULL REFERENCES servicios (id) ON DELETE RESTRICT,
    correo       TEXT    NOT NULL,
    UNIQUE (servicio_id, correo)           -- la misma cuenta no se registra dos veces
);

-- Clientes que compran perfiles.
CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL CHECK (length(trim(nombre)) >= 3),
    telefono  TEXT    NOT NULL UNIQUE      -- el mismo cliente no se carga dos veces
                      CHECK (telefono GLOB '+[0-9]*'),   -- formato internacional: +595981123456
    correo    TEXT
);

-- Perfiles de una cuenta vendidos a un cliente durante un período.
CREATE TABLE IF NOT EXISTS suscripciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id    INTEGER NOT NULL REFERENCES clientes (id) ON DELETE RESTRICT,
    cuenta_id     INTEGER NOT NULL REFERENCES cuentas (id)  ON DELETE RESTRICT,
    perfiles      INTEGER NOT NULL CHECK (perfiles >= 1),
    fecha_inicio  TEXT    NOT NULL,        -- formato AAAA-MM-DD
    vencimiento   TEXT    NOT NULL,        -- formato AAAA-MM-DD
    estado        TEXT    NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'BAJA')),
    fecha_baja    TEXT,
    CHECK (vencimiento > fecha_inicio)
);

-- Cada cobro: la venta inicial y cada renovación.
CREATE TABLE IF NOT EXISTS pagos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    suscripcion_id  INTEGER NOT NULL REFERENCES suscripciones (id) ON DELETE RESTRICT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios (id)      ON DELETE RESTRICT,
    fecha           TEXT    NOT NULL,
    concepto        TEXT    NOT NULL CHECK (concepto IN ('VENTA', 'RENOVACION')),
    meses           INTEGER NOT NULL CHECK (meses BETWEEN 1 AND 12),
    monto           INTEGER NOT NULL CHECK (monto > 0)
);
