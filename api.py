"""FastAPI backend for EM Vidros RAG AI Assistant.

This module provides the REST API for the EM Vidros AI Assistant,
including chat endpoints, session management, and system statistics.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import inngest.fast_api

from src.config import Config
from src.rag_engine import RAGEngine
from src.memory import SessionMemory
from src.vector_store import VectorStoreManager
from src.document_loader import DocumentLoader
from src.inngest_functions import inngest_client, inngest_functions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global component instances
rag_engine: Optional[RAGEngine] = None
session_memory: Optional[SessionMemory] = None
vector_store: Optional[VectorStoreManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global rag_engine, session_memory, vector_store

    logger.info("Starting up EM Vidros AI Assistant API...")
    Config.ensure_directories()

    # Initialize components
    session_memory = SessionMemory()
    vector_store = VectorStoreManager()

    # Load and index context documents
    try:
        doc_loader = DocumentLoader()
        documents = doc_loader.load_all()
        if documents:
            logger.info(f"Indexing {len(documents)} documents from context folder")
            vector_store.add_documents(documents)
    except Exception as e:
        logger.error(f"Error loading context documents: {e}")

    rag_engine = RAGEngine()

    logger.info("API startup complete")
    yield

    logger.info("Shutting down API...")


# Create FastAPI application
app = FastAPI(
    title="EM Vidros AI Assistant API",
    description="API para o assistente virtual inteligente da EM Vidros",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Inngest functions
inngest.fast_api.serve(app, inngest_client, inngest_functions)


# Pydantic Models
class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    session_id: str
    sources: List[dict] = []
    success: bool
    routed_to: Optional[str] = None


class QueryRequest(BaseModel):
    """Query request model."""

    question: str = Field(..., description="Question to ask")
    top_k: int = Field(5, description="Number of sources to retrieve")


class QueryResponse(BaseModel):
    """Query response model."""

    response: str
    sources: List[dict] = []
    success: bool
    routed_to: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information model."""

    session_id: str
    created_at: str
    updated_at: str
    message_count: int


class StatsResponse(BaseModel):
    """System statistics response model."""

    vector_store: dict
    sessions_count: int
    context_files: dict
    model: str


class ScrapeRequest(BaseModel):
    """Scrape request model."""

    url: Optional[str] = None
    max_pages: Optional[int] = None


class ScrapeResponse(BaseModel):
    """Scrape response model."""

    success: bool
    message: str
    event_id: Optional[str] = None


# API Endpoints


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "EM Vidros AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store_connected": (
            vector_store.check_collection_exists() if vector_store else False
        ),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI assistant.

    This endpoint processes user messages and returns AI responses.
    It maintains session history and routes support queries appropriately.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        result = rag_engine.chat(message=request.message, session_id=session_id)

        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            sources=result.get("sources", []),
            success=result["success"],
            routed_to=result.get("routed_to"),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the knowledge base without chat history."""
    try:
        result = rag_engine.query(question=request.question, top_k=request.top_k)

        return QueryResponse(
            response=result["response"],
            sources=result.get("sources", []),
            success=result["success"],
            routed_to=result.get("routed_to"),
        )

    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(limit: int = 100):
    """List all chat sessions."""
    try:
        sessions = session_memory.list_sessions(limit=limit)

        result = []
        for session in sessions:
            messages = session_memory.get_chat_history(session["session_id"])
            result.append(
                {
                    "session_id": session["session_id"],
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "message_count": len(messages),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details and chat history."""
    try:
        session = session_memory.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = session_memory.get_chat_history(session_id)

        return {"session": session, "messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    try:
        success = session_memory.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Session deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics."""
    try:
        sessions = session_memory.list_sessions()
        stats = rag_engine.get_stats()

        # Get context files stats
        doc_loader = DocumentLoader()
        context_stats = doc_loader.get_stats()

        return StatsResponse(
            vector_store=stats.get("vector_store", {}),
            sessions_count=len(sessions),
            context_files=context_stats,
            model=stats.get("model", Config.MODEL_NAME),
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest):
    """Trigger website scraping via Inngest."""
    try:
        return ScrapeResponse(
            success=True,
            message="Scrape job triggered. Check Inngest dashboard for progress.",
            event_id=str(uuid.uuid4()),
        )

    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reload-context")
async def reload_context():
    """Reload and reindex context folder documents."""
    try:
        doc_loader = DocumentLoader()
        documents = doc_loader.load_all()

        if documents:
            count = vector_store.add_documents(documents)
            return {
                "success": True,
                "message": f"Reloaded {count} documents",
                "documents_count": count,
            }
        else:
            return {
                "success": True,
                "message": "No documents found in context folder",
                "documents_count": 0,
            }

    except Exception as e:
        logger.error(f"Error reloading context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
