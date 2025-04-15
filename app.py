import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Fondos de Inversión", layout="centered")
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

st.title("💼 Evolución de Fondos de Inversión")
st.markdown("""
Consulta la evolución de tus fondos y visualiza el rendimiento acumulado con estimaciones actualizadas.
""")

# Función para buscar precio actual según ISIN
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

# Enlace de Google Drive (enlace directo de descarga)
url = 'https://drive.google.com/uc?export=download&id=1DID_ABC12345'  # Cambia este ID por el tuyo

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
fondo_seleccionado = st.selectbox("🎯 Seleccioná un fondo", fondos_disponibles)

# Filtrar datos por fondo
datos = df[df['Fondo'] == fondo_seleccionado].copy()

# Ordenar los datos por fecha de más reciente a más antigua (se cambió ascending=False)
datos.sort_values('Fecha', ascending=False, inplace=True)

# Formatear la columna 'Fecha' a un formato legible
datos['Fecha'] = datos['Fecha'].dt.strftime('%d/%m/%Y')

# Mostrar tabla con solo las columnas deseadas
st.subheader("🔍 Vista previa de los datos del fondo seleccionado")

# Asegúrate de que 'Valor Compra' esté en formato numérico antes de las operaciones
datos['Valor Compra'] = pd.to_numeric(datos['Valor Compra'], errors='coerce')

# Eliminar columna redundante "Fecha Formateada" y renombrar
datos = datos.drop(columns=["Fecha Formateada"])

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
else:
    datos['Estimación Acumulada'] = None
    datos['Rendimiento (%)'] = None

# Función de color condicional para el rendimiento
def color_rendimiento(val):
    try:
        # Convertir el valor a float para evitar errores de tipo
        val = float(val)
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    except ValueError:
        return 'color: black'  # Si no es un número, mostrar en negro

# Redondear la columna de rendimiento a 2 decimales y formatear la tabla
datos['Rendimiento (%)'] = datos['Rendimiento (%)'].apply(lambda x: f'{x:.2f}' if pd.notnull(x) else x)

# Formatear 'Valor Compra' para mostrar dos decimales, pero sin cambiar su tipo
datos['Valor Compra'] = datos['Valor Compra'].apply(lambda x: f"{x:.2f}")

# Mostrar la tabla con los valores redondeados, color condicional y centrado
st.dataframe(datos[['Fecha', 'Dinero Inv.', 'Valor Compra', 'Rendimiento (%)']].style.applymap(color_rendimiento, subset=['Rendimiento (%)']).set_properties(**{'text-align': 'center'}), use_container_width=True, height=300, hide_index=True)

# Asegurar que 'Valor Compra' sea numérico (por si fue formateado como string)
datos['Valor Compra'] = pd.to_numeric(datos['Valor Compra'], errors='coerce')

# Crear una columna de fechas reales para ordenar y graficar correctamente
datos['Fecha_dt'] = pd.to_datetime(datos['Fecha'], format='%d/%m/%Y')
datos.sort_values('Fecha_dt', inplace=True)

# Gráfico de valor de compra
st.subheader("📈 Evolución del valor de compra")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=datos['Fecha_dt'], y=datos['Valor Compra'],
    mode='lines+markers', name='Valor Compra', line=dict(color='teal')
))
fig1.update_layout(
    title=f"Valor de Compra - {fondo_seleccionado}",
    xaxis_title="Fecha",
    yaxis_title="Valor",
    template="plotly_white",
    yaxis=dict(tickformat=".2f")  # Formato del eje Y con 2 decimales
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
        title=f"Inversión vs Estimación - {fondo_seleccionado}",
        xaxis_title="Fecha", yaxis_title="Euros", template="plotly_white",
        xaxis=dict(showgrid=True), yaxis=dict(showgrid=True),
        plot_bgcolor="rgba(245, 247, 250, 1)"
    )

    st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("💶 Precio actual", f"{precio_actual:.2f} €")
    with col2:
        st.metric("📌 Valor estimado", f"{datos['Valor Actual Estimado'].iloc[-1]:.2f} €")
else:
    st.warning("⚠️ No se pudo obtener el precio actual de este fondo.")
