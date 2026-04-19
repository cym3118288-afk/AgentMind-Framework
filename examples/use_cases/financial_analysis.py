"""
Financial Analysis and Reporting System

A multi-agent system for comprehensive financial analysis, risk assessment,
and automated report generation.

Features:
- Financial data analysis
- Risk assessment
- Market trend analysis
- Automated report generation
- Investment recommendations

Usage:
    python examples/use_cases/financial_analysis.py
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import random

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


@dataclass
class FinancialData:
    """Financial metrics and data"""
    company: str
    ticker: str
    revenue: float
    profit: float
    debt: float
    cash: float
    market_cap: float
    pe_ratio: float
    growth_rate: float
    sector: str


@dataclass
class MarketData:
    """Market and economic indicators"""
    date: datetime
    sp500: float
    nasdaq: float
    interest_rate: float
    inflation_rate: float
    unemployment_rate: float


# Sample financial data
COMPANIES = [
    FinancialData("TechCorp", "TECH", 50_000_000, 8_000_000, 5_000_000,
                  15_000_000, 200_000_000, 25.0, 0.15, "Technology"),
    FinancialData("RetailGiant", "RETL", 80_000_000, 4_000_000, 20_000_000,
                  10_000_000, 150_000_000, 18.5, 0.08, "Retail"),
    FinancialData("BioPharm", "BPHR", 30_000_000, 2_000_000, 8_000_000,
                  12_000_000, 100_000_000, 50.0, 0.25, "Healthcare"),
]


class FinancialDataTool(Tool):
    """Retrieve financial data for companies"""

    def __init__(self, companies: List[FinancialData]):
        self.companies = {c.ticker: c for c in companies}
        super().__init__(
            name="get_financial_data",
            description="Get financial metrics for a company by ticker symbol",
            parameters={
                "ticker": {"type": "string", "description": "Stock ticker symbol"}
            }
        )

    async def execute(self, ticker: str) -> str:
        """Get financial data for ticker"""
        if ticker.upper() not in self.companies:
            return json.dumps({"error": f"Ticker {ticker} not found"})

        company = self.companies[ticker.upper()]
        return json.dumps({
            "company": company.company,
            "ticker": company.ticker,
            "revenue": company.revenue,
            "profit": company.profit,
            "profit_margin": (company.profit / company.revenue) * 100,
            "debt": company.debt,
            "cash": company.cash,
            "net_debt": company.debt - company.cash,
            "market_cap": company.market_cap,
            "pe_ratio": company.pe_ratio,
            "growth_rate": company.growth_rate * 100,
            "sector": company.sector,
            "debt_to_equity": (company.debt / (company.market_cap * 0.6)) * 100,
        }, indent=2)


class RatioCalculatorTool(Tool):
    """Calculate financial ratios and metrics"""

    def __init__(self):
        super().__init__(
            name="calculate_ratios",
            description="Calculate financial ratios from raw data",
            parameters={
                "revenue": {"type": "number"},
                "profit": {"type": "number"},
                "debt": {"type": "number"},
                "equity": {"type": "number"},
                "assets": {"type": "number"},
            }
        )

    async def execute(self, revenue: float, profit: float, debt: float,
                     equity: float, assets: float) -> str:
        """Calculate key financial ratios"""
        ratios = {
            "profit_margin": (profit / revenue) * 100 if revenue > 0 else 0,
            "return_on_equity": (profit / equity) * 100 if equity > 0 else 0,
            "return_on_assets": (profit / assets) * 100 if assets > 0 else 0,
            "debt_to_equity": (debt / equity) * 100 if equity > 0 else 0,
            "current_ratio": assets / debt if debt > 0 else 0,
        }
        return json.dumps(ratios, indent=2)


class MarketDataTool(Tool):
    """Get market and economic indicators"""

    def __init__(self):
        super().__init__(
            name="get_market_data",
            description="Get current market indices and economic indicators",
            parameters={}
        )

    async def execute(self) -> str:
        """Get market data"""
        # Simulated market data
        data = {
            "date": datetime.now().isoformat(),
            "sp500": 4500 + random.uniform(-50, 50),
            "nasdaq": 14000 + random.uniform(-200, 200),
            "interest_rate": 5.25,
            "inflation_rate": 3.2,
            "unemployment_rate": 3.8,
            "market_sentiment": "Neutral",
            "volatility_index": 15.5 + random.uniform(-2, 2),
        }
        return json.dumps(data, indent=2)


class RiskAssessmentTool(Tool):
    """Assess investment risk based on various factors"""

    def __init__(self):
        super().__init__(
            name="assess_risk",
            description="Assess risk level based on financial metrics",
            parameters={
                "debt_to_equity": {"type": "number"},
                "profit_margin": {"type": "number"},
                "volatility": {"type": "number"},
                "sector": {"type": "string"},
            }
        )

    async def execute(self, debt_to_equity: float, profit_margin: float,
                     volatility: float, sector: str) -> str:
        """Assess risk level"""
        risk_score = 0

        # Debt risk
        if debt_to_equity > 100:
            risk_score += 3
        elif debt_to_equity > 50:
            risk_score += 2
        else:
            risk_score += 1

        # Profitability risk
        if profit_margin < 5:
            risk_score += 3
        elif profit_margin < 10:
            risk_score += 2
        else:
            risk_score += 1

        # Volatility risk
        if volatility > 30:
            risk_score += 3
        elif volatility > 20:
            risk_score += 2
        else:
            risk_score += 1

        # Sector risk
        high_risk_sectors = ["Technology", "Biotech", "Crypto"]
        if sector in high_risk_sectors:
            risk_score += 2

        risk_level = "Low" if risk_score <= 4 else "Medium" if risk_score <= 7 else "High"

        return json.dumps({
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": {
                "debt_risk": "High" if debt_to_equity > 100 else "Medium" if debt_to_equity > 50 else "Low",
                "profitability_risk": "High" if profit_margin < 5 else "Medium" if profit_margin < 10 else "Low",
                "volatility_risk": "High" if volatility > 30 else "Medium" if volatility > 20 else "Low",
                "sector_risk": "High" if sector in high_risk_sectors else "Medium"
            },
            "recommendation": "Proceed with caution" if risk_level == "High" else "Suitable for moderate investors" if risk_level == "Medium" else "Suitable for conservative investors"
        }, indent=2)


async def analyze_investment(ticker: str, investment_amount: float) -> Dict[str, Any]:
    """
    Perform comprehensive financial analysis for investment decision

    Args:
        ticker: Stock ticker symbol
        investment_amount: Amount to invest

    Returns:
        Analysis report with recommendations
    """
    # Initialize LLM provider
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    # Create tools
    financial_tool = FinancialDataTool(COMPANIES)
    ratio_tool = RatioCalculatorTool()
    market_tool = MarketDataTool()
    risk_tool = RiskAssessmentTool()

    # Create specialized agents
    data_analyst = Agent(
        name="DataAnalyst",
        role="financial_data_analyst",
        system_prompt="""You are a financial data analyst. Retrieve and analyze
        company financial data including revenue, profit, debt, and market metrics.
        Calculate key ratios and identify trends. Present data clearly and highlight
        important metrics.""",
        tools=[financial_tool, ratio_tool]
    )

    market_analyst = Agent(
        name="MarketAnalyst",
        role="market_analyst",
        system_prompt="""You are a market analyst who monitors economic indicators
        and market conditions. Analyze current market trends, interest rates, inflation,
        and overall economic health. Assess how market conditions might impact the investment.""",
        tools=[market_tool]
    )

    risk_analyst = Agent(
        name="RiskAnalyst",
        role="risk_assessment_specialist",
        system_prompt="""You are a risk assessment specialist. Evaluate investment
        risks based on financial metrics, market conditions, and sector factors.
        Provide clear risk ratings and identify potential concerns.""",
        tools=[risk_tool]
    )

    investment_advisor = Agent(
        name="InvestmentAdvisor",
        role="investment_advisor",
        system_prompt="""You are a senior investment advisor. Synthesize financial
        data, market analysis, and risk assessment to provide clear investment
        recommendations. Consider the investment amount and provide specific advice
        on whether to invest, how much, and what to watch for.""",
        tools=[]
    )

    # Add agents to mind
    mind.add_agent(data_analyst)
    mind.add_agent(market_analyst)
    mind.add_agent(risk_analyst)
    mind.add_agent(investment_advisor)

    # Create analysis task
    task = f"""Perform comprehensive investment analysis for {ticker}.

    Investment Amount: ${investment_amount:,.2f}

    Required Analysis:
    1. Retrieve and analyze financial data for {ticker}
    2. Assess current market conditions and economic indicators
    3. Evaluate investment risks and potential concerns
    4. Provide final investment recommendation with reasoning

    Deliver a clear recommendation: BUY, HOLD, or AVOID with detailed justification."""

    print(f"\n{'='*60}")
    print(f"Financial Analysis: {ticker}")
    print(f"Investment Amount: ${investment_amount:,.2f}")
    print(f"{'='*60}\n")

    result = await mind.collaborate(task, max_rounds=4)

    return {
        "ticker": ticker,
        "investment_amount": investment_amount,
        "analysis": result,
        "timestamp": datetime.now().isoformat()
    }


async def generate_portfolio_report(tickers: List[str]) -> Dict[str, Any]:
    """
    Generate comprehensive portfolio analysis report

    Args:
        tickers: List of stock tickers in portfolio

    Returns:
        Portfolio analysis report
    """
    llm = OllamaProvider(model="llama3.2")
    mind = AgentMind(llm_provider=llm)

    financial_tool = FinancialDataTool(COMPANIES)
    market_tool = MarketDataTool()
    risk_tool = RiskAssessmentTool()

    portfolio_analyst = Agent(
        name="PortfolioAnalyst",
        role="portfolio_analyst",
        system_prompt="""You are a portfolio analyst. Analyze multiple holdings,
        assess diversification, identify concentration risks, and evaluate overall
        portfolio health. Provide actionable recommendations for rebalancing.""",
        tools=[financial_tool, market_tool, risk_tool]
    )

    mind.add_agent(portfolio_analyst)

    task = f"""Analyze portfolio containing: {', '.join(tickers)}

    Provide:
    1. Individual holding analysis
    2. Sector diversification assessment
    3. Overall risk profile
    4. Rebalancing recommendations
    5. Performance outlook"""

    print(f"\n{'='*60}")
    print(f"Portfolio Analysis")
    print(f"Holdings: {', '.join(tickers)}")
    print(f"{'='*60}\n")

    result = await mind.collaborate(task, max_rounds=3)

    return {
        "portfolio": tickers,
        "report": result,
        "timestamp": datetime.now().isoformat()
    }


async def main():
    """Run financial analysis examples"""

    # Scenario 1: Single stock analysis
    print("\n" + "="*60)
    print("SCENARIO 1: Investment Analysis - TechCorp")
    print("="*60)
    result1 = await analyze_investment("TECH", 10000)
    print("\nAnalysis:")
    print(result1["analysis"])

    # Scenario 2: Different company
    print("\n" + "="*60)
    print("SCENARIO 2: Investment Analysis - BioPharm")
    print("="*60)
    result2 = await analyze_investment("BPHR", 5000)
    print("\nAnalysis:")
    print(result2["analysis"])

    # Scenario 3: Portfolio analysis
    print("\n" + "="*60)
    print("SCENARIO 3: Portfolio Analysis")
    print("="*60)
    result3 = await generate_portfolio_report(["TECH", "RETL", "BPHR"])
    print("\nPortfolio Report:")
    print(result3["report"])


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   Financial Analysis System - AgentMind Demo            ║
    ║                                                          ║
    ║   Multi-agent system for investment analysis            ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
