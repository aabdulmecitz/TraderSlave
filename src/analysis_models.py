"""
Analysis Output Models for Autonomous Merchant Engine.
Contains Pydantic models for structured analysis results.
"""
from __future__ import annotations
from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VelocityGrade(str, Enum):
    SPRINTER = "sprinter"
    STEADY = "steady"
    SLOW = "slow"


class Verdict(str, Enum):
    GO = "go"
    NO_GO = "no_go"
    CONDITIONAL = "conditional"


class ArbitrageAnalysis(BaseModel):
    """Arbitrage and Dropshipping profitability analysis."""
    buy_box_price: float = Field(description="Current BuyBox price")
    amazon_fees: float = Field(description="Estimated Amazon referral fees")
    fba_costs: float = Field(description="Estimated FBA storage + fulfillment")
    overhead_cost: float = Field(description="15% operational overhead")
    net_profit: float = Field(description="Net profit after all deductions")
    roi_percentage: float = Field(description="Return on Investment %")
    margin_percentage: float = Field(description="Profit margin %")
    
    buybox_risk_level: RiskLevel = Field(description="BuyBox competition risk")
    amazon_is_seller: bool = Field(description="Whether Amazon is a direct seller")
    fba_seller_count: int = Field(description="Number of FBA sellers")
    total_offer_count: int = Field(description="Total seller offers")
    
    velocity_grade: VelocityGrade = Field(description="Capital churn speed")
    bsr_trend: str = Field(description="BSR trend direction")
    estimated_monthly_sales: int = Field(description="Estimated monthly units sold")
    capital_turnover_days: Optional[int] = Field(None, description="Estimated days to sell through")


class SentimentGap(BaseModel):
    """Identified gap from negative sentiment analysis."""
    keyword: str
    frequency_score: float = Field(default=1.0, description="Relative frequency 0-10")
    improvement_potential: str = Field(description="Suggested improvement area")


class PrivateLabelAnalysis(BaseModel):
    """Private Label opportunity analysis."""
    pl_score: int = Field(ge=0, le=100, description="PL Opportunity Score 0-100")
    pl_score_breakdown: dict = Field(description="Score component breakdown")
    
    sentiment_gaps: List[SentimentGap] = Field(default_factory=list)
    has_improvement_opportunity: bool = Field(description="High sales + negative sentiment")
    
    target_cogs: float = Field(description="Target manufacturing cost (25% of list)")
    projected_pl_margin: float = Field(description="Projected PL profit margin %")
    projected_pl_profit: float = Field(description="Projected profit per unit")
    
    market_demand_signals: dict = Field(description="Demand indicators")
    competition_level: RiskLevel = Field(description="Market competition level")


class RiskAnalysis(BaseModel):
    """Risk and defensive analysis."""
    ip_risk_level: RiskLevel = Field(description="IP/Trademark infringement risk")
    ip_auto_reject: bool = Field(description="Whether to auto-reject due to IP")
    
    price_stability_score: float = Field(ge=0, le=1, description="Price stability 0-1")
    price_war_detected: bool = Field(description="Active price war indicator")
    
    return_rate_risk: RiskLevel = Field(description="Return rate risk level")
    seasonal_risk: str = Field(description="Seasonal dependency factor")
    
    overall_risk_score: float = Field(ge=0, le=100, description="Aggregate risk 0-100")
    risk_flags: List[str] = Field(default_factory=list, description="Active risk warnings")


class BusinessModelVerdict(BaseModel):
    """Final Go/No-Go verdicts for each business model."""
    arbitrage_verdict: Verdict
    arbitrage_reason: str
    
    dropshipping_verdict: Verdict
    dropshipping_reason: str
    
    private_label_verdict: Verdict
    private_label_reason: str
    
    recommended_model: Optional[str] = Field(None, description="Best recommended approach")
    overall_verdict: Verdict
    summary: str


class MerchantAnalysisReport(BaseModel):
    """Complete analysis report container."""
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    
    arbitrage_analysis: ArbitrageAnalysis
    private_label_analysis: PrivateLabelAnalysis
    risk_analysis: RiskAnalysis
    verdict: BusinessModelVerdict
    
    data_quality_score: float = Field(description="Input data quality 0-1")
    analysis_timestamp: str
    engine_version: str = "1.0.0"
