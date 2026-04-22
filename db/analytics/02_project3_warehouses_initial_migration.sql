-- =====================================================
-- Project #3: Initial migration of warehouse dictionary
-- Source: oltp.warehouses_current
-- Target: analytics.warehouses
--
-- Важно:
-- - запрос предполагает доступ к OLTP данным через схему oltp
-- - warehouse_id должен совпадать с id в OLTP
-- - геометрия из OLTP преобразуется в plain lat/lon
-- - загрузка cities ниже требует наличия колонки city_name в oltp.warehouses_current
--   (если city_name отсутствует, этот блок нужно заменить на источник названий городов)
-- =====================================================

INSERT INTO analytics.cities (city_id, name)
SELECT DISTINCT city_id, city_name
FROM oltp.warehouses_current
ON CONFLICT (city_id) DO NOTHING;

INSERT INTO analytics.warehouses (
    warehouse_id,
    name,
    city_id,
    warehouse_type_id,
    lat,
    lon
)
SELECT
    id,
    name,
    city_id,
    warehouse_type_id,
    ST_Y(location),
    ST_X(location)
FROM oltp.warehouses_current
ON CONFLICT (warehouse_id) DO NOTHING;
