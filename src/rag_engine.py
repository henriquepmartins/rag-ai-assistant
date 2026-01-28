"""Motor RAG - orquestra busca vetorial + LLM."""

import logging
from typing import List, Dict, Any, Optional, Generator

from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    LLMMetadata,
    ChatMessage,
    ChatResponse,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from openai import OpenAI as OpenAIClient

from src.config import Config
from src.vector_store import VectorStoreManager
from src.memory import SessionMemory
from src.query_router import QueryRouter

logger = logging.getLogger(__name__)


class OpenRouterLLM(CustomLLM):
    """Adaptador para usar OpenRouter com LlamaIndex."""

    _client: Any = None
    _model: str = ""

    def __init__(self):
        super().__init__()
        self._client = OpenAIClient(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
        )
        self._model = Config.MODEL_NAME

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=128000,
            num_output=2000,
            model_name=self._model,
            is_chat_model=True,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            extra_headers={
                "HTTP-Referer": "https://emvidros.com.br",
                "X-Title": "EM Vidros AI Assistant",
            },
        )
        return CompletionResponse(text=response.choices[0].message.content)

    @llm_completion_callback()
    def stream_complete(
        self, prompt: str, **kwargs
    ) -> Generator[CompletionResponse, None, None]:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            stream=True,
            extra_headers={
                "HTTP-Referer": "https://emvidros.com.br",
                "X-Title": "EM Vidros AI Assistant",
            },
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield CompletionResponse(text=chunk.choices[0].delta.content)

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        openai_messages = []
        for msg in messages:
            role = "user"
            if hasattr(msg.role, "value"):
                role = msg.role.value
            else:
                role = str(msg.role)

            if role == "user":
                openai_role = "user"
            elif role == "assistant":
                openai_role = "assistant"
            elif role == "system":
                openai_role = "system"
            else:
                openai_role = "user"

            openai_messages.append({"role": openai_role, "content": msg.content})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            temperature=0.7,
            max_tokens=2000,
            extra_headers={
                "HTTP-Referer": "https://emvidros.com.br",
                "X-Title": "EM Vidros AI Assistant",
            },
        )

        assistant_message = ChatMessage(
            role="assistant", content=response.choices[0].message.content
        )
        return ChatResponse(message=assistant_message)


class RAGEngine:
    """Orquestra o pipeline completo de RAG."""

    SYSTEM_PROMPT = """Você é um assistente virtual inteligente da EM Vidros, uma empresa especializada em vidros e espelhos.

MISSÃO:
- Responder perguntas sobre produtos, serviços e informações da EM Vidros
- Ser prestativo, cordial e profissional
- Fornecer informações precisas baseadas no contexto disponível

REGRAS:
1. Responda APENAS com base nas informações fornecidas no contexto
2. Se não souber a resposta, diga honestamente que não tem essa informação
3. Não invente informações sobre preços, produtos ou serviços
4. Mantenha um tom profissional e amigável
5. Responda em português do Brasil
6. Seja conciso mas completo nas respostas

CONTEXTO:
EM Vidros é uma empresa do ramo de vidraçaria, oferecendo produtos e serviços relacionados a vidros e espelhos.
"""

    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.session_memory = SessionMemory()
        self.query_router = QueryRouter()
        self.llm = OpenRouterLLM()

    def _build_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Converte histórico do SQLite para formato LlamaIndex."""
        messages = self.session_memory.get_chat_history(session_id)
        chat_history = []

        for msg in messages:
            if msg["role"] == "user":
                chat_history.append(ChatMessage(role="user", content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(
                    ChatMessage(role="assistant", content=msg["content"])
                )

        return chat_history

    def chat(
        self,
        message: str,
        session_id: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> Dict[str, Any]:
        """Processa mensagem do usuário e retorna resposta."""
        try:
            # Cria sessão se não existir
            if not self.session_memory.get_session(session_id):
                self.session_memory.create_session(session_id)

            # Salva mensagem do usuário
            self.session_memory.add_message(session_id, "user", message)

            # Verifica se deve ir para suporte
            routed_response = self.query_router.route(message)
            if routed_response:
                self.session_memory.add_message(
                    session_id, "assistant", routed_response["response"]
                )
                return {
                    **routed_response,
                    "session_id": session_id,
                    "sources": [],
                }

            # Recupera histórico se não fornecido
            if chat_history is None:
                chat_history = self._build_chat_history(session_id)

            # Configura memória do chat
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=4000,
                chat_history=chat_history,
            )

            # Cria engine de chat com contexto
            chat_engine = CondensePlusContextChatEngine.from_defaults(
                retriever=self.vector_store.index.as_retriever(similarity_top_k=5),
                memory=memory,
                llm=self.llm,
                system_prompt=self.SYSTEM_PROMPT,
                verbose=False,
            )

            # Obtém resposta
            response = chat_engine.chat(message)

            # Extrai fontes usadas
            source_nodes = []
            if hasattr(response, "source_nodes") and response.source_nodes:
                for node in response.source_nodes:
                    source_nodes.append({
                        "text": (
                            node.node.text[:500]
                            if len(node.node.text) > 500
                            else node.node.text
                        ),
                        "score": node.score,
                        "metadata": node.node.metadata,
                    })

            response_text = str(response)

            # Salva resposta do assistente
            self.session_memory.add_message(
                session_id,
                "assistant",
                response_text,
                metadata={"sources": source_nodes} if source_nodes else None,
            )

            return {
                "response": response_text,
                "session_id": session_id,
                "sources": source_nodes,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "session_id": session_id,
                "sources": [],
                "success": False,
                "error": str(e),
            }

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Consulta simples sem histórico de chat."""
        try:
            # Verifica roteamento
            routed_response = self.query_router.route(question)
            if routed_response:
                return routed_response

            # Busca documentos relevantes
            results = self.vector_store.search(question, top_k=top_k)

            if not results:
                return {
                    "response": "Não encontrei informações relevantes sobre isso nos nossos documentos.",
                    "sources": [],
                    "success": True,
                }

            # Monta contexto
            context = "\n\n".join(
                [
                    f"[Fonte: {r['metadata'].get('title', 'Documento')} - {r['metadata'].get('url', '')}]\n{r['text']}"
                    for r in results
                ]
            )

            # Gera resposta
            prompt = f"""Com base nas seguintes informações, responda à pergunta:

CONTEXTO:
{context}

PERGUNTA: {question}

Responda de forma clara e objetiva em português:"""

            response = self.llm.complete(prompt)

            return {
                "response": response.text,
                "sources": results,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua pergunta.",
                "sources": [],
                "success": False,
                "error": str(e),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do engine."""
        return {
            "vector_store": self.vector_store.get_stats(),
            "model": Config.MODEL_NAME,
        }
