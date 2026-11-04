import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import warnings

warnings.filterwarnings("ignore")

# ── 1. CONFIGURAÇÃO DA PÁGINA E CSS (RESPONSIVO E TRADUZIDO) ────────────────
def setup_page():
    st.set_page_config(
        page_title="Painel DCGFT - Lotação",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        * { font-family: 'Roboto', sans-serif; }
        
        .main { background-color: #f5f5f5; }
        
        /* ── CARDS DE KPI RESPONSIVOS (CORREÇÃO PARA MACBOOK E TELAS MENORES) ── */
        .stMetric { 
            background: white; 
            border-radius: 8px; 
            padding: 10px 14px !important; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            border: 1px solid #e8e8e8;
            border-left: 4px solid #D2691E;
        }
        .stMetric label { 
            font-size: 0.70rem !important; 
            color: #666;
            font-weight: 500;
            text-transform: uppercase;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #D2691E;
            font-weight: 700;
            font-size: clamp(1.1rem, 1.3vw, 1.6rem) !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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

        /* Ajuste visual para campos de busca na Sidebar */
        div[data-baseweb="select"] input::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
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

# ── 2. CARREGAMENTO DE DADOS (BASE DE LOTAÇÃO) ──────────────────────────────
@st.cache_data(show_spinner="Carregando base de lotação…")
def load_data(path="BASE_LOTACAO.xlsx"):
    df = pd.read_excel(path)
    
    # Padronização do nome da coluna de instituição para Lotação
    if "DS_SIGLA_INST_LOTACAO" in df.columns:
        df["DS_SIGLA_INST_DOTACAO"] = df["DS_SIGLA_INST_LOTACAO"]
    elif "DS_SIGLA_INST_DOTACAO" in df.columns:
        df["DS_SIGLA_INST_LOTACAO"] = df["DS_SIGLA_INST_DOTACAO"]
    
    # Extração matemática de Ano e Mês (Alta Performance)
    df["ANO"] = (df["NR_ANO_MES_REF"] // 100).astype("int16")
    df["MES"] = (df["NR_ANO_MES_REF"] % 100).astype("int8")
    
    df["ANO_MES_STR"] = df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)
    df["ANO_MES_STR"] = df["ANO_MES_STR"].astype("category")
    
    # Otimização de memória RAM
    colunas_categoricas = [
        "DS_SIGLA_CARREIRA", "DS_SIGLA_INST_LOTACAO", "DS_SIGLA_INST_DOTACAO",
        "SIT_FUNCIONAL_AGRUPADA_REV", "SIT_SERVIDOR_AGRUPADA", 
        "REMUN_DIF_0_REV", "DS_NOME_CARREIRA"
    ]
    for col in colunas_categoricas:
        if col in df.columns:
            df[col] = df[col].astype("category")
            
    if "COUNT_NR_MASP_ADM" in df.columns:
        df["COUNT_NR_MASP_ADM"] = pd.to_numeric(df["COUNT_NR_MASP_ADM"], downcast="integer")
    if "SUM_CH_FINAL" in df.columns:
        df["SUM_CH_FINAL"] = pd.to_numeric(df["SUM_CH_FINAL"], downcast="float")
        
    return df

# ── 3. FILTROS DA SIDEBAR (TEXTOS EM PORTUGUÊS) ─────────────────────────────
def render_sidebar_filters(df):
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Brasão_de_Minas_Gerais.svg/120px-Brasão_de_Minas_Gerais.svg.png" width="70">
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("### 🔍 Filtros", unsafe_allow_html=True)

    filtros = {}
    
    anos_disp = sorted(df["ANO"].unique())
    filtros["anos"] = st.sidebar.multiselect(
        "Ano de Referência", anos_disp, default=anos_disp[-3:], placeholder="Selecione o ano..."
    )

    meses_disp = sorted(df["MES"].unique())
    filtros["meses"] = st.sidebar.multiselect(
        "Mês", meses_disp, default=[], placeholder="Selecione o mês..."
    )

    carreira_disp = sorted(df["DS_SIGLA_CARREIRA"].dropna().unique())
    filtros["carreira"] = st.sidebar.multiselect(
        "Sigla da Carreira", carreira_disp, default=[], placeholder="Selecione a carreira..."
    )

    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in df.columns else "DS_SIGLA_INST_DOTACAO"
    inst_disp = sorted(df[col_inst].dropna().unique())
    filtros["inst"] = st.sidebar.multiselect(
        "Órgão / Instituição de Lotação", inst_disp, default=[], placeholder="Selecione o órgão..."
    )

    sit_func_disp = sorted(df["SIT_FUNCIONAL_AGRUPADA_REV"].dropna().unique())
    filtros["sit_func"] = st.sidebar.multiselect(
        "Situação Funcional", sit_func_disp, default=[], placeholder="Selecione a situação..."
    )

    sit_serv_disp = sorted(df["SIT_SERVIDOR_AGRUPADA"].dropna().unique())
    filtros["sit_serv"] = st.sidebar.multiselect(
        "Situação do Servidor", sit_serv_disp, default=[], placeholder="Selecione a situação..."
    )

    remun_disp = sorted(df["REMUN_DIF_0_REV"].dropna().unique())
    filtros["remun"] = st.sidebar.multiselect(
        "Remuneração Diferenciada", remun_disp, default=[], placeholder="Selecione a opção..."
    )

    st.sidebar.divider()
    st.sidebar.caption("Dashboard RH – Lotação de Pessoal\nFeito com Streamlit 🚀")
    
    return filtros

def apply_filters(df, filtros):
    mask = pd.Series([True] * len(df), index=df.index)
    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in df.columns else "DS_SIGLA_INST_DOTACAO"
    
    if filtros["anos"]: mask &= df["ANO"].isin(filtros["anos"])
    if filtros["meses"]: mask &= df["MES"].isin(filtros["meses"])
    if filtros["carreira"]: mask &= df["DS_SIGLA_CARREIRA"].isin(filtros["carreira"])
    if filtros["inst"]: mask &= df[col_inst].isin(filtros["inst"])
    if filtros["sit_func"]: mask &= df["SIT_FUNCIONAL_AGRUPADA_REV"].isin(filtros["sit_func"])
    if filtros["sit_serv"]: mask &= df["SIT_SERVIDOR_AGRUPADA"].isin(filtros["sit_serv"])
    if filtros["remun"]: mask &= df["REMUN_DIF_0_REV"].isin(filtros["remun"])
    
    return df[mask].copy()

# ── 4. CABEÇALHO E KPIS ─────────────────────────────────────────────────────
def render_kpis(dff, total_linhas):
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Logo_Governo_MG.svg/320px-Logo_Governo_MG.svg.png", width=180)
    with col_title:
        st.markdown("""
        <h1 style="margin-top: 1rem; margin-bottom: 0.2rem;">PAINEL DCGFT - VERSÃO TESTE</h1>
        <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Dados Funcionais - Lotação</p>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"📊 Base: {len(dff):,.0f} registros filtrados de {total_linhas:,.0f} totais")

    if dff.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados. Ajuste os filtros na barra lateral.")
        st.stop()

    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in dff.columns else "DS_SIGLA_INST_DOTACAO"
    
    total_servidores = dff["COUNT_NR_MASP_ADM"].sum()
    total_ch = dff["SUM_CH_FINAL"].sum()
    media_ch = dff["SUM_CH_FINAL"].mean()
    n_orgaos = dff[col_inst].nunique()
    n_carreiras = dff["DS_NOME_CARREIRA"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👤 Total Servidores", f"{total_servidores:,.0f}")
    c2.metric("🏛️ Órgãos", f"{n_orgaos}")
    c3.metric("📋 Carreiras", f"{n_carreiras}")
    c4.metric("⏱️ CH Total (h)", f"{total_ch:,.0f}")
    c5.metric("⏱️ CH Média (h)", f"{media_ch:,.1f}")

    st.divider()

# ── 5. GRÁFICOS (SEM TOP 15 E TOP 20) ───────────────────────────────────────
def render_charts(dff):
    # Linha 1: Evolução Temporal + Situação Funcional
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("📈 Evolução de Servidores por Mês/Ano")
        evol = dff.groupby("ANO_MES_STR", observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index().sort_values("ANO_MES_STR")
        fig_evol = px.line(
            evol, x="ANO_MES_STR", y="COUNT_NR_MASP_ADM", markers=True,
            labels={"ANO_MES_STR": "Período", "COUNT_NR_MASP_ADM": "Servidores"},
            color_discrete_sequence=["#D2691E"]
        )
        fig_evol.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig_evol, use_container_width=True)

    with col2:
        st.subheader("🏷️ Por Situação Funcional e Ano")
        sit_func_ano = dff.groupby(["ANO", "SIT_FUNCIONAL_AGRUPADA_REV"], observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index()
        fig_sit = px.bar(
            sit_func_ano, x="ANO", y="COUNT_NR_MASP_ADM", color="SIT_FUNCIONAL_AGRUPADA_REV",
            labels={"ANO": "Ano", "COUNT_NR_MASP_ADM": "Servidores", "SIT_FUNCIONAL_AGRUPADA_REV": "Situação Funcional"},
            color_discrete_sequence=["#FF4500", "#808080", "#D2691E", "#A0522D", "#CD853F", "#DEB887"]
        )
        fig_sit.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", showlegend=True,
            legend=dict(orientation="v", font=dict(size=9), yanchor="top", y=1),
            margin=dict(l=0, r=0, t=10, b=0), height=300, barmode='stack'
        )
        st.plotly_chart(fig_sit, use_container_width=True)

    # Linha 2: Evolução de Carga Horária
    st.subheader("⏱️ Evolução de Carga Horária por Mês/Ano")
    evol_ch = dff.groupby("ANO_MES_STR", observed=True)["SUM_CH_FINAL"].sum().reset_index().sort_values("ANO_MES_STR")
    fig_evol_ch = px.line(
        evol_ch, x="ANO_MES_STR", y="SUM_CH_FINAL", markers=True,
        labels={"ANO_MES_STR": "Período", "SUM_CH_FINAL": "Carga Horária Total (h)"},
        color_discrete_sequence=["#C85A17"]
    )
    fig_evol_ch.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=20), height=300)
    st.plotly_chart(fig_evol_ch, use_container_width=True)

    st.divider()

    # Linha 3: Situação do Servidor
    st.subheader("👔 Por Situação do Servidor")
    sit_serv_agg = dff.groupby("SIT_SERVIDOR_AGRUPADA", observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index()
    fig_serv = px.bar(
        sit_serv_agg.sort_values("COUNT_NR_MASP_ADM", ascending=False), x="SIT_SERVIDOR_AGRUPADA", y="COUNT_NR_MASP_ADM",
        labels={"SIT_SERVIDOR_AGRUPADA": "Situação do Servidor", "COUNT_NR_MASP_ADM": "Servidores"},
        color="SIT_SERVIDOR_AGRUPADA", color_discrete_sequence=["#FF4500", "#D2691E", "#A0522D"]
    )
    fig_serv.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_serv, use_container_width=True)

# ── 6. TABELA E EXPORTAÇÃO EXCEL ────────────────────────────────────────────
@st.cache_data
def to_excel_bytes(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Lotacao_Filtrada")
        wb_xl = writer.book
        ws_xl = writer.sheets["Lotacao_Filtrada"]
        header_fmt = wb_xl.add_format({
            "bold": True, "bg_color": "#D2691E",
            "font_color": "white", "border": 1
        })
        for col_num, value in enumerate(dataframe.columns.values):
            ws_xl.write(0, col_num, value, header_fmt)
            ws_xl.set_column(col_num, col_num, max(len(str(value)) + 4, 14))
    return output.getvalue()

def render_table_and_export(dff):
    st.divider()
    st.subheader("📊 Tabela de Dados Filtrados")

    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in dff.columns else "DS_SIGLA_INST_DOTACAO"

    tabela = (
        dff.groupby([
            "NR_ANO_MES_REF", col_inst, "DS_NOME_CARREIRA",
            "SIT_FUNCIONAL_AGRUPADA_REV", "SIT_SERVIDOR_AGRUPADA", "REMUN_DIF_0_REV"
        ], as_index=False, observed=True)
        .agg(SERVIDORES=("COUNT_NR_MASP_ADM", "sum"), CH_TOTAL=("SUM_CH_FINAL", "sum"))
        .sort_values(["NR_ANO_MES_REF", "SERVIDORES"], ascending=[True, False])
    )

    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.caption(f"Exibindo {len(tabela):,} linhas agrupadas")
    with col_t2:
        excel_data = to_excel_bytes(tabela)
        st.download_button(
            label="⬇️ Exportar Excel",
            data=excel_data,
            file_name="lotacao_filtrada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.dataframe(
        tabela,
        use_container_width=True,
        height=380,
        column_config={
            "NR_ANO_MES_REF": st.column_config.NumberColumn("Período", format="%d"),
            col_inst: "Órgão Lotação",
            "DS_NOME_CARREIRA": "Carreira",
            "SIT_FUNCIONAL_AGRUPADA_REV": "Sit. Funcional",
            "SIT_SERVIDOR_AGRUPADA": "Sit. Servidor",
            "REMUN_DIF_0_REV": "Rem. Diferenciada",
            "SERVIDORES": st.column_config.NumberColumn("Servidores", format="%d"),
            "CH_TOTAL": st.column_config.NumberColumn("CH Total (h)", format="%d"),
        }
    )

# ── 7. EXECUÇÃO PRINCIPAL ───────────────────────────────────────────────────
def main():
    setup_page()

    try:
        df = load_data("BASE_LOTACAO.xlsx")
    except FileNotFoundError:
        uploaded = st.file_uploader("📂 Selecione o arquivo BASE_LOTACAO.xlsx", type=["xlsx"])
        if uploaded:
            df = load_data(uploaded)
        else:
            st.info("Aguardando o arquivo Excel para iniciar o dashboard.")
            st.stop()

    filtros = render_sidebar_filters(df)
    dff = apply_filters(df, filtros)
    
    render_kpis(dff, len(df))
    render_charts(dff)
    render_table_and_export(dff)

if __name__ == "__main__":
    main()
