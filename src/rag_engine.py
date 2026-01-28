"""RAG Engine for EM Vidros AI Assistant.

This module provides the core RAG functionality for answering questions
about EM Vidros using vector search and LLM generation.
"""

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
    """Custom LLM wrapper for OpenRouter API.

    This class wraps the OpenRouter API to work with LlamaIndex's
    CustomLLM interface, enabling chat completions with various models.
    """

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
        """Complete a prompt."""
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
        """Stream complete a prompt."""
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
        """Chat with messages."""
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
    """RAG Engine for answering questions about EM Vidros.

    This class orchestrates the RAG pipeline:
    1. Query routing (detect support queries)
    2. Vector search for relevant context
    3. LLM generation with context
    4. Session memory management
    """

    SYSTEM_PROMPT = """Você é um assistente virtual inteligente da EM Vidros, uma empresa especializada em vidros e espelhos.

SUA MISSÃO:
- Responder perguntas sobre produtos, serviços e informações da EM Vidros
- Ser prestativo, cordial e profissional
- Fornecer informações precisas baseadas no contexto disponível

REGRAS IMPORTANTES:
1. Responda APENAS com base nas informações fornecidas no contexto
2. Se não souber a resposta, diga honestamente que não tem essa informação
3. Não invente informações sobre preços, produtos ou serviços
4. Mantenha um tom profissional e amigável
5. Responda em português do Brasil
6. Seja conciso mas completo nas respostas

CONTEXTO DA EMPRESA:
EM Vidros é uma empresa do ramo de vidraçaria, oferecendo produtos e serviços relacionados a vidros e espelhos.
"""

    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.session_memory = SessionMemory()
        self.query_router = QueryRouter()
        self.llm = OpenRouterLLM()

    def _build_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Build chat history from session memory for LlamaIndex."""
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
        """Process a chat message and return a response.

        Args:
            message: User message
            session_id: Session identifier for memory
            chat_history: Optional pre-built chat history

        Returns:
            Dict with response, sources, and success status
        """
        try:
            # Ensure session exists
            if not self.session_memory.get_session(session_id):
                self.session_memory.create_session(session_id)

            # Store user message
            self.session_memory.add_message(session_id, "user", message)

            # Check if query should be routed to support
            routed_response = self.query_router.route(message)
            if routed_response:
                # Store support response
                self.session_memory.add_message(
                    session_id, "assistant", routed_response["response"]
                )
                return {
                    **routed_response,
                    "session_id": session_id,
                    "sources": [],
                }

            # Get chat history from memory if not provided
            if chat_history is None:
                chat_history = self._build_chat_history(session_id)

            # Create chat memory buffer
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=4000,
                chat_history=chat_history,
            )

            # Create chat engine with context retrieval
            chat_engine = CondensePlusContextChatEngine.from_defaults(
                retriever=self.vector_store.index.as_retriever(similarity_top_k=5),
                memory=memory,
                llm=self.llm,
                system_prompt=self.SYSTEM_PROMPT,
                verbose=False,
            )

            # Get response
            response = chat_engine.chat(message)

            # Extract source nodes for context
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

            # Store assistant response
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
        """Simple query without chat history.

        Args:
            question: Question to answer
            top_k: Number of sources to retrieve

        Returns:
            Dict with response, sources, and success status
        """
        try:
            # Check if query should be routed to support
            routed_response = self.query_router.route(question)
            if routed_response:
                return routed_response

            # Search for relevant context
            results = self.vector_store.search(question, top_k=top_k)

            if not results:
                return {
                    "response": "Não encontrei informações relevantes sobre isso nos nossos documentos.",
                    "sources": [],
                    "success": True,
                }

            # Build context from search results
            context = "\n\n".join(
                [
                    f"[Fonte: {r['metadata'].get('title', 'Documento')} - {r['metadata'].get('url', '')}]\n{r['text']}"
                    for r in results
                ]
            )

            # Create prompt with context
            prompt = f"""Com base nas seguintes informações, responda à pergunta:

CONTEXTO:
{context}

PERGUNTA: {question}

Responda de forma clara e objetiva em português:"""

            # Get response from LLM
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
        """Get engine statistics."""
        return {
            "vector_store": self.vector_store.get_stats(),
            "model": Config.MODEL_NAME,
        }
