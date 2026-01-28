"""Session memory storage using SQLite."""

import json
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from src.config import Config

logger = logging.getLogger(__name__)


class SessionMemory:
    """SQLite-based session memory for chat history."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id, timestamp)
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def create_session(self, session_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Create a new chat session."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO sessions (session_id, metadata, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (session_id, json.dumps(metadata) if metadata else None)
                )
                conn.commit()
                logger.info(f"Session created: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add a message to a session."""
        try:
            with self._get_connection() as conn:
                # Ensure session exists
                conn.execute(
                    "INSERT OR IGNORE INTO sessions (session_id) VALUES (?)",
                    (session_id,)
                )

                # Add message
                conn.execute(
                    """
                    INSERT INTO messages (session_id, role, content, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, role, content, json.dumps(metadata) if metadata else None)
                )

                # Update session timestamp
                conn.execute(
                    """
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                    """,
                    (session_id,)
                )

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    def get_chat_history(
        self,
        session_id: str,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        limit = limit or Config.MAX_CHAT_HISTORY

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT role, content, timestamp, metadata
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                    (session_id, limit)
                )

                messages = []
                for row in cursor.fetchall():
                    msg = {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                    }
                    if row["metadata"]:
                        msg["metadata"] = json.loads(row["metadata"])
                    messages.append(msg)

                return messages
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT session_id, created_at, updated_at, metadata
                    FROM sessions
                    WHERE session_id = ?
                    """,
                    (session_id,)
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "session_id": row["session_id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT session_id, created_at, updated_at, metadata
                    FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )

                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        "session_id": row["session_id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    })

                return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                logger.info(f"Session deleted: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def clear_old_sessions(self, days: int = 30) -> int:
        """Clear sessions older than specified days."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM sessions
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    """,
                    (days,)
                )
                conn.commit()
                deleted = cursor.rowcount
                logger.info(f"Cleared {deleted} old sessions")
                return deleted
        except Exception as e:
            logger.error(f"Error clearing old sessions: {e}")
            return 0
