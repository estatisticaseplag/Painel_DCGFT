import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import warnings

warnings.filterwarnings("ignore")

# ── 1. CONFIGURAÇÃO DA PÁGINA E CSS (COM TRADUÇÃO VIA JS NATIVO) ────────────
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
        
        /* ── CARDS DE KPI (AJUSTE DE TEXTO E ESPAÇAMENTO) ── */
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
            font-size: 0.72rem !important; 
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
            font-size: clamp(0.95rem, 1.15vw, 1.4rem) !important;
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

    # Injeção real de JavaScript via componente isolado para traduzir "Select all"
    components.html("""
    <script>
        const translateSelectAll = () => {
            const parentDoc = window.parent.document;
            const elements = parentDoc.querySelectorAll('div[data-baseweb="popover"] *');
            elements.forEach(el => {
                if (el.children.length === 0 && el.textContent.trim() === 'Select all') {
                    el.textContent = 'Selecionar todos';
                }
            });
        };
        
        const observer = new MutationObserver(translateSelectAll);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        translateSelectAll();
    </script>
    """, height=0, width=0)

# ── 2. CARREGAMENTO DE DADOS (BASE DE LOTAÇÃO) ──────────────────────────────
@st.cache_data(show_spinner="Carregando base de lotação…")
def load_data(path="BASE_LOTACAO.xlsx"):
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

# ── 3. FILTROS DA SIDEBAR ───────────────────────────────────────────────────
def render_sidebar_filters(df):
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
        "Situação do Servidor", sit_serv_disp,
