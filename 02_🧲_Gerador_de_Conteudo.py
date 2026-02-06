# Importações necessárias
import streamlit as st
from dotenv import load_dotenv
from functions_and_documents.Gerador_de_Conteudo.functions import load_llm

st.set_page_config(page_title="🤖 Gerador de Conteúdo", layout="centered")

chave_groq = load_dotenv()

with st.sidebar:
    id_model = "llama-3.1-8b-instant" # "llama-3.3-70b-versatile"
    st.markdown("## ⚙️ Configurações da Geração")
    topic= st.text_area("Tema", placeholder="Ex: Saúde, Alimentação Saudável, Exercícios Físicos etc")
    keywords = st.text_area("Incluir palavras chave", placeholder="Deseja incluir palavras-chave")
    avoid_keywords = st.text_area("Palavras a evitar", placeholder="Ex: junk food, sedentário, etc")
    platform = st.selectbox("Selecione a plataforma", options=("LinkedIn", "Facebook", "Blog", "X", "Instagram"))
    length = st.selectbox("Selecione o tamanho da mensagem", options=("Curto", "Médio", "Longo", "Um Parágrafo", "Uma Página"))
    tone = st.selectbox("Selecione o tom da mensagem", options=("Normal", "Inspirador", "Urgente", "Informal", "Informativo", "Divertido", "Profissional"))
    public = st.selectbox("Selecione o público alvo", options=("Adolescentes", "Adultos", "Jovens adultos", "Profissionais de marketing", "Empreendedores", "Público geral"))
    cta = st.text_area("Incluir CTA", placeholder="Ex: Clique aqui, Saiba mais, Inscreva-se")        
    with st.expander("Opções Adicionais"):
        analogys = st.checkbox("Incluir analogias", value=False)
        hashtags = st.checkbox("Incluir Hashtags", value=False)    
        emojis = st.checkbox("Incluir Emojis", value=False)    
    generate_button = st.button("Gerar Conteúdo", use_container_width=True)

if generate_button:
    with st.spinner("Aguarde... Gerando conteúdo..."):
        prompt = f""""
        Escreva um texto com SEO otimizado sobre o tema: {topic}.
        O conteúdo deve ser exclusivo para alcançar engajamento do público na plataforma: {platform}.
        Retorne em sua resposta apenas o texto final sem aspas ou conclusões.
        O tamanho da mensagem deve ser {length}.
        O tom da mensagem é: {tone}.
        Público alvo da mensagem: {public}.
        - {"Inclua uma analogia concisa" if analogys else "Não inclua analogias"}
        - {"Evite as seguintes palavras: " + avoid_keywords if avoid_keywords else "Não há palavras a evitar"}
        - {"inclua chamada à ação clara com: " + cta if cta else "Não inclua chamada à ação"}
        - {"Inclua no texto as seguintes palavras-chave" + keywords if keywords else "Nenhum palavra-chave específica"}
        - {"Inclua hashtags relevantes" if hashtags else "Não inlcua hashtags"}
        - {"Inclua emojis apropriados" if emojis else "Não inclua emojis"}
        """
        
        res = load_llm(id_model, prompt)
        st.title("📝 Conteúdo Gerado")
        st.markdown(res)


