"""Document loader for context folder files.

This module handles loading and indexing various document formats
from the context folder into the vector store.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from llama_index.core import Document
from llama_index.readers.file import PDFReader, DocxReader, MarkdownReader

from src.config import Config

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Load documents from context folder."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

    def __init__(self, context_path: str = None):
        self.context_path = Path(context_path or "./context")
        self.context_path.mkdir(exist_ok=True)

        # Initialize readers
        self._pdf_reader = PDFReader()
        self._docx_reader = DocxReader()
        self._md_reader = MarkdownReader()

    def _read_text_file(self, file_path: Path) -> List[Document]:
        """Read plain text files."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return [Document(
                text=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "type": "text",
                }
            )]
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return []

    def _read_pdf(self, file_path: Path) -> List[Document]:
        """Read PDF files."""
        try:
            documents = self._pdf_reader.load_data(file_path)
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "type": "pdf",
                })
            return documents
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return []

    def _read_docx(self, file_path: Path) -> List[Document]:
        """Read Word documents."""
        try:
            documents = self._docx_reader.load_data(file_path)
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "type": "docx",
                })
            return documents
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return []

    def _read_markdown(self, file_path: Path) -> List[Document]:
        """Read Markdown files."""
        try:
            documents = self._md_reader.load_data(file_path)
            for doc in documents:
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "type": "markdown",
                })
            return documents
        except Exception as e:
            logger.error(f"Error reading Markdown {file_path}: {e}")
            return []

    def load_file(self, file_path: Path) -> List[Document]:
        """Load a single file based on its extension."""
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return self._read_pdf(file_path)
        elif extension in (".docx", ".doc"):
            return self._read_docx(file_path)
        elif extension == ".md":
            return self._read_markdown(file_path)
        elif extension == ".txt":
            return self._read_text_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return []

    def load_all(self) -> List[Document]:
        """Load all supported documents from context folder."""
        all_documents = []

        if not self.context_path.exists():
            logger.warning(f"Context path does not exist: {self.context_path}")
            return all_documents

        for file_path in self.context_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                logger.info(f"Loading document: {file_path.name}")
                documents = self.load_file(file_path)
                all_documents.extend(documents)

        logger.info(f"Loaded {len(all_documents)} documents from context folder")
        return all_documents

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about context folder."""
        stats = {
            "total_files": 0,
            "by_type": {},
            "files": [],
        }

        if not self.context_path.exists():
            return stats

        for file_path in self.context_path.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    stats["total_files"] += 1
                    stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1
                    stats["files"].append(file_path.name)

        return stats
