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
        
        /* ── CARDS DE KPI RESPONSIVOS ── */
        [data-testid="stMetric"] { 
            background: white; 
            border-radius: 8px; 
            padding: 10px 12px !important; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            border: 1px solid #e8e8e8;
            border-left: 4px solid #D2691E;
            min-width: 0 !important;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] *,
        div[data-testid="stMetricLabel"] p { 
            font-size: 0.70rem !important; 
            color: #666 !important;
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
            font-size: clamp(0.88rem, 1.05vw, 1.35rem) !important;
            white-space: nowrap !important;
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

        /* Caixa de Objetivo Legal (Magistério) */
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
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* ── SIDEBAR LARANJA E MENU DE NAVEGAÇÃO ── */
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

        div[data-baseweb="select"] input::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
        }

        /* Estilo dos botões do Menu de Navegação */
        div[data-testid="stSidebar"] [data-testid="stRadio"] > div {
            gap: 0.4rem;
        }
        div[data-testid="stSidebar"] [data-testid="stRadio"] label {
            background-color: rgba(255, 255, 255, 0.14);
            padding: 0.55rem 0.8rem;
            border-radius: 6px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: background-color 0.2s ease;
            cursor: pointer;
        }
        div[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background-color: rgba(255, 255, 255, 0.26);
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
    try:
        df = load_data_lotacao("BASE_LOTACAO.xlsx")
    except FileNotFoundError:
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
    c1.metric("👤 Servidores", f"{total_servidores:,.0f}")
    c2.metric("🏛️ Órgãos", f"{n_orgaos}")
    c3.metric("📋 Carreiras", f"{n_carreiras}")
    c4.metric("⏱️ CH Total (h)", f"{total_ch:,.0f}")
    c5.metric("⏱️ CH Média (h)", f"{media_ch:,.1f}")

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

    # Tratamento da coluna de período DT_ANO_MES_REF (ex.: "2025/01" ou 202501)
    ref_str = df["DT_ANO_MES_REF"].astype(str).str.strip()
    if ref_str.str.contains("/").any():
        partes = ref_str.str.split("/", expand=True)
        df["ANO"] = partes[0].astype(int)
        df["MES"] = partes[1].astype(int)
    else:
        df["ANO"] = (pd.to_numeric(ref_str) // 100).astype(int)
        df["MES"] = (pd.to_numeric(ref_str) % 100).astype(int)

    df["PERIODO"] = df["ANO"].astype(str) + "/" + df["MES"].astype(str).str.zfill(2)
    df["MES_NOME"] = df["MES"].map(MESES_PT)

    # Limpeza das colunas numéricas
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

    # Busca automática pelo arquivo na pasta
    arquivo_encontrado = None
    for nome_arquivo in ["BASE_PAINEL.xlsx", "BASE PAINEL.xlsx"]:
        if os.path.exists(nome_arquivo):
            arquivo_encontrado = nome_arquivo
            break

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

    # ── Filtros na Sidebar (idênticos ao painel de referência) ──
    st.sidebar.markdown("### 🔍 Filtros — Magistério", unsafe_allow_html=True)

    anos_disp = sorted(df_mag["ANO"].unique())
    ano_sel = st.sidebar.selectbox(
        "Ano de Referência (Quadro Atual)",
        options=anos_disp,
        index=len(anos_disp) - 1  # Padrão: ano mais recente
    )

    meses_do_ano = sorted(df_mag[df_mag["ANO"] == ano_sel]["MES"].unique())
    mes_sel = st.sidebar.selectbox(
        "Mês de Referência (Quadro Atual)",
        options=meses_do_ano,
        index=len(meses_do_ano) - 1,  # Padrão: mês mais recente do ano
        format_func=lambda m: f"{str(m).zfill(2)} - {MESES_PT.get(m, str(m))}"
    )

    carreiras_disp = sorted(df_mag["DS_SIGLA_CARREIRA"].dropna().unique())
    carreiras_sel = st.sidebar.multiselect(
        "Sigla da Carreira",
        options=carreiras_disp,
        default=[],
        placeholder="Selecione a carreira..."
    )

    orgaos_disp = sorted(df_mag["INSTITUICAO"].dropna().unique())
    orgaos_sel = st.sidebar.multiselect(
        "Órgão / Instituição",
        options=orgaos_disp,
        default=[],
        placeholder="Selecione o órgão..."
    )

    # Filtro para Série Histórica (todas as datas, filtrado por órgão e carreira)
    mask_hist = pd.Series([True] * len(df_mag), index=df_mag.index)
    if carreiras_sel:
        mask_hist &= df_mag["DS_SIGLA_CARREIRA"].isin(carreiras_sel)
    if orgaos_sel:
        mask_hist &= df_mag["INSTITUICAO"].isin(orgaos_sel)
    df_hist = df_mag[mask_hist].copy()

    # Filtro para o Quadro Atual (período específico selecionado)
    df_atual = df_hist[(df_hist["ANO"] == ano_sel) & (df_hist["MES"] == mes_sel)].copy()

    if df_atual.empty:
        st.warning("Nenhum dado encontrado para os filtros aplicados.")
        st.stop()

    # ── Cálculo dos 6 KPIs Principais ──
    mes_ref_texto = f"{MESES_PT.get(mes_sel, '').upper()} DE {ano_sel}"
    total_lei = df_atual["QUANT_LEI"].sum()
    total_ct = df_atual["COUNT_of_NR_MASP_ADM"].sum()
    perc_ct = (total_ct / total_lei * 100) if total_lei > 0 else 0.0

    # Regra legal escalonada: 50% (até 2025), 40% (2026), 30% (2027 em diante)
    if ano_sel <= 2025:
        taxa_limite = 0.50
    elif ano_sel == 2026:
        taxa_limite = 0.40
    else:
        taxa_limite = 0.30

    limite_qtd = total_lei * taxa_limite
    margem = limite_qtd - total_ct  # Positivo = folga; Negativo = acima do limite

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📅 Mês de Referência", mes_ref_texto)
    c2.metric("🏛️ Quant. em Lei (EF)", fmt_int_br(total_lei))
    c3.metric("📝 Contrato Temp. (CT)", fmt_int_br(total_ct))
    c4.metric("📊 % Contratos Temp.", fmt_pct_br(perc_ct, 2))
    c5.metric(f"⚖️ Limite de {int(taxa_limite*100)}%", fmt_int_br(limite_qtd))
    c6.metric("📉 Margem", fmt_int_br(margem))

    # ── Texto Legal Explicativo ──
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

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 1: QUADRO ATUAL (QUANTIDADE DE SERVIDORES POR ÓRGÃO NO MÊS)
    # ══════════════════════════════════════════════════════════════════════════
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

    # Linha de Total Geral no final do Quadro Atual
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

    # Tabela formatada para exibição e exportação
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

    # Gráfico visual do Quadro Atual por Órgão/Carreira
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

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 2: SÉRIE HISTÓRICA (EVOLUÇÃO E TABELA PIVOTADA POR MÊS)
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("📈 Série Histórica — Histórico da Quantidade de servidores por órgão")

    # Gráfico de evolução temporal
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

    # Tabela Histórica Pivotada (Órgão x Carreira nas linhas, Períodos nas colunas)
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

# ── 7. EXECUÇÃO PRINCIPAL E MENU DE NAVEGAÇÃO ───────────────────────────────
def main():
    setup_page()

    st.sidebar.markdown("### 🧭 Navegação", unsafe_allow_html=True)
    pagina_selecionada = st.sidebar.radio(
        "Selecione o painel:",
        options=[
            "📊 Lotação de Pessoal",
            "🎓 Contratos Temporários - Magistério",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.divider()

    if pagina_selecionada == "📊 Lotação de Pessoal":
        page_lotacao()
    elif pagina_selecionada == "🎓 Contratos Temporários - Magistério":
        page_magisterio()

    st.sidebar.divider()
    st.sidebar.caption("Dashboard RH – DCGFT MG\nFeito com Streamlit 🚀")

if __name__ == "__main__":
    main()