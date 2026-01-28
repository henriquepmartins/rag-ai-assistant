"""
EM Vidros AI Assistant - Interface

Chat interface with clean, modern design inspired by shadcn/ui.
Uses teal/cyan color palette from EM Vidros brand.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any

import requests
import streamlit as st

from src.config import Config

API_BASE_URL = "http://localhost:8000"

# EM Vidros Color Palette
COLORS = {
    "primary": "#5DBDB6",
    "primary_light": "#7ECDC7",
    "primary_dark": "#4A9E98",
    "background": "#FAFAFA",
    "surface": "#FFFFFF",
    "text": "#1A1A1A",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "user_bubble": "#5DBDB6",
    "assistant_bubble": "#F3F4F6",
}


def init_session():
    """Initialize session variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = False


def send_message(message: str) -> Dict[str, Any]:
    """Send message to backend API."""
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
            "response": "Não foi possível conectar ao servidor. Verifique se a API está rodando.",
            "sources": [],
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"Erro: {str(e)}",
            "sources": [],
        }


def clear_chat():
    """Reset conversation."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []


def get_stats() -> Dict[str, Any]:
    """Fetch system stats."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def render_css():
    """Inject custom styles."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    .stApp {{
        background-color: {COLORS["background"]};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {COLORS["surface"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{
        font-size: 0.875rem;
        color: {COLORS["text_secondary"]};
    }}
    
    /* Main content area */
    .main .block-container {{
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 8rem;
    }}
    
    /* Chat container */
    .chat-container {{
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }}
    
    /* Message bubbles */
    .message-wrapper {{
        display: flex;
        width: 100%;
        margin-bottom: 1rem;
    }}
    
    .message-wrapper.user {{
        justify-content: flex-end;
    }}
    
    .message-wrapper.assistant {{
        justify-content: flex-start;
    }}
    
    .message-bubble {{
        max-width: 80%;
        padding: 1rem 1.25rem;
        border-radius: 1rem;
        font-size: 0.9375rem;
        line-height: 1.6;
        font-weight: 400;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    
    .message-bubble.user {{
        background-color: {COLORS["user_bubble"]};
        color: white;
        border-bottom-right-radius: 0.25rem;
    }}
    
    .message-bubble.assistant {{
        background-color: {COLORS["assistant_bubble"]};
        color: {COLORS["text"]};
        border-bottom-left-radius: 0.25rem;
        border: 1px solid {COLORS["border"]};
    }}
    
    /* Input area */
    .input-container {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(to top, {COLORS["background"]} 0%, {COLORS["background"]} 80%, transparent 100%);
        padding: 1.5rem 2rem 2rem;
        z-index: 100;
    }}
    
    .input-wrapper {{
        max-width: 900px;
        margin: 0 auto;
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}
    
    .stTextInput input {{
        border: none !important;
        background: transparent !important;
        font-size: 0.9375rem !important;
        padding: 0.5rem !important;
        color: {COLORS["text"]} !important;
    }}
    
    .stTextInput input:focus {{
        box-shadow: none !important;
    }}
    
    .stTextInput input::placeholder {{
        color: {COLORS["text_secondary"]} !important;
    }}
    
    /* Send button */
    .stButton button {{
        background-color: {COLORS["primary"]} !important;
        color: white !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton button:hover {{
        background-color: {COLORS["primary_dark"]} !important;
        transform: translateY(-1px);
    }}
    
    /* Sources accordion */
    .stExpander {{
        border: 1px solid {COLORS["border"]};
        border-radius: 0.75rem;
        margin-top: 0.75rem;
        background: {COLORS["surface"]};
    }}
    
    .stExpander summary {{
        font-size: 0.8125rem;
        color: {COLORS["text_secondary"]};
        font-weight: 500;
    }}
    
    /* Welcome message */
    .welcome-container {{
        text-align: center;
        padding: 4rem 2rem;
        max-width: 600px;
        margin: 0 auto;
    }}
    
    .welcome-title {{
        font-size: 2rem;
        font-weight: 300;
        color: {COLORS["text"]};
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }}
    
    .welcome-subtitle {{
        font-size: 1rem;
        color: {COLORS["text_secondary"]};
        font-weight: 400;
        line-height: 1.6;
    }}
    
    .suggestion-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        margin-top: 2rem;
    }}
    
    .suggestion-chip {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 2rem;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        color: {COLORS["text_secondary"]};
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .suggestion-chip:hover {{
        border-color: {COLORS["primary"]};
        color: {COLORS["primary"]};
    }}
    
    /* Sidebar elements */
    .sidebar-title {{
        font-size: 1.125rem;
        font-weight: 600;
        color: {COLORS["text"]};
        margin-bottom: 0.25rem;
    }}
    
    .sidebar-subtitle {{
        font-size: 0.8125rem;
        color: {COLORS["text_secondary"]};
        font-weight: 400;
    }}
    
    .sidebar-section {{
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid {COLORS["border"]};
    }}
    
    .sidebar-label {{
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {COLORS["text_secondary"]};
        font-weight: 600;
        margin-bottom: 0.75rem;
    }}
    
    /* Stats */
    .stat-value {{
        font-size: 1.5rem;
        font-weight: 300;
        color: {COLORS["text"]};
    }}
    
    .stat-label {{
        font-size: 0.75rem;
        color: {COLORS["text_secondary"]};
    }}
    
    /* Support badge */
    .support-badge {{
        background: linear-gradient(135deg, {COLORS["primary_light"]}20, {COLORS["primary"]}10);
        border: 1px solid {COLORS["primary"]}30;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        font-size: 0.8125rem;
        color: {COLORS["primary_dark"]};
        margin-top: 0.75rem;
    }}
    
    /* Spinner */
    .stSpinner > div {{
        border-color: {COLORS["primary"]} !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS["border"]};
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["text_secondary"]};
    }}
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with minimal styling."""
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-title">EM Vidros</div>
            <div class="sidebar-subtitle">Assistente Virtual</div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'></div>", unsafe_allow_html=True)
        
        # New chat button
        if st.button("Nova conversa", use_container_width=True):
            clear_chat()
            st.rerun()
        
        # Show sources toggle
        st.session_state.show_sources = st.checkbox(
            "Mostrar fontes",
            value=st.session_state.show_sources
        )
        
        st.markdown("<div class='sidebar-section'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Estatísticas</div>", unsafe_allow_html=True)
        
        stats = get_stats()
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                points = stats.get("vector_store", {}).get("points_count", 0)
                st.markdown(f"<div class='stat-value'>{points}</div>", unsafe_allow_html=True)
                st.markdown("<div class='stat-label'>documentos</div>", unsafe_allow_html=True)
            with col2:
                sessions = stats.get("sessions_count", 0)
                st.markdown(f"<div class='stat-value'>{sessions}</div>", unsafe_allow_html=True)
                st.markdown("<div class='stat-label'>sessões</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Suporte</div>", unsafe_allow_html=True)
        st.markdown("""
            <div style="font-size: 0.8125rem; color: #6B7280;">
                Dúvidas sobre entregas:<br>
                <a href="mailto:suporte@emvidros.com.br" style="color: #5DBDB6; text-decoration: none;">
                    suporte@emvidros.com.br
                </a>
            </div>
        """, unsafe_allow_html=True)


def render_welcome():
    """Render centered welcome message."""
    if st.session_state.messages:
        return
    
    suggestions = [
        "Quais produtos vocês vendem?",
        "Qual o horário de funcionamento?",
        "Como solicitar um orçamento?",
        "Vocês fazem instalação?",
    ]
    
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title">Como posso ajudar?</div>
            <div class="welcome-subtitle">
                Assistente virtual da EM Vidros. Tire dúvidas sobre produtos, 
                serviços e informações da empresa.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Suggestion chips
    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                handle_message(suggestion)


def render_message(message: Dict[str, Any]):
    """Render single chat message."""
    role = message.get("role", "user")
    content = message.get("content", "")
    sources = message.get("sources", [])
    routed_to = message.get("routed_to")
    
    is_user = role == "user"
    
    # Support routing indicator
    if routed_to == "support" and not is_user:
        st.markdown("""
            <div class="support-badge">
                Redirecionado para Suporte
            </div>
        """, unsafe_allow_html=True)
    
    # Message bubble
    alignment = "flex-end" if is_user else "flex-start"
    bubble_class = "user" if is_user else "assistant"
    
    st.markdown(f"""
        <div style="display: flex; justify-content: {alignment}; margin-bottom: 1rem;">
            <div class="message-bubble {bubble_class}">
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Sources
    if not is_user and st.session_state.show_sources and sources:
        with st.expander("Fontes"):
            for i, source in enumerate(sources, 1):
                metadata = source.get("metadata", {})
                title = metadata.get("title", "Documento")
                url = metadata.get("url", "")
                
                st.markdown(f"**{i}. {title}**")
                if url:
                    st.caption(url)


def handle_message(message: str):
    """Process user message and get response."""
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat(),
    })
    
    # Get AI response
    result = send_message(message)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": result.get("response", ""),
        "sources": result.get("sources", []),
        "routed_to": result.get("routed_to"),
        "timestamp": datetime.now().isoformat(),
    })
    
    st.rerun()


def render_chat():
    """Render chat interface."""
    # Display messages
    for message in st.session_state.messages:
        render_message(message)
    
    # Input area at bottom
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([6, 1])
    with col1:
        prompt = st.text_input(
            "",
            placeholder="Digite sua mensagem...",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col2:
        send_clicked = st.button("Enviar", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle input
    if send_clicked and prompt:
        handle_message(prompt)


def main():
    """Main entry point."""
    st.set_page_config(
        page_title="EM Vidros - Assistente",
        page_icon="🪟",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    render_css()
    init_session()
    render_sidebar()
    render_welcome()
    render_chat()


if __name__ == "__main__":
    main()
