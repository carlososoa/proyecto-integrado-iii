"""Aplicación Streamlit del proyecto integrador — Métricas y visualización.

Curso: Proyecto Integrado III - Analítica de Datos (IU Digital de Antioquia)
Grupo: AE_Grupo 3 — Carlos Andrés Osorio Agudelo, Estefanía Martínez Guzmán,
       Valentina Pérez Flórez

La app recorre las seis preguntas de negocio del proyecto. Cada sección muestra
la métrica con su unidad, el gráfico, la lectura de los datos, la decisión que
puede apoyar y la limitación del análisis.

Ejecutar en local:
    streamlit run AE4/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import metricas as m

# ---------------------------------------------------------------------------
# Configuración de página y estilo
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Demanda de bicicletas públicas · Proyecto Integrado III",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

AZUL = "#0F5C6B"
AZUL_CLARO = "#4A97A6"
TERRACOTA = "#C8623F"
ARENA = "#F6F3EC"
GRIS = "#5C5C5C"
VERDE = "#2A9D8F"

COLORES_TIPO = {"Laborable": AZUL, "No laborable": TERRACOTA}
COLORES_USUARIO = {"Registrado": AZUL, "Casual": TERRACOTA}

st.markdown(
    f"""
    <style>
      .stApp {{ background: {ARENA}; }}
      h1, h2, h3 {{ color: {AZUL}; letter-spacing: -0.01em; }}
      .bloque {{ background: #FFFFFF; border-radius: 14px; padding: 1.1rem 1.3rem;
                 border: 1px solid #E6E0D4; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
      .etiqueta {{ color: {GRIS}; font-size: .78rem; text-transform: uppercase;
                   letter-spacing: .08em; margin-bottom: .15rem; }}
      .cifra {{ color: {AZUL}; font-size: 1.7rem; font-weight: 700; line-height: 1.1; }}
      .unidad {{ color: {GRIS}; font-size: .8rem; }}
      .respuesta {{ background: #EAF2F4; border-left: 4px solid {AZUL};
                    padding: .8rem 1rem; border-radius: 6px; font-size: 1rem; }}
      .decision {{ background: #EAF5F0; border-left: 4px solid {VERDE};
                   padding: .8rem 1rem; border-radius: 6px; }}
      .limite {{ background: #FBF1E8; border-left: 4px solid {TERRACOTA};
                 padding: .8rem 1rem; border-radius: 6px; }}
      .pie {{ color: {GRIS}; font-size: .8rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Utilidades de formato (es-CO: miles con punto, decimales con coma)
# ---------------------------------------------------------------------------
def num(valor: float, decimales: int = 0) -> str:
    """Formatea un número al estilo colombiano: 3.292.679 / 189,5."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


def estilo(fig: go.Figure, alto: int = 380, titulo_y: str = "", titulo_x: str = "") -> go.Figure:
    """Aplica el estilo común a todos los gráficos."""
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#2E2E2E"),
        separators=".,",  # miles con punto, decimales con coma
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(title_text=titulo_x, showgrid=False, linecolor="#D9D3C7")
    fig.update_yaxes(title_text=titulo_y, gridcolor="#EDE8DD", zeroline=False, tickformat=",.0f")
    return fig


def tarjeta(etiqueta: str, valor: str, unidad: str) -> str:
    """HTML de una tarjeta de indicador."""
    return (
        f'<div class="bloque"><div class="etiqueta">{etiqueta}</div>'
        f'<div class="cifra">{valor}</div><div class="unidad">{unidad}</div></div>'
    )


def caja(clase: str, titulo: str, texto: str) -> None:
    st.markdown(f'<div class="{clase}"><strong>{titulo}</strong><br>{texto}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Datos y filtros
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando el dataset preparado…")
def datos() -> pd.DataFrame:
    return m.cargar_datos(Path(__file__).resolve().parents[1] / m.RUTA_DATOS)


df_total = datos()
k_total = m.kpis(df_total)

st.sidebar.markdown("### Filtros")
st.sidebar.caption("Los indicadores y los gráficos se recalculan con la selección.")

fechas = st.sidebar.date_input(
    "Periodo",
    value=(k_total["fecha_min"].date(), k_total["fecha_max"].date()),
    min_value=k_total["fecha_min"].date(),
    max_value=k_total["fecha_max"].date(),
    format="DD/MM/YYYY",
)
temporadas = st.sidebar.multiselect("Temporada", m.ORDEN_TEMPORADAS, default=m.ORDEN_TEMPORADAS)
tipos_dia = st.sidebar.multiselect("Tipo de día", ["Laborable", "No laborable"], default=["Laborable", "No laborable"])
climas = st.sidebar.multiselect("Clima", sorted(df_total["clima"].unique()), default=sorted(df_total["clima"].unique()))

st.sidebar.divider()
st.sidebar.caption(
    f"Dataset: `t22000t/bike-sharing-tabular` (UCI id 275) · {num(k_total['horas'])} horas · "
    f"{k_total['fecha_min']:%d/%m/%Y} a {k_total['fecha_max']:%d/%m/%Y}"
)
st.sidebar.caption("Grupo AE_Grupo 3 · Proyecto Integrado III · IU Digital")

# Aplicación de filtros
inicio, fin = (fechas if isinstance(fechas, tuple) and len(fechas) == 2 else (k_total["fecha_min"], k_total["fecha_max"]))
df = df_total[
    (df_total["fecha_hora"].dt.date >= inicio)
    & (df_total["fecha_hora"].dt.date <= fin)
    & (df_total["temporada"].isin(temporadas))
    & (df_total["tipo_dia"].isin(tipos_dia))
    & (df_total["clima"].isin(climas))
].copy()

if df.empty:
    st.error("Con esos filtros no queda ninguna hora registrada. Amplía la selección.")
    st.stop()

k = m.kpis(df)
periodo = f"{k['fecha_min']:%d/%m/%Y} – {k['fecha_max']:%d/%m/%Y}"

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown("## Demanda de un sistema de bicicletas públicas")
st.markdown(
    "El área de operaciones necesita **anticipar en qué momentos del día y bajo qué condiciones se concentra "
    "la demanda**, porque de eso dependen la disponibilidad de bicicletas por zona, el personal de reubicación "
    "y el mantenimiento programado. Cada fila del dataset es **una hora de operación** del sistema "
    "(Capital Bikeshare, Washington D. C., 2011–2012)."
)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(tarjeta("Rentas en el periodo", num(k["rentas"]), "rentas (conteo)"), unsafe_allow_html=True)
c2.markdown(tarjeta("Promedio por hora", num(k["promedio"], 1), "rentas/hora"), unsafe_allow_html=True)
c3.markdown(tarjeta("Mediana por hora", num(k["mediana"], 0), "rentas/hora"), unsafe_allow_html=True)
c4.markdown(tarjeta("Horas con registro", num(k["horas"]), f"de {num(k['horas_esperadas'])} horas del periodo"), unsafe_allow_html=True)

st.markdown(
    f'<p class="pie">Periodo mostrado: {periodo} · {num(k["dias"])} días · '
    f'cobertura {num(m.cobertura_pct(df), 1)} % de las horas · '
    f'{num(k["horas_faltantes"])} horas sin registro (no se imputan).</p>',
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Navegación por pregunta
# ---------------------------------------------------------------------------
preguntas = m.tabla_preguntas()
opciones = ["Resumen del periodo"] + [f"{i + 1}. {p['pregunta']}" for i, p in enumerate(preguntas)]
seleccion = st.radio("Recorre el proyecto", opciones, horizontal=True, label_visibility="collapsed")
indice = opciones.index(seleccion) - 1  # -1 = resumen

# ---------------------------------------------------------------------------
# Vista 0 — Resumen del periodo
# ---------------------------------------------------------------------------
if indice == -1:
    st.markdown("### Qué se hizo y cómo se lee esta aplicación")
    st.markdown(
        "El proyecto prepara 17.379 horas de operación (2011–2012) y las resume en seis preguntas de negocio. "
        "Cada sección de la app muestra **la métrica con su unidad**, el gráfico, la respuesta, la decisión que "
        "puede apoyar y la limitación. Los filtros de la izquierda recalculan todo el contenido."
    )

    izquierda, derecha = st.columns([3, 2])
    with izquierda:
        hora = m.por_hora(df)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=hora["hr"], y=hora["promedio"], mode="lines+markers", name="Promedio por hora",
                line=dict(color=AZUL, width=3), marker=dict(size=6), fill="tozeroy",
                fillcolor="rgba(15,92,107,0.10)",
                hovertemplate="Hora %{x}:00<br>%{y:,.1f} rentas/hora<extra></extra>",
            )
        )
        fig.update_layout(title="Demanda promedio a lo largo del día")
        estilo(fig, titulo_y="Rentas por hora", titulo_x="Hora del día")
        st.plotly_chart(fig)
    with derecha:
        franjas = m.por_franja(df)
        fig = go.Figure(
            go.Bar(
                x=franjas["participacion_pct"], y=franjas["franja_horaria"], orientation="h",
                marker_color=[AZUL if p == franjas["participacion_pct"].max() else AZUL_CLARO for p in franjas["participacion_pct"]],
                text=[f"{num(p, 1)} %" for p in franjas["participacion_pct"]], textposition="outside",
                hovertemplate="%{y}: %{x:,.1f} % del total<extra></extra>",
            )
        )
        fig.update_layout(title="Participación por franja horaria", showlegend=False)
        estilo(fig, titulo_y="", titulo_x="Participación del total (%)")
        st.plotly_chart(fig)

    st.markdown("#### Las seis preguntas y su métrica")
    tabla = pd.DataFrame(
        [{"#": i + 1, "Pregunta": p["pregunta"], "Métrica": p["metrica"], "Unidad": p["unidad"]} for i, p in enumerate(preguntas)]
    )
    st.dataframe(tabla, hide_index=True)

    st.markdown("#### Conclusiones del periodo")
    usuarios = m.por_tipo_usuario(df).set_index("tipo_usuario")
    st.markdown(
        f"- La demanda no se reparte de forma uniforme: **{num(franjas['participacion_pct'].max(), 1)} %** de las rentas "
        f"ocurre en la franja de mayor peso (**{franjas.loc[franjas['participacion_pct'].idxmax(), 'franja_horaria']}**).\n"
        f"- El promedio por hora ({num(k['promedio'], 1)}) es mayor que la mediana ({num(k['mediana'])}): "
        "hay horas de baja demanda y pocas horas muy cargadas, no un comportamiento parejo.\n"
        f"- El usuario registrado concentra **{num(usuarios.loc['Registrado', 'participacion_pct'], 1)} %** de las rentas: "
        "es un servicio de movilidad cotidiana más que de uso recreativo.\n"
        "- La lectura es **descriptiva y comparativa**: no se atribuyen causas ni se predicen valores futuros."
    )

# ---------------------------------------------------------------------------
# Preguntas
# ---------------------------------------------------------------------------
else:
    p = preguntas[indice]
    st.markdown(f"### {p['pregunta']}")
    st.caption(f"Métrica: {p['metrica']} · Unidad: {p['unidad']} · Periodo: {periodo}")

    # --- P1: volumen y reparto del día -------------------------------------
    if p["id"] == "p1":
        hora = m.por_hora(df)
        maximo = hora.loc[hora["promedio"].idxmax()]
        minimo = hora.loc[hora["promedio"].idxmin()]

        c1, c2, c3 = st.columns(3)
        c1.markdown(tarjeta("Rentas totales", num(k["rentas"]), "rentas en el periodo"), unsafe_allow_html=True)
        c2.markdown(tarjeta("Hora más cargada", f"{int(maximo['hr'])}:00", f"{num(maximo['promedio'], 1)} rentas/hora"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Hora más floja", f"{int(minimo['hr'])}:00", f"{num(minimo['promedio'], 1)} rentas/hora"), unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=hora["hr"], y=hora["rentas"], name="Rentas acumuladas", marker_color="#D9E4E7",
                   hovertemplate="Hora %{x}:00<br>%{y:,.0f} rentas en total<extra></extra>")
        )
        fig.add_trace(
            go.Scatter(x=hora["hr"], y=hora["promedio"], name="Promedio por hora", yaxis="y2",
                       line=dict(color=AZUL, width=3), mode="lines+markers", marker=dict(size=5),
                       hovertemplate="Hora %{x}:00<br>%{y:,.1f} rentas/hora<extra></extra>")
        )
        fig.update_layout(
            title="Rentas acumuladas y promedio por hora",
            yaxis=dict(title="Rentas acumuladas (conteo)", tickformat=",.0f", gridcolor="#EDE8DD"),
            yaxis2=dict(title="Rentas por hora (promedio)", overlaying="y", side="right", showgrid=False, tickformat=",.0f"),
        )
        estilo(fig, alto=420, titulo_x="Hora del día")
        st.plotly_chart(fig)

        caja("respuesta", "Qué muestran los datos",
             f"En {num(k['dias'])} días se registraron {num(k['rentas'])} rentas, con un promedio de "
             f"{num(k['promedio'], 1)} por hora y una mediana de {num(k['mediana'])}. El promedio supera la mediana, "
             f"señal de una distribución con horas muy cargadas: la más alta es las {int(maximo['hr'])}:00 con "
             f"{num(maximo['promedio'], 1)} rentas/hora, y la más baja las {int(minimo['hr'])}:00 con {num(minimo['promedio'], 1)}.")
        caja("decision", "Decisión que puede apoyar",
             "Dimensionar la flota y los turnos por hora en lugar de por día: la operación necesita más bicicletas "
             "disponibles en la hora pico y puede programar el mantenimiento en la madrugada.")
        caja("limite", "Limitación",
             "El dataset no trae la capacidad instalada ni la demanda insatisfecha (viajes que no ocurrieron por falta "
             "de bicicleta), así que el conteo describe lo que se usó, no lo que se pudo haber usado.")

    # --- P2: franjas horarias ---------------------------------------------
    elif p["id"] == "p2":
        franjas = m.por_franja(df)
        top = franjas.loc[franjas["participacion_pct"].idxmax()]
        pico = franjas[franjas["franja_horaria"].isin(["Pico mañana", "Pico tarde"])]["participacion_pct"].sum()

        c1, c2, c3 = st.columns(3)
        c1.markdown(tarjeta("Franja con más demanda", top["franja_horaria"], f"{num(top['participacion_pct'], 1)} % de las rentas"), unsafe_allow_html=True)
        c2.markdown(tarjeta("Peso de las horas pico", f"{num(pico, 1)} %", "pico mañana + pico tarde"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Veces el promedio", num(top["veces_promedio"], 1), "frente a la hora promedio"), unsafe_allow_html=True)

        colores = [TERRACOTA if f in ("Pico mañana", "Pico tarde") else AZUL_CLARO for f in franjas["franja_horaria"]]
        fig = go.Figure(
            go.Bar(
                x=franjas["participacion_pct"], y=franjas["franja_horaria"], orientation="h", marker_color=colores,
                text=[f"{num(p, 1)} %" for p in franjas["participacion_pct"]], textposition="outside",
                customdata=franjas["promedio"],
                hovertemplate="%{y}<br>%{x:,.1f} % del total<br>%{customdata:,.1f} rentas/hora<extra></extra>",
            )
        )
        fig.update_layout(title="Participación de cada franja horaria (naranja = horas pico)", showlegend=False)
        estilo(fig, alto=400, titulo_x="Participación del total (%)")
        st.plotly_chart(fig)

        with st.expander("Ver la tabla de la franja horaria"):
            tabla = franjas.copy()
            tabla["participacion_pct"] = tabla["participacion_pct"].round(1)
            tabla["promedio"] = tabla["promedio"].round(1)
            tabla["veces_promedio"] = tabla["veces_promedio"].round(2)
            tabla.columns = ["Franja", "Horas", "Rentas", "Promedio (rentas/hora)", "Mediana", "Participación (%)", "Veces el promedio"]
            st.dataframe(tabla, hide_index=True)

        caja("respuesta", "Qué muestran los datos",
             f"La demanda se concentra en la tarde: **{top['franja_horaria']}** aporta {num(top['participacion_pct'], 1)} % "
             f"de las rentas ({num(top['promedio'], 1)} rentas/hora, {num(top['veces_promedio'], 1)} veces el promedio), "
             f"mientras la madrugada aporta {num(franjas.loc[franjas['franja_horaria'] == 'Madrugada', 'participacion_pct'].squeeze(), 1)} %. "
             f"Sumando las dos horas pico, la operación atiende {num(pico, 1)} % de la demanda.")
        caja("decision", "Decisión que puede apoyar",
             "Concentrar el personal de reubicación de bicicletas entre las 16:00 y las 19:00 y dejar la madrugada "
             "para mantenimiento y recarga de estaciones.")
        caja("limite", "Limitación",
             "Las franjas son cortes definidos en el proyecto (0-5, 6-8, 9-11, 12-15, 16-19, 20-23 h); otro corte "
             "mueve los porcentajes. La franja agrupa horas y oculta diferencias internas, que se ven en la pregunta 1.")

    # --- P3: tipo de día ---------------------------------------------------
    elif p["id"] == "p3":
        tipo = m.por_tipo_dia(df)
        perfil = m.perfil_horario_por(df, "tipo_dia")
        laborable = tipo[tipo["tipo_dia"] == "Laborable"]
        no_lab = tipo[tipo["tipo_dia"] == "No laborable"]

        c1, c2, c3 = st.columns(3)
        if not laborable.empty:
            c1.markdown(tarjeta("Laborable · promedio", num(laborable["promedio"].iloc[0], 1), "rentas/hora"), unsafe_allow_html=True)
        if not no_lab.empty:
            c2.markdown(tarjeta("No laborable · promedio", num(no_lab["promedio"].iloc[0], 1), "rentas/hora"), unsafe_allow_html=True)
        if not no_lab.empty:
            c3.markdown(tarjeta("Ocasional en no laborable", f"{num(no_lab['pct_casual'].iloc[0], 1)} %", "del total de ese tipo de día"), unsafe_allow_html=True)

        izq, der = st.columns(2)
        with izq:
            fig = go.Figure(
                go.Bar(x=tipo["tipo_dia"], y=tipo["promedio"], marker_color=[COLORES_TIPO.get(t, AZUL) for t in tipo["tipo_dia"]],
                       text=[num(v, 1) for v in tipo["promedio"]], textposition="outside",
                       hovertemplate="%{x}<br>%{y:,.1f} rentas/hora<extra></extra>")
            )
            fig.update_layout(title="Promedio de rentas por hora", showlegend=False)
            estilo(fig, alto=360, titulo_y="Rentas por hora")
            st.plotly_chart(fig)
        with der:
            fig = go.Figure(
                go.Bar(x=tipo["tipo_dia"], y=tipo["pct_casual"], marker_color=[COLORES_TIPO.get(t, TERRACOTA) for t in tipo["tipo_dia"]],
                       text=[f"{num(v, 1)} %" for v in tipo["pct_casual"]], textposition="outside",
                       hovertemplate="%{x}<br>%{y:,.1f} % de las rentas son ocasionales<extra></extra>")
            )
            fig.update_layout(title="Peso del usuario ocasional", showlegend=False)
            estilo(fig, alto=360, titulo_y="% de rentas ocasionales")
            st.plotly_chart(fig)

        fig = go.Figure()
        for col in perfil.columns:
            fig.add_trace(
                go.Scatter(x=perfil.index, y=perfil[col], mode="lines+markers", name=str(col),
                           line=dict(color=COLORES_TIPO.get(str(col), AZUL), width=3), marker=dict(size=5),
                           hovertemplate=f"{col} · hora %{{x}}:00<br>%{{y:,.1f}} rentas/hora<extra></extra>")
            )
        fig.update_layout(title="Perfil horario: dónde se separan los dos tipos de día")
        estilo(fig, alto=400, titulo_x="Hora del día", titulo_y="Rentas por hora (promedio)")
        st.plotly_chart(fig)

        if not laborable.empty and not no_lab.empty:
            caja("respuesta", "Qué muestran los datos",
                 f"El promedio por hora es mayor en día laborable ({num(laborable['promedio'].iloc[0], 1)}) que en no laborable "
                 f"({num(no_lab['promedio'].iloc[0], 1)}), pero la diferencia grande está en el **perfil**: el día laborable "
                 f"tiene dos picos marcados (mañana y tarde, movilidad casa–trabajo) y el no laborable una curva más plana y "
                 f"corrida hacia el mediodía. Además, el usuario ocasional pasa de {num(laborable['pct_casual'].iloc[0], 1)} % "
                 f"a {num(no_lab['pct_casual'].iloc[0], 1)} % del total del día.")
            caja("decision", "Decisión que puede apoyar",
                 "Programar reubicación y personal por tipo de día: refuerzo en horas pico de lunes a viernes y cobertura "
                 "continua el fin de semana, cuando el uso es más recreativo y más disperso.")
            caja("limite", "Limitación",
                 "La clasificación viene de las variables `workingday` y `holiday` del dataset original: agrupa festivos y "
                 "fines de semana en una sola categoría, así que no distingue un sábado de un festivo en martes.")

    # --- P4: temporada y año ----------------------------------------------
    elif p["id"] == "p4":
        temp = m.por_temporada(df)
        anios = m.por_anio(df)
        cruce = m.temporada_por_anio(df)
        mejor = temp.loc[temp["promedio"].idxmax()]

        c1, c2, c3 = st.columns(3)
        c1.markdown(tarjeta("Temporada más fuerte", mejor["temporada"], f"{num(mejor['promedio'], 1)} rentas/hora"), unsafe_allow_html=True)
        if len(anios) == 2:
            crec = 100 * (anios["promedio"].iloc[-1] / anios["promedio"].iloc[0] - 1)
            c2.markdown(tarjeta("Crecimiento 2011 → 2012", f"{num(crec, 1)} %", "en promedio por hora"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Rentas por temporada", num(temp["rentas"].sum()), "rentas en el periodo filtrado"), unsafe_allow_html=True)

        izq, der = st.columns(2)
        with izq:
            fig = go.Figure(
                go.Bar(x=temp["temporada"], y=temp["promedio"], marker_color=[AZUL if t == mejor["temporada"] else AZUL_CLARO for t in temp["temporada"]],
                       text=[num(v, 1) for v in temp["promedio"]], textposition="outside",
                       hovertemplate="%{x}<br>%{y:,.1f} rentas/hora<extra></extra>")
            )
            fig.update_layout(title="Promedio por temporada", showlegend=False)
            estilo(fig, alto=360, titulo_y="Rentas por hora")
            st.plotly_chart(fig)
        with der:
            fig = go.Figure()
            for anio in sorted(anios["anio"].unique()):
                datos_anio = cruce.set_index("temporada")[anio] if anio in cruce.columns else pd.Series(dtype=float)
                fig.add_trace(
                    go.Bar(x=cruce["temporada"], y=datos_anio, name=str(anio),
                           marker_color=AZUL_CLARO if anio == min(anios["anio"]) else AZUL,
                           hovertemplate=f"{anio} · %{{x}}<br>%{{y:,.1f}} rentas/hora<extra></extra>")
                )
            fig.update_layout(title="Promedio por temporada y año", barmode="group")
            estilo(fig, alto=360, titulo_y="Rentas por hora")
            st.plotly_chart(fig)

        with st.expander("Ver la variación porcentual por temporada"):
            tabla = cruce.copy()
            tabla.columns = ["Temporada"] + [
                f"Promedio {c}" if not str(c).startswith("variacion") else "Variación 2011→2012 (%)"
                for c in tabla.columns[1:]
            ]
            st.dataframe(tabla.round(1), hide_index=True)

        caja("respuesta", "Qué muestran los datos",
             f"La temporada más fuerte es **{mejor['temporada']}** con {num(mejor['promedio'], 1)} rentas/hora y la más floja "
             f"{temp.loc[temp['promedio'].idxmin(), 'temporada']} con {num(temp['promedio'].min(), 1)}. El promedio por hora "
             f"creció {num(100 * (anios['promedio'].iloc[-1] / anios['promedio'].iloc[0] - 1), 1)} % entre 2011 y 2012, y el "
             "crecimiento se repite en las cuatro temporadas: es aumento del sistema, no un efecto de una sola estación."
             if len(anios) == 2 else
             f"La temporada más fuerte es **{mejor['temporada']}** con {num(mejor['promedio'], 1)} rentas/hora y la más floja "
             f"{temp.loc[temp['promedio'].idxmin(), 'temporada']} con {num(temp['promedio'].min(), 1)}.")
        caja("decision", "Decisión que puede apoyar",
             "Planear la compra y el mantenimiento de la flota con la estacionalidad: reforzar capacidad antes de la "
             "temporada alta y usar la baja para renovar equipos, y no leer el crecimiento como demanda de un día puntual.")
        caja("limite", "Limitación",
             "Son solo dos años y cuatro temporadas por año: describen un patrón, no una serie suficiente para proyectar. "
             "Comparar temporadas mezcla además crecimiento, clima y cambios de la ciudad.")

    # --- P5: clima y temperatura -------------------------------------------
    elif p["id"] == "p5":
        clima = m.por_clima(df)
        rango = m.por_rango_temperatura(df)
        despejado = clima[clima["clima"] == "Despejado"]
        lluvia = clima[clima["clima"].str.contains("Lluvia", case=False, na=False)]
        caida = None

        c1, c2, c3 = st.columns(3)
        if not despejado.empty:
            c1.markdown(tarjeta("Clima despejado", num(despejado["promedio"].iloc[0], 1), "rentas/hora"), unsafe_allow_html=True)
        if not lluvia.empty:
            peor = lluvia.loc[lluvia["promedio"].idxmin()]
            c2.markdown(tarjeta("Con lluvia", num(peor["promedio"], 1), f"rentas/hora · {peor['clima']}"), unsafe_allow_html=True)
        if not despejado.empty and not lluvia.empty:
            caida = 100 * (1 - lluvia["promedio"].min() / despejado["promedio"].iloc[0])
            c3.markdown(tarjeta("Caída frente a despejado", f"{num(caida, 1)} %", "en promedio por hora"), unsafe_allow_html=True)

        izq, der = st.columns(2)
        with izq:
            fig = go.Figure(
                go.Bar(x=clima["promedio"], y=clima["clima"], orientation="h",
                       marker_color=[AZUL if c == "Despejado" else (TERRACOTA if "Lluvia" in c else AZUL_CLARO) for c in clima["clima"]],
                       text=[num(v, 1) for v in clima["promedio"]], textposition="outside",
                       hovertemplate="%{y}<br>%{x:,.1f} rentas/hora<extra></extra>")
            )
            fig.update_layout(title="Promedio por condición climática", showlegend=False)
            estilo(fig, alto=380, titulo_x="Rentas por hora")
            st.plotly_chart(fig)
        with der:
            fig = go.Figure(
                go.Scatter(x=rango["rango_temperatura"], y=rango["promedio"], mode="lines+markers+text",
                           text=[num(v, 1) for v in rango["promedio"]], textposition="top center",
                           line=dict(color=TERRACOTA, width=3), marker=dict(size=9),
                           hovertemplate="%{x}<br>%{y:,.1f} rentas/hora<extra></extra>")
            )
            fig.update_layout(title="Promedio por rango de temperatura", showlegend=False)
            estilo(fig, alto=380, titulo_y="Rentas por hora")
            st.plotly_chart(fig)

        with st.expander("Ver tabla de clima y temperatura"):
            t1 = clima.copy()
            t1.columns = ["Clima", "Horas", "Rentas", "Promedio (rentas/hora)", "Mediana", "Participación (%)"]
            st.dataframe(t1.round(1), hide_index=True)
            t2 = rango.copy()
            t2.columns = ["Rango de temperatura", "Horas", "Rentas", "Promedio (rentas/hora)", "Mediana", "Participación (%)"]
            st.dataframe(t2.round(1), hide_index=True)

        if not despejado.empty and not lluvia.empty:
            caja("respuesta", "Qué muestran los datos",
                 f"Con cielo despejado se promedian {num(despejado['promedio'].iloc[0], 1)} rentas/hora; con lluvia o nieve "
                 f"ligera bajan a {num(clima[clima['clima'] == 'Lluvia o nieve ligera']['promedio'].squeeze(), 1) if (clima['clima'] == 'Lluvia o nieve ligera').any() else 'sin datos'}, "
                 f"una caída de {num(caida, 1)} %. La temperatura acompaña el mismo patrón: la demanda sube al pasar de frío a "
                 "templado y se mantiene alta en los rangos cálidos.")
            caja("decision", "Decisión que puede apoyar",
                 "Ajustar la operación al pronóstico: en días de lluvia conviene reducir la reubicación hacia zonas de oficinas "
                 "y reforzar estaciones cercanas a transporte público, donde el viaje de última milla se vuelve más necesario.")
            caja("limite", "Limitación",
                 "La relación es descriptiva y no causal: el clima se registró junto con la demanda, pero también cambian la "
                 "estación y el día. La categoría de lluvia fuerte o tormenta tiene muy pocas horas (3), así que su promedio "
                 "no es representativo.")

    # --- P6: casuales vs. registrados -------------------------------------
    elif p["id"] == "p6":
        usuarios = m.por_tipo_usuario(df).set_index("tipo_usuario")
        por_dia = m.usuarios_por_tipo_dia(df)
        perfil = m.perfil_horario_por(df, "tipo_dia")

        c1, c2, c3 = st.columns(3)
        c1.markdown(tarjeta("Registrados", f"{num(usuarios.loc['Registrado', 'participacion_pct'], 1)} %", f"{num(usuarios.loc['Registrado', 'rentas'])} rentas"), unsafe_allow_html=True)
        c2.markdown(tarjeta("Casuales", f"{num(usuarios.loc['Casual', 'participacion_pct'], 1)} %", f"{num(usuarios.loc['Casual', 'rentas'])} rentas"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Ocasional en fin de semana", f"{num(por_dia.loc[por_dia['tipo_dia'] == 'No laborable', 'pct_casual'].squeeze(), 1) if (por_dia['tipo_dia'] == 'No laborable').any() else 'sin datos'} %", "frente al laborable"), unsafe_allow_html=True)

        izq, der = st.columns([2, 3])
        with izq:
            fig = go.Figure(
                go.Pie(labels=usuarios.index, values=usuarios["rentas"], hole=0.62,
                       marker=dict(colors=[COLORES_USUARIO.get(x, AZUL) for x in usuarios.index]),
                       textinfo="label+percent", textfont_size=13,
                       hovertemplate="%{label}<br>%{value:,.0f} rentas (%{percent})<extra></extra>")
            )
            fig.update_layout(title="Participación sobre el total de rentas", showlegend=False)
            estilo(fig, alto=380)
            st.plotly_chart(fig)
        with der:
            perfil_usuarios = df.pivot_table(index="hr", values=["casual", "registered"], aggfunc="mean").reindex(range(24))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perfil_usuarios.index, y=perfil_usuarios["registered"], name="Registrado",
                                     line=dict(color=AZUL, width=3), mode="lines+markers", marker=dict(size=5),
                                     hovertemplate="Hora %{x}:00<br>%{y:,.1f} rentas/hora<extra></extra>"))
            fig.add_trace(go.Scatter(x=perfil_usuarios.index, y=perfil_usuarios["casual"], name="Casual",
                                     line=dict(color=TERRACOTA, width=3), mode="lines+markers", marker=dict(size=5),
                                     hovertemplate="Hora %{x}:00<br>%{y:,.1f} rentas/hora<extra></extra>"))
            fig.update_layout(title="Perfil horario de cada tipo de usuario")
            estilo(fig, alto=380, titulo_x="Hora del día", titulo_y="Rentas por hora (promedio)")
            st.plotly_chart(fig)

        with st.expander("Ver peso de cada tipo de usuario por tipo de día"):
            tabla = por_dia.copy()
            for c in ("pct_casual", "pct_registrado"):
                tabla[c] = tabla[c].round(1)
            tabla.columns = ["Tipo de día", "Rentas casuales", "Rentas registradas", "Total", "% casual", "% registrado"]
            st.dataframe(tabla, hide_index=True)

        casual_lab = por_dia.loc[por_dia["tipo_dia"] == "Laborable", "pct_casual"]
        casual_fin = por_dia.loc[por_dia["tipo_dia"] == "No laborable", "pct_casual"]
        caja("respuesta", "Qué muestran los datos",
             f"El usuario registrado concentra {num(usuarios.loc['Registrado', 'participacion_pct'], 1)} % de las rentas frente a "
             f"{num(usuarios.loc['Casual', 'participacion_pct'], 1)} % del ocasional. Los perfiles horarios son distintos: el registrado "
             "marca los picos de entrada y salida del trabajo, mientras el casual se reparte hacia el mediodía y la tarde. "
             + (f"El peso del casual sube de {num(casual_lab.squeeze(), 1)} % en laborable a {num(casual_fin.squeeze(), 1)} % en no laborable."
                if not casual_lab.empty and not casual_fin.empty else ""))
        caja("decision", "Decisión que puede apoyar",
             "Dos estrategias distintas: para el registrado, garantizar disponibilidad en horas pico (servicio de movilidad); "
             "para el casual, promociones y estaciones en zonas turísticas o de esparcimiento los fines de semana.")
        caja("limite", "Limitación",
             "El dataset no identifica usuarios únicos: 'registrado' y 'casual' son tipos de renta, no personas. No se puede "
             "afirmar cuántos clientes distintos hay ni su frecuencia.")

# ---------------------------------------------------------------------------
# Pie de página
# ---------------------------------------------------------------------------
st.divider()
st.markdown(
    '<p class="pie">Proyecto Integrado III — Analítica de Datos · AE_Grupo 3: Carlos Andrés Osorio Agudelo, '
    "Estefanía Martínez Guzmán y Valentina Pérez Flórez · Docente: Andrés Felipe Callejas Jaramillo · "
    "Institución Universitaria Digital de Antioquia · Fuente: UCI Machine Learning Repository, Bike Sharing Dataset "
    "(id 275), vía Hugging Face <code>t22000t/bike-sharing-tabular</code>.</p>",
    unsafe_allow_html=True,
)
