import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Estilo para replicar el dashboard oscuro tipo imagen de referencia
st.markdown(
    """
    <style>
    .stApp {
        background: #050b12;
        color: #e5e7eb;
    }

    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 0.75rem 1rem 0.9rem 1rem;
        min-height: 150px;
        box-shadow: none;
    }

    div[data-testid="stMetric"] > label {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #e5e7eb !important;
        padding-bottom: 0.35rem;
    }

    div[data-testid="stMetric"] > div {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    div[data-testid="stMetric"] > div > div {
        font-size: clamp(2rem, 2.3vw, 3rem) !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        line-height: 1.1;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        display: none;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    h1 {
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título del Dashboard
st.title("📈 Dashboard de Análisis de Ventas e Ingresos")
st.markdown("---")


# Función para cargar datos de manera optimizada
@st.cache_data
def load_data():
  # Apunta al archivo local dentro del repositorio de GitHub
  file_path = "SalidaVentas.xlsx"
  df = pd.read_excel(file_path)
  df["Order Date"] = pd.to_datetime(df["Order Date"])
  df["es devolución?"] = (
      df["es devolución?"].astype(str).str.lower().str.strip()
  )
  return df


try:
  df = load_data()
except Exception as e:
  st.error(f"Error al cargar los datos: {e}")
  st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Datos")

# Filtro de Fecha
min_date = df["Order Date"].min().to_pydatetime()
max_date = df["Order Date"].max().to_pydatetime()
start_date, end_date = st.sidebar.slider(
    "Selecciona el rango de fechas:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
)

# Filtro de Región
regiones = sorted(df["Region"].unique())
regiones_selected = st.sidebar.multiselect(
    "Selecciona la(s) Región(es):", options=regiones, default=regiones
)

# Filtro de Estado (Dinámico según Región)
df_filtrado = df[
    (df["Order Date"] >= start_date)
    & (df["Order Date"] <= end_date)
    & (df["Region"].isin(regiones_selected))
]

estados = sorted(df_filtrado["State"].unique())
estados_selected = st.sidebar.multiselect(
    "Selecciona el/los Estado(s):", options=estados, default=estados
)

# Aplicar filtro final de Estado
df_filtrado = df_filtrado[df_filtrado["State"].isin(estados_selected)]

# --- MÉTRICAS CLAVE (KPIs) ---
if not df_filtrado.empty:
  total_sales = df_filtrado["Sales"].sum()
  total_profit = df_filtrado["Profit"].sum()
  avg_margin = (
      (total_profit / total_sales * 100) if total_sales > 0 else 0
  )
  total_orders = df_filtrado["Order ID-1"].nunique()

  # Tasa de devolución
devueltos = df_filtrado[df_filtrado["es devolución?"] == "sí"].shape[0]
  tasa_devolucion = (
      (devueltos / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
  )

  col1, col2, col3, col4, col5 = st.columns(5)
  col1.metric("Ventas Totales", f"${total_sales:,.2f}")
  col2.metric("Ganancias Totales", f"${total_profit:,.2f}")
  col3.metric("Margen de Ganancia", f"{avg_margin:.2f}%")
  col4.metric("Órdenes Únicas", f"{total_orders:,}")
  col5.metric("Tasa Devolución", f"{tasa_devolucion:.2f}%")
else:
  st.warning("No hay datos que coincidan con los filtros seleccionados.")
  st.stop()

st.markdown("---")

# --- GRÁFICOS ---
col_left, col_right = st.columns(2)

with col_left:
  st.subheader("Evolución de Ventas en el Tiempo")
  # CORRECCIÓN: Se cambió 'M' por 'ME' para compatibilidad con versiones recientes de Pandas
  df_trend = (
      df_filtrado.resample("ME", on="Order Date")[["Sales", "Profit"]]
      .sum()
      .reset_index()
  )
  fig_trend = px.line(
      df_trend,
      x="Order Date",
      y=["Sales", "Profit"],
      labels={"value": "Monto ($)", "Order Date": "Fecha"},
      title="Tendencia Mensual de Ventas y Ganancias",
      color_discrete_sequence=["royalblue", "forestgreen"],
  )
  st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
  st.subheader("Relación de Ventas vs Ganancia por Transacción")
  fig_scatter = px.scatter(
      df_filtrado,
      x="Sales",
      y="Profit",
      color="Category",
      hover_data=["Customer Name", "State"],
      title="Dispersión: Sales vs Profit por Categoría",
      labels={"Sales": "Ventas ($)", "Profit": "Ganancias ($)"},
      opacity=0.6,
  )
  st.plotly_chart(fig_scatter, use_container_width=True)

col_bottom1, col_bottom2 = st.columns(2)

with col_bottom1:
  st.subheader("Ventas por Estado")
  df_state = (
      df_filtrado.groupby("State")["Sales"]
      .sum()
      .reset_index()
      .sort_values(by="Sales", ascending=False)
      .head(10)
  )
  fig_state = px.bar(
      df_state,
      x="Sales",
      y="State",
      orientation="h",
      title="Top 10 Estados con más Ventas",
      labels={"Sales": "Total Ventas ($)", "State": "Estado"},
      color="Sales",
      color_continuous_scale="Blues",
  )
  st.plotly_chart(fig_state, use_container_width=True)

with col_bottom2:
  st.subheader("Ventas por Categoría y Sub-Categoría")
  fig_sunburst = px.sunburst(
      df_filtrado,
      path=["Category", "Sub-Category"],
      values="Sales",
      title="Distribución de Ventas por Categorías",
      color="Sales",
      color_continuous_scale="YlOrRd",
  )
  st.plotly_chart(fig_sunburst, use_container_width=True)
