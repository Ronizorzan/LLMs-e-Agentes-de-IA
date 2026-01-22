from langchain_community.document_loaders import PyMuPDFLoader
from  langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import  FAISS
from langchain_core.messages import HumanMessage, AIMessage
import  streamlit as st
from pathlib import Path


# ====================== Extrator de textos de documentos PDF ========================================
def extract_text_pdf(pdf_path):
    """Usa o `PyMuPDFLoader` para extrair
    e concatenar textos de um pdf.
    Retorna os textos concatenados em uma única string.
    """
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()
    pdf_texts = "\n".join([doc.page_content for doc in docs])
    return pdf_texts


# =================== Processamento dos documentos com embedding e indexação ======================================
def process_pdf(folder_path=".", chunk_size=1000, chunk_overlap=100):
    """Lista todos os arquivos em formato
    pdf em uma determinada pasta.
    Divide, aplica embedding e indexação dos documentos para maior eficiência.
    """

    # Extração e concatenação dos textos
    path = Path(folder_path)
    pdf_files_path = [paths for paths in path.glob("*pdf")]
    pdf_texts = [extract_text_pdf(path) for path in pdf_files_path]

    # Divisão dos textos em pedaços menores
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap)

    chunks = []
    for docs in pdf_texts:
        chunks.extend(text_splitter.split_text(docs))

    # Embedding dos documentos
    embedding_model = "BAAI/bge-m3"
    embeddings = HuggingFaceEmbeddings(model=embedding_model)

    # Indexação e recuperação dos documentos
    if Path("functions_and_documents/index_ps5").exists():
        vectorstore = FAISS.load_local("functions_and_documents/index_ps5",
                                       embeddings, allow_dangerous_deserialization=True)
        # st.success("Reaproveitando documentos carregados previamente...")

    else:  # Caso contrário, cria os índices
        vectorstore = FAISS.from_texts(chunks, embeddings)
        vectorstore.save_local("functions_and_documents/index_ps5")

    retriever = vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10}
    )

    return retriever

def config_rag_chain(llm, retriever):
    context_q_system_prompt = ("""Given the following chat history and the follow-up question
                        which might reference context in the chat history, formulate 
                       a standalone question which can be understood without the chat history.
                   Do NOT answer the question, just reformulate it if needed and otherwise return it as is.""")

    context_q_user_prompt = "Question: {input}"

    context_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", context_q_system_prompt),
            (MessagesPlaceholder("chat_history")),
            ("human", context_q_user_prompt)
        ]
    )


    history_aware_retriever = create_history_aware_retriever(
        llm=llm, retriever=retriever, prompt=context_q_prompt
    )

    system_prompt = """Você é um assistente virtual prestativo e está
     respondendo perguntas gerais sobre os serviços de uma empresa.
  Use os seguintes pedaços de contexto recuperado para responder à pergunta.
  Se você não sabe a resposta, apenas comente que não sabe dizer com certeza, e passe os dados de contato, se disponíveis.
  Mas caso seja uma dúvida muito comum, pode sugerir como alternativa uma solução possível.
  Mantenha a resposta concisa.
  Responda em português. \n\n"""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "Pergunta: {input}\n\n Contexto: {context}")
    ])

    qa_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        qa_chain
    )

    return rag_chain


def chat_llm_streamlit(rag_chain, chat_input):

    st.session_state.chat_history.append(HumanMessage(content=chat_input))

    response = rag_chain.invoke({
        "input": chat_input,
        "chat_history": st.session_state.chat_history
    })

    final_res = response["answer"]

    if "</think>" in final_res:
        response = final_res.split("</think>").strip()[-1]
    else:
        response = final_res.strip()

    st.session_state.chat_history.append(AIMessage(content=response))

    return response

# Rodapé na barra lateral com as informações do desenvolvedor
markdown = """
<style>
.footer {
    background-color: #f8f9fa;
    padding: 20px 25px;
    border-radius: 10px;
    border-left: 9px solid #972328;
    text-align: center;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-top: 20px;
    color: #343a40;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
.footer p {
    font-size: 16px;
    margin-bottom: 15px;
}
.footer a {
    margin: 0 12px;
    display: inline-block;
}
.footer img {
    height: 36px;
    width: 36px;
    border-radius: 6px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.footer img:hover {
    transform: scale(1.1);
    box-shadow: 0 0 8px rgba(151, 35, 40, 0.4);
}
</style>

<div class="footer">
    <p><strong>Desenvolvido por: Ronivan</strong></p>
    <a href="http://107.22.129.114:5678/webhook/4091fa09-fb9a-4039-9411-7104d213f601/chat" target="_blank">
        <img src="https://cdn-icons-gif.flaticon.com/12205/12205168.gif" alt="Film Reel Icon">
    </a>
    <a href="https://github.com/Ronizorzan/Projeto-LinRecom" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/128/2504/2504911.png" alt="GitHub">
    </a>
    <a href="https://www.linkedin.com/in/ronivan-zorzan-barbosa" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/128/1384/1384072.png" alt="LinkedIn">
    </a>
    <a href="mailto:ronizorzan1992@gmail.com" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/128/5968/5968534.png" alt="Email">
    </a>

</div>
"""
