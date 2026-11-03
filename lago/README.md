# Lago de datos del Cerebro Orlando

| Zona | Carpeta | Qué guarda |
|---|---|---|
| Cruda | `crudo/sitio=<servidor>/fecha=<AAAA-MM-DD>/` | Lo que respondió cada fuente, tal cual y comprimido (solo se retiran datos de personas al guardar) |
| Curada | `curado/tema=<tema>/fecha=<AAAA-MM-DD>/` | Un archivo por tema y foto con la forma del contrato, verificado, con el linaje a lo crudo |
| Consumo | `consumo/` | Tablas para SQL (una fila por cifra y por punto) y el archivo que lee el tablero |
| Referencia | `territorio/` | Capas geográficas en WGS84 |
| Catálogo | `catalogo/` | Manifiesto de lo crudo (`manifiesto_crudo/manifiesto.jsonl`), fuentes e inventario (`catalogo_lago.json`) |

Cómo se llena, se verifica, se reconstruye sin internet y vive en S3: ver el README de la raíz del repositorio.
