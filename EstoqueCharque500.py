import streamlit as st
import pandas as pd
import plotly.express as px
from database import PALETA_CORES
from database import buscar_vendas_reais, buscar_estoque_real

# -------------------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO NO PADRÃO BRASILEIRO (PT-BR)
# -------------------------------------------------------------
def formatar_br(valor, sufixo="", prefixo=""):
    """
    Formata um número float para o padrão brasileiro: 183.180.959,97
    """
    if valor is None or pd.isna(valor):
        return f"{prefixo}0,00{sufixo}"
    
    # Formata em padrão americano primeiro (com vírgula nos milhares)
    texto = f"{valor:,.2f}"
    # Inverte ponto por vírgula e vírgula por ponto
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"{prefixo}{texto}{sufixo}"

# Configuração da Página
st.set_page_config(
    page_title="Dashboard de Vendas & Estoque - Rede Market",
    page_icon="🥩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Leve
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# FUNÇÃO DE AUTENTICAÇÃO (SISTEMA DE LOGIN SEGURO)
# -------------------------------------------------------------
def check_password():
    """Retorna True se o usuário digitou a senha correta configurada nos Secrets."""
    def password_entered():
        # Compara a senha digitada com a chave PASSWORD nos Secrets do Streamlit
        if st.session_state["password"] == st.secrets.get("PASSWORD", ""):
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Não mantém a senha na memória
        else:
            st.session_state["authenticated"] = False

    # Se já estiver autenticado na sessão, libera o acesso
    if st.session_state.get("authenticated", False):
        return True

    # Tela de Login
    st.title("🔒 Acesso Restrito - Rede Market")
    st.text_input("Digite a senha do sistema:", type="password", on_change=password_entered, key="password")
    
    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("😕 Senha incorreta. Tente novamente.")
        
    return False

# -------------------------------------------------------------
# EXECUÇÃO DO APLICATIVO
# -------------------------------------------------------------
if check_password():
    
    # -------------------------------------------------------------
    # CARREGAMENTO DE DADOS COM CACHE (API / FIREBIRD)
    # -------------------------------------------------------------
    @st.cache_data(ttl=300) # Atualiza a cada 5 min ou quando clica no botão
    def load_sales():
        return buscar_vendas_reais(data_inicio='2026-01-01')

    @st.cache_data(ttl=300)
    def load_inventory():
        return buscar_estoque_real()

    # Carregamento dos dados reais
    try:
        df_sales = load_sales()
        df_inv = load_inventory()
    except Exception as e:
        st.error(f"Erro ao conectar com a API do Banco de Dados: {e}")
        st.stop()

    # -------------------------------------------------------------
    # MENU LATERAL & NAVEGAÇÃO
    # -------------------------------------------------------------
    st.sidebar.title("Navegação & Operações")
    
    # 🔄 Botão de Atualizar Dados em Tempo Real
    if st.sidebar.button("🔄 Atualizar Dados do Banco", use_container_width=True):
        st.cache_data.clear()  # Limpa o cache para forçar a nova consulta à API
        st.sidebar.success("Dados atualizados com sucesso!")
        st.rerun()

    st.sidebar.divider()

    page = st.sidebar.radio("Selecione a Visão:", [
        "📦 Estoque Lojas vs. Indústria (IN)"
    ])

    st.sidebar.divider()

   

    # -------------------------------------------------------------
    # PÁGINA 2: ESTOQUE LOJAS VS INDÚSTRIA
    # -------------------------------------------------------------
    if page == "📦 Estoque Lojas vs. Indústria (IN)":
        st.title("📦 Consulta e Comparativo de Estoque")
        st.caption("Visão geral dos saldos físicos na Indústria (IN) e nas Filiais")

        if df_inv.empty:
            st.warning("Sem dados de estoque disponíveis no momento.")
        else:
            # 1. BARRA DE FILTRO E PESQUISA
            col_busca, col_filtro = st.columns([2, 1])
            
            with col_busca:
                termo_busca = st.text_input("🔍 Buscar Produto por Nome ou Código:", "")
            
            # Aplica o filtro de busca se houver digitação
            df_exibicao = df_inv.copy()
            if termo_busca:
                termo = termo_busca.lower()
                df_exibicao = df_exibicao[
                    df_exibicao["PRODUTO"].astype(str).str.lower().str.contains(termo) |
                    df_exibicao["IDPRODUTO"].astype(str).str.contains(termo)
                ]

            # 2. DEFINIÇÃO DAS COLUNAS LIMPAS (Sem Mínimo Recomendado)
            colunas_estoque = [
                "IDPRODUTO", 
                "PRODUTO", 
                "Indústria (IN)", 
           ]
            
            # Filtra apenas colunas que existem no DataFrame
            cols_finais = [c for c in colunas_estoque if c in df_exibicao.columns]

            # 3. EXIBIÇÃO DA TABELA
            st.dataframe(
                df_exibicao[cols_finais],
                use_container_width=True,
                hide_index=True
            )

            # 4. CARD DETALHADO CASO ENCONTRE UM ÚNICO PRODUTO OU SEJA SELECIONADO
            st.markdown("---")
            st.subheader("🔍 Detalhamento por Item")
            
            lista_produtos = df_inv["PRODUTO"].unique().tolist()
            produto_sel = st.selectbox("Selecione um Produto para ver os detalhes completos:", ["Todos"] + lista_produtos)

            if produto_sel != "Todos":
                item_dados = df_inv[df_inv["PRODUTO"] == produto_sel].iloc[0]
                
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("🏭 Indústria (IN)", formatar_br(item_dados.get('Indústria (IN)', 0), sufixo=" kg"))
               

   

           

           

    # -------------------------------------------------------------
    # BOTÃO DE LOGOUT
    # -------------------------------------------------------------
    if st.sidebar.button("🔒 Sair / Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
