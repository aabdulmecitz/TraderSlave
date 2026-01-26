import asyncio
import logging
import random
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from playwright_stealth import stealth_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraperEngine:
    """
    Asynchronous Scraper Engine using Playwright with stealth capabilities
    and rotating User-Agents.
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    def __init__(self, headless: bool = True, timeout: int = 30000, max_retries: int = 3):
        self.headless = headless
        self.timeout = timeout
        self.max_retries = max_retries
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
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
        return random.choice(self.USER_AGENTS)

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
        url = f"https://www.amazon.com/dp/{asin}"
        
        for attempt in range(self.max_retries):
            context = None
            page = None
            try:
                context = await self._create_context()
                page = await context.new_page()
                
                # Apply stealth
                await stealth_async(page)
                
                logger.info(f"Fetching {asin} (Attempt {attempt + 1}/{self.max_retries})")
                
                # Navigate
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                
                # Basic check for bot detection/captcha
                # In a real scenario, you'd add more sophisticated checks here
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
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt + random.uniform(1, 3))
            
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
        
        return None
