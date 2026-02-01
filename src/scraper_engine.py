import asyncio
import logging
import random
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

from .config_manager import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonScraperEngine:
    """
    Asynchronous Scraper Engine using Playwright with stealth capabilities
    and rotating User-Agents. Configuration loaded from config/scraping_config.json.
    """

    def __init__(self, headless: bool = None, timeout: int = None, max_retries: int = None):
        # Use config values as defaults, allow override via constructor
        self.headless = headless if headless is not None else config.headless
        self.timeout = timeout if timeout is not None else config.timeout
        self.max_retries = max_retries if max_retries is not None else config.max_retries
        self.base_url = config.base_url
        self.user_agents = config.user_agents
        self.delay = config.delay
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        logger.info(f"ScraperEngine initialized: marketplace={config.marketplace}, base_url={self.base_url}")
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents) if self.user_agents else (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

    async def _create_context(self) -> BrowserContext:
        user_agent = self._get_random_user_agent()
        logger.debug(f"Using User-Agent: {user_agent}")
        
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            accept_downloads=False
        )
        return context

    async def fetch_page(self, asin: str) -> Optional[str]:
        """
        Fetches the product page for a given ASIN with retries and rotation.
        Returns the HTML content string or None if failed.
        """
        url = f"{self.base_url}{asin}"
        
        for attempt in range(self.max_retries):
            context = None
            page = None
            try:
                context = await self._create_context()
                page = await context.new_page()
                
                if HAS_STEALTH:
                    await stealth_async(page)
                
                logger.info(f"Fetching {asin} (Attempt {attempt + 1}/{self.max_retries})")
                
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                
                content = await page.content()
                
                if "Type the characters you see below" in content:
                    logger.warning(f"CAPTCHA detected for {asin}")
                    raise Exception("CAPTCHA detected")
                
                return content

            except Exception as e:
                logger.warning(f"Error fetching {asin} on attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {asin} after {self.max_retries} attempts")
                    return None
                
                await asyncio.sleep(2 ** attempt + random.uniform(1, 3))
            
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
        
        return None
