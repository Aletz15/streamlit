import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Estilo para replicar el dashboard oscuro tipo mockup
st.markdown(
    """
    <style>
    .stApp {
        background: #050b12;
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    h1 {
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }

    .metric-card {
        background: rgba(11, 18, 30, 0.92);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        min-height: 160px;
        padding: 1.1rem 1.2rem 1.2rem 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
    }

    .metric-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: #e5e7eb;
        margin-bottom: 0.55rem;
        line-height: 1.2;
    }

    .metric-value {
        font-size: clamp(2.1rem, 2.5vw, 3.2rem);
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
        letter-spacing: -0.04em;
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
st.sidebar.header("Filtros de Búsqueda")

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
    "Selecciona Región(es)", options=regiones, default=regiones
)

# Filtro de Estado (Dinámico según Región)
df_filtrado = df[
    (df["Order Date"] >= start_date)
    & (df["Order Date"] <= end_date)
    & (df["Region"].isin(regiones_selected))
]

estados = sorted(df_filtrado["State"].unique())
estados_selected = st.sidebar.multiselect(
    "Selecciona Estado(s)", options=estados, default=estados
)

df_filtrado = df_filtrado[df_filtrado["State"].isin(estados_selected)]

# Filtro de Categoría
categorias = sorted(df_filtrado["Category"].unique())
categorias_selected = st.sidebar.multiselect(
    "Selecciona Categoría(s)", options=categorias, default=categorias
)

df_filtrado = df_filtrado[df_filtrado["Category"].isin(categorias_selected)]

# --- MÉTRICAS CLAVE (KPIs) ---
def metric_card(title, value):
  st.markdown(
      f"""
      <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
      </div>
      """,
      unsafe_allow_html=True,
  )


# Pestañas de navegación
principal_tab, mapa_ventas_tab = st.tabs(["Dashboard", "mapa ventas por estado"])

with principal_tab:
  if not df_filtrado.empty:
    total_sales = df_filtrado["Sales"].sum()
    total_profit = df_filtrado["Profit"].sum()
    total_orders = df_filtrado["Order ID-1"].nunique()

    if "Discount" in df_filtrado.columns:
      avg_discount = df_filtrado["Discount"].mean() * 100
    else:
      avg_discount = 0

    cols = st.columns(4)
    cards = [
        ("Ventas Totales", f"${total_sales:,.2f}"),
        ("Beneficio Total (Profit)", f"${total_profit:,.2f}"),
        ("Descuento Promedio", f"{avg_discount:.2f}%"),
        ("Órdenes Únicas", f"{total_orders:,}"),
    ]

    for col, (title, value) in zip(cols, cards):
        with col:
            metric_card(title, value)
  else:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
    st.stop()

  st.markdown("---")

  # --- GRÁFICOS ---
  col_left, col_right = st.columns(2)

  with col_left:
    st.subheader("Evolución de Ventas en el Tiempo")
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

with mapa_ventas_tab:
  if df_filtrado.empty:
    st.warning("No hay datos para mostrar en el mapa de ventas con los filtros actuales.")
  else:
    state_abbr = {
      "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
      "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
      "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
      "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
      "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
      "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
      "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
      "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
      "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
      "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
      "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
      "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
      "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
    }

    df_state_map = (
        df_filtrado.groupby("State", as_index=False)["Sales"]
        .sum()
        .rename(columns={"State": "Estado", "Sales": "Ventas"})
    )
    df_state_map["Estado"] = df_state_map["Estado"].astype(str)
    df_state_map["State Abbr"] = df_state_map["Estado"].map(state_abbr)
    df_state_map = df_state_map.dropna(subset=["State Abbr"]).sort_values("Ventas", ascending=False)

    if df_state_map.empty:
      st.warning("No hay estados válidos para visualizar en el mapa.")
    else:
      st.subheader("Ventas Totales por Estado")
      fig_map = px.choropleth(
          df_state_map,
          locations="State Abbr",
          locationmode="USA-states",
          color="Ventas",
          scope="usa",
          hover_name="Estado",
          hover_data={"State Abbr": False, "Ventas": ":,.2f"},
          labels={"Ventas": "Ventas"},
          color_continuous_scale="Plasma",
      )
      fig_map.update_layout(
          title=None,
          margin=dict(l=10, r=10, t=10, b=10),
          height=620,
          paper_bgcolor="#f5f5f5",
          geo=dict(bgcolor="#f5f5f5", lakecolor="#f5f5f5", showlakes=False),
      )
      fig_map.update_coloraxes(colorbar_title="Ventas")
      st.plotly_chart(fig_map, use_container_width=True)

      st.markdown("---")
      st.subheader("Tabla de ventas por estado")
      df_table = df_state_map[["Estado", "Ventas"]].rename(columns={"Estado": "State", "Ventas": "Ventas"})
      df_table = df_table.sort_values("Ventas", ascending=False).reset_index(drop=True)
      st.dataframe(df_table, use_container_width=True, hide_index=True)

      st.caption("Mapa y tabla de ventas por estado según los filtros actuales.")
