# EM Vidros AI Assistant 🤖

Assistente virtual inteligente e production-ready para a EM Vidros, utilizando RAG (Retrieval-Augmented Generation) com LlamaIndex, vector database Qdrant, e memória de sessão SQLite.

## 🌟 Funcionalidades

- **🧠 RAG Inteligente**: Responde perguntas baseadas no conteúdo do site da EM Vidros e documentos de contexto
- **📁 Contexto Personalizado**: Adicione PDFs, DOCX, TXT e MD na pasta `context/` para enriquecer a base de conhecimento
- **🚚 Roteamento de Suporte**: Perguntas sobre entrega são automaticamente direcionadas ao suporte
- **💬 Memória de Sessão**: Lembra conversas anteriores usando SQLite
- **🔍 Vector Search**: Busca semântica com embeddings via OpenRouter
- **⚡ Processamento Assíncrono**: Inngest para jobs de scraping e ingestão
- **🎨 Interface Amigável**: Frontend Streamlit com design responsivo
- **🔌 API REST**: FastAPI para integrações

## 🏗️ Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Streamlit UI   │────▶│   FastAPI API   │────▶│  RAG Engine     │
│  (Frontend)     │     │   (Backend)     │     │  (LlamaIndex)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────┐
                              │                          │          │
                              ▼                          ▼          ▼
                    ┌─────────────────┐        ┌─────────────────┐  ┌─────────────────┐
                    │  Qdrant Vector  │        │  SQLite Memory  │  │  OpenRouter     │
                    │     Store       │        │    (Sessions)   │  │    (LLM)        │
                    └─────────────────┘        └─────────────────┘  └─────────────────┘
                              ▲
                              │
                    ┌─────────┴─────────┐
                    │  Context Folder   │
                    │  (PDF, DOCX, TXT) │
                    └───────────────────┘
```

## 📁 Estrutura do Projeto

```
em-vidros-ai-assistant/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configurações e variáveis de ambiente
│   ├── document_loader.py     # Carregador de documentos (PDF, DOCX, etc.)
│   ├── query_router.py        # Roteamento de queries (suporte vs RAG)
│   ├── scraper.py             # Web scraper para o site EM Vidros
│   ├── vector_store.py        # Integração Qdrant + LlamaIndex
│   ├── memory.py              # SQLite session storage
│   ├── rag_engine.py          # Motor RAG principal
│   └── inngest_functions.py   # Funções Inngest para background jobs
├── scripts/
│   ├── __init__.py
│   └── scrape_and_ingest.py   # Script manual de scraping
├── context/                   # Pasta para documentos personalizados
│   └── README.md
├── .streamlit/
│   └── secrets.toml.template  # Template para secrets do Streamlit
├── api.py                     # FastAPI application
├── streamlit_app.py           # Streamlit frontend
├── pyproject.toml             # Dependências do projeto
├── .env                       # Variáveis de ambiente (não commitar)
├── .gitignore                 # Arquivos ignorados pelo Git
└── README.md                  # Este arquivo
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes)
- Qdrant (vector database)

### 1. Clone e instale dependências

```bash
# Clone o repositório
git clone https://github.com/henriquepmartins/em-vidros-ai-assistant.git
cd em-vidros-ai-assistant

# Instalar dependências
uv sync

# Ativar ambiente virtual
source .venv/bin/activate
```

### 2. Configure as variáveis de ambiente

Crie o arquivo `.env`:

```env
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1/
MODEL_NAME=google/gemini-2.0-flash-exp:free

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=emvidros_docs
VECTOR_DIMENSION=3072

# SQLite Database
SQLITE_DB_PATH=./data/sessions.db

# Website Settings
WEBSITE_URL=https://emvidros.com.br
MAX_PAGES=100
SCRAPE_DELAY=1.0

# Inngest
INNGEST_APP_ID=rag_app
```

### 3. Inicie o Qdrant

```bash
# Usando Docker
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 4. Execute o scraping inicial

```bash
# Scraping do site
python scripts/scrape_and_ingest.py --max-pages 50

# Ou carregue documentos na pasta context/
# Eles serão indexados automaticamente na inicialização
```

## 🖥️ Uso

### Iniciar a API (FastAPI)

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

- Documentação: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Iniciar o Frontend (Streamlit)

```bash
streamlit run streamlit_app.py
```

O frontend estará disponível em: http://localhost:8501

## 📁 Pasta de Contexto

Adicione documentos à pasta `context/` para enriquecer a base de conhecimento:

- **PDF** (.pdf) - Catálogos, manuais, documentos técnicos
- **Word** (.docx, .doc) - Documentos comerciais
- **Texto** (.txt) - Notas, instruções
- **Markdown** (.md) - Documentação estruturada

Os arquivos são automaticamente indexados na inicialização da API.

## 🚚 Suporte e Entregas

Perguntas sobre status de entrega, rastreamento e pedidos são automaticamente direcionadas ao suporte:

📧 **suporte@emvidros.com.br**

Exemplos de queries que acionam o suporte:

- "Meu produto já saiu para entrega?"
- "Quanto tempo vai demorar?"
- "Onde está meu pedido?"
- "Status da entrega"

## 📡 API Endpoints

| Método | Endpoint          | Descrição                   |
| ------ | ----------------- | --------------------------- |
| GET    | `/`               | Info da API                 |
| GET    | `/health`         | Health check                |
| POST   | `/chat`           | Chat com o assistente       |
| POST   | `/query`          | Query simples (sem memória) |
| GET    | `/sessions`       | Listar sessões              |
| GET    | `/sessions/{id}`  | Detalhes da sessão          |
| DELETE | `/sessions/{id}`  | Deletar sessão              |
| GET    | `/stats`          | Estatísticas do sistema     |
| POST   | `/scrape`         | Trigger scraping            |
| POST   | `/reload-context` | Recarregar documentos       |

### Exemplo de uso da API

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais produtos vocês vendem?"}'

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Horário de funcionamento"}'
```

## 🚀 Deploy no Streamlit Cloud

### 1. Preparar o repositório

```bash
# Certifique-se de que todos os arquivos estão commitados
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Configurar Secrets

No Streamlit Cloud, vá em **Settings > Secrets** e adicione:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENAI_BASE_URL = "https://openrouter.ai/api/v1/"
MODEL_NAME = "google/gemini-2.0-flash-exp:free"
QDRANT_URL = "https://your-qdrant-cloud-url.cloud.qdrant.io:6333"
QDRANT_COLLECTION = "emvidros_docs"
VECTOR_DIMENSION = "3072"
SQLITE_DB_PATH = "/tmp/sessions.db"
WEBSITE_URL = "https://emvidros.com.br"
MAX_PAGES = "100"
SCRAPE_DELAY = "1.0"
INNGEST_APP_ID = "rag_app"
```

> **Nota**: Para deploy, use Qdrant Cloud ou outro serviço de hospedagem Qdrant.

### 3. Deploy

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte sua conta GitHub
3. Selecione o repositório `em-vidros-ai-assistant`
4. O deploy será feito automaticamente

## 🔧 Comandos Úteis

```bash
# Scraping manual
python scripts/scrape_and_ingest.py --url https://emvidros.com.br --max-pages 50

# Limpar e reindexar
python scripts/scrape_and_ingest.py --clear

# Verificar estatísticas
curl http://localhost:8000/stats

# Listar sessões
curl http://localhost:8000/sessions

# Recarregar documentos de contexto
curl -X POST http://localhost:8000/reload-context
```

## 🧪 Desenvolvimento

### Linting

```bash
ruff check .
ruff format .
```

### Testes

```bash
pytest
```

## 📝 Configurações Avançadas

### Modelos LLM Suportados (via OpenRouter)

- `google/gemini-2.0-flash-exp:free` (padrão - gratuito)
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `meta-llama/llama-3.1-8b-instruct:free`

Altere no `.env`:

```env
MODEL_NAME=anthropic/claude-3.5-sonnet
```

### Ajustar Memória de Sessão

```env
MAX_CHAT_HISTORY=20  # Número de mensagens mantidas
```

### Configurações de Scraping

```env
MAX_PAGES=200        # Máximo de páginas
SCRAPE_DELAY=2.0     # Delay entre requests (segundos)
```

## 🐛 Troubleshooting

### Erro de conexão com Qdrant

```bash
# Verifique se o Qdrant está rodando
curl http://localhost:6333/collections
```

### Erro de API Key

```bash
# Verifique se a chave está configurada
echo $OPENROUTER_API_KEY
```

### Erro de módulos não encontrados

```bash
# Reinstale as dependências
uv sync --reinstall
```

## 🤝 Suporte

Para suporte técnico ou dúvidas sobre o assistente:

📧 **suporte@emvidros.com.br**

## 📄 Licença

Este projeto é proprietário da EM Vidros.

---

Desenvolvido com ❤️ para EM Vidros
