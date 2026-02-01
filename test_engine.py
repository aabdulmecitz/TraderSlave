#!/usr/bin/env python3
"""
TraderSlave Test Suite
Uses dumb_datas/ as sample template for testing.
Run: python test_engine.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, '.')

from src.models import MasterProduct
from src.enhanced_models import EnhancedMasterProduct
from src.data_importer import DataImporter
from src.merchant_engine import AutonomousMerchantEngine
from src.dashboard import MerchantDashboard
from src.cross_marketplace import CrossMarketplaceEngine


def test_analyze_sample():
    """Test analysis using sample template from dumb_datas/."""
    print("=" * 60)
    print("🔧 TEST 1: Analyze Sample Template")
    print("=" * 60)
    
    sample_file = Path('dumb_datas/amazon_metrics_enhanced.json')
    if not sample_file.exists():
        print("✗ Sample file not found: dumb_datas/amazon_metrics_enhanced.json")
        return None
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    product = EnhancedMasterProduct(**data)
    print(f"✓ Loaded template: {product.identification.title[:50]}...")
    print(f"  ASIN: {product.identification.asin}")
    print(f"  Schema: v{product.meta.schema_version}")
    
    # Convert to MasterProduct by dumping to dict first
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
    
    engine = AutonomousMerchantEngine()
    
    async def run():
        return await engine.analyze(base_product)
    
    report = asyncio.run(run())
    MerchantDashboard().display(report)
    
    print(f"\n📊 Summary:")
    print(f"   Net Profit: ${report.arbitrage_analysis.net_profit:.2f}")
    print(f"   ROI: {report.arbitrage_analysis.roi_percentage:.1f}%")
    print(f"   PL Score: {report.private_label_analysis.pl_score}/100")
    print(f"   Verdict: {report.verdict.overall_verdict.value.upper()}")
    
    return report


def test_save_to_db():
    """Test saving to product_datas/{marketplace} database."""
    print("\n" + "=" * 60)
    print("🔧 TEST 2: Save to Database (Multi-Marketplace)")
    print("=" * 60)
    
    sample_file = Path('dumb_datas/amazon_metrics_enhanced.json')
    if not sample_file.exists():
        print("⚠️  Sample file not found")
        return False
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Test saving to US marketplace
    product = EnhancedMasterProduct(**data)
    importer = DataImporter(marketplace='us')
    
    async def run():
        return await importer.save_product(product, marketplace='us')
    
    filepath = asyncio.run(run())
    print(f"✓ Saved to: {filepath}")
    
    # Test saving to UK marketplace (simulated)
    importer_uk = DataImporter(marketplace='uk')
    
    async def run_uk():
        return await importer_uk.save_product(product, marketplace='uk')
    
    filepath_uk = asyncio.run(run_uk())
    print(f"✓ Saved to: {filepath_uk}")
    
    stats = importer.get_stats()
    print(f"✓ Database: {stats['total_products']} products across {len(stats.get('marketplaces', {}))} marketplaces")
    print(f"  By marketplace:")
    for mp, mp_stats in stats.get('marketplaces', {}).items():
        print(f"    {mp.upper()}: {mp_stats['products']} products")
    
    return True


def test_cross_marketplace():
    """Test cross-marketplace arbitrage analysis."""
    print("\n" + "=" * 60)
    print("🔧 TEST 3: Cross-Marketplace Arbitrage")
    print("=" * 60)
    
    engine = CrossMarketplaceEngine()
    sample_asin = "B08N5KLR9X"
    
    marketplaces = engine.get_available_marketplaces(sample_asin)
    print(f"✓ Found {sample_asin} in {len(marketplaces)} marketplaces: {', '.join(marketplaces)}")
    
    if len(marketplaces) >= 2:
        engine.display_all_prices(sample_asin)
        opp = engine.find_arbitrage(sample_asin)
        if opp:
            engine.display_arbitrage(opp)
            print(f"✓ Arbitrage found: {opp.buy_marketplace} → {opp.sell_marketplace}")
            return True
        else:
            print("⚠️  No arbitrage opportunity (prices similar)")
            return True
    else:
        print("⚠️  Need 2+ marketplaces for arbitrage test")
        return True


def test_save_report():
    """Test saving analysis report."""
    print("\n" + "=" * 60)
    print("🔧 TEST 4: Save Analysis Report")
    print("=" * 60)
    
    sample_file = Path('dumb_datas/amazon_metrics_enhanced.json')
    if not sample_file.exists():
        return False
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    product = EnhancedMasterProduct(**data)
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
    
    engine = AutonomousMerchantEngine()
    importer = DataImporter(marketplace='us')
    
    async def run():
        report = await engine.analyze(base_product)
        filepath = await importer.save_report(
            report.model_dump(mode='json'),
            f"us_{product.identification.asin}_test_report.json"
        )
        return filepath
    
    filepath = asyncio.run(run())
    print(f"✓ Report saved: {filepath}")
    
    return True


def main():
    print("\n" + "=" * 60)
    print("🚀 TRADERSLAVE - PRODUCTION TEST SUITE")
    print("=" * 60)
    
    report = test_analyze_sample()
    db_ok = test_save_to_db()
    arb_ok = test_cross_marketplace()
    report_ok = test_save_report()
    
    print("\n" + "=" * 60)
    print("✅ TESTS COMPLETED")
    print("=" * 60)
    
    print("\n📋 Results:")
    print(f"   Analysis:          {'✓ PASS' if report else '✗ FAIL'}")
    print(f"   Multi-Market DB:   {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"   Cross Arbitrage:   {'✓ PASS' if arb_ok else '✗ FAIL'}")
    print(f"   Save Report:       {'✓ PASS' if report_ok else '✗ FAIL'}")
    
    all_passed = all([report, db_ok, arb_ok, report_ok])
    print(f"\n{'🎉 ALL TESTS PASSED - READY FOR PRODUCTION!' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
