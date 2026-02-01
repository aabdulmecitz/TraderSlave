"""
Enhanced Product Models for LLM Training Data.
Comprehensive schema capturing all product intelligence.
Schema Version: 2.0.0
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class MetaInfo(BaseModel):
    """Metadata about the scraped data."""
    schema_version: str = "2.0.0"
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "amazon_us"
    marketplace: str = "amazon.com"
    marketplace_code: str = "us"  # us, uk, de, fr, es, it, ca, jp
    currency: str = "USD"
    marketplace_url: str = "https://www.amazon.com"
    data_quality_score: float = Field(default=0.0, ge=0, le=1)
    scrape_duration_ms: Optional[int] = None
    proxy_region: Optional[str] = None


class Identification(BaseModel):
    """Product identification and basic info."""
    asin: str
    parent_asin: Optional[str] = None
    ean_upc: Optional[str] = None
    isbn: Optional[str] = None
    mpn: Optional[str] = None
    model_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    title: Optional[str] = None
    title_length: Optional[int] = None
    color: Optional[str] = None
    size: Optional[str] = None
    style: Optional[str] = None
    material: Optional[str] = None
    category_path: List[str] = Field(default_factory=list)
    category_id: Optional[str] = None
    product_group: Optional[str] = None


class PriceHistoryPoint(BaseModel):
    """Single price history data point."""
    date: str
    price: float
    source: str = "buybox"


class BSRHistoryPoint(BaseModel):
    """Single BSR history data point."""
    date: str
    bsr: int
    category: str


class SubcategoryRank(BaseModel):
    """BSR rank in a subcategory."""
    category: str
    rank: int


class SalesAnalytics(BaseModel):
    """Sales performance metrics."""
    bsr_current: Optional[int] = None
    bsr_category: Optional[str] = None
    bsr_90_day_avg: Optional[int] = None
    bsr_30_day_avg: Optional[int] = None
    bsr_7_day_avg: Optional[int] = None
    bsr_change_percentage: Optional[float] = None
    bsr_change_7d: Optional[float] = None
    bsr_change_30d: Optional[float] = None
    bsr_trend: Optional[str] = None
    bsr_subcategory_ranks: List[SubcategoryRank] = Field(default_factory=list)
    bsr_history: List[BSRHistoryPoint] = Field(default_factory=list)
    
    estimated_monthly_sales: Optional[int] = None
    estimated_daily_sales: Optional[float] = None
    estimated_monthly_revenue: Optional[float] = None
    estimated_yearly_revenue: Optional[float] = None
    units_sold_lifetime_est: Optional[int] = None
    
    sales_trend_7d: Optional[str] = None
    sales_trend_30d: Optional[str] = None
    sales_velocity_label: Optional[str] = None
    sales_rank_percentile: Optional[float] = None


class PricingMechanics(BaseModel):
    """Pricing information and history."""
    buy_box_price: Optional[float] = None
    currency: str = "USD"
    list_price: Optional[float] = None
    was_price: Optional[float] = None
    sale_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    
    lowest_new_price: Optional[float] = None
    lowest_used_price: Optional[float] = None
    highest_new_price: Optional[float] = None
    lowest_fba_price: Optional[float] = None
    lowest_fbm_price: Optional[float] = None
    
    price_history: List[PriceHistoryPoint] = Field(default_factory=list)
    historical_price_90d_avg: Optional[float] = None
    historical_price_90d_min: Optional[float] = None
    historical_price_90d_max: Optional[float] = None
    price_volatility_score: Optional[float] = None
    price_stability_score: Optional[float] = None
    
    map_price: Optional[float] = None
    wholesale_price_est: Optional[float] = None
    cogs_estimate: Optional[float] = None
    profit_margin_at_buybox: Optional[float] = None
    breakeven_price: Optional[float] = None
    
    amazon_referral_fee_est: Optional[float] = None
    amazon_referral_fee_pct: Optional[float] = None
    fba_fulfillment_fee: Optional[float] = None
    fba_storage_fee_monthly: Optional[float] = None
    fba_total_fee: Optional[float] = None
    
    coupon_active: bool = False
    coupon_value: Optional[str] = None
    subscribe_save_discount: Optional[float] = None
    prime_exclusive_deal: bool = False


class CompetitorInfo(BaseModel):
    """Individual competitor details."""
    seller_id: str
    seller_name: Optional[str] = None
    price: float
    rating_percentage: Optional[int] = None
    rating_count: Optional[int] = None
    is_fba: bool = False
    is_amazon: bool = False
    ships_from: Optional[str] = None
    delivery_days: Optional[int] = None
    stock_estimate: Optional[int] = None


class CompetitorStockLevel(BaseModel):
    """Competitor stock tracking."""
    seller_id: str
    stock: int
    last_updated: Optional[str] = None


class CompetitionAndInventory(BaseModel):
    """Competitive landscape analysis."""
    total_offer_count: Optional[int] = None
    new_offer_count: Optional[int] = None
    used_offer_count: Optional[int] = None
    fba_seller_count: Optional[int] = None
    fbm_seller_count: Optional[int] = None
    amazon_is_seller: bool = False
    
    buy_box_winner: Optional[str] = None
    buy_box_winner_is_fba: Optional[bool] = None
    buy_box_seller_rating: Optional[int] = None
    buy_box_ownership_pct: Optional[float] = None
    
    top_competitors: List[CompetitorInfo] = Field(default_factory=list)
    competitor_stock_levels: List[CompetitorStockLevel] = Field(default_factory=list)
    
    market_concentration: Optional[str] = None
    competitive_intensity: Optional[str] = None
    new_seller_trend_30d: Optional[str] = None
    avg_competitor_rating: Optional[float] = None
    avg_days_in_stock: Optional[int] = None
    stockout_frequency_90d: Optional[int] = None


class RatingBreakdown(BaseModel):
    """Star rating distribution."""
    five_star: Optional[int] = Field(None, alias="5_star")
    four_star: Optional[int] = Field(None, alias="4_star")
    three_star: Optional[int] = Field(None, alias="3_star")
    two_star: Optional[int] = Field(None, alias="2_star")
    one_star: Optional[int] = Field(None, alias="1_star")


class ReviewSample(BaseModel):
    """Individual review sample for training."""
    stars: int
    title: str
    snippet: str
    full_text: Optional[str] = None
    verified_purchase: bool = True
    helpful_votes: Optional[int] = None
    date: Optional[str] = None
    reviewer_id: Optional[str] = None


class ReviewHistoryPoint(BaseModel):
    """Review count history."""
    date: str
    review_count: int
    avg_rating: float


class SentimentAndQuality(BaseModel):
    """Customer sentiment and review analysis."""
    rating_overall: Optional[float] = None
    rating_recent_trend: Optional[str] = None
    review_count: Optional[int] = None
    review_count_verified: Optional[int] = None
    review_velocity_monthly: Optional[int] = None
    review_velocity_weekly: Optional[int] = None
    
    rating_breakdown: Optional[RatingBreakdown] = None
    rating_history: List[ReviewHistoryPoint] = Field(default_factory=list)
    
    top_positive_keywords: List[str] = Field(default_factory=list)
    top_negative_keywords: List[str] = Field(default_factory=list)
    common_complaints: List[str] = Field(default_factory=list)
    common_praises: List[str] = Field(default_factory=list)
    
    review_samples_positive: List[ReviewSample] = Field(default_factory=list)
    review_samples_negative: List[ReviewSample] = Field(default_factory=list)
    review_samples_neutral: List[ReviewSample] = Field(default_factory=list)
    
    sentiment_score: Optional[float] = None
    recent_review_sentiment: Optional[str] = None
    review_authenticity_score: Optional[float] = None
    
    image_review_count: Optional[int] = None
    video_review_count: Optional[int] = None
    answered_questions_count: Optional[int] = None
    unanswered_questions_count: Optional[int] = None
    
    top_questions: List[str] = Field(default_factory=list)


class Dimensions(BaseModel):
    """Physical dimensions."""
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    unit: str = "cm"


class LogisticsAndPhysical(BaseModel):
    """Physical attributes and logistics."""
    item_weight_grams: Optional[float] = None
    item_weight_oz: Optional[float] = None
    package_weight_grams: Optional[float] = None
    package_weight_oz: Optional[float] = None
    
    item_dimensions: Optional[Dimensions] = None
    package_dimensions: Optional[Dimensions] = None
    dimensions_cm: Optional[Dimensions] = None
    
    volume_cubic_cm: Optional[float] = None
    volume_cubic_inches: Optional[float] = None
    dimensional_weight: Optional[float] = None
    
    size_tier: Optional[str] = None
    shipping_tier: Optional[str] = None
    is_oversize: bool = False
    
    is_hazmat: bool = False
    is_fragile: bool = False
    is_meltable: bool = False
    is_adult_product: bool = False
    requires_special_handling: bool = False
    
    origin_country: Optional[str] = None
    made_in: Optional[str] = None
    assembly_required: bool = False
    batteries_required: bool = False
    batteries_included: bool = False


class ListingQuality(BaseModel):
    """SEO and listing optimization metrics."""
    title_length: Optional[int] = None
    title_word_count: Optional[int] = None
    title_keyword_count: Optional[int] = None
    title_brand_position: Optional[int] = None
    
    bullet_count: Optional[int] = None
    bullet_avg_length: Optional[int] = None
    bullets_use_keywords: bool = False
    
    description_length: Optional[int] = None
    description_word_count: Optional[int] = None
    
    image_count: Optional[int] = None
    image_has_infographic: bool = False
    image_has_lifestyle: bool = False
    image_quality_score: Optional[float] = None
    
    video_count: Optional[int] = None
    video_exists: bool = False
    
    a_plus_content_exists: bool = False
    a_plus_modules: Optional[int] = None
    a_plus_type: Optional[str] = None
    
    brand_story_exists: bool = False
    brand_registered: bool = False
    
    listing_score: Optional[int] = None
    seo_score: Optional[int] = None
    seo_issues: List[str] = Field(default_factory=list)
    seo_recommendations: List[str] = Field(default_factory=list)
    
    mobile_optimized: bool = True
    enhanced_content: bool = False


class ContentAssets(BaseModel):
    """Media and content assets."""
    main_image_url: Optional[str] = None
    gallery_images: List[str] = Field(default_factory=list)
    video_urls: List[str] = Field(default_factory=list)
    
    bullet_points: List[str] = Field(default_factory=list)
    description_text: Optional[str] = None
    description_html: Optional[str] = None
    
    from_manufacturer: Optional[str] = None
    technical_specifications: Dict[str, str] = Field(default_factory=dict)
    
    important_information: Optional[str] = None
    warranty_info: Optional[str] = None
    safety_warnings: Optional[str] = None


class VariationInfo(BaseModel):
    """Individual product variation."""
    asin: str
    attribute_name: Optional[str] = None
    attribute_value: Optional[str] = None
    price: Optional[float] = None
    in_stock: bool = True
    is_current: bool = False


class Variations(BaseModel):
    """Product variation data."""
    is_variation_parent: bool = False
    is_variation_child: bool = False
    parent_asin: Optional[str] = None
    variation_count: Optional[int] = None
    variation_theme: Optional[str] = None
    variation_dimensions: List[str] = Field(default_factory=list)
    all_variations: List[VariationInfo] = Field(default_factory=list)
    best_selling_variation: Optional[str] = None


class DemandSignals(BaseModel):
    """Market demand indicators."""
    search_volume_main_kw: Optional[int] = None
    search_volume_trend: Optional[str] = None
    keyword_difficulty: Optional[int] = None
    organic_keyword_count: Optional[int] = None
    sponsored_keyword_count: Optional[int] = None
    
    google_trends_score: Optional[int] = None
    google_trends_trend: Optional[str] = None
    
    trending_direction: Optional[str] = None
    seasonality_label: Optional[str] = None
    seasonal_index: List[float] = Field(default_factory=list)
    peak_months: List[int] = Field(default_factory=list)
    
    frequently_bought_together: List[str] = Field(default_factory=list)
    customers_also_viewed: List[str] = Field(default_factory=list)
    related_products: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk and compliance analysis."""
    ip_infringement_risk: Optional[str] = None
    trademark_protection: Optional[str] = None
    brand_gating: bool = False
    category_gating: bool = False
    
    return_rate_estimated: Optional[float] = None
    return_rate_vs_category: Optional[str] = None
    
    seasonal_factor: Optional[str] = None
    demand_volatility: Optional[str] = None
    supply_chain_risk: Optional[str] = None
    
    counterfeit_risk: Optional[str] = None
    review_manipulation_risk: Optional[str] = None
    listing_hijack_risk: Optional[str] = None
    
    regulatory_requirements: List[str] = Field(default_factory=list)
    certifications_required: List[str] = Field(default_factory=list)
    
    overall_risk_score: Optional[float] = None
    risk_flags: List[str] = Field(default_factory=list)


class ProfitScenario(BaseModel):
    """Profit calculation for a scenario."""
    scenario_name: str
    buy_price: float
    sell_price: float
    total_fees: float
    profit: float
    roi_percentage: float
    margin_percentage: float


class ProfitCalculations(BaseModel):
    """Comprehensive profit analysis."""
    estimated_cogs: Optional[float] = None
    target_cogs_25pct: Optional[float] = None
    target_cogs_30pct: Optional[float] = None
    
    fba_fee_breakdown: Dict[str, float] = Field(default_factory=dict)
    total_amazon_fees: Optional[float] = None
    fees_as_pct_of_price: Optional[float] = None
    
    breakeven_price: Optional[float] = None
    minimum_viable_price: Optional[float] = None
    
    profit_at_buybox: Optional[float] = None
    profit_at_lowest: Optional[float] = None
    
    profit_scenarios: List[ProfitScenario] = Field(default_factory=list)
    
    recommended_sell_price: Optional[float] = None
    recommended_max_buy_price: Optional[float] = None


class MerchantAnalysisOutput(BaseModel):
    """Embedded merchant engine analysis."""
    arbitrage_analysis: Optional[Dict[str, Any]] = None
    private_label_analysis: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    verdict: Optional[Dict[str, Any]] = None
    analyzed_at: Optional[str] = None


class EnhancedMasterProduct(BaseModel):
    """
    Comprehensive product data model for LLM training.
    Schema Version: 2.0.0
    """
    meta: MetaInfo = Field(default_factory=MetaInfo)
    identification: Identification
    sales_analytics: Optional[SalesAnalytics] = None
    pricing_mechanics: Optional[PricingMechanics] = None
    competition_and_inventory: Optional[CompetitionAndInventory] = None
    sentiment_and_quality: Optional[SentimentAndQuality] = None
    logistics_and_physical: Optional[LogisticsAndPhysical] = None
    listing_quality: Optional[ListingQuality] = None
    content_assets: Optional[ContentAssets] = None
    variations: Optional[Variations] = None
    demand_signals: Optional[DemandSignals] = None
    risk_assessment: Optional[RiskAssessment] = None
    profit_calculations: Optional[ProfitCalculations] = None
    merchant_analysis: Optional[MerchantAnalysisOutput] = None
    
    class Config:
        populate_by_name = True
