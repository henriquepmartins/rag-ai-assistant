"""Script to manually scrape and ingest website content."""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.scraper import WebsiteScraper
from src.vector_store import VectorStoreManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(
        description="Scrape EM Vidros website and ingest into vector store"
    )
    parser.add_argument(
        "--url",
        default=Config.WEBSITE_URL,
        help=f"Website URL to scrape (default: {Config.WEBSITE_URL})"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=Config.MAX_PAGES,
        help=f"Maximum pages to scrape (default: {Config.MAX_PAGES})"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear vector store before ingesting"
    )

    args = parser.parse_args()

    # Initialize vector store
    vector_store = VectorStoreManager()

    # Clear if requested
    if args.clear:
        logger.info("Clearing vector store...")
        vector_store.clear_collection()
        logger.info("Vector store cleared")

    # Scrape website
    logger.info(f"Starting scrape of {args.url}")
    scraper = WebsiteScraper(base_url=args.url, max_pages=args.max_pages)
    scraped_content = await scraper.scrape()

    logger.info(f"Scraped {len(scraped_content)} pages")

    if not scraped_content:
        logger.warning("No content scraped. Exiting.")
        return

    # Ingest into vector store
    logger.info("Ingesting content into vector store...")
    documents_added = vector_store.add_web_content(scraped_content)

    logger.info(f"Successfully ingested {documents_added} documents")

    # Show stats
    stats = vector_store.get_stats()
    logger.info(f"Vector store stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
