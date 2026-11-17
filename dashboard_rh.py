import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import warnings

warnings.filterwarnings("ignore")

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def fmt_int_br(val):
    if pd.isna(val):
        return "-"
    return f"{val:,.0f}".replace(",", ".")

def fmt_pct_br(val, decimals=1):
    if pd.isna(val):
        return "-"
    return f"{val:,.{decimals}f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def encontrar_arquivo(possiveis_nomes):
    """Procura o arquivo na pasta ignorando diferenças entre maiúsculas e minúsculas."""
    try:
        arquivos_dir = os.listdir(".")
        mapa_lower = {f.lower(): f for f in arquivos_dir}
        for nome in possiveis_nomes:
            if nome.lower() in mapa_lower:
                return mapa_lower[nome.lower()]
    except Exception:
        pass
    return None

# ── 1. CONFIGURAÇÃO DA PÁGINA E CSS ─────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title="Painel DCGFT - Gestão da Força de Trabalho",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        * { font-family: 'Roboto', sans-serif; }
        
        .main { background-color: #f5f5f5; }
        
        /* ── CARDS DE KPI EMPILHADOS (UM ABAIXO DO OUTRO) ── */
        [data-testid="stMetric"] { 
            background: #ffffff; 
            border-radius: 8px; 
            padding: 14px 18px !important; 
            margin-bottom: 10px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            border: 1px solid #e5e7eb;
            border-left: 5px solid #D2691E;
            width: 100% !important;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] *,
        div[data-testid="stMetricLabel"] p { 
            font-size: 0.82rem !important; 
            color: #555555 !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.03em !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            line-height: 1.3 !important;
            margin-bottom: 4px !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #D2691E !important;
            font-weight: 700 !important;
            font-size: 1.45rem !important;
            white-space: normal !important;
        }
        
        h1 { 
            color: #2d2d2d;
            font-weight: 700;
            font-size: 1.8rem;
            margin-bottom: 0.2rem;
        }
        
        h3 {
            color: #555;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .block-container { padding-top: 1rem; }

        /* Caixa de Objetivo e Metodologia */
        .objetivo-box {
            background-color: #ffffff;
            border-left: 4px solid #D2691E;
            border-top: 1px solid #e8e8e8;
            border-right: 1px solid #e8e8e8;
            border-bottom: 1px solid #e8e8e8;
            border-radius: 6px;
            padding: 14px 18px;
            font-size: 0.9rem;
            color: #333;
            line-height: 1.5;
            margin-top: 0.6rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* ── SIDEBAR CLARA E LEGÍVEL ── */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] { 
            background-color: #f8f9fa !important;
            border-right: 1px solid #e0e0e0 !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] p,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] label { 
            color: #2d2d2d !important;
        }

        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stMultiSelect label,
        div[data-testid="stSidebar"] .stSelectbox label,
        div[data-testid="stSidebar"] .stMultiSelect label { 
            color: #333333 !important;
            font-weight: 600 !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        div[data-testid="stSidebar"] [data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border-color: #d1d5db !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        div[data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #2d2d2d !important;
        }

        div[data-baseweb="select"] input::placeholder {
            color: #888888 !important;
        }

        /* Estilo dos botões do Menu de Navegação */
        section[data-testid="stSidebar"] [data-testid="stRadio"] > div,
        div[data-testid="stSidebar"] [data-testid="stRadio"] > div {
            gap: 0.45rem;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label,
        div[data-testid="stSidebar"] [data-testid="stRadio"] label {
            background-color: #ffffff;
            padding: 0.6rem 0.85rem;
            border-radius: 6px;
            width: 100%;
            border: 1px solid #dcdcdc;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover,
        div[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            border-color: #D2691E;
            background-color: #fff8f3;
        }
        
        /* Download button */
        .stDownloadButton button {
            background-color: #D2691E;
            color: white !important;
            border: none;
            font-weight: 600;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
        }
        .stDownloadButton button:hover {
            background-color: #B8551A;
        }

        /* ── TRADUÇÃO DO 'SELECT ALL' NO DROPDOWN DE OPÇÕES ── */
        [data-baseweb="popover"] [role="option"]:first-child span,
        [data-baseweb="popover"] ul li:first-child span {
            font-size: 0 !important;
        }
        [data-baseweb="popover"] [role="option"]:first-child span::after,
        [data-baseweb="popover"] ul li:first-child span::after {
            content: "Selecionar todos" !important;
            font-size: 0.85rem !important;
            color: #333 !important;
            visibility: visible !important;
            display: inline-block !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ── 2. EXPORTAÇÃO EXCEL REUTILIZÁVEL ────────────────────────────────────────
@st.cache_data
def to_excel_bytes(dataframe, sheet_name="Dados_Filtrados"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
        wb_xl = writer.book
        ws_xl = writer.sheets[sheet_name]
        header_fmt = wb_xl.add_format({
            "bold": True, "bg_color": "#D2691E",
            "font_color": "white", "border": 1
        })
        for col_num, value in enumerate(dataframe.columns.values):
            ws_xl.write(0, col_num, value, header_fmt)
            ws_xl.set_column(col_num, col_num, max(len(str(value)) + 4, 14))
    return output.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1: DADOS FUNCIONAIS - LOTAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Carregando base de lotação…")
def load_data_lotacao(path="BASE_LOTACAO.xlsx"):
    df = pd.read_excel(path)
    
    if "DS_SIGLA_INST_LOTACAO" in df.columns:
        df["DS_SIGLA_INST_DOTACAO"] = df["DS_SIGLA_INST_LOTACAO"]
    elif "DS_SIGLA_INST_DOTACAO" in df.columns:
        df["DS_SIGLA_INST_LOTACAO"] = df["DS_SIGLA_INST_DOTACAO"]
    
    df["ANO"] = (df["NR_ANO_MES_REF"] // 100).astype("int16")
    df["MES"] = (df["NR_ANO_MES_REF"] % 100).astype("int8")
    
    df["ANO_MES_STR"] = df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)
    df["ANO_MES_STR"] = df["ANO_MES_STR"].astype("category")
    
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

def render_sidebar_filters_lotacao(df):
    st.sidebar.markdown("### 🔍 Filtros — Lotação", unsafe_allow_html=True)

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
    
    return filtros

def apply_filters_lotacao(df, filtros):
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

def page_lotacao():
    arquivo_lot = encontrar_arquivo(["BASE_LOTACAO.xlsx", "BASE LOTACAO.xlsx"])
    if arquivo_lot:
        df = load_data_lotacao(arquivo_lot)
    else:
        uploaded = st.file_uploader("📂 Selecione o arquivo BASE_LOTACAO.xlsx", type=["xlsx"], key="up_lotacao")
        if uploaded:
            df = load_data_lotacao(uploaded)
        else:
            st.info("Aguardando o arquivo BASE_LOTACAO.xlsx para iniciar o dashboard.")
            st.stop()

    filtros = render_sidebar_filters_lotacao(df)
    dff = apply_filters_lotacao(df, filtros)

    st.markdown("""
    <h1 style="margin-top: 0.2rem; margin-bottom: 0.2rem;">PAINEL DCGFT - LOTAÇÃO</h1>
    <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Dados Funcionais - Lotação</p>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"📊 Base: {len(dff):,.0f} registros filtrados de {len(df):,.0f} totais")

    if dff.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados. Ajuste os filtros na barra lateral.")
        st.stop()

    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in dff.columns else "DS_SIGLA_INST_DOTACAO"
    
    total_servidores = dff["COUNT_NR_MASP_ADM"].sum()
    total_ch = dff["SUM_CH_FINAL"].sum()
    media_ch = dff["SUM_CH_FINAL"].mean()
    n_orgaos = dff[col_inst].nunique()
    n_carreiras = dff["DS_NOME_CARREIRA"].nunique()

    # Cards empilhados um abaixo do outro
    st.metric("👤 Servidores", fmt_int_br(total_servidores))
    st.metric("🏛️ Órgãos", f"{n_orgaos}")
    st.metric("📋 Carreiras", f"{n_carreiras}")
    st.metric("⏱️ CH Total (h)", fmt_int_br(total_ch))
    st.metric("⏱️ CH Média (h)", f"{media_ch:,.1f}".replace(".", ","))

    st.divider()

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

    st.subheader("👔 Por Situação do Servidor")
    sit_serv_agg = dff.groupby("SIT_SERVIDOR_AGRUPADA", observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index()
    fig_serv = px.bar(
        sit_serv_agg.sort_values("COUNT_NR_MASP_ADM", ascending=False), x="SIT_SERVIDOR_AGRUPADA", y="COUNT_NR_MASP_ADM",
        labels={"SIT_SERVIDOR_AGRUPADA": "Situação do Servidor", "COUNT_NR_MASP_ADM": "Servidores"},
        color="SIT_SERVIDOR_AGRUPADA", color_discrete_sequence=["#FF4500", "#D2691E", "#A0522D"]
    )
    fig_serv.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_serv, use_container_width=True)

    st.divider()
    st.subheader("📊 Tabela de Dados Filtrados")

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
        excel_data = to_excel_bytes(tabela, sheet_name="Lotacao_Filtrada")
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

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2: CONTROLE DE CONTRATOS TEMPORÁRIOS - MAGISTÉRIO (BASE PAINEL)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Carregando base do Magistério…")
def load_data_magisterio(source):
    xl = pd.ExcelFile(source)
    sheet = "APPEND_TABLE" if "APPEND_TABLE" in xl.sheet_names else 0
    df = pd.read_excel(xl, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    ref_str = df["DT_ANO_MES_REF"].astype(str).str.strip()
    if ref_str.str.contains("/").any():
        partes = ref_str.str.split("/", expand=True)
        df["ANO"] = pd.to_numeric(partes[0], errors="coerce").fillna(0).astype(int)
        df["MES"] = pd.to_numeric(partes[1], errors="coerce").fillna(0).astype(int)
    else:
        df["ANO"] = (pd.to_numeric(ref_str, errors="coerce").fillna(0) // 100).astype(int)
        df["MES"] = (pd.to_numeric(ref_str, errors="coerce").fillna(0) % 100).astype(int)

    df = df[df["ANO"] > 0].copy()
    df["PERIODO"] = df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)
    df["MES_NOME"] = df["MES"].map(MESES_PT)

    df["COUNT_of_NR_MASP_ADM"] = pd.to_numeric(df["COUNT_of_NR_MASP_ADM"], errors="coerce").fillna(0)
    df["QUANT_LEI"] = pd.to_numeric(df["QUANT_LEI"], errors="coerce").fillna(0)
    df["INSTITUICAO"] = df["INSTITUICAO"].astype(str).str.strip()
    df["DS_SIGLA_CARREIRA"] = df["DS_SIGLA_CARREIRA"].astype(str).str.strip()

    return df

def page_magisterio():
    st.markdown("""
    <h1 style="margin-top: 0.2rem; margin-bottom: 0.2rem;">CONTRATOS TEMPORÁRIOS — MAGISTÉRIO</h1>
    <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Controle de Índices Legais — Lei 24.805/2024 e Decreto 48.780/2024</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    arquivo_encontrado = encontrar_arquivo(["BASE_PAINEL.xlsx", "BASE PAINEL.xlsx"])

    if arquivo_encontrado:
        df_mag = load_data_magisterio(arquivo_encontrado)
    else:
        uploaded_mag = st.file_uploader(
            "📂 Selecione a planilha BASE_PAINEL.xlsx (aba APPEND_TABLE)",
            type=["xlsx"],
            key="up_magisterio"
        )
        if uploaded_mag:
            df_mag = load_data_magisterio(uploaded_mag)
        else:
            st.info("Aguardando o arquivo `BASE_PAINEL.xlsx` para iniciar o painel do Magistério.")
            st.stop()

    st.sidebar.markdown("### 🔍 Filtros — Magistério", unsafe_allow_html=True)

    anos_disp = sorted(df_mag["ANO"].unique())
    ano_sel = st.sidebar.selectbox(
        "Ano de Referência (Quadro Atual)",
        options=anos_disp,
        index=len(anos_disp) - 1,
        key="ano_mag"
    )

    meses_do_ano = sorted(df_mag[df_mag["ANO"] == ano_sel]["MES"].unique())
    mes_sel = st.sidebar.selectbox(
        "Mês de Referência (Quadro Atual)",
        options=meses_do_ano,
        index=len(meses_do_ano) - 1,
        format_func=lambda m: f"{str(m).zfill(2)} - {MESES_PT.get(m, str(m))}",
        key="mes_mag"
    )

    carreiras_disp = sorted(df_mag["DS_SIGLA_CARREIRA"].dropna().unique())
    carreiras_sel = st.sidebar.multiselect(
        "Sigla da Carreira",
        options=carreiras_disp,
        default=[],
        placeholder="Selecione a carreira...",
        key="carr_mag"
    )

    orgaos_disp = sorted(df_mag["INSTITUICAO"].dropna().unique())
    orgaos_sel = st.sidebar.multiselect(
        "Órgão / Instituição",
        options=orgaos_disp,
        default=[],
        placeholder="Selecione o órgão...",
        key="org_mag"
    )

    mask_hist = pd.Series([True] * len(df_mag), index=df_mag.index)
    if carreiras_sel:
        mask_hist &= df_mag["DS_SIGLA_CARREIRA"].isin(carreiras_sel)
    if orgaos_sel:
        mask_hist &= df_mag["INSTITUICAO"].isin(orgaos_sel)
    df_hist = df_mag[mask_hist].copy()

    df_atual = df_hist[(df_hist["ANO"] == ano_sel) & (df_hist["MES"] == mes_sel)].copy()

    if df_atual.empty:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")
        st.stop()

    mes_ref_texto = f"{MESES_PT.get(mes_sel, '').upper()} DE {ano_sel}"
    total_lei = df_atual["QUANT_LEI"].sum()
    total_ct = df_atual["COUNT_of_NR_MASP_ADM"].sum()
    perc_ct = (total_ct / total_lei * 100) if total_lei > 0 else 0.0

    if ano_sel <= 2025:
        taxa_limite = 0.50
    elif ano_sel == 2026:
        taxa_limite = 0.40
    else:
        taxa_limite = 0.30

    limite_qtd = total_lei * taxa_limite
    margem = limite_qtd - total_ct

    # Cards empilhados um abaixo do outro
    st.metric("📅 Mês de Referência", mes_ref_texto)
    st.metric("🏛️ Quant. em Lei (EF)", fmt_int_br(total_lei))
    st.metric("📝 Contrato Temp. (CT)", fmt_int_br(total_ct))
    st.metric("📊 % Contratos Temp.", fmt_pct_br(perc_ct, 2))
    st.metric(f"⚖️ Limite de {int(taxa_limite*100)}%", fmt_int_br(limite_qtd))
    st.metric("📉 Margem", fmt_int_br(margem))

    st.markdown("""
    <div class="objetivo-box">
        <strong>Objetivo:</strong> Averiguar o cumprimento dos índices máximos de <strong>50% em 2025</strong>, 
        <strong>40% em 2026</strong> e <strong>30% em 2027</strong> de servidores contratados temporários magistério 
        em relação ao total de servidores efetivos ativos das carreiras: Professor de Educação Básica, Especialista 
        em Educação Básica, Analista Educacional com função de Inspeção Escolar, Professor de Educação Superior, 
        Professor Ensino Médio e Tecnológico, Professor de Arte, Professor de Arte e Restauro e Pesquisador em 
        Ciências Aplicadas e Políticas Públicas conforme previsto na <strong>LEI 24.805 de 11 de junho de 2024</strong> 
        e <strong>Decreto 48.780 de 30 de junho de 2024</strong>.
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📋 Quadro Atual — Quantidade de servidores por órgão no mês ({mes_ref_texto})")

    quadro = (
        df_atual.groupby(["INSTITUICAO", "DS_SIGLA_CARREIRA"], as_index=False)
        .agg(
            QTDE_LEI=("QUANT_LEI", "sum"),
            QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum")
        )
        .sort_values(["INSTITUICAO", "DS_SIGLA_CARREIRA"])
    )

    quadro["PERCENTUAL"] = np.where(quadro["QTDE_LEI"] > 0, (quadro["QTDE_CT"] / quadro["QTDE_LEI"]) * 100, np.nan)
    quadro["LIM_25"] = 50.0
    quadro["DIF_25"] = quadro["PERCENTUAL"] - 50.0
    quadro["LIM_26"] = 40.0
    quadro["DIF_26"] = quadro["PERCENTUAL"] - 40.0
    quadro["LIM_27"] = 30.0
    quadro["DIF_27"] = quadro["PERCENTUAL"] - 30.0

    perc_total = (total_ct / total_lei * 100) if total_lei > 0 else np.nan
    linha_total = pd.DataFrame([{
        "INSTITUICAO": "TOTAL GERAL",
        "DS_SIGLA_CARREIRA": "-",
        "QTDE_LEI": total_lei,
        "QTDE_CT": total_ct,
        "PERCENTUAL": perc_total,
        "LIM_25": 50.0,
        "DIF_25": perc_total - 50.0 if not pd.isna(perc_total) else np.nan,
        "LIM_26": 40.0,
        "DIF_26": perc_total - 40.0 if not pd.isna(perc_total) else np.nan,
        "LIM_27": 30.0,
        "DIF_27": perc_total - 30.0 if not pd.isna(perc_total) else np.nan,
    }])

    quadro_exibicao = pd.concat([quadro, linha_total], ignore_index=True)

    quadro_fmt = pd.DataFrame({
        "Órgão": quadro_exibicao["INSTITUICAO"],
        "Carreira": quadro_exibicao["DS_SIGLA_CARREIRA"],
        "Qtde LEI": quadro_exibicao["QTDE_LEI"].apply(fmt_int_br),
        "Qtde Contratos Temporários": quadro_exibicao["QTDE_CT"].apply(fmt_int_br),
        "Percentual": quadro_exibicao["PERCENTUAL"].apply(lambda x: fmt_pct_br(x, 1)),
        "Limite Julho 25": "50%",
        "Diferença 25 (p.p.)": quadro_exibicao["DIF_25"].apply(lambda x: f"{x:+.1f} p.p.".replace(".", ",") if pd.notna(x) else "-"),
        "Limite Julho 26": "40%",
        "Diferença 26 (p.p.)": quadro_exibicao["DIF_26"].apply(lambda x: f"{x:+.1f} p.p.".replace(".", ",") if pd.notna(x) else "-"),
        "Limite Julho 27": "30%",
        "Diferença 27 (p.p.)": quadro_exibicao["DIF_27"].apply(lambda x: f"{x:+.1f} p.p.".replace(".", ",") if pd.notna(x) else "-"),
    })

    col_q1, col_q2 = st.columns([4, 1])
    with col_q1:
        st.caption("Nota: Diferença positiva (+ p.p.) indica percentual acima do limite legal; negativa (- p.p.) indica dentro do limite.")
    with col_q2:
        st.download_button(
            label="⬇️ Exportar Quadro",
            data=to_excel_bytes(quadro_fmt, sheet_name="Quadro_Atual"),
            file_name=f"quadro_magisterio_{ano_sel}_{str(mes_sel).zfill(2)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_quadro_mag"
        )

    st.dataframe(quadro_fmt, use_container_width=True, hide_index=True, height=430)

    quadro_plot = quadro[quadro["QTDE_LEI"] > 0].copy()
    if not quadro_plot.empty:
        quadro_plot["ORGAO_CARREIRA"] = quadro_plot["INSTITUICAO"] + " - " + quadro_plot["DS_SIGLA_CARREIRA"]
        quadro_plot = quadro_plot.sort_values("PERCENTUAL", ascending=True)

        fig_q = px.bar(
            quadro_plot,
            x="PERCENTUAL",
            y="ORGAO_CARREIRA",
            orientation="h",
            text=quadro_plot["PERCENTUAL"].apply(lambda x: fmt_pct_br(x, 1)),
            labels={"PERCENTUAL": "% Contratos Temporários", "ORGAO_CARREIRA": "Órgão / Carreira"},
            color="PERCENTUAL",
            color_continuous_scale=["#FFA07A", "#FF7F50", "#FF4500", "#D2691E"]
        )
        fig_q.add_vline(x=50, line_dash="dash", line_color="#2d2d2d", annotation_text="Limite 2025 (50%)", annotation_position="top right")
        fig_q.add_vline(x=40, line_dash="dot", line_color="#555555", annotation_text="2026 (40%)", annotation_position="bottom right")
        fig_q.update_traces(textposition="outside")
        fig_q.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            coloraxis_showscale=False,
            margin=dict(l=0, r=40, t=25, b=0),
            height=max(320, len(quadro_plot) * 32)
        )
        st.plotly_chart(fig_q, use_container_width=True)

    st.divider()

    st.subheader("📈 Série Histórica — Histórico da Quantidade de servidores por órgão")

    hist_evol = (
        df_hist.groupby("PERIODO", as_index=False)
        .agg(QTDE_LEI=("QUANT_LEI", "sum"), QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum"))
        .sort_values("PERIODO")
    )
    hist_evol["PERCENTUAL"] = np.where(hist_evol["QTDE_LEI"] > 0, (hist_evol["QTDE_CT"] / hist_evol["QTDE_LEI"]) * 100, np.nan)

    fig_hist = px.line(
        hist_evol,
        x="PERIODO",
        y="PERCENTUAL",
        markers=True,
        text=hist_evol["PERCENTUAL"].apply(lambda x: fmt_pct_br(x, 1)),
        labels={"PERIODO": "Período (Ano/Mês)", "PERCENTUAL": "% Contratos Temporários"},
        color_discrete_sequence=["#D2691E"]
    )
    fig_hist.add_hline(y=50, line_dash="dash", line_color="#808080", annotation_text="Limite 2025 (50%)")
    fig_hist.add_hline(y=40, line_dash="dot", line_color="#A0522D", annotation_text="Limite 2026 (40%)")
    fig_hist.update_traces(textposition="top center")
    fig_hist.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_tickangle=-45,
        margin=dict(l=0, r=0, t=20, b=0),
        height=310
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    hist_agg = (
        df_hist.groupby(["INSTITUICAO", "DS_SIGLA_CARREIRA", "PERIODO"], as_index=False)
        .agg(QTDE_LEI=("QUANT_LEI", "sum"), QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum"))
    )
    hist_agg["PERCENTUAL"] = np.where(hist_agg["QTDE_LEI"] > 0, (hist_agg["QTDE_CT"] / hist_agg["QTDE_LEI"]) * 100, np.nan)

    periodos_ord = sorted(hist_agg["PERIODO"].unique())
    base_idx = hist_agg[["INSTITUICAO", "DS_SIGLA_CARREIRA"]].drop_duplicates().sort_values(["INSTITUICAO", "DS_SIGLA_CARREIRA"])

    tabela_hist_final = base_idx.rename(columns={"INSTITUICAO": "Órgão", "DS_SIGLA_CARREIRA": "Carreira"}).copy()

    for p in periodos_ord:
        sub_p = hist_agg[hist_agg["PERIODO"] == p].set_index(["INSTITUICAO", "DS_SIGLA_CARREIRA"])
        idx_tuplas = list(zip(base_idx["INSTITUICAO"], base_idx["DS_SIGLA_CARREIRA"]))

        lei_vals = [sub_p.loc[k, "QTDE_LEI"] if k in sub_p.index else np.nan for k in idx_tuplas]
        ct_vals = [sub_p.loc[k, "QTDE_CT"] if k in sub_p.index else np.nan for k in idx_tuplas]
        pct_vals = [sub_p.loc[k, "PERCENTUAL"] if k in sub_p.index else np.nan for k in idx_tuplas]

        tabela_hist_final[f"{p} | Qtde LEI"] = [fmt_int_br(v) if pd.notna(v) and v > 0 else "-" for v in lei_vals]
        tabela_hist_final[f"{p} | Contratos Temp."] = [fmt_int_br(v) if pd.notna(v) else "-" for v in ct_vals]
        tabela_hist_final[f"{p} | Percentual"] = [fmt_pct_br(v, 1) for v in pct_vals]

    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.caption(f"Histórico consolidado por órgão e carreira ({len(periodos_ord)} períodos)")
    with col_h2:
        st.download_button(
            label="⬇️ Exportar Histórico",
            data=to_excel_bytes(tabela_hist_final, sheet_name="Serie_Historica"),
            file_name="serie_historica_magisterio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_hist_mag"
        )

    st.dataframe(tabela_hist_final, use_container_width=True, hide_index=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3: ÍNDICE 35% - CONTRATOS (HISTORICO.XLSX)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Carregando base histórica de Contratos Temporários…")
def load_data_contratos_geral(source):
    xl = pd.ExcelFile(source)
    sheet = "QUERY_FOR_TRNSTRANSPOSED" if "QUERY_FOR_TRNSTRANSPOSED" in xl.sheet_names else 0
    df = pd.read_excel(xl, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    ref_str = df["ANO_MES"].astype(str).str.strip()
    if ref_str.str.contains("/").any():
        partes = ref_str.str.split("/", expand=True)
        df["ANO"] = pd.to_numeric(partes[0], errors="coerce").fillna(0).astype(int)
        df["MES"] = pd.to_numeric(partes[1], errors="coerce").fillna(0).astype(int)
    else:
        ref_num = pd.to_numeric(ref_str, errors="coerce").fillna(0).astype(int)
        df["ANO"] = (ref_num // 100).astype(int)
        df["MES"] = (ref_num % 100).astype(int)

    df = df[df["ANO"] > 0].copy()
    df["PERIODO"] = df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)

    df["SIGLA"] = df["SIGLA"].astype(str).str.strip()
    df["Efetivo"] = pd.to_numeric(df["Efetivo"], errors="coerce").fillna(0)
    df["Contrato/Designado"] = pd.to_numeric(df["Contrato/Designado"], errors="coerce").fillna(0)

    return df

def page_indice_35_contratos():
    st.markdown("""
    <h1 style="margin-top: 0.2rem; margin-bottom: 0.2rem;">ÍNDICE 35% - CONTRATOS</h1>
    <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Controle de Índice Legal — Art. 2º, § 3º do Decreto 48.097/2020 (Lei 23.750/2020)</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    arquivo_encontrado = encontrar_arquivo(["Historico.xlsx", "Histórico.xlsx", "Historico_Contratos.xlsx"])

    if arquivo_encontrado:
        df_ct = load_data_contratos_geral(arquivo_encontrado)
    else:
        uploaded_ct = st.file_uploader(
            "📂 Selecione a planilha Historico.xlsx (aba QUERY_FOR_TRNSTRANSPOSED)",
            type=["xlsx"],
            key="up_ct_geral"
        )
        if uploaded_ct:
            df_ct = load_data_contratos_geral(uploaded_ct)
        else:
            st.info("Aguardando o arquivo `Historico.xlsx` para iniciar o painel Índice 35% - Contratos.")
            st.stop()

    # ── Filtros na Sidebar ──
    st.sidebar.markdown("### 🔍 Filtros — Índice 35%", unsafe_allow_html=True)

    anos_disp = sorted(df_ct["ANO"].unique())
    ano_sel = st.sidebar.selectbox(
        "Ano de Referência",
        options=anos_disp,
        index=len(anos_disp) - 1,
        key="ano_ct_geral"
    )

    meses_do_ano = sorted(df_ct[df_ct["ANO"] == ano_sel]["MES"].unique())
    mes_sel = st.sidebar.selectbox(
        "Mês de Referência",
        options=meses_do_ano,
        index=len(meses_do_ano) - 1,
        format_func=lambda m: f"{str(m).zfill(2)} - {MESES_PT.get(m, str(m))}",
        key="mes_ct_geral"
    )

    orgaos_disp = sorted(df_ct["SIGLA"].dropna().unique())
    orgaos_sel = st.sidebar.multiselect(
        "Órgão (SIGLA)",
        options=orgaos_disp,
        default=[],
        placeholder="Selecione o órgão...",
        key="org_ct_geral"
    )

    # Histórico respeita o filtro de órgão
    if orgaos_sel:
        df_hist = df_ct[df_ct["SIGLA"].isin(orgaos_sel)].copy()
    else:
        df_hist = df_ct.copy()

    # Recorte do mês/ano selecionado
    df_atual = df_hist[(df_hist["ANO"] == ano_sel) & (df_hist["MES"] == mes_sel)].copy()

    if df_atual.empty:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")
        st.stop()

    # ── 6 Cards de KPIs empilhados um abaixo do outro ──
    mes_ref_texto = f"{MESES_PT.get(mes_sel, '').upper()} DE {ano_sel}"
    total_ef = df_atual["Efetivo"].sum()
    total_ct = df_atual["Contrato/Designado"].sum()
    perc_ct = (total_ct / total_ef * 100) if total_ef > 0 else 0.0
    limite_35 = total_ef * 0.35
    margem = limite_35 - total_ct

    st.metric("📅 Mês de Referência", mes_ref_texto)
    st.metric("🏛️ Efetivos (EF)", fmt_int_br(total_ef))
    st.metric("📝 Contrato Temp. (CT)", fmt_int_br(total_ct))
    st.metric("📊 % Contratos Temp.", fmt_pct_br(perc_ct, 2))
    st.metric("⚖️ Limite de 35% (L)", fmt_int_br(limite_35))
    st.metric("📉 Margem (M)", fmt_int_br(margem))

    # ── Caixa de Objetivo e Metodologia ──
    st.markdown("""
    <div class="objetivo-box">
        <strong>Objetivo:</strong> Averiguar o cumprimento do índice máximo de <strong>35%</strong> de servidores 
        contratados em relação ao total de servidores efetivos em exercício no quadro civil do Poder Executivo de MG 
        conforme previsto no <strong>Art. 2º, § 3º do Decreto 48.097/2020</strong> (que regulamenta a <strong>Lei 23.750/2020</strong>).<br>
        <strong>Metodologia:</strong> Foi considerado como contratos os servidores na situação funcional "Contrato Temporário" 
        com natureza de ingresso relacionada a insuficiência de servidores efetivos nos quadros da administração pública: 
        os servidores na situação funcional "Convocado" não pertencentes às carreiras de PEB, EEB, ANE-IE e PES foram considerados como convocados.
    </div>
    """, unsafe_allow_html=True)

    # ── Layout Principal: Tabela à esquerda + 2 Gráficos à direita ──
    col_esq, col_dir = st.columns([2, 3])

    with col_esq:
        st.subheader("📋 Quantidade de servidores por órgão")

        tab_org = (
            df_atual.groupby("SIGLA", as_index=False)
            .agg(
                QTDE_EF=("Efetivo", "sum"),
                QTDE_CT=("Contrato/Designado", "sum")
            )
            .sort_values("SIGLA")
        )
        tab_org["PERCENTUAL"] = np.where(
            tab_org["QTDE_EF"] > 0,
            (tab_org["QTDE_CT"] / tab_org["QTDE_EF"]) * 100,
            np.nan
        )

        linha_tot = pd.DataFrame([{
            "SIGLA": "TOTAL GERAL",
            "QTDE_EF": total_ef,
            "QTDE_CT": total_ct,
            "PERCENTUAL": (total_ct / total_ef * 100) if total_ef > 0 else np.nan
        }])
        tab_org_full = pd.concat([tab_org, linha_tot], ignore_index=True)

        tab_org_fmt = pd.DataFrame({
            "SIGLA": tab_org_full["SIGLA"],
            "Qtde Efetivos": tab_org_full["QTDE_EF"].apply(fmt_int_br),
            "Qtde Contratos Temp.": tab_org_full["QTDE_CT"].apply(fmt_int_br),
            "Percentual": tab_org_full["PERCENTUAL"].apply(
                lambda x: "0%" if pd.notna(x) and x == 0 else fmt_pct_br(x, 2)
            )
        })

        st.download_button(
            label="⬇️ Exportar Tabela por Órgão",
            data=to_excel_bytes(tab_org_fmt, sheet_name="Indice_35_Por_Orgao"),
            file_name=f"indice_35_contratos_{ano_sel}_{str(mes_sel).zfill(2)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_ct_orgaos"
        )

        st.dataframe(tab_org_fmt, use_container_width=True, hide_index=True, height=620)

    with col_dir:
        # Gráfico 1: Série Histórica dos Contratos Temporários vs Limite Máximo (35%)
        st.subheader("📈 Série Histórica dos Contratos Temporários")

        hist_ct = (
            df_hist.groupby("PERIODO", as_index=False)
            .agg(
                QTDE_EF=("Efetivo", "sum"),
                QTDE_CT=("Contrato/Designado", "sum")
            )
            .sort_values("PERIODO")
        )
        hist_ct["LIMITE_MAX"] = hist_ct["QTDE_EF"] * 0.35

        fig_hist_ct = go.Figure()
        fig_hist_ct.add_trace(go.Scatter(
            x=hist_ct["PERIODO"],
            y=hist_ct["QTDE_CT"],
            mode="lines+markers",
            name="Qtde de Contratos",
            line=dict(color="#D2691E", width=2.5),
            marker=dict(size=5)
        ))
        fig_hist_ct.add_trace(go.Scatter(
            x=hist_ct["PERIODO"],
            y=hist_ct["LIMITE_MAX"],
            mode="lines+markers",
            name="Limite Máximo (35%)",
            line=dict(color="#808080", width=2, dash="dash"),
            marker=dict(size=4)
        ))
        fig_hist_ct.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="x unified",
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=10, t=30, b=0),
            height=290
        )
        st.plotly_chart(fig_hist_ct, use_container_width=True)

        # Gráfico 2: Qtde de contratos temporários por Órgão (Top 10 + Outros + TOTAL)
        st.subheader(f"🏛️ Qtde de contratos temporários por Órgão ({mes_ref_texto})")

        ct_positivos = tab_org[tab_org["QTDE_CT"] > 0].sort_values("QTDE_CT", ascending=False).copy()

        if not ct_positivos.empty and total_ct > 0:
            if len(ct_positivos) > 10:
                top10 = ct_positivos.head(10).copy()
                outros_val = ct_positivos.iloc[10:]["QTDE_CT"].sum()
                linha_outros = pd.DataFrame([{"SIGLA": "Outros", "QTDE_CT": outros_val}])
                df_barras = pd.concat([top10[["SIGLA", "QTDE_CT"]], linha_outros], ignore_index=True)
            else:
                df_barras = ct_positivos[["SIGLA", "QTDE_CT"]].copy()

            linha_total_bar = pd.DataFrame([{"SIGLA": "TOTAL", "QTDE_CT": total_ct}])
            df_barras = pd.concat([df_barras, linha_total_bar], ignore_index=True)

            df_barras["PARTICIPACAO"] = (df_barras["QTDE_CT"] / total_ct) * 100
            df_barras["ROTULO"] = (
                df_barras["PARTICIPACAO"].apply(lambda p: fmt_pct_br(p, 2))
                + "  |  "
                + df_barras["QTDE_CT"].apply(fmt_int_br)
            )

            df_barras_plot = df_barras.iloc[::-1].reset_index(drop=True)
            cores = ["#A0522D" if s == "TOTAL" else "#D2691E" for s in df_barras_plot["SIGLA"]]

            fig_bar_ct = go.Figure(go.Bar(
                x=df_barras_plot["QTDE_CT"],
                y=df_barras_plot["SIGLA"],
                orientation="h",
                text=df_barras_plot["ROTULO"],
                textposition="outside",
                marker_color=cores
            ))
            fig_bar_ct.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis=dict(range=[0, df_barras_plot["QTDE_CT"].max() * 1.32], showticklabels=False),
                margin=dict(l=0, r=20, t=10, b=0),
                height=340
            )
            st.plotly_chart(fig_bar_ct, use_container_width=True)
        else:
            st.info("Não há contratos temporários registrados para os filtros selecionados neste período.")

# ── 7. EXECUÇÃO PRINCIPAL E MENU DE NAVEGAÇÃO ───────────────────────────────
def main():
    setup_page()

    PAGINAS = {
        "📊 Lotação de Pessoal": page_lotacao,
        "🎓 Contratos Temporários - Magistério": page_magisterio,
        "📉 Índice 35% - Contratos": page_indice_35_contratos,
    }

    st.sidebar.markdown("### 🧭 Navegação", unsafe_allow_html=True)
    pagina_selecionada = st.sidebar.radio(
        "Selecione o painel:",
        options=list(PAGINAS.keys()),
        label_visibility="collapsed",
    )
    st.sidebar.divider()

    PAGINAS[pagina_selecionada]()

    st.sidebar.divider()
    st.sidebar.caption("Dashboard RH – DCGFT MG\nFeito com Streamlit 🚀")

if __name__ == "__main__":
    main()
