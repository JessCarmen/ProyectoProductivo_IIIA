-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA META: CONTROL, TRAZABILIDAD Y AUDITORÍA
-- ============================================================


-- ============================================================
-- 1. CONFIGURACIÓN DEL PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_config (
    id_config BIGSERIAL PRIMARY KEY,

    nombre_tabla VARCHAR(150) NOT NULL,

    esquema_origen VARCHAR(50),
    esquema_destino VARCHAR(50),

    ruta_archivo TEXT,

    tipo_carga VARCHAR(20) NOT NULL DEFAULT 'FULL'
        CHECK (tipo_carga IN ('FULL', 'DELTA')),

    campo_delta VARCHAR(100),

    ultima_fecha_delta TIMESTAMP,

    procedimiento_sp VARCHAR(200),

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    orden_ejecucion INTEGER,

    descripcion TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. LOG DE EJECUCIONES DEL PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_run_log (
    id_run BIGSERIAL PRIMARY KEY,

    id_config BIGINT REFERENCES meta.pipeline_config(id_config),

    nombre_proceso VARCHAR(150) NOT NULL,

    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_fin TIMESTAMP,

    estado VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
        CHECK (estado IN ('RUNNING', 'SUCCESS', 'WARNING', 'ERROR')),

    registros_leidos BIGINT DEFAULT 0,

    registros_insertados BIGINT DEFAULT 0,

    registros_actualizados BIGINT DEFAULT 0,

    registros_rechazados BIGINT DEFAULT 0,

    mensaje TEXT,

    error_detalle TEXT,

    ejecutado_por VARCHAR(150),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. LOG DE ERRORES
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_error_log (
    id_error BIGSERIAL PRIMARY KEY,

    id_run BIGINT REFERENCES meta.pipeline_run_log(id_run),

    nombre_proceso VARCHAR(150),

    nombre_tabla VARCHAR(150),

    registro_id VARCHAR(150),

    record_json JSONB,

    tipo_error VARCHAR(100),

    mensaje_error TEXT NOT NULL,

    fecha_error TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ejecutado_por VARCHAR(150)
);


-- ============================================================
-- 4. LOG DE CALIDAD DE DATOS
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.data_quality_log (
    id_quality BIGSERIAL PRIMARY KEY,

    id_run BIGINT REFERENCES meta.pipeline_run_log(id_run),

    esquema VARCHAR(50),

    nombre_tabla VARCHAR(150),

    regla_calidad VARCHAR(200) NOT NULL,

    descripcion TEXT,

    registros_evaluados BIGINT DEFAULT 0,

    registros_ok BIGINT DEFAULT 0,

    registros_error BIGINT DEFAULT 0,

    porcentaje_calidad NUMERIC(6,3),

    estado VARCHAR(20)
        CHECK (estado IN ('OK', 'WARNING', 'ERROR')),

    fecha_ejecucion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. REGISTRO DE MODELOS
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.model_registry (
    id_modelo BIGSERIAL PRIMARY KEY,

    nombre_modelo VARCHAR(150) NOT NULL,

    version VARCHAR(50) NOT NULL,

    algoritmo VARCHAR(100),

    objetivo VARCHAR(200),

    variables_usadas JSONB,

    metricas JSONB,

    ruta_modelo TEXT,

    estado VARCHAR(30) DEFAULT 'EXPERIMENTAL'
        CHECK (
            estado IN (
                'EXPERIMENTAL',
                'VALIDATED',
                'PRODUCTION',
                'RETIRED'
            )
        ),

    fecha_entrenamiento TIMESTAMP,

    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    observaciones TEXT
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_pipeline_config_activo
    ON meta.pipeline_config(activo);

CREATE INDEX IF NOT EXISTS idx_pipeline_config_orden
    ON meta.pipeline_config(orden_ejecucion);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_log_estado
    ON meta.pipeline_run_log(estado);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_log_fecha
    ON meta.pipeline_run_log(fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_pipeline_error_log_run
    ON meta.pipeline_error_log(id_run);

CREATE INDEX IF NOT EXISTS idx_data_quality_log_run
    ON meta.data_quality_log(id_run);

CREATE INDEX IF NOT EXISTS idx_model_registry_nombre
    ON meta.model_registry(nombre_modelo);