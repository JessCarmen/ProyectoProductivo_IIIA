-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CREACIÓN DE ESQUEMAS
-- ============================================================

-- ------------------------------------------------------------
-- META
-- Metadatos, configuración, auditoría y control del pipeline
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS meta;


-- ------------------------------------------------------------
-- BRONZE
-- Datos RAW recibidos desde la fuente original
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS bronze;


-- ------------------------------------------------------------
-- SILVER
-- Datos tipificados, validados y estructurados
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS silver;


-- ------------------------------------------------------------
-- GOLD
-- Datos preparados para analítica, ML y scoring
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS gold;