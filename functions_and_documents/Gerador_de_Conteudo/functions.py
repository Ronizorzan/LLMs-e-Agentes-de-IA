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
        ("system", """Você é um especialista em marketing digital com foco em SEO, copywriting persuasivo e estratégias de engajamento em redes sociais.
         Sua missão é criar conteúdos originais, criativos e otimizados para aumentar o engajamento em redes sociais. 

        Regras:
        - Use linguagem envolvente e clara, ajustando o tom conforme a rede social.        
        - Aplique técnicas de storytelling e gatilhos mentais (curiosidade, urgência, autoridade, prova social).                
        - Sempre entregue exemplos práticos e prontos para publicação, de acordo com os parâmetros fornecidos."""),
        ("human", "{prompt}")
    ])

    chain = template | llm | StrOutputParser()

    # Remove o raciocínio da resposta se houver
    res = chain.invoke({"prompt": prompt})
    if "</think>" in res:
        res = res.split("</think>")[-1].strip()

    return res