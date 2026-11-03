# Cerebro Orlando

Sistema de información sobre Orlando, Florida, para el taller de datos de Tópicos de Sistemas de Información (EAFIT).
Responde seis preguntas con datos abiertos, ayuda a decidir (emprender, vivir, comprar o invertir, gobernar) y compara
Orlando con otras ciudades, sus seis distritos y sus barrios. Cada cifra trae su fuente, su vigencia y la fecha en que la
comprobamos.

Réplica del lago del Cerebro Lima: un script por tema, un contrato común, una verificación que sabe fallar y una vista
de una sola página. Solo biblioteca estándar de Python 3.9 o superior: no hay nada que instalar ni llaves que pedir.
(`catalogo/exportar_catalogo.py` es la excepción: usa `openpyxl` para leer el Excel, y no forma parte del lago.)

## Las seis preguntas y de dónde salen

| Pregunta | Temas del lago | Fuentes (ficha del Excel) |
|---|---|---|
| ¿Cuánta gente vive aquí y cómo le va frente a condados parecidos? | `gente`, `censo` | Census y BEA vía FRED: población, ingreso mediano e ingreso por persona, pobreza, IPC (F14); American Community Survey por sector y por ciudad (F12, F78) |
| ¿Cómo se mueve la economía y cuánto cuesta vivir aquí? | `economia`, `empleo`, `vivienda`, `permisos` | BLS, FHFA, Realtor.com y Census vía FRED: desempleo, salarios, solicitudes de negocio, inventario y rebajas (F14); Zillow, arriendo y valor típicos (F41); Indeed Hiring Lab (F70); permisos de la ciudad (F79) |
| ¿Qué pasa en cada barrio, quién vive allí, qué tiene cerca y hacia dónde va? | `permisos`, `seguridad`, `codigo`, `negocios`, `territorio`, `censo`, `riesgo`, `servicios`, `planeacion` | Datos abiertos de Orlando (F79, F81, F83, F86, F88, F90, F93, F94, F96); SIG de la ciudad (F107); censo (F12, F78); FEMA (F108); Policía de Orlando (F106) |
| ¿Qué pasa con la seguridad y la convivencia? | `seguridad`, `codigo` | Policía de Orlando (F106); casos de código urbano (F83) |
| ¿Cuánto pesa el turismo? | `turismo`, `negocios`, `escucha` | BLS vía FRED (F14); licencias de negocio (F81) y de alquiler de corto plazo (F85); Wikipedia (F71) |
| ¿Qué clima hay hoy, cómo está cambiando y qué barrios están más expuestos? | `clima`, `clima_historico`, `riesgo` | National Weather Service (F57); NOAA NCEI (F58); FEMA, Índice Nacional de Riesgo (F108) |

Cada pregunta se compara «contra algo»: Tampa, Miami y Jacksonville (y Florida y EE. UU.) para las cifras del área y de
la ciudad; el año anterior para las tendencias; la mediana de los 125 barrios en cada ficha; los demás distritos.

## Cómo se corre

```
python3 reconstruir.py                       # borra el lago, corre todos los ingesta/pull_*.py y verifica (funciona en Windows)
python3 verificacion/verificar.py            # con un solo FAIL no se publica
python3 verificacion/probar_verificador.py   # comprueba que la verificación sepa fallar
python3 vista/construir_vista.py             # arma vista/index.html; corre verificar.py antes y no construye si falla
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

**Cómo se trajeron los datos de la v3.** El contenedor donde se construyó no tiene salida a esas fuentes, así que el
navegador del grupo pidió cada URL (las mismas que arman los scripts), las guardó en un archivo y los scripts corrieron
contra esa copia, sin cambiar una línea. En un computador con internet, `reconstruir.py` las pide directo.

En Windows se usa `python` o `py` en lugar de `python3`. Opcional: `set CONTACTO=correo-del-grupo@...` antes de
correr, porque el servicio del clima pide que el cliente se identifique.

## Qué hay en cada carpeta

| Carpeta | Qué guarda |
|---|---|
| `ingesta/` | Un script por tema. `comun.py` tiene lo compartido: contrato, consultas a Socrata, ArcGIS y FRED, la supresión bajo el umbral y la geometría (índice espacial, rejilla, reparto de zonas entre barrios). |
| `catalogo/` | `fuentes_lago.json`: las 32 fuentes que alimentan el lago, con su licencia tal como aparece y su nivel de protección. `catalogo_completo.json`, `diccionario.json` y `bitacora_ia.json`: exportados del Excel por `exportar_catalogo.py`. |
| `lago/` | `lago/raw/<tema>/<tema>.json` (17 temas): lo que escribe cada script, con la forma del contrato. Está en `.gitignore`. `lago/territorio/`: capas GeoJSON en WGS84, simplificadas; esta sí se publica. |
| `verificacion/` | `verificar.py` y la prueba de que sabe fallar. |
| `vista/` | `plantilla.html` (estructura), `estilos.css`, `app.js` y `construir_vista.py`, que junta todo con el lago en una sola página: `index.html`. |
| `entrega1/`, `entrega2/` | El diccionario de datos (Excel) tal como se entregó en cada corte. |

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
  excluida o una celda por barrio bajo el umbral. `probar_verificador.py` comprueba que esas fallas se detecten.
- El censo es agregado por diseño, pero un porcentaje de un barrio con muy poca gente se acerca a describir hogares: los
  barrios con menos de 200 habitantes estimados no publican porcentajes ni medianas, y `verificar.py` lo exige.
- De los colegios solo se pide el tipo: el servidor trae nombre del director y teléfono, y no se descargan.

Las demás fuentes son **«abierto»**: series agregadas por área sin datos de personas.

**Población por barrio (estimada).** El censo publica por sector censal, no por barrio. `comun.reparto()` cubre la ciudad
con una rejilla de puntos cada 150 m (sin lagos) y reparte cada sector entre los barrios según los puntos que comparten.
Los conteos se suman así; las medianas (ingreso, arriendo, edad) se promedian ponderando por población y se llaman
«aproximadas». Control: los barrios suman 313.636 habitantes frente a 319.758 oficiales (−1,9 %); `verificar.py` falla
si la diferencia pasa de 15 %. El índice de riesgo de FEMA y la proyección 2045 de la ciudad se llevan a barrios igual.

## La vista

`vista/index.html` es una sola página sin servidor. Diez secciones: resumen, decidir, comparar, gente, economía y
vivienda, barrios, seguridad, turismo, clima y fuentes.

- **Resumen:** un tablero por perfil con su dato principal; las seis respuestas con su cifra, su tendencia en palabras y
  su fuente; Orlando contra ciudades parecidas (seis medidas); las preguntas sin respuesta abierta; un mapa 3D que gira
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
- Para desplegar en Vercel: carpeta raíz `vista/`, sin comando de build.
- `python3 vista/construir_vista.py --sin-verificar` sirve solo para probar el diseño; la página lo dice en «Fuentes».
- Desde la consola del navegador, `cerebro.B` tiene el modelo de barrios que usan todas las vistas.

## Lo que sigue pendiente

1. **Licencias de la ciudad.** Las fuentes del portal de Orlando y la capa de la policía «no declaran» licencia (la ficha
   del portal tiene el campo vacío). `verificar.py` lo marca con WARN. Antes de un uso fuera del curso, hay que leer los
   términos del portal.
2. **Realtor.com vía FRED** dice «Copyrighted: Citation Required»: se usa con la atribución visible en la vista.
3. **Zillow y el SIG de la ciudad** no traen texto de licencia: se citan junto a cada gráfico y quedan con WARN.
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
