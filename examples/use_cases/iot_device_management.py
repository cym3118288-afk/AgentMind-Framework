"""
Real - world Use Case: IoT Device Management

This example demonstrates an IoT device management system using AgentMind.
The system monitors, controls, and optimizes IoT devices across smart homes,
industrial settings, and smart cities.

Features:
- Multi - agent device monitoring
- Predictive maintenance
- Energy optimization
- Anomaly detection
- Automated control and scheduling
- Security monitoring
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class DeviceType(str, Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CAMERA = "camera"
    THERMOSTAT = "thermostat"
    LIGHT = "light"
    LOCK = "lock"
    APPLIANCE = "appliance"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class IoTDevice:
    """Represents an IoT device"""

    device_id: str
    name: str
    device_type: DeviceType
    location: str
    status: DeviceStatus
    last_seen: datetime
    firmware_version: str
    battery_level: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class DeviceAlert:
    """Alert from IoT device"""

    alert_id: str
    device_id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False


@dataclass
class MaintenanceSchedule:
    """Maintenance schedule for devices"""

    device_id: str
    next_maintenance: datetime
    maintenance_type: str
    estimated_duration: int  # minutes
    priority: int


@dataclass
class IoTManagementReport:
    """Complete IoT management report"""

    total_devices: int
    online_devices: int
    alerts: List[DeviceAlert]
    maintenance_needed: List[str]
    energy_optimization: Dict[str, any]
    security_status: Dict[str, any]
    recommendations: List[str]


# Custom Tools for IoT Management


class DeviceMonitorTool(Tool):
    """Monitors IoT device health and status"""

    def __init__(self):
        super().__init__(
            name="monitor_devices",
            description="Monitor IoT device health, status, and metrics",
            parameters={
                "device_ids": {"type": "array", "description": "List of device IDs to monitor"},
                "metrics": {"type": "array", "description": "Metrics to check"},
            },
        )

    async def execute(self, device_ids: List[str], metrics: List[str] = None) -> str:
        """Monitor devices"""
        metrics = metrics or ["status", "battery", "connectivity"]

        monitoring_results = []

        for device_id in device_ids:
            # Simulate device monitoring
            result = {
                "device_id": device_id,
                "status": random.choice(["online", "online", "online", "warning"]),
                "uptime": random.randint(1, 720),  # hours
                "battery_level": random.uniform(20, 100) if random.random() > 0.3 else None,
                "signal_strength": random.uniform(50, 100),
                "last_update": "2 minutes ago",
                "metrics": {},
            }

            # Add specific metrics
            if "temperature" in metrics:
                result["metrics"]["temperature"] = random.uniform(18, 28)
            if "humidity" in metrics:
                result["metrics"]["humidity"] = random.uniform(30, 70)
            if "power_consumption" in metrics:
                result["metrics"]["power_consumption"] = random.uniform(10, 500)

            monitoring_results.append(result)

        return f"Device Monitoring: {monitoring_results}"


class AnomalyDetectorTool(Tool):
    """Detects anomalies in IoT device behavior"""

    def __init__(self):
        super().__init__(
            name="detect_anomalies",
            description="Detect anomalous behavior in IoT devices",
            parameters={
                "device_data": {"type": "object", "description": "Device telemetry data"},
                "baseline": {"type": "object", "description": "Normal behavior baseline"},
            },
        )

    async def execute(self, device_data: Dict, baseline: Dict = None) -> str:
        """Detect anomalies"""
        baseline = baseline or {
            "temperature": {"min": 18, "max": 26},
            "power_consumption": {"min": 10, "max": 200},
            "response_time": {"max": 1000},
        }

        anomalies = []

        for metric, value in device_data.items():
            if metric in baseline:
                limits = baseline[metric]

                # Check if value is outside normal range
                if "min" in limits and value < limits["min"]:
                    anomalies.append(
                        {
                            "metric": metric,
                            "value": value,
                            "expected_min": limits["min"],
                            "severity": "warning",
                        }
                    )
                elif "max" in limits and value > limits["max"]:
                    anomalies.append(
                        {
                            "metric": metric,
                            "value": value,
                            "expected_max": limits["max"],
                            "severity": "critical" if value > limits["max"] * 1.5 else "warning",
                        }
                    )

        return f"Anomaly Detection: {anomalies if anomalies else 'No anomalies detected'}"


class PredictiveMaintenanceTool(Tool):
    """Predicts device maintenance needs"""

    def __init__(self):
        super().__init__(
            name="predict_maintenance",
            description="Predict when devices will need maintenance",
            parameters={
                "device_id": {"type": "string", "description": "Device ID"},
                "usage_data": {"type": "object", "description": "Device usage history"},
                "device_type": {"type": "string", "description": "Type of device"},
            },
        )

    async def execute(self, device_id: str, usage_data: Dict, device_type: str) -> str:
        """Predict maintenance needs"""

        # Simulate predictive analysis
        uptime_hours = usage_data.get("uptime_hours", 1000)
        error_count = usage_data.get("error_count", 0)
        last_maintenance = usage_data.get("days_since_maintenance", 90)

        # Calculate maintenance score (0 - 100, higher = more urgent)
        maintenance_score = min(
            100,
            ((uptime_hours / 100) * 0.3 + (error_count * 5) * 0.4 + (last_maintenance / 3) * 0.3),
        )

        prediction = {
            "device_id": device_id,
            "maintenance_score": round(maintenance_score, 2),
            "urgency": (
                "high" if maintenance_score > 70 else "medium" if maintenance_score > 40 else "low"
            ),
            "predicted_failure_date": None,
            "recommended_actions": [],
        }

        if maintenance_score > 70:
            prediction["predicted_failure_date"] = "Within 7 days"
            prediction["recommended_actions"] = [
                "Schedule immediate inspection",
                "Prepare replacement parts",
                "Plan downtime window",
            ]
        elif maintenance_score > 40:
            prediction["predicted_failure_date"] = "Within 30 days"
            prediction["recommended_actions"] = ["Schedule routine maintenance", "Monitor closely"]
        else:
            prediction["recommended_actions"] = ["Continue normal operation"]

        return f"Maintenance Prediction: {prediction}"


class EnergyOptimizerTool(Tool):
    """Optimizes energy consumption of IoT devices"""

    def __init__(self):
        super().__init__(
            name="optimize_energy",
            description="Optimize energy consumption across IoT devices",
            parameters={
                "devices": {"type": "array", "description": "List of devices"},
                "constraints": {"type": "object", "description": "Optimization constraints"},
            },
        )

    async def execute(self, devices: List[Dict], constraints: Dict = None) -> str:
        """Optimize energy usage"""
        constraints = constraints or {
            "max_total_power": 5000,  # watts
            "priority_devices": [],
            "time_of_use_rates": {"peak": 0.25, "off_peak": 0.10},
        }

        optimization = {
            "current_consumption": 0,
            "optimized_consumption": 0,
            "savings": 0,
            "recommendations": [],
        }

        total_power = sum(d.get("power_consumption", 0) for d in devices)
        optimization["current_consumption"] = total_power

        # Optimization strategies
        for device in devices:
            device_id = device.get("device_id")
            power = device.get("power_consumption", 0)
            device_type = device.get("device_type")

            # Suggest optimizations
            if device_type == "thermostat" and power > 100:
                optimization["recommendations"].append(
                    {
                        "device_id": device_id,
                        "action": "Adjust temperature by 2°C",
                        "estimated_savings": power * 0.15,
                    }
                )
            elif device_type == "light" and power > 50:
                optimization["recommendations"].append(
                    {
                        "device_id": device_id,
                        "action": "Switch to LED or dim lights",
                        "estimated_savings": power * 0.30,
                    }
                )
            elif device_type == "appliance":
                optimization["recommendations"].append(
                    {
                        "device_id": device_id,
                        "action": "Schedule for off - peak hours",
                        "estimated_savings": power * 0.40,
                    }
                )

        # Calculate total savings
        total_savings = sum(r["estimated_savings"] for r in optimization["recommendations"])
        optimization["optimized_consumption"] = total_power - total_savings
        optimization["savings"] = total_savings
        optimization["savings_percentage"] = (
            round((total_savings / total_power) * 100, 2) if total_power > 0 else 0
        )

        return f"Energy Optimization: {optimization}"


class SecurityMonitorTool(Tool):
    """Monitors IoT security"""

    def __init__(self):
        super().__init__(
            name="monitor_security",
            description="Monitor IoT device security and detect threats",
            parameters={
                "devices": {"type": "array", "description": "Devices to monitor"},
                "network_traffic": {"type": "object", "description": "Network traffic data"},
            },
        )

    async def execute(self, devices: List[Dict], network_traffic: Dict = None) -> str:
        """Monitor security"""

        security_status = {
            "overall_status": "secure",
            "vulnerabilities": [],
            "threats_detected": [],
            "recommendations": [],
        }

        for device in devices:
            device_id = device.get("device_id")
            firmware = device.get("firmware_version", "unknown")

            # Check for outdated firmware
            if firmware == "unknown" or firmware < "2.0":
                security_status["vulnerabilities"].append(
                    {
                        "device_id": device_id,
                        "issue": "Outdated firmware",
                        "severity": "high",
                        "recommendation": "Update firmware immediately",
                    }
                )

            # Check for weak authentication
            if device.get("auth_type") == "none":
                security_status["vulnerabilities"].append(
                    {
                        "device_id": device_id,
                        "issue": "No authentication",
                        "severity": "critical",
                        "recommendation": "Enable authentication",
                    }
                )

            # Check for unusual activity
            if device.get("failed_login_attempts", 0) > 5:
                security_status["threats_detected"].append(
                    {
                        "device_id": device_id,
                        "threat": "Brute force attack",
                        "severity": "critical",
                        "action": "Block IP and reset credentials",
                    }
                )

        # Update overall status
        if security_status["threats_detected"]:
            security_status["overall_status"] = "under_attack"
        elif security_status["vulnerabilities"]:
            security_status["overall_status"] = "vulnerable"

        return f"Security Status: {security_status}"


# Agent System Setup


async def create_iot_management_system(llm_provider) -> AgentMind:
    """Create the IoT device management agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Device Monitor Agent
    device_monitor = Agent(
        name="Device_Monitor",
        role="device_monitoring",
        system_prompt="""You are an IoT device monitoring specialist. Your role is to:
        1. Monitor device health and status continuously
        2. Track device metrics and telemetry
        3. Detect connectivity issues
        4. Monitor battery levels and power
        5. Alert on device failures

        Keep all devices running smoothly.""",
        tools=[DeviceMonitorTool()],
    )

    # Anomaly Detector Agent
    anomaly_detector = Agent(
        name="Anomaly_Detector",
        role="anomaly_detection",
        system_prompt="""You are an IoT anomaly detection specialist. Your role is to:
        1. Detect unusual device behavior
        2. Identify patterns that indicate problems
        3. Distinguish between normal variation and anomalies
        4. Alert on potential issues early
        5. Learn normal behavior patterns

        Catch problems before they become failures.""",
        tools=[AnomalyDetectorTool()],
    )

    # Maintenance Predictor Agent
    maintenance_predictor = Agent(
        name="Maintenance_Predictor",
        role="predictive_maintenance",
        system_prompt="""You are a predictive maintenance specialist. Your role is to:
        1. Predict when devices will need maintenance
        2. Schedule maintenance proactively
        3. Prevent unexpected failures
        4. Optimize maintenance schedules
        5. Reduce downtime

        Maintain devices before they fail.""",
        tools=[PredictiveMaintenanceTool()],
    )

    # Energy Optimizer Agent
    energy_optimizer = Agent(
        name="Energy_Optimizer",
        role="energy_optimization",
        system_prompt="""You are an energy optimization specialist. Your role is to:
        1. Minimize energy consumption
        2. Optimize device schedules
        3. Balance performance with efficiency
        4. Reduce costs
        5. Support sustainability goals

        Save energy without compromising functionality.""",
        tools=[EnergyOptimizerTool()],
    )

    # Security Monitor Agent
    security_monitor = Agent(
        name="Security_Monitor",
        role="security_monitoring",
        system_prompt="""You are an IoT security specialist. Your role is to:
        1. Monitor device security continuously
        2. Detect and respond to threats
        3. Ensure firmware is up to date
        4. Enforce security policies
        5. Protect against attacks

        Security is paramount. Be vigilant.""",
        tools=[SecurityMonitorTool()],
    )

    # Add all agents
    mind.add_agent(device_monitor)
    mind.add_agent(anomaly_detector)
    mind.add_agent(maintenance_predictor)
    mind.add_agent(energy_optimizer)
    mind.add_agent(security_monitor)

    return mind


async def manage_iot_infrastructure(devices: List[IoTDevice], llm_provider) -> IoTManagementReport:
    """Manage IoT device infrastructure"""

    print(f"\n{'=' * 60}")
    print("Managing IoT Infrastructure")
    print(f"Total Devices: {len(devices)}")
    print(f"{'=' * 60}\n")

    # Create the IoT management system
    mind = await create_iot_management_system(llm_provider)

    # Format device data
    # device_summary = "\n".join([
    #     f"- {d.name} ({d.device_type.value}): {d.status.value} at {d.location}"
    #     for d in devices
    # ])

    # Format the management request
    management_request = """
IoT Infrastructure Management:

Devices ({len(devices)} total):
{device_summary}

Please perform comprehensive IoT management including:

1. DEVICE MONITORING
   - Check health and status of all devices
   - Monitor key metrics and telemetry
   - Identify offline or problematic devices

2. ANOMALY DETECTION
   - Detect unusual behavior patterns
   - Identify potential issues
   - Alert on anomalies

3. PREDICTIVE MAINTENANCE
   - Predict maintenance needs
   - Schedule proactive maintenance
   - Prevent failures

4. ENERGY OPTIMIZATION
   - Analyze energy consumption
   - Recommend optimizations
   - Reduce costs

5. SECURITY MONITORING
   - Check security status
   - Detect threats
   - Recommend security improvements

Provide actionable recommendations for optimal IoT operations.
"""

    # Collaborate to manage infrastructure
    result = await mind.collaborate(task=management_request, max_rounds=5)

    print(f"\n{'=' * 60}")
    print("IoT Management Complete")
    print(f"{'=' * 60}\n")
    print(result)

    # Create management report
    online_count = sum(1 for d in devices if d.status == DeviceStatus.ONLINE)

    report = IoTManagementReport(
        total_devices=len(devices),
        online_devices=online_count,
        alerts=[],
        maintenance_needed=[],
        energy_optimization={},
        security_status={},
        recommendations=[],
    )

    return report


# Example IoT Scenarios


async def example_smart_home():
    """Example: Smart home management"""

    devices = [
        IoTDevice(
            "SH001",
            "Living Room Thermostat",
            DeviceType.THERMOSTAT,
            "Living Room",
            DeviceStatus.ONLINE,
            datetime.now(),
            "2.1.0",
            metrics={"temperature": 22.5, "humidity": 45},
        ),
        IoTDevice(
            "SH002",
            "Front Door Lock",
            DeviceType.LOCK,
            "Front Door",
            DeviceStatus.ONLINE,
            datetime.now(),
            "1.8.0",
            battery_level=85,
        ),
        IoTDevice(
            "SH003",
            "Kitchen Light",
            DeviceType.LIGHT,
            "Kitchen",
            DeviceStatus.ONLINE,
            datetime.now(),
            "2.0.0",
        ),
        IoTDevice(
            "SH004",
            "Security Camera",
            DeviceType.CAMERA,
            "Driveway",
            DeviceStatus.WARNING,
            datetime.now(),
            "1.5.0",
            metrics={"motion_detected": 5},
        ),
        IoTDevice(
            "SH005",
            "Bedroom Sensor",
            DeviceType.SENSOR,
            "Bedroom",
            DeviceStatus.ONLINE,
            datetime.now(),
            "2.2.0",
            battery_level=45,
        ),
    ]

    llm = OllamaProvider(model="llama3.2")
    report = await manage_iot_infrastructure(devices, llm)
    return report


async def example_industrial_iot():
    """Example: Industrial IoT management"""

    devices = [
        IoTDevice(
            "IND001",
            "Temperature Sensor A1",
            DeviceType.SENSOR,
            "Production Line 1",
            DeviceStatus.ONLINE,
            datetime.now(),
            "3.0.0",
            metrics={"temperature": 85.2},
        ),
        IoTDevice(
            "IND002",
            "Pressure Sensor B2",
            DeviceType.SENSOR,
            "Tank 2",
            DeviceStatus.ONLINE,
            datetime.now(),
            "3.0.0",
            metrics={"pressure": 120.5},
        ),
        IoTDevice(
            "IND003",
            "Motor Controller",
            DeviceType.ACTUATOR,
            "Assembly Line",
            DeviceStatus.WARNING,
            datetime.now(),
            "2.5.0",
            metrics={"rpm": 1500, "vibration": 8.5},
        ),
        IoTDevice(
            "IND004",
            "Quality Camera",
            DeviceType.CAMERA,
            "Inspection Station",
            DeviceStatus.ONLINE,
            datetime.now(),
            "2.8.0",
        ),
        IoTDevice(
            "IND005",
            "Valve Actuator",
            DeviceType.ACTUATOR,
            "Cooling System",
            DeviceStatus.ONLINE,
            datetime.now(),
            "3.1.0",
        ),
    ]

    llm = OllamaProvider(model="llama3.2")
    report = await manage_iot_infrastructure(devices, llm)
    return report


async def main():
    """Run example IoT management scenarios"""

    print("IoT Device Management System")
    print("=" * 60)

    # Example 1: Smart Home
    print("\n\nExample 1: Smart Home Management")
    await example_smart_home()

    # Example 2: Industrial IoT
    print("\n\nExample 2: Industrial IoT Management")
    await example_industrial_iot()


if __name__ == "__main__":
    asyncio.run(main())
