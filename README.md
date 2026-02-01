# TraderSlave 🚀

Amazon Product Intelligence Engine - Scrape, analyze, and evaluate products for arbitrage and private label opportunities.

## Quick Start

### 1. Configure (Optional)
Edit `config/scraping_config.json` to customize:
- **Marketplace**: Amazon US, UK, DE, FR, ES, IT, CA, JP
- **Timeouts and retries**
- **User agents**

```json
{
  "scraper": {
    "base_url": "https://www.amazon.com/dp/",
    "marketplace": "amazon_us",
    "headless": true,
    "timeout_ms": 30000
  }
}
```

### 2. Add ASINs
```bash
echo "B08N5KLR9X" >> asins.txt
echo "B017OEL8P0" >> asins.txt
```

### 3. Run Scraper
```bash
# With Docker
docker compose up scraper

# Or locally
python -m src.main --file asins.txt --with-analysis
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m src.main B08N5KLR9X` | Scrape single ASIN |
| `python -m src.main --file asins.txt` | Scrape from file |
| `python -m src.main --with-analysis B08N5KLR9X` | Scrape + analyze |
| `python -m src.main --analyze-db B08N5KLR9X` | Analyze from database |
| `python -m src.main --list-db` | List all products |
| `python -m src.main --stats` | Database statistics |

## Project Structure

```
TraderSlave/
├── config/
│   └── scraping_config.json    # ⚙️ Configuration
├── src/
│   ├── main.py                 # CLI entry point
│   ├── scraper_engine.py       # Playwright scraper
│   ├── parser.py               # HTML parser
│   ├── merchant_engine.py      # Analysis engine
│   ├── config_manager.py       # Config loader
│   ├── data_importer.py        # Database manager
│   ├── models.py               # Core schemas
│   └── enhanced_models.py      # LLM training schemas
├── product_datas/              # 📦 Product database
│   └── {ASIN}/
│       ├── latest.json
│       └── YYYY-MM-DD.json
├── output/reports/             # 📊 Analysis reports
├── dumb_datas/                 # 📋 Sample templates
└── docker-compose.yml
```

## Configuration

### Supported Marketplaces

| Marketplace | Config Value |
|-------------|--------------|
| Amazon US | `amazon_us` |
| Amazon UK | `amazon_uk` |
| Amazon Germany | `amazon_de` |
| Amazon France | `amazon_fr` |
| Amazon Spain | `amazon_es` |
| Amazon Italy | `amazon_it` |
| Amazon Canada | `amazon_ca` |
| Amazon Japan | `amazon_jp` |

To change marketplace, edit `config/scraping_config.json`:
```json
{
  "scraper": {
    "base_url": "https://www.amazon.co.uk/dp/",
    "marketplace": "amazon_uk"
  }
}
```

## Docker Commands

```bash
# Scrape ASINs from file
docker compose up scraper

# View database stats
docker compose --profile stats up stats

# Run tests
docker compose --profile test up test

# Rebuild after config changes
docker compose up --build scraper
```

## Analysis Output

The merchant engine analyzes:
- **Arbitrage**: Net profit, ROI, margin, BuyBox risk
- **Private Label**: PL Score, sentiment gaps, improvement opportunities
- **Risk**: IP risk, price wars, return rates, seasonality

Verdicts: `GO`, `CONDITIONAL`, or `NO-GO` for each business model.

## Testing

```bash
# Local
python test_engine.py

# Docker
docker compose --profile test up test
```

## Requirements

- Python 3.10+
- Playwright
- Pydantic 2.x
- Docker (optional)
