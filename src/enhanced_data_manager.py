"""
Enhanced Data Manager for LLM Training Data.
Saves comprehensive product data to product_datas/ directory.
"""
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Union
import aiofiles

from .enhanced_models import EnhancedMasterProduct
from .models import MasterProduct

logger = logging.getLogger(__name__)


class EnhancedDataManager:
    """
    Manages storage of enhanced product data for LLM training.
    Saves JSON files to product_datas/ directory with ASIN and date naming.
    """
    
    def __init__(self, base_dir: str = "product_datas"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.lock = asyncio.Lock()
        logger.info(f"EnhancedDataManager initialized: {self.base_dir.absolute()}")
    
    def _get_filename(self, asin: str, include_date: bool = True) -> str:
        """Generate filename for a product."""
        if include_date:
            today = date.today().isoformat()
            return f"{asin}_{today}.json"
        return f"{asin}.json"
    
    def _get_filepath(self, asin: str, include_date: bool = True) -> Path:
        """Get full path for a product file."""
        return self.base_dir / self._get_filename(asin, include_date)
    
    async def save_product(
        self, 
        product: Union[EnhancedMasterProduct, MasterProduct],
        with_date_suffix: bool = True,
        pretty_print: bool = True
    ) -> Path:
        """
        Save a single product to JSON file.
        
        Args:
            product: Product data to save
            with_date_suffix: If True, filename includes date (ASIN_2026-02-01.json)
            pretty_print: If True, JSON is formatted with indentation
            
        Returns:
            Path to saved file
        """
        asin = product.identification.asin
        filepath = self._get_filepath(asin, with_date_suffix)
        
        async with self.lock:
            try:
                product_dict = product.model_dump(mode='json', exclude_none=False)
                
                indent = 2 if pretty_print else None
                json_str = json.dumps(product_dict, indent=indent, ensure_ascii=False)
                
                async with aiofiles.open(filepath, mode='w', encoding='utf-8') as f:
                    await f.write(json_str)
                
                logger.info(f"Saved product {asin} to {filepath}")
                return filepath
                
            except Exception as e:
                logger.error(f"Failed to save product {asin}: {e}")
                raise
    
    async def save_batch(
        self,
        products: List[Union[EnhancedMasterProduct, MasterProduct]],
        with_date_suffix: bool = True
    ) -> List[Path]:
        """Save multiple products."""
        saved_paths = []
        for product in products:
            try:
                path = await self.save_product(product, with_date_suffix)
                saved_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to save product: {e}")
        return saved_paths
    
    async def load_product(self, asin: str, date_str: Optional[str] = None) -> Optional[EnhancedMasterProduct]:
        """
        Load a product from JSON file.
        
        Args:
            asin: Product ASIN
            date_str: Optional date (YYYY-MM-DD), defaults to today
            
        Returns:
            Loaded product or None if not found
        """
        if date_str:
            filename = f"{asin}_{date_str}.json"
        else:
            filename = self._get_filename(asin, include_date=True)
        
        filepath = self.base_dir / filename
        
        if not filepath.exists():
            filepath_no_date = self.base_dir / f"{asin}.json"
            if filepath_no_date.exists():
                filepath = filepath_no_date
            else:
                logger.warning(f"Product file not found: {filepath}")
                return None
        
        try:
            async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                content = await f.read()
            
            data = json.loads(content)
            return EnhancedMasterProduct(**data)
            
        except Exception as e:
            logger.error(f"Failed to load product {asin}: {e}")
            return None
    
    def load_product_sync(self, asin: str, date_str: Optional[str] = None) -> Optional[EnhancedMasterProduct]:
        """Synchronous version of load_product."""
        return asyncio.run(self.load_product(asin, date_str))
    
    def list_products(self, asin_filter: Optional[str] = None) -> List[Path]:
        """List all product files, optionally filtered by ASIN prefix."""
        pattern = f"{asin_filter}*.json" if asin_filter else "*.json"
        return sorted(self.base_dir.glob(pattern))
    
    def get_product_history(self, asin: str) -> List[Path]:
        """Get all historical snapshots for a product."""
        return sorted(self.base_dir.glob(f"{asin}_*.json"))
    
    async def merge_with_analysis(
        self,
        product: Union[EnhancedMasterProduct, MasterProduct],
        analysis_dict: dict
    ) -> EnhancedMasterProduct:
        """
        Merge product data with merchant analysis output.
        
        Args:
            product: Base product data
            analysis_dict: Output from AutonomousMerchantEngine.analyze()
            
        Returns:
            Enhanced product with embedded analysis
        """
        if isinstance(product, MasterProduct):
            product_dict = product.model_dump(mode='json')
            if 'meta' not in product_dict:
                product_dict['meta'] = {
                    'schema_version': '2.0.0',
                    'scraped_at': product_dict.get('scraped_at', datetime.utcnow().isoformat()),
                    'source': 'amazon_us',
                    'data_quality_score': product_dict.get('data_quality_score', 0.0)
                }
            enhanced = EnhancedMasterProduct(**product_dict)
        else:
            enhanced = product
        
        from .analysis_models import MerchantAnalysisReport
        if isinstance(analysis_dict, MerchantAnalysisReport):
            analysis_dict = analysis_dict.model_dump(mode='json')
        
        from .enhanced_models import MerchantAnalysisOutput
        enhanced.merchant_analysis = MerchantAnalysisOutput(
            arbitrage_analysis=analysis_dict.get('arbitrage_analysis'),
            private_label_analysis=analysis_dict.get('private_label_analysis'),
            risk_analysis=analysis_dict.get('risk_analysis'),
            verdict=analysis_dict.get('verdict'),
            analyzed_at=analysis_dict.get('analysis_timestamp')
        )
        
        return enhanced
    
    def get_stats(self) -> dict:
        """Get storage statistics."""
        files = list(self.base_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        
        unique_asins = set()
        for f in files:
            asin = f.stem.split('_')[0]
            unique_asins.add(asin)
        
        return {
            "total_files": len(files),
            "unique_products": len(unique_asins),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.base_dir.absolute())
        }
