import asyncio
import argparse
import logging
from typing import List

from scraper_engine import AmazonScraperEngine
from parser import AmazonParser
from data_manager import DataManager

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_asin(asin: str, engine: AmazonScraperEngine, parser: AmazonParser, manager: DataManager):
    """
    Orchestrates the scraping pipeline for a single ASIN.
    """
    try:
        html = await engine.fetch_page(asin)
        if not html:
            logger.warning(f"Skipping {asin}: No HTML fetched")
            return

        product = parser.parse(html, asin)
        if not product:
            logger.warning(f"Skipping {asin}: Parsing failed")
            return
            
        await manager.save_product(product)
        logger.info(f"Successfully processed {asin}")
        
    except Exception as e:
        logger.error(f"Unhandled error processing {asin}: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Amazon Dropshipping Scraper Skeleton")
    parser.add_argument('asins', nargs='*', help="List of ASINs to scrape")
    parser.add_argument('--file', help="File containing list of ASINs (one per line)")
    parser.add_argument('--no-headless', action='store_true', help="Run browser in headful mode")
    parser.add_argument('--output', default="products.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    asin_list = args.asins
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_asins = [line.strip() for line in f if line.strip()]
                asin_list.extend(file_asins)
        except Exception as e:
            logger.error(f"Error reading ASIN file: {e}")
            return

    if not asin_list:
        logger.error("No ASINs provided. Use arguments or --file.")
        return

    # Initialize components
    logger.info(f"Starting scraper for {len(asin_list)} ASINs...")
    data_manager = DataManager(filename=args.output)
    amazon_parser = AmazonParser()
    
    # Run Scraper
    async with AmazonScraperEngine(headless=not args.no_headless) as engine:
        tasks = []
        for asin in asin_list:
            # Add a small delay between tasks to avoid immediate massive concurrency if we were using gather
            # For this skeleton, we'll process sequentially or with specific concurrency limits 
            # to be safe against varying Playwright constraints, but here is a simple sequential await for safety
            # In a high-scale real prod env, you'd use a semaphore and asyncio.gather
            
            await process_asin(asin, engine, amazon_parser, data_manager)
            await asyncio.sleep(2) # Politeness delay

    logger.info("Scraping completed.")

if __name__ == "__main__":
    asyncio.run(main())
