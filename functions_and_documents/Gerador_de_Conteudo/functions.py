# Função utilizada no Projeto Gerador_de_Conteudo
from langchain_groq import ChatGroq
from langchain_core.prompts import  ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ======================= Carregamento da LLM (Projeto Gerador_de_Conteudo) ====================================
def load_llm(id_model, prompt):
    llm = ChatGroq(model=id_model,
                   max_retries=2,
                   max_tokens=None,
                   temperature=0.9,
                   timeout=None)

    template = ChatPromptTemplate.from_messages([
        ("system", "Você é um especialista em marketing digital com foco em SEO e escrita persuasiva."),
        ("human", "{prompt}")
    ])

    chain = template | llm | StrOutputParser()

    # Remove o raciocínio da resposta se houver
    res = chain.invoke({"prompt": prompt})
    if "</think>" in res:
        res = res.split("</think>")[-1].strip()

    return res