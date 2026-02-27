# =================== Visualização ===========================
import plotly.graph_objects as go
import plotly.io as pio

# =============== Manipulação de dados e Variáveis ====================
import json
import streamlit as st
import sys
import io
import re
from pathlib import Path
from typing import Union, Dict, List
import pandas as pd
import asyncio

# ======================= Bibliotecas Principais ======================
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from deep_translator import GoogleTranslator
from llama_index.core.agent.workflow import AgentStream, ToolCallResult


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
    Retorne o texto em linguagem natural e com caracteres que possuem em um teclado comum, sem caracteres ou símbolos LaTex, para serem exibidos em uma interface de usuário com markdown.
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

# ===================== Detecção automática de Coluna com data =======================

# Regex para formatos comuns de data
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})$")

def looks_like_date(value):
    pattern = r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}$'
    return bool(re.match(pattern, str(value)))


def is_date_column(series, threshold=0.9):
    matches = series.astype(str).apply(lambda x: bool(date_pattern.match(x)))
    return matches.mean() >= threshold

# ==================== Execução do agente (Melhorado o Log) =========================

async def run_agent(query, timeout=30):
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    logs = ""

    try:
        handler = st.session_state.agent.run(query, early_stopping_method="generate")

        # Captura de eventos para mostrar "pensamento" do Agente
        async for event in handler.stream_events():
            if isinstance(event, ToolCallResult):
                sys.stdout.write(f"\n🛠️ **Usou ferramenta:** {event.tool_name}\n")
                sys.stdout.write(f"   ARGS: {event.tool_kwargs}\n")
                sys.stdout.write(f"   RETORNO: {str(event.tool_output)[:200]}...\n")
            elif isinstance(event, AgentStream):
                pass

        # Aqui usamos asyncio.wait_for em vez de signal
        response = await asyncio.wait_for(handler, timeout=timeout)
        formatted_response = str(response.response)

    except asyncio.TimeoutError:
        formatted_response = "⏱️ Tempo limite atingido, consulta cancelada."
        sys.stdout.write("\nERRO CRÍTICO: Timeout\n")

    except Exception as e:
        formatted_response = f"Ocorreu um erro durante o processamento: {str(e)}"
        sys.stdout.write(f"\nERRO CRÍTICO: {str(e)}\n")

    finally:
        sys.stdout = old_stdout

    logs = mystdout.getvalue()
    return formatted_response, logs

# ==================== Função para salvar arquivo JSON (CORRIGIDA) =====================
def save_json(data: Union[Dict, List[Dict]], file_path: Union[str, Path] = "financial_data.json") -> str:
    """
    Salva dados extraídos (dict ou lista de dicts) em um arquivo JSON.
    OBRIGATÓRIO: Esta função deve ser chamada ANTES de gerar gráficos.
    
    Parameters
    ----------
    data : Dict | List[Dict]
        Os dados a serem salvos. O Agente deve garantir que isso seja um JSON válido.
    file_path : str
        Nome do arquivo.
    """
    path_obj = Path(file_path)
    if path_obj.suffix != ".json":
        path_obj = path_obj.with_suffix(".json")
    
    try:        
        with open(path_obj, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as error:
        raise IOError(f"Erro ao salvar JSON: {str(error)}")
    
    # Removido st.toast daqui para evitar erros de thread, o agente retorna a string
    return str(path_obj)


# ==================== Função para geração dos Gráficos (Robusta) ====================
def generate_graphs(
    json_path: Union[str, Path],
    col_x: str,
    col_y: str = "revenue",
    graph_type: str = "bar",
    color_map: str = "#302DF1",
    title: str = "Resumo Financeiro"
):
    """
    Gera um gráfico interativo a partir de dados salvos em JSON.

    A função lê um arquivo JSON previamente salvo, converte em DataFrame
    e cria um gráfico com Plotly. É útil para visualizações rápidas
    e impactantes em relatórios ou dashboards.

    Parameters
    ----------
    json_path : str ou Path
        Caminho para o arquivo JSON salvo anteriormente.
    col_x : str
        Nome da coluna que será usada no eixo X.
    col_y : str, default="revenue"
        Nome da coluna que será usada no eixo Y.
    graph_type : {"bar", "line", "scatter", "gauge"}, default="bar"
        Tipo de gráfico desejado.
    color_map : str, default="#302DF1"
        Cor principal do gráfico (hexadecimal ou nome).
    title : str, default="Resumo Financeiro"
        Título exibido no gráfico.

    Returns
    -------
    str
        Mensagem de sucesso ou erro.
    """
    path_obj = Path(json_path)
    
    # 1. Tenta carregar o DataFrame
    if not path_obj.exists():
         path_obj = path_obj.with_suffix(".json")
         if not path_obj.exists():
            return "Erro: Arquivo JSON não encontrado. Você salvou os dados antes com save_json?"

    try:
        with open(path_obj, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normalização robusta: se for lista ou dict
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Tenta converter dict diretamente ou usa json_normalize
            df = pd.json_normalize(data)
        else:
            return "Erro: Formato de JSON desconhecido/inválido para gráfico."

    except Exception as e:
        return f"Erro ao ler JSON: {e}"

    # 2. Validação de Colunas (Case Insensitive para ajudar o Agente)
    df.columns = [c.strip() for c in df.columns] # Remove espaços extras
    
    if col_x not in df.columns or col_y not in df.columns:
        # Tenta achar colunas parecidas se o agente errou por pouco
        return f"Erro: Colunas '{col_x}' ou '{col_y}' não encontradas. Colunas disponíveis: {list(df.columns)}"

    fig = go.Figure()

    try:
        if graph_type == "bar":
            fig.add_trace(go.Bar(x=df[col_x], y=df[col_y], name=col_y, marker_color=color_map))
        elif graph_type == "line":
            fig.add_trace(go.Scatter(x=df[col_x], y=df[col_y], mode='lines+markers', line=dict(color=color_map)))
        elif graph_type == "scatter":
            fig.add_trace(go.Scatter(x=df[col_x], y=df[col_y], mode='markers', marker=dict(color=color_map, size=10)))
        elif graph_type == "gauge":
             fig.add_trace(go.Indicator(
                mode="gauge+number", value=df[col_y].iloc[-1],
                gauge={'axis': {'range': [None, df[col_y].max()*1.2]}, 'bar': {'color': color_map}}
            ))
        else:
            return f"Tipo de gráfico '{graph_type}' não suportado."

        
        # Estilização do Gráfico
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color=color_map)),
            xaxis_title=col_x,
            yaxis_title=col_y,
            template="plotly_white",
            hovermode="x unified",            
            xaxis=dict(showgrid=True, gridcolor="lightgrey"),
            yaxis=dict(showgrid=True, gridcolor="lightgrey")
        )
   
        
        # SALVAMENTO ESTÁTICO DO PLOTLY
        static_graph_path = "static_graph.json"
        pio.write_json(fig, static_graph_path) # Salva o Gráfico fisicamente
        st.toast(f"✅ Gráfico gerado com sucesso e salvo em: {static_graph_path}!")
        return "✅ Gráfico gerado com sucesso"


    except Exception as e:        
        return f"Erro ao plotar gráfico: {e}"
    
            
# ==================== Fim do código =========================
