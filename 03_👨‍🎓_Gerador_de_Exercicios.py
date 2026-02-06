import streamlit as st
from functions_and_documents.Gerador_de_exercicios.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown
from langchain_huggingface import HuggingFaceEmbeddings
import tempfile
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

st.set_page_config(page_title="Geração de Exercícios", layout="wide")


#  --- APLICA ESTILIZAÇÃO CUSTOMIZADA (CSS) ---estilização com CSS
with open("style.css") as f:
   st.markdown(f"""<style>{f.read()}</style> """, unsafe_allow_html=True) 


# --- SIDEBAR (CONFIGURAÇÕES E CONTATO) ---
with st.sidebar:
    st.image("https://th.bing.com/th/id/OIG3.qDcKcmcgj3BZ71_PJvPb?w=270&h=270&c=6&r=0&o=5&pid=ImgGn", width=250)
    st.title("Painel de Controle")
    
    with st.expander("⚙️ Parâmetros da IA", expanded=True):
        model = st.selectbox("Modelo", options=("GPT-120B", "Llama"))
        temperature = st.slider("Criatividade do Modelo", 0.1, 1.5, 0.7, 
                                help="""Valores baixos = respostas mais objetivas\
                                \nvalores altos = respostas mais criativas""" )
    
    with st.expander("✉️ Contato", expanded=False):
        st.markdown(markdown, unsafe_allow_html=True)

#st.header("📘 Gerador de Exercícios Inteligente", divider="red")  
#tab1, tab2 = st.tabs(["Gerador de Exercícios", "Tutor Digital"])


id_model = "openai/gpt-oss-120b" if model=="GPT-120B" else "meta-llama/llama-4-maverick-17b-128e-instruct"
llm, embeddings = get_tools(id_model, temperature)

# --- CONTEÚDO PRINCIPAL ---
st.markdown('<h1 class="main-header">📘 Gerador de Exercícios Inteligente</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎯 Gerador de Conteúdo", "🤖 Tutor RAG Digital"])

# Interface Geração de exercícios
with tab1:  
    # Divisão em Colunas: Esquerda (Input) | Direita (Output)
  col_input, col_output = st.columns([0.45, 0.55], gap="large")  
  with col_input:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Configurar Geração")
    with st.form("formulario"):                  
        col1, col2 = st.columns(2)
        file = col1.file_uploader("📄 Carregue um PDF (opcional)", type=["pdf"],
                          help="Se carregar um documento, os exercícios serão baseados no conteúdo dele", accept_multiple_files=True)
        level = col2.selectbox("Nível", ["Iniciante", "Intermediário", "Avançado"], index=1,
                          help="Se um arquivo for carregado como contexto, os exercícios serão baseados apenas no conteúdo do documento.")
        
        topic = col1.text_input("Tema", placeholder="Matemática, Inglês, Programação, Desenvolvimento Web, etc.", help="""Se um PDF for carregado\
                                \nesse campo será ignorado""")
        quantity = col2.number_input("Quantidade de Exercícios", 1, 15, 5)
        interests = col2.text_input("Interesses ou Preferências", placeholder="Ex: Filmes, Esportes, Jogos, Música, etc....")
        generate_btn = st.form_submit_button("Gerar Material agora 🚀", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
  
  
  with col_output:
    if generate_btn:
        if not topic and not file:
            st.warning("⚠️ Por favor, informe um tema ou carregue um arquivo.")
        else:
            with st.spinner("🧠 A IA está processando seu material..."):
                try:
                    if file:
                        # Cria um identificador único para o(s) arquivo(s)
                        file_id = "-".join([f"{f.name}-{f.size}" for f in file])

                        # Só processa se for um arquivo novo
                        if st.session_state.get("processed_file_id") != file_id:
                            for uploaded_file in file:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                    tmp_file.write(uploaded_file.read())
                                    tmp_path = Path(tmp_file.name)

                                    # Processa chunks apenas uma vez
                                    context = build_chunks(tmp_path)
                                    st.session_state["cached_context"] = context
                                    st.session_state["processed_file_id"] = file_id
                                    st.toast("Conhecimento do documento atualizado!", icon="📚")

                        # Sempre usa o contexto já armazenado
                        context = st.session_state.get("cached_context", [])
                        prompt = build_rag_prompt(quantity, level, interests, context)

                    else:                        
                        prompt = build_prompt(topic, quantity, level, interests)
                        

                    # Geração final
                    res = llm.invoke(prompt)
                    st.markdown(format_res(res, return_thinking=False))

                    file_docx, path = convert_docx(res)
                    if file_docx:
                        col_input.download_button(
                            "⬇️ Baixar conteúdo em DOCX",
                            key="download_button",
                            data=file_docx,
                            file_name=path,
                            use_container_width=True,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a aplicação: {e}")


with tab2:
    # Layout: uma coluna para o chat, outra para controles extras
    chat_col, side_col = st.columns([0.7, 0.3], gap="large")

    if "graph" not in st.session_state:
        st.session_state["graph"] = graph_builder()
    graph = st.session_state["graph"]

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            ("assistant", "Olá, eu sou seu tutor digital. Como posso lhe ajudar?")
        ]    

    # Input fixo no rodapé da aba (fora das colunas)
    user_input = chat_col.chat_input("Digite sua pergunta...")

    if user_input:
        with st.spinner("Consultando o agente... Por favor aguarde"):
            st.session_state["messages"].append(("user", user_input))                       

            for event in graph.stream(
                {"messages": [("user", user_input)]},
                {"configurable": {"thread_id": "1"}}
            ):
                for value in event.values():
                    last_message = value["messages"][-1].content
                    if last_message:
                        st.session_state["messages"].append(("assistant", last_message))                                                                                                

                        if "query" not  in last_message or "0" not in last_message:
                           st.chat_message("assistant").markdown(last_message)
                        
                        #with side_col:
                        #    if "query" or "0" in last_message:
                        #        with st.expander("Ver logs do Agente"):
                        #            st.markdown(last_message)
                                    
                           


          



  
