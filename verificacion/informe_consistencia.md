# Consistencia de cifras entre pestañas

Revisión del 2 nov 2026 sobre la última foto del lago (`lago/curado/tema=…/fecha=2026-11-02/`, antes `lago/raw/`) y sobre
el texto que la página muestra de verdad en cada pestaña (inicio, decidir ×4, comparar ×3, gente, economía, barrios,
seguridad, turismo, clima, fuentes y el modo presentación), leído con un navegador.

La comprobación automática está en `verificacion/consistencia.py` y la corre `verificar.py`: con un FAIL no se publica.
`probar_verificador.py` prueba que sepa fallar.

| Cifra | Pestañas | Valor en cada una | Fuente (lago) | ¿Consistente? | Causa / qué se hizo |
|---|---|---|---|---|---|
| Población del condado de Orange | Inicio, Gente, Comparar (ciudades), Presentación | 1,53 millones (2025) en todas. Crecimiento en 10 años: «+18,3 %» en Inicio y Comparar, «18 %» en la frase de Gente y en Presentación | Census vía FRED · `gente.poblacion_condado_ultimo_anio`, `crecimiento_condado_10_anios` | Valor sí; redondeo no | La frase redondeaba a entero. **Corregido**: 18,3 % en todas |
| Población de la ciudad | Gente (escala), Barrios (cuadre), Comparar (distritos), Decidir | 319.758 oficial (censo 2020–2024) en Gente y Barrios; 314.042 (suma de barrios) en Barrios y en «Toda la ciudad» de Distritos | `censo.poblacion_ciudad` y `censo.poblacion_estimada_en_barrios` | Sí, explicado | Barrios dice la diferencia (−1,8 %); Distritos la rotula «estimaciones del censo por barrio». **Pregunta 1** |
| Desempleo del área | Inicio, Economía, Comparar, Presentación, Datos y fuentes | 4,4 % (sep 2026), +0,3 puntos frente a 4,1 % (sep 2025); Florida 4,2 %; «segunda de menor desempleo» | BLS vía FRED · `economia.desempleo_ultimo_mes` = último punto de `desempleo_orlando` | Sí | — |
| Salario por hora | Inicio, Economía, Comparar, Decidir (Emprender, Vivir) | US$ 33,42 (sep 2026); −8 % frente a Tampa, Miami y Jacksonville | BLS vía FRED · `economia.salario_hora_ultimo_mes` | Valor sí; fuente no | Emprender mostraba el número sin su fuente. **Corregido**: se agregó la ficha «BLS vía FRED» |
| Arriendo típico | Inicio, Economía, Comparar, Decidir (Vivir, Invertir) | US$ 1.929 (sep 2026, área metropolitana) en todas | Zillow · `vivienda.arriendo_tipico_ultimo_mes` | Sí | Vivir lo usa para llevar la mediana del censo (US$ 1.747) a hoy: × 1,10, y lo dice |
| Arriendo mediano del censo | Gente, Decidir (Vivir) | US$ 1.747 (2020–2024) | Census ACS · `censo.arriendo_mediano_ciudad` | Sí | — |
| Ingreso mediano · condado de Orange | Inicio, Gente, Presentación | US$ 81.645 (2024), 5 % más que Florida | Census vía FRED · `gente.ingreso_mediano_condado` | Sí | — |
| Ingreso mediano · ciudad | Gente (ciudad contra ciudad), Comparar (ciudades), Decidir (Emprender) | US$ 72.336 (2020–2024); en «Toda la ciudad» de Distritos, US$ 77.781 (aprox., agregado de barrios) | Census ACS · `censo.ingreso_mediano_ciudad` | Sí, rotulado | Distritos dice «Ingreso (aprox.)». **Pregunta 1** |
| Ingreso y pobreza · Florida | Inicio (carrusel), Gente (dos gráficos) | Ingreso US$ 77.687 (2024, un año) y US$ 74.568 (promedio 2020–2024); pobreza 12,1 % y 12,6 % | FRED (`gente.ingreso_mediano_florida`) y Census Reporter (`censo.*_ciudades`) | Sí, con aviso | Son dos mediciones distintas y cada gráfico dice su fuente y su periodo. **Pregunta 2** |
| Permisos emitidos (ciudad) | Inicio, Economía, Barrios, Presentación | 30.721 en 2025; variación «−3,3 %» en la tarjeta y «3 %» en las frases | Datos abiertos de Orlando · `permisos.permisos_emitidos_ultimo_anio_completo` | Valor sí; redondeo no | **Corregido**: «3,3 % menos» en todas |
| Permisos por barrio | Inicio/Economía/Presentación (frase), Barrios (mapa, ranking, ficha), Comparar (barrios), Decidir (Invertir) | Vista Park 2.736 y Lake Nona South 2.624 en frase, ficha, ranking, Comparar e Invertir; «se llevan 17 de cada 100» | La frase lee `permisos_por_barrio_ultimo_anio` y el mapa `permisos_barrio_2025` | Sí | Son dos series idénticas (122 barrios, 30.312). Ahora una comprobación falla si se separan. Suma del mapa 30.304: 8 en Narcoossee Groves (sin polígono), 401 sin barrio y 8 en barrios bajo 5: cuadra |
| Casos de policía (ciudad) | Inicio, Seguridad, Barrios (cuadre), Presentación | 17.574 en 2025 = 9.100 + 5.125 + 3.349; variación «−15,1 %» en la tarjeta y «15 %» en la frase | Policía de Orlando · `seguridad.delitos_ultimo_anio` | Valor sí; redondeo no | **Corregido**: «15,1 % menos» |
| Casos de policía por barrio | Seguridad (ranking por km²), Barrios (frase, mapa, ranking, ficha), Comparar (barrios) | Florida Center encabeza el total (1.587); Central Business District, la densidad (935 por km²) | `seguridad.delitos_barrio_2025` (un solo modelo de barrios para todas las vistas) | Sí | Cada pestaña dice si es total o por km². Suma 17.190 + 366 sin barrio + 18 bajo el umbral = 17.574 |
| Tasa de casos de la ciudad | Decidir (Emprender y Vivir), Comparar (distritos) | Emprender: «ciudad: 29,9 por cada 1.000 personas»; Vivir y Distritos: «ciudad: 54,7 por 1.000 habitantes» | Misma fuente, otra base: Emprender divide por residentes + empleos | No: parecía una contradicción | **Corregido el rótulo**: Emprender ahora dice «por cada 1.000 personas entre residentes y empleos» (igual en restaurantes por 10.000). **Pregunta 3** |
| Empleo en ocio y hotelería | Inicio, Turismo, Comparar, Decidir (Emprender), Presentación | 19,8 % del empleo, 299 mil, +1,4 % (sep 2026). «El área más turística de las cuatro» sale del dato (puesto 1: 19,8 % frente a 11,7 / 10,8 / 11,7) | BLS vía FRED · `turismo.participacion_ocio_ultimo_mes` | Valor sí; fuente no | Emprender no mostraba la fuente. **Corregido** |
| Hospedajes con licencia | Inicio, Turismo | 345 (2 nov 2026) | `negocios.hospedajes_vigentes` | Sí | — |
| Negocios con licencia | Barrios, Decidir | 24.865; suma por barrio 21.659 + 3.184 sin barrio + 22 bajo el umbral | `negocios.negocios_vigentes` | Sí | — |
| Temperatura y alertas | Inicio, Clima, Presentación | 75 °F (24 °C), 1 alerta | weather.gov · `clima.temperatura_actual`, `alertas_activas` | Valor sí; texto no | Inicio decía «1 alertas». **Corregido**: «1 alerta vigente» |
| Calentamiento | Inicio, Clima, Presentación | +1,7 °F (1953–1986 → 1996–2025) | NOAA · `clima_historico.diferencia_entre_periodos` | Sí | — |
| Visitas en Wikipedia | Inicio, Turismo, Comparar | Español: 41.778 en 12 meses (0,64 veces los pares); inglés: 724.030 | Wikimedia · `escucha.*` | Sí | — |
| Precio de lista | Inicio, Economía, Decidir (Invertir), Presentación | US$ 410.000 (sep 2026), −2,5 % | Realtor.com vía FRED | Sí | — |
| Índice de precios de vivienda (pares) | Economía | Orlando, Miami y Jacksonville a 2026-T2; Tampa termina en 2024-T4 | FHFA vía FRED | Sí, con aviso | La página ya dice «La serie de Tampa termina en…»; la verificación deja un WARN |
| Textos fijos del recorrido | Inicio (recorrido por 6 barrios) | «En el sureste, donde Orlando crece hacia el aeropuerto» y «El centro concentra…» eran fijos aunque el barrio sale del dato | — | Hoy sí, mañana podía no | **Corregido**: solo se dicen si el barrio es del distrito 1 o es el Central Business District |
| «Menos de 5 casos» (plantilla) | Inicio, Barrios, Seguridad | 5 | `umbral_minimo_por_barrio` de cada tema | Sí | Comprobado en la verificación |

## Preguntas (no se cambiaron: dependen de una decisión)

1. En Comparar → Distritos, la fila «Toda la ciudad» suma los barrios (314.042 habitantes, ingreso aprox. US$ 77.781,
   7,1 % sin carro), mientras Gente y Comparar → Ciudades usan la cifra oficial de la ciudad (319.758, US$ 72.336, 7,4 %).
   ¿Dejamos la suma (coherente con los distritos) o ponemos la oficial (coherente con las otras pestañas)?
2. Florida sale con dos ingresos (US$ 77.687 de 2024 y US$ 74.568 promedio 2020–2024) y dos tasas de pobreza (12,1 % y
   12,6 %) en Gente. Son mediciones distintas y están rotuladas. ¿Dejamos las dos o usamos una sola?
3. Emprender mide «gente cerca» como residentes + empleos; Vivir y Seguridad, solo residentes. Ya está rotulado. ¿Se
   unifica la base?
4. El índice de vivienda de Tampa no se actualiza desde 2024-T4. ¿Lo quitamos de la comparación o lo dejamos con el aviso?
