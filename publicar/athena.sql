-- Cerebro Orlando · el lago en S3 consultado con SQL (Amazon Athena)
-- Reemplazar <BUCKET> por el nombre del bucket (el mismo que se usó en publicar/subir_s3.py).
-- Las tablas usan «proyección de particiones»: cada fecha nueva que suba subir_s3.py aparece sola, sin MSCK REPAIR.
-- Las mismas consultas se probaron en local con DuckDB sobre los mismos archivos: publicar/probar_sql.py

CREATE DATABASE IF NOT EXISTS cerebro_orlando;

-- Zona de consumo: una fila por cifra de cada foto del lago
CREATE EXTERNAL TABLE IF NOT EXISTS cerebro_orlando.cifras (
  tema string, clave string, valor double, unidad string, vigencia string, fuente string)
PARTITIONED BY (fecha string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<BUCKET>/consumo/cifras/'
TBLPROPERTIES ('projection.enabled'='true', 'projection.fecha.type'='date', 'projection.fecha.format'='yyyy-MM-dd',
               'projection.fecha.range'='2026-10-01,NOW', 'projection.fecha.interval'='1', 'projection.fecha.interval.unit'='DAYS',
               'storage.location.template'='s3://<BUCKET>/consumo/cifras/fecha=${fecha}/');

-- Zona de consumo: una fila por punto de cada serie (meses, años, barrios…)
CREATE EXTERNAL TABLE IF NOT EXISTS cerebro_orlando.series (
  tema string, serie string, etiqueta string, valor double, unidad string, fuente string)
PARTITIONED BY (fecha string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<BUCKET>/consumo/series/'
TBLPROPERTIES ('projection.enabled'='true', 'projection.fecha.type'='date', 'projection.fecha.format'='yyyy-MM-dd',
               'projection.fecha.range'='2026-10-01,NOW', 'projection.fecha.interval'='1', 'projection.fecha.interval.unit'='DAYS',
               'storage.location.template'='s3://<BUCKET>/consumo/series/fecha=${fecha}/');

-- Catálogo: el manifiesto de la zona cruda (una fila por respuesta guardada)
CREATE EXTERNAL TABLE IF NOT EXISTS cerebro_orlando.manifiesto (
  fecha string, sitio string, url string, tema string, como string, formato string, estado string, archivo string,
  bytes_original bigint, bytes_guardado bigint, sha256_original string, sha256_guardado string, retirado map<string,int>)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<BUCKET>/catalogo/manifiesto_crudo/';

-- Catálogo: las fuentes en uso
CREATE EXTERNAL TABLE IF NOT EXISTS cerebro_orlando.fuentes (
  id string, ficha_excel string, nombre string, entidad string, licencia string, personas string, proteccion string, uso string, nota string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<BUCKET>/catalogo/fuentes/';

-- Vista: todo lo que está por barrio (las series cuyo nombre dice «barrio»)
CREATE OR REPLACE VIEW cerebro_orlando.por_barrio AS
SELECT fecha, tema, serie, etiqueta AS barrio, valor, unidad, fuente FROM cerebro_orlando.series WHERE serie LIKE '%barrio%';

-- ===== Consultas de ejemplo (las mismas de probar_sql.py) =====

-- 1. ¿Qué cifras cambiaron entre las dos fotos del lago?
SELECT a.tema, a.clave, a.valor AS antes, b.valor AS ahora, a.vigencia AS vigencia_antes, b.vigencia AS vigencia_ahora
FROM cerebro_orlando.cifras a JOIN cerebro_orlando.cifras b ON a.tema = b.tema AND a.clave = b.clave
WHERE a.fecha = '2026-10-26' AND b.fecha = '2026-11-02' AND (a.valor <> b.valor OR a.vigencia <> b.vigencia)
ORDER BY a.tema, a.clave;

-- 2. Los 10 barrios con más casos de policía en 2025 (última foto)
SELECT barrio, valor AS casos FROM cerebro_orlando.por_barrio
WHERE fecha = '2026-11-02' AND serie = 'delitos_barrio_2025' ORDER BY casos DESC LIMIT 10;

-- 3. De qué sitios sale cada tema y cuánto pesó lo que respondieron
SELECT tema, sitio, count(*) AS respuestas, round(sum(bytes_original) / 1e6, 2) AS mb
FROM cerebro_orlando.manifiesto WHERE fecha = '2026-11-02' GROUP BY tema, sitio ORDER BY tema, sitio;

-- 4. Qué se retiró por privacidad antes de guardar
SELECT fecha, url, retirado FROM cerebro_orlando.manifiesto WHERE cardinality(retirado) > 0 ORDER BY fecha, url;

-- 5. Cada cifra con su fuente y licencia
SELECT c.tema, c.clave, c.valor, c.unidad, f.entidad, f.licencia
FROM cerebro_orlando.cifras c JOIN cerebro_orlando.fuentes f ON c.fuente = f.id
WHERE c.fecha = '2026-11-02' ORDER BY c.tema, c.clave;
