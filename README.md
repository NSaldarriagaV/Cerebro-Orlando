# Cerebro Orlando

Sistema de información sobre Orlando, Florida, para el taller de datos de Tópicos de Sistemas de Información (EAFIT).
Responde siete preguntas con datos abiertos, ayuda a decidir (emprender, vivir, comprar o invertir, gobernar) y compara
Orlando con otras ciudades, sus seis distritos y sus barrios. Cada cifra trae su fuente, su vigencia y la fecha en que la
comprobamos.

**Publicado en https://cerebro-orlando.vercel.app** (el lago completo, en https://cerebro-orlando.vercel.app/lago/…; el
inventario está en `lago/catalogo/catalogo_lago.json`). **Se actualiza solo cada lunes en AWS** (EventBridge → Step
Functions → Lambda → S3 → Athena; ver «Actualización semanal en AWS»).

Réplica mejorada del lago del Cerebro Lima: un script por tema, un **lago de datos con tres zonas** (cruda, curada y de
consumo) y fotos con fecha, una verificación que sabe fallar y una vista publicada en Vercel. La ingesta, la verificación
y la vista usan solo la biblioteca estándar de Python 3.9 o superior: no hay nada que instalar ni llaves que pedir.
Opcionales: `boto3` para subir el lago a Amazon S3, `duckdb` para consultarlo con SQL en local y `openpyxl` para
exportar el Excel del catálogo.

**Las tres preguntas de la sustentación, en corto:**

- **¿De dónde jalamos los datos?** De 37 fuentes abiertas en 16 sitios (Datos abiertos y SIG de la Ciudad de Orlando,
  FRED, Census Reporter, FEMA, Servicio Meteorológico, NOAA, Wikimedia y Wikipedia, Indeed Hiring Lab en GitHub, Zillow,
  el Departamento de Transporte de Florida (FDOT), NHTSA y LYNX).
  Cada pedido queda en `lago/catalogo/manifiesto_crudo/manifiesto.jsonl` con su URL exacta, la fecha y su huella.
- **¿De dónde los sacó la IA?** La IA (Claude) no puso ninguna cifra: escribió los scripts y pidió esas mismas URL desde el
  navegador del equipo, porque su entorno no tenía salida a esos sitios. Desde el 3 de noviembre, además, una Lambda en
  AWS pide cada lunes las mismas URL directamente a las fuentes, con los mismos scripts. Las respuestas se guardaron tal cual en la zona
  cruda y los scripts las leyeron. `verificar.py` falla si una fuente no apunta a una respuesta cruda con la huella
  correcta, y `reconstruir.py --desde-crudo` rehace la zona curada sin internet y sale idéntica. La única excepción está
  en la bitácora (encargo 1): el primer borrador del catálogo de fuentes lo llenó de memoria y el equipo lo corrigió.
- **¿Dónde están guardados?** En `lago/`, con historial en este repositorio; publicado completo en Vercel junto a la
  página (`/lago/…`); y en un bucket privado de Amazon S3, `cerebro-orlando-lago-eafit` (us-east-1, cifrado y con
  versiones), donde Athena lo consulta con SQL (`publicar/athena.sql`). Cada lunes AWS le agrega una foto nueva, y la
  página lee la última a través de CloudFront (el bucket sigue privado).

## Las siete preguntas y de dónde salen

| Pregunta | Temas del lago | Fuentes (ficha del Excel) |
|---|---|---|
| ¿Cuánta gente vive aquí y cómo le va frente a condados parecidos? | `gente`, `censo` | Census y BEA vía FRED: población, ingreso mediano e ingreso por persona, pobreza, IPC (F14); American Community Survey por sector y por ciudad (F12, F78) |
| ¿Cómo se mueve la economía y cuánto cuesta vivir aquí? | `economia`, `empleo`, `vivienda`, `permisos` | BLS, FHFA, Realtor.com y Census vía FRED: desempleo, salarios, solicitudes de negocio, inventario y rebajas (F14); Zillow, arriendo y valor típicos (F41); Indeed Hiring Lab (F70); permisos de la ciudad (F79) |
| ¿Qué pasa en cada barrio, quién vive allí, qué tiene cerca y hacia dónde va? | `permisos`, `seguridad`, `codigo`, `negocios`, `territorio`, `censo`, `riesgo`, `servicios`, `planeacion` | Datos abiertos de Orlando (F79, F81, F83, F86, F88, F90, F93, F94, F96); SIG de la ciudad (F107); censo (F12, F78); FEMA (F108); Policía de Orlando (F106) |
| ¿Qué pasa con la seguridad y la convivencia? | `seguridad`, `codigo` | Policía de Orlando (F106); casos de código urbano (F83) |
| ¿Cuánto pesa el turismo? | `turismo`, `negocios`, `escucha` | BLS vía FRED (F14); licencias de negocio (F81) y de alquiler de corto plazo (F85); Wikipedia (F71) |
| ¿Qué clima hay hoy, cómo está cambiando y qué barrios están más expuestos? | `clima`, `clima_historico`, `riesgo` | National Weather Service (F57); NOAA NCEI (F58); FEMA, Índice Nacional de Riesgo (F108) |
| ¿Cómo se mueve la gente y qué tan seguras son las vías? | `trafico`, `transporte` | FDOT, tráfico promedio diario por vía (AADT) y su histórico (F25), dibujado como mapa de carreteras; NHTSA, choques mortales (FARS, F109); LYNX, horario y recorridos de los buses en GTFS (F21) |

Cada pregunta se compara «contra algo»: Tampa, Miami y Jacksonville (y Florida y EE. UU.) para las cifras del área y de
la ciudad; el año anterior para las tendencias; la mediana de los 125 barrios en cada ficha; los demás distritos.

## Cómo se corre

```
python3 reconstruir.py                           # pide todo a las fuentes, guarda una foto nueva con la fecha de hoy y verifica
python3 reconstruir.py --desde-crudo 2026-11-02  # rehace esa foto SIN internet, solo con la zona cruda (git diff debe salir vacío)
python3 verificacion/verificar.py                # con un solo FAIL no se publica
python3 verificacion/probar_verificador.py       # comprueba que la verificación sepa fallar
python3 publicar/consumo.py                      # zona de consumo (tablas para SQL) e inventario del lago
python3 vista/construir_vista.py                 # arma el tablero (publico/ para Vercel y vista/index.html); no construye si verificar falla
python3 publicar/probar_sql.py                   # consultas SQL de ejemplo sobre el lago, con DuckDB (pip install duckdb)
python3 publicar/subir_s3.py --bucket NOMBRE     # sube el lago a S3 (pip install boto3 y llaves de AWS; ver abajo)
python3 publicar/correr_athena.py --bucket NOMBRE  # crea las tablas en Athena y corre las 5 consultas de ejemplo
python3 verificacion/consistencia.py             # que una cifra diga lo mismo en todas las pestañas (verificar.py ya la corre)
python3 aws/crear_infra.py --bucket NOMBRE       # (en AWS CloudShell) monta o actualiza la actualización semanal
```

Los scripts de ingesta, uno por tema (cada uno dice arriba qué lee y qué escribe):

| Script | Qué trae |
|---|---|
| `pull_gente.py` | Población del condado, del área y de los condados pares; ingreso mediano, ingreso por persona y pobreza; ingreso real |
| `pull_censo.py` | Censo (ACS 5 años) por sector, estimado por barrio y por ciudad; índice de riesgo de FEMA por barrio (escribe `censo` y `riesgo`) |
| `pull_economia.py` | Desempleo de Orlando, Tampa, Miami, Jacksonville, Florida y EE. UU.; empleo total; salario por hora; solicitudes de negocio |
| `pull_empleo.py` | Índice de avisos de empleo de Indeed para Orlando y sus pares |
| `pull_vivienda.py` | Índice de precios, precio de lista, inventario, días, rebajas (Orlando y pares), viviendas autorizadas; Zillow (arriendo y valor típicos) |
| `pull_servicios.py` | Parques, colegios públicos y chárter, estaciones de SunRail y ciclovías por barrio (SIG de la ciudad) |
| `pull_planeacion.py` | Residentes y empleos 2017 y 2045, zonas con incentivos, solicitudes de planeación y anexiones por barrio |
| `pull_permisos.py` | Permisos de construcción por año y por barrio (cinco años) |
| `pull_seguridad.py` | Casos de la policía por año, por grupo (hurtos, violencia, drogas), por barrio y por tipo |
| `pull_codigo.py` | Casos de código urbano por año y por barrio; quejas ciudadanas; motivos |
| `pull_negocios.py` | Licencias de negocio vigentes por barrio (restaurantes, hospedajes, comercio, belleza, servicios, cuidado infantil, talleres), aperturas, categorías |
| `pull_turismo.py` | Empleo en ocio y hotelería y su peso en el empleo (Orlando y pares); alquileres de corto plazo con licencia |
| `pull_escucha.py` | Visitas al artículo de cada ciudad en Wikipedia en español y en inglés |
| `pull_clima.py` | Temperatura actual, alertas y pronóstico (cambia en cada corrida) |
| `pull_clima_historico.py` | Temperatura media y lluvia de cada año desde 1953 |
| `pull_territorio.py` | Límite de la ciudad, barrios, distritos de comisionados y lagos |

**Cómo se trajeron los datos de las dos fotos (26 oct y 2 nov de 2026).** El entorno donde trabajó la IA no tiene
salida a esas fuentes, así que el navegador del equipo pidió cada URL (las mismas que arman los scripts) y los scripts
corrieron contra esa captura sin cambiar una línea (`CEREBRO_CAPTURA=<carpeta>`, un archivo por URL). Cada respuesta
quedó en la zona cruda anotada como «navegador del equipo». La excepción es el archivo de Indeed, que está en GitHub y el
script lo pidió directo; el del 26 de octubre se recuperó del historial de GitHub (commit `4f4b784`, el vigente ese día).
`CEREBRO_FECHA_PRUEBA` fija la fecha de la foto. En un computador con internet, `reconstruir.py` pide todo directo.

En Windows se usa `python` o `py` en lugar de `python3`. Opcional: `set CONTACTO=correo-del-grupo@...` antes de
correr, porque el servicio del clima pide que el cliente se identifique.

## Qué hay en cada carpeta

| Carpeta | Qué guarda |
|---|---|
| `ingesta/` | Un script por tema. `comun.py` tiene lo compartido (contrato, consultas a Socrata, ArcGIS y FRED, supresión bajo el umbral, geometría); `crudo.py` guarda y relee la zona cruda; `privacidad.py` tiene las reglas de datos de personas que usan la ingesta y la verificación. |
| `lago/` | El lago de datos (ver abajo). Va completo al repositorio. |
| `catalogo/` | `fuentes_lago.json`: las 37 fuentes que alimentan el lago, con su licencia tal como aparece y su nivel de protección. `catalogo_completo.json`, `diccionario.json` y `bitacora_ia.json`: exportados del Excel por `exportar_catalogo.py`. |
| `verificacion/` | `verificar.py`, `consistencia.py` (la misma cifra en todas las pestañas), la prueba de que saben fallar y `informe_consistencia.md`. |
| `aws/` | La actualización semanal: `lambda_cerebro.py`, `maquina.asl.json` (Step Functions) y `crear_infra.py` (lo monta todo). |
| `publicar/` | `consumo.py` (zona de consumo e inventario), `subir_s3.py` (lago → Amazon S3), `athena.sql` (tablas y consultas de ejemplo), `correr_athena.py` (las crea y las corre en Athena), `probar_sql.py` (las mismas consultas con DuckDB), `politica_iam.json` (permisos mínimos para subir) y `explorador.html` (la página que muestra el lago desde S3). |
| `vista/` | `plantilla.html`, `estilos.css`, `app.js` y `construir_vista.py`. |
| `publico/` | Lo que publica Vercel: `index.html` y `app.js`. Al construir (y en el build de Vercel) se copia `lago/` adentro. |
| `middleware.js` | La puerta con contraseña de la página en Vercel. |
| `entrega1/`, `entrega2/` | El diccionario de datos (Excel) tal como se entregó en cada corte. |

## El lago de datos

```
lago/
  crudo/sitio=<servidor>/fecha=<AAAA-MM-DD>/<nombre>-<huella>.<json|csv>.gz   lo que respondió cada fuente, tal cual
  curado/tema=<tema>/fecha=<AAAA-MM-DD>/<tema>.json                          un archivo por tema y foto, verificado
  territorio/*.geojson                                                       capas de referencia (barrios, distritos, límite, lagos, vías con su tráfico y recorridos de bus)
  consumo/cifras/fecha=<…>/cifras.jsonl.gz                                   una fila por cifra (para SQL)
  consumo/series/fecha=<…>/series.jsonl.gz                                   una fila por punto de cada serie (para SQL)
  consumo/tablero/tablero.json                                               lo que lee el tablero publicado
  catalogo/manifiesto_crudo/manifiesto.jsonl                                 una línea por respuesta: URL, fecha, huellas, cómo se pidió, qué se retiró
  catalogo/fuentes/fuentes.jsonl                                             las fuentes en uso, con licencia y protección
  catalogo/catalogo_lago.json                                                inventario: cada archivo con su zona, fecha, tamaño y huella
```

- **Zona cruda.** `ingesta/crudo.py` guarda cada respuesta antes de que el script la toque, comprimida y con dos
  huellas SHA-256: la de lo que llegó y la de lo guardado. Antes de guardar se retiran los datos de personas que traen
  algunas respuestas (las fichas del portal de Orlando traen el nombre de quien publicó el conjunto y «valores de
  muestra» de cada columna, con correos de personas; la capa de distritos trae el nombre de cada comisionado). El
  manifiesto dice qué se retiró. Si después de retirar todavía aparece un correo o un teléfono, la respuesta no se
  guarda y queda «bloqueada».
- **Zona curada.** La forma del contrato (`tema`, `probado`, `fuentes`, `cifras`, `series`), y cada fuente con la lista
  `crudo` de respuestas de las que salió: ese es el **linaje**. Cada foto queda en su carpeta de fecha; nada se sobrescribe.
- **Zona de consumo.** Tablas planas para consultar con SQL y el archivo del tablero.
- **Particiones** `clave=valor` al estilo Hive: Athena, DuckDB o Spark las leen como columnas sin configurar nada.
- **Reproducible:** `reconstruir.py --desde-crudo <fecha>` borra la zona curada de esa fecha y la rehace leyendo solo la
  zona cruda; sale idéntica byte a byte (probado con las dos fotos). Todo lo que depende del día usa la fecha de la foto,
  no el reloj (`comun.fecha_prueba()`).
- En el repositorio pesa ~33 MB (dos fotos), casi todo zona cruda: el archivo de Indeed (63 MB sin comprimir) es casi la
  mitad. En S3 crece con cada foto semanal.

## Dónde viven los datos

| Lugar | Qué hay | Para qué |
|---|---|---|
| Este repositorio (GitHub) | Todo `lago/` | Historial: cada foto nueva es un cambio con fecha y autor; cualquiera puede clonar y reconstruir |
| Vercel | La página y una copia de `lago/` en `/lago/…`, detrás de una contraseña | Ver y descargar; es el respaldo si CloudFront no responde |
| Amazon S3 | El lago maestro: el mismo árbol en el bucket privado `cerebro-orlando-lago-eafit` (us-east-1), cifrado y con versionado, más una foto nueva cada lunes | Nube de verdad: Athena consulta las tablas con SQL (base `cerebro_orlando`) |
| CloudFront | Una puerta de solo lectura a las zonas del lago (`publicar/nube.json` tiene la dirección) | La página lee de ahí la última foto; `_athena/`, `_trabajo/` y todo lo demás responden 403. Para ver el lago: [explorador del lago](https://d1uzvgzpbvgblk.cloudfront.net/catalogo/explorador.html), una página guardada en el bucket que lista cada archivo |

### Publicar en Vercel

`vercel.json` ya trae todo: sin framework, sin instalación, el build copia `lago/` dentro de `publico/` y se publica
`publico/`. Pasos: en vercel.com, *Add New → Project → Import* este repositorio (lo importa quien tenga acceso al repo en
GitHub) y *Deploy*, sin cambiar nada. Cada push a la rama vuelve a publicar. Plan Hobby: gratis para uso personal y no
comercial; 100 GB de transferencia al mes (el sitio pesa ~35 MB). Sin GitHub: `npx vercel deploy --prod` desde la raíz.

**Contraseña de entrada.** `middleware.js` (Routing Middleware de Vercel) pide una contraseña antes de servir la página o
su copia del lago; al acertar deja una cookie por 30 días (`/salir` la borra). El repositorio no guarda la contraseña, solo
SHA-256 de su derivación PBKDF2; la contraseña la tiene el equipo. Siguen abiertos a propósito este repositorio y la puerta
de CloudFront: son datos abiertos y cualquiera puede verificarlos. `package.json` existe solo para que Vercel trate
`middleware.js` como módulo; no hay dependencias.

### Subir el lago a Amazon S3 y consultarlo con Athena

Ya está hecho en la cuenta de AWS de Mateo Villada (2026-11-02): bucket `cerebro-orlando-lago-eafit` en us-east-1, 264 archivos
(31 MB), base de Athena `cerebro_orlando` con sus 4 tablas y la vista; las 5 consultas de ejemplo corrieron bien. Para
volver a subir después de una foto nueva, o para montarlo en otra cuenta:

1. Lo más fácil: abrir **AWS CloudShell** en la consola (ya trae Python, boto3 y las credenciales de quien inició
   sesión; no hay llaves que copiar) y `git clone` este repositorio. Desde un computador propio: un usuario con la
   política de `publicar/politica_iam.json`, `pip install boto3` y `aws configure` (las llaves nunca van al repo).
2. (Solo fuera de CloudShell) Revisar la región: el bucket está en us-east-1.
3. `python publicar/subir_s3.py --bucket cerebro-orlando-lago-eafit --crear`: crea el bucket privado (acceso público
   bloqueado, cifrado SSE-S3, versionado) y sube el lago. Las siguientes veces, sin `--crear`: sube solo lo nuevo y
   **nunca pisa** lo que ya está (el manifiesto se une; lo derivado lo rehace la próxima ejecución en AWS).
4. `python publicar/correr_athena.py --bucket cerebro-orlando-lago-eafit` (o pegar en el editor de Athena el archivo
   `publicar/athena_<bucket>.sql` que deja el paso 3): crea la base
   `cerebro_orlando`, las tablas `cifras`, `series`, `manifiesto` y `fuentes`, la vista `por_barrio` y cinco consultas
   de ejemplo (qué cambió entre fotos, barrios con más casos, de qué sitios sale cada tema, qué se retiró por privacidad,
   cada cifra con su licencia).
5. Sin nube: `python publicar/probar_sql.py` corre las mismas consultas con DuckDB sobre los archivos locales.

Costo: el lago pesa ~31 MB; S3 cobra centavos al año y Athena cobra por datos leídos (las 5 consultas leen menos de 1 MB).
Los resultados de Athena quedan en `s3://<bucket>/_athena/` y se borran solos a los 7 días.
El bucket es privado: para que otro integrante lo vea, se le crea un usuario de IAM con la política de
`publicar/politica_iam.json`; lo público es la puerta de CloudFront (solo las zonas del lago) y la copia de Vercel.

### Actualización semanal en AWS (EventBridge → Step Functions)

Montada el 3 nov 2026 en la cuenta de AWS de Mateo Villada (us-east-1) con `python3 aws/crear_infra.py --bucket
cerebro-orlando-lago-eafit`, desde CloudShell. Todos los lunes a las 6:00 (hora de Bogotá):

```
EventBridge Scheduler «cerebro-orlando-lunes»
  └─▶ Step Functions «cerebro-orlando-semanal»
        Planear ─▶ Traer de las fuentes (Map: un script de ingesta por tema, 4 a la vez, cada uno en la Lambda)
              ─▶ Verificar (verificar.py sobre el lago + lo traído) ─▶ ¿0 fallos?
                     no ─▶ «No se publica» (falla la ejecución; el lago y la página quedan como estaban)
                     sí ─▶ Publicar (consumo, tablero, sube a S3 solo lo nuevo, invalida CloudFront)
                           ─▶ Contar en Athena las cifras de la foto nueva ─▶ ¿más de 0? ─▶ Listo
```

- **Lambda** `cerebro-orlando-actualizar` (Python 3.12, 2 GB, hasta 15 min): lleva el código del repositorio y baja el
  lago del bucket en cada paso. Lo que trae cada script queda en `_trabajo/<ejecución>/` (se borra a los 3 días).
- **Primera ejecución** (3 nov, a mano): 16 temas traídos desde AWS sin errores, 1.572 comprobaciones y 0 fallos, 135
  archivos subidos y 148 cifras de la foto nueva vistas en Athena, en 3 minutos.
- **La página** pide primero `consumo/tablero/tablero.json` a CloudFront; lo usa solo si salió del mismo código que la
  página (`version_vista`) y, si no, usa su copia de Vercel.
- **Después de cambiar el código** (push a `main`): en CloudShell, `git pull` y `python3 aws/crear_infra.py --bucket
  cerebro-orlando-lago-eafit --solo-codigo` (con `--correr` lanza una ejecución en el momento).
- **Pausar**: `aws scheduler update-schedule …` con `--state DISABLED`, o en la consola: *EventBridge → Schedules*.
- **Costo:** una ejecución por semana cabe en la capa gratuita de Lambda, Step Functions, Scheduler y CloudFront; S3 y
  Athena cuestan centavos.
- Tres roles de IAM, uno por pieza, con lo mínimo: la Lambda solo lee y escribe en el bucket; Step Functions solo invoca
  la Lambda y consulta Athena; el horario solo puede arrancar la máquina.

`.github/workflows/actualizar-lago.yml` hace lo mismo desde los servidores de GitHub, en modo manual. Queda como
alternativa.

## Cómo cuidamos a las personas

Seis fuentes traen datos de personas: permisos (propietario, contratista), casos de la policía (número de caso, fecha,
punto exacto), código urbano (nombres en el caso), licencias de negocio (dueño, teléfono), alquileres de corto plazo
(nombre, correo) y solicitudes de planeación (solicitante, comentarios). Su nivel de protección en `fuentes_lago.json` es **«solo agregados»**:

- Nada de eso se descarga. Los servidores de la ciudad devuelven conteos por barrio y por año (`$group` en Socrata,
  `outStatistics` en ArcGIS); el lago nunca tiene una fila por persona.
- Un barrio con menos de 5 casos en el año no se publica (`umbral_minimo_por_barrio`), y los barrios suprimidos no se
  nombran en ninguna parte. En la vista salen en gris, igual que los que no tuvieron ninguno.
- De la policía no entran Baker Act (salud mental), suicidios, muertes, personas desaparecidas, custodia ni órdenes de
  alejamiento: no son delitos y señalarían a personas vulnerables.
- `verificar.py` falla si aparece un campo personal (nombres, número de caso, dirección, teléfono, correo), una categoría
  excluida, una celda por barrio bajo el umbral o un lago vacío (una verificación que no revisa nada no puede pasar).
  `probar_verificador.py` comprueba que esas fallas se detecten.
- El censo es agregado por diseño, pero un porcentaje de un barrio con muy poca gente se acerca a describir hogares: los
  barrios con menos de 200 habitantes estimados no publican porcentajes ni medianas, y `verificar.py` lo exige.
- De los colegios solo se pide el tipo: el servidor trae nombre del director y teléfono, y no se descargan.
- La zona cruda guarda respuestas enteras, así que tiene su propio filtro (`ingesta/privacidad.py`): antes de guardar
  se retiran los campos con nombre de dato personal y los «valores de muestra» de las fichas del portal (ahí aparecían
  correos de personas que registraron alquileres de corto plazo); `verificar.py` revisa cada respuesta guardada.

- **Choques mortales (FARS).** Cada registro de NHTSA es un choque con muertos, con fecha, hora y punto. No se baja
  ninguno: al servidor solo se le piden conteos por año y por vía, y una vía con menos de 5 choques en cinco años no se
  publica (`umbral_minimo_por_via`).
- **Buses (GTFS de LYNX).** Son horarios publicados, sin personas. El ZIP se guarda entero en la zona cruda y
  `verificar.py` revisa el texto de cada archivo de adentro; el único contacto permitido es el de atención al público de
  la empresa (`agency.txt`).

Las demás fuentes son **«abierto»**: series agregadas por área sin datos de personas.

**Población por barrio (estimada).** El censo publica por sector censal, no por barrio. `comun.reparto()` cubre la ciudad
con una rejilla de puntos cada 40 m (sin lagos) y reparte cada sector entre los barrios según los puntos que comparten (con 150 m los barrios más pequeños recibían tan pocos puntos que su población variaba hasta 44 %).
Los conteos se suman así; las medianas (ingreso, arriendo, edad) se promedian ponderando por población y se llaman
«aproximadas». Control: los barrios suman 314.042 habitantes frente a 319.758 oficiales (−1,8 %); `verificar.py` falla
si la diferencia pasa de 15 %. El índice de riesgo de FEMA y la proyección 2045 de la ciudad se llevan a barrios igual.

## La vista

Once secciones: resumen, decidir, comparar, gente, economía y vivienda, barrios, seguridad, turismo, clima, movilidad y
«datos y fuentes». Se publica de dos formas: `publico/` (Vercel; la página lee sus datos de la última foto en CloudFront o,
si no, de `lago/consumo/tablero/tablero.json`) y `vista/index.html` (un solo archivo con los datos adentro: se abre sin servidor).

**Diseño «señal y lago».** Overpass (derivada de la letra de las señales viales de EE. UU.) para títulos, cifras y
etiquetas; Atkinson Hyperlegible para el texto. Color solo en los datos: verde azulado de lago para Orlando, ámbar para
lo comparado, rojo y verde para peor y mejor. Superficies planas, sin etiquetas en mayúsculas encima de los títulos.
Contraste AA en los dos temas. Animación corta solo cuando responde a algo (cambio de pestaña, ficha de un barrio,
diálogos, avisos, presionar un botón); con «reducir movimiento» queda solo el cambio de opacidad. Los tokens están en
`:root` de `vista/estilos.css`.

- **Resumen:** un tablero por perfil con su dato principal; las siete respuestas y la casilla de los datos, con su cifra,
  su tendencia en palabras y su fuente; Orlando contra ciudades parecidas (seis medidas); las preguntas sin respuesta abierta; un mapa 3D que gira
  despacio, con recorrido guiado por seis barrios elegidos por los datos.
- **Decidir:** cuatro perfiles, cada uno con su regla escrita a la vista («Cómo se calcula») y lo que no sabe.
  *Emprender* ordena barrios para cinco tipos de negocio por gente cerca, competencia por cada 10.000 personas, ingreso,
  crecimiento a 2045 y seguridad, con pesos movibles y filtro de incentivos. *Vivir* filtra por arriendo (la mediana del
  censo llevada a hoy con Zillow) y ordena por seguridad, tranquilidad, parques, colegios, movilidad sin carro, riesgo de
  inundación e idioma; dice cuánto hay que ganar para ese arriendo. *Comprar o invertir* cuenta cuatro señales de mercado
  (precio, días, inventario, rebajas), años de ingreso para comprar y rentabilidad bruta frente a los pares, y barrios para
  mirar. *Gobernar* resume la ciudad o un distrito frente a la ciudad y levanta alertas por barrio con seis reglas
  escritas (casos que suben, arriendo que ahoga, sin carro y sin alternativas, gente sin parque, riesgo y vulnerabilidad,
  crecimiento que presiona). Nada de esto es asesoría financiera ni legal.
- **Comparar:** Orlando contra Tampa, Miami, Jacksonville, Florida o EE. UU. en 20 medidas con su ámbito (ciudad, área o
  condado) y un marcador de mejor/peor; los seis distritos lado a lado (verde mejor, rojo peor); hasta tres barrios con la
  mediana de la ciudad marcada.
- **Barrios:** mapa 3D (MapLibre GL desde cdnjs, sin teselas ni llaves: solo las capas del lago) con 21 lentes en
  seis grupos (qué pasa, quién vive, qué tiene cerca, riesgo, hacia dónde va, índice), total, por km² o por 1.000
  habitantes, barra de años, buscador, ficha por barrio con 31 medidas agrupadas y la mediana de la ciudad, ranking, un **índice de atención** con
  pesos movibles (y cuántos barrios siguen arriba con cualquier enfoque), dispersión entre dos medidas con ρ de Spearman
  y la tabla completa. Si el navegador no tiene WebGL, el mapa cae a SVG plano.
- **Gente, economía, turismo y clima** suman ingreso por persona e ingreso real, ciudad contra ciudad con el censo,
  «quién vive en cada barrio», salarios, arriendo típico, mercado de compradores o vendedores, solicitudes de negocio,
  turismo e interés en inglés frente a los pares y el mapa de riesgo de FEMA por barrio.
- **Modo presentación:** once láminas con las respuestas, decidir y comparar, para exponer (flechas, Esc para salir).
- Cada cifra abre su ficha de trazabilidad: fuente, licencia, enlace exacto consultado, fecha de prueba y campo del
  diccionario. Lo que la vista calcula (distrito de cada barrio, área, «por km²», «por 1.000 habitantes», el índice, los
  puntajes de Decidir) está marcado como «derivado».
- **Datos y fuentes:** las tres preguntas (de dónde salen, qué hizo la IA, dónde viven); el recorrido de los datos
  (diagrama de flujo sitio → tema del lago → pestaña: al tocar un nodo se ven sus archivos); el lago zona por zona;
  «sigue un número» (del tablero a la fila de consumo, al archivo curado, a la respuesta cruda y a la fuente, paso a paso);
  qué cambió entre una foto y la siguiente; un explorador de las respuestas crudas con filtros y vista previa (en la
  versión publicada abre el archivo del lago y lo descomprime en el navegador); la bitácora de la IA; el catálogo y el
  diccionario.
- **Buscador** (botón «Buscar» o tecla `/`): barrios, pestañas, fuentes y números para rastrear. Cada barrio tiene un
  enlace directo (`#barrios/<id>`) que se copia desde su ficha.
- `python3 vista/construir_vista.py --sin-verificar` sirve solo para probar el diseño; la página lo dice en «Datos y fuentes».
- Desde la consola del navegador, `cerebro.B` tiene el modelo de barrios que usan todas las vistas.

## Lo que sigue pendiente

1. **Licencias de la ciudad.** Las fuentes del portal de Orlando y la capa de la policía «no declaran» licencia (la ficha
   del portal tiene el campo vacío). `verificar.py` lo marca con WARN. Antes de un uso fuera del curso, hay que leer los
   términos del portal.
2. **Realtor.com vía FRED** dice «Copyrighted: Citation Required»: se usa con la atribución visible en la vista.
3. **Zillow, el SIG de la ciudad, FDOT y LYNX** no traen texto de licencia (FDOT entrega sus capas «as is»): se citan
   junto a cada gráfico y quedan con WARN.
4. **Huecos declarados:** zonas inundables por predio (el servidor de FEMA no respondió; se usa el índice por sector),
   supermercados y farmacias por barrio (OpenStreetMap rechazó el navegador automatizado y no se saltó con espejos),
   PIB del área (descontinuado en FRED), solicitudes al 311 (no publicadas), turistas y pasajeros (solo en PDF), cargos y
   salarios de las ofertas (Indeed prohíbe extraerlas), arriendo de locales comerciales y calidad de los colegios.
5. **Estimaciones por barrio:** tienen margen de error (mayor en barrios pequeños). Sirven para comparar, no para citar un
   barrio al detalle; la vista lo dice en cada lugar donde aparecen.

## Cosas que cambian solas

- `clima.json` cambia en cada corrida (tiempo real): no entra en la prueba de reproducibilidad. La fecha de la
  observación se pasa a la hora de Orlando (llega en UTC).
- Zillow publica cada mes; el censo (ACS 5 años) y el índice de FEMA, una vez al año: al cambiar de edición cambian
  todas las estimaciones por barrio.
- Wikipedia suma un mes nuevo cada mes; Indeed, cada semana; las series de FRED, cuando la agencia publica.
- Seguridad, código y permisos guardan el año en curso solo como cifra aparte («va en …»); los gráficos usan años completos.
- FDOT publica los conteos de tráfico una vez al año; FARS, los choques mortales con más de un año de rezago; LYNX cambia
  su horario de buses unas veces al año (la fecha del horario es la vigencia).
