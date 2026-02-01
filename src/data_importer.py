"""
Data Importer - Import raw data from dumb_datas to product_datas database.
"""
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from .enhanced_models import EnhancedMasterProduct
from .models import MasterProduct

logger = logging.getLogger(__name__)


class DataImporter:
    """
    Import and manage data from dumb_datas to product_datas database.
    
    Structure:
        product_datas/
        ├── B08N5KLR9X/
        │   ├── latest.json         # Current complete data
        │   └── 2026-02-01.json     # Historical snapshot
        └── ...
    """
    
    def __init__(
        self, 
        raw_dir: str = "dumb_datas",
        db_dir: str = "product_datas",
        output_dir: str = "output"
    ):
        self.raw_dir = Path(raw_dir)
        self.db_dir = Path(db_dir)
        self.output_dir = Path(output_dir)
        
        self.db_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        
        self.lock = asyncio.Lock()
        logger.info(f"DataImporter initialized: raw={self.raw_dir}, db={self.db_dir}")
    
    def _get_asin_dir(self, asin: str) -> Path:
        """Get or create ASIN directory."""
        asin_dir = self.db_dir / asin
        asin_dir.mkdir(parents=True, exist_ok=True)
        return asin_dir
    
    async def import_raw_file(self, filepath: Path) -> Optional[str]:
        """Import a single raw JSON file into the database."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'identification' not in data or 'asin' not in data.get('identification', {}):
                logger.warning(f"No ASIN found in {filepath.name}")
                return None
            
            asin = data['identification']['asin']
            
            if 'meta' in data:
                product = EnhancedMasterProduct(**data)
            else:
                product = MasterProduct(**data)
                data['meta'] = {
                    'schema_version': '2.0.0',
                    'scraped_at': datetime.utcnow().isoformat(),
                    'source': 'imported',
                    'data_quality_score': data.get('data_quality_score', 0.5)
                }
                product = EnhancedMasterProduct(**data)
            
            await self.save_product(product)
            logger.info(f"Imported {asin} from {filepath.name}")
            return asin
            
        except Exception as e:
            logger.error(f"Failed to import {filepath}: {e}")
            return None
    
    async def import_all_raw(self) -> List[str]:
        """Import all JSON files from dumb_datas."""
        if not self.raw_dir.exists():
            logger.warning(f"Raw directory not found: {self.raw_dir}")
            return []
        
        imported = []
        for filepath in self.raw_dir.glob("*.json"):
            asin = await self.import_raw_file(filepath)
            if asin:
                imported.append(asin)
        
        logger.info(f"Imported {len(imported)} products from dumb_datas/")
        return imported
    
    async def save_product(
        self, 
        product: EnhancedMasterProduct,
        create_snapshot: bool = True
    ) -> Path:
        """Save product to database (latest.json + optional dated snapshot)."""
        asin = product.identification.asin
        asin_dir = self._get_asin_dir(asin)
        
        async with self.lock:
            product_dict = product.model_dump(mode='json', exclude_none=False)
            json_str = json.dumps(product_dict, indent=2, ensure_ascii=False)
            
            latest_path = asin_dir / "latest.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            if create_snapshot:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                snapshot_path = asin_dir / f"{today}.json"
                with open(snapshot_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            
            logger.info(f"Saved {asin} to database")
            return latest_path
    
    def get_product(self, asin: str) -> Optional[EnhancedMasterProduct]:
        """Load latest product data from database."""
        latest_path = self.db_dir / asin / "latest.json"
        
        if not latest_path.exists():
            logger.warning(f"Product not found in database: {asin}")
            return None
        
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return EnhancedMasterProduct(**data)
        except Exception as e:
            logger.error(f"Failed to load {asin}: {e}")
            return None
    
    def get_product_history(self, asin: str) -> List[Path]:
        """Get all historical snapshots for a product."""
        asin_dir = self.db_dir / asin
        if not asin_dir.exists():
            return []
        return sorted([f for f in asin_dir.glob("*.json") if f.name != "latest.json"])
    
    def list_all_products(self) -> List[str]:
        """List all ASINs in the database."""
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
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        products = self.list_all_products()
        
        total_size = 0
        total_snapshots = 0
        for asin in products:
            asin_dir = self.db_dir / asin
            for f in asin_dir.glob("*.json"):
                total_size += f.stat().st_size
                if f.name != "latest.json":
                    total_snapshots += 1
        
        return {
            "total_products": len(products),
            "total_snapshots": total_snapshots,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "db_path": str(self.db_dir.absolute()),
            "output_path": str(self.output_dir.absolute())
        }
