# 🤖 Gerador de Conteúdo
**O Gerador de Conteúdo é uma aplicação interativa desenvolvida em Python com Streamlit que utiliza LangChain e modelos da Groq para criar textos otimizados para SEO, copywriting persuasivo e engajamento em redes sociais.**
**O projeto foi pensado para profissionais de marketing digital, criadores de conteúdo e empreendedores que desejam gerar textos originais, criativos e prontos para publicação em diferentes plataformas.**

## 🚀 Funcionalidades
*- Geração de conteúdo otimizado para SEO.*
*- Ajuste automático de tom de voz (informal, profissional, inspirador, etc).*
*- Personalização por plataforma (LinkedIn, Instagram, Facebook, Blog, X/Twitter).*
*- Inclusão de palavras-chave, hashtags, emojis e CTAs.*
*- Opção de evitar termos indesejados.*
*- Interface simples e intuitiva via Streamlit.*

🛠️ Tecnologias Utilizadas
- Python 3.10+
- Streamlit
- LangChain
- Groq API


## 📂 Estrutura do Projeto
Gerador_de_Conteudo/
│
├── functions_and_documents/
│   └── Gerador_de_Conteudo/
│       └── functions.py            # Função load_llm para interação com LLM
│
├── 02_🧲_Gerador_de_Conteudo.py    # Arquivo principal Streamlit
├── .env                            # Configurações de chave da Groq API
├── pyproject.toml                  # Dependências do projeto
└── README.md                       # Documentação 



🧩 Como Funciona
- O usuário define parâmetros no sidebar:
- Tema
- Palavras-chave
- Palavras a evitar
- Plataforma
- Tamanho do texto
- Tom da mensagem
- Público-alvo
- CTA (Call to Action)
- Opções adicionais (analogias, hashtags, emojis)
- O sistema monta um prompt estruturado com base nas escolhas.
- O prompt é enviado para o modelo da Groq via função load_llm.
- O resultado é exibido diretamente na interface Streamlit.

📜 Exemplo de Uso
Entrada:
- Tema: Alimentação Saudável
- Plataforma: Instagram
- Tom: Inspirador
- Público-alvo: Jovens adultos
- CTA: Saiba mais no link da bio
- Opções: Hashtags + Emojis
Saída:
🍎 Descubra como pequenas escolhas podem transformar sua saúde!  
Troque o refrigerante por água, inclua frutas no seu dia e sinta a diferença.  
A jornada para uma vida saudável começa com um passo simples.  
✨ Saiba mais no link da bio!  
#Saúde #BemEstar #VidaSaudável



📌 Roadmap Futuro
- [ ] Exportar conteúdo diretamente para arquivos .txt ou .docx.
- [ ] Suporte a múltiplos idiomas.
- [ ] Integração com agendamento de posts em redes sociais.
- [ ] Ajuste automático de tamanho conforme plataforma.

🤝 Contribuição
Contribuições são bem-vindas!
Faça um fork, crie uma branch e envie um pull request.

📄 Licença
Este projeto está sob a licença MIT.
Sinta-se livre para usar, modificar e distribuir.

