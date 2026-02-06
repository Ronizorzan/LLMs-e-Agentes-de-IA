import streamlit as st
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Importações do seu projeto
from functions_and_documents.Gerador_de_exercicios.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown

load_dotenv()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LinRecom | IA Education", layout="wide", page_icon="📘")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; margin-bottom: 1rem; }
    .card { background-color: white; padding: 2rem; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CACHE DE RECURSOS ---
@st.cache_resource
def get_tools():
    # Cache do LLM e Embeddings para evitar recarregamento
    llm = load_llm("meta-llama/llama-4-maverick-17b-128e-instruct")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    return llm, embeddings

llm, embeddings = get_tools()

# --- SIDEBAR (CONFIGURAÇÕES E CONTATO) ---
with st.sidebar:
    st.image("https://github.com/Ronizorzan.png", width=80)
    st.title("Painel de Controle")

    with st.expander("⚙️ Parâmetros da IA", expanded=True):
        id_model = st.selectbox("Modelo", options=("Llama-4 Maverick", "GPT-OSS 120B"))
        temperature = st.slider("Criatividade (Temp)", 0.1, 1.5, 0.7)

    with st.expander("✉️ Contato", expanded=False):
        st.markdown(markdown, unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
st.markdown('<h1 class="main-header">📘 Gerador de Exercícios Inteligente</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎯 Gerador de Conteúdo", "🤖 Tutor RAG Digital"])

with tab1:
    # Divisão em Colunas: Esquerda (Input) | Direita (Output)
    col_input, col_output = st.columns([0.4, 0.6], gap="large")

    with col_input:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Configurar Geração")

        with st.form("form_geracao"):
            topic = st.text_input("Tema Principal", placeholder="Ex: Machine Learning em AWS")
            files = st.file_uploader("Documentos de Contexto (PDF)", type=["pdf"], accept_multiple_files=True)

            c1, c2 = st.columns(2)
            level = c1.selectbox("Nível", ["Iniciante", "Intermediário", "Avançado"])
            quantity = c2.number_input("Qtd. Exercícios", 1, 20, 5)

            interests = st.text_area("Personalização (Interesses)", placeholder="Ex: Focar em estudos de caso reais...")

            generate_btn = st.form_submit_button("Gerar Material agora 🚀", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_output:
        if generate_btn:
            if not topic and not files:
                st.warning("⚠️ Por favor, informe um tema ou carregue um arquivo.")
            else:
                with st.spinner("🧠 A IA está processando seu material..."):
                    try:
                        all_context = ""
                        # Processamento de arquivos para RAG
                        if files:
                            for uploaded_file in files:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                    tmp.write(uploaded_file.read())
                                    chunks = build_chunks(Path(tmp.name))
                                    all_context += f"\n{chunks}"

                            prompt = build_rag_prompt(quantity, level, interests, all_context)
                        else:
                            prompt = build_prompt(topic, quantity, level, interests)

                        # Invocação do Modelo
                        res = llm.invoke(prompt)

                        # Área de Resultado
                        st.success("✅ Exercícios Gerados com Sucesso!")
                        st.markdown("---")
                        st.markdown(format_res(res))

                        # Ações de Download
                        file_docx, path = convert_docx(res)
                        if file_docx:
                            st.download_button(
                                label="⬇️ Baixar em DOCX",
                                data=file_docx,
                                file_name=f"{topic or 'exercicios'}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Ocorreu um erro no processamento: {e}")

with tab2:
    st.info("🤖 O Tutor Digital está sendo treinado com seus documentos do AWS App Runner.")
    st.image("https://raw.githubusercontent.com/Ronizorzan/Projeto-LinRecom/main/reports/figures/workflow.png", caption="Arquitetura RAG")
