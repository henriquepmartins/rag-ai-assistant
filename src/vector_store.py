"""Integração com Qdrant via LlamaIndex."""

import logging
from typing import List, Dict, Any, Optional

from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import QdrantClient

from src.config import Config

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Gerencia armazenamento e busca vetorial."""

    def __init__(self):
        self.client = QdrantClient(url=Config.QDRANT_URL, timeout=30)
        self.embed_model = OpenAIEmbedding(
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENAI_BASE_URL,
            model="text-embedding-3-large",
        )

        # Garante que coleção existe
        self._ensure_collection()

        # Inicializa vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=Config.QDRANT_COLLECTION,
        )

        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        self._index = None

    def _ensure_collection(self):
        """Cria coleção se não existir."""
        try:
            from qdrant_client.models import VectorParams, Distance

            if not self.client.collection_exists(Config.QDRANT_COLLECTION):
                logger.info(f"Creating collection: {Config.QDRANT_COLLECTION}")
                self.client.create_collection(
                    collection_name=Config.QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=Config.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    ),
                )
                logger.info(f"Collection created successfully")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")

    @property
    def index(self) -> VectorStoreIndex:
        """Retorna ou cria índice vetorial."""
        if self._index is None:
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )
        return self._index

    def add_documents(self, documents: List[Document]) -> int:
        """Adiciona documentos ao banco vetorial."""
        try:
            for doc in documents:
                self.index.insert(doc)
            logger.info(f"Added {len(documents)} documents to vector store")
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return 0

    def add_web_content(self, scraped_content: List[Dict[str, Any]]) -> int:
        """Converte conteúdo web em documentos e adiciona."""
        documents = []

        for item in scraped_content:
            content = item.get("content", "")
            if not content or len(content) < 50:
                continue

            doc = Document(
                text=content,
                metadata={
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "source": "website",
                    "content_length": item.get("content_length", 0),
                }
            )
            documents.append(doc)

        if documents:
            return self.add_documents(documents)
        return 0

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Busca documentos relevantes."""
        try:
            # Constrói filtros se fornecidos
            llama_filters = None
            if filters:
                match_filters = [
                    ExactMatchFilter(key=k, value=v)
                    for k, v in filters.items()
                ]
                llama_filters = MetadataFilters(filters=match_filters)

            # Cria retriever
            retriever = self.index.as_retriever(
                similarity_top_k=top_k,
                filters=llama_filters,
            )

            # Recupera nós
            nodes = retriever.retrieve(query)

            results = []
            for node in nodes:
                results.append({
                    "text": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata,
                })

            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco."""
        try:
            collection_info = self.client.get_collection(Config.QDRANT_COLLECTION)
            stats = {"collection": Config.QDRANT_COLLECTION}

            # Tenta diferentes atributos para compatibilidade
            if hasattr(collection_info, 'vectors_count'):
                stats["vectors_count"] = collection_info.vectors_count
            if hasattr(collection_info, 'points_count'):
                stats["points_count"] = collection_info.points_count
            elif hasattr(collection_info, 'config'):
                stats["points_count"] = collection_info.points_count if hasattr(collection_info, 'points_count') else 0

            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"collection": Config.QDRANT_COLLECTION, "points_count": 0}

    def clear_collection(self) -> bool:
        """Remove todos os documentos da coleção."""
        try:
            self.client.delete_collection(Config.QDRANT_COLLECTION)
            self.client.create_collection(
                collection_name=Config.QDRANT_COLLECTION,
                vectors_config={
                    "size": Config.VECTOR_DIMENSION,
                    "distance": "Cosine"
                }
            )
            self._index = None
            logger.info("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def check_collection_exists(self) -> bool:
        """Verifica se coleção existe."""
        try:
            return self.client.collection_exists(Config.QDRANT_COLLECTION)
        except Exception:
            return False
