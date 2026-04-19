"""
Real-world Use Case: Medical Diagnosis Assistant

This example demonstrates a medical diagnosis support system using AgentMind.
The system assists healthcare professionals by analyzing symptoms, reviewing
medical history, suggesting diagnoses, and recommending tests.

DISCLAIMER: This is for educational purposes only. Not for actual medical use.
Always consult qualified healthcare professionals for medical advice.

Features:
- Multi-agent medical analysis
- Symptom analysis and pattern recognition
- Differential diagnosis generation
- Test recommendation
- Treatment suggestion
- Medical literature search
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class Urgency(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class Symptom:
    """Represents a patient symptom"""

    name: str
    severity: Severity
    duration_days: int
    description: str


@dataclass
class PatientCase:
    """Represents a patient case for diagnosis"""

    case_id: str
    age: int
    gender: str
    symptoms: List[Symptom]
    medical_history: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    vital_signs: Dict[str, float] = field(default_factory=dict)


@dataclass
class DiagnosisResult:
    """Diagnosis analysis result"""

    case_id: str
    differential_diagnoses: List[Dict[str, any]]
    recommended_tests: List[str]
    urgency: Urgency
    treatment_suggestions: List[str]
    specialist_referral: Optional[str]
    confidence_score: float
    reasoning: str


# Custom Tools for Medical Analysis


class SymptomAnalyzerTool(Tool):
    """Analyzes symptoms and identifies patterns"""

    def __init__(self):
        super().__init__(
            name="analyze_symptoms",
            description="Analyze patient symptoms and identify patterns",
            parameters={
                "symptoms": {"type": "array", "description": "List of symptoms"},
                "vital_signs": {"type": "object", "description": "Patient vital signs"},
            },
        )

    async def execute(self, symptoms: List[Dict], vital_signs: Dict) -> str:
        """Analyze symptoms for patterns and severity"""
        analysis = {
            "symptom_count": len(symptoms),
            "severity_distribution": {},
            "duration_analysis": {},
            "vital_signs_status": {},
        }

        # Analyze severity distribution
        for symptom in symptoms:
            severity = symptom.get("severity", "unknown")
            analysis["severity_distribution"][severity] = (
                analysis["severity_distribution"].get(severity, 0) + 1
            )

        # Analyze vital signs
        if vital_signs:
            temp = vital_signs.get("temperature", 37.0)
            bp_sys = vital_signs.get("blood_pressure_systolic", 120)
            heart_rate = vital_signs.get("heart_rate", 70)

            analysis["vital_signs_status"] = {
                "temperature": "elevated" if temp > 37.5 else "normal",
                "blood_pressure": "elevated" if bp_sys > 140 else "normal",
                "heart_rate": "elevated" if heart_rate > 100 else "normal",
            }

        return f"Symptom Analysis: {analysis}"


class MedicalKnowledgeBaseTool(Tool):
    """Searches medical knowledge base for conditions"""

    def __init__(self):
        super().__init__(
            name="search_medical_kb",
            description="Search medical knowledge base for conditions and treatments",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "category": {
                    "type": "string",
                    "description": "Category: diagnosis, treatment, or test",
                },
            },
        )

        # Simulated medical knowledge base
        self.knowledge_base = {
            "fever + cough + fatigue": {
                "conditions": ["Influenza", "COVID-19", "Pneumonia", "Bronchitis"],
                "tests": ["PCR test", "Chest X-ray", "Blood count"],
                "treatments": ["Rest", "Hydration", "Antipyretics"],
            },
            "chest pain + shortness of breath": {
                "conditions": [
                    "Myocardial infarction",
                    "Pulmonary embolism",
                    "Pneumonia",
                    "Anxiety",
                ],
                "tests": ["ECG", "Troponin", "D-dimer", "Chest X-ray"],
                "treatments": ["Emergency evaluation", "Oxygen therapy"],
            },
            "headache + nausea + sensitivity to light": {
                "conditions": [
                    "Migraine",
                    "Meningitis",
                    "Intracranial pressure",
                    "Cluster headache",
                ],
                "tests": ["CT scan", "Lumbar puncture", "Blood tests"],
                "treatments": ["Pain management", "Anti-nausea medication"],
            },
        }

    async def execute(self, query: str, category: str = "diagnosis") -> str:
        """Search knowledge base"""
        # Simple keyword matching
        results = []
        query_lower = query.lower()

        for key, data in self.knowledge_base.items():
            if any(term in query_lower for term in key.split(" + ")):
                results.append({"pattern": key, "data": data})

        if not results:
            return "No specific matches found. Recommend comprehensive evaluation."

        return f"Medical KB Results: {results}"


class DiagnosticTestRecommenderTool(Tool):
    """Recommends diagnostic tests based on symptoms"""

    def __init__(self):
        super().__init__(
            name="recommend_tests",
            description="Recommend diagnostic tests based on differential diagnosis",
            parameters={
                "suspected_conditions": {
                    "type": "array",
                    "description": "List of suspected conditions",
                },
                "urgency": {"type": "string", "description": "Case urgency level"},
            },
        )

    async def execute(self, suspected_conditions: List[str], urgency: str) -> str:
        """Recommend appropriate tests"""
        test_recommendations = []

        # Map conditions to tests
        test_mapping = {
            "influenza": ["Rapid flu test", "PCR test"],
            "covid-19": ["COVID-19 PCR", "Rapid antigen test"],
            "pneumonia": ["Chest X-ray", "Blood culture", "Sputum culture"],
            "myocardial infarction": ["ECG", "Troponin", "CK-MB", "Echocardiogram"],
            "migraine": ["CT scan", "MRI", "Blood tests"],
            "diabetes": ["Fasting glucose", "HbA1c", "Oral glucose tolerance test"],
        }

        for condition in suspected_conditions:
            condition_lower = condition.lower()
            for key, tests in test_mapping.items():
                if key in condition_lower:
                    test_recommendations.extend(tests)

        # Remove duplicates
        test_recommendations = list(set(test_recommendations))

        # Prioritize based on urgency
        if urgency == "emergency":
            priority_tests = ["ECG", "Troponin", "CT scan", "Blood culture"]
            test_recommendations = [t for t in priority_tests if t in test_recommendations] + [
                t for t in test_recommendations if t not in priority_tests
            ]

        return f"Recommended Tests: {test_recommendations}"


# Agent System Setup


async def create_medical_diagnosis_system(llm_provider) -> AgentMind:
    """Create the medical diagnosis agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Symptom Analyzer Agent
    symptom_analyzer = Agent(
        name="Symptom_Analyzer",
        role="symptom_analysis",
        system_prompt="""You are an expert medical symptom analyzer. Your role is to:
        1. Carefully analyze all reported symptoms
        2. Identify symptom patterns and clusters
        3. Assess severity and urgency
        4. Note any red flags or concerning signs
        5. Consider vital signs in your analysis

        Be thorough and systematic. Flag any emergency symptoms immediately.""",
        tools=[SymptomAnalyzerTool()],
    )

    # Differential Diagnosis Agent
    diagnosis_agent = Agent(
        name="Diagnosis_Specialist",
        role="differential_diagnosis",
        system_prompt="""You are an expert diagnostician. Your role is to:
        1. Generate a comprehensive differential diagnosis list
        2. Rank diagnoses by likelihood based on symptoms
        3. Consider patient history and risk factors
        4. Identify life-threatening conditions first
        5. Provide reasoning for each diagnosis

        Use evidence-based medicine. Consider common conditions first, but don't miss rare but serious ones.""",
        tools=[MedicalKnowledgeBaseTool()],
    )

    # Test Recommendation Agent
    test_recommender = Agent(
        name="Test_Recommender",
        role="diagnostic_testing",
        system_prompt="""You are a diagnostic testing specialist. Your role is to:
        1. Recommend appropriate diagnostic tests
        2. Prioritize tests based on urgency and likelihood
        3. Consider cost-effectiveness
        4. Avoid unnecessary testing
        5. Ensure critical tests are not missed

        Balance thoroughness with practicality.""",
        tools=[DiagnosticTestRecommenderTool()],
    )

    # Treatment Advisor Agent
    treatment_advisor = Agent(
        name="Treatment_Advisor",
        role="treatment_planning",
        system_prompt="""You are a treatment planning specialist. Your role is to:
        1. Suggest initial treatment approaches
        2. Consider patient allergies and contraindications
        3. Recommend specialist referrals when needed
        4. Provide emergency interventions for urgent cases
        5. Consider evidence-based guidelines

        Patient safety is paramount. When in doubt, recommend specialist consultation.""",
    )

    # Add all agents
    mind.add_agent(symptom_analyzer)
    mind.add_agent(diagnosis_agent)
    mind.add_agent(test_recommender)
    mind.add_agent(treatment_advisor)

    return mind


async def analyze_patient_case(case: PatientCase, llm_provider) -> DiagnosisResult:
    """Analyze a patient case and generate diagnosis recommendations"""

    print(f"\n{'='*60}")
    print(f"Analyzing Patient Case: {case.case_id}")
    print(f"{'='*60}\n")

    # Create the medical system
    mind = await create_medical_diagnosis_system(llm_provider)

    # Format the case for analysis
    case_description = f"""
Patient Case Analysis Request:

Patient Information:
- Age: {case.age}
- Gender: {case.gender}

Symptoms:
{chr(10).join(f"- {s.name}: {s.severity.value} severity, {s.duration_days} days duration - {s.description}" for s in case.symptoms)}

Medical History:
{chr(10).join(f"- {h}" for h in case.medical_history) if case.medical_history else "- None reported"}

Current Medications:
{chr(10).join(f"- {m}" for m in case.medications) if case.medications else "- None"}

Allergies:
{chr(10).join(f"- {a}" for a in case.allergies) if case.allergies else "- None known"}

Vital Signs:
{chr(10).join(f"- {k}: {v}" for k, v in case.vital_signs.items()) if case.vital_signs else "- Not provided"}

Please provide:
1. Differential diagnosis (ranked by likelihood)
2. Recommended diagnostic tests
3. Urgency assessment
4. Initial treatment suggestions
5. Specialist referral recommendations if needed
"""

    # Collaborate to analyze the case
    result = await mind.collaborate(task=case_description, max_rounds=4)

    print(f"\n{'='*60}")
    print("Analysis Complete")
    print(f"{'='*60}\n")
    print(result)

    # Parse result into structured format (simplified)
    diagnosis_result = DiagnosisResult(
        case_id=case.case_id,
        differential_diagnoses=[{"condition": "See detailed analysis", "likelihood": "high"}],
        recommended_tests=["See detailed analysis"],
        urgency=Urgency.ROUTINE,
        treatment_suggestions=["See detailed analysis"],
        specialist_referral="See detailed analysis",
        confidence_score=0.85,
        reasoning=result,
    )

    return diagnosis_result


# Example Cases


async def example_respiratory_infection():
    """Example: Respiratory infection case"""

    case = PatientCase(
        case_id="CASE-001",
        age=35,
        gender="Female",
        symptoms=[
            Symptom("Fever", Severity.MODERATE, 3, "Temperature 38.5°C"),
            Symptom("Cough", Severity.MODERATE, 4, "Dry cough, worse at night"),
            Symptom("Fatigue", Severity.SEVERE, 5, "Extreme tiredness"),
            Symptom("Body aches", Severity.MODERATE, 3, "Generalized muscle pain"),
        ],
        medical_history=["Asthma (controlled)"],
        medications=["Albuterol inhaler as needed"],
        allergies=["Penicillin"],
        vital_signs={
            "temperature": 38.5,
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 80,
            "heart_rate": 88,
            "respiratory_rate": 18,
            "oxygen_saturation": 96,
        },
    )

    llm = OllamaProvider(model="llama3.2")
    result = await analyze_patient_case(case, llm)
    return result


async def example_cardiac_symptoms():
    """Example: Cardiac symptoms case"""

    case = PatientCase(
        case_id="CASE-002",
        age=58,
        gender="Male",
        symptoms=[
            Symptom("Chest pain", Severity.SEVERE, 0, "Crushing chest pain, radiating to left arm"),
            Symptom("Shortness of breath", Severity.SEVERE, 0, "Difficulty breathing"),
            Symptom("Sweating", Severity.MODERATE, 0, "Profuse sweating"),
            Symptom("Nausea", Severity.MODERATE, 0, "Feeling nauseous"),
        ],
        medical_history=["Hypertension", "High cholesterol", "Type 2 diabetes"],
        medications=["Lisinopril", "Atorvastatin", "Metformin"],
        allergies=[],
        vital_signs={
            "temperature": 37.2,
            "blood_pressure_systolic": 160,
            "blood_pressure_diastolic": 95,
            "heart_rate": 110,
            "respiratory_rate": 22,
            "oxygen_saturation": 94,
        },
    )

    llm = OllamaProvider(model="llama3.2")
    result = await analyze_patient_case(case, llm)
    return result


async def main():
    """Run example cases"""

    print("Medical Diagnosis Assistant - Example Cases")
    print("=" * 60)
    print("DISCLAIMER: For educational purposes only.")
    print("Not for actual medical use. Always consult healthcare professionals.")
    print("=" * 60)

    # Example 1: Respiratory infection
    print("\n\nExample 1: Respiratory Infection")
    await example_respiratory_infection()

    # Example 2: Cardiac symptoms (EMERGENCY)
    print("\n\nExample 2: Cardiac Symptoms (EMERGENCY)")
    await example_cardiac_symptoms()


if __name__ == "__main__":
    asyncio.run(main())
