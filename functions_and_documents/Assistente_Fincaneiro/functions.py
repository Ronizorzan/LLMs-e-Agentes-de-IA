from llama_index.llms.google_genai import GoogleGenAI
from llama_index.experimental.query_engine import PandasQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.agent.workflow import AgentStream, ToolCallResult, FunctionAgent
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from deep_translator import GoogleTranslator
import plotly.graph_objects as go
import pandas as pd
import sys
import io
import streamlit as st
from pathlib import Path
from typing import Dict, Union



# ============================ Carregamento e indexação dos documentos em PDF =========================
def load_and_index_documents(file_path: str):
    docs = SimpleDirectoryReader(input_files=[file_path]).load_data()

    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.embed_model = embed_model

    index = VectorStoreIndex.from_documents(
        docs, embed_model=embed_model
    )
    return docs, index


# ================== Resumo inicial dos documentos ==========================
def summary_docs(content: str):
    template = """
    Você é um analista financeiro com vasta experiência em análise financeira.
    Ao ler o relatório a seguir, extraia insights financeiros relevantes e explique-os de forma clara, didática e resumida, como se estivesse apresentando para gestores não especialistas.
    Utilize linguagem acessível e destaque pontos importantes sobre lucros, despesas, fluxo de caixa, riscos e oportunidades.
    Retorne o texto em linguagem natural e com caracteres que possuem em um teclado comum, sem caracteres ou símbolos LaTex, para serem exibidos em uma interface de usuário como markdown.
    Resuma o conteúdo de forma breve e objetiva. Retorne a mensagem direta, sem apresentações no início.    

    ---
    Conteúdo do documento:
    '{}'
    """
    
    llm = Settings.llm
    prompt = template.format(content)
    response = llm.complete(prompt)
    return response.text.strip()


# ==================== Tradução dos documentos para o português =========================
def translate_content(content: str, source_lang: str = "auto", target_lang: str = "pt"):
    translated_content = GoogleTranslator(source=source_lang, target=target_lang).translate(content)
    return translated_content


# ==================== Consulta em planilhas usando PandasQueryEngine =========================
def query_spreadsheet(query):
    """Consulta dados na planilha carregada. Use para cálculos e análises de tabelas utilizando o pandas."""    
    try:
        df = st.session_state["df"]
    except Exception as e:
        st.write(f"Erro ao carregar o arquivo: {str(e)}")
    pandas_query_engine = PandasQueryEngine(df=df, llm=Settings.llm, verbose=True)
    result = pandas_query_engine.query(query)
    return str(result)

# ==================== Execução do agente FunctionAgent =========================
async def run_agent(query):
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    try:
        handler = st.session_state.agent.run(query)

        async for event in handler.stream_events():
            if isinstance(event, ToolCallResult):
                print(f"**{event.tool_name}** with args: {event.tool_kwargs}. Returned: {event.tool_output} ")
            elif isinstance(event, AgentStream):
                print(event.delta, end="", flush=True)
        
        response = await handler
        formatted = f"### Resposta do Assistente Financeiro:\n\n{str(response.response)}"
    
    finally:
        sys.stdout = old_stdout

    logs = mystdout.getvalue()
    return formatted, logs



def generate_graphs(
    df_path: Union[str, Path],
    col_x: str,
    col_y: str = "revenue",
    graph_type: str = "bar",
    color_map: str = "#FFBBFF",
    title: str = "Resumo Financeiro"
):
    """
    Gera gráficos financeiros de forma robusta e flexível.
    O caminho correto do arquivo gravado anteriormente com 'save_df' é obrigatório.

    Parameters
    ----------
    df_path : str | Path
        Caminho para o arquivo CSV contendo os dados.
    col_x : str
        Nome da coluna a ser usada no eixo X.
    col_y : str, default="revenue"
        Nome da coluna a ser usada no eixo Y.
    graph_type : str, default="bar"
        Tipo de gráfico a ser gerado. Opções: "bar", "line", "gauge", "scatter".
    color_map : str, default="#FFBBFF"
        Cor ou esquema de cores para o gráfico.
    title : str, default="Resumo Financeiro"
        Título do gráfico.

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Objeto da figura gerada.
    """

    # Verificação do caminho
    df_path = Path(df_path)
    if not df_path.exists():
        raise FileNotFoundError(f"O arquivo '{df_path}' não foi encontrado.")

    try:
        df = pd.read_csv(df_path)
    except Exception as e:
        raise ValueError(f"Erro ao carregar o DataFrame: {e}")

    # Verificação das colunas
    for col in [col_x, col_y]:
        if col not in df.columns:
            raise KeyError(f"A coluna '{col}' não existe no DataFrame. Colunas disponíveis: {list(df.columns)}")

    fig = go.Figure()

    # Seleção do tipo de gráfico
    if graph_type == "bar":
        fig.add_trace(go.Bar(
            x=df[col_x], y=df[col_y],
            name='Receita',
            marker_color=color_map
        ))
    elif graph_type == "line":
        fig.add_trace(go.Scatter(
            x=df[col_x], y=df[col_y],
            mode='lines+markers',
            name='Receita',
            line=dict(color=color_map)
        ))
    elif graph_type == "gauge":
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=df[col_y].iloc[-1],
            title={'text': title},
            gauge={
                'axis': {'range': [None, df[col_y].max() * 1.2]},
                'bar': {'color': color_map}
            }
        ))
    elif graph_type == "scatter":
        fig.add_trace(go.Scatter(
            x=df[col_x], y=df[col_y],
            mode='markers',
            name='Receita',
            marker=dict(color=color_map, size=10)
        ))
    else:
        raise ValueError(f"Tipo de gráfico '{graph_type}' não suportado. Use: bar, line, gauge, scatter.")

    # Configurações adicionais
    fig.update_layout(
        title=title,
        xaxis_title=col_x,
        yaxis_title=col_y,
        template="plotly_white"
    )

    # Guardar no estado do Streamlit
    st.session_state["last_fig"] = fig
    st.success(f"✅ Gráfico gerado com sucesso usando o arquivo: {df_path}")

    return fig


def save_df(data: Dict, file_path: Union[str, Path] = "spreadsheet_data.csv") -> Path:
    """
    Salva dados de um dicionário em um DataFrame Pandas e exporta para CSV.

    Parameters
    ----------
    data : dict
        Dicionário contendo os dados. As chaves devem ser nomes de colunas.
    file_path : str | Path, default="spreadsheet_data.csv"
        Caminho onde o arquivo CSV será salvo.

    Returns
    -------
    Path
        Caminho do arquivo salvo.
    """

    if not isinstance(data, dict):
        raise TypeError("Os dados devem ser fornecidos como um dicionário.")

    df = pd.DataFrame.from_dict(data)

    file_path = Path(file_path)
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        raise IOError(f"Erro ao salvar o DataFrame em '{file_path}': {e}")

    st.success(f"✅ DataFrame salvo com sucesso em: {file_path}")
    return file_path


    
# ==================== Fim do código =========================
