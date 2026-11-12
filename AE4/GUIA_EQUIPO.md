# Guía del equipo — todo lo que hay que saber para presentar la AE4

**Grupo AE_Grupo 3** · Estefanía Martínez Guzmán · Carlos Andrés Osorio Agudelo · Valentina Pérez Flórez
**Curso:** Proyecto Integrado III — Analítica de Datos · Docente: Andrés Felipe Callejas Jaramillo

> Esta guía está escrita para leerse en 15 minutos y poder responder cualquier pregunta del
> profesor sobre los datos y el proceso. Si algo no queda claro, preguntar antes del martes 17.

---

## 1. El proyecto en una página

Un sistema de bicicletas públicas necesita saber **cuándo se usa más y bajo qué condiciones**,
porque de eso dependen tres decisiones de operación:

1. **Cuántas bicicletas** hay disponibles en cada zona.
2. **Cuántas personas** se necesitan para reubicar bicicletas entre estaciones.
3. **Cuándo** hacer el mantenimiento sin afectar el servicio.

El dataset no trae esa lectura hecha. El proyecto toma los datos crudos del sistema, los limpia,
los enriquece y construye métricas que responden **seis preguntas de negocio**. La evidencia final
es una aplicación en Streamlit que cualquiera puede abrir y recorrer.

**Alcance:** el análisis es **descriptivo y comparativo**. No explica causas ni predice valores
futuros. Esa frase hay que decirla tal cual si el profesor pregunta por el alcance.

---

## 2. El dataset, explicado sin jerga

| Dato | Valor |
|---|---|
| Fuente | UCI Machine Learning Repository, *Bike Sharing Dataset* (id 275), vía Hugging Face `t22000t/bike-sharing-tabular` |
| Sistema real | **Capital Bikeshare**, Washington D. C. |
| Periodo | 1 de enero de 2011 – 31 de diciembre de 2012 |
| Registros | **17.379 horas** (de 17.544 posibles) |
| Columnas originales | 17 |
| Columnas después del enriquecimiento | 40 |

### La idea clave: una fila = una hora
Cada fila no es un cliente ni un viaje: es **una hora de operación** del sistema, con la cantidad
de bicicletas que se rentaron en esa hora y cómo estaban el clima y el calendario.

### Las variables que hay que saber sí o sí

| Variable | Qué significa | Unidad / valores |
|---|---|---|
| `cnt` | Rentas totales de esa hora | conteo (entero) |
| `casual` | Rentas de usuarios sin suscripción | conteo |
| `registered` | Rentas de usuarios con suscripción | conteo |
| `hr` | Hora del día | 0 a 23 |
| `workingday` / `holiday` | Si es día laborable / festivo | 0 o 1 |
| `season` | Temporada | 1 primavera, 2 verano, 3 otoño, 4 invierno |
| `weathersit` | Condición del clima | 1 despejado … 4 lluvia fuerte |
| `temp`, `hum`, `windspeed` | Temperatura, humedad, viento (venían normalizados 0–1) | convertidos a °C, %, km/h |
| `yr` | Año | 0 = 2011, 1 = 2012 |

**Regla que siempre se cumple:** `cnt = casual + registered` en los 17.379 registros.
Si el profesor pregunta cómo se validó, esa es la primera respuesta.

### Qué es "enriquecer" (etapa 2)
No se agregaron filas ni fuentes externas: se **construyeron 12 variables nuevas** a partir de las
que ya existían. Ejemplos:

- `franja_horaria`: agrupa las 24 horas en 6 franjas (madrugada, mañana, pico mañana, mediodía, pico tarde, noche).
- `tipo_dia`: laborable o no laborable, combinando `workingday` y `holiday`.
- `temp_c`, `hum_pct`, `windspeed_kmh`: las escalas originales pasadas a unidades entendibles.
- `total_dia`, `promedio_hora_dia`, `pct_hora_del_dia`: contexto del día para comparar una hora contra su propio día.

### Calidad de los datos (lo que sí se corrigió y lo que no)
- 0 duplicados de hora, 0 inconsistencias entre `cnt` y `casual + registered`.
- **165 horas faltantes en 76 días** (≈ 0,9 % del periodo). **No se imputaron**: se declaran como
  limitación. Responder así si preguntan por datos faltantes.

---

## 3. Qué se entregó en cada etapa

| Etapa | Qué hicimos | Evidencia en el repositorio |
|---|---|---|
| **EA1** | Cargar el dataset y describir su estructura | `EA1/notebooks/`, `EA1/resultados/resumen_dataset.txt` |
| **AE2** | Definir la necesidad, las preguntas y revisar la calidad (tipos, nulos, dominios) | `AE2/documento/`, `AE2/notebooks/` |
| **AE3** | Transformar, enriquecer y generar las **17 tablas de resultados** | `AE3/notebooks/`, `AE3/resultados/*.csv`, `dataset_preparado.csv` |
| **AE4** | Métricas, app en Streamlit y documento integral | `AE4/app.py`, `AE4/metricas.py` |

**Aplicación publicada:** <https://proyecto-integrado-iii-team3-preica2602b020038.streamlit.app/>

Un solo repositorio para todo el periodo: **https://github.com/carlososoa/proyecto-integrado-iii**

---

## 4. Las seis preguntas y su respuesta (con la cifra)

Estas cifras son del periodo completo (2011–2012). En la app cambian si se aplican filtros.

| # | Pregunta | Respuesta en una frase | Cifra clave |
|---|---|---|---|
| 1 | ¿Cuánta demanda hay y cómo se reparte en el día? | 3.292.679 rentas en 17.379 horas; promedio 189,5 por hora y mediana 142, así que hay horas muy cargadas y muchas flojas. | 189,5 vs 142 |
| 2 | ¿En qué franjas horarias se concentra? | La tarde concentra la demanda: "pico tarde" (16–19 h) aporta 33,4 % del total. La madrugada solo 3,2 %. | 33,4 % |
| 3 | ¿Cambia según el tipo de día? | El laborable promedia 193,2 rentas/hora y el no laborable 181,4, pero el perfil es distinto: el laborable tiene dos picos (entrada y salida del trabajo). El ocasional pasa de 13,2 % a 31,7 %. | 13,2 % → 31,7 % |
| 4 | ¿Cambia con la temporada y entre años? | Otoño es la temporada más fuerte (236,0 rentas/hora) y primavera la más floja (111,1). El promedio creció 63 % de 2011 a 2012, en las cuatro temporadas. | +63 % |
| 5 | ¿Cambia con el clima y la temperatura? | Con cielo despejado 204,9 rentas/hora; con lluvia o nieve ligera 111,6: cae 45,5 %. La demanda sube al pasar de frío a templado. | −45,5 % |
| 6 | ¿Qué peso tienen casuales y registrados? | El registrado concentra 81,2 % de las rentas (2.672.662) y el casual 18,8 % (620.017). El casual crece los fines de semana. | 81,2 % / 18,8 % |

**Frase de cierre del análisis:** la demanda es **predecible en su forma** (franja horaria, tipo de
día, clima) y **creciente en su volumen** (2012 sobre 2011), lo que permite planear operación, pero
el dataset **no permite afirmar causas** ni proyectar años futuros.

---

## 5. Cómo se usa la app (recorrido para la demo)

La aplicación tiene nueve secciones y con eso se puede hacer **toda la presentación sin diapositivas**:

1. **Proyecto y datos** (apertura): necesidad, pregunta de análisis, alcance y ficha del dataset.
2. **Resumen del periodo**: gráfico de demanda promedio por hora + participación por franja + tabla de las seis preguntas.
3. **Filtros (barra izquierda)**: periodo, temporada, tipo de día y clima. Todo se recalcula.
4. **Preguntas 1 a 6**: cada una muestra la métrica con su unidad, el gráfico, la lectura, la decisión que apoya y la limitación.
5. **Tablas desplegables**: cada sección tiene la tabla exacta de respaldo (las mismas cifras del documento).
6. **Conclusiones y recomendaciones** (cierre): cuatro tarjetas de conclusión, cinco recomendaciones y el bloque de lo que el análisis no afirma.

Demostración sugerida para los 5 minutos: apertura (30 s) → resumen (30 s) → pregunta 2 con filtro a "No laborable"
(40 s) → pregunta 5 cambiando el clima (30 s) → pregunta 6 (30 s) → cierre en conclusiones (1 min).

---

## 6. Preguntas que puede hacer el profesor (y cómo responder)

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué ese dataset? | Porque trae la variable que se quiere describir (`cnt`) y los criterios para compararla (hora, tipo de día, temporada, clima), en un registro horario real de dos años. |
| ¿Los datos son reales? | Sí: registro horario del sistema Capital Bikeshare (Washington D. C.), publicado en UCI y replicado en Hugging Face. |
| ¿Qué es una fila? | Una hora de operación del sistema, no un viaje ni un cliente. |
| ¿Cómo validaron los datos? | `cnt = casual + registered` en los 17.379 registros; 0 duplicados de hora; 40 columnas documentadas y verificadas contra el dataframe. |
| ¿Qué hicieron con los datos faltantes? | Son 165 horas de 76 días (0,9 %). No se imputan: se declaran como limitación porque inventar horas alteraría los promedios. |
| ¿Por qué promedio y mediana? | Porque si el promedio (189,5) está muy por encima de la mediana (142), la distribución tiene horas muy cargadas: la mediana describe la hora típica, el promedio el volumen. |
| ¿Eso es causalidad? | No. Es descriptivo y comparativo: se observa que con lluvia baja la demanda, pero clima y temporada se mueven juntos, así que no se aísla la causa. |
| ¿Por qué Streamlit? | Porque se conecta al mismo repositorio, lee los datos preparados y publica una URL accesible; el profesor puede revisarla sin instalar nada. |
| ¿Qué limitación tiene el análisis? | Tres: no hay capacidad instalada (no se mide demanda insatisfecha), no hay usuarios únicos (registrado/casual son tipos de renta, no personas) y solo hay dos años, insuficiente para proyectar. |
| ¿Qué decisión se puede tomar con esto? | Reforzar flota y personal en el pico de la tarde (16–19 h), programar mantenimiento en la madrugada, y ajustar la operación según el clima y el tipo de día. |
| ¿Qué cambiarían con más datos? | Agregar capacidad por estación y datos de usuarios para separar efecto clima de efecto temporada, y más años para proyectar. |

---

## 7. Reparto del guion (5 minutos + 5 de preguntas)

| Minuto | Quién | Qué dice |
|---|---|---|
| 0:00 – 1:00 | Estefanía | Necesidad, pregunta de negocio y qué representa una fila del dataset |
| 1:00 – 3:30 | Carlos | Demo en la app: resumen, filtros y preguntas 1 a 3 (con las cifras) |
| 3:30 – 4:30 | Valentina | Preguntas 4 a 6: temporada, clima y tipo de usuario |
| 4:30 – 5:00 | Estefanía | Conclusiones, recomendaciones y limitaciones |

Cada integrante debe poder responder por **cualquier** pregunta: el profesor ya avisó que pregunta
a un integrante qué hizo el otro.

---

## 8. Reglas y fechas (lo que dijo el profesor)

- **Presentación: martes 17 de noviembre, 7:20 – 7:30 p. m.** (semana 7). Conectarse 6:45 p. m. al Meet del sincrónico.
- **Formato: 5 min de presentación + 5 min de preguntas.** Es obligatorio presentar: la nota se entrega al final de la clase.
- **Todos los integrantes participan** y deben conocer el proceso.
- **Entrega en Canvas: domingo 29 de noviembre, 11:59 p. m.** con el PDF completo y los enlaces del repositorio y de la app.
- La app gratuita **se duerme por inactividad**: hay que abrirla 10 minutos antes de presentar.
