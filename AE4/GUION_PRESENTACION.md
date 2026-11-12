# Guion de la presentación — martes 17 de noviembre, 7:20 p. m.

**AE_Grupo 3** · Estefanía Martínez Guzmán · Carlos Andrés Osorio Agudelo · Valentina Pérez Flórez
**Turno:** martes 17 de noviembre, 7:20 – 7:30 p. m. · Meet: `meet.google.com/cie-cowy-rzb`
**Formato:** 5 minutos de presentación + 5 minutos de preguntas · obligatorio

---

## 0. Antes de conectar (6:40 – 6:55 p. m.)

| Hora | Qué hacer |
|---|---|
| 6:40 | Abrir la app para despertarla: `https://proyecto-integrado-iii-team3-preica2602b020038.streamlit.app/` |
| 6:45 | Entrar al Meet con cámara y micrófono probados. Ceñir el tiempo: el profesor tiene 3 grupos. |
| 6:50 | Tener abiertas en pestañas: (1) la app, (2) el PDF del informe en la página de conclusiones, (3) la lista de respuestas rápidas (sección 5 de este guion). |
| 6:55 | Compartir pantalla con la app ya cargada en **"Proyecto y datos"** (la primera sección) y zoom del navegador en 100 %. |
| 6:58 | Silenciar notificaciones; cerrar chat y correo. |

**Si la app no responde:** recargar una vez. Si sigue caída, usar el PDF del informe (sección 9) y las capturas de las figuras. Nunca improvisar cifras: todas están en el documento.

---

## 1. Estructura de los 5 minutos

| Minuto | Quién | Contenido |
|---|---|---|
| 0:00 – 0:50 | Estefanía | Problema, necesidad y qué representa una fila del dataset |
| 0:50 – 2:20 | Carlos | Resumen del periodo + preguntas 1 y 2 (con la app en vivo) |
| 2:20 – 3:30 | Valentina | Preguntas 3, 4 y 5 (temporada, clima, tipo de día) |
| 3:30 – 4:10 | Estefanía | Pregunta 6: casuales vs. registrados |
| 4:10 – 5:00 | Carlos | Conclusiones, recomendaciones y cierre |

---

## 2. Texto de la presentación

### Estefanía · 0:00 – 0:50 · El problema

> "Buenas noches, profesor. Somos el grupo 3: Estefanía Martínez, Carlos Osorio y Valentina Pérez.
>
> El área de operaciones de un sistema de bicicletas públicas necesita saber **cuándo se usa más el sistema y bajo qué condiciones**, porque de eso dependen tres decisiones: cuántas bicicletas tener disponibles por zona, cuántas personas destinar a reubicarlas entre estaciones y cuándo programar el mantenimiento sin afectar el servicio.
>
> Trabajamos con el registro horario del sistema Capital Bikeshare de Washington D. C., 2011 y 2012: **17.379 horas de operación** y **3.292.679 rentas**. Un dato importante para leer todo lo que viene: **cada fila es una hora**, no un viaje ni una persona. Por eso describimos la operación del sistema, no el comportamiento individual."

### Carlos · 0:50 – 2:20 · Resumen, pregunta 1 y 2

> "Esta es la aplicación. Arriba, el periodo completo: 3.292.679 rentas en 17.379 horas, con **189,5 rentas por hora de promedio y 142 de mediana**. Esa diferencia ya dice algo: hay horas muy cargadas y muchas horas flojas; el promedio no representa la hora típica.
>
> *(señalar el gráfico)* La demanda tiene dos picos y un valle profundo en la madrugada. La hora más cargada son las 17:00, con 461,5 rentas; la más floja, las 4:00, con 6,4.
>
> Paso a la pregunta 2, que es la que más le sirve a la operación: **¿en qué franjas se concentra?** *(clic en "2 · Franjas horarias")*. La franja de pico tarde, de 16 a 19, concentra el **33,4 % de las rentas**, con 377,6 por hora: casi el doble del promedio. Sumando las dos horas pico llegamos al **47,7 %**. La madrugada, en cambio, apenas el 3,2 %.
>
> Ahí hay un factor de quince entre la franja más cargada y la más floja. Por eso la recomendación es planear por franja y no por día."

### Valentina · 2:20 – 3:30 · Preguntas 3, 4 y 5

> "Sigo con las condiciones que cambian esa demanda. **Tipo de día** *(clic)*: los promedios son parecidos, 193,2 en laborable y 181,4 en no laborable, pero el perfil no: el laborable tiene dos picos, entrada y salida del trabajo, y el no laborable una meseta de mediodía. Y el usuario ocasional pasa del 13,2 % al 31,7 % del día.
>
> **Temporada y año** *(clic)*: la más fuerte es otoño, con 236 rentas por hora, y la más floja primavera, con 111,1. Entre 2011 y 2012 el promedio por hora creció **63,2 %**, y el crecimiento aparece en las cuatro temporadas: no es efecto de una estación.
>
> **Clima** *(clic)*: con cielo despejado, 204,9 rentas por hora; con lluvia o nieve ligera, 111,6. Una caída del **45,5 %**. La temperatura acompaña: la demanda se concentra en los rangos templado y cálido.
>
> Una aclaración metodológica: son asociaciones, no causas. Clima, temporada y tipo de día se mueven juntos y el dataset no permite separarlos."

### Estefanía · 3:30 – 4:10 · Pregunta 6

> "**¿Quiénes usan el sistema?** *(clic)* El usuario registrado concentra el **81,2 %** de las rentas, 2.672.662, y el ocasional el 18,8 %. Pero lo interesante es el perfil: el registrado marca los picos de entrada y salida del trabajo; el ocasional se reparte en el mediodía y la tarde, y crece los fines de semana.
>
> Son dos usos del mismo sistema: movilidad cotidiana y esparcimiento. Cada uno pide capacidad en momentos distintos."

### Carlos · 4:10 – 5:00 · Conclusiones

> "Tres conclusiones y cierro.
>
> Primera: la demanda **es predecible en su forma**. Dos picos en día laborable, meseta el fin de semana, valle nocturno, más volumen en otoño y verano, y caída con lluvia.
>
> Segunda: **la operación se debe planear por franja**. La ventana de 16 a 19 concentra un tercio de la demanda y la madrugada es el momento natural para el mantenimiento.
>
> Tercera: **el proyecto deja la evidencia disponible**. La app está publicada, vinculada al repositorio, con las cifras verificadas contra las tablas del análisis; cualquiera del área puede abrirla y filtrar sin instalar nada.
>
> Lo que no afirmamos: no hablamos de causas ni de rentabilidad, porque los datos no traen precios ni costos, y registran la demanda que se atendió, no la que se perdió por falta de bicicletas.
>
> Quedamos atentos a sus preguntas."

---

## 3. Coreografía de la demo (para no perderse)

1. Abrir en **"Proyecto y datos"** — es la sección de la apertura: necesidad, pregunta y ficha del dataset.
2. Pasar a **"Resumen del periodo"** y señalar las cuatro tarjetas de indicadores (rentas, promedio, mediana, horas).
3. Clic en **"2 · Franjas horarias"** → leer el 33,4 % y el 47,7 %.
4. Clic en **"3 · Tipo de día"** → los dos gráficos de barras y el perfil horario.
5. Clic en **"4 · Temporada y año"** → barras por temporada y por año.
6. Clic en **"5 · Clima y temperatura"** → barras de clima y línea de temperatura.
7. **Aplicar un filtro en vivo** (opcional, si sobra tiempo): quitar "Invierno" y "Primavera" en Temporada y mostrar que las cifras cambian.
8. Clic en **"6 · Casuales y registrados"** → dona y perfiles.
9. Cerrar en **"Conclusiones y recomendaciones"**: las cuatro tarjetas de conclusión y las recomendaciones. Es la pantalla del cierre; no hay que cambiar de herramienta.

> La app ya tiene apertura y cierre: **no se necesitan diapositivas**. Todo el recorrido ocurre en la misma pestaña.

> Si el tiempo aprieta, saltar los pasos 4 y 5: lo indispensable es 1, 3 y 8.

---

## 4. Reparto de responsabilidades durante las preguntas

- **Datos y proceso** (qué es una fila, cuántas horas, cómo se validó): Carlos.
- **Métricas de demanda, franjas y temporada**: Estefanía.
- **Clima, tipo de día y tipo de usuario**: Valentina.
- Si la pregunta es de otro, la responde quien la tenga más fresca y el otro complementa con una cifra. **Nunca decir "eso lo hizo él/ella"**: el profesor ya avisó que pregunta a cualquiera por el trabajo del otro.

---

## 5. Respuestas rápidas (tenerlas a mano)

| Pregunta | Respuesta |
|---|---|
| ¿Qué es una fila? | Una hora de operación del sistema, no un viaje ni un usuario. |
| ¿Datos reales? | Sí: Capital Bikeshare (Washington D. C.), 2011-2012, publicado en UCI y replicado en Hugging Face. |
| ¿Cuántos registros? | 17.379 horas de 17.544 posibles (99,1 % de cobertura). |
| ¿Qué hicieron con los faltantes? | 165 horas en 76 días. No se imputan: se marcan y se declaran como limitación. |
| ¿Cómo validaron? | `cnt = casual + registered` en los 17.379 registros; 0 duplicados de hora; dominios revisados. |
| ¿Por qué promedio y mediana? | El promedio (189,5) supera la mediana (142): hay horas muy cargadas. La mediana describe la hora típica. |
| ¿Por qué esa franja? | Cortes definidos en el proyecto (0-5, 6-8, 9-11, 12-15, 16-19, 20-23). Otro corte mueve los porcentajes. |
| ¿Eso es causalidad? | No. Es descriptivo y comparativo; clima, temporada y día se mueven juntos. |
| ¿Por qué Streamlit? | Se conecta al mismo repositorio, lee los datos preparados y publica una URL accesible sin instalar nada. |
| ¿Cómo sé que la app no inventa cifras? | La app y el documento usan el mismo módulo de cálculo, y un script compara 53 cifras contra las tablas del análisis. |
| ¿Limitaciones? | Sin oferta (no hay demanda insatisfecha), sin usuarios únicos, dos años y una ciudad, sin precios ni costos. |
| ¿Qué harían con más datos? | Capacidad por estación y datos de usuarios para separar clima de temporada; más años para proyectar. |
| ¿Grupal o individual? | Grupal, AE_Grupo 3; los tres participamos en el análisis, la app y el documento. |

---

## 6. Errores que cuestan puntos (evitarlos)

- Decir "ingresos" o "rentabilidad": el dataset no tiene precios ni costos.
- Decir "la lluvia hace que baje la demanda": es asociación, no causa.
- Leer el promedio como si fuera la hora típica: la mediana es 142, no 189,5.
- Presentar solo un integrante o que uno no sepa qué hizo el otro.
- Pasarse de los 5 minutos: el profesor tiene tres grupos y avisó que es puntual.
- Mostrar el notebook en vez de la app: la app es la evidencia de esta etapa.

---

## 7. Después de presentar

1. Confirmar con el profesor que la nota quedó registrada (la da al final de la clase).
2. Enviar en Canvas, antes del **domingo 29 de noviembre, 11:59 p. m.**: el PDF completo, el enlace del repositorio y el enlace de la app.
3. Verificar en Canvas que el envío quede en estado *Entregado* con el archivo adjunto.
