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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def import_raw_data():
    """Import all data from dumb_datas/ to product_datas/ database."""
    logger.info("Starting raw data import...")
    importer = DataImporter()
    imported = await importer.import_all_raw()
    
    stats = importer.get_stats()
    logger.info(f"Import complete: {len(imported)} products")
    logger.info(f"Database: {stats['total_products']} products, {stats['total_size_mb']} MB")
    
    return imported


async def analyze_from_db(asins: List[str], importer: DataImporter):
    """Analyze products from database, save reports to output/."""
    engine = AutonomousMerchantEngine()
    dashboard = MerchantDashboard()
    
    for asin in asins:
        product = importer.get_product(asin)
        if not product:
            logger.warning(f"Product {asin} not found in database")
            continue
        
        base_product = MasterProduct(
            identification=product.identification,
            sales_analytics=product.sales_analytics,
            pricing_mechanics=product.pricing_mechanics,
            competition_and_inventory=product.competition_and_inventory,
            sentiment_and_quality=product.sentiment_and_quality,
            logistics_and_physical=product.logistics_and_physical,
            content_assets=product.content_assets,
            risk_assessment=product.risk_assessment,
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
        
        report_filename = f"{asin}_{datetime.utcnow().strftime('%Y-%m-%d')}_analysis.json"
        await importer.save_report(report.model_dump(mode='json'), report_filename)
        logger.info(f"Report saved: output/reports/{report_filename}")


async def process_asin(
    asin: str, 
    engine: AmazonScraperEngine, 
    parser: AmazonParser, 
    importer: DataImporter,
    run_analysis: bool = False
):
    """Scrape and save to database."""
    try:
        html = await engine.fetch_page(asin)
        if not html:
            logger.warning(f"Skipping {asin}: No HTML fetched")
            return

        product = parser.parse(html, asin)
        if not product:
            logger.warning(f"Skipping {asin}: Parsing failed")
            return
        
        product_dict = product.model_dump(mode='json')
        product_dict['meta'] = {
            'schema_version': '2.0.0',
            'scraped_at': datetime.utcnow().isoformat(),
            'source': 'amazon_us',
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
            
            report_filename = f"{asin}_{datetime.utcnow().strftime('%Y-%m-%d')}_analysis.json"
            await importer.save_report(report.model_dump(mode='json'), report_filename)
        
        await importer.save_product(enhanced)
        logger.info(f"Saved to database: {asin}")
        
    except Exception as e:
        logger.error(f"Error processing {asin}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(
        description="TraderSlave - Amazon Product Database & Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Import raw data:        python -m src.main --import-raw
  Scrape to database:     python -m src.main B08N5KLR9X B017OEL8P0
  Scrape with analysis:   python -m src.main B08N5KLR9X --with-analysis
  Analyze from database:  python -m src.main --analyze-db B08N5KLR9X
  List database:          python -m src.main --list-db
  Database stats:         python -m src.main --stats
        """
    )
    parser.add_argument('asins', nargs='*', help="ASINs to scrape")
    parser.add_argument('--file', help="File containing ASINs (one per line)")
    parser.add_argument('--no-headless', action='store_true', help="Show browser window")
    
    parser.add_argument('--import-raw', action='store_true', help="Import dumb_datas/ to database")
    parser.add_argument('--analyze-db', nargs='+', metavar='ASIN', help="Analyze ASINs from database")
    parser.add_argument('--with-analysis', action='store_true', help="Run analysis during scrape")
    parser.add_argument('--list-db', action='store_true', help="List all products in database")
    parser.add_argument('--stats', action='store_true', help="Show database statistics")
    
    args = parser.parse_args()
    importer = DataImporter()
    
    if args.import_raw:
        await import_raw_data()
        return
    
    if args.list_db:
        products = importer.list_all_products()
        print(f"\n📦 Products in database ({len(products)}):")
        for asin in products:
            print(f"  • {asin}")
        return
    
    if args.stats:
        stats = importer.get_stats()
        print(f"\n📊 Database Statistics:")
        print(f"  Products:  {stats['total_products']}")
        print(f"  Snapshots: {stats['total_snapshots']}")
        print(f"  Size:      {stats['total_size_mb']} MB")
        print(f"  DB Path:   {stats['db_path']}")
        print(f"  Output:    {stats['output_path']}")
        return
    
    if args.analyze_db:
        await analyze_from_db(args.analyze_db, importer)
        return
    
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

    logger.info(f"Starting scraper for {len(asin_list)} ASINs...")
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
