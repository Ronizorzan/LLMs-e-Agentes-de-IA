# 🚀 Projetos com LLMs

Este portfólio reúne projetos que utilizam **Modelos de Linguagem (LLMs)** para resolver diferentes problemas de negócio.  
O repositório está em constante evolução: novas funções e páginas serão adicionadas gradualmente.

Cada arquivo representa uma solução prática para desafios comuns enfrentados por empresas.  
Os projetos foram desenvolvidos para serem **facilmente adaptáveis** a diferentes contextos, bastando ajustes simples em lógicas, prompts e dados.

---

## 📂 Estrutura do Repositório

### [`functions_and_documents`](functions_and_documents)
Contém funções auxiliares e documentos adicionais, organizados por projeto para garantir controle e clareza.

- [`functions_and_documents/Gerador_de_Conteudo/functions.py`](functions_and_documents/Gerador_de_Conteudo/functions.py)  
  Funções utilizadas no projeto de **geração de conteúdo**.

- [`functions_and_documents/ProjetoRAG/functions.py`](functions_and_documents/ProjetoRAG/functions.py)  
  Funções utilizadas no projeto **RAG (Retrieval-Augmented Generation)**.

---

### [`Projects`](Projects)
Projetos prontos para execução via arquivos `.py`.

#### 1) [RAGProject.py](01_💬_Projeto_RAG.py)
**Projeto principal – Autoatendimento Personalizado com RAG**  
- Modelo que responde a perguntas e dúvidas de clientes com base em documentos da empresa.  
- Respostas rápidas e contextualizadas a partir de PDFs.  
- Estudo de caso: manual do **PlayStation 5**.  
- [📖 Manual do Console aqui](https://www.playstation.com/content/dam/global_pdc/pt-br/corporate/support/manuals/ps5-docs/2100ab/CFI-21XX_PS5_Instruction_Manual_Web$pt-br.pdf)
  
  ![Interface_Chat_RAG](functions_and_documents\Interface_Streamlit\Interface_Chat_RAG.gif)

---

#### 2) [MarketingProject.py](02_🧲_Gerador_de_Conteudo.py)
**Geração de Conteúdo Dinâmico para Marketing**  
- Criação de conteúdos personalizados para redes sociais (Facebook, LinkedIn, Instagram, etc).  
- Interface simples para engenharia de prompts sem necessidade de conhecimento técnico.  
- Possibilidade de configurar: tópico, público-alvo, tamanho do texto, CTA, emojis e muito mais.  
- Resultado: **conteúdo para aumentar engajamento pronto em segundos.**

---

#### 3)[Education](03_👨‍🎓_Gerador_de_Exercicios.py)
**Geração de Exercícios para professores**
- Criação de exercícios personalizados para estudantes de diversas áreas.
- Interface pronta para e altamente personalizável com possibilidade de exportações de documentos.
- Possibilidade de configurar: nível, matéria, quantidade de exercícios, interesses, etc
- Resultado: **Exercícios personalizados baseados em documentos recuperados através de técnicas RAG.** 

## ✨ Diferenciais
- Projetos modulares e reutilizáveis.  
- Fácil adaptação para diferentes setores e empresas.  
- Documentação clara e organizada.  
- Foco em aplicações reais de LLMs.

---

## 📌 Status
🔧 Em desenvolvimento contínuo – novas funcionalidades e projetos serão adicionados regularmente.