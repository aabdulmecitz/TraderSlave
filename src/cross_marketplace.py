"""
Cross-Marketplace Arbitrage Engine.
Compares product prices across multiple Amazon marketplaces to find arbitrage opportunities.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Currency exchange rates to USD (approximate - should be updated from API in production)
EXCHANGE_RATES = {
    "USD": 1.0,
    "GBP": 1.26,
    "EUR": 1.08,
    "CAD": 0.74,
    "JPY": 0.0067,
    "AUD": 0.65,
}

MARKETPLACE_FLAGS = {
    "us": "🇺🇸",
    "uk": "🇬🇧",
    "de": "🇩🇪",
    "fr": "🇫🇷",
    "es": "🇪🇸",
    "it": "🇮🇹",
    "ca": "🇨🇦",
    "jp": "🇯🇵",
}

MARKETPLACE_CURRENCIES = {
    "us": "USD",
    "uk": "GBP",
    "de": "EUR",
    "fr": "EUR",
    "es": "EUR",
    "it": "EUR",
    "ca": "CAD",
    "jp": "JPY",
}


@dataclass
class MarketplacePrice:
    """Price data for a single marketplace."""
    marketplace: str
    currency: str
    local_price: float
    usd_price: float
    buy_box_price: float
    fba_fee_estimate: float
    available: bool = True


@dataclass
class ArbitrageOpportunity:
    """Cross-marketplace arbitrage opportunity."""
    asin: str
    title: str
    buy_marketplace: str
    buy_price_local: float
    buy_price_usd: float
    buy_currency: str
    sell_marketplace: str
    sell_price_local: float
    sell_price_usd: float
    sell_currency: str
    gross_profit_usd: float
    profit_margin_pct: float
    recommendation: str


class CrossMarketplaceEngine:
    """
    Analyzes product pricing across multiple Amazon marketplaces
    to find arbitrage opportunities.
    """
    
    def __init__(self, db_dir: str = "product_datas"):
        self.db_dir = Path(db_dir)
    
    def get_available_marketplaces(self, asin: str) -> List[str]:
        """Get list of marketplaces where this ASIN has data."""
        marketplaces = []
        for mp_dir in self.db_dir.iterdir():
            if mp_dir.is_dir() and (mp_dir / asin / "latest.json").exists():
                marketplaces.append(mp_dir.name)
        return sorted(marketplaces)
    
    def load_marketplace_data(self, asin: str, marketplace: str) -> Optional[Dict[str, Any]]:
        """Load product data for a specific marketplace."""
        filepath = self.db_dir / marketplace / asin / "latest.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return None
    
    def get_all_marketplace_prices(self, asin: str) -> List[MarketplacePrice]:
        """Get prices for an ASIN across all available marketplaces."""
        prices = []
        
        for marketplace in self.get_available_marketplaces(asin):
            data = self.load_marketplace_data(asin, marketplace)
            if not data:
                continue
            
            pricing = data.get("pricing_mechanics", {})
            buy_box = pricing.get("buy_box_price", 0)
            
            if buy_box <= 0:
                continue
            
            currency = MARKETPLACE_CURRENCIES.get(marketplace, "USD")
            rate = EXCHANGE_RATES.get(currency, 1.0)
            usd_price = buy_box * rate
            
            fba_fee = pricing.get("fba_total_fee", 0) or (buy_box * 0.15)
            
            prices.append(MarketplacePrice(
                marketplace=marketplace,
                currency=currency,
                local_price=buy_box,
                usd_price=round(usd_price, 2),
                buy_box_price=buy_box,
                fba_fee_estimate=fba_fee,
                available=True
            ))
        
        return sorted(prices, key=lambda x: x.usd_price)
    
    def find_arbitrage(self, asin: str) -> Optional[ArbitrageOpportunity]:
        """Find the best arbitrage opportunity for an ASIN."""
        prices = self.get_all_marketplace_prices(asin)
        
        if len(prices) < 2:
            logger.warning(f"Need at least 2 marketplaces for arbitrage, found {len(prices)}")
            return None
        
        # Best = lowest USD price (buy), Worst = highest USD price (sell)
        best_buy = prices[0]
        best_sell = prices[-1]
        
        if best_buy.marketplace == best_sell.marketplace:
            return None
        
        gross_profit = best_sell.usd_price - best_buy.usd_price
        margin_pct = (gross_profit / best_buy.usd_price) * 100 if best_buy.usd_price > 0 else 0
        
        # Generate recommendation
        if margin_pct >= 20:
            recommendation = "🟢 STRONG BUY - Excellent arbitrage opportunity"
        elif margin_pct >= 10:
            recommendation = "🟡 CONDITIONAL - Consider fees and shipping costs"
        elif margin_pct >= 5:
            recommendation = "🟠 MARGINAL - Low profit after fees"
        else:
            recommendation = "🔴 NOT RECOMMENDED - Insufficient margin"
        
        # Get title from any available data
        title = "Unknown Product"
        for mp in [best_buy.marketplace, best_sell.marketplace]:
            data = self.load_marketplace_data(asin, mp)
            if data and data.get("identification", {}).get("title"):
                title = data["identification"]["title"]
                break
        
        return ArbitrageOpportunity(
            asin=asin,
            title=title[:60] + "..." if len(title) > 60 else title,
            buy_marketplace=best_buy.marketplace,
            buy_price_local=best_buy.local_price,
            buy_price_usd=best_buy.usd_price,
            buy_currency=best_buy.currency,
            sell_marketplace=best_sell.marketplace,
            sell_price_local=best_sell.local_price,
            sell_price_usd=best_sell.usd_price,
            sell_currency=best_sell.currency,
            gross_profit_usd=round(gross_profit, 2),
            profit_margin_pct=round(margin_pct, 1),
            recommendation=recommendation
        )
    
    def display_arbitrage(self, opp: ArbitrageOpportunity):
        """Display arbitrage opportunity in a formatted way."""
        buy_flag = MARKETPLACE_FLAGS.get(opp.buy_marketplace, "🌐")
        sell_flag = MARKETPLACE_FLAGS.get(opp.sell_marketplace, "🌐")
        
        print(f"\n{'='*60}")
        print(f"🌍 CROSS-MARKETPLACE ARBITRAGE: {opp.asin}")
        print(f"{'='*60}")
        print(f"📦 {opp.title}")
        print()
        print(f"  💰 BUY FROM:  {buy_flag} {opp.buy_marketplace.upper()}")
        print(f"     Price: {opp.buy_currency} {opp.buy_price_local:.2f} (${opp.buy_price_usd:.2f})")
        print()
        print(f"  📤 SELL ON:   {sell_flag} {opp.sell_marketplace.upper()}")
        print(f"     Price: {opp.sell_currency} {opp.sell_price_local:.2f} (${opp.sell_price_usd:.2f})")
        print()
        print(f"  📊 PROFIT:    ${opp.gross_profit_usd:.2f} ({opp.profit_margin_pct:.1f}% margin)")
        print()
        print(f"  {opp.recommendation}")
        print(f"{'='*60}\n")
    
    def display_all_prices(self, asin: str):
        """Display prices across all marketplaces."""
        prices = self.get_all_marketplace_prices(asin)
        
        if not prices:
            print(f"No marketplace data found for {asin}")
            return
        
        print(f"\n{'='*60}")
        print(f"🌍 MARKETPLACE PRICES: {asin}")
        print(f"{'='*60}")
        print(f"{'Marketplace':<12} {'Local Price':<15} {'USD Equiv.':<12}")
        print("-" * 39)
        
        for p in prices:
            flag = MARKETPLACE_FLAGS.get(p.marketplace, "🌐")
            marker = " ← LOWEST" if p == prices[0] else ""
            print(f"{flag} {p.marketplace.upper():<9} {p.currency} {p.local_price:<10.2f} ${p.usd_price:<8.2f}{marker}")
        
        print(f"{'='*60}\n")
