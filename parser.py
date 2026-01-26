import logging
import re
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup, Tag
from models import (
    MasterProduct, Identification, SalesAnalytics, PricingMechanics,
    CompetitionAndInventory, SentimentAndQuality, LogisticsAndPhysical,
    ContentAssets, RiskAssessment, CompetitorStockLevel, RatingBreakdown, Dimensions
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Centralized Selector Map for easy updates
SELECTOR_MAP = {
    "identification": {
        "title": "#productTitle",
        "brand": "#bylineInfo",
        "manufacturer": "#detailBullets_feature_div > ul > li:nth-child(3) > span > span:nth-child(2)",
        "category_path": "#wayfinding-breadcrumbs_feature_div ul li a",
    },
    "sales_analytics": {
        "bsr_info": "#SalesRank", # Often extracting text involves regex
    },
    "pricing_mechanics": {
        "buy_box_price": ".a-price .a-offscreen", 
        "list_price": ".a-text-price .a-offscreen",
    },
    "competition": {
        "offer_count": "#olpLinkWidget_feature_div .a-declarative",
    },
    "sentiment": {
        "rating_overall": "#acrPopover .a-icon-alt",
        "review_count": "#acrCustomerReviewText",
    },
    "logistics": {
        "details_table": "#prodDetails",
    },
    "content": {
        "main_image": "#landingImage",
        "bullets": "#feature-bullets ul li span.a-list-item",
        "description": "#productDescription",
    }
}

class AmazonParser:
    """
    Parses HTML content using BeautifulSoup and a Selector Map 
    to populate Pydantic models.
    """

    def _clean_text(self, text: str) -> str:
        return text.strip() if text else ""

    def _extract_price(self, text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r'[\d,]+\.\d{2}', text)
        if match:
            return float(match.group().replace(',', ''))
        return None

    def _extract_int(self, text: str) -> Optional[int]:
        if not text:
            return None
        match = re.search(r'[\d,]+', text)
        if match:
            return int(match.group().replace(',', ''))
        return None

    def parse(self, html: str, asin: str) -> Optional[MasterProduct]:
        """
        Parses HTML string and returns a MasterProduct instance.
        """
        if not html:
            logger.error(f"Empty HTML provided for {asin}")
            return None

        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            return MasterProduct(
                identification=self._extract_identification(soup, asin),
                sales_analytics=self._extract_sales_analytics(soup),
                pricing_mechanics=self._extract_pricing(soup),
                competition_and_inventory=self._extract_competition(soup),
                sentiment_and_quality=self._extract_sentiment(soup),
                logistics_and_physical=self._extract_logistics(soup),
                content_assets=self._extract_content(soup),
                risk_assessment=self._extract_risk(soup)
            )
        except Exception as e:
            logger.error(f"Failed to parse product {asin}: {str(e)}")
            return None

    def _get_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        element = soup.select_one(selector)
        return self._clean_text(element.get_text()) if element else None

    def _extract_identification(self, soup: BeautifulSoup, asin: str) -> Identification:
        selectors = SELECTOR_MAP["identification"]
        
        # Category path extraction
        categories = []
        cat_elements = soup.select(selectors["category_path"])
        for cat in cat_elements:
            categories.append(self._clean_text(cat.get_text()))

        return Identification(
            asin=asin,
            title=self._get_text(soup, selectors["title"]),
            brand=self._get_text(soup, selectors["brand"]),
            manufacturer=self._get_text(soup, selectors["manufacturer"]),
            category_path=categories
            # parent_asin, ean_upc, mpn often require more complex extraction or API calls
        )

    def _extract_sales_analytics(self, soup: BeautifulSoup) -> SalesAnalytics:
        # Placeholder logic - often requires regex on specific containers
        return SalesAnalytics()

    def _extract_pricing(self, soup: BeautifulSoup) -> PricingMechanics:
        selectors = SELECTOR_MAP["pricing_mechanics"]
        
        buy_box_text = self._get_text(soup, selectors["buy_box_price"])
        list_price_text = self._get_text(soup, selectors["list_price"])
        
        return PricingMechanics(
            buy_box_price=self._extract_price(buy_box_text),
            list_price=self._extract_price(list_price_text)
        )

    def _extract_competition(self, soup: BeautifulSoup) -> CompetitionAndInventory:
        # Logic to extract seller counts / stock would go here
        return CompetitionAndInventory()

    def _extract_sentiment(self, soup: BeautifulSoup) -> SentimentAndQuality:
        selectors = SELECTOR_MAP["sentiment"]
        
        rating_text = self._get_text(soup, selectors["rating_overall"])
        review_count_text = self._get_text(soup, selectors["review_count"])
        
        rating = self._extract_price(rating_text) # Reusing float extractor
        reviews = self._extract_int(review_count_text)
        
        return SentimentAndQuality(
            rating_overall=rating,
            review_count=reviews
        )

    def _extract_logistics(self, soup: BeautifulSoup) -> LogisticsAndPhysical:
        # Extraction logic for product details table
        return LogisticsAndPhysical()

    def _extract_content(self, soup: BeautifulSoup) -> ContentAssets:
        selectors = SELECTOR_MAP["content"]
        
        bullets = []
        bullet_elements = soup.select(selectors["bullets"])
        for b in bullet_elements:
            bullets.append(self._clean_text(b.get_text()))

        main_img_elem = soup.select_one(selectors["main_image"])
        main_image = main_img_elem.get('src') or main_img_elem.get('data-old-hires') if main_img_elem else None

        return ContentAssets(
            main_image_url=main_image,
            description_text=self._get_text(soup, selectors["description"]),
            bullet_points=bullets
        )

    def _extract_risk(self, soup: BeautifulSoup) -> RiskAssessment:
        # Risk logic is often heuristics-based
        return RiskAssessment()
