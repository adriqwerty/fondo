import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px
import re
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Fondos de Inversión3", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #2c3e50; font-size: 36px;'>💼 Evolución de la Inversión2</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50; font-size: 20px;'>Consulta la evolución de tus fondos y visualiza el rendimiento acumulado con estimaciones actualizadas.</h1>", unsafe_allow_html=True)
def obtener_url_alternativa(isin):
    urls = {
        "IE00BYX5NX33": "https://markets.ft.com/data/funds/tearsheet/historical?s=IE00BYX5NX33:EUR",
        "LU1213836080": "https://markets.ft.com/data/funds/tearsheet/historical?s=LU1213836080:EUR",
        "LU0625737910": "https://markets.ft.com/data/funds/tearsheet/historical?s=LU0625737910:EUR",
        "ES0165243025": "https://markets.ft.com/data/funds/tearsheet/historical?s=ES0165243025:EUR"
    }
    return urls.get(isin)
def obtener_url_morningstar(isin):
    urls = {
        "IE00BYX5NX33": 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00001019E',
        "LU1213836080": 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00000VKNA',
        "LU0625737910": 'https://www.morningstar.co.uk/uk/funds/snapshot/snapshot.aspx?id=F00000MO6Y',
        "ES0165243025": 'https://www.morningstar.es/es/funds/snapshot/snapshot.aspx?id=F00001LWDD'
    }
    return urls.get(isin)
def obtener_precio_y_fecha_alt(isin):
    website = obtener_url_alternativa(isin)
    if not website:
        return None, None
    result = requests.get(website)
    soup = BeautifulSoup(result.text, 'lxml')
    precio_box = soup.find('span', class_='mod-ui-data-list__value')
    precio=float(precio_box.text.strip())
    fecha_box = soup.find('div', class_='mod-disclaimer')
    match = re.search(r'as of ([A-Za-z]+ \d{1,2} \d{4})', fecha_box.text.strip())
    fecha_str = match.group(1)
    fecha_obj = datetime.strptime(fecha_str, "%b %d %Y")
    return round(precio, 2) if precio else None, fecha_obj

def obtener_precio_y_fecha_mor(isin):
    website = obtener_url_morningstar(isin)
    if not website:
        return None, None
    try:
        result = requests.get(website)
        soup = BeautifulSoup(result.text, 'lxml')
        precio_box = soup.find('td', class_='line text')
        fecha_box = soup.find('td', class_='line heading')

        if not precio_box or not fecha_box:
            return None, None

        # Obtener precio
        precio_texto = precio_box.text.strip()
        # Extraer el número final (normalmente viene como "EUR 123.45")
        match_precio = re.search(r"(\d+,\d+|\d+\.\d+)$", precio_texto)
        if not match_precio:
            return None, None
        precio = float(match_precio.group(1).replace(",", "."))

        # Obtener fecha
        fecha_texto = fecha_box.text.strip()
        # Extraer fechas válidas (día entre 1 y 31)
        match_fecha = re.search(r"\b([1-9]|[12][0-9]|3[01])/([01][0-9])/(\d{4})\b", fecha_texto)
        if not match_fecha:
            return None, None
        fecha = datetime.strptime(match_fecha.group(0), "%d/%m/%Y")

        return round(precio, 2), fecha
    except Exception as e:
        print(f"Error mor ({isin}): {e}")
        return None, None

@st.cache_data(ttl=3600)
def obtener_precio_y_fecha(isin):
    precio1, fecha1 = obtener_precio_y_fecha_mor(isin)
    precio2, fecha2 = obtener_precio_y_fecha_alt(isin)

    # Casos posibles:
    if fecha1 and fecha2:
        if fecha1 > fecha2:
            return precio1, fecha1
        else:
            return precio2, fecha2
    elif fecha1:
        return precio1, fecha1
    elif fecha2:
        return precio2, fecha2
    else:
        return None, None



# Enlace de Google Drive (enlace directo de descarga)
url = 'https://drive.google.com/uc?export=download&id=18zva1x4v5UCxamu9qbV97EVA6DbZAOzb'  # Cambia este ID por el tuyo

# Descargar el archivo Excel desde Google Drive
response = requests.get(url)

# Verificar si la descarga fue exitosa
if response.status_code == 200:
    # Usar BytesIO para leer el archivo Excel desde la respuesta
    df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
    st.write("¡Archivo cargado correctamente!")
else:
    st.error("Hubo un problema al descargar el archivo desde Google Drive.")
    st.stop()

# Procesamiento de fechas
df['Fecha'] = pd.to_datetime(df['Fecha'])
df['Fecha Formateada'] = df['Fecha'].dt.strftime("%d/%m/%Y")



opcion_seleccionada = st.sidebar.radio(
    "Seleccione una opción:",
    ("Fondo Individual", "Total de la Inversión")
)

isin_map = {
        "MSCI World": "IE00BYX5NX33",
        "Global Technology": "LU1213836080",
        "Pictet China": "LU0625737910",
        "MyInvestor Value":"ES0165243025"
}


if opcion_seleccionada == "Fondo Individual":
    # Fondos disponibles
    fondos_disponibles = df['Fondo'].unique()
    fondo_seleccionado = st.selectbox("🎯 Seleccionar un fondo", fondos_disponibles)

    # Filtrar datos por fondo
    datos = df[df['Fondo'] == fondo_seleccionado].copy()

    # Ordenar los datos por fecha de más reciente a más antigua
    datos.sort_values('Fecha', ascending=False, inplace=True)

    # Formatear la columna 'Fecha' a un formato legible
    datos['Fecha'] = datos['Fecha'].dt.strftime('%d/%m/%Y')

    # Asignar ISIN
    
    isin = isin_map.get(fondo_seleccionado.strip(), None)
    precio_actual, fecha = obtener_precio_y_fecha(isin)

    # Cálculo de rendimiento
    datos['Total Invertido'] = datos['Dinero Inv.'].cumsum()
    if precio_actual:
        datos['Valor Actual Estimado'] = datos['Dinero Inv.'] / datos['Valor Compra'] * precio_actual
        datos['Estimación Acumulada'] = datos['Valor Actual Estimado'].cumsum()

        # Calcular el rendimiento comparado con el precio actual
        datos['Rendimiento (%)'] = ((precio_actual - datos['Valor Compra']) / datos['Valor Compra']) * 100
        # Redondear a 2 decimales
        datos['Rendimiento (%)'] = datos['Rendimiento (%)'].round(2)
        
        # Calcular el valor actual de cada aportación
        datos['Valor Actual'] = (datos['Dinero Inv.'] / datos['Valor Compra']) * precio_actual
    else:
        datos['Estimación Acumulada'] = None
        datos['Rendimiento (%)'] = None
        datos['Valor Actual'] = None

    # Llenar los NaN o None antes de mostrar
    datos['Valor Actual'] = datos['Valor Actual'].fillna('-')
    datos['Rendimiento (%)'] = datos['Rendimiento (%)'].fillna('-')

    # Calcular el precio medio de compra ponderado
    total_invertido = datos['Dinero Inv.'].sum()
    valor_estimado_total = datos['Valor Actual Estimado'].sum() if 'Valor Actual Estimado' in datos.columns else 0

    # Calcular el precio medio de compra ponderado
    precio_medio_compra = (datos['Valor Compra'] * datos['Dinero Inv.']).sum() / total_invertido

    if fecha is None:
        fecha = ""
    else:
        fecha_fin=fecha.date()
        fecha=fecha_fin.strftime("%d de %B de %Y")
    # Crear columnas de métricas
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if precio_actual is not None:
            texto_fecha = f"💶 Precio actual con fecha: {fecha}" if fecha else "💶 Precio actual"
            st.metric(texto_fecha, f"{precio_actual:.2f} €")
        else:
            st.metric("💶 Precio actual", "No disponible")
    with col2:
        st.metric("📊 Precio medio compra", f"{precio_medio_compra:.2f} €")
    with col3:
        st.metric("📥 Total aportado", f"{total_invertido:.2f} €")
    with col4:
        st.metric("💸 Valor estimado", f"{valor_estimado_total:.2f} €")
    with col5:
        st.metric("📌 Diferencia", f"{valor_estimado_total-total_invertido:.2f} €")
    with col6:
        if total_invertido != 0:
            porcentaje = ((valor_estimado_total - total_invertido) / total_invertido) * 100
            st.metric("📈 Rendimiento total (%)", f"{porcentaje:.2f} %")
        else:
            st.metric("📈 Rendimiento total (%)", "N/A")

    # Mostrar tabla con solo las columnas deseadas
    st.subheader("🔍 Datos del fondo seleccionado")

    # Asegúrate de que 'Valor Compra' esté en formato numérico antes de las operaciones
    datos['Valor Compra'] = pd.to_numeric(datos['Valor Compra'], errors='coerce')

    # Eliminar columna redundante "Fecha Formateada" y renombrar
    datos = datos.drop(columns=["Fecha Formateada"])

    # Función para formatear los valores con símbolo de euro y porcentaje
    def formato_decimal_con_simbolos(x, tipo='euro'):
        if isinstance(x, (int, float)):
            if tipo == 'euro':
                return f"{x:.2f} €"  # El símbolo del euro va al final
            elif tipo == 'porcentaje':
                return f"{x:.2f} %"  # El símbolo de porcentaje va al final
        return x

    # Función para colorear el rendimiento
    def color_rendimiento(val):
        try:
            val = float(val)
            if val > 0:
                color = 'green'
            elif val < 0:
                color = 'red'
            else:
                color = 'black'
        except:
            color = 'gray'  # Para valores no numéricos o nulos
        return f'color: {color}'

    # Columnas a mostrar
    columnas_mostrar = ['Fecha', 'Valor Compra', 'Dinero Inv.', 'Valor Actual', 'Rendimiento (%)']

    # Crear objeto Styler solo si hay datos de rendimiento válidos
    if datos['Rendimiento (%)'].ne('-').any():
        styled_df = datos[columnas_mostrar].style \
            .applymap(color_rendimiento, subset=['Rendimiento (%)']) \
            .format({
                'Valor Compra': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Dinero Inv.': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Valor Actual': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Rendimiento (%)': lambda x: formato_decimal_con_simbolos(x, tipo='porcentaje'),
            }) \
            .set_properties(**{'text-align': 'center', 'font-weight': 'bold'})
    else:
        styled_df = datos[columnas_mostrar].style \
            .format({
                'Valor Compra': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Dinero Inv.': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Valor Actual': lambda x: formato_decimal_con_simbolos(x, tipo='euro'),
                'Rendimiento (%)': lambda x: formato_decimal_con_simbolos(x, tipo='porcentaje'),
            }) \
            .set_properties(**{'text-align': 'center', 'font-weight': 'bold'})

    # Mostrar en Streamlit
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=300,
        hide_index=True
    )

    # Crear una columna de fechas reales para ordenar y graficar correctamente
    datos['Fecha_dt'] = pd.to_datetime(datos['Fecha'], format='%d/%m/%Y')
    datos.sort_values('Fecha_dt', inplace=True)

    # Título de la sección del primer gráfico
    st.subheader("📈 Evolución del valor de compra")

    # Gráfico de valor de compra
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=datos['Fecha_dt'], y=datos['Valor Compra'],
        mode='lines+markers', name='Valor Compra', line=dict(color='teal')
    ))
    fig1.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Valor",
        template="plotly_white",
        yaxis=dict(tickformat=".2f"),  # Formato del eje Y con 2 decimales
        height=500,  # Aumentar el tamaño del gráfico
        width=1000  # Aumentar el tamaño del gráfico
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Asegurarse de que la columna 'Fecha' esté en formato datetime antes de ordenar
    datos['Fecha'] = pd.to_datetime(datos['Fecha'], format='%d/%m/%Y')

    # Ordenar los datos por fecha de la más antigua a la más reciente
    datos = datos.sort_values('Fecha')

    # Gráfico comparativo de barras superpuestas sin acumulación
    if precio_actual:
        st.subheader("💰 Inversión vs Estimación por Fecha")
        fig2 = go.Figure()

        # Total invertido (sin acumulación)
        fig2.add_trace(go.Bar(
            x=datos['Fecha'], y=datos['Dinero Inv.'], 
            name="Total Invertido", 
            marker=dict(color="#2c3e50")
        ))

        # Estimación acumulada (sin acumulación)
        fig2.add_trace(go.Bar(
            x=datos['Fecha'], y=datos['Valor Actual Estimado'], 
            name="Valor Estimado Actual", 
            marker=dict(color="#27ae60")
        ))

        fig2.update_layout(
            barmode='group',  # Barras superpuestas
            xaxis_title="Fecha", yaxis_title="Euros", template="plotly_white",
            xaxis=dict(showgrid=True), yaxis=dict(showgrid=True),
            plot_bgcolor="rgba(245, 247, 250, 1)",
            height=500,  # Aumentar el tamaño del gráfico
            width=1000,  # Aumentar el tamaño del gráfico
            legend=dict(
                orientation="h",  # Establecer la orientación horizontal
                yanchor="bottom",  # Posicionar la leyenda debajo del gráfico
                y=-0.2  # Colocar la leyenda un poco debajo
            )
        )

        st.plotly_chart(fig2, use_container_width=True)


elif opcion_seleccionada == "Total de la Inversión":
    st.subheader("📊 Resumen General de la Inversión")

    df['Valor Actual Estimado'] = 0.0  # Inicializar columna
    fecha_ult_actualizacion = None

    for fondo in df['Fondo'].unique():
        isin_fondo = isin_map.get(fondo)
        if not isin_fondo:
            st.warning(f"ISIN no definido para {fondo}")
            continue

        try:
            precio_actual, fecha = obtener_precio_y_fecha(isin_fondo)
            fecha_ult_actualizacion = fecha  # Tomamos la última con éxito
            indices = df[df['Fondo'] == fondo].index
            df.loc[indices, 'Valor Actual Estimado'] = (
                df.loc[indices, 'Dinero Inv.'] / df.loc[indices, 'Valor Compra']
            ) * precio_actual
        except Exception as e:
            st.warning(f"No se pudo obtener el precio de {fondo} ({isin_fondo}): {e}")

    resumen_total = df.groupby('Fondo').agg({
        'Dinero Inv.': 'sum',
        'Valor Actual Estimado': 'sum'
    }).reset_index()

    resumen_total['Rendimiento (%)'] = (
        (resumen_total['Valor Actual Estimado'] - resumen_total['Dinero Inv.']) /
        resumen_total['Dinero Inv.']
    ) * 100
    resumen_total['Rendimiento (%)'] = resumen_total['Rendimiento (%)'].round(2)

    # Mostrar métricas generales
    total_invertido = resumen_total['Dinero Inv.'].sum()
    total_estimado = resumen_total['Valor Actual Estimado'].sum()
    rendimiento_total = (
        ((total_estimado - total_invertido) / total_invertido) * 100
        if total_invertido else 0
    )

    if fecha_ult_actualizacion:
        st.caption(f"🕒 Última actualización de precios: {fecha_ult_actualizacion}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Total Invertido", f"{total_invertido:.2f} €")
    col2.metric("📌 Valor Estimado", f"{total_estimado:.2f} €")
    col3.metric("📌 Diferencia", f"{total_estimado-total_invertido:.2f} €")
    col4.metric("📈 Rendimiento Total", f"{rendimiento_total:.2f} %")
    # Tabla resumen
    st.subheader("📊 Detalle por Fondo")

    def color_total(val):
        try:
            val = float(val)
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
            else:
                return 'color: black'
        except:
            return 'color: gray'

    resumen_total['Precio Medio Compra'] = 0.0  # Inicializar columna
    resumen_total['Precio Actual'] = 0.0  # Inicializar columna

    for fondo in resumen_total['Fondo']:
        isin_fondo = isin_map.get(fondo)
        if not isin_fondo:
            continue
        
        # Filtrar los datos para el fondo actual
        datos_fondo = df[df['Fondo'] == fondo]
        
        # Calcular el precio medio ponderado de compra
        total_invertido_fondo = datos_fondo['Dinero Inv.'].sum()
        valor_compra_ponderado = (datos_fondo['Valor Compra'] * datos_fondo['Dinero Inv.']).sum()
        if total_invertido_fondo != 0:
            precio_medio_compra_fondo = valor_compra_ponderado / total_invertido_fondo
            resumen_total.loc[resumen_total['Fondo'] == fondo, 'Precio Medio Compra'] = precio_medio_compra_fondo

        # Obtener el precio actual
        precio_actual_fondo, _ = obtener_precio_y_fecha(isin_fondo)
        if precio_actual_fondo:
            resumen_total.loc[resumen_total['Fondo'] == fondo, 'Precio Actual'] = precio_actual_fondo

    # Añadir las nuevas métricas a la tabla resumen
    styled_resumen = resumen_total.style \
        .applymap(color_total, subset=['Rendimiento (%)']) \
        .format({
            'Dinero Inv.': lambda x: f"{x:.2f} €",
            'Valor Actual Estimado': lambda x: f"{x:.2f} €",
            'Rendimiento (%)': lambda x: f"{x:.2f} %",
            'Precio Medio Compra': lambda x: f"{x:.2f} €",  # Añadir formato para el precio medio de compra
            'Precio Actual': lambda x: f"{x:.2f} €",  # Añadir formato para el precio actual
        }) \
        .set_properties(**{'text-align': 'center', 'font-weight': 'bold'})

    # Mostrar la tabla
    st.dataframe(styled_resumen, use_container_width=True, hide_index=True)
    fig_rendimiento = px.bar(resumen_total,
                                 x='Fondo',
                                 y='Rendimiento (%)',
                                 color='Rendimiento (%)',
                                 color_continuous_scale='Viridis',  # Escala de colores atractiva
                                 labels={'Rendimiento (%)': 'Rendimiento (%)'},
                                 title="📊 Rendimiento por Fondo",
                                 template="plotly_dark",  # Estilo oscuro para un diseño más moderno
                                 height=500)  # Mejorar el tamaño del gráfico

    # Asegurar formato datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

    # Agrupar por fecha y sumar valores
    df_acumulado = df.groupby('Fecha').agg({
        'Dinero Inv.': 'sum',
        'Valor Actual Estimado': 'sum'
    }).sort_index().cumsum().reset_index()
    fig_acum = px.line(df_acumulado, x='Fecha',
                       y=['Dinero Inv.', 'Valor Actual Estimado'],
                       labels={'value': '€', 'variable': 'Indicador'},
                       title='📈 Evolución Acumulada: Inversión vs Valor Actual')

    fig_acum.update_layout(
        template="plotly_dark",
        xaxis_title="Fecha",
        yaxis_title="Euros (€)",
        legend_title="Indicador",
        showlegend=True
    )

    st.plotly_chart(fig_acum, use_container_width=True)
