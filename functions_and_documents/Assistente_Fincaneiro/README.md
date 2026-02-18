# 📊 Assistente Financeiro Inteligente com IA Generativa
Uma aplicação analítica autônoma que transforma relatórios financeiros (PDF) e planilhas brutas (CSV/Excel) em insights estratégicos e visualizações de dados interativas.

## 🚀 Sobre o Projeto
O Assistente Financeiro é uma solução de Business Intelligence impulsionada por Agentes de IA. Diferente de chatbots comuns, este sistema utiliza um Function Agent (LlamaIndex) capaz de orquestrar ferramentas para manipular dados, realizar cálculos matemáticos precisos via Pandas e gerar gráficos dinamicamente.O objetivo é reduzir o tempo de análise financeira de horas para segundos, fornecendo resumos executivos, identificação de riscos e visualização de tendências automaticamente.

### 📸 Galeria de Funcionalidades
1). **Análise de Planilhas e Geração de Gráficos**
- O agente entende a estrutura dos dados, decide qual o melhor gráfico para a visualização e o plota automaticamente.
2). **Processamento de Documentos (RAG) e Dashboards**
- Capacidade de ler relatórios em PDF não estruturados ou gerar tabelas resumo de grandes datasets.
3). **Resumo Executivo**
 Geração de Tabelas de Performance - Identificação e extração de riscos - Oportunidades Ocultas nos dados- Geração e Análise de KPIs financeiros

### ⚙️ Arquitetura e Como Funciona
O núcleo da aplicação é um Agente de Fluxo de Trabalho (Function Agent) que opera com um System Prompt rigoroso para garantir precisão financeira. O fluxo segue a lógica:

graph TD

    A[Usuário Faz Pergunta] --> B{Tipo de Arquivo?}
    B -- PDF --> C[RAG (Vector Store)]
    B -- CSV/XLSX --> D[Agente Pandas]
    
    D --> E{Decisão do Agente}
    E -- "Análise de Texto/Cálculo" --> F[PandasQueryEngine]
    E -- "Pedido de Gráfico" --> G[Extrair Dados]
    
    G --> H[Ferramenta: save_json] -- Salva os dados para plotagem
    H --> I[Ferramenta: generate_graphs] -- Lê o arquivo salvo anteriormente e gera o gráfico
    
    F --> J[Resposta Final]
    I --> J[Renderização Plotly + Explicação]

## Principais Componentes Técnicos
+ **Agente Orquestrador:** Decide quando usar busca semântica (textos) ou execução de código (cálculos/gráficos).
+ **Hybrid LLM Engine:** Suporte para Google Gemini 2.5 Flash (raciocínio rápido e visão) e Groq (Inferência de baixa latência) como fallback.
+ **Pandas Query Engine:** Transforma linguagem natural em código Python/Pandas para consultas à prova de alucinações em dados numéricos.
+ **Tratamento de Dados:** Detecção automática de delimitadores de CSV e conversão inteligente de formatos de data (difflib para matching difuso de colunas).

## 🛠️ Tecnologias Utilizadas

### Frontend:
> Streamlit (com Custom CSS e Layout em Abas dinâmicas para Interface mais amigável para o usuário final).
### Orquestração de IA:
> LlamaIndex (FunctionAgent, ToolMetadata).
### LLMs:
> Google GenAI (Gemini) e Groq (Llama 3/Mixtral, GPT-OSS).
### Manipulação de Dados:
> Pandas (para dados tabulares - DF e XLSX) & docling (para dados não estruturados - PDFs).
### Visualização:
> Plotly Express & Graph Objects.
### Tradução:
> DeepTranslator (Suporte a documentos PDF em Inglês).