import asyncio
import json
import logging
from pathlib import Path
from typing import List
import aiofiles
from .models import MasterProduct

logger = logging.getLogger(__name__)

class DataManager:
    """
    Handles asynchronous file I/O for storing product data.
    Ensures data integrity during saves.
    """
    def __init__(self, filename: str = "products.json"):
        self.filename = filename
        self.lock = asyncio.Lock()

    async def _read_file(self) -> List[dict]:
        path = Path(self.filename)
        if not path.exists():
            return []
        
        try:
            async with aiofiles.open(self.filename, mode='r') as f:
                content = await f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Corrupt JSON in {self.filename}, backing up and starting fresh.")
            if path.exists():
                path.rename(f"{self.filename}.bak")
            return []
        except Exception as e:
            logger.error(f"Error reading {self.filename}: {e}")
            return []

    async def save_product(self, product: MasterProduct):
        """Thread-safe append of a single product to the JSON array."""
        async with self.lock:
            data = await self._read_file()
            product_dict = product.model_dump(mode='json')
            data.append(product_dict)
            
            try:
                temp_filename = f"{self.filename}.tmp"
                async with aiofiles.open(temp_filename, mode='w') as f:
                    await f.write(json.dumps(data, indent=2))
                
                Path(temp_filename).replace(self.filename)
                logger.info(f"Saved product {product.identification.asin} to {self.filename}")
            except Exception as e:
                logger.error(f"Failed to save product: {e}")

    async def save_batch(self, products: List[MasterProduct]):
        """Thread-safe batch save."""
        async with self.lock:
            data = await self._read_file()
            for p in products:
                data.append(p.model_dump(mode='json'))
            
            try:
                temp_filename = f"{self.filename}.tmp"
                async with aiofiles.open(temp_filename, mode='w') as f:
                    await f.write(json.dumps(data, indent=2))
                Path(temp_filename).replace(self.filename)
                logger.info(f"Saved batch of {len(products)} products to {self.filename}")
            except Exception as e:
                logger.error(f"Failed to save batch: {e}")
