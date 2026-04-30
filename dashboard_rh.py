import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import warnings
warnings.filterwarnings("ignore")

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Painel DCGFT - versão preliminar",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    * { font-family: 'Roboto', sans-serif; }
    
    .main { background-color: #f5f5f5; }
    
    .stMetric { 
        background: white; 
        border-radius: 8px; 
        padding: 16px 20px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        border: 1px solid #e8e8e8;
        border-left: 4px solid #D2691E;
    }
    .stMetric label { 
        font-size: 0.75rem; 
        color: #666;
        font-weight: 500;
        text-transform: uppercase;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #D2691E;
        font-weight: 700;
    }
    
    h1 { 
        color: #2d2d2d;
        font-weight: 700;
        font-size: 1.8rem;
        margin-bottom: 0.3rem;
    }
    
    h3 {
        color: #555;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .block-container { padding-top: 1rem; }
    
    /* Sidebar laranja */
    div[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #D2691E 0%, #C85A17 100%);
    }
    div[data-testid="stSidebar"] * { color: white !important; }
    div[data-testid="stSidebar"] .stSelectbox label,
    div[data-testid="stSidebar"] .stMultiSelect label { 
        color: white !important;
        font-weight: 500;
    }
    div[data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: rgba(255,255,255,0.15);
    }
    
    /* Download button */
    .stDownloadButton button {
        background-color: #D2691E;
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
    }
    .stDownloadButton button:hover {
        background-color: #B8551A;
    }
</style>
""", unsafe_allow_html=True)

# ── Carregamento dos dados ──────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando base de dados…")
def load_data(path="BASE_DOTACAO.xlsx"):
    df = pd.read_excel(path)
    df["ANO"] = df["NR_ANO_MES_REF"].astype(str).str[:4].astype(int)
    df["MES"] = df["NR_ANO_MES_REF"].astype(str).str[4:].astype(int)
    df["ANO_MES_STR"] = (
        df["ANO"].astype(str) + "/" +
        df["MES"].astype(str).str.zfill(2)
    )
    return df

try:
    df = load_data("BASE_DOTACAO.xlsx")
except FileNotFoundError:
    uploaded = st.file_uploader("📂 Selecione o arquivo BASE_DOTACAO.xlsx", type=["xlsx"])
    if uploaded:
        df = load_data(uploaded)
    else:
        st.info("Aguardando o arquivo Excel para iniciar o dashboard.")
        st.stop()

# ── Sidebar – Filtros ───────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0 1.5rem 0;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Brasão_de_Minas_Gerais.svg/120px-Brasão_de_Minas_Gerais.svg.png" width="70">
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("### 🔍 Filtros", unsafe_allow_html=True)

anos_disp = sorted(df["ANO"].unique())
anos_sel = st.sidebar.multiselect("Ano de Referência", anos_disp, default=anos_disp[-3:])

meses_disp = sorted(df["MES"].unique())
meses_sel = st.sidebar.multiselect("Mês", meses_disp, default=[])

carreira_disp = sorted(df["DS_SIGLA_CARREIRA"].dropna().unique())
carreira_sel = st.sidebar.multiselect("Sigla da Carreira", carreira_disp, default=[])

inst_disp = sorted(df["DS_SIGLA_INST_DOTACAO"].dropna().unique())
inst_sel = st.sidebar.multiselect("Órgão / Instituição", inst_disp, default=[])

sit_func_disp = sorted(df["SIT_FUNCIONAL_AGRUPADA_REV"].dropna().unique())
sit_func_sel = st.sidebar.multiselect("Situação Funcional", sit_func_disp, default=[])

sit_serv_disp = sorted(df["SIT_SERVIDOR_AGRUPADA"].dropna().unique())
sit_serv_sel = st.sidebar.multiselect("Situação do Servidor", sit_serv_disp, default=[])

remun_disp = sorted(df["REMUN_DIF_0_REV"].dropna().unique())
remun_sel = st.sidebar.multiselect("Remuneração Diferenciada", remun_disp, default=[])

# ── Aplicar filtros ─────────────────────────────────────────────────────────
mask = pd.Series([True] * len(df), index=df.index)
if anos_sel:
    mask &= df["ANO"].isin(anos_sel)
if meses_sel:
    mask &= df["MES"].isin(meses_sel)
if carreira_sel:
    mask &= df["DS_SIGLA_CARREIRA"].isin(carreira_sel)
if inst_sel:
    mask &= df["DS_SIGLA_INST_DOTACAO"].isin(inst_sel)
if sit_func_sel:
    mask &= df["SIT_FUNCIONAL_AGRUPADA_REV"].isin(sit_func_sel)
if sit_serv_sel:
    mask &= df["SIT_SERVIDOR_AGRUPADA"].isin(sit_serv_sel)
if remun_sel:
    mask &= df["REMUN_DIF_0_REV"].isin(remun_sel)

dff = df[mask].copy()

# ── Header ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Logo_Governo_MG.svg/320px-Logo_Governo_MG.svg.png", width=180)
with col_title:
    st.markdown("""
    <h1 style="margin-top: 1rem; margin-bottom: 0.2rem;">PAINEL DCGFT - VERSÃO TESTE</h1>
    <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Dados Funcionais - Vínculo</p>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(f"📊 Base: {len(dff):,.0f} registros filtrados de {len(df):,.0f} totais")

if dff.empty:
    st.warning("Nenhum dado encontrado com os filtros aplicados. Ajuste os filtros na barra lateral.")
    st.stop()

# ── KPIs ────────────────────────────────────────────────────────────────────
total_servidores = dff["COUNT_NR_MASP_ADM"].sum()
total_ch = dff["SUM_CH_FINAL"].sum()
media_ch = dff["SUM_CH_FINAL"].mean()
n_orgaos = dff["DS_SIGLA_INST_DOTACAO"].nunique()
n_carreiras = dff["DS_NOME_CARREIRA"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("👤 Total Servidores", f"{total_servidores:,.0f}")
c2.metric("🏛️ Órgãos", f"{n_orgaos}")
c3.metric("📋 Carreiras", f"{n_carreiras}")
c4.metric("⏱️ CH Total (h)", f"{total_ch:,.0f}")
c5.metric("⏱️ CH Média (h)", f"{media_ch:,.1f}")

st.divider()

# ── Linha 1: Evolução temporal + Situação Funcional ─────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📈 Evolução de Servidores por Mês/Ano")
    evol = (
        dff.groupby("ANO_MES_STR")["COUNT_NR_MASP_ADM"]
        .sum()
        .reset_index()
        .sort_values("ANO_MES_STR")
    )
    fig_evol = px.line(
        evol, x="ANO_MES_STR", y="COUNT_NR_MASP_ADM",
        markers=True,
        labels={"ANO_MES_STR": "Período", "COUNT_NR_MASP_ADM": "Servidores"},
        color_discrete_sequence=["#D2691E"]
    )
    fig_evol.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=0), height=300
    )
    st.plotly_chart(fig_evol, use_container_width=True)

with col2:
    st.subheader("🏷️ Por Situação Funcional e Ano")
    sit_func_ano = (
        dff.groupby(["ANO", "SIT_FUNCIONAL_AGRUPADA_REV"])["COUNT_NR_MASP_ADM"]
        .sum()
        .reset_index()
    )
    fig_sit = px.bar(
        sit_func_ano,
        x="ANO",
        y="COUNT_NR_MASP_ADM",
        color="SIT_FUNCIONAL_AGRUPADA_REV",
        labels={
            "ANO": "Ano",
            "COUNT_NR_MASP_ADM": "Servidores",
            "SIT_FUNCIONAL_AGRUPADA_REV": "Situação Funcional"
        },
        color_discrete_sequence=["#FF4500", "#808080", "#D2691E", "#A0522D", "#CD853F", "#DEB887"],
    )
    fig_sit.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="v", font=dict(size=9), yanchor="top", y=1),
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        barmode='stack'
    )
    st.plotly_chart(fig_sit, use_container_width=True)

# ── Linha 1.5: Evolução de Carga Horária ───────────────────────────────────
st.subheader("⏱️ Evolução de Carga Horária por Mês/Ano")
evol_ch = (
    dff.groupby("ANO_MES_STR")["SUM_CH_FINAL"]
    .sum()
    .reset_index()
    .sort_values("ANO_MES_STR")
)
fig_evol_ch = px.line(
    evol_ch, x="ANO_MES_STR", y="SUM_CH_FINAL",
    markers=True,
    labels={"ANO_MES_STR": "Período", "SUM_CH_FINAL": "Carga Horária Total (h)"},
    color_discrete_sequence=["#C85A17"]
)
fig_evol_ch.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=20), height=300
)
st.plotly_chart(fig_evol_ch, use_container_width=True)

st.divider()

# ── Linha 2: Top Órgãos + Situação Servidor ────────────────────────────────
col3, col4 = st.columns([3, 2])

with col3:
    st.subheader("🏛️ Top 15 Órgãos por Nº de Servidores")
    top_orgaos = (
        dff.groupby("DS_SIGLA_INST_DOTACAO")["COUNT_NR_MASP_ADM"]
        .sum()
        .reset_index()
        .sort_values("COUNT_NR_MASP_ADM", ascending=False)
        .head(15)
    )
    fig_orgaos = px.bar(
        top_orgaos.sort_values("COUNT_NR_MASP_ADM"),
        x="COUNT_NR_MASP_ADM", y="DS_SIGLA_INST_DOTACAO",
        orientation="h",
        labels={"DS_SIGLA_INST_DOTACAO": "Órgão", "COUNT_NR_MASP_ADM": "Servidores"},
        color="COUNT_NR_MASP_ADM",
        color_continuous_scale=["#FFA07A", "#FF7F50", "#FF6347", "#FF4500", "#D2691E"],
    )
    fig_orgaos.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0), height=380
    )
    st.plotly_chart(fig_orgaos, use_container_width=True)

with col4:
    st.subheader("👔 Por Situação do Servidor")
    sit_serv_agg = (
        dff.groupby("SIT_SERVIDOR_AGRUPADA")["COUNT_NR_MASP_ADM"]
        .sum()
        .reset_index()
    )
    fig_serv = px.bar(
        sit_serv_agg.sort_values("COUNT_NR_MASP_ADM", ascending=False),
        x="SIT_SERVIDOR_AGRUPADA", y="COUNT_NR_MASP_ADM",
        labels={"SIT_SERVIDOR_AGRUPADA": "", "COUNT_NR_MASP_ADM": "Servidores"},
        color="SIT_SERVIDOR_AGRUPADA",
        color_discrete_sequence=["#FF4500", "#D2691E", "#A0522D"],
    )
    fig_serv.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0), height=380
    )
    st.plotly_chart(fig_serv, use_container_width=True)

# ── Linha 3: Top Carreiras ──────────────────────────────────────────────────
st.subheader("📋 Top 20 Carreiras por Nº de Servidores")
top_carr = (
    dff.groupby("DS_NOME_CARREIRA")["COUNT_NR_MASP_ADM"]
    .sum()
    .reset_index()
    .sort_values("COUNT_NR_MASP_ADM", ascending=False)
    .head(20)
)
fig_carr = px.bar(
    top_carr,
    x="DS_NOME_CARREIRA", y="COUNT_NR_MASP_ADM",
    labels={"DS_NOME_CARREIRA": "Carreira", "COUNT_NR_MASP_ADM": "Servidores"},
    color="COUNT_NR_MASP_ADM",
    color_continuous_scale=["#FFA07A", "#FF7F50", "#FF6347", "#FF4500", "#D2691E"],
)
fig_carr.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    coloraxis_showscale=False,
    xaxis_tickangle=-40,
    margin=dict(l=0, r=0, t=10, b=0), height=320
)
st.plotly_chart(fig_carr, use_container_width=True)

# ── Tabela de dados + Export ─────────────────────────────────────────────────
st.divider()
st.subheader("📊 Tabela de Dados Filtrados")

# Resumo agregado para exibição
tabela = (
    dff.groupby([
        "NR_ANO_MES_REF", "DS_SIGLA_INST_DOTACAO", "DS_NOME_CARREIRA",
        "SIT_FUNCIONAL_AGRUPADA_REV", "SIT_SERVIDOR_AGRUPADA", "REMUN_DIF_0_REV"
    ], as_index=False)
    .agg(
        SERVIDORES=("COUNT_NR_MASP_ADM", "sum"),
        CH_TOTAL=("SUM_CH_FINAL", "sum"),
    )
    .sort_values(["NR_ANO_MES_REF", "SERVIDORES"], ascending=[True, False])
)

col_t1, col_t2 = st.columns([4, 1])
with col_t1:
    st.caption(f"Exibindo {len(tabela):,} linhas agrupadas")
with col_t2:
    # ── BOTÃO DE EXPORT EXCEL ──
    @st.cache_data
    def to_excel_bytes(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Dotacao_Filtrada")
            wb_xl = writer.book
            ws_xl = writer.sheets["Dotacao_Filtrada"]
            header_fmt = wb_xl.add_format({
                "bold": True, "bg_color": "#1e3a5f",
                "font_color": "white", "border": 1
            })
            for col_num, value in enumerate(dataframe.columns.values):
                ws_xl.write(0, col_num, value, header_fmt)
                ws_xl.set_column(col_num, col_num, max(len(str(value)) + 4, 14))
        return output.getvalue()

    excel_data = to_excel_bytes(tabela)
    st.download_button(
        label="⬇️ Exportar Excel",
        data=excel_data,
        file_name="dotacao_filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.dataframe(
    tabela,
    use_container_width=True,
    height=380,
    column_config={
        "NR_ANO_MES_REF": st.column_config.NumberColumn("Período", format="%d"),
        "DS_SIGLA_INST_DOTACAO": "Órgão",
        "DS_NOME_CARREIRA": "Carreira",
        "SIT_FUNCIONAL_AGRUPADA_REV": "Sit. Funcional",
        "SIT_SERVIDOR_AGRUPADA": "Sit. Servidor",
        "REMUN_DIF_0_REV": "Rem. Diferenciada",
        "SERVIDORES": st.column_config.NumberColumn("Servidores", format="%d"),
        "CH_TOTAL": st.column_config.NumberColumn("CH Total (h)", format="%d"),
    }
)

st.sidebar.divider()
st.sidebar.caption("Dashboard RH – Dotação de Pessoal\nFeito com Streamlit 🚀")
