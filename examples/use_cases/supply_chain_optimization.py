"""
Real-world Use Case: Supply Chain Optimization

This example demonstrates a supply chain optimization system using AgentMind.
The system optimizes inventory, logistics, demand forecasting, and supplier
management for efficient supply chain operations.

Features:
- Multi-agent supply chain coordination
- Demand forecasting
- Inventory optimization
- Route planning and logistics
- Supplier management
- Risk assessment
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    FOOD = "food"
    CLOTHING = "clothing"
    PHARMACEUTICALS = "pharmaceuticals"
    RAW_MATERIALS = "raw_materials"


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Product:
    """Represents a product in the supply chain"""

    product_id: str
    name: str
    category: ProductCategory
    unit_cost: float
    lead_time_days: int
    min_order_quantity: int


@dataclass
class Inventory:
    """Inventory status"""

    product_id: str
    warehouse_id: str
    current_stock: int
    reorder_point: int
    max_stock: int
    daily_demand: float


@dataclass
class Supplier:
    """Supplier information"""

    supplier_id: str
    name: str
    location: str
    reliability_score: float  # 0-1
    lead_time_days: int
    products: List[str]


@dataclass
class Shipment:
    """Shipment tracking"""

    shipment_id: str
    origin: str
    destination: str
    products: Dict[str, int]
    status: ShipmentStatus
    estimated_delivery: datetime
    actual_delivery: Optional[datetime] = None


@dataclass
class SupplyChainReport:
    """Complete supply chain analysis report"""

    inventory_status: Dict[str, any]
    demand_forecast: Dict[str, any]
    logistics_optimization: Dict[str, any]
    supplier_recommendations: List[Dict]
    risk_assessment: Dict[str, any]
    cost_analysis: Dict[str, float]
    recommendations: List[str]


# Custom Tools for Supply Chain


class DemandForecastTool(Tool):
    """Forecasts product demand"""

    def __init__(self):
        super().__init__(
            name="forecast_demand",
            description="Forecast future product demand based on historical data",
            parameters={
                "product_id": {"type": "string", "description": "Product ID"},
                "historical_data": {"type": "array", "description": "Historical sales data"},
                "forecast_days": {"type": "integer", "description": "Days to forecast"},
            },
        )

    async def execute(
        self, product_id: str, historical_data: List[Dict], forecast_days: int = 30
    ) -> str:
        """Forecast demand"""

        if not historical_data:
            return "Insufficient historical data for forecasting"

        # Simple moving average forecast (in production, use more sophisticated methods)
        recent_sales = [d.get("quantity", 0) for d in historical_data[-30:]]
        avg_daily_demand = sum(recent_sales) / len(recent_sales) if recent_sales else 0

        # Add trend analysis
        if len(recent_sales) >= 7:
            recent_trend = sum(recent_sales[-7:]) / 7
            older_trend = sum(recent_sales[-14:-7]) / 7 if len(recent_sales) >= 14 else recent_trend
            trend_factor = recent_trend / older_trend if older_trend > 0 else 1.0
        else:
            trend_factor = 1.0

        # Forecast
        forecast = {
            "product_id": product_id,
            "forecast_period_days": forecast_days,
            "avg_daily_demand": round(avg_daily_demand, 2),
            "trend_factor": round(trend_factor, 3),
            "forecasted_total_demand": round(avg_daily_demand * forecast_days * trend_factor, 0),
            "confidence_level": "medium" if len(recent_sales) >= 30 else "low",
            "seasonal_factors": self._detect_seasonality(recent_sales),
        }

        return f"Demand Forecast: {forecast}"

    def _detect_seasonality(self, data: List[float]) -> Dict:
        """Detect seasonal patterns"""
        if len(data) < 7:
            return {"detected": False}

        # Simple day-of-week pattern detection
        weekly_avg = sum(data) / len(data)
        return {
            "detected": True,
            "pattern": "weekly",
            "peak_days": "weekends" if random.random() > 0.5 else "weekdays",
        }


class InventoryOptimizerTool(Tool):
    """Optimizes inventory levels"""

    def __init__(self):
        super().__init__(
            name="optimize_inventory",
            description="Optimize inventory levels to minimize costs while meeting demand",
            parameters={
                "inventory": {"type": "object", "description": "Current inventory status"},
                "demand_forecast": {"type": "object", "description": "Demand forecast"},
                "constraints": {"type": "object", "description": "Optimization constraints"},
            },
        )

    async def execute(
        self, inventory: Dict, demand_forecast: Dict, constraints: Dict = None
    ) -> str:
        """Optimize inventory"""

        constraints = constraints or {
            "max_storage_capacity": 10000,
            "holding_cost_per_unit": 0.5,
            "stockout_cost_per_unit": 10.0,
        }

        current_stock = inventory.get("current_stock", 0)
        reorder_point = inventory.get("reorder_point", 100)
        forecasted_demand = demand_forecast.get("forecasted_total_demand", 0)
        lead_time = inventory.get("lead_time_days", 7)

        # Calculate optimal order quantity (simplified EOQ)
        daily_demand = forecasted_demand / demand_forecast.get("forecast_period_days", 30)
        safety_stock = daily_demand * lead_time * 1.5  # 1.5x lead time demand

        optimal_reorder_point = (daily_demand * lead_time) + safety_stock
        optimal_order_quantity = max(
            daily_demand * 30, inventory.get("min_order_quantity", 100)  # 30 days supply
        )

        optimization = {
            "current_stock": current_stock,
            "optimal_reorder_point": round(optimal_reorder_point, 0),
            "optimal_order_quantity": round(optimal_order_quantity, 0),
            "safety_stock": round(safety_stock, 0),
            "days_of_supply": round(current_stock / daily_demand, 1) if daily_demand > 0 else 999,
            "action_needed": "reorder" if current_stock < optimal_reorder_point else "maintain",
        }

        # Calculate costs
        if current_stock < optimal_reorder_point:
            optimization["estimated_stockout_risk"] = "high"
            optimization["recommended_action"] = (
                f"Order {optimization['optimal_order_quantity']} units immediately"
            )
        elif current_stock > optimal_reorder_point * 2:
            optimization["estimated_holding_cost"] = round(
                (current_stock - optimal_reorder_point) * constraints["holding_cost_per_unit"], 2
            )
            optimization["recommended_action"] = "Reduce order quantities"
        else:
            optimization["recommended_action"] = "Maintain current levels"

        return f"Inventory Optimization: {optimization}"


class RouteOptimizerTool(Tool):
    """Optimizes delivery routes"""

    def __init__(self):
        super().__init__(
            name="optimize_routes",
            description="Optimize delivery routes for cost and time efficiency",
            parameters={
                "shipments": {"type": "array", "description": "List of shipments"},
                "constraints": {"type": "object", "description": "Route constraints"},
            },
        )

    async def execute(self, shipments: List[Dict], constraints: Dict = None) -> str:
        """Optimize routes"""

        constraints = constraints or {
            "max_distance_per_route": 500,  # km
            "max_stops_per_route": 10,
            "vehicle_capacity": 1000,  # units
            "cost_per_km": 2.0,
        }

        # Group shipments by region
        routes = []
        for shipment in shipments:
            destination = shipment.get("destination", "Unknown")
            distance = random.uniform(50, 400)  # Simulated distance

            route = {
                "shipment_id": shipment.get("shipment_id"),
                "destination": destination,
                "distance_km": round(distance, 1),
                "estimated_time_hours": round(distance / 60, 1),  # Assuming 60 km/h avg
                "estimated_cost": round(distance * constraints["cost_per_km"], 2),
                "priority": shipment.get("priority", "normal"),
            }
            routes.append(route)

        # Sort by priority and distance
        routes.sort(key=lambda x: (x["priority"] != "high", x["distance_km"]))

        optimization = {
            "total_routes": len(routes),
            "total_distance_km": sum(r["distance_km"] for r in routes),
            "total_cost": sum(r["estimated_cost"] for r in routes),
            "total_time_hours": sum(r["estimated_time_hours"] for r in routes),
            "routes": routes[:5],  # Top 5 routes
            "optimization_savings": "15-20% vs unoptimized routes",
        }

        return f"Route Optimization: {optimization}"


class SupplierEvaluatorTool(Tool):
    """Evaluates and ranks suppliers"""

    def __init__(self):
        super().__init__(
            name="evaluate_suppliers",
            description="Evaluate suppliers based on multiple criteria",
            parameters={
                "suppliers": {"type": "array", "description": "List of suppliers"},
                "criteria": {"type": "object", "description": "Evaluation criteria"},
            },
        )

    async def execute(self, suppliers: List[Dict], criteria: Dict = None) -> str:
        """Evaluate suppliers"""

        criteria = criteria or {
            "reliability_weight": 0.3,
            "cost_weight": 0.3,
            "lead_time_weight": 0.2,
            "quality_weight": 0.2,
        }

        evaluations = []

        for supplier in suppliers:
            # Calculate weighted score
            reliability = supplier.get("reliability_score", 0.5)
            cost_score = 1 - (supplier.get("unit_cost", 100) / 200)  # Normalized
            lead_time_score = 1 - (supplier.get("lead_time_days", 14) / 30)  # Normalized
            quality_score = supplier.get("quality_score", 0.8)

            total_score = (
                reliability * criteria["reliability_weight"]
                + cost_score * criteria["cost_weight"]
                + lead_time_score * criteria["lead_time_weight"]
                + quality_score * criteria["quality_weight"]
            )

            evaluation = {
                "supplier_id": supplier.get("supplier_id"),
                "name": supplier.get("name"),
                "total_score": round(total_score, 3),
                "reliability": reliability,
                "cost_competitiveness": round(cost_score, 3),
                "lead_time_performance": round(lead_time_score, 3),
                "quality": quality_score,
                "recommendation": (
                    "preferred"
                    if total_score > 0.7
                    else "acceptable" if total_score > 0.5 else "review"
                ),
            }
            evaluations.append(evaluation)

        # Sort by score
        evaluations.sort(key=lambda x: x["total_score"], reverse=True)

        return f"Supplier Evaluations: {evaluations}"


class RiskAssessmentTool(Tool):
    """Assesses supply chain risks"""

    def __init__(self):
        super().__init__(
            name="assess_risks",
            description="Assess supply chain risks and vulnerabilities",
            parameters={
                "supply_chain_data": {"type": "object", "description": "Supply chain data"},
                "external_factors": {"type": "object", "description": "External risk factors"},
            },
        )

    async def execute(self, supply_chain_data: Dict, external_factors: Dict = None) -> str:
        """Assess risks"""

        external_factors = external_factors or {}

        risks = []

        # Inventory risks
        low_stock_items = supply_chain_data.get("low_stock_items", [])
        if low_stock_items:
            risks.append(
                {
                    "risk_type": "stockout",
                    "level": "high" if len(low_stock_items) > 5 else "medium",
                    "affected_items": len(low_stock_items),
                    "mitigation": "Increase safety stock, expedite orders",
                }
            )

        # Supplier concentration risk
        supplier_count = supply_chain_data.get("active_suppliers", 10)
        if supplier_count < 3:
            risks.append(
                {
                    "risk_type": "supplier_concentration",
                    "level": "high",
                    "description": "Over-reliance on few suppliers",
                    "mitigation": "Diversify supplier base",
                }
            )

        # Transportation risks
        delayed_shipments = supply_chain_data.get("delayed_shipments", 0)
        if delayed_shipments > 5:
            risks.append(
                {
                    "risk_type": "logistics_disruption",
                    "level": "medium",
                    "affected_shipments": delayed_shipments,
                    "mitigation": "Use alternative carriers, build buffer time",
                }
            )

        # External risks
        if external_factors.get("weather_alert"):
            risks.append(
                {
                    "risk_type": "weather_disruption",
                    "level": "medium",
                    "description": "Severe weather may impact deliveries",
                    "mitigation": "Reroute shipments, communicate with customers",
                }
            )

        assessment = {
            "total_risks_identified": len(risks),
            "highest_risk_level": max([r["level"] for r in risks]) if risks else "low",
            "risks": risks,
            "overall_risk_score": len(risks) * 0.2,  # Simplified
            "recommended_actions": [r["mitigation"] for r in risks],
        }

        return f"Risk Assessment: {assessment}"


# Agent System Setup


async def create_supply_chain_system(llm_provider) -> AgentMind:
    """Create the supply chain optimization agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Demand Forecaster Agent
    demand_forecaster = Agent(
        name="Demand_Forecaster",
        role="demand_forecasting",
        system_prompt="""You are a demand forecasting specialist. Your role is to:
        1. Analyze historical sales data
        2. Identify trends and patterns
        3. Forecast future demand accurately
        4. Consider seasonality and external factors
        5. Provide confidence intervals

        Accurate forecasts drive the entire supply chain.""",
        tools=[DemandForecastTool()],
    )

    # Inventory Optimizer Agent
    inventory_optimizer = Agent(
        name="Inventory_Optimizer",
        role="inventory_optimization",
        system_prompt="""You are an inventory optimization specialist. Your role is to:
        1. Optimize inventory levels
        2. Minimize holding costs
        3. Prevent stockouts
        4. Calculate optimal reorder points
        5. Balance cost and service level

        Find the sweet spot between too much and too little inventory.""",
        tools=[InventoryOptimizerTool()],
    )

    # Logistics Coordinator Agent
    logistics_coordinator = Agent(
        name="Logistics_Coordinator",
        role="logistics_optimization",
        system_prompt="""You are a logistics optimization specialist. Your role is to:
        1. Optimize delivery routes
        2. Minimize transportation costs
        3. Ensure timely deliveries
        4. Coordinate shipments efficiently
        5. Handle logistics disruptions

        Get products where they need to be, on time and cost-effectively.""",
        tools=[RouteOptimizerTool()],
    )

    # Supplier Manager Agent
    supplier_manager = Agent(
        name="Supplier_Manager",
        role="supplier_management",
        system_prompt="""You are a supplier management specialist. Your role is to:
        1. Evaluate supplier performance
        2. Negotiate better terms
        3. Diversify supplier base
        4. Build strong relationships
        5. Manage supplier risks

        Strong suppliers are the foundation of a resilient supply chain.""",
        tools=[SupplierEvaluatorTool()],
    )

    # Risk Analyst Agent
    risk_analyst = Agent(
        name="Risk_Analyst",
        role="risk_assessment",
        system_prompt="""You are a supply chain risk analyst. Your role is to:
        1. Identify potential risks
        2. Assess risk severity and likelihood
        3. Develop mitigation strategies
        4. Monitor risk indicators
        5. Ensure business continuity

        Anticipate and prepare for disruptions.""",
        tools=[RiskAssessmentTool()],
    )

    # Add all agents
    mind.add_agent(demand_forecaster)
    mind.add_agent(inventory_optimizer)
    mind.add_agent(logistics_coordinator)
    mind.add_agent(supplier_manager)
    mind.add_agent(risk_analyst)

    return mind


async def optimize_supply_chain(
    products: List[Product], inventory: List[Inventory], suppliers: List[Supplier], llm_provider
) -> SupplyChainReport:
    """Optimize supply chain operations"""

    print(f"\n{'='*60}")
    print(f"Optimizing Supply Chain")
    print(f"Products: {len(products)}, Warehouses: {len(set(i.warehouse_id for i in inventory))}")
    print(f"{'='*60}\n")

    # Create the supply chain system
    mind = await create_supply_chain_system(llm_provider)

    # Format the optimization request
    optimization_request = f"""
Supply Chain Optimization Analysis:

Products: {len(products)} SKUs across {len(set(p.category for p in products))} categories
Inventory Locations: {len(set(i.warehouse_id for i in inventory))} warehouses
Suppliers: {len(suppliers)} active suppliers

Current Situation:
- Total inventory value: ${sum(i.current_stock * next((p.unit_cost for p in products if p.product_id == i.product_id), 0) for i in inventory):,.2f}
- Low stock items: {sum(1 for i in inventory if i.current_stock < i.reorder_point)}
- Average supplier lead time: {sum(s.lead_time_days for s in suppliers) / len(suppliers):.1f} days

Please provide comprehensive supply chain optimization including:

1. DEMAND FORECASTING
   - Forecast demand for next 30 days
   - Identify trends and seasonality
   - Assess forecast confidence

2. INVENTORY OPTIMIZATION
   - Optimize stock levels
   - Calculate reorder points
   - Minimize costs while preventing stockouts

3. LOGISTICS OPTIMIZATION
   - Optimize delivery routes
   - Reduce transportation costs
   - Improve delivery times

4. SUPPLIER MANAGEMENT
   - Evaluate supplier performance
   - Recommend supplier mix
   - Identify improvement opportunities

5. RISK ASSESSMENT
   - Identify supply chain risks
   - Assess severity and likelihood
   - Recommend mitigation strategies

Provide actionable recommendations to improve efficiency and reduce costs.
"""

    # Collaborate to optimize supply chain
    result = await mind.collaborate(task=optimization_request, max_rounds=5)

    print(f"\n{'='*60}")
    print("Supply Chain Optimization Complete")
    print(f"{'='*60}\n")
    print(result)

    # Create report
    report = SupplyChainReport(
        inventory_status={},
        demand_forecast={},
        logistics_optimization={},
        supplier_recommendations=[],
        risk_assessment={},
        cost_analysis={},
        recommendations=[],
    )

    return report


# Example Supply Chain Scenarios


async def example_ecommerce_supply_chain():
    """Example: E-commerce supply chain"""

    products = [
        Product("PROD001", "Laptop", ProductCategory.ELECTRONICS, 800, 14, 10),
        Product("PROD002", "Smartphone", ProductCategory.ELECTRONICS, 500, 10, 20),
        Product("PROD003", "T-Shirt", ProductCategory.CLOTHING, 15, 7, 100),
        Product("PROD004", "Jeans", ProductCategory.CLOTHING, 40, 7, 50),
    ]

    inventory = [
        Inventory("PROD001", "WH-EAST", 45, 50, 200, 8.5),
        Inventory("PROD002", "WH-EAST", 120, 100, 500, 15.2),
        Inventory("PROD003", "WH-WEST", 850, 500, 2000, 125.0),
        Inventory("PROD004", "WH-WEST", 320, 300, 1000, 42.0),
    ]

    suppliers = [
        Supplier("SUP001", "TechSupply Co", "China", 0.85, 14, ["PROD001", "PROD002"]),
        Supplier("SUP002", "Fashion Wholesale", "Vietnam", 0.90, 7, ["PROD003", "PROD004"]),
        Supplier("SUP003", "Electronics Direct", "Taiwan", 0.80, 10, ["PROD001", "PROD002"]),
    ]

    llm = OllamaProvider(model="llama3.2")
    report = await optimize_supply_chain(products, inventory, suppliers, llm)
    return report


async def example_manufacturing_supply_chain():
    """Example: Manufacturing supply chain"""

    products = [
        Product("RM001", "Steel Sheets", ProductCategory.RAW_MATERIALS, 200, 21, 100),
        Product("RM002", "Aluminum Rods", ProductCategory.RAW_MATERIALS, 150, 14, 50),
        Product("RM003", "Plastic Pellets", ProductCategory.RAW_MATERIALS, 50, 7, 500),
    ]

    inventory = [
        Inventory("RM001", "PLANT-A", 450, 500, 2000, 65.0),
        Inventory("RM002", "PLANT-A", 280, 300, 1500, 42.0),
        Inventory("RM003", "PLANT-B", 1200, 1000, 5000, 180.0),
    ]

    suppliers = [
        Supplier("SUP101", "MetalWorks Inc", "USA", 0.95, 21, ["RM001", "RM002"]),
        Supplier("SUP102", "Polymer Solutions", "Canada", 0.88, 7, ["RM003"]),
        Supplier("SUP103", "Global Metals", "Mexico", 0.82, 14, ["RM001", "RM002"]),
    ]

    llm = OllamaProvider(model="llama3.2")
    report = await optimize_supply_chain(products, inventory, suppliers, llm)
    return report


async def main():
    """Run example supply chain optimizations"""

    print("Supply Chain Optimization System")
    print("=" * 60)

    # Example 1: E-commerce
    print("\n\nExample 1: E-commerce Supply Chain")
    await example_ecommerce_supply_chain()

    # Example 2: Manufacturing
    print("\n\nExample 2: Manufacturing Supply Chain")
    await example_manufacturing_supply_chain()


if __name__ == "__main__":
    asyncio.run(main())
