import asyncio
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from .scraper_engine import AmazonScraperEngine
from .parser import AmazonParser
from .data_importer import DataImporter
from .models import MasterProduct
from .enhanced_models import EnhancedMasterProduct, MerchantAnalysisOutput
from .merchant_engine import AutonomousMerchantEngine
from .dashboard import MerchantDashboard
from .cross_marketplace import CrossMarketplaceEngine
from .config_manager import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def import_raw_data(marketplace: str = None):
    """Import all data from dumb_datas/ to product_datas/{marketplace}/."""
    logger.info("Starting raw data import...")
    importer = DataImporter(marketplace=marketplace)
    imported = await importer.import_all_raw(marketplace)
    
    stats = importer.get_stats()
    logger.info(f"Import complete: {len(imported)} products to {importer.marketplace}/")
    logger.info(f"Database: {stats['total_products']} products, {stats['total_size_mb']} MB")
    
    return imported


async def analyze_from_db(asins: List[str], importer: DataImporter):
    """Analyze products from database, save reports to output/."""
    engine = AutonomousMerchantEngine()
    dashboard = MerchantDashboard()
    
    for asin in asins:
        product = importer.get_product(asin)
        if not product:
            logger.warning(f"Product {asin} not found in {importer.marketplace}/ database")
            continue
        
        # Convert to dict first to avoid Pydantic type mismatch
        product_dict = product.model_dump(mode='json')
        base_product = MasterProduct(
            identification=product_dict['identification'],
            sales_analytics=product_dict.get('sales_analytics'),
            pricing_mechanics=product_dict.get('pricing_mechanics'),
            competition_and_inventory=product_dict.get('competition_and_inventory'),
            sentiment_and_quality=product_dict.get('sentiment_and_quality'),
            logistics_and_physical=product_dict.get('logistics_and_physical'),
            content_assets=product_dict.get('content_assets'),
            risk_assessment=product_dict.get('risk_assessment'),
            data_quality_score=product.meta.data_quality_score if product.meta else 0.5,
        )
        
        report = await engine.analyze(base_product)
        dashboard.display(report)
        
        product.merchant_analysis = MerchantAnalysisOutput(
            arbitrage_analysis=report.arbitrage_analysis.model_dump(mode='json'),
            private_label_analysis=report.private_label_analysis.model_dump(mode='json'),
            risk_analysis=report.risk_analysis.model_dump(mode='json'),
            verdict=report.verdict.model_dump(mode='json'),
            analyzed_at=report.analysis_timestamp
        )
        await importer.save_product(product)
        
        mp = importer.marketplace
        report_filename = f"{mp}_{asin}_{datetime.utcnow().strftime('%Y-%m-%d')}_analysis.json"
        await importer.save_report(report.model_dump(mode='json'), report_filename)
        logger.info(f"Report saved: output/reports/{report_filename}")


def cross_arbitrage(asins: List[str]):
    """Find cross-marketplace arbitrage opportunities."""
    engine = CrossMarketplaceEngine()
    
    for asin in asins:
        # Show all prices
        engine.display_all_prices(asin)
        
        # Find best arbitrage
        opp = engine.find_arbitrage(asin)
        if opp:
            engine.display_arbitrage(opp)
        else:
            print(f"No arbitrage opportunity found for {asin}")
            print("(Need data from at least 2 marketplaces)")


async def scrape_multi_marketplace(asin: str, marketplaces: List[str], with_analysis: bool = False):
    """Scrape same ASIN across multiple marketplaces."""
    parser = AmazonParser()
    
    for mp in marketplaces:
        logger.info(f"Scraping {asin} from {mp}...")
        
        # Get marketplace config
        mp_config = config.get_marketplace_config(f"amazon_{mp}")
        base_url = mp_config.get("base_url", f"https://www.amazon.com/dp/")
        
        importer = DataImporter(marketplace=mp)
        
        async with AmazonScraperEngine() as engine:
            # Override base URL for this marketplace
            engine.base_url = base_url
            
            html = await engine.fetch_page(asin)
            if not html:
                logger.warning(f"Failed to fetch {asin} from {mp}")
                continue
            
            product = parser.parse(html, asin)
            if not product:
                logger.warning(f"Failed to parse {asin} from {mp}")
                continue
            
            # Create enhanced product with marketplace info
            product_dict = product.model_dump(mode='json')
            product_dict['meta'] = {
                'schema_version': '2.0.0',
                'scraped_at': datetime.utcnow().isoformat(),
                'source': f'amazon_{mp}',
                'marketplace_code': mp,
                'currency': mp_config.get('currency', 'USD'),
                'marketplace_url': base_url.replace('/dp/', ''),
                'data_quality_score': product.data_quality_score or 0.5
            }
            
            enhanced = EnhancedMasterProduct(**product_dict)
            
            if with_analysis:
                merchant_engine = AutonomousMerchantEngine()
                base_product = MasterProduct(**product.model_dump(mode='json'))
                report = await merchant_engine.analyze(base_product)
                
                enhanced.merchant_analysis = MerchantAnalysisOutput(
                    arbitrage_analysis=report.arbitrage_analysis.model_dump(mode='json'),
                    private_label_analysis=report.private_label_analysis.model_dump(mode='json'),
                    risk_analysis=report.risk_analysis.model_dump(mode='json'),
                    verdict=report.verdict.model_dump(mode='json'),
                    analyzed_at=report.analysis_timestamp
                )
            
            await importer.save_product(enhanced, marketplace=mp)
            logger.info(f"Saved {asin} to {mp}/ database")


async def process_asin(
    asin: str, 
    engine: AmazonScraperEngine, 
    parser: AmazonParser, 
    importer: DataImporter,
    run_analysis: bool = False
):
    """Scrape and save to marketplace-specific database."""
    try:
        html = await engine.fetch_page(asin)
        if not html:
            logger.warning(f"Skipping {asin}: No HTML fetched")
            return

        product = parser.parse(html, asin)
        if not product:
            logger.warning(f"Skipping {asin}: Parsing failed")
            return
        
        mp = importer.marketplace
        mp_config = config.get_marketplace_config(f"amazon_{mp}")
        
        product_dict = product.model_dump(mode='json')
        product_dict['meta'] = {
            'schema_version': '2.0.0',
            'scraped_at': datetime.utcnow().isoformat(),
            'source': f'amazon_{mp}',
            'marketplace_code': mp,
            'currency': mp_config.get('currency', 'USD'),
            'data_quality_score': product.data_quality_score or 0.5
        }
        enhanced = EnhancedMasterProduct(**product_dict)
        
        if run_analysis:
            merchant_engine = AutonomousMerchantEngine()
            base_product = MasterProduct(**product.model_dump(mode='json'))
            report = await merchant_engine.analyze(base_product)
            
            enhanced.merchant_analysis = MerchantAnalysisOutput(
                arbitrage_analysis=report.arbitrage_analysis.model_dump(mode='json'),
                private_label_analysis=report.private_label_analysis.model_dump(mode='json'),
                risk_analysis=report.risk_analysis.model_dump(mode='json'),
                verdict=report.verdict.model_dump(mode='json'),
                analyzed_at=report.analysis_timestamp
            )
            
            report_filename = f"{mp}_{asin}_{datetime.utcnow().strftime('%Y-%m-%d')}_analysis.json"
            await importer.save_report(report.model_dump(mode='json'), report_filename)
        
        await importer.save_product(enhanced)
        logger.info(f"Saved to database: {mp}/{asin}")
        
    except Exception as e:
        logger.error(f"Error processing {asin}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(
        description="TraderSlave - Multi-Marketplace Amazon Intelligence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Scrape single ASIN:           python -m src.main B08N5KLR9X
  Scrape to UK marketplace:     python -m src.main --marketplace uk B08N5KLR9X
  Scrape across all markets:    python -m src.main --multi us,uk,de B08N5KLR9X
  Cross-marketplace arbitrage:  python -m src.main --cross-arbitrage B08N5KLR9X
  Analyze from database:        python -m src.main --analyze-db B08N5KLR9X
  List products in marketplace: python -m src.main --list-db
  Database stats:               python -m src.main --stats
  Import raw data:              python -m src.main --import-raw
        """
    )
    parser.add_argument('asins', nargs='*', help="ASINs to scrape")
    parser.add_argument('--file', help="File containing ASINs (one per line)")
    parser.add_argument('--no-headless', action='store_true', help="Show browser window")
    
    # Marketplace options
    parser.add_argument('--marketplace', '-m', default=None, 
                        help="Target marketplace: us, uk, de, fr, es, it, ca, jp")
    parser.add_argument('--multi', metavar='MARKETS', 
                        help="Scrape across multiple marketplaces (comma-separated): us,uk,de")
    
    # Analysis options
    parser.add_argument('--import-raw', action='store_true', help="Import dumb_datas/ to database")
    parser.add_argument('--analyze-db', nargs='+', metavar='ASIN', help="Analyze ASINs from database")
    parser.add_argument('--with-analysis', action='store_true', help="Run analysis during scrape")
    parser.add_argument('--cross-arbitrage', nargs='+', metavar='ASIN', 
                        help="Find cross-marketplace arbitrage opportunities")
    
    # Database options
    parser.add_argument('--list-db', action='store_true', help="List all products in database")
    parser.add_argument('--stats', action='store_true', help="Show database statistics")
    
    args = parser.parse_args()
    
    # Set marketplace from args or config
    marketplace = args.marketplace
    importer = DataImporter(marketplace=marketplace)
    
    # Import raw data
    if args.import_raw:
        await import_raw_data(marketplace)
        return
    
    # List products
    if args.list_db:
        if marketplace:
            products = importer.list_all_products(marketplace)
            print(f"\n📦 Products in {marketplace.upper()} ({len(products)}):")
            for asin in products:
                print(f"  • {asin}")
        else:
            for mp in importer.list_all_marketplaces():
                products = importer.list_all_products(mp)
                print(f"\n📦 {mp.upper()} ({len(products)} products):")
                for asin in products:
                    print(f"  • {asin}")
        return
    
    # Show stats
    if args.stats:
        stats = importer.get_stats()
        print(f"\n📊 Database Statistics:")
        print(f"  Total Products:  {stats['total_products']}")
        print(f"  Total Snapshots: {stats['total_snapshots']}")
        print(f"  Total Size:      {stats['total_size_mb']} MB")
        print(f"  DB Path:         {stats['db_path']}")
        print(f"\n  By Marketplace:")
        for mp, mp_stats in stats.get('marketplaces', {}).items():
            flag = {'us': '🇺🇸', 'uk': '🇬🇧', 'de': '🇩🇪', 'jp': '🇯🇵', 'fr': '🇫🇷', 
                    'es': '🇪🇸', 'it': '🇮🇹', 'ca': '🇨🇦'}.get(mp, '🌐')
            print(f"    {flag} {mp.upper()}: {mp_stats['products']} products, {mp_stats['size_mb']} MB")
        return
    
    # Cross-marketplace arbitrage
    if args.cross_arbitrage:
        cross_arbitrage(args.cross_arbitrage)
        return
    
    # Analyze from database
    if args.analyze_db:
        await analyze_from_db(args.analyze_db, importer)
        return
    
    # Build ASIN list
    asin_list = args.asins or []
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_asins = [line.strip() for line in f if line.strip()]
                asin_list.extend(file_asins)
        except Exception as e:
            logger.error(f"Error reading ASIN file: {e}")
            return

    if not asin_list:
        parser.print_help()
        return

    # Multi-marketplace scraping
    if args.multi:
        marketplaces = [m.strip() for m in args.multi.split(',')]
        for asin in asin_list:
            await scrape_multi_marketplace(asin, marketplaces, args.with_analysis)
        
        # Show arbitrage after scraping
        print("\n" + "="*60)
        print("🌍 CROSS-MARKETPLACE COMPARISON")
        print("="*60)
        cross_arbitrage(asin_list)
        return

    # Single marketplace scraping
    logger.info(f"Starting scraper for {len(asin_list)} ASINs to {importer.marketplace}/...")
    amazon_parser = AmazonParser()
    
    async with AmazonScraperEngine(headless=not args.no_headless) as engine:
        for asin in asin_list:
            await process_asin(asin, engine, amazon_parser, importer, args.with_analysis)
            await asyncio.sleep(2)
    
    stats = importer.get_stats()
    logger.info(f"Database: {stats['total_products']} products in {stats['db_path']}")
    logger.info("Scraping completed.")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
