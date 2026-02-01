"""
Data Importer - Manage product data across multiple marketplaces.
Database structure: product_datas/{marketplace}/{ASIN}/latest.json
"""
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from .enhanced_models import EnhancedMasterProduct
from .models import MasterProduct
from .config_manager import config

logger = logging.getLogger(__name__)


class DataImporter:
    """
    Import and manage data across multiple marketplaces.
    
    Structure:
        product_datas/
        ├── us/
        │   └── B08N5KLR9X/
        │       ├── latest.json
        │       └── 2026-02-01.json
        ├── uk/
        │   └── B08N5KLR9X/
        │       └── latest.json
        └── ...
    """
    
    def __init__(
        self, 
        raw_dir: str = "dumb_datas",
        db_dir: str = None,
        output_dir: str = None,
        marketplace: str = None
    ):
        self.raw_dir = Path(raw_dir)
        self.db_dir = Path(db_dir or config.database_dir)
        self.output_dir = Path(output_dir or config.output_dir)
        self.marketplace = marketplace or self._get_marketplace_code()
        
        self.db_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        
        self.lock = asyncio.Lock()
        logger.info(f"DataImporter initialized: marketplace={self.marketplace}, db={self.db_dir}")
    
    def _get_marketplace_code(self) -> str:
        """Extract marketplace code from config."""
        mp = config.marketplace
        # amazon_us -> us, amazon_uk -> uk
        if mp.startswith("amazon_"):
            return mp.replace("amazon_", "")
        return mp
    
    def _get_asin_dir(self, asin: str, marketplace: str = None) -> Path:
        """Get or create ASIN directory for a marketplace."""
        mp = marketplace or self.marketplace
        asin_dir = self.db_dir / mp / asin
        asin_dir.mkdir(parents=True, exist_ok=True)
        return asin_dir
    
    async def import_raw_file(self, filepath: Path, marketplace: str = None) -> Optional[str]:
        """Import a single raw JSON file into the database."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'identification' not in data or 'asin' not in data.get('identification', {}):
                logger.warning(f"No ASIN found in {filepath.name}")
                return None
            
            asin = data['identification']['asin']
            mp = marketplace or self.marketplace
            
            # Add marketplace to meta if missing
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['marketplace_code'] = mp
            data['meta']['schema_version'] = '2.0.0'
            data['meta']['scraped_at'] = datetime.utcnow().isoformat()
            data['meta']['source'] = f'amazon_{mp}'
            
            product = EnhancedMasterProduct(**data)
            await self.save_product(product, marketplace=mp)
            logger.info(f"Imported {asin} to {mp}/ from {filepath.name}")
            return asin
            
        except Exception as e:
            logger.error(f"Failed to import {filepath}: {e}")
            return None
    
    async def import_all_raw(self, marketplace: str = None) -> List[str]:
        """Import all JSON files from dumb_datas."""
        if not self.raw_dir.exists():
            logger.warning(f"Raw directory not found: {self.raw_dir}")
            return []
        
        imported = []
        for filepath in self.raw_dir.glob("*.json"):
            asin = await self.import_raw_file(filepath, marketplace)
            if asin:
                imported.append(asin)
        
        mp = marketplace or self.marketplace
        logger.info(f"Imported {len(imported)} products to {mp}/")
        return imported
    
    async def save_product(
        self, 
        product: EnhancedMasterProduct,
        marketplace: str = None,
        create_snapshot: bool = True
    ) -> Path:
        """Save product to marketplace-specific database."""
        asin = product.identification.asin
        mp = marketplace or self.marketplace
        asin_dir = self._get_asin_dir(asin, mp)
        
        async with self.lock:
            product_dict = product.model_dump(mode='json', exclude_none=False)
            
            # Ensure marketplace is in meta
            if 'meta' in product_dict and product_dict['meta']:
                product_dict['meta']['marketplace_code'] = mp
            
            json_str = json.dumps(product_dict, indent=2, ensure_ascii=False)
            
            latest_path = asin_dir / "latest.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            if create_snapshot:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                snapshot_path = asin_dir / f"{today}.json"
                with open(snapshot_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            
            logger.info(f"Saved {asin} to {mp}/ database")
            return latest_path
    
    def get_product(self, asin: str, marketplace: str = None) -> Optional[EnhancedMasterProduct]:
        """Load latest product data from database."""
        mp = marketplace or self.marketplace
        latest_path = self.db_dir / mp / asin / "latest.json"
        
        if not latest_path.exists():
            logger.warning(f"Product not found: {mp}/{asin}")
            return None
        
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return EnhancedMasterProduct(**data)
        except Exception as e:
            logger.error(f"Failed to load {mp}/{asin}: {e}")
            return None
    
    def get_product_history(self, asin: str, marketplace: str = None) -> List[Path]:
        """Get all historical snapshots for a product."""
        mp = marketplace or self.marketplace
        asin_dir = self.db_dir / mp / asin
        if not asin_dir.exists():
            return []
        return sorted([f for f in asin_dir.glob("*.json") if f.name != "latest.json"])
    
    def list_all_products(self, marketplace: str = None) -> List[str]:
        """List all ASINs in a marketplace."""
        mp = marketplace or self.marketplace
        mp_dir = self.db_dir / mp
        if not mp_dir.exists():
            return []
        return sorted([d.name for d in mp_dir.iterdir() if d.is_dir()])
    
    def list_all_marketplaces(self) -> List[str]:
        """List all marketplaces with data."""
        if not self.db_dir.exists():
            return []
        return sorted([d.name for d in self.db_dir.iterdir() if d.is_dir()])
    
    async def save_report(self, report_data: dict, filename: str) -> Path:
        """Save analysis report to output/reports/."""
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = reports_dir / filename
        json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"Saved report: {filepath}")
        return filepath
    
    def get_stats(self, marketplace: str = None) -> dict:
        """Get database statistics for a marketplace or all."""
        if marketplace:
            marketplaces = [marketplace]
        else:
            marketplaces = self.list_all_marketplaces()
        
        total_products = 0
        total_snapshots = 0
        total_size = 0
        mp_stats = {}
        
        for mp in marketplaces:
            products = self.list_all_products(mp)
            mp_snapshots = 0
            mp_size = 0
            
            for asin in products:
                asin_dir = self.db_dir / mp / asin
                for f in asin_dir.glob("*.json"):
                    mp_size += f.stat().st_size
                    if f.name != "latest.json":
                        mp_snapshots += 1
            
            mp_stats[mp] = {
                "products": len(products),
                "snapshots": mp_snapshots,
                "size_mb": round(mp_size / (1024 * 1024), 2)
            }
            
            total_products += len(products)
            total_snapshots += mp_snapshots
            total_size += mp_size
        
        return {
            "total_products": total_products,
            "total_snapshots": total_snapshots,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "marketplaces": mp_stats,
            "db_path": str(self.db_dir.absolute()),
            "output_path": str(self.output_dir.absolute())
        }
