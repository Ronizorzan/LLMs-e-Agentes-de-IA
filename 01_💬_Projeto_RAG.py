from functions_and_documents.ProjetoRAG.functions import *
import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

#Configuração do Layout
st.set_page_config(page_title="Auto-Atendimento - PS5", page_icon="🎮")
st.subheader("Chat Assistente Virtual - PS5")
st.sidebar.markdown(markdown, unsafe_allow_html=True)


# Carregamento da LLM
llm = ChatGroq(model="openai/gpt-oss-20b",
               timeout=None,
               max_tokens=None,
               max_retries=2,
               temperature=0.7)


if "chat_started" not in st.session_state:
    st.session_state.chat_started = None

if "retriever" not in st.session_state:
    st.session_state.retriever = None

if not st.session_state.chat_started:
    if st.button("Iniciar atendimento",
                              help="Clique no botão para iniciar o atendimento"):
        with st.spinner("Carregando os manuais do console... Isso pode levar alguns segundos... "):
            st.session_state.retriever = process_pdf("functions_and_documents/")
            st.session_state.chat_started = True
            st.rerun()
    st.markdown("Pressione o botão para iniciar seu atendimento...")
    st.stop()


# Entrada do Chat
chat_input = st.chat_input("Digite sua mensagem aqui...")

# Exibe a primeira mensagem no chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage("Olá! Eu sou seu assistente virtual. "
                                               "Posso esclarecer todas as suas dúvidas sobre o console PS5!")]

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    if isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)


if chat_input is not None:
    with st.chat_message("Human"):
        st.markdown(chat_input)

    with st.chat_message("AI"):
        rag_chain = config_rag_chain(llm, st.session_state.retriever)
        response = chat_llm_streamlit(rag_chain, chat_input)
        st.markdown(response)

