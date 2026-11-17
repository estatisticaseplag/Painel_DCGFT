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

def encontrar_arquivo_por_aba(nome_aba_alvo):
    """Procura um arquivo .xlsx na pasta que contenha a aba especificada."""
    try:
        for f in os.listdir("."):
            if f.lower().endswith(".xlsx"):
                try:
                    xl = pd.ExcelFile(f)
                    if nome_aba_alvo in xl.sheet_names:
                        return f
                except Exception:
                    continue
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
        
        /* ── CARDS DE KPI HORIZONTAIS E RESPONSIVOS ── */
        [data-testid="stMetric"] { 
            background: #ffffff; 
            border-radius: 8px; 
            padding: 10px 12px !important; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            border: 1px solid #e5e7eb;
            border-left: 4px solid #D2691E;
            min-width: 0 !important;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] *,
        div[data-testid="stMetricLabel"] p { 
            font-size: 0.70rem !important; 
            color: #666666 !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            white-space: normal !important;
            word-break: break-word !important;
            overflow: visible !important;
            text-overflow: unset !important;
            line-height: 1.2 !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #D2691E !important;
            font-weight: 700 !important;
            font-size: clamp(0.88rem, 1.08vw, 1.35rem) !important;
            white-space: nowrap !important;
        }
        
        h1 { 
            color: #2d2d2d;
            font-weight: 700;
            font-size: 1.8rem;
            margin-bottom: 0.2rem;
        }
        
        h3 {
            color: #444;
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
            padding: 12px 16px;
            font-size: 0.88rem;
            color: #333;
            line-height: 1.45;
            margin-top: 0.6rem;
            margin-bottom: 1.1rem;
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
            padding: 0.45rem 1.2rem;
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
    df["ANO_MES_STR"] = (df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)).astype("category")

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
    filtros["anos"] = st.sidebar.multiselect("Ano de Referência", anos_disp, default=anos_disp[-3:], placeholder="Selecione o ano...")
    filtros["meses"] = st.sidebar.multiselect("Mês", sorted(df["MES"].unique()), default=[], placeholder="Selecione o mês...")
    filtros["carreira"] = st.sidebar.multiselect("Sigla da Carreira", sorted(df["DS_SIGLA_CARREIRA"].dropna().unique()), default=[], placeholder="Selecione a carreira...")

    col_inst = "DS_SIGLA_INST_LOTACAO" if "DS_SIGLA_INST_LOTACAO" in df.columns else "DS_SIGLA_INST_DOTACAO"
    filtros["inst"] = st.sidebar.multiselect("Órgão / Instituição de Lotação", sorted(df[col_inst].dropna().unique()), default=[], placeholder="Selecione o órgão...")
    filtros["sit_func"] = st.sidebar.multiselect("Situação Funcional", sorted(df["SIT_FUNCIONAL_AGRUPADA_REV"].dropna().unique()), default=[], placeholder="Selecione a situação...")
    filtros["sit_serv"] = st.sidebar.multiselect("Situação do Servidor", sorted(df["SIT_SERVIDOR_AGRUPADA"].dropna().unique()), default=[], placeholder="Selecione a situação...")
    filtros["remun"] = st.sidebar.multiselect("Remuneração Diferenciada", sorted(df["REMUN_DIF_0_REV"].dropna().unique()), default=[], placeholder="Selecione a opção...")
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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👤 Servidores", fmt_int_br(total_servidores))
    c2.metric("🏛️ Órgãos", f"{n_orgaos}")
    c3.metric("📋 Carreiras", f"{n_carreiras}")
    c4.metric("⏱️ CH Total (h)", fmt_int_br(total_ch))
    c5.metric("⏱️ CH Média (h)", f"{media_ch:,.1f}".replace(".", ","))

    st.divider()

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("📈 Evolução de Servidores por Mês/Ano")
        evol = dff.groupby("ANO_MES_STR", observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index().sort_values("ANO_MES_STR")
        fig_evol = px.line(evol, x="ANO_MES_STR", y="COUNT_NR_MASP_ADM", markers=True,
                           labels={"ANO_MES_STR": "Período", "COUNT_NR_MASP_ADM": "Servidores"}, color_discrete_sequence=["#D2691E"])
        fig_evol.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig_evol, use_container_width=True)

    with col2:
        st.subheader("🏷️ Por Situação Funcional e Ano")
        sit_func_ano = dff.groupby(["ANO", "SIT_FUNCIONAL_AGRUPADA_REV"], observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index()
        fig_sit = px.bar(sit_func_ano, x="ANO", y="COUNT_NR_MASP_ADM", color="SIT_FUNCIONAL_AGRUPADA_REV",
                         labels={"ANO": "Ano", "COUNT_NR_MASP_ADM": "Servidores", "SIT_FUNCIONAL_AGRUPADA_REV": "Situação Funcional"},
                         color_discrete_sequence=["#FF4500", "#808080", "#D2691E", "#A0522D", "#CD853F", "#DEB887"])
        fig_sit.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=True,
                              legend=dict(orientation="v", font=dict(size=9), yanchor="top", y=1),
                              margin=dict(l=0, r=0, t=10, b=0), height=300, barmode="stack")
        st.plotly_chart(fig_sit, use_container_width=True)

    st.subheader("⏱️ Evolução de Carga Horária por Mês/Ano")
    evol_ch = dff.groupby("ANO_MES_STR", observed=True)["SUM_CH_FINAL"].sum().reset_index().sort_values("ANO_MES_STR")
    fig_evol_ch = px.line(evol_ch, x="ANO_MES_STR", y="SUM_CH_FINAL", markers=True,
                          labels={"ANO_MES_STR": "Período", "SUM_CH_FINAL": "Carga Horária Total (h)"}, color_discrete_sequence=["#C85A17"])
    fig_evol_ch.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=20), height=300)
    st.plotly_chart(fig_evol_ch, use_container_width=True)

    st.divider()
    st.subheader("👔 Por Situação do Servidor")
    sit_serv_agg = dff.groupby("SIT_SERVIDOR_AGRUPADA", observed=True)["COUNT_NR_MASP_ADM"].sum().reset_index()
    fig_serv = px.bar(sit_serv_agg.sort_values("COUNT_NR_MASP_ADM", ascending=False), x="SIT_SERVIDOR_AGRUPADA", y="COUNT_NR_MASP_ADM",
                      labels={"SIT_SERVIDOR_AGRUPADA": "Situação do Servidor", "COUNT_NR_MASP_ADM": "Servidores"},
                      color="SIT_SERVIDOR_AGRUPADA", color_discrete_sequence=["#FF4500", "#D2691E", "#A0522D"])
    fig_serv.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_serv, use_container_width=True)

    st.divider()
    st.subheader("📊 Tabela de Dados Filtrados")
    tabela = (
        dff.groupby(["NR_ANO_MES_REF", col_inst, "DS_NOME_CARREIRA", "SIT_FUNCIONAL_AGRUPADA_REV", "SIT_SERVIDOR_AGRUPADA", "REMUN_DIF_0_REV"], as_index=False, observed=True)
        .agg(SERVIDORES=("COUNT_NR_MASP_ADM", "sum"), CH_TOTAL=("SUM_CH_FINAL", "sum"))
        .sort_values(["NR_ANO_MES_REF", "SERVIDORES"], ascending=[True, False])
    )

    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.caption(f"Exibindo {len(tabela):,} linhas agrupadas")
    with col_t2:
        st.download_button("⬇️ Exportar Excel", data=to_excel_bytes(tabela, "Lotacao_Filtrada"),
                           file_name="lotacao_filtrada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.dataframe(tabela, use_container_width=True, height=380, column_config={
        "NR_ANO_MES_REF": st.column_config.NumberColumn("Período", format="%d"),
        col_inst: "Órgão Lotação",
        "DS_NOME_CARREIRA": "Carreira",
        "SIT_FUNCIONAL_AGRUPADA_REV": "Sit. Funcional",
        "SIT_SERVIDOR_AGRUPADA": "Sit. Servidor",
        "REMUN_DIF_0_REV": "Rem. Diferenciada",
        "SERVIDORES": st.column_config.NumberColumn("Servidores", format="%d"),
        "CH_TOTAL": st.column_config.NumberColumn("CH Total (h)", format="%d"),
    })

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
        uploaded_mag = st.file_uploader("📂 Selecione a planilha BASE_PAINEL.xlsx (aba APPEND_TABLE)", type=["xlsx"], key="up_magisterio")
        if uploaded_mag:
            df_mag = load_data_magisterio(uploaded_mag)
        else:
            st.info("Aguardando o arquivo `BASE_PAINEL.xlsx` para iniciar o painel do Magistério.")
            st.stop()

    st.sidebar.markdown("### 🔍 Filtros — Magistério", unsafe_allow_html=True)
    anos_disp = sorted(df_mag["ANO"].unique())
    ano_sel = st.sidebar.selectbox("Ano de Referência (Quadro Atual)", options=anos_disp, index=len(anos_disp) - 1, key="ano_mag")
    meses_do_ano = sorted(df_mag[df_mag["ANO"] == ano_sel]["MES"].unique())
    mes_sel = st.sidebar.selectbox("Mês de Referência (Quadro Atual)", options=meses_do_ano, index=len(meses_do_ano) - 1,
                                   format_func=lambda m: f"{str(m).zfill(2)} - {MESES_PT.get(m, str(m))}", key="mes_mag")
    carreiras_sel = st.sidebar.multiselect("Sigla da Carreira", options=sorted(df_mag["DS_SIGLA_CARREIRA"].dropna().unique()), default=[], placeholder="Selecione a carreira...", key="carr_mag")
    orgaos_sel = st.sidebar.multiselect("Órgão / Instituição", options=sorted(df_mag["INSTITUICAO"].dropna().unique()), default=[], placeholder="Selecione o órgão...", key="org_mag")

    mask_hist = pd.Series([True] * len(df_mag), index=df_mag.index)
    if carreiras_sel: mask_hist &= df_mag["DS_SIGLA_CARREIRA"].isin(carreiras_sel)
    if orgaos_sel: mask_hist &= df_mag["INSTITUICAO"].isin(orgaos_sel)
    df_hist = df_mag[mask_hist].copy()
    df_atual = df_hist[(df_hist["ANO"] == ano_sel) & (df_hist["MES"] == mes_sel)].copy()

    if df_atual.empty:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")
        st.stop()

    mes_ref_texto = f"{MESES_PT.get(mes_sel, '').upper()} DE {ano_sel}"
    total_lei = df_atual["QUANT_LEI"].sum()
    total_ct = df_atual["COUNT_of_NR_MASP_ADM"].sum()
    perc_ct = (total_ct / total_lei * 100) if total_lei > 0 else 0.0
    taxa_limite = 0.50 if ano_sel <= 2025 else (0.40 if ano_sel == 2026 else 0.30)
    limite_qtd = total_lei * taxa_limite
    margem = limite_qtd - total_ct

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📅 Mês de Referência", mes_ref_texto)
    c2.metric("🏛️ Quant. em Lei (EF)", fmt_int_br(total_lei))
    c3.metric("📝 Contrato Temp. (CT)", fmt_int_br(total_ct))
    c4.metric("📊 % Contratos Temp.", fmt_pct_br(perc_ct, 2))
    c5.metric(f"⚖️ Limite de {int(taxa_limite*100)}%", fmt_int_br(limite_qtd))
    c6.metric("📉 Margem", fmt_int_br(margem))

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
        .agg(QTDE_LEI=("QUANT_LEI", "sum"), QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum"))
        .sort_values(["INSTITUICAO", "DS_SIGLA_CARREIRA"])
    )
    quadro["PERCENTUAL"] = np.where(quadro["QTDE_LEI"] > 0, (quadro["QTDE_CT"] / quadro["QTDE_LEI"]) * 100, np.nan)
    quadro["DIF_25"] = quadro["PERCENTUAL"] - 50.0
    quadro["DIF_26"] = quadro["PERCENTUAL"] - 40.0
    quadro["DIF_27"] = quadro["PERCENTUAL"] - 30.0

    perc_total = (total_ct / total_lei * 100) if total_lei > 0 else np.nan
    linha_total = pd.DataFrame([{
        "INSTITUICAO": "TOTAL GERAL", "DS_SIGLA_CARREIRA": "-", "QTDE_LEI": total_lei, "QTDE_CT": total_ct,
        "PERCENTUAL": perc_total,
        "DIF_25": perc_total - 50.0 if not pd.isna(perc_total) else np.nan,
        "DIF_26": perc_total - 40.0 if not pd.isna(perc_total) else np.nan,
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
        st.download_button("⬇️ Exportar Quadro", data=to_excel_bytes(quadro_fmt, "Quadro_Atual"),
                           file_name=f"quadro_magisterio_{ano_sel}_{str(mes_sel).zfill(2)}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_quadro_mag")

    st.dataframe(quadro_fmt, use_container_width=True, hide_index=True, height=430)

    quadro_plot = quadro[quadro["QTDE_LEI"] > 0].copy()
    if not quadro_plot.empty:
        quadro_plot["ORGAO_CARREIRA"] = quadro_plot["INSTITUICAO"] + " - " + quadro_plot["DS_SIGLA_CARREIRA"]
        quadro_plot = quadro_plot.sort_values("PERCENTUAL", ascending=True)
        fig_q = px.bar(quadro_plot, x="PERCENTUAL", y="ORGAO_CARREIRA", orientation="h",
                       text=quadro_plot["PERCENTUAL"].apply(lambda x: fmt_pct_br(x, 1)),
                       labels={"PERCENTUAL": "% Contratos Temporários", "ORGAO_CARREIRA": "Órgão / Carreira"},
                       color="PERCENTUAL", color_continuous_scale=["#FFA07A", "#FF7F50", "#FF4500", "#D2691E"])
        fig_q.add_vline(x=50, line_dash="dash", line_color="#2d2d2d", annotation_text="Limite 2025 (50%)", annotation_position="top right")
        fig_q.add_vline(x=40, line_dash="dot", line_color="#555555", annotation_text="2026 (40%)", annotation_position="bottom right")
        fig_q.update_traces(textposition="outside")
        fig_q.update_layout(plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False, margin=dict(l=0, r=40, t=25, b=0), height=max(320, len(quadro_plot) * 32))
        st.plotly_chart(fig_q, use_container_width=True)

    st.divider()
    st.subheader("📈 Série Histórica — Histórico da Quantidade de servidores por órgão")
    hist_evol = df_hist.groupby("PERIODO", as_index=False).agg(QTDE_LEI=("QUANT_LEI", "sum"), QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum")).sort_values("PERIODO")
    hist_evol["PERCENTUAL"] = np.where(hist_evol["QTDE_LEI"] > 0, (hist_evol["QTDE_CT"] / hist_evol["QTDE_LEI"]) * 100, np.nan)

    fig_hist = px.line(hist_evol, x="PERIODO", y="PERCENTUAL", markers=True,
                       text=hist_evol["PERCENTUAL"].apply(lambda x: fmt_pct_br(x, 1)),
                       labels={"PERIODO": "Período (Ano/Mês)", "PERCENTUAL": "% Contratos Temporários"}, color_discrete_sequence=["#D2691E"])
    fig_hist.add_hline(y=50, line_dash="dash", line_color="#808080", annotation_text="Limite 2025 (50%)")
    fig_hist.add_hline(y=40, line_dash="dot", line_color="#A0522D", annotation_text="Limite 2026 (40%)")
    fig_hist.update_traces(textposition="top center")
    fig_hist.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45, margin=dict(l=0, r=0, t=20, b=0), height=310)
    st.plotly_chart(fig_hist, use_container_width=True)

    hist_agg = df_hist.groupby(["INSTITUICAO", "DS_SIGLA_CARREIRA", "PERIODO"], as_index=False).agg(QTDE_LEI=("QUANT_LEI", "sum"), QTDE_CT=("COUNT_of_NR_MASP_ADM", "sum"))
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
        st.download_button("⬇️ Exportar Histórico", data=to_excel_bytes(tabela_hist_final, "Serie_Historica"),
                           file_name="serie_historica_magisterio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, key="dl_hist_mag")

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
        uploaded_ct = st.file_uploader("📂 Selecione a planilha Historico.xlsx (aba QUERY_FOR_TRNSTRANSPOSED)", type=["xlsx"], key="up_ct_geral")
        if uploaded_ct:
            df_ct = load_data_contratos_geral(uploaded_ct)
        else:
            st.info("Aguardando o arquivo `Historico.xlsx` para iniciar o painel Índice 35% - Contratos.")
            st.stop()

    st.sidebar.markdown("### 🔍 Filtros — Índice 35%", unsafe_allow_html=True)
    anos_disp = sorted(df_ct["ANO"].unique())
    ano_sel = st.sidebar.selectbox("Ano de Referência", options=anos_disp, index=len(anos_disp) - 1, key="ano_ct_geral")
    meses_do_ano = sorted(df_ct[df_ct["ANO"] == ano_sel]["MES"].unique())
    mes_sel = st.sidebar.selectbox("Mês de Referência", options=meses_do_ano, index=len(meses_do_ano) - 1,
                                   format_func=lambda m: f"{str(m).zfill(2)} - {MESES_PT.get(m, str(m))}", key="mes_ct_geral")
    orgaos_sel = st.sidebar.multiselect("Órgão (SIGLA)", options=sorted(df_ct["SIGLA"].dropna().unique()), default=[], placeholder="Selecione o órgão...", key="org_ct_geral")

    df_hist = df_ct[df_ct["SIGLA"].isin(orgaos_sel)].copy() if orgaos_sel else df_ct.copy()
    df_atual = df_hist[(df_hist["ANO"] == ano_sel) & (df_hist["MES"] == mes_sel)].copy()

    if df_atual.empty:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")
        st.stop()

    mes_ref_texto = f"{MESES_PT.get(mes_sel, '').upper()} DE {ano_sel}"
    total_ef = df_atual["Efetivo"].sum()
    total_ct = df_atual["Contrato/Designado"].sum()
    perc_ct = (total_ct / total_ef * 100) if total_ef > 0 else 0.0
    limite_35 = total_ef * 0.35
    margem = limite_35 - total_ct

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📅 Mês de Referência", mes_ref_texto)
    c2.metric("🏛️ Efetivos (EF)", fmt_int_br(total_ef))
    c3.metric("📝 Contrato Temp. (CT)", fmt_int_br(total_ct))
    c4.metric("📊 % Contratos Temp.", fmt_pct_br(perc_ct, 2))
    c5.metric("⚖️ Limite de 35% (L)", fmt_int_br(limite_35))
    c6.metric("📉 Margem (M)", fmt_int_br(margem))

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

    # Bloco 1: Tabela Servidores por Órgão
    tab_org = df_atual.groupby("SIGLA", as_index=False).agg(QTDE_EF=("Efetivo", "sum"), QTDE_CT=("Contrato/Designado", "sum")).sort_values("SIGLA")
    tab_org["PERCENTUAL"] = np.where(tab_org["QTDE_EF"] > 0, (tab_org["QTDE_CT"] / tab_org["QTDE_EF"]) * 100, np.nan)
    linha_tot = pd.DataFrame([{"SIGLA": "TOTAL GERAL", "QTDE_EF": total_ef, "QTDE_CT": total_ct, "PERCENTUAL": (total_ct / total_ef * 100) if total_ef > 0 else np.nan}])
    tab_org_full = pd.concat([tab_org, linha_tot], ignore_index=True)

    tab_org_fmt = pd.DataFrame({
        "SIGLA": tab_org_full["SIGLA"],
        "Qtde Efetivos": tab_org_full["QTDE_EF"].apply(fmt_int_br),
        "Qtde Contratos Temp.": tab_org_full["QTDE_CT"].apply(fmt_int_br),
        "Percentual": tab_org_full["PERCENTUAL"].apply(lambda x: "0%" if pd.notna(x) and x == 0 else fmt_pct_br(x, 2))
    })

    col_t1, col_t2 = st.columns([4.5, 1])
    with col_t1:
        st.subheader(f"📋 Servidores por Órgão ({mes_ref_texto})")
    with col_t2:
        st.download_button("⬇️ Exportar Excel", data=to_excel_bytes(tab_org_fmt, "Indice_35_Por_Orgao"),
                           file_name=f"indice_35_contratos_{ano_sel}_{str(mes_sel).zfill(2)}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_ct_orgaos")

    st.dataframe(tab_org_fmt, use_container_width=True, hide_index=True, height=450)
    st.divider()

    # Bloco 2: Série Histórica
    st.subheader("📈 Série Histórica dos Contratos Temporários")
    hist_ct = df_hist.groupby("PERIODO", as_index=False).agg(QTDE_EF=("Efetivo", "sum"), QTDE_CT=("Contrato/Designado", "sum")).sort_values("PERIODO")
    hist_ct["LIMITE_MAX"] = hist_ct["QTDE_EF"] * 0.35

    n_pts = len(hist_ct)
    indices_rotulo = {0, n_pts - 1}
    if n_pts > 10:
        indices_rotulo.update(range(0, n_pts, 6))

    fig_hist_ct = go.Figure()
    fig_hist_ct.add_trace(go.Scatter(
        x=hist_ct["PERIODO"], y=hist_ct["QTDE_CT"], mode="lines+markers+text", name="Qtde de Contratos",
        text=[fmt_int_br(v) if i in indices_rotulo else "" for i, v in enumerate(hist_ct["QTDE_CT"])],
        textposition="bottom center", textfont=dict(size=10, color="#B8551A"), line=dict(color="#D2691E", width=2.5), marker=dict(size=6)
    ))
    fig_hist_ct.add_trace(go.Scatter(
        x=hist_ct["PERIODO"], y=hist_ct["LIMITE_MAX"], mode="lines+markers+text", name="Limite Máximo (35%)",
        text=[fmt_int_br(v) if i in indices_rotulo else "" for i, v in enumerate(hist_ct["LIMITE_MAX"])],
        textposition="top center", textfont=dict(size=10, color="#555555"), line=dict(color="#808080", width=2, dash="dash"), marker=dict(size=5)
    ))
    y_max_hist = max(hist_ct["LIMITE_MAX"].max(), hist_ct["QTDE_CT"].max()) * 1.15
    fig_hist_ct.update_layout(plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified", xaxis=dict(tickangle=-45, nticks=20),
                              yaxis=dict(range=[0, y_max_hist], gridcolor="#eeeeee"),
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=10, t=30, b=0), height=340)
    st.plotly_chart(fig_hist_ct, use_container_width=True)
    st.divider()

    # Bloco 3: Contratos Temporários por Órgão
    st.subheader(f"🏛️ Contratos Temporários por Órgão ({mes_ref_texto})")
    ct_positivos = tab_org[tab_org["QTDE_CT"] > 0].sort_values("QTDE_CT", ascending=False).copy()

    if not ct_positivos.empty and total_ct > 0:
        if len(ct_positivos) > 10:
            top10 = ct_positivos.head(10).copy()
            outros_val = ct_positivos.iloc[10:]["QTDE_CT"].sum()
            df_barras = pd.concat([top10[["SIGLA", "QTDE_CT"]], pd.DataFrame([{"SIGLA": "Outros", "QTDE_CT": outros_val}])], ignore_index=True)
        else:
            df_barras = ct_positivos[["SIGLA", "QTDE_CT"]].copy()

        df_barras = pd.concat([df_barras, pd.DataFrame([{"SIGLA": "TOTAL", "QTDE_CT": total_ct}])], ignore_index=True)
        df_barras["PARTICIPACAO"] = (df_barras["QTDE_CT"] / total_ct) * 100
        df_barras["ROTULO"] = df_barras["PARTICIPACAO"].apply(lambda p: fmt_pct_br(p, 2)) + "  |  " + df_barras["QTDE_CT"].apply(fmt_int_br)
        df_barras_plot = df_barras.iloc[::-1].reset_index(drop=True)
        cores = ["#A0522D" if s == "TOTAL" else "#D2691E" for s in df_barras_plot["SIGLA"]]

        fig_bar_ct = go.Figure(go.Bar(x=df_barras_plot["QTDE_CT"], y=df_barras_plot["SIGLA"], orientation="h",
                                      text=df_barras_plot["ROTULO"], textposition="outside", textfont=dict(size=11, color="#333333"), marker_color=cores))
        fig_bar_ct.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                 xaxis=dict(range=[0, df_barras_plot["QTDE_CT"].max() * 1.25], showticklabels=False, showgrid=False),
                                 yaxis=dict(tickfont=dict(size=11)), margin=dict(l=0, r=20, t=10, b=0), height=400)
        st.plotly_chart(fig_bar_ct, use_container_width=True)
    else:
        st.info("Não há contratos temporários registrados para os filtros selecionados neste período.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4: CONTROLE DE VAGAS (DADOS_VAGAS_REV.PARQUET / XLSX)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Carregando base de Controle de Vagas…")
def load_data_vagas(source):
    is_parquet = (
        (isinstance(source, str) and source.lower().endswith(".parquet"))
        or (hasattr(source, "name") and source.name.lower().endswith(".parquet"))
    )

    if is_parquet:
        df = pd.read_parquet(source)
    else:
        xl = pd.ExcelFile(source)
        sheet = "QUERY_FOR_VACANCIA_AGOV_GGO_000" if "QUERY_FOR_VACANCIA_AGOV_GGO_000" in xl.sheet_names else 0
        df = pd.read_excel(xl, sheet_name=sheet)

    df.columns = [str(c).strip() for c in df.columns]

    cols_texto = [
        "SG_INSTITUICAO", "DS_SITVAGA", "DS_CARGO", "TP_CARGO",
        "CD_CARGO", "DDCDRECRUTAMENTO", "DS_CARGO_ATUALIZADO"
    ]
    for col in cols_texto:
        if col in df.columns:
            df[col] = (
                df[col]
                .replace("", np.nan)
                .fillna("Não informado")
                .astype(str)
                .str.strip()
                .astype("category")
            )

    if "CD_ORCAMENTO" in df.columns:
        df["CD_ORCAMENTO_STR"] = (
            pd.to_numeric(df["CD_ORCAMENTO"], errors="coerce")
            .fillna(0)
            .astype(int)
            .astype(str)
            .astype("category")
        )
    if "DDCDSITVAGA" in df.columns:
        df["DDCDSITVAGA_STR"] = (
            pd.to_numeric(df["DDCDSITVAGA"], errors="coerce")
            .fillna(-1)
            .astype(int)
            .astype(str)
            .astype("category")
        )

    return df

def page_controle_vagas():
    st.markdown("""
    <h1 style="margin-top: 0.2rem; margin-bottom: 0.2rem;">CONTROLE DE VAGAS</h1>
    <p style="color: #666; font-size: 1.1rem; margin-top: 0;">Quadro de Vagas por Situação, Órgão e Cargo</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    arquivo_vagas = encontrar_arquivo([
        "DADOS_VAGAS_rev.parquet", "DADOS_VAGAS.parquet", "BASE_VAGAS.parquet",
        "DADOS_VAGAS_rev.xlsx", "DADOS_VAGAS.xlsx", "BASE_VAGAS.xlsx"
    ])
    if not arquivo_vagas:
        arquivo_vagas = encontrar_arquivo_por_aba("QUERY_FOR_VACANCIA_AGOV_GGO_000")

    if arquivo_vagas:
        df_vagas = load_data_vagas(arquivo_vagas)
    else:
        uploaded_vagas = st.file_uploader(
            "📂 Selecione a base de vagas (DADOS_VAGAS_rev.parquet ou .xlsx)",
            type=["parquet", "xlsx"],
            key="up_vagas"
        )
        if uploaded_vagas:
            df_vagas = load_data_vagas(uploaded_vagas)
        else:
            st.info("Aguardando o arquivo `DADOS_VAGAS_rev.parquet` para iniciar o painel de Controle de Vagas.")
            st.stop()

    # ── Filtros na Sidebar ──
    st.sidebar.markdown("### 🔍 Filtros — Controle de Vagas", unsafe_allow_html=True)

    ano_sel_vagas = None
    mes_sel_vagas = None
    if "ANO_FTL" in df_vagas.columns:
        anos_v = sorted(df_vagas["ANO_FTL"].dropna().unique())
        ano_sel_vagas = st.sidebar.multiselect("Ano (ANO_FTL)", options=anos_v, default=[anos_v[-1]] if anos_v else [], key="ano_vagas")
    if "MES_FTL" in df_vagas.columns:
        meses_v = sorted(df_vagas["MES_FTL"].dropna().unique())
        mes_sel_vagas = st.sidebar.multiselect("Mês (MES_FTL)", options=meses_v, default=[meses_v[-1]] if meses_v else [], key="mes_vagas")

    inst_sel = st.sidebar.multiselect(
        "Sigla Instituição",
        options=sorted(df_vagas["SG_INSTITUICAO"].unique()) if "SG_INSTITUICAO" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione a instituição...",
        key="inst_vagas"
    )

    cod_inst_sel = st.sidebar.multiselect(
        "Código Instituição",
        options=sorted(df_vagas["CD_ORCAMENTO_STR"].unique(), key=lambda x: int(x) if x.isdigit() else 999999) if "CD_ORCAMENTO_STR" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione o código...",
        key="cod_inst_vagas"
    )

    sit_vaga_sel = st.sidebar.multiselect(
        "Situação Vaga",
        options=sorted(df_vagas["DS_SITVAGA"].unique()) if "DS_SITVAGA" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione a situação...",
        key="sit_vagas"
    )

    cod_vaga_sel = st.sidebar.multiselect(
        "Código Vaga (Situação)",
        options=sorted(df_vagas["DDCDSITVAGA_STR"].unique(), key=lambda x: int(x) if x.lstrip("-").isdigit() else 999) if "DDCDSITVAGA_STR" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione o código...",
        key="cod_sit_vagas"
    )

    cargo_sel = st.sidebar.multiselect(
        "Descrição Cargo",
        options=sorted(df_vagas["DS_CARGO"].unique()) if "DS_CARGO" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione o cargo...",
        key="cargo_vagas"
    )

    tp_cargo_sel = st.sidebar.multiselect(
        "Tipo do Cargo",
        options=sorted(df_vagas["TP_CARGO"].unique()) if "TP_CARGO" in df_vagas.columns else [],
        default=[],
        placeholder="Selecione o tipo...",
        key="tp_cargo_vagas"
    )

    # Aplicação dos filtros
    mask = pd.Series([True] * len(df_vagas), index=df_vagas.index)
    if ano_sel_vagas and "ANO_FTL" in df_vagas.columns:
        mask &= df_vagas["ANO_FTL"].isin(ano_sel_vagas)
    if mes_sel_vagas and "MES_FTL" in df_vagas.columns:
        mask &= df_vagas["MES_FTL"].isin(mes_sel_vagas)
    if inst_sel:
        mask &= df_vagas["SG_INSTITUICAO"].isin(inst_sel)
    if cod_inst_sel:
        mask &= df_vagas["CD_ORCAMENTO_STR"].isin(cod_inst_sel)
    if sit_vaga_sel:
        mask &= df_vagas["DS_SITVAGA"].isin(sit_vaga_sel)
    if cod_vaga_sel:
        mask &= df_vagas["DDCDSITVAGA_STR"].isin(cod_vaga_sel)
    if cargo_sel:
        mask &= df_vagas["DS_CARGO"].isin(cargo_sel)
    if tp_cargo_sel:
        mask &= df_vagas["TP_CARGO"].isin(tp_cargo_sel)

    dff = df_vagas[mask]

    if dff.empty:
        st.warning("Nenhuma vaga encontrada com os filtros selecionados.")
        st.stop()

    # ── 6 Cards de KPIs no Topo ──
    total_vagas = len(dff)
    sit_counts = dff["DS_SITVAGA"].value_counts() if "DS_SITVAGA" in dff.columns else pd.Series(dtype=int)

    qtd_ocupada = int(sit_counts.get("OCUPADA", 0))
    qtd_livre = int(sit_counts.get("LIVRE", 0))
    qtd_reservada = int(sit_counts.get("RESERVADA PARA CONCURSO", 0))
    n_orgaos = dff["SG_INSTITUICAO"].nunique() if "SG_INSTITUICAO" in dff.columns else 0
    n_cargos = dff["DS_CARGO"].nunique() if "DS_CARGO" in dff.columns else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🪑 Total de Vagas", fmt_int_br(total_vagas))
    c2.metric("✅ Ocupadas", fmt_int_br(qtd_ocupada))
    c3.metric("🟢 Livres", fmt_int_br(qtd_livre))
    c4.metric("📋 Reservadas Concurso", fmt_int_br(qtd_reservada))
    c5.metric("🏛️ Órgãos", f"{n_orgaos}")
    c6.metric("👔 Cargos", f"{n_cargos}")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 1: QUANTIDADE DE VAGAS POR SITUAÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("📊 Quantidade de vagas por situação")

    df_sit = sit_counts[sit_counts > 0].reset_index()
    df_sit.columns = ["SITUACAO", "QTDE"]
    df_sit = df_sit.sort_values("QTDE", ascending=False).reset_index(drop=True)

    linha_total_sit = pd.DataFrame([{"SITUACAO": "Total", "QTDE": total_vagas}])
    df_sit_plot = pd.concat([df_sit, linha_total_sit], ignore_index=True)
    df_sit_plot["PERC"] = (df_sit_plot["QTDE"] / total_vagas) * 100
    df_sit_plot["ROTULO"] = (
        df_sit_plot["QTDE"].apply(fmt_int_br)
        + "<br>"
        + df_sit_plot["PERC"].apply(lambda p: fmt_pct_br(p, 2))
    )

    cores_sit = ["#A0522D" if s == "Total" else "#D2691E" for s in df_sit_plot["SITUACAO"]]

    fig_sit_vagas = go.Figure(go.Bar(
        x=df_sit_plot["SITUACAO"],
        y=df_sit_plot["QTDE"],
        text=df_sit_plot["ROTULO"],
        textposition="outside",
        textfont=dict(size=10, color="#2d2d2d"),
        marker_color=cores_sit
    ))
    fig_sit_vagas.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(range=[0, df_sit_plot["QTDE"].max() * 1.22], gridcolor="#eeeeee", title="Quantidade de Vagas"),
        margin=dict(l=0, r=10, t=20, b=10),
        height=410
    )
    st.plotly_chart(fig_sit_vagas, use_container_width=True)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 2: QUANTIDADE DE VAGAS POR ÓRGÃO
    # ══════════════════════════════════════════════════════════════════════════
    ct_orgao = pd.crosstab(
        dff["SG_INSTITUICAO"].astype(str),
        dff["DS_SITVAGA"].astype(str)
    )
    ordem_cols = [c for c in df_sit["SITUACAO"].tolist() if c in ct_orgao.columns]
    ct_orgao = ct_orgao[ordem_cols].sort_index()
    ct_orgao["Total"] = ct_orgao.sum(axis=1)

    totais_col = ct_orgao.sum(axis=0).to_frame().T
    totais_col.index = ["TOTAL GERAL"]
    ct_orgao_full = pd.concat([totais_col, ct_orgao])
    ct_orgao_full.index.name = "Instituição"
    ct_orgao_reset = ct_orgao_full.reset_index()

    ct_orgao_fmt = ct_orgao_reset.copy()
    for col in ct_orgao_fmt.columns:
        if col != "Instituição":
            ct_orgao_fmt[col] = ct_orgao_fmt[col].apply(fmt_int_br)

    col_o1, col_o2 = st.columns([4.5, 1])
    with col_o1:
        st.subheader("🏛️ Quantidade de vagas por órgão")
    with col_o2:
        st.download_button(
            label="⬇️ Exportar Excel",
            data=to_excel_bytes(ct_orgao_reset, sheet_name="Vagas_Por_Orgao"),
            file_name="quantidade_vagas_por_orgao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_vagas_orgao"
        )

    st.dataframe(ct_orgao_fmt, use_container_width=True, hide_index=True, height=440)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 3: INFORMAÇÕES DOS CARGOS
    # ══════════════════════════════════════════════════════════════════════════
    mapa_colunas_detalhe = [
        ("SG_INSTITUICAO", "Sigla Instituição"),
        ("CD_ORCAMENTO", "Cód. Instituição"),
        ("DDNRVAGA", "DDNRVAGA"),
        ("DDSQVAGA", "SQ Vaga"),
        ("CD_CARGO", "Cód. Cargo"),
        ("DS_CARGO", "Descrição Cargo"),
        ("DDCDSITVAGA", "Cód. Situação"),
        ("DS_SITVAGA", "Situação Vaga"),
        ("TP_CARGO", "Tipo do Cargo"),
        ("DDCDRECRUTAMENTO", "Recrutamento"),
        ("DDNRMASPFUNC", "MASP Ocupante"),
        ("DDNRCONCURSO", "Nr. Concurso"),
        ("DDNRLEICRIACAO", "Lei Criação"),
        ("DT_INI_VAGA", "Data Início Vaga"),
        ("DT_FIM_VAGA", "Data Fim Vaga"),
        ("DS_CARGO_ATUALIZADO", "Cargo Atualizado"),
    ]

    cols_existentes = [c for c, _ in mapa_colunas_detalhe if c in dff.columns]
    renomear_dict = {c: nome for c, nome in mapa_colunas_detalhe if c in dff.columns}

    limite_visualizacao = 20000
    df_detalhe = dff[cols_existentes].head(limite_visualizacao).rename(columns=renomear_dict).copy()

    for col_cat in df_detalhe.select_dtypes(include=["category"]).columns:
        df_detalhe[col_cat] = df_detalhe[col_cat].astype(str)

    col_c1, col_c2 = st.columns([4.5, 1])
    with col_c1:
        st.subheader("📋 Informações dos cargos")
        if len(dff) > limite_visualizacao:
            st.caption(f"Exibindo os primeiros {fmt_int_br(limite_visualizacao)} registros de {fmt_int_br(len(dff))} filtrados. Use os filtros na lateral para refinar ou exporte para Excel.")
        else:
            st.caption(f"Exibindo {fmt_int_br(len(dff))} vagas filtradas.")
    with col_c2:
        df_export_cargos = dff[cols_existentes].rename(columns=renomear_dict).copy()
        for col_cat in df_export_cargos.select_dtypes(include=["category"]).columns:
            df_export_cargos[col_cat] = df_export_cargos[col_cat].astype(str)

        st.download_button(
            label="⬇️ Exportar Excel",
            data=to_excel_bytes(df_export_cargos, sheet_name="Informacoes_Cargos"),
            file_name="informacoes_cargos_vagas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_vagas_cargos"
        )

    st.dataframe(df_detalhe, use_container_width=True, hide_index=True, height=450)

# ── 7. EXECUÇÃO PRINCIPAL E MENU DE NAVEGAÇÃO ───────────────────────────────
def main():
    setup_page()

    PAGINAS = {
        "📊 Lotação de Pessoal": page_lotacao,
        "🎓 Contratos Temporários - Magistério": page_magisterio,
        "📉 Índice 35% - Contratos": page_indice_35_contratos,
        "🪑 Controle de Vagas": page_controle_vagas,
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
