# ======================== Funções Adicionais =======================
from functions_and_documents.Assistente_Fincaneiro.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown

# ======================= Bibliotecas Principais ===========================
from llama_index.llms.groq import Groq
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings
from llama_index.core.tools import ToolMetadata
from llama_index.core.tools import QueryEngineTool
from llama_index.experimental import PandasQueryEngine
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool

# =================== Bibliotecas Adicionais ===========================
import streamlit as st
import pandas as pd
import tempfile
import asyncio
import traceback
import os
import difflib

from dotenv import load_dotenv
load_dotenv()


# ==================== Consulta em planilhas (Refinado) =========================
def query_spreadsheet(query: str):
    """
    Ferramenta Principal. Use para consultar o DataFrame carregado.
    Se precisar extrair dados para gráficos, peça explicitamente os dados brutos 
    nesta query para depois passar para o save_json.
    Não utilize SQL. Utilize somente comandos do Pandas para executar a consulta no DataFrame.
    """    
          
    try:
        # Configuração verbose=True para depuração
        pandas_query_engine = PandasQueryEngine(df=df, llm=Settings.llm, verbose=True)
        
        result = pandas_query_engine.query(query)
        return str(result)
    except Exception as e:
        return f"Erro ao executar query no Pandas: {e}" 
           


# ----------- Estilização com CSS ----------------------
with open("style.css") as file:
    st.html(f"<style>{file.read()}</style>")

st.set_page_config(page_title="Assistente Financeiro", layout="wide", page_icon="💵")

# -------------------- Sidebar (Estilização, Contato e seleção de Modelo)
with st.sidebar:
    st.image("https://www.bing.com/th/id/OIG3.1XJ31rftz4RgJmLBOJOq?w=540&h=540&c=6&r=0&o=5&cb=defcachec2&pid=ImgGn", width=225)    
    st.markdown("")
    uploaded_file = st.file_uploader("**💵 Carregue um documento\
                                     \npara iniciar a Análise Financeira**",
                                type=["pdf", "csv", "xlsx"], accept_multiple_files=False) # Botão de Upload fixo na Barra Lateral
    with st.expander("**🔧 Seleção da IA**"):
        model = st.selectbox("🔍 Selecione o Provedor do LLM", ["Groq", "Gemini"])            

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

       
# Fallback para Modelo alternativo caso Haja muita requisições à API do Modelo
if model == "Groq":
    try:
        llm = Groq(model="moonshotai/kimi-k2-instruct", temperature=0.15)        
    
    except Exception as rate_limit:
        if "limit" or "429" in str(rate_limit).lower():
            llm = Groq(model="openai/gpt-oss-120b", temperature=0.15)        
            
            

elif model == "Gemini":    
    llm = GoogleGenAI(model="models/gemini-2.5-flash", 
                      temperature=0.15, api_key=os.getenv("GOOGLE_NEW_API_KEY"))

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
                df = pd.read_csv(path, sep=None, engine="python")     # Descobre o delimitador dinamicamente utilizando python           
                st.session_state["df"] = df
                try:
                    st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce') # Tenta converter a coluna de data                    
                
                
                except: # Se a conversão falhar, usa 'difflib' para selecionar a coluna mais parecida com 'date'
                    target = "Date"
                    columns = st.session_state.df.columns.tolist()
                    date_col = difflib.get_close_matches(target, columns, n=1, cutoff=0)[0]                    
                    st.session_state.df[date_col] = pd.to_datetime(st.session_state.df[date_col], errors='coerce', format="mixed")
                
                else:
                    date = st.sidebar.selectbox("Selecione a coluna de data", options=st.session_state.df.columns.tolist())
                    st.session_state.df[date] = pd.to_datetime(st.session_state.df[date], errors='coerce', format="mixed")

                finally:
                    main_tool = FunctionTool.from_defaults(
                    fn=query_spreadsheet,
                    description="FERRAMENTA PRINCIPAL. Use para acessar os dados do arquivo carregado (CSV/Excel). "
                                "Use para responder perguntas de texto E TAMBÉM para buscar dados numéricos antes de criar gráficos." \
                                "Use preferencialmente comandos do pandas ou queries com aspas duplas. " \
                                "Do contrário um erro do tipo Failed to parse tool call arguments as JSON pode ser disparado")
                    
                    

            elif uploaded_file.name.endswith(".xlsx"): # Processa arquivo Excel
                df = pd.read_excel(path)
                st.session_state.df = df
                st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce')
                main_tool = FunctionTool.from_defaults(
                    fn=query_spreadsheet,
                    description="FERRAMENTA PRINCIPAL. Use para acessar os dados do arquivo carregado (CSV/Excel). "
                                "Use para responder perguntas de texto E TAMBÉM para buscar dados numéricos antes de criar gráficos."
                    )
                
            else: # Processa arquivo PDF
                st.session_state["df"] = None # Zera o Arquivo dataframe
                docs, index = load_and_index_documents(path)  # Carrega e indexa os documentos carregados
                main_tool = QueryEngineTool(query_engine=index.as_query_engine(
                    similarity_top_k=5, llm=llm, verbose=True),
                    metadata=ToolMetadata(
                        name="doc_search", description="FERRAMENTA PRINCIPAL. Use para acessar os dados do arquivo carregado (PDF). "
                                    "Use para responder perguntas de texto E TAMBÉM para buscar dados numéricos antes de criar gráficos." \
                                    "Para essa ferramenta com busca semântica você deve passar os dados brutos da pesquisa do usuário, sem utilizar códigos SQL ou Pandas."
                    ))
            
            # Configuração das Ferramentas do Agente                            
            json_save_tool = FunctionTool.from_defaults(fn=save_json, description=("Use APENAS quando precisar gerar um gráfico. "
                                                "Passo 1: Receba os dados da main_tool. "
                                                "Passo 2: Formate como lista de dicionários [{'col': val}, ...]. "
                                                "Passo 3: Salve com esta ferramenta."
                                                "Passo 4: Utilize sempre o mesmo nome de arquivo: finantial_data.json"))
            
            graph_tool = FunctionTool.from_defaults(fn=generate_graphs, description="Use APÓS salvar o JSON. Cria visualizações (barra, linha, etc). "
                            "Argumentos obrigatórios: json_path (retornado pelo save_json), col_x, col_y.")
            
            # --- SYSTEM PROMPT (INDISPENSÁVEL PARA AGENTES INTELIGENTES) ---
            system_prompt = """
            Você é um Assistente Financeiro Especialista capaz de analisar dados e gerar gráficos.
            
            REGRAS CRITICAS:
            1. O usuário JÁ CARREGOU um arquivo de dados. Ele está disponível através da ferramenta 'query_spreadsheet' ou 'doc_search' (PARA PDFs).
            2. NÃO pergunte ao usuário pelo arquivo. Use a ferramenta de acordo com a descrição para ver o que tem dentro.
            3. Se o usuário pedir um gráfico:
            a. Primeiro, use 'query_spreadsheet' para extrair os dados necessários.
            b. Segundo, formate esses dados internamente e use 'save_json'.
            c. Terceiro, use 'generate_graphs' com o caminho do arquivo salvo.
            d. As cores, títulos e outras personalizações ficam a seu critério. Estilize de forma a manter o gráfico informativo e impactante. Use nomes descritivos e impactantes para o título e os eixos.
            4. Responda sempre em Português do Brasil.
            5. Se fizer sentido no contexto, retorne em sua resposta final uma conclusão com análises e recomendações relevantes para o negócio, sem menções a detalhes técnicos ou a campos específicos do conjunto de dados.
            """
            
            # Atribui as ferramentas ao Agente 
            agent = FunctionAgent(tools=[main_tool, json_save_tool, graph_tool], 
                                llm=Settings.llm, system_prompt=system_prompt)


            # Inicializa o Agente e os documentos
            if st.session_state["agent"] is None or st.session_state["docs_list"] != uploaded_file:
                st.session_state["agent"] = agent
                st.session_state["docs_list"] = uploaded_file                        

            if uploaded_file.name.endswith(".pdf"):
                content = "\n".join([doc.text for doc in docs])
                st.session_state["summary"] = summary_docs(content[:15000])
            elif uploaded_file.name.endswith(".xlsx"):                
                st.session_state["summary"] = summary_docs(st.session_state.df.head(500))
            else:                
                st.session_state["summary"] = summary_docs(st.session_state.df.head(500))
                    
                           
            st.toast("Resumo gerado com sucesso!", icon="✅")             

    # ---------------- Aqui começa a Nova Lógica de UI -------------------------
        
    # Cria uma coluna centralizada para o histórico e uma para as respostas
    chat_col, output_col = st.columns([0.35, 0.65], gap="large")    
    if st.session_state["summary"]: # Mostra o resumo apenas uma vez
        with output_col:
            st.markdown("<h2 style='text-align: center; color: #B9B9B9;'>🟢 Insights Iniciais sobre o Documento</h2>", unsafe_allow_html=True)
            st.write(str(st.session_state["summary"]).replace("R$", "R\$").replace("<br>", "\n"))
            del st.session_state["summary"]
    
    
    # A barra de chat fica fixa embaixo
    with chat_col:
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
            with st.chat_message("assistant", avatar="ai"):
                with st.status("🔍 Analisando dados e processando requisição...", expanded=True) as status:
                    query_engine = translate_content(query, source_lang="pt", target_lang="en") if translate_option else query                
                    
                    try:
                        response_text, agent_logs = asyncio.run(run_agent(query_engine))
                        final_response = translate_content(response_text, source_lang="en", target_lang="pt") if translate_option else response_text
                        status.update(label="✅ Análise concluída!", state="complete", expanded=False)
                        
                    except Exception as e:
                        status.update(label="❌ Erro no processamento", state="error")
                        st.error(f"Detalhe do erro: {e}")
                        final_response = "Não foi possível completar a solicitação."
                        agent_logs = traceback.format_exc()

                # Lógica de renderização Profissional com ABAS (Tabs)
                final_response = str(final_response).replace("assistant", "**Assistente**").replace("<br>", "\n").replace("R$", "R\$")
                if os.path.exists(static_graph_path):
                    tab1, tab2, tab3 = st.tabs(["📊 Gráfico Gerado", "💬 Análise Detalhada", "🛠️ Logs Técnicos"])
                    
                    with tab1:
                        fig = pio.read_json(static_graph_path)
                        # Renderização do Gráfico aqui:
                        st.plotly_chart(fig, use_container_width=True) 
                    
                    with tab2:
                        # Resposta Final do Modelo
                        st.write(final_response)
                        
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

    