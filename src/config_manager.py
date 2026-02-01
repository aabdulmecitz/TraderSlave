"""
Configuration Manager - Load and manage scraping configuration.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "scraper": {
        "base_url": "https://www.amazon.com/dp/",
        "marketplace": "amazon_us",
        "headless": True,
        "timeout_ms": 30000,
        "max_retries": 3,
        "delay_between_requests_sec": 2,
    },
    "paths": {
        "database_dir": "product_datas",
        "output_dir": "output",
        "reports_dir": "output/reports",
        "asins_file": "asins.txt"
    },
    "analysis": {
        "auto_analyze_on_scrape": False,
        "save_reports": True
    }
}


class ConfigManager:
    """Manage scraping configuration from config/scraping_config.json."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from file or use defaults."""
        config_paths = [
            Path("config/scraping_config.json"),
            Path("/app/config/scraping_config.json"),  # Docker path
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                    logger.info(f"Loaded config from {config_path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load config: {e}")
        
        logger.info("Using default configuration")
        self._config = DEFAULT_CONFIG.copy()
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
    
    @property
    def scraper(self) -> Dict[str, Any]:
        return self._config.get("scraper", DEFAULT_CONFIG["scraper"])
    
    @property
    def paths(self) -> Dict[str, Any]:
        return self._config.get("paths", DEFAULT_CONFIG["paths"])
    
    @property
    def analysis(self) -> Dict[str, Any]:
        return self._config.get("analysis", DEFAULT_CONFIG["analysis"])
    
    @property
    def user_agents(self) -> list:
        return self._config.get("user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ])
    
    @property
    def base_url(self) -> str:
        return self.scraper.get("base_url", "https://www.amazon.com/dp/")
    
    @property
    def marketplace(self) -> str:
        return self.scraper.get("marketplace", "amazon_us")
    
    @property
    def headless(self) -> bool:
        return self.scraper.get("headless", True)
    
    @property
    def timeout(self) -> int:
        return self.scraper.get("timeout_ms", 30000)
    
    @property
    def max_retries(self) -> int:
        return self.scraper.get("max_retries", 3)
    
    @property
    def delay(self) -> float:
        return self.scraper.get("delay_between_requests_sec", 2)
    
    @property
    def database_dir(self) -> str:
        return self.paths.get("database_dir", "product_datas")
    
    @property
    def output_dir(self) -> str:
        return self.paths.get("output_dir", "output")
    
    def get_marketplace_config(self, marketplace: str) -> Dict[str, Any]:
        """Get configuration for a specific marketplace."""
        marketplaces = self._config.get("supported_marketplaces", {})
        return marketplaces.get(marketplace, {
            "base_url": "https://www.amazon.com/dp/",
            "currency": "USD",
            "language": "en"
        })
    
    def set_marketplace(self, marketplace: str):
        """Switch to a different marketplace."""
        mp_config = self.get_marketplace_config(marketplace)
        if mp_config:
            self._config["scraper"]["marketplace"] = marketplace
            self._config["scraper"]["base_url"] = mp_config["base_url"]
            logger.info(f"Switched to marketplace: {marketplace}")


# Global config instance
config = ConfigManager()
