import streamlit as st
from functions_and_documents.Gerador_de_exercicios.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown
import tempfile
from dotenv import load_dotenv
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
        model = st.selectbox("Modelo", options=("GPT-20B", "Llama"))
        temperature = st.slider("Criatividade do Modelo", 0.1, 1.5, 0.7, 
                                help="""Valores baixos = respostas mais objetivas\
                                \nvalores altos = respostas mais criativas""" )
    
    with st.expander("Contato e Assistência", expanded=False, icon="✉️"):
        st.markdown(markdown, unsafe_allow_html=True)


# Funções Adicionais
def agent(state: State):
    messages = state["messages"]        
    response = llm_with_tools.invoke(messages)
    tool_calls = response.additional_kwargs.get("tool_calls")
    if tool_calls is not None:
        st.write(tool_calls)
    return {"messages": [response], "tool_calls": tool_calls}


def graph_builder():
    builder = StateGraph(State)
    
    builder.add_node("agent", agent)
    builder.add_node("tools", tools_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, ["tools", END])
    builder.add_edge("tools", "agent")
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph




# Carregamento do Modelo Escolhido com cache (PARA OTIMIZAÇÃO DE DESEMPENHO)
id_model = "openai/gpt-oss-20b" if model=="GPT-20B" else "meta-llama/llama-prompt-guard-2-86m"
llm = get_tools(id_model, temperature) 

# --- CONTEÚDO PRINCIPAL ---
st.markdown('<h1 class="main-header">📘 Gerador de Exercícios Inteligente</h1>', unsafe_allow_html=True)
st.sidebar.markdown(
    "### ⚠️ IMPORTANTE\n"
    "Lembre-se: a IA funciona como suporte ao aprendizado, "
    "mas a correção final deve sempre ser feita por um profissional da educação qualificado.",
    unsafe_allow_html=False
)


tab1, tab2 = st.tabs(["🎯 Gerador de Conteúdo", "👨‍🏫 Tutor Digital"])

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
                    response = str(res.content)
                    st.markdown(response)

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
    # Agente com as ferramentas (Wikipedia e Tavily)
    llm_with_tools, tools_node = get_llm_tools(llm)
    # Layout: uma coluna para o chat, outra para as perguntas do usuário
    chat_col, output_col = st.columns([0.3, 0.7], gap="large")

    # Mensagem Inicial do Agente
    initial_message = """Olá, eu sou seu tutor digital! Estou aqui para lhe ajudar com todas as suas dúvidas.\
            \nDesde explicações sobre os exercícios até pesquisas sobre tópicos recentes na internet!"""     

    # Inicializar e salvar o estado do agente com as ferramentas
    if "graph" not in st.session_state:
        st.session_state["graph"] = graph_builder()
    graph = st.session_state["graph"]

    # Inicializar mensagens apenas uma vez
    if "messages" not in st.session_state or st.session_state["messages"] is None:
        st.session_state["messages"] = [("assistant", initial_message)]
        chat_col.chat_message("assistant", avatar="🎓").write(initial_message)

    # Inicializar logs
    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    
    # Input fixo no rodapé da aba
    user_input = chat_col.chat_input("Digite aqui sua pergunta...")
    if user_input:
        # Adiciona mensagem do usuário
        st.session_state["messages"].append(("user", user_input))

        chat_col.chat_message("user").write(user_input)

        with output_col.chat_message("assistant", avatar="🎓"):
            #st.status para esconder a complexidade do agente 
            with st.status("🔍 Consultando fontes e processando...", expanded=False) as status:       # Mensagem inical de Status         
                try:
                    for event in graph.stream(
                        {"messages": [("user", user_input)]},
                        {"configurable": {"thread_id": "1"}}
                    ):
                        for node, value in event.items():
                            # Captura mensagens de ferramentas (Wikipedia, Tavily)
                            current_msg = value["messages"][-1]
                            
                            if hasattr(current_msg, "tool_calls") and current_msg.tool_calls:
                                for tool in current_msg.tool_calls:
                                    st.write(f"🛠️ Ativando ferramenta: **{tool['name']}**")
                                    st.caption(f"Argumentos: {tool['args']}") # Menos técnico que o JSON puro
                            
                            # Se for a resposta final da ferramenta (output do Tavily/Wiki)
                            if current_msg.type == "tool":
                                st.write(f"✅ Informações coletadas de {current_msg.name}")
                                # Mostramos apenas um resumo ou o conteúdo formatado, não o JSON bruto
                                with st.expander("Ver dados brutos da pesquisa"):
                                    st.json(current_msg.content)

                    status.update(label="✅ Pesquisa concluída!", state="complete", expanded=False)

                    # Exibe a resposta final amigável fora do status
                    final_res = value["messages"][-1].content
                    output_col.markdown(final_res)
                    st.session_state["messages"].append(("assistant", final_res))

                except Exception as error:
                    status.update(label="Erro ao processar a requisição.", state="error")
                    st.error(f"Erro ao processar a requisição. Por favor tente novamente: {error}")
                                

                
                        
                