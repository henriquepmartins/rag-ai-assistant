# EM Vidros AI Assistant

Assistente conversacional baseado em RAG para a EM Vidros. Desenvolvido com Python, LlamaIndex e Qdrant.

## Arquitetura

```
Streamlit UI → FastAPI → RAG Engine (LlamaIndex)
                      ↓
        Qdrant (vetores) + SQLite (sessões) + OpenRouter (LLM)
```

**Componentes Principais**

- **RAG Engine**: LlamaIndex com CondensePlusContextChatEngine para respostas contextuais
- **Vector Store**: Qdrant para busca semântica com embeddings OpenAI
- **Memória**: SQLite para persistência de sessões
- **LLM**: API OpenRouter (modelo configurável)
- **Web Scraping**: Crawler assíncrono para ingestão de conteúdo do site

## Início Rápido

**Pré-requisitos**: Python 3.11+, [uv](https://github.com/astral-sh/uv), Qdrant

```bash
# Instalação
uv sync

# Configuração
cp .env.example .env
# Edite .env com sua OPENROUTER_API_KEY

# Iniciar Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Executar API
uv run uvicorn api:app --reload

# Executar UI (novo terminal)
uv run streamlit run streamlit_app.py
```

## Configuração

Variáveis de ambiente no `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_NAME=google/gemini-2.0-flash-exp:free
QDRANT_URL=http://localhost:6333
```

## API

| Método | Endpoint  | Descrição                           |
| ------ | --------- | ----------------------------------- |
| POST   | `/chat`   | Endpoint conversacional com memória |
| POST   | `/query`  | Consulta pontual sem histórico      |
| GET    | `/health` | Verificação de saúde                |
| GET    | `/stats`  | Estatísticas do sistema             |

## Documentos de Contexto

Adicione arquivos na pasta `context/` (PDF, DOCX, TXT, MD). Indexados automaticamente na inicialização.

## Estrutura do Projeto

```
src/
  config.py            # Configuração de ambiente
  rag_engine.py        # Lógica RAG principal
  vector_store.py      # Integração com Qdrant
  memory.py            # Armazenamento de sessões SQLite
  query_router.py      # Detecção de intenção
  scraper.py           # Crawler web
  document_loader.py   # Ingestão de arquivos
  inngest_functions.py # Jobs em background
api.py                 # Aplicação FastAPI
streamlit_app.py       # Interface web
```

## Roteamento de Suporte

Consultas sobre status de entrega são direcionadas automaticamente ao suporte humano:

```
suporte@emvidros.com.br
```

## Licença

Proprietário - EM Vidros
