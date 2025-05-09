
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Fondos de Inversión2", layout="wide")
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

st.markdown("<h1 style='text-align: center; color: #2c3e50; font-size: 36px;'>💼 Evolución de la Inversión</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50; font-size: 20px;'>Consulta la evolución de tus fondos y visualiza el rendimiento acumulado con estimaciones actualizadas.</h1>", unsafe_allow_html=True)

# Función para obtener el precio actual según ISIN
def obtener_precio_actual(isin):
    try:
        if isin == "IE00BYX5NX33":
            website = 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00001019E'
        elif isin == "LU1213836080":
            website = 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00000VKNA'
        else:
            return None

        result = requests.get(website)
        content = result.text
        soup = BeautifulSoup(content, 'lxml')
        box = soup.find('td', class_='line text')
        if box:
            valor = str(box)[26:31].replace(",", ".")
            return round(float(valor), 2)
        return None
    except:
        return None


def obtener_fecha_actual(isin):
    try:
        if isin == "IE00BYX5NX33":
            website = 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00001019E'
        elif isin == "LU1213836080":
            website = 'https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=F00000VKNA'
        else:
            return None

        result = requests.get(website)
        content = result.text
        soup = BeautifulSoup(content, 'lxml')
        box = soup.find('td', class_='line heading')
        if box:
            valor = box.text.strip()
            return str(box.text.strip()[3:])
        return None
    except:
        return None

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
isin_map = {
    "MSCI World": "IE00BYX5NX33",
    "Global Technology": "LU1213836080"
}
isin = isin_map.get(fondo_seleccionado.strip(), None)
precio_actual = obtener_precio_actual(isin) if isin else None

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
valor_estimado_total = datos['Valor Actual Estimado'].sum()

# Calcular el precio medio de compra ponderado
precio_medio_compra = (datos['Valor Compra'] * datos['Dinero Inv.']).sum() / total_invertido

# Crear columnas de métricas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💶 Precio actual con fecha:  "+obtener_fecha_actual(isin), f"{precio_actual:.2f} €")
with col2:
    st.metric("📊 Precio medio compra", f"{precio_medio_compra:.2f} €")
with col3:
    st.metric("📥 Total aportado", f"{total_invertido:.2f} €")
with col4:
    st.metric("📌 Valor estimado", f"{valor_estimado_total:.2f} €")

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

