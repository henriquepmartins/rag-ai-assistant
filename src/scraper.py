"""Web scraper para o site EM Vidros."""

import asyncio
import logging
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Any

import aiohttp
from bs4 import BeautifulSoup

from src.config import Config

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Extrai conteúdo do site EM Vidros."""

    def __init__(self, base_url: str = None, max_pages: int = None, delay: float = None):
        self.base_url = base_url or Config.WEBSITE_URL
        self.max_pages = max_pages or Config.MAX_PAGES
        self.delay = delay or Config.SCRAPE_DELAY
        self.visited_urls: Set[str] = set()
        self.scraped_content: List[Dict[str, Any]] = []

    def _is_valid_url(self, url: str) -> bool:
        """Valida se URL pertence ao domínio e é acessível."""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)

        if parsed_url.netloc != parsed_base.netloc:
            return False

        if parsed_url.scheme not in ("http", "https"):
            return False

        skip_patterns = [
            ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".css", ".js",
            ".zip", ".tar", ".gz", ".mp4", ".mp3", ".avi",
            "/wp-content/uploads/", "/wp-includes/",
            "mailto:", "tel:", "javascript:",
        ]
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in skip_patterns)

    def _extract_text(self, soup: BeautifulSoup, url: str) -> str:
        """Extrai texto relevante da página."""
        # Remove elementos não relevantes
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Busca área principal de conteúdo
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", class_="content") or
            soup.find("div", id="content") or
            soup.find("div", class_="entry-content")
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Limpa texto
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extrai links válidos da página."""
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            full_url = urljoin(current_url, href)
            if self._is_valid_url(full_url):
                links.append(full_url)
        return links

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extrai metadados da página."""
        metadata = {
            "url": url,
            "title": "",
            "description": "",
        }

        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["description"] = meta_desc["content"]

        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content") and not metadata["description"]:
            metadata["description"] = og_desc["content"]

        return metadata

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """Busca página e retorna conteúdo."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    return url, html
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return url, None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return url, None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Inicia scraping a partir da URL base."""
        logger.info(f"Starting scrape of {self.base_url}")

        async with aiohttp.ClientSession() as session:
            urls_to_visit = [self.base_url]

            while urls_to_visit and len(self.visited_urls) < self.max_pages:
                batch = urls_to_visit[:5]
                urls_to_visit = urls_to_visit[5:]

                # Busca páginas em paralelo
                tasks = [self._fetch_page(session, url) for url in batch]
                results = await asyncio.gather(*tasks)

                for url, html in results:
                    if html is None or url in self.visited_urls:
                        continue

                    self.visited_urls.add(url)
                    soup = BeautifulSoup(html, "html.parser")

                    text = self._extract_text(soup, url)
                    metadata = self._extract_metadata(soup, url)
                    links = self._extract_links(soup, url)

                    if text and len(text) > 100:
                        self.scraped_content.append({
                            **metadata,
                            "content": text,
                            "content_length": len(text),
                        })
                        logger.info(f"Scraped: {url} ({len(text)} chars)")

                    # Adiciona novas URLs
                    for link in links:
                        if link not in self.visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)

                # Rate limiting
                await asyncio.sleep(self.delay)

        logger.info(f"Scraping complete. Total pages: {len(self.scraped_content)}")
        return self.scraped_content

    def scrape_sync(self) -> List[Dict[str, Any]]:
        """Wrapper síncrono para scrape."""
        return asyncio.run(self.scrape())


def scrape_website(url: str = None) -> List[Dict[str, Any]]:
    """Função auxiliar para scraping."""
    scraper = WebsiteScraper(base_url=url)
    return scraper.scrape_sync()
