# ======================== Gerenciamento de Sinais do Python para Execução Assíncrona =======================
# ====================  IMPORTANTÍSSIMO EM SISTEMAS LINUX ============================
import signal, threading

# Patch para evitar erro fora da main thread (Extremamente importante para ambientes Linux, onde o gerenciamento de sinais é mais restrito)
if threading.current_thread() is not threading.main_thread():
    def _fake_signal(sig, handler):
        # Ignora a tentativa de configurar sinais fora da thread principal
        return handler
    signal.signal = _fake_signal



# ======================== Funções Adicionais =======================
from functions_and_documents.Assistente_Fincaneiro.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown

# ======================= Bibliotecas Principais ===========================
from llama_index.llms.groq import Groq
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.tools import ToolMetadata, FunctionTool, QueryEngineTool
from llama_index.experimental import PandasQueryEngine
from llama_index.core.agent.workflow import FunctionAgent

# =================== Bibliotecas Adicionais ===========================
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import tempfile
import asyncio
import traceback
import time
import os
import difflib
from textwrap import dedent

from dotenv import load_dotenv
load_dotenv()


# ==================== Consulta em planilhas (Refinado) =========================
def query_spreadsheet(query: str):
    """
    Ferramenta para consultar o DataFrame.
    
    **Muito importante:**
    JAMAIS use comandos como pd.to_datetime, pd.query ou qualquer outro comando que utilize bibliotecas externas ou um erro do tipo 'pd is not defined'. 
    O pedido deve ser feito em linguagem natural, como se estivesse pedindo para um analista humano (ex:. {'query': 'Total de vendas da categoria Smartphone por mês'}).
    """
    # Checagem de importação indevida
    if "pd." in query or "pandas" in query.lower():
        return "Erro: Não utilize pandas diretamente. Reformule sua pergunta em linguagem natural."
    try:
        # Passamos a instrução explícita para o engine interno tentar retornar algo limpo
        pandas_query_engine = PandasQueryEngine(
            df=df, 
            llm=Settings.llm, 
            verbose=True, 
            use_async=False, 
            timeout=None
        )
        
        # Vital: Forçamos o PandasQueryEngine a formatar a saída de forma amigável
        enhanced_query = f"{query}. Retorne os dados puros de forma clara. Responda apenas com dados, SEM CÓDIGO, SEM PANDAS!"
        result = pandas_query_engine.query(enhanced_query)
        
        # Retornamos APENAS o resultado da consulta para não confundir o agente
        return f"Resultado da Consulta:\n{str(result)}"
    except Exception as e:
        # Só passamos o contexto se der erro, para o agente entender o que fez de errado
        df_columns = list(df.columns)
        return f"""Erro na consulta: {e}. Lembre-se, as colunas disponíveis são: {df_columns}. Tente fazer a pergunta de outra forma.
        **MUITO IMPORTANTE:** Não chame o pandas (ou pd) diretamente, caso contrário um erro 'pd is not defined' será retornado (Reforçando - NUNCA, JAMAIS CHAME pd.).        
        """
    

# ==================== Configuração de Múltiplos Modelos com Fallback Inteligente =========================
models = [
    "openai/gpt-oss-120b",    
    "openai/gpt-oss-20b", 
    "meta-llama/llama-prompt-guard-2-22m",   
    "gemma/gemma-2-9b-it"
]

@st.cache_resource(show_spinner=True)
def get_llm_with_fallback(temperature=0.15):
    for model in models:
        try:
            return Groq(model=model, temperature=temperature, api_key=os.getenv("GROQ_API_KEY"))
            st.toast(f"Usando modelo: {model}")
        except Exception as e:
            st.write(f"Erro com {model}: {e}")
            continue
    
    raise RuntimeError("Nenhum modelo disponível no momento.")

           


# ----------- Estilização com CSS ----------------------
with open("style.css") as file:
    st.html(f"<style>{file.read()}</style>")

st.set_page_config(page_title="Assistente Financeiro", layout="wide", page_icon="💵")

# -------------------- Sidebar (Estilização, Contato e seleção de Modelo)
with st.sidebar:
    st.image("https://th.bing.com/th/id/OIG3.8LLduKEW1Sddr_p7bGiJ?w=270&h=270&c=6&r=0&o=5&pid=ImgGn", width=225)    
    st.markdown("")
    uploaded_file = st.file_uploader("**💵 Carregue um documento\
                                     \npara iniciar a Análise Financeira**",
                                type=["pdf", "csv", "xlsx"], accept_multiple_files=False) # Botão de Upload fixo na Barra Lateral
    with st.expander("**🔧 Seleção da IA**"):
        model = st.selectbox("🔍 Selecione o Provedor do LLM", 
                             ["🧠 OpenAI (Raciocínio Avançado)", "⚡ Groq (Velocidade insuperável)"], index=0)

    with st.expander("**Contato e Assistência**", expanded=False, icon="✉️"):
        st.markdown(markdown, unsafe_allow_html=True)
    with st.expander("**💡 Nota de Qualidade**", expanded=False):
        st.markdown("""**🎯 Atenção:** *A qualidade dos insights gerados pelos LLMs é limitada pela qualidade dos seus dados.
                    Portanto, para maximizar a precisão e a coerência das respostas da IA, é crucial que os dados de entrada
                    sejam consistentes, confiáveis e sem contradições semânticas.*""")
        
# Cache das variáveis de sessão
if "docs_list" not in st.session_state:
    st.session_state["docs_list"] = None

if "agent" not in st.session_state:
    st.session_state["agent"] = None

if "summary" not in st.session_state:
    st.session_state["summary"] = None

if "df" not in st.session_state:
    st.session_state["df"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

       
if model == "⚡ Groq (Velocidade insuperável)":
    try:
        llm = get_llm_with_fallback(temperature=0.15)
    except Exception as e:
        st.error(str(e))

        # Fallback para OpenAI se o Groq estiver indisponível, garantindo que o app continue funcional mesmo em caso de falhas com o modelo principal
        llm = OpenAI(model="gpt-5-nano", temperature=0.15, api_key=os.getenv("OPENAI_API_KEY"))        
    
    llm = get_llm_with_fallback(temperature=0.15)
            
# Modelo Mistral como opção alternativa, caso o Groq esteja indisponível ou para comparação de resultados
elif model == "🧠 OpenAI (Raciocínio Avançado)":
    llm = OpenAI(model="gpt-5-mini", temperature=0.15, api_key=os.getenv("OPENAI_API_KEY"))

# Seta o LLM escolhido globalmente
Settings.llm = llm


if uploaded_file: # Primeira interação
    with st.spinner("Um Instante... O agente está analisando o documento 🚀"):
        if st.session_state["docs_list"] != uploaded_file: # Se um novo arquivo for carregado, é feito um novo processamento.
            st.session_state["chat_history"] = [] # Zera novamente o histórico de conversa
            # Identifica o tipo de arquivo e salva temporariamente
            suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".csv" if uploaded_file.type== "text/csv" else ".xlsx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                path = tmp_file.name
            
            if uploaded_file.name.endswith(".csv"): # Processa arquivo CSV                
                df = pd.read_csv(path, sep=None, engine="python").dropna()     # Descobre o delimitador dinamicamente utilizando python           
                st.session_state["df"] = df
                try:
                    st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce') # Primeira tentativa de converter a coluna de data                    
                
                # Segunda tentativa de Conversão (Mais robusta)
                except:
                    # Detectar e converter
                    for col in df.columns:
                        if is_date_column(df[col]):
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                    
                
                # Terceira e última tentativa de conversão
                else:
                    # Se as conversões falharem, usa 'difflib' para selecionar a coluna mais parecida com 'Date'
                    target = "Date"
                    columns = st.session_state.df.columns.tolist()
                    date_col = difflib.get_close_matches(target, columns, n=1, cutoff=0)[0]                    
                    st.session_state.df[date_col] = pd.to_datetime(st.session_state.df[date_col], errors='coerce', format="mixed")

                finally:
                    main_tool = FunctionTool.from_defaults(
                    fn=query_spreadsheet,
                    description=dedent("""FERRAMENTA PRINCIPAL PARA ACESSAR DADOS TABULARES (CSV/Excel).
                        Passe a sua pergunta em LINGUAGEM NATURAL CLARA.
                        Exemplos de uso correto: 'Qual o total de vendas por semana?' ou 'Liste as vendas agrupadas por mês'.
                        NÃO passe códigos Python, Pandas ou SQL para esta ferramenta. Apenas faça o pedido em texto puro."""))
                    
                    

            elif uploaded_file.name.endswith(".xlsx"): # Processa arquivo Excel
                df = pd.read_excel(path).dropna()
                st.session_state["df"] = df
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce') # Primeira tentativa de conversão
                except:
                    # Detectar e converter
                    for col in df.columns: # Segunda tentativa de Conversão (mais robusta)
                        if is_date_column(df[col]):
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                    
                main_tool = FunctionTool.from_defaults(
                    fn=query_spreadsheet,
                    description="FERRAMENTA PRINCIPAL. Use para acessar os dados do arquivo carregado (CSV/Excel). "
                                "Use para responder perguntas de texto E TAMBÉM para buscar dados numéricos antes de criar gráficos.",
                    )
                
            else: # Processa arquivo PDF
                st.session_state["df"] = None # Zera o Arquivo dataframe
                docs, index = load_and_index_documents(path)  # Carrega e indexa os documentos carregados
                main_tool = QueryEngineTool(query_engine=index.as_query_engine(
                    similarity_top_k=7, llm=llm, verbose=True),
                    metadata=ToolMetadata(
                        name="doc_search", description=dedent("""FERRAMENTA PRINCIPAL PARA ACESSAR DADOS EM PDF.
                Use para responder perguntas de texto ou buscar dados financeiros/numéricos brutos.
                Passe APENAS perguntas em linguagem natural clara (ex: 'Qual a receita no último trimestre?').
                NÃO utilize códigos Python, Pandas ou SQL nesta ferramenta.
                Se o usuário pedir algo genérico como 'Faça um relatório geral', use essa ferramenta com o termo 'query' para acessar os dados."""
                    )))
            
            # Configuração das Ferramentas do Agente                            
            json_save_tool = FunctionTool.from_defaults(fn=save_json, description=("Use APENAS quando precisar gerar um gráfico. "
                                                "Passo 1: Receba os dados da main_tool. "
                                                "Passo 2: Formate como lista de dicionários [{'col': val}, ...]. "
                                                "Passo 3: Salve com esta ferramenta."
                                                "Passo 4: Utilize sempre o mesmo nome de arquivo: finantial_data.json"))
            
            graph_tool = FunctionTool.from_defaults(fn=generate_graphs, description="Use APÓS salvar o JSON. Cria visualizações (barra, linha, etc). "
                            "Argumentos obrigatórios: json_path (retornado pelo save_json), col_x, col_y.")
            
            # --- SYSTEM PROMPT OTIMIZADO ---
            system_prompt = dedent("""
            Você é um Assistente Financeiro Especialista, focado em analisar dados, gerar relatórios executivos e criar gráficos impactantes.

            REGRAS CRÍTICAS DE EXECUÇÃO:
            1. EXPLORAÇÃO DE DADOS: O arquivo do usuário já está carregado. Use a ferramenta 'query_spreadsheet' (para planilhas) ou 'doc_search' (para PDFs) fazendo pedidos diretos em LINGUAGEM NATURAL (ex: "Traga a soma de receitas agrupada por semana"). Não escreva código para essas ferramentas.
            2. CRIAÇÃO DE GRÁFICOS (Fluxo Obrigatório):
            - Passo A: Peça os dados agrupados/filtrados necessários usando a ferramenta de busca de dados.
            - Passo B: Analise o 'Resultado da Consulta' retornado (se houver dados vazios, como meses sem vendas não inclua na geração dos gráficos).
            - Passo C: Formate esses dados recebidos rigorosamente como uma lista de dicionários (ex: [{"Mes": "2024-01", "Vendas": 1500}, ...]) e passe para a ferramenta 'save_json'. O nome do arquivo deve ser sempre "finantial_data.json".
            - Passo D: Chame a ferramenta 'generate_graphs' utilizando o arquivo salvo.
            3. PRECISÃO E VELOCIDADE:
            - Se o usuário pedir visualizações semanais, mensais ou anuais, garanta que seu pedido em texto para a ferramenta de dados deixe isso explícito.
            - Não invente, não presuma e não adicione dados zerados ou falsos.
            - Faça apenas UMA consulta aos dados se for suficiente para responder à pergunta.
            4. COMUNICAÇÃO:
            - Responda sempre em Português do Brasil.
            - Finalize sua resposta com uma breve conclusão executiva e recomendações baseadas exclusivamente nos dados encontrados, voltadas para a tomada de decisão.
            """)
            
            # Atribui as ferramentas ao Agente 
            agent = FunctionAgent(tools=[main_tool, json_save_tool, graph_tool], 
                                llm=Settings.llm, system_prompt=system_prompt)


            # Inicializa o Agente e os documentos
            if st.session_state["agent"] is None or st.session_state["docs_list"] != uploaded_file:
                st.session_state["agent"] = agent
                st.session_state["docs_list"] = uploaded_file                        
            
            if uploaded_file.name.endswith(".pdf"):
                st.toast("O carregamento inicial de documentos em PDF requer um maior tempo de processamento." \
                " Por favor, aguarde um instante enquanto o documento é processado.", icon="⏳", duration="long")
                content = "\n".join([doc.text for doc in docs])
                st.session_state["summary"] = summary_docs(content[:15000])
            elif uploaded_file.name.endswith(".xlsx"):
                if df.columns.size > 10: # Se tiver muitas colunas, gera o resumo somente com as 10 primeiras para evitar sobrecarga de tokens
                    st.session_state.df = df.iloc[:, :10] # Mantém apenas as 10 primeiras colunas para o resumo                                    
                st.session_state["summary"] = summary_docs(st.session_state.df.head(100)[:10000])
            elif uploaded_file.name.endswith("csv"):
                if df.columns.size > 10: # Se tiver muitas colunas, gera o resumo somente com as 10 primeiras para evitar sobrecarga de tokens
                    st.session_state.df = df.iloc[:, :10] # Mantém apenas as 10 primeiras colunas para o resumo
                st.session_state["summary"] = summary_docs(st.session_state.df.head(100)[:10000])
                
                           
            st.toast("Resumo gerado com sucesso!", icon="✅")             

    # ---------------- Aqui começa a Nova Lógica de UI -------------------------
        
    # Cria uma coluna centralizada para o histórico e uma para as respostas
    chat_col, output_col = st.columns([0.35, 0.65], gap="large")    
    if st.session_state["summary"]: # Mostra o resumo apenas uma vez
        with output_col:
            st.markdown("<h2 style='text-align: center; color: #B9B9B9;'>✅ Insights Iniciais sobre o Documento</h2>", unsafe_allow_html=True)
            st.markdown("<hr style='border: 1px solid; color: #008000'>", unsafe_allow_html=True)
            st.write(str(st.session_state["summary"]).replace("<br>", "\n"))
            del st.session_state["summary"]
    
        
    with chat_col:
        selected = option_menu(
            "Tipos de gráficos disponíveis",
            ["Bar", "Line", "Scatter", "Gauge", "Donut", "Treemap"],
            icons=["bar-chart", "graph-up", "scatter", "speedometer", "circle", "tree"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
                styles={
                    "container": {"padding": "0!important", "background-color": "#0a0a0a"},
                    "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0 5px"},
                    "nav-link-selected": {"background-color": "#008000"},
                }
        )

        # A barra de chat fica fixa em cima
        query = st.chat_input("Faça uma pergunta sobre seus dados financeiros\
                                \n(ex: Quais as maiores despesas)", key="chat_input_key")
        
    # Checkbox de tradução na sidebar para manter a interface principal mais limpa
    #with st.sidebar:
    translate_option = chat_col.checkbox("🌐 Ativar tradução (Inglês)", value=False, help="Para documentos em Inglês, ative a tradução.")

    # Execução do agente com base na consulta do usuário       
    if query:
        # Renderiza a pergunta do usuário com estilo de chat        
        with chat_col:
            st.session_state.chat_history.append({"role": "user", "content": query})            
            for message in st.session_state.chat_history:
                if message["role"]=="user":
                    with st.chat_message("user", avatar="human"):
                        st.markdown(message["content"])
            if len(st.session_state.chat_history) >=3:
                del st.session_state.chat_history
        
        static_graph_path = "static_graph.json"
        if os.path.exists(static_graph_path): 
            os.remove(static_graph_path)
        
        # Renderiza a resposta do assistente
        with output_col:
            st.header("🎯 Resposta do Assistente Financeiro")
            st.markdown("<hr style='border: 1px solid; color: #008000'>", unsafe_allow_html=True)
            with st.chat_message("assistant", avatar="ai"):
                with st.status("🔍 Analisando dados e processando requisição...", expanded=True) as status:
                    query_engine = translate_content(query, source_lang="pt", target_lang="en") if translate_option else query                
                    
                    try:
                        time_before = time.time()
                        status.update(label="⏳ Lembre-se. Pergutas mais complexas podem demandar mais tempo de processamento.", state="running", expanded=True)
                        response_text, agent_logs = run_query_safe(query_engine)                        
                        final_response = translate_content(response_text, source_lang="en", target_lang="pt") if translate_option else response_text
                        time_after = time.time()
                        st.toast(f"O Agente pensou por: {round(time_after - time_before, 2)} segundos!", icon="⏱️", duration="long")
                        status.update(label="✅ Análise concluída!", state="complete", expanded=False)
                        
                    except Exception as e:
                        status.update(label="❌ Erro no processamento", state="error")
                        st.error(f"Detalhe do erro: {e}")
                        final_response = "Não foi possível completar a solicitação."
                        agent_logs = traceback.format_exc()

                # Lógica de renderização Profissional com ABAS (Tabs)
                final_response = str(final_response).replace("assistant", "## **Assistente**\n").replace("<br>", "\n")
                if os.path.exists(static_graph_path):
                    tab1, tab2, tab3 = st.tabs(["📊 Gráfico Gerado", "💬 Análise Detalhada", "🛠️ Logs Técnicos"], default="💬 Análise Detalhada")
                    
                    with tab1:
                        fig = pio.read_json(static_graph_path)
                        # Renderização do Gráfico aqui:
                        st.plotly_chart(fig, width="stretch") 
                    
                    with tab2:
                        # Resposta Final do Modelo
                        st.write(final_response.replace("$", "R\\$"))
                        
                    with tab3:
                        # Logs do Agente
                        with st.expander("🛠️ Ver logs técnicos (Como o Agente chegou na resposta)", expanded=False):
                            st.code(agent_logs, language="text")
                        
                # Se nenhum gráfico for gerado, exibe tudo em duas Aba
                else:
                    tab1, tab2 = st.tabs(["💬 Análise Detalhada", "🛠️ Logs Técnicos"]) 
                    with tab1:
                        st.markdown(final_response)
                    with tab2:
                        with st.expander("🛠️ Ver logs técnicos (Como o Agente Chegou na resposta)", expanded=False):
                            st.code(agent_logs, language="text")

# Adicionando o Estado Vazio (Empty State) fora do if uploaded_file
else:
    # O que aparece quando o usuário entra no app sem subir arquivo
    st.markdown("<h1 style='text-align: center; color: #C9C9C9;'>Bem-vindo ao seu Assistente Financeiro 💵</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #C9C9C9;'>Utilize o menu lateral para carregar sua planilha (CSV/XLSX) ou relatório (PDF) e começar a análise.</p>", unsafe_allow_html=True)    

    