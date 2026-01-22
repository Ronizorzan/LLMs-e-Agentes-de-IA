import streamlit as st
from functions_and_documents.Gerador_de_exercicios.functions import *
from functions_and_documents.ProjetoRAG.functions import markdown
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Geração de Exercícios", layout="centered")
st.markdown(markdown, unsafe_allow_html=True)


st.sidebar.header("Configurações do Modelo")
id_model = st.sidebar.text_input("ID do Modelo", value = "openai/gpt-oss-120b")
temperature = st.sidebar.slider("Temperatura do Modelo", 0.1, 1.5, 0.7, 0.1)

with st.form("formulario"):
  level = st.selectbox("Nível", ["Iniciante", "Intermediário", "Avançado"])
  topic = st.text_input("Tema", placeholder="Matemática, Inglês, Física, Biologia, etc.")
  quantity = st.slider("Quantidade de Exercícios", 1, 10, 5)
  interests = st.text_input("Interesses ou Preferências", placeholder="Ex: Filmes, Esportes, Jogos, Música, etc....")
  generate_btn = st.form_submit_button("Gerar Exercícios")

if generate_btn:
  with st.spinner("Gerando exercícios...")
    prompt = build_prompt(topic, quantity, level, interests)
    llm = load_llm(id_model, temperature)
    res = llm.invoke(prompt)
    st.markdown(format_res(res, return_thinking=True))
