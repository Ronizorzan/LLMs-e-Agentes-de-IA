from langchain_community.document_loaders import PyMuPDFLoader
from  langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_qdrant import QdrantVectorStore
from langchain_classic.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import  FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
import os
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
def process_pdf(folder_path=".", chunk_size=500, chunk_overlap=50):
    path = Path(folder_path)
    pdf_files_path = [paths for paths in path.glob("*pdf")]
    pdf_texts = [extract_text_pdf(path) for path in pdf_files_path]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = [chunk for text in pdf_texts for chunk in text_splitter.split_text(text)]

    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-ada-002")
    #embedding_model = "BAAI/bge-m3"
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    
    try: # Tenta criar o vetor no Qdrant, se já existir, apenas usa o existente
        client = QdrantClient(url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
        client.recreate_collection(
        collection_name="projeto_rag_ps5",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE))

        vectorstore = QdrantVectorStore.from_texts(
            url=os.getenv("QDRANT_HOST"),
            api_key=os.getenv("QDRANT_API_KEY"),
            texts=chunks,
            embedding=embeddings,
            prefer_grpc=True,
            force_recreate=True,
            collection_name="projeto_rag_ps5"
        )
    
    except Exception:
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name="projeto_rag_ps5",
            embedding=embeddings
        )  

        


    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10, "fetch_k": 15})
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

    system_prompt = """You are a helpful virtual assistant answering general questions about the video-game console PS5.  
        Use the provided context snippets to guide your response.  
        If you are unsure of the answer, simply say you cannot confirm and share the available contact details.  
        For very common questions, you may suggest a possible solution as an alternative.  
        Keep your response concise.  
        Reply in Portuguese.\n\n"""

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
<div class="footer">
    <p><strong>Desenvolvido por: Ronivan</strong></p>
    <a href="http://107.22.129.114:5678/webhook/4091fa09-fb9a-4039-9411-7104d213f601/chat" target="_blank">
        <img src="https://cdn-icons-gif.flaticon.com/12205/12205168.gif" alt="Film Reel Icon">
    </a>
    <a href="https://github.com/Ronizorzan/LLMs-e-Agentes-de-IA" target="_blank">
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
