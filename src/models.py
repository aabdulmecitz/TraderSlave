from __future__ import annotations
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class Identification(BaseModel):
    asin: str
    parent_asin: Optional[str] = None
    ean_upc: Optional[str] = None
    mpn: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    title: Optional[str] = None
    category_path: List[str] = Field(default_factory=list)

class SalesAnalytics(BaseModel):
    bsr_current: Optional[int] = None
    bsr_category: Optional[str] = None
    bsr_90_day_avg: Optional[int] = None
    bsr_change_percentage: Optional[float] = None
    estimated_monthly_sales: Optional[int] = None
    estimated_monthly_revenue: Optional[float] = None
    sales_velocity_label: Optional[str] = None

class PricingMechanics(BaseModel):
    buy_box_price: Optional[float] = None
    currency: str = "USD"
    list_price: Optional[float] = None
    discount_percentage: Optional[int] = None
    lowest_new_price: Optional[float] = None
    highest_new_price: Optional[float] = None
    historical_price_90d_avg: Optional[float] = None
    price_stability_score: Optional[float] = None
    amazon_referral_fee_est: Optional[float] = None

class CompetitorStockLevel(BaseModel):
    seller_id: str
    stock: int

class CompetitionAndInventory(BaseModel):
    total_offer_count: Optional[int] = None
    fba_seller_count: Optional[int] = None
    fbm_seller_count: Optional[int] = None
    amazon_is_seller: bool = False
    buy_box_winner: Optional[str] = None
    competitor_stock_levels: List[CompetitorStockLevel] = Field(default_factory=list)
    new_seller_trend_30d: Optional[str] = None

class RatingBreakdown(BaseModel):
    five_star: Optional[int] = Field(None, alias="5_star")
    four_star: Optional[int] = Field(None, alias="4_star")
    three_star: Optional[int] = Field(None, alias="3_star")
    two_star: Optional[int] = Field(None, alias="2_star")
    one_star: Optional[int] = Field(None, alias="1_star")

class SentimentAndQuality(BaseModel):
    rating_overall: Optional[float] = None
    review_count: Optional[int] = None
    review_velocity_monthly: Optional[int] = None
    rating_breakdown: Optional[RatingBreakdown] = None
    top_positive_keywords: List[str] = Field(default_factory=list)
    top_negative_keywords: List[str] = Field(default_factory=list)
    recent_review_sentiment: Optional[str] = None
    image_review_count: Optional[int] = None
    video_review_count: Optional[int] = None
    answered_questions_count: Optional[int] = None

class Dimensions(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

class LogisticsAndPhysical(BaseModel):
    item_weight_grams: Optional[float] = None
    package_weight_grams: Optional[float] = None
    dimensions_cm: Optional[Dimensions] = None
    is_hazmat: bool = False
    is_adult_product: bool = False
    shipping_tier: Optional[str] = None
    origin_country: Optional[str] = None

class ContentAssets(BaseModel):
    main_image_url: Optional[str] = None
    gallery_images: List[str] = Field(default_factory=list)
    bullet_points: List[str] = Field(default_factory=list)
    description_text: Optional[str] = None
    a_plus_content_exists: bool = False

class RiskAssessment(BaseModel):
    ip_infringement_risk: Optional[str] = None
    trademark_protection: Optional[str] = None
    return_rate_estimated: Optional[float] = None
    seasonal_factor: Optional[str] = None

class MasterProduct(BaseModel):
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: Optional[float] = None
    
    identification: Identification
    sales_analytics: Optional[SalesAnalytics] = None
    pricing_mechanics: Optional[PricingMechanics] = None
    competition_and_inventory: Optional[CompetitionAndInventory] = None
    sentiment_and_quality: Optional[SentimentAndQuality] = None
    logistics_and_physical: Optional[LogisticsAndPhysical] = None
    content_assets: Optional[ContentAssets] = None
    risk_assessment: Optional[RiskAssessment] = None
