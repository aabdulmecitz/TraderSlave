# TraderSlave 🚀

Multi-Marketplace Amazon Intelligence Engine - Find profitable products across global Amazon marketplaces.

## 🌍 Features

- **Multi-Marketplace Scraping**: US, UK, DE, FR, ES, IT, CA, JP
- **Cross-Marketplace Arbitrage**: Find buy low / sell high opportunities
- **Trend Detection**: BSR velocity, review momentum analysis
- **Profit Calculator**: ROI, margins, FBA fee estimation
- **Private Label Analysis**: Gap detection, competition scoring

## Quick Start

### 1. Configure Marketplaces
Edit `config/scraping_config.json`:
```json
{
  "enabled_marketplaces": ["us", "uk", "de", "jp"]
}
```

### 2. Add ASINs
```bash
echo "B08N5KLR9X" >> asins.txt
```

### 3. Scrape Across Marketplaces
```bash
# Scrape same product in US, UK, DE
python -m src.main --multi us,uk,de B08N5KLR9X

# Find arbitrage opportunities
python -m src.main --cross-arbitrage B08N5KLR9X
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `--marketplace uk ASIN` | Scrape to specific marketplace |
| `--multi us,uk,de ASIN` | Scrape across multiple marketplaces |
| `--cross-arbitrage ASIN` | Find cross-market arbitrage |
| `--analyze-db ASIN` | Analyze from database |
| `--with-analysis ASIN` | Scrape + analyze |
| `--list-db` | List all products |
| `--stats` | Database statistics |

## Database Structure

```
product_datas/
├── us/                    # 🇺🇸 Amazon.com
│   └── B08N5KLR9X/
│       ├── latest.json
│       └── 2026-02-01.json
├── uk/                    # 🇬🇧 Amazon.co.uk
│   └── B08N5KLR9X/
│       └── latest.json
└── de/                    # 🇩🇪 Amazon.de
    └── B08N5KLR9X/
        └── latest.json
```

## Cross-Marketplace Arbitrage

```
🌍 CROSS-MARKETPLACE ARBITRAGE: B08N5KLR9X
============================================================
📦 AeroPress Clear Coffee Maker

  💰 BUY FROM:  🇬🇧 UK
     Price: GBP 28.99 ($36.50)

  📤 SELL ON:   🇯🇵 JP
     Price: JPY 5,980 ($40.12)

  📊 PROFIT:    $3.62 (9.9% margin)

  🟢 STRONG BUY - Excellent arbitrage opportunity
```

## Docker

```bash
# Scrape from file
docker compose up scraper

# Stats
docker compose --profile stats up stats

# Test
docker compose --profile test up test
```

## Supported Marketplaces

| Flag | Code | Site |
|------|------|------|
| 🇺🇸 | us | amazon.com |
| 🇬🇧 | uk | amazon.co.uk |
| 🇩🇪 | de | amazon.de |
| 🇫🇷 | fr | amazon.fr |
| 🇪🇸 | es | amazon.es |
| 🇮🇹 | it | amazon.it |
| 🇨🇦 | ca | amazon.ca |
| 🇯🇵 | jp | amazon.co.jp |
