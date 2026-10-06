# Cerebro Orlando · ingesta del lago

Réplica mínima del lago del Cerebro Lima: un script por tema, un contrato común, una verificación que sabe fallar.
Solo biblioteca estándar de Python 3.9 o superior: no hay nada que instalar ni llaves que pedir.
(`catalogo/exportar_catalogo.py` es la excepción: usa `openpyxl`, y no forma parte del lago.)

## Cómo se corre

```
python3 ingesta/pull_escucha.py      # Wikipedia: cuánta gente busca Orlando          (F71)
python3 ingesta/pull_empleo.py       # Indeed Hiring Lab: índice de vacantes          (F70)
python3 ingesta/pull_vivienda.py     # FRED: índice de precios de vivienda            (F14)
python3 ingesta/pull_clima.py        # National Weather Service: clima y alertas      (F57)
python3 ingesta/pull_territorio.py   # Límites, barrios y distritos de Orlando        (F88, F90, F94)
python3 verificacion/verificar.py    # con un solo FAIL no se publica
python3 reconstruir.py               # borra el lago, lo reconstruye y verifica (funciona en Windows)
python3 verificacion/probar_verificador.py   # comprueba que la verificación sepa fallar
```

En Windows se usa `python` o `py` en lugar de `python3`. Opcional: `set CONTACTO=correo-del-grupo@...` antes de
correr, porque el servicio del clima pide que el cliente se identifique.

## Qué hay en cada carpeta

| Carpeta | Qué guarda |
|---|---|
| `ingesta/` | Un script por tema. Cada uno dice arriba qué lee y qué escribe. `comun.py` tiene lo compartido. |
| `catalogo/` | `fuentes_lago.json`: las fuentes que alimentan el lago, con su licencia (aquí se corrige). `catalogo_completo.json`: las 105 fichas del Excel, con las que no entraron, generadas por `exportar_catalogo.py`. |
| `lago/` | El dato limpio, un JSON por tema con la forma del contrato. `lago/raw/` está en `.gitignore`. |
| `territorio/` | Capas GeoJSON en WGS84, simplificadas. |
| `verificacion/` | `verificar.py` y la prueba de que sabe fallar. |

## Lo que hay que hacer a mano antes de publicar

1. **Escribir dos licencias.** En `catalogo/fuentes_lago.json`, las fuentes `fred_ihv_orlando` y `nws_api` dicen
   «por verificar». Se abre la página de la serie de FRED y los términos de weather.gov, se copia el texto tal como
   aparece, y mientras tanto `verificar.py` falla a propósito.
2. **Leer los términos del portal de Orlando.** Las tres capas de territorio quedaron como «no declara»: la ficha del
   portal no trae licencia (probado el 2026-10-06). `verificar.py` lo marca con WARN, no con FAIL.
3. **Pasar las fichas del Excel a «Integrada al lago»** solo cuando el script de esa fuente haya corrido de verdad y la
   verificación pase. Después, correr otra vez `exportar_catalogo.py`.
4. **Atribución visible** en la vista que use cada dato: Indeed Hiring Lab (CC BY 4.0) lo exige.

## Cosas que cambian solas

- `clima.json` cambia en cada corrida (tiempo real). Es esperado: no entra en la prueba de reproducibilidad.
- `escucha.json` suma un mes nuevo cada mes; `empleo.json`, cada semana.
- Las capas de Orlando se actualizan cuando la ciudad las actualiza (ver `vigencia` en cada cifra).
