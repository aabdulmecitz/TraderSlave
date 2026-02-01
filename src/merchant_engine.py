"""
Autonomous Merchant Engine - AI-Powered Product Analysis.
Calculates profitability, assesses risks, and determines optimal business models.
No external API dependencies - pure mathematical and heuristic logic.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from .models import MasterProduct
from .analysis_models import (
    MerchantAnalysisReport,
    ArbitrageAnalysis,
    PrivateLabelAnalysis,
    RiskAnalysis,
    BusinessModelVerdict,
    SentimentGap,
    RiskLevel,
    VelocityGrade,
    Verdict,
)

logger = logging.getLogger(__name__)


class AutonomousMerchantEngine:
    """
    AI Autonomous Merchant Intelligence Engine.
    Processes Amazon product data to calculate profitability, 
    assess risks, and recommend business models (RA, Dropshipping, PL).
    """
    
    OVERHEAD_PERCENTAGE: float = 0.15
    FBA_BASE_FULFILLMENT: float = 3.00
    FBA_WEIGHT_RATE: float = 0.50
    FBA_STORAGE_PER_CUBIC_FOOT: float = 0.75
    PL_COGS_TARGET_RATIO: float = 0.25
    
    VELOCITY_THRESHOLDS = {
        "sprinter": {"bsr_change": -10, "monthly_sales": 500},
        "steady": {"bsr_change": 0, "monthly_sales": 200},
    }
    
    PL_WEIGHTS = {
        "velocity": 0.30,
        "rating_gap": 0.25,
        "competition": 0.25,
        "review_momentum": 0.20,
    }

    def __init__(self):
        self.engine_version = "1.0.0"

    async def analyze(self, product: MasterProduct) -> MerchantAnalysisReport:
        """
        Main entry point - performs complete product analysis.
        
        Args:
            product: Validated MasterProduct from scraped data
            
        Returns:
            Complete MerchantAnalysisReport with all analysis results
        """
        logger.info(f"Analyzing product: {product.identification.asin}")
        
        arbitrage = self._analyze_arbitrage(product)
        pl_analysis = self._analyze_private_label(product)
        risk = self._analyze_risks(product)
        verdict = self._generate_verdict(arbitrage, pl_analysis, risk, product)
        
        return MerchantAnalysisReport(
            asin=product.identification.asin,
            title=product.identification.title or "Unknown",
            brand=product.identification.brand,
            category=product.identification.category_path[0] if product.identification.category_path else None,
            arbitrage_analysis=arbitrage,
            private_label_analysis=pl_analysis,
            risk_analysis=risk,
            verdict=verdict,
            data_quality_score=product.data_quality_score or 0.0,
            analysis_timestamp=datetime.utcnow().isoformat(),
            engine_version=self.engine_version,
        )

    def _analyze_arbitrage(self, product: MasterProduct) -> ArbitrageAnalysis:
        """Analyze arbitrage and dropshipping profitability."""
        pricing = product.pricing_mechanics
        competition = product.competition_and_inventory
        sales = product.sales_analytics
        logistics = product.logistics_and_physical
        
        # Safe extraction with None handling
        buy_box = (pricing.buy_box_price if pricing and pricing.buy_box_price else 0.0) or 0.0
        amazon_fees = (pricing.amazon_referral_fee_est if pricing and pricing.amazon_referral_fee_est else 0.0) or 0.0
        
        fba_costs = self._calculate_fba_costs(logistics)
        overhead = buy_box * self.OVERHEAD_PERCENTAGE
        
        net_profit = buy_box - amazon_fees - fba_costs - overhead
        
        total_investment = amazon_fees + fba_costs + overhead
        roi = (net_profit / total_investment * 100) if total_investment > 0 else 0.0
        margin = (net_profit / buy_box * 100) if buy_box > 0 else 0.0
        
        # Safe extraction with None handling for competition
        amazon_is_seller = (competition.amazon_is_seller if competition and competition.amazon_is_seller is not None else False)
        fba_count = (competition.fba_seller_count if competition and competition.fba_seller_count is not None else 0) or 0
        total_offers = (competition.total_offer_count if competition and competition.total_offer_count is not None else 0) or 0
        
        buybox_risk = self._assess_buybox_risk(amazon_is_seller, fba_count, total_offers)
        
        # Safe extraction for sales
        bsr_change = (sales.bsr_change_percentage if sales and sales.bsr_change_percentage is not None else 0.0) or 0.0
        monthly_sales = (sales.estimated_monthly_sales if sales and sales.estimated_monthly_sales is not None else 0) or 0
        velocity = self._assess_velocity(bsr_change, monthly_sales)
        
        capital_turnover = None
        if monthly_sales and monthly_sales > 0:
            capital_turnover = int(30 / (monthly_sales / 100)) if monthly_sales >= 100 else 90
        
        return ArbitrageAnalysis(
            buy_box_price=buy_box,
            amazon_fees=amazon_fees,
            fba_costs=fba_costs,
            overhead_cost=overhead,
            net_profit=round(net_profit, 2),
            roi_percentage=round(roi, 2),
            margin_percentage=round(margin, 2),
            buybox_risk_level=buybox_risk,
            amazon_is_seller=amazon_is_seller,
            fba_seller_count=fba_count,
            total_offer_count=total_offers,
            velocity_grade=velocity,
            bsr_trend="improving" if bsr_change < 0 else "declining" if bsr_change > 0 else "stable",
            estimated_monthly_sales=monthly_sales,
            capital_turnover_days=capital_turnover,
        )

    def _calculate_fba_costs(self, logistics) -> float:
        """Estimate FBA costs based on product dimensions and weight."""
        if not logistics:
            return self.FBA_BASE_FULFILLMENT
        
        weight_kg = (logistics.package_weight_grams or 500) / 1000
        weight_cost = weight_kg * self.FBA_WEIGHT_RATE
        
        dims = logistics.dimensions_cm
        if dims and dims.length and dims.width and dims.height:
            cubic_cm = dims.length * dims.width * dims.height
            cubic_feet = cubic_cm / 28316.8
            storage_cost = cubic_feet * self.FBA_STORAGE_PER_CUBIC_FOOT
        else:
            storage_cost = 0.25
        
        return round(self.FBA_BASE_FULFILLMENT + weight_cost + storage_cost, 2)

    def _assess_buybox_risk(self, amazon_is_seller: bool, fba_count: int, total_offers: int) -> RiskLevel:
        """Assess BuyBox competition risk level."""
        if amazon_is_seller:
            return RiskLevel.CRITICAL
        if fba_count > 10:
            return RiskLevel.HIGH
        if fba_count > 5 or total_offers > 15:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _assess_velocity(self, bsr_change: float, monthly_sales: int) -> VelocityGrade:
        """Determine velocity grade for Sprinter Mode assessment."""
        thresholds = self.VELOCITY_THRESHOLDS
        
        if bsr_change <= thresholds["sprinter"]["bsr_change"] and monthly_sales >= thresholds["sprinter"]["monthly_sales"]:
            return VelocityGrade.SPRINTER
        if bsr_change <= thresholds["steady"]["bsr_change"] and monthly_sales >= thresholds["steady"]["monthly_sales"]:
            return VelocityGrade.STEADY
        return VelocityGrade.SLOW

    def _analyze_private_label(self, product: MasterProduct) -> PrivateLabelAnalysis:
        """Analyze Private Label opportunity."""
        sentiment = product.sentiment_and_quality
        sales = product.sales_analytics
        competition = product.competition_and_inventory
        pricing = product.pricing_mechanics
        
        # Safe extraction with None handling
        list_price = (pricing.list_price if pricing and pricing.list_price else 0.0) or 0.0
        buy_box = (pricing.buy_box_price if pricing and pricing.buy_box_price else 0.0) or 0.0
        
        # Use buy_box if list_price is 0
        if list_price == 0:
            list_price = buy_box
        
        target_cogs = list_price * self.PL_COGS_TARGET_RATIO
        projected_profit = buy_box - target_cogs - (buy_box * self.OVERHEAD_PERCENTAGE)
        projected_margin = (projected_profit / buy_box * 100) if buy_box > 0 else 0.0
        
        sentiment_gaps = self._extract_sentiment_gaps(sentiment)
        
        bsr_current = (sales.bsr_current if sales and sales.bsr_current else 999999) or 999999
        rating = (sentiment.rating_overall if sentiment and sentiment.rating_overall else 5.0) or 5.0
        has_opportunity = bsr_current < 5000 and rating < 4.5 and len(sentiment_gaps) > 0
        
        pl_score, breakdown = self._calculate_pl_score(product)
        
        fba_count = (competition.fba_seller_count if competition and competition.fba_seller_count else 0) or 0
        review_velocity = (sentiment.review_velocity_monthly if sentiment and sentiment.review_velocity_monthly else 0) or 0
        monthly_sales = (sales.estimated_monthly_sales if sales and sales.estimated_monthly_sales else 0) or 0
        
        market_demand = {
            "review_velocity_monthly": review_velocity,
            "estimated_monthly_sales": monthly_sales,
            "bsr_current": bsr_current,
            "demand_level": "high" if monthly_sales > 500 else "medium" if monthly_sales > 200 else "low",
        }
        
        comp_level = RiskLevel.LOW if fba_count < 3 else RiskLevel.MEDIUM if fba_count < 8 else RiskLevel.HIGH
        
        return PrivateLabelAnalysis(
            pl_score=pl_score,
            pl_score_breakdown=breakdown,
            sentiment_gaps=sentiment_gaps,
            has_improvement_opportunity=has_opportunity,
            target_cogs=round(target_cogs, 2),
            projected_pl_margin=round(projected_margin, 2),
            projected_pl_profit=round(projected_profit, 2),
            market_demand_signals=market_demand,
            competition_level=comp_level,
        )

    def _extract_sentiment_gaps(self, sentiment) -> List[SentimentGap]:
        """Extract improvement opportunities from negative keywords."""
        if not sentiment or not sentiment.top_negative_keywords:
            return []
        
        gaps = []
        improvement_map = {
            "plastic": "Use premium materials (metal, glass, BPA-free)",
            "taste": "Food-grade certification, better materials",
            "small": "Offer larger capacity variant",
            "capacity": "Increase size or offer size options",
            "break": "Reinforce durability, add protective features",
            "fragile": "Use shatter-resistant materials",
            "instructions": "Include comprehensive manual/video guide",
            "leak": "Improve sealing mechanism",
            "cheap": "Upgrade materials and finish quality",
            "flimsy": "Strengthen construction, use better materials",
        }
        
        for i, keyword in enumerate(sentiment.top_negative_keywords[:5]):
            keyword_lower = keyword.lower()
            improvement = "Address customer pain point"
            
            for key, suggestion in improvement_map.items():
                if key in keyword_lower:
                    improvement = suggestion
                    break
            
            gaps.append(SentimentGap(
                keyword=keyword,
                frequency_score=10.0 - (i * 2),
                improvement_potential=improvement,
            ))
        
        return gaps

    def _calculate_pl_score(self, product: MasterProduct) -> tuple[int, dict]:
        """Calculate Private Label opportunity score (0-100)."""
        weights = self.PL_WEIGHTS
        breakdown = {}
        
        sales = product.sales_analytics
        sentiment = product.sentiment_and_quality
        competition = product.competition_and_inventory
        
        monthly_sales = (sales.estimated_monthly_sales if sales and sales.estimated_monthly_sales else 0) or 0
        if monthly_sales >= 1000:
            velocity_score = 100
        elif monthly_sales >= 500:
            velocity_score = 80
        elif monthly_sales >= 200:
            velocity_score = 50
        else:
            velocity_score = 20
        breakdown["velocity_score"] = velocity_score
        
        rating = (sentiment.rating_overall if sentiment and sentiment.rating_overall else 5.0) or 5.0
        if rating < 3.5:
            rating_gap_score = 100
        elif rating < 4.0:
            rating_gap_score = 80
        elif rating < 4.5:
            rating_gap_score = 50
        else:
            rating_gap_score = 20
        breakdown["rating_gap_score"] = rating_gap_score
        
        fba_count = (competition.fba_seller_count if competition and competition.fba_seller_count else 0) or 0
        if fba_count <= 2:
            competition_score = 100
        elif fba_count <= 5:
            competition_score = 70
        elif fba_count <= 10:
            competition_score = 40
        else:
            competition_score = 10
        breakdown["competition_score"] = competition_score
        
        review_velocity = (sentiment.review_velocity_monthly if sentiment and sentiment.review_velocity_monthly else 0) or 0
        if review_velocity >= 100:
            momentum_score = 100
        elif review_velocity >= 50:
            momentum_score = 70
        elif review_velocity >= 20:
            momentum_score = 40
        else:
            momentum_score = 15
        breakdown["momentum_score"] = momentum_score
        
        final_score = int(
            velocity_score * weights["velocity"] +
            rating_gap_score * weights["rating_gap"] +
            competition_score * weights["competition"] +
            momentum_score * weights["review_momentum"]
        )
        
        return min(max(final_score, 0), 100), breakdown

    def _analyze_risks(self, product: MasterProduct) -> RiskAnalysis:
        """Analyze risk factors and defensive logic."""
        risk = product.risk_assessment
        pricing = product.pricing_mechanics
        
        ip_risk_str = risk.ip_infringement_risk.lower() if risk and risk.ip_infringement_risk else "low"
        ip_level = RiskLevel.HIGH if ip_risk_str == "high" else RiskLevel.MEDIUM if ip_risk_str == "medium" else RiskLevel.LOW
        ip_auto_reject = ip_level == RiskLevel.HIGH
        
        stability = (pricing.price_stability_score if pricing and pricing.price_stability_score is not None else 1.0) or 1.0
        price_war = stability < 0.5
        
        return_rate = (risk.return_rate_estimated if risk and risk.return_rate_estimated is not None else 0.0) or 0.0
        return_risk = RiskLevel.HIGH if return_rate > 0.10 else RiskLevel.MEDIUM if return_rate > 0.05 else RiskLevel.LOW
        
        seasonal = (risk.seasonal_factor if risk and risk.seasonal_factor else "non-seasonal") or "non-seasonal"
        
        risk_flags = []
        overall_risk = 0.0
        
        if ip_auto_reject:
            risk_flags.append("🚨 HIGH IP INFRINGEMENT RISK - AVOID")
            overall_risk += 40
        elif ip_level == RiskLevel.MEDIUM:
            risk_flags.append("⚠️ Moderate IP concern - verify trademark")
            overall_risk += 15
        
        if price_war:
            risk_flags.append("⚠️ PRICE WAR DETECTED - Unstable margins")
            overall_risk += 25
        
        if return_risk == RiskLevel.HIGH:
            risk_flags.append("⚠️ High return rate - quality concerns")
            overall_risk += 20
        
        if seasonal != "non-seasonal":
            risk_flags.append(f"📅 Seasonal product: {seasonal}")
            overall_risk += 10
        
        return RiskAnalysis(
            ip_risk_level=ip_level,
            ip_auto_reject=ip_auto_reject,
            price_stability_score=stability,
            price_war_detected=price_war,
            return_rate_risk=return_risk,
            seasonal_risk=seasonal,
            overall_risk_score=min(overall_risk, 100),
            risk_flags=risk_flags,
        )

    def _generate_verdict(
        self,
        arbitrage: ArbitrageAnalysis,
        pl: PrivateLabelAnalysis,
        risk: RiskAnalysis,
        product: MasterProduct,
    ) -> BusinessModelVerdict:
        """Generate final Go/No-Go verdicts for each business model."""
        
        if risk.ip_auto_reject:
            return BusinessModelVerdict(
                arbitrage_verdict=Verdict.NO_GO,
                arbitrage_reason="High IP infringement risk - immediate avoidance recommended",
                dropshipping_verdict=Verdict.NO_GO,
                dropshipping_reason="High IP infringement risk - immediate avoidance recommended",
                private_label_verdict=Verdict.NO_GO,
                private_label_reason="High IP infringement risk - cannot create variant",
                recommended_model=None,
                overall_verdict=Verdict.NO_GO,
                summary="❌ REJECTED: High IP/Trademark risk. Do not proceed with any model.",
            )
        
        arb_go = (
            arbitrage.net_profit > 5.0 and
            arbitrage.roi_percentage > 20.0 and
            arbitrage.margin_percentage > 15.0 and
            not arbitrage.amazon_is_seller and
            arbitrage.buybox_risk_level != RiskLevel.CRITICAL
        )
        
        arb_verdict = Verdict.GO if arb_go else Verdict.CONDITIONAL if arbitrage.net_profit > 3.0 else Verdict.NO_GO
        arb_reasons = []
        if arbitrage.amazon_is_seller:
            arb_reasons.append("Amazon is seller (high competition)")
        if arbitrage.roi_percentage < 20:
            arb_reasons.append(f"Low ROI ({arbitrage.roi_percentage:.1f}%)")
        if arbitrage.velocity_grade == VelocityGrade.SLOW:
            arb_reasons.append("Slow velocity (capital lock)")
        arb_reason = "; ".join(arb_reasons) if arb_reasons else "Good margins and velocity"
        
        drop_go = arb_go and arbitrage.velocity_grade != VelocityGrade.SLOW
        drop_verdict = Verdict.GO if drop_go else Verdict.CONDITIONAL if arb_verdict != Verdict.NO_GO else Verdict.NO_GO
        drop_reason = "Fast turnover suitable for dropship" if drop_go else "Consider velocity and margins"
        
        pl_go = (
            pl.pl_score >= 60 and
            pl.has_improvement_opportunity and
            pl.competition_level != RiskLevel.HIGH and
            not risk.price_war_detected
        )
        
        pl_verdict = Verdict.GO if pl_go else Verdict.CONDITIONAL if pl.pl_score >= 40 else Verdict.NO_GO
        pl_reasons = []
        if pl.pl_score < 60:
            pl_reasons.append(f"PL Score too low ({pl.pl_score}/100)")
        if not pl.has_improvement_opportunity:
            pl_reasons.append("No clear improvement gap")
        if pl.competition_level == RiskLevel.HIGH:
            pl_reasons.append("High competition")
        pl_reason = "; ".join(pl_reasons) if pl_reasons else f"Strong opportunity (Score: {pl.pl_score}/100)"
        
        go_count = sum([
            arb_verdict == Verdict.GO,
            drop_verdict == Verdict.GO,
            pl_verdict == Verdict.GO,
        ])
        
        if go_count >= 2:
            overall = Verdict.GO
            recommended = "Arbitrage" if arb_verdict == Verdict.GO else "Private Label"
        elif go_count == 1 or arb_verdict == Verdict.CONDITIONAL:
            overall = Verdict.CONDITIONAL
            recommended = "Arbitrage" if arb_verdict != Verdict.NO_GO else "Private Label" if pl_verdict != Verdict.NO_GO else None
        else:
            overall = Verdict.NO_GO
            recommended = None
        
        summary_parts = []
        if overall == Verdict.GO:
            summary_parts.append(f"✅ APPROVED: Recommended model is {recommended}")
        elif overall == Verdict.CONDITIONAL:
            summary_parts.append(f"⚠️ CONDITIONAL: Proceed with caution, consider {recommended}")
        else:
            summary_parts.append("❌ NOT RECOMMENDED: Risk factors outweigh potential")
        
        if risk.risk_flags:
            summary_parts.append(f"Flags: {len(risk.risk_flags)}")
        
        return BusinessModelVerdict(
            arbitrage_verdict=arb_verdict,
            arbitrage_reason=arb_reason,
            dropshipping_verdict=drop_verdict,
            dropshipping_reason=drop_reason,
            private_label_verdict=pl_verdict,
            private_label_reason=pl_reason,
            recommended_model=recommended,
            overall_verdict=overall,
            summary=" | ".join(summary_parts),
        )

    def analyze_sync(self, product: MasterProduct) -> MerchantAnalysisReport:
        """Synchronous wrapper for analyze method."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.analyze(product))
