from functions_and_documents.Assistente_Fincaneiro.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown
from llama_index.llms.groq import Groq
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings
from llama_index.core.tools import ToolMetadata
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
import streamlit as st
import pandas as pd
import tempfile
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()




st.set_page_config(page_title="Assistente Financeiro", layout="wide", page_icon="💵")


st.sidebar.header("Configurações do Modelo")
uploaded_file = st.sidebar.file_uploader("Carregue o documento para análise financeira (PDF, CSV, Excel)",
                                 type=["pdf", "csv", "xlsx"])    
model = st.sidebar.selectbox("Selecione o Modelo", ["Groq", "Gemini"])


# Cache das variáveis de sessão
if "docs_list" not in st.session_state:
    st.session_state["docs_list"] = None

if "agent" not in st.session_state:
    st.session_state["agent"] = None

if "summary" not in st.session_state:
    st.session_state["summary"] = None

if "df" not in st.session_state:
    st.session_state["df"] = None

if model == "Groq":
    llm = Groq(model="openai/gpt-oss-20b", temperature=0.15)

elif model == "Gemini":    
    llm = GoogleGenAI(model="models/gemini-2.5-flash", 
                      temperature=0.15)

# Seta o LLM escolhido globalmente
Settings.llm = llm


# Interface do Streamlit
if uploaded_file:    
    if st.session_state["docs_list"] != uploaded_file:
        # Identifica o tipo de arquivo e salva temporariamente
        suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".csv" if uploaded_file.type== "text/csv" else ".xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            path = tmp_file.name
        
        if uploaded_file.name.endswith(".csv"): # Processa arquivo CSV
            df = pd.read_csv(path)
            st.session_state.df = df
            try:
                st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce')                
                main_tool = FunctionTool.from_defaults(
                fn=query_spreadsheet,
                description="Utilize essa ferramenta para filtrar dados em um dataframe com o PandasQueryEngine."
                
            )
            
            except:
                date = st.sidebar.selectbox("Selecione a coluna de data", options=st.session_state.df.columns.tolist())
                st.session_state.df[date] = pd.to_datetime(st.session_state.df[date], errors='coerce')
                

        elif uploaded_file.name.endswith(".xlsx"): # Processa arquivo Excel
            df = pd.read_excel(path)
            st.session_state["df"] = df
            st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce')            
            main_tool = FunctionTool.from_defaults(
                fn=query_spreadsheet,
                description="Utilize essa ferramenta para filtrar dados em um dataframe com o PandasQueryEngine."
                )
            
        else: # Processa arquivo PDF
            st.session_state["df"] = None
            docs, index = load_and_index_documents(path) 
            main_tool = QueryEngineTool(query_engine=index.as_query_engine(
                similarity_top_k=4, llm=llm, verbose=True),
                metadata=ToolMetadata(
                    name="doc_search", description="Provides information about the company's finance. Use whenever the user asks for something. This is the first tool to use." 
                ))
        
        # Configuração do FunctionAgent
        graph_tool = FunctionTool.from_defaults(fn=generate_graphs, description="Útil para criar visualizações. Informe os nomes exatos das colunas para X e Y e o caminho do dataframe salvo no passo anterior.")
        df_save_tool = FunctionTool.from_defaults(fn=save_df, description="Salva os dados financeiros em um dataframe do pandas. Essa é a segunda função a ser usada e deve ser chamada sempre que for necessário gerar um gráfico no passo seguinte")
        agent = FunctionAgent(tools=[main_tool, df_save_tool, graph_tool], llm=Settings.llm)

        if st.session_state["agent"] is None or st.session_state["docs_list"] != uploaded_file:
            st.session_state["agent"] = agent
            st.session_state["docs_list"] = uploaded_file                        

        if uploaded_file.name.endswith(".pdf"):
            content = "\n".join([doc.text for doc in docs])
            st.session_state["summary"] = summary_docs(content[:50000])
        elif uploaded_file.name.endswith(".xlsx"):
            content = st.session_state["df"].to_csv(index=False)
            st.session_state["summary"] = summary_docs(content)
        else:
            content = st.session_state["df"].to_csv(index=False)            
            st.session_state["summary"] = summary_docs(content)            
                
        col1, col2 = st.columns([0.6,0.4], gap="large")
        with col1:
            st.header(" Insights Iniciais sobre o Documento:", divider="blue")
            with st.expander("Insights iniciais sobre o documento: ", expanded=True):
                st.markdown(st.session_state["summary"])
        with col2:
            st.header("Visualização dos Dados", divider="blue")
            st.markdown(st.session_state["df"].head())
            
        
        st.toast("Resumo gerado com sucesso!", icon="✅")


    # Após carregamento do documento, permite ao usuário fazer perguntas
    
    query = st.sidebar.text_area("Digite sua pergunta sobre o documento:", key="query_input",
                                  placeholder="Ex: Quais foram as principais despesas no último trimestre?", height=150)
    translate_option = st.sidebar.checkbox("Traduzir o texto", value=False, help="Útil para documentos em inglês")
    send = st.sidebar.button("Enviar Pergunta", type="primary", 
                             use_container_width=True, help="Faça sua pergunta ao Assistente Financeiro")
    
    st.sidebar.markdown(markdown, unsafe_allow_html=True)
        
    # Execução do agente com base na consulta do usuário
    if send and query:
        st.session_state["last_fig"] = None
        col1, col2 = st.columns([0.4,0.6], gap="large")        
        with st.spinner("O Assistente Financeiro está processando sua pergunta... Aguarde."):
            with col1:
                query = translate_content(query, source_lang="pt", target_lang="en") if translate_option else query            
                old_stdout = sys.stdout
                sys.stdout = mystdout = io.StringIO()
                try:
                    # Execução                    
                    response, agent_logs = asyncio.run(run_agent(query))
                    response = str(response).replace("assistant:", "**-->**")

                finally:
                    sys.stdout = old_stdout
                result = translate_content(response, source_lang="en", target_lang="pt") if translate_option else response                            
                st.markdown(result)
                st.divider()
                if st.session_state.get("last_fig") is not None:
                        st.plotly_chart(st.session_state["last_fig"], use_container_width=True)
                else:
                    st.markdown("O gráfico não foi carregado corretamente")
                    
                with st.expander("Ver Log de Execução: (Como o Agente chegou na resposta)", expanded=False):    
                    st.code(agent_logs)
                
                if st.session_state["last_fig"] is not None:
                    st.plotly_chart(st.session_state["last_fig"], use_container_width=True)
            
            with col2:
                if st.session_state["df"] is not None:
                    st.dataframe(st.session_state["df"].head(10)                                                    
                        )
                                
                with st.expander(" Insights rápidos", expanded=True):
                    st.write(st.session_state["summary"])                    
                    
            
else:
    st.sidebar.info("Por favor, carregue um documento na barra lateral para começar a análise financeira.")





    


