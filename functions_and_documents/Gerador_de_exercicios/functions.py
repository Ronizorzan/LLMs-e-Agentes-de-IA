import os

from langchain_groq import ChatGroq
import qdrant_client
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


def load_llm(id_model="openai/gpt-oss-120b", temperature=0.7):
    llm = ChatGroq(
        model=id_model,
        temperature=temperature,
        timeout=None,
        max_tokens=None,
        max_retries=3)
    return llm


def format_res(response, return_thinking=False):
    res = response.content
    if "<think>" in res and return_thinking:
        res = res.replace("<think>", "pensando")
        res = res.replace("</think>", "\n---\n")
        if "</think>" and not return_thinking:
            return res.split("</think>")[-1].strip()
    return res


# Função para criar o prompt
def build_prompt(topic, quantity, level, interests):
    prompt = f"""
Você é um tutor especialista em {topic}. Gere {quantity} exercícios para um aluno de nível {level}.
{f"- Apenas caso faça sentido no contexto, adapte de forma natural e sutil os enunciados dos exercícios para refletir a afinidade do aluno com o tema '{interests}'." if interests else ""}
- Formato dos exercícios: Múltipla escolha com 4 opções.
- Incluir explicação passo a passo e o raciocínio usado para chegar à resposta.
- Não use LaTeX e nenhuma sequência iniciada por barra invertida (como \frac, \sqrt, ou similares). Use apenas linguagem natural e símbolos comuns do teclado.

Exemplo de estrutura:
1. [Enunciado]
   a) Opção 1
   b) Opção 2
   c) Opção 3
   d) Opção 4
   Resposta: [Letra correta]
   Explicação: [Passo a passo detalhado]
"""
    return prompt

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


