# 🎮 Projeto RAG - Auto-Atendimento PS5
**O Projeto RAG - Auto-Atendimento PS5 é uma aplicação baseada em Streamlit que utiliza técnicas de Retrieval-Augmented Generation (RAG) para oferecer 
um assistente virtual inteligente capaz de responder dúvidas sobre qualquer empresa, manual de instrução ou conteúdo em formato PDF.**
**Para esse exemplo foi escolhido o manual do console PlayStation 5 --> https://www.playstation.com/content/dam/global_pdc/pt-br/corporate/support/manuals/ps5-docs/2100ab/CFI-21XX_PS5_Instruction_Manual_Web$pt-br.pdf**
**Esse sistema RAG combina modelos de linguagem (LLMs) com os documentos técnicos e manuais oficiais do console, permitindo que os usuários tenham acesso rápido e contextualizado às informações importantes em poucos segundos.**

## 🚀 Objetivo
O projeto foi desenvolvido para simular um chat de autoatendimento que auxilia usuários em questões comuns, como:
*- Configurações do console*
*- Solução de problemas técnicos*
*- Funcionalidades e recursos*
*- Dúvidas sobre jogos e compatibilidade*
*- Links e canais de contato da empresa*

🧩 Principais Componentes
1). Interface Streamlit
- Layout simples e intuitivo.
- Sidebar com informações e botão para iniciar atendimento.
- Campo de entrada para mensagens no estilo chat.
- Histórico de conversas exibido em formato de mensagens (usuário e assistente).

2). Carregamento da LLM
- Utiliza o modelo openai/gpt-oss-20b via LangChain Groq.
- Configuração com temperatura ajustada para respostas equilibradas e consistentes.

3). Processamento de Documentos
- Extração de textos de PDFs com PyMuPDFLoader.
- Divisão em chunks com RecursiveCharacterTextSplitter.
- Criação de embeddings com OpenAI ou HuggingFace.
- Indexação vetorial em Qdrant (com fallback para FAISS).

4). Retriever
- Recupera trechos relevantes dos documentos.
- Configurado com busca MMR (Maximal Marginal Relevance) para maior diversidade de contexto.

5). RAG Chain
- Reformulação de perguntas com histórico de conversa.
- Recuperação de contexto relevante.
- Geração de resposta final com base nos documentos e no modelo de linguagem.
- Respostas sempre em Português, concisas e úteis.

6). Chat Interativo
- Histórico de mensagens disponibilizado para o modelo, para contextualização eficiente.
- Respostas geradas dinamicamente com base no contexto dos manuais.

📜 Fluxo de Funcionamento
- Usuário acessa a interface e clica em Iniciar atendimento.
- O sistema carrega os manuais do PS5 e cria o índice vetorial.
- Usuário envia uma pergunta no campo de chat.
- O sistema:
- Reformula a pergunta considerando o histórico -- se necessário.
- Recupera trechos relevantes dos documentos através de busca vetorial.
- Gera uma resposta contextualizada via LLM.
- A resposta é exibida no chat e adicionada ao histórico.

📌 Exemplos de Uso
Entrada:
Como configuro o controle DualSense no PS5?


Saída esperada:
Para configurar o controle DualSense no PS5:
1. Conecte o controle ao console usando o cabo USB.
2. Pressione o botão PS para sincronizar.
3. Após a sincronização, o controle pode ser usado sem fio via Bluetooth.



🔎 Destaques do Projeto
- Integração de LLM + RAG para respostas precisas.
- Uso de Qdrant como banco vetorial para indexação dos manuais e recuperação eficiente.
- Suporte a diferentes modelos de embeddings (OpenAI e HuggingFace) -- de acordo com a necessidade.
- Respostas contextualizadas e adaptadas ao histórico da conversa.
- Interface amigável e prática para usuários finais não-técnicos.

📌 Roadmap Futuro
- [ ] Expansão para outros casos (empresas, documentações extensas)
- [ ] Suporte multilíngue.
- [ ] Exportação de histórico de atendimento.
