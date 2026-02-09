import os
from pathlib import Path
import streamlit as st

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_tavily import TavilySearch
from langchain_docling import DoclingLoader
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from typing_extensions import Annotated
from typing import TypedDict
import pypandoc
from datetime import datetime
import tempfile
from dotenv import load_dotenv
load_dotenv()



# --- CACHE DE RECURSOS ---
@st.cache_resource
def get_tools(id_model, temperature):
    # Cache do LLM e Embeddings para evitar recarregamento
    llm = load_llm(id_model, temperature)
    #embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")   # Modelo de Embedding Alternativo --> (BAAI/bge-small-en-v1.5, BAAI/bge-m3)
    return llm#, embeddings


def load_llm(id_model="openai/gpt-oss-120b", temperature=0.7, max_tokens=None):
    llm = ChatGroq(
        model=id_model,
        temperature=temperature,
        timeout=None,
        max_tokens=max_tokens,
        max_retries=3
        )
    return llm


def format_res(response, return_thinking=False):
    res = response.content
    if "<think>" in res and return_thinking:
        res = res.replace("<think>", "pensando")
        res = res.replace("</think>", "\n---\n")
        if "</think>" and not return_thinking:
            return res.split("</think>")[-1].strip()
    return res


# Função para criar o prompt caso não seja fornecido nenhum conteúdo para contexto
def build_prompt(topic, quantity, level, interests):
    prompt = f"""
Você é um tutor especialista em {topic}. Gere {quantity} exercícios EM PORTUGUÊS para um aluno de nível {level}.
{f"- Apenas caso faça sentido no contexto, adapte de forma natural e sutil os enunciados dos exercícios para refletir a afinidade do aluno com o tema '{interests}'." if interests else ""}
- Formato dos exercícios: Múltipla escolha com 4 opções.
- Incluir explicação passo a passo e o raciocínio usado para chegar à resposta.
- Não use LaTeX e nenhuma sequência iniciada por barra invertida (como \frac, \sqrt, ou similares). Use apenas linguagem natural e símbolos comuns do teclado.

Exemplo de estrutura:
1. [Enunciado]
   - a) [Opção 1]
   - b) [Opção 2]
   - c) [Opção 3]
   - d) [Opção 4]

   > **Resposta:** [Letra correta] 

   > **Explicação:** [Passo a passo detalhado]
"""
    return prompt

def build_rag_prompt(quantity, level, interests, context):
    prompt = f"""
        Gere {quantity} exercícios sobre o conteúdo fornecido como contexto abaixo. Nível de dificuldade: {level}.
        Cada exercício deve ser de múltipla escolha com 4 alternativas e no idioma português.
        Ao final, inclua as respostas corretas e uma explicação passo a passo.
        Não invente dados externos nem saia do escopo do material apresentado, utilize exclusivamente o conteúdo fornecido como contexto.
        Para e explicação da resposta, não justifique mencionando que foi obtido com o contexto fornecido abaixo. Você deve justificá-la com base no conhecimento que você tem.
        {f"- Apenas caso faça sentido no contexto, adapte de forma natural e sutil os enunciados dos exercícios para refletir a afinidade do aluno com o tema '{interests}'" if interests else ""}        
        - Não use LaTeX e nenhuma sequência iniciada por barra invertida (como \frac, \sqrt, ou similares). Use apenas linguagem natural e símbolos comuns do teclado.

        Exemplo de estrutura:
        1. [Enunciado]
        - a) [Opção 1]
        - b) [Opção 2]
        - c) [Opção 3]
        - d) [Opção 4]

        > **Resposta:** [Letra correta]

        > **Explicação:** [Passo a passo detalhado]        
        """
    prompt_template_rag = """
    {input}
    --------
    {context}
        """        
    template_rag = PromptTemplate(
        input_variables=["input", "context"],
        template=prompt
    )
    final_prompt = prompt_template_rag.format(input=template_rag, context=context)
    return final_prompt

    
    


def config_retriever(docs, embeddings, qdrant_collections="projeto_educacao"):
    vector_store = QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        url=os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
        prefer_grcp=True,
        collection_name=qdrant_collections
    )
    return vector_store.as_retriever()



def get_retriever(qdrant_collection: str, embeddings, recreate: bool = False):
    """
    Cria ou recupera um retriever baseado em Qdrant.
    Se a coleção não existir ou se 'recreate=True', a coleção será recriada.

    Parameters
    ----------
    qdrant_collection : str
        Nome da coleção no Qdrant.
    embeddings : Embeddings
        Objeto de embeddings usado para indexar os dados.
    recreate : bool, default=False
        Se True, força a recriação da coleção mesmo que já exista.

    Returns
    -------
    retriever : BaseRetriever
        Objeto retriever configurado para busca MMR.
    """

    # Conexão com Qdrant
    client = QdrantClient(
        url=os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    # Verifica se a coleção existe
    collections = [c.name for c in client.get_collections().collections]

    if recreate and qdrant_collection in collections:
        client.delete_collection(qdrant_collection)
        collections.remove(qdrant_collection)

    if qdrant_collection not in collections:
        # Cria coleção nova
        client.create_collection(
            collection_name=qdrant_collection,
            vectors_config=client.get_fastest_config(embeddings)
        )

    # Cria o vector store a partir da coleção
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=qdrant_collection
    )

    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 10}
    )


def parse_documents(file_path):
    loader = DoclingLoader(file_path)
    docs = loader.load()
    return docs



def load_documents(input_path):
    input_path = Path(input_path)
    if input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))
    elif input_path.is_file():
        pdf_files = [input_path]
    else:
        raise ValueError("Caminho inválido. Forneça um diretório ou arquivo válido")
    
    documents = []

    # Extrai e concatena cada documento com a função parse
    for file in pdf_files:
        documents.extend(parse_documents(file))

    print(f"Documentos carregados: {len(documents)}")
    return documents


def split_markdown(documents):
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header1"),
            ("##", "Header2"),
            ("#", "Header3")
        ]
    )
    markdown_splits = [
        split for doc in documents
        for split in splitter.split_text(doc.page_content)
    ]
    print(f"Splits Gerados: {len(markdown_splits)}")

    return markdown_splits


def split_chunks(markdown_splits, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(markdown_splits)
    print(f"Chunks gerados: {len(chunks)}")
    return chunks


def build_chunks(input_path):
    documents = load_documents(input_path)
    markdown_splits = split_markdown(documents)
    chunks = split_chunks(markdown_splits)
    return chunks


class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_tools(tools):
    return tools, ToolNode(tools)


def stream_graph_updates(messages):

    
    builder = StateGraph(State)
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    # Reserva um espaço dinâmico para as mensagens
    placeholder = st.empty()

    for event in graph.stream(
        {"messages": messages},
        {"configurable": {"thread_id": "1"}}
    ):
        for value in event.values():
            last_message = value["messages"].content[-1]
            if len(last_message) >0:
                placeholder.markdown(f"**Tutor: {last_message}**")


def convert_docx(doc_content):    
    if not doc_content:
        st.warning(f"Nenhum conteúdo fornecido. Gere um exercício para salvamento")
        return 
        
    timestamp = datetime.now().strftime("%Y-%m-%d-H:M")    
    filename = f"exercicios{timestamp}.docx"

    # Cria arquivo temporário
    tmp_path = Path(tempfile.gettempdir()) / filename

    # Converte e Salva em docx

        
    content = f"Conteúdo personalizado  \n---\n" + format_res(doc_content)    
    pypandoc.convert_text(content, "docx", format="md", outputfile=str(tmp_path))
    
    #Lê os bytes para download no streamlit
    with open(tmp_path, "rb") as file:
        file_bytes = file.read()
                
    return file_bytes, filename


@tool
def wikipedia_tool(query): 
    """Útil para pesquisas na Wikipedia"""   
    wikipedia_tool = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(),
        description="Use para pesquisas na Wikipedia sempre que necessário."
    )
    return wikipedia_tool.run(query)


@tool
def search_tool(query: str):
    """Busca informações na internet com base na consulta fornecida.
    Use sempre que o usuário pedir por informações recentes, por pesquisa, ou quando você julgar que é necessário."""    
    tavily_search = TavilySearch(max_results=2)
    result = tavily_search.invoke(query)
    return result


def get_llm_tools(llm):
    tools = [wikipedia_tool, search_tool]
    tools_node = ToolNode(tools=tools)
    llm_with_tools = llm.bind_tools(tools=tools)
    return llm_with_tools, tools_node

llm = load_llm(max_tokens=3000)
llm_with_tools, tools_node = get_llm_tools(llm)

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

