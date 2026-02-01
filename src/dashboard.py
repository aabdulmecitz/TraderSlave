"""
Rich Terminal Dashboard for Autonomous Merchant Engine.
Displays analysis results in a visually appealing format.
"""
from __future__ import annotations
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

from .analysis_models import (
    MerchantAnalysisReport,
    RiskLevel,
    VelocityGrade,
    Verdict,
)


class MerchantDashboard:
    """Terminal dashboard for displaying analysis reports."""
    
    def __init__(self):
        self.console = Console()
    
    def display(self, report: MerchantAnalysisReport) -> None:
        """Display the complete analysis report in terminal."""
        self.console.print()
        self._print_header(report)
        self._print_arbitrage_section(report)
        self._print_pl_section(report)
        self._print_risk_section(report)
        self._print_verdict_section(report)
        self.console.print()
    
    def _print_header(self, report: MerchantAnalysisReport) -> None:
        """Print the main header with product info."""
        title_text = Text()
        title_text.append("🚀 AUTONOMOUS MERCHANT ENGINE ", style="bold cyan")
        title_text.append("v" + report.engine_version, style="dim")
        
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Label", style="dim")
        info_table.add_column("Value", style="bold white")
        
        info_table.add_row("Product", report.title[:60] + "..." if len(report.title) > 60 else report.title)
        info_table.add_row("ASIN", f"[cyan]{report.asin}[/cyan]")
        
        arb = report.arbitrage_analysis
        bsr_text = f"#{arb.estimated_monthly_sales:,} sales/mo" if arb.estimated_monthly_sales else "N/A"
        info_table.add_row("Brand", report.brand or "Unknown")
        info_table.add_row("Monthly Sales", bsr_text)
        
        quality_color = "green" if report.data_quality_score >= 0.8 else "yellow" if report.data_quality_score >= 0.5 else "red"
        info_table.add_row("Data Quality", f"[{quality_color}]{report.data_quality_score:.0%}[/{quality_color}]")
        
        self.console.print(Panel(info_table, title=title_text, border_style="cyan", box=box.DOUBLE))
    
    def _print_arbitrage_section(self, report: MerchantAnalysisReport) -> None:
        """Print arbitrage and dropshipping analysis."""
        arb = report.arbitrage_analysis
        
        table = Table(title="💰 ARBITRAGE & DROPSHIPPING ANALYSIS", box=box.ROUNDED, border_style="green")
        table.add_column("Metric", style="dim", width=18)
        table.add_column("Value", justify="right", width=12)
        table.add_column("Status", justify="center", width=15)
        
        profit_color = "green" if arb.net_profit > 5 else "yellow" if arb.net_profit > 0 else "red"
        profit_icon = "✅" if arb.net_profit > 5 else "⚠️" if arb.net_profit > 0 else "❌"
        
        table.add_row("Buy Box Price", f"${arb.buy_box_price:.2f}", "")
        table.add_row("Amazon Fees", f"-${arb.amazon_fees:.2f}", "")
        table.add_row("FBA Costs", f"-${arb.fba_costs:.2f}", "")
        table.add_row("Overhead (15%)", f"-${arb.overhead_cost:.2f}", "")
        table.add_row("─" * 16, "─" * 10, "─" * 13)
        table.add_row(
            "[bold]Net Profit[/bold]",
            f"[{profit_color}]${arb.net_profit:.2f}[/{profit_color}]",
            profit_icon
        )
        
        roi_color = "green" if arb.roi_percentage > 30 else "yellow" if arb.roi_percentage > 15 else "red"
        table.add_row("ROI", f"[{roi_color}]{arb.roi_percentage:.1f}%[/{roi_color}]", "")
        table.add_row("Margin", f"{arb.margin_percentage:.1f}%", "")
        
        velocity_styles = {
            VelocityGrade.SPRINTER: ("cyan", "⚡ SPRINTER"),
            VelocityGrade.STEADY: ("yellow", "🏃 STEADY"),
            VelocityGrade.SLOW: ("red", "🐢 SLOW"),
        }
        vel_color, vel_text = velocity_styles.get(arb.velocity_grade, ("white", "Unknown"))
        table.add_row("Velocity", f"[{vel_color}]{vel_text}[/{vel_color}]", "")
        
        risk_styles = {
            RiskLevel.LOW: ("green", "🟢 LOW"),
            RiskLevel.MEDIUM: ("yellow", "🟡 MEDIUM"),
            RiskLevel.HIGH: ("red", "🔴 HIGH"),
            RiskLevel.CRITICAL: ("red bold", "🚨 CRITICAL"),
        }
        risk_color, risk_text = risk_styles.get(arb.buybox_risk_level, ("white", "Unknown"))
        table.add_row("BuyBox Risk", f"[{risk_color}]{risk_text}[/{risk_color}]", "")
        
        if arb.amazon_is_seller:
            table.add_row("⚠️ Amazon Seller", "[red]YES[/red]", "❌")
        
        table.add_row("FBA Sellers", str(arb.fba_seller_count), "")
        table.add_row("Total Offers", str(arb.total_offer_count), "")
        
        if arb.capital_turnover_days:
            table.add_row("Turnover Est.", f"~{arb.capital_turnover_days} days", "")
        
        self.console.print(table)
    
    def _print_pl_section(self, report: MerchantAnalysisReport) -> None:
        """Print Private Label analysis."""
        pl = report.private_label_analysis
        
        table = Table(title="🏭 PRIVATE LABEL ANALYSIS", box=box.ROUNDED, border_style="magenta")
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value", justify="right", width=25)
        
        score_color = "green" if pl.pl_score >= 70 else "yellow" if pl.pl_score >= 50 else "red"
        score_bar = self._make_progress_bar(pl.pl_score, 100, 20)
        table.add_row("[bold]PL Score[/bold]", f"[{score_color}]{pl.pl_score}/100[/{score_color}] {score_bar}")
        
        breakdown_text = " | ".join([f"{k[:3]}:{v}" for k, v in pl.pl_score_breakdown.items()])
        table.add_row("Score Breakdown", f"[dim]{breakdown_text}[/dim]")
        
        table.add_row("Target COGS", f"${pl.target_cogs:.2f}")
        table.add_row("Projected Margin", f"{pl.projected_pl_margin:.1f}%")
        table.add_row("Projected Profit/Unit", f"${pl.projected_pl_profit:.2f}")
        
        opp_text = "[green]✅ YES[/green]" if pl.has_improvement_opportunity else "[red]❌ NO[/red]"
        table.add_row("Improvement Opportunity", opp_text)
        
        if pl.sentiment_gaps:
            gaps_text = ", ".join([f"'{g.keyword}'" for g in pl.sentiment_gaps[:3]])
            table.add_row("Negative Keywords", f"[yellow]{gaps_text}[/yellow]")
            
            if pl.sentiment_gaps[0].improvement_potential:
                table.add_row("Suggested Fix", f"[dim]{pl.sentiment_gaps[0].improvement_potential}[/dim]")
        
        demand = pl.market_demand_signals.get("demand_level", "unknown")
        demand_color = "green" if demand == "high" else "yellow" if demand == "medium" else "red"
        table.add_row("Market Demand", f"[{demand_color}]{demand.upper()}[/{demand_color}]")
        
        self.console.print(table)
    
    def _print_risk_section(self, report: MerchantAnalysisReport) -> None:
        """Print risk assessment section."""
        risk = report.risk_analysis
        
        table = Table(title="⚠️ RISK ASSESSMENT", box=box.ROUNDED, border_style="yellow")
        table.add_column("Factor", style="dim", width=20)
        table.add_column("Status", justify="right", width=25)
        
        ip_styles = {
            RiskLevel.LOW: ("green", "🟢 LOW"),
            RiskLevel.MEDIUM: ("yellow", "🟡 MEDIUM"),
            RiskLevel.HIGH: ("red", "🔴 HIGH - AVOID"),
        }
        ip_color, ip_text = ip_styles.get(risk.ip_risk_level, ("white", "Unknown"))
        table.add_row("IP Infringement Risk", f"[{ip_color}]{ip_text}[/{ip_color}]")
        
        stability_color = "green" if risk.price_stability_score >= 0.8 else "yellow" if risk.price_stability_score >= 0.5 else "red"
        stability_bar = self._make_progress_bar(int(risk.price_stability_score * 100), 100, 15)
        table.add_row("Price Stability", f"[{stability_color}]{risk.price_stability_score:.0%}[/{stability_color}] {stability_bar}")
        
        war_text = "[red]🔥 YES - ACTIVE[/red]" if risk.price_war_detected else "[green]✅ NO[/green]"
        table.add_row("Price War", war_text)
        
        return_styles = {
            RiskLevel.LOW: ("green", "🟢 LOW"),
            RiskLevel.MEDIUM: ("yellow", "🟡 MEDIUM"),
            RiskLevel.HIGH: ("red", "🔴 HIGH"),
        }
        ret_color, ret_text = return_styles.get(risk.return_rate_risk, ("white", "Unknown"))
        table.add_row("Return Rate Risk", f"[{ret_color}]{ret_text}[/{ret_color}]")
        
        table.add_row("Seasonal Factor", risk.seasonal_risk)
        
        overall_color = "green" if risk.overall_risk_score < 25 else "yellow" if risk.overall_risk_score < 50 else "red"
        table.add_row("[bold]Overall Risk Score[/bold]", f"[{overall_color}]{risk.overall_risk_score:.0f}/100[/{overall_color}]")
        
        self.console.print(table)
        
        if risk.risk_flags:
            flags_text = "\n".join(risk.risk_flags)
            self.console.print(Panel(flags_text, title="🚩 Active Risk Flags", border_style="red", box=box.ROUNDED))
    
    def _print_verdict_section(self, report: MerchantAnalysisReport) -> None:
        """Print final verdicts."""
        v = report.verdict
        
        table = Table(title="📋 FINAL VERDICT", box=box.HEAVY, border_style="blue")
        table.add_column("Business Model", style="bold", width=15)
        table.add_column("Verdict", justify="center", width=12)
        table.add_column("Reason", width=40)
        
        verdict_styles = {
            Verdict.GO: ("green", "✅ GO"),
            Verdict.NO_GO: ("red", "❌ NO-GO"),
            Verdict.CONDITIONAL: ("yellow", "⚠️ CONDITIONAL"),
        }
        
        arb_color, arb_icon = verdict_styles.get(v.arbitrage_verdict, ("white", "?"))
        table.add_row("Arbitrage/RA", f"[{arb_color}]{arb_icon}[/{arb_color}]", v.arbitrage_reason)
        
        drop_color, drop_icon = verdict_styles.get(v.dropshipping_verdict, ("white", "?"))
        table.add_row("Dropshipping", f"[{drop_color}]{drop_icon}[/{drop_color}]", v.dropshipping_reason)
        
        pl_color, pl_icon = verdict_styles.get(v.private_label_verdict, ("white", "?"))
        table.add_row("Private Label", f"[{pl_color}]{pl_icon}[/{pl_color}]", v.private_label_reason)
        
        self.console.print(table)
        
        overall_color, overall_icon = verdict_styles.get(v.overall_verdict, ("white", "?"))
        summary_style = "bold " + overall_color
        
        summary_panel = Panel(
            f"[{summary_style}]{v.summary}[/{summary_style}]",
            title="🎯 RECOMMENDATION" + (f" → {v.recommended_model}" if v.recommended_model else ""),
            border_style=overall_color,
            box=box.DOUBLE,
        )
        self.console.print(summary_panel)
    
    def _make_progress_bar(self, value: int, max_val: int, width: int = 20) -> str:
        """Create a simple progress bar string."""
        filled = int((value / max_val) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def export_json(self, report: MerchantAnalysisReport, filepath: str) -> None:
        """Export the report to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(report.model_dump(mode='json'), f, indent=2)
        self.console.print(f"[green]✓ Report exported to {filepath}[/green]")
    
    def print_summary_line(self, report: MerchantAnalysisReport) -> None:
        """Print a single-line summary for batch processing."""
        v = report.verdict
        verdict_icons = {Verdict.GO: "✅", Verdict.NO_GO: "❌", Verdict.CONDITIONAL: "⚠️"}
        icon = verdict_icons.get(v.overall_verdict, "?")
        
        self.console.print(
            f"{icon} [cyan]{report.asin}[/cyan] | "
            f"Profit: ${report.arbitrage_analysis.net_profit:.2f} | "
            f"PL: {report.private_label_analysis.pl_score}/100 | "
            f"{v.summary[:50]}..."
        )
