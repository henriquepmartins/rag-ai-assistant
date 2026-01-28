"""Inngest functions for background processing."""

import logging
from typing import List, Dict, Any

import inngest
from inngest.experimental import ai

from src.config import Config
from src.scraper import WebsiteScraper
from src.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


# Initialize Inngest client
inngest_client = inngest.Inngest(
    app_id=Config.INNGEST_APP_ID,
    logger=logging.getLogger("uvicorn"),
    is_production=False,
)


class ScrapeEvent(inngest.Event):
    """Event for triggering website scraping."""
    name = "rag/scrape_website"

    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(
            name=self.name,
            data=data or {}
        )


class IngestEvent(inngest.Event):
    """Event for triggering content ingestion."""
    name = "rag/ingest_content"

    def __init__(self, data: Dict[str, Any] = None):
        super().__init__(
            name=self.name,
            data=data or {}
        )


@inngest_client.create_function(
    fn_id="scrape-website",
    trigger=inngest.TriggerEvent(event="rag/scrape_website"),
)
async def scrape_website_function(ctx: inngest.Context) -> Dict[str, Any]:
    """Scrape the EM Vidros website and store content."""
    logger.info("Starting website scraping...")

    try:
        # Get URL from event data or use default
        url = ctx.event.data.get("url", Config.WEBSITE_URL)
        max_pages = ctx.event.data.get("max_pages", Config.MAX_PAGES)

        # Scrape website
        scraper = WebsiteScraper(base_url=url, max_pages=max_pages)
        scraped_content = await scraper.scrape()

        logger.info(f"Scraped {len(scraped_content)} pages from {url}")

        # Trigger ingestion event
        await ctx.step.send_event(
            "ingest-content",
            inngest.Event(
                name="rag/ingest_content",
                data={"content": scraped_content}
            )
        )

        return {
            "success": True,
            "pages_scraped": len(scraped_content),
            "url": url,
        }

    except Exception as e:
        logger.error(f"Error scraping website: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@inngest_client.create_function(
    fn_id="ingest-content",
    trigger=inngest.TriggerEvent(event="rag/ingest_content"),
)
async def ingest_content_function(ctx: inngest.Context) -> Dict[str, Any]:
    """Ingest scraped content into vector store."""
    logger.info("Starting content ingestion...")

    try:
        # Get content from event data
        content = ctx.event.data.get("content", [])

        if not content:
            logger.warning("No content to ingest")
            return {
                "success": False,
                "error": "No content provided",
            }

        # Initialize vector store
        vector_store = VectorStoreManager()

        # Add content to vector store
        documents_added = vector_store.add_web_content(content)

        logger.info(f"Ingested {documents_added} documents")

        # Get stats
        stats = vector_store.get_stats()

        return {
            "success": True,
            "documents_added": documents_added,
            "vector_store_stats": stats,
        }

    except Exception as e:
        logger.error(f"Error ingesting content: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@inngest_client.create_function(
    fn_id="clear-and-rescrape",
    trigger=inngest.TriggerEvent(event="rag/clear_and_rescrape"),
)
async def clear_and_rescrape_function(ctx: inngest.Context) -> Dict[str, Any]:
    """Clear vector store and rescrape website."""
    logger.info("Starting clear and rescrape process...")

    try:
        # Clear vector store
        vector_store = VectorStoreManager()
        cleared = vector_store.clear_collection()

        if not cleared:
            logger.warning("Failed to clear vector store")

        # Trigger scraping
        url = ctx.event.data.get("url", Config.WEBSITE_URL)
        max_pages = ctx.event.data.get("max_pages", Config.MAX_PAGES)

        await ctx.step.send_event(
            "scrape-after-clear",
            inngest.Event(
                name="rag/scrape_website",
                data={"url": url, "max_pages": max_pages}
            )
        )

        return {
            "success": True,
            "cleared": cleared,
            "message": "Vector store cleared and rescrape triggered",
        }

    except Exception as e:
        logger.error(f"Error in clear and rescrape: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# List of all functions to serve
inngest_functions = [
    scrape_website_function,
    ingest_content_function,
    clear_and_rescrape_function,
]


def trigger_scrape(url: str = None, max_pages: int = None) -> None:
    """Trigger a scrape event (for manual triggering)."""
    import asyncio

    async def _send():
        await inngest_client.send(
            inngest.Event(
                name="rag/scrape_website",
                data={
                    "url": url or Config.WEBSITE_URL,
                    "max_pages": max_pages or Config.MAX_PAGES,
                }
            )
        )

    asyncio.run(_send())
