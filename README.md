# ai assistant

assistente conversacional baseado em RAG para a EM Vidros. Desenvolvido com Python, LlamaIndex e Qdrant.

## arquitetura

```
streamlit ui → fastapi → rag engine (llamaindex)
                      ↓
        qdrant (vetores) + sqlite (sessões) + openrouter (llm)
```

**componentes principais**

- **rag engine**: llamaindex + condense context chat para respostas diretas
- **vetor store**: qdrant para busca semântica (embeddings openai por padrão)
- **memória**: sqlite para persistência de sessões
- **llm**: openrouter (modelo configurável)
- **scraper**: crawler assíncrono para ingestão de conteúdo


## instalação 

requisitos: python 3.11+, `uv`, qdrant

```bash
# instalar dependências
uv sync

# copiar e ajustar env
cp .env.example .env
# preencha OPENROUTER_API_KEY no .env

# iniciar qdrant
docker run -p 6333:6333 qdrant/qdrant

# executar api
uv run uvicorn api:app --reload

# executar ui (novo terminal)
uv run streamlit run streamlit_app.py
```

## configuração

defina no `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_NAME=google/gemini-2.0-flash-exp:free
QDRANT_URL=http://localhost:6333
```

## endpoints

- `POST /chat` — conversação com memória de sessão
- `POST /query` — consulta pontual (sem histórico)
- `GET /health` — checagem de saúde
- `GET /stats` — estatísticas do sistema

## documentos de contexto

adicione arquivos na pasta `context/` (pdf, docx, txt, md). indexados automaticamente na inicialização.

## estrutura do projeto

```
src/
  config.py            # configuração de ambiente
  rag_engine.py        # lógica principal do rag
  vector_store.py      # integração com qdrant
  memory.py            # armazenamento de sessões (sqlite)
  query_router.py      # roteamento / detecção de intenção
  scraper.py           # crawler web
  document_loader.py   # ingestão de arquivos
  inngest_functions.py # jobs em background
api.py                 # aplicação fastapi
streamlit_app.py       # interface streamlit
```
