"""Streamlit frontend for EM Vidros RAG AI Assistant.

This module provides the web interface for the EM Vidros AI Assistant,
featuring a chat interface with source citations and session management.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any

import requests
import streamlit as st

from src.config import Config

# API Configuration
API_BASE_URL = "http://localhost:8000"


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True


def send_message(message: str) -> Dict[str, Any]:
    """Send message to API and get response.

    Args:
        message: User message to send

    Returns:
        API response dictionary
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "response": (
                "⚠️ Não foi possível conectar ao servidor. "
                "Verifique se a API está rodando em http://localhost:8000"
            ),
            "sources": [],
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"⚠️ Erro ao enviar mensagem: {str(e)}",
            "sources": [],
        }


def get_stats() -> Dict[str, Any]:
    """Get system statistics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def clear_chat():
    """Clear current chat session and start fresh."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []


def render_sidebar():
    """Render the sidebar with controls and statistics."""
    with st.sidebar:
        st.title("EM Vidros")
        st.markdown("*Assistente Virtual Inteligente*")

        st.divider()

        # Chat controls
        st.subheader("Controles")

        if st.button("🗑️ Nova Conversa", use_container_width=True):
            clear_chat()
            st.rerun()

        st.session_state.show_sources = st.checkbox(
            "📚 Mostrar Fontes", value=st.session_state.show_sources
        )

        st.divider()

        # System stats
        st.subheader("Estatísticas")
        stats = get_stats()

        if stats:
            col1, col2 = st.columns(2)
            with col1:
                points = stats.get("vector_store", {}).get("points_count", 0)
                st.metric("Documentos", points)
            with col2:
                st.metric("Sessões", stats.get("sessions_count", 0))

            # Context files
            context_files = stats.get("context_files", {})
            if context_files.get("total_files", 0) > 0:
                st.caption(f"📁 Arquivos de contexto: {context_files['total_files']}")

            st.caption(f"Modelo: {stats.get('model', 'N/A')}")
        else:
            st.info("API não conectada")

        st.divider()

        # Support information
        st.subheader("Suporte")
        st.markdown(
            "📧 **suporte@emvidros.com.br**\n\n"
            "Para dúvidas sobre entregas e pedidos, entre em contato."
        )

        st.divider()

        # Session info
        st.markdown("---")
        st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")


def render_welcome():
    """Render welcome message when chat is empty."""
    if not st.session_state.messages:
        st.info("👋 **Bem-vindo ao Assistente Virtual da EM Vidros!**")
        st.markdown(
            """
        Posso ajudar você com informações sobre:
        - 🪟 **Produtos**: Vidros temperados, laminados, espelhos
        - 🔧 **Serviços**: Instalação, manutenção, projetos personalizados
        - 📍 **Localização**: Onde encontrar nossas lojas
        - 📞 **Contato**: Telefones e horários de atendimento

        **Exemplos de perguntas:**
        - Quais tipos de vidros vocês vendem?
        - Qual o horário de funcionamento?
        - Vocês fazem instalação em residências?
        - Como faço para solicitar um orçamento?

        ---
        *Para consultas sobre entrega de produtos, fale diretamente com nosso suporte:*
        📧 suporte@emvidros.com.br
        """
        )


def render_chat_message(message: Dict[str, Any]):
    """Render a single chat message.

    Args:
        message: Message dictionary with role, content, and optional sources
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    sources = message.get("sources", [])
    routed_to = message.get("routed_to")

    with st.chat_message(role):
        # Show routing indicator for support queries
        if routed_to == "support" and role == "assistant":
            st.info("🔄 Redirecionado para Suporte")

        st.markdown(content)

        # Show sources if enabled and available
        if st.session_state.show_sources and sources and role == "assistant":
            with st.expander("📚 Fontes utilizadas"):
                for i, source in enumerate(sources, 1):
                    metadata = source.get("metadata", {})
                    title = metadata.get("title", "Documento")
                    url = metadata.get("url", "")
                    score = source.get("score", 0)

                    st.markdown(f"**{i}. {title}**")
                    if url:
                        st.caption(f"🔗 {url}")
                    if score:
                        st.caption(f"Relevância: {score:.2f}")

                    text = source.get("text", "")
                    if text:
                        st.text(text[:300] + "..." if len(text) > 300 else text)
                    st.divider()


def render_chat():
    """Render the main chat interface."""
    st.title("💬 Assistente EM Vidros")
    st.markdown("*Pergunte sobre nossos produtos e serviços de vidros e espelhos*")

    # Display existing messages
    for message in st.session_state.messages:
        render_chat_message(message)

    # Chat input
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Add user message to state
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        }
        st.session_state.messages.append(user_message)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                result = send_message(prompt)

            response_text = result.get(
                "response", "Desculpe, não consegui processar sua mensagem."
            )
            routed_to = result.get("routed_to")

            # Show routing indicator
            if routed_to == "support":
                st.info("🔄 Redirecionado para Suporte")

            st.markdown(response_text)

            # Show sources
            sources = result.get("sources", [])
            if st.session_state.show_sources and sources:
                with st.expander("📚 Fontes utilizadas"):
                    for i, source in enumerate(sources, 1):
                        metadata = source.get("metadata", {})
                        title = metadata.get("title", "Documento")
                        url = metadata.get("url", "")

                        st.markdown(f"**{i}. {title}**")
                        if url:
                            st.caption(f"🔗 {url}")

                        text = source.get("text", "")
                        if text:
                            st.text(text[:300] + "..." if len(text) > 300 else text)
                        st.divider()

        # Add assistant message to history
        assistant_message = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat(),
            "sources": sources,
            "routed_to": routed_to,
        }
        st.session_state.messages.append(assistant_message)


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="EM Vidros - Assistente Virtual",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    init_session_state()
    render_sidebar()
    render_welcome()
    render_chat()


if __name__ == "__main__":
    main()
