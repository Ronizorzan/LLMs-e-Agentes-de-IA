# Usa uma imagem oficial do Python
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala uv (sem precisar do pip install uv separado)
RUN pip install uv

# Copia os arquivos de dependências
COPY requirements.txt .

# Instala as dependências
RUN uv pip install -r requiremets.txt

# Copia o restante do projeto
COPY . .

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar o Streamlit
CMD ["streamlit", "run", "04_💵_Assistente_Financeiro.py", "--server.port=8501"]