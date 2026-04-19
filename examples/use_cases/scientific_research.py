"""
Real-world Use Case: Scientific Research Automation

This example demonstrates a scientific research automation system using AgentMind.
The system assists researchers by analyzing papers, designing experiments,
analyzing data, and generating research reports.

Features:
- Multi-agent research collaboration
- Literature review and synthesis
- Experiment design and methodology
- Data analysis and visualization
- Hypothesis generation and testing
- Research report generation
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class ResearchField(str, Enum):
    BIOLOGY = "biology"
    CHEMISTRY = "chemistry"
    PHYSICS = "physics"
    COMPUTER_SCIENCE = "computer_science"
    MEDICINE = "medicine"
    PSYCHOLOGY = "psychology"


class ExperimentStatus(str, Enum):
    DESIGNED = "designed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"


@dataclass
class ResearchPaper:
    """Represents a scientific paper"""

    title: str
    authors: List[str]
    abstract: str
    year: int
    journal: str
    citations: int = 0
    key_findings: List[str] = field(default_factory=list)


@dataclass
class Experiment:
    """Represents a scientific experiment"""

    experiment_id: str
    title: str
    hypothesis: str
    methodology: str
    variables: Dict[str, List[str]]
    expected_outcomes: List[str]
    status: ExperimentStatus = ExperimentStatus.DESIGNED


@dataclass
class ResearchData:
    """Represents experimental data"""

    experiment_id: str
    measurements: List[Dict[str, float]]
    observations: List[str]
    statistical_summary: Dict[str, float]


@dataclass
class ResearchReport:
    """Complete research report"""

    title: str
    research_question: str
    literature_review: str
    methodology: str
    results: str
    discussion: str
    conclusions: List[str]
    future_work: List[str]
    references: List[str]


# Custom Tools for Research


class LiteratureSearchTool(Tool):
    """Searches scientific literature"""

    def __init__(self):
        super().__init__(
            name="search_literature",
            description="Search scientific literature for relevant papers",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "field": {"type": "string", "description": "Research field"},
                "year_from": {"type": "integer", "description": "Start year"},
            },
        )

        # Simulated paper database
        self.papers = [
            ResearchPaper(
                title="Deep Learning for Protein Structure Prediction",
                authors=["Smith, J.", "Johnson, A."],
                abstract="Novel deep learning approach for predicting protein structures...",
                year=2023,
                journal="Nature",
                citations=150,
                key_findings=["90% accuracy", "Faster than traditional methods"],
            ),
            ResearchPaper(
                title="CRISPR Gene Editing in Cancer Treatment",
                authors=["Lee, K.", "Wang, M."],
                abstract="Application of CRISPR technology for targeted cancer therapy...",
                year=2024,
                journal="Science",
                citations=89,
                key_findings=["Successful in vitro trials", "Minimal off-target effects"],
            ),
            ResearchPaper(
                title="Quantum Computing for Drug Discovery",
                authors=["Brown, R.", "Davis, S."],
                abstract="Using quantum algorithms to accelerate drug discovery...",
                year=2023,
                journal="Nature Biotechnology",
                citations=120,
                key_findings=["10x speedup", "Novel compounds identified"],
            ),
        ]

    async def execute(self, query: str, field: str = "biology", year_from: int = 2020) -> str:
        """Search for papers"""
        query_lower = query.lower()
        results = []

        for paper in self.papers:
            if paper.year >= year_from:
                # Simple keyword matching
                if any(
                    term in paper.title.lower() or term in paper.abstract.lower()
                    for term in query_lower.split()
                ):
                    results.append(
                        {
                            "title": paper.title,
                            "authors": paper.authors,
                            "year": paper.year,
                            "journal": paper.journal,
                            "citations": paper.citations,
                            "key_findings": paper.key_findings,
                        }
                    )

        return f"Found {len(results)} papers: {results}"


class ExperimentDesignTool(Tool):
    """Designs scientific experiments"""

    def __init__(self):
        super().__init__(
            name="design_experiment",
            description="Design a scientific experiment with proper methodology",
            parameters={
                "hypothesis": {"type": "string", "description": "Research hypothesis"},
                "field": {"type": "string", "description": "Research field"},
                "constraints": {"type": "object", "description": "Experimental constraints"},
            },
        )

    async def execute(self, hypothesis: str, field: str, constraints: Dict = None) -> str:
        """Design an experiment"""
        constraints = constraints or {}

        design = {
            "hypothesis": hypothesis,
            "field": field,
            "methodology": self._suggest_methodology(field),
            "variables": self._identify_variables(hypothesis),
            "controls": self._suggest_controls(field),
            "sample_size": self._calculate_sample_size(constraints),
            "duration": self._estimate_duration(field),
            "equipment": self._list_equipment(field),
            "safety_considerations": self._safety_checks(field),
        }

        return f"Experiment Design: {design}"

    def _suggest_methodology(self, field: str) -> str:
        methodologies = {
            "biology": "Randomized controlled trial with proper controls",
            "chemistry": "Systematic synthesis and characterization",
            "physics": "Controlled measurement with error analysis",
            "computer_science": "Benchmarking with statistical validation",
        }
        return methodologies.get(field, "Standard scientific methodology")

    def _identify_variables(self, hypothesis: str) -> Dict[str, List[str]]:
        return {
            "independent": ["Variable to be manipulated"],
            "dependent": ["Variable to be measured"],
            "controlled": ["Variables to keep constant"],
        }

    def _suggest_controls(self, field: str) -> List[str]:
        return ["Positive control", "Negative control", "Blank control"]

    def _calculate_sample_size(self, constraints: Dict) -> int:
        budget = constraints.get("budget", 10000)
        return min(100, budget // 100)  # Simplified

    def _estimate_duration(self, field: str) -> str:
        durations = {
            "biology": "6-12 months",
            "chemistry": "3-6 months",
            "physics": "3-9 months",
            "computer_science": "2-4 months",
        }
        return durations.get(field, "6 months")

    def _list_equipment(self, field: str) -> List[str]:
        equipment = {
            "biology": ["Microscope", "Centrifuge", "PCR machine", "Incubator"],
            "chemistry": ["Spectrometer", "Chromatograph", "pH meter", "Balance"],
            "physics": ["Oscilloscope", "Laser", "Detector", "Data acquisition system"],
        }
        return equipment.get(field, ["Standard lab equipment"])

    def _safety_checks(self, field: str) -> List[str]:
        return [
            "PPE required",
            "Proper ventilation",
            "Waste disposal protocol",
            "Emergency procedures",
        ]


class DataAnalysisTool(Tool):
    """Analyzes experimental data"""

    def __init__(self):
        super().__init__(
            name="analyze_data",
            description="Perform statistical analysis on experimental data",
            parameters={
                "data": {"type": "array", "description": "Experimental measurements"},
                "analysis_type": {"type": "string", "description": "Type of analysis"},
            },
        )

    async def execute(self, data: List[Dict], analysis_type: str = "descriptive") -> str:
        """Analyze data"""
        if not data:
            return "No data provided"

        # Extract numeric values
        values = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    values.append(value)

        if not values:
            return "No numeric data found"

        # Calculate statistics
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = variance**0.5
        min_val = min(values)
        max_val = max(values)

        analysis = {
            "sample_size": n,
            "mean": round(mean, 3),
            "std_dev": round(std_dev, 3),
            "min": min_val,
            "max": max_val,
            "range": max_val - min_val,
            "coefficient_of_variation": round((std_dev / mean) * 100, 2) if mean != 0 else 0,
        }

        # Hypothesis testing (simplified)
        if analysis_type == "hypothesis_test":
            # Simple t-test simulation
            t_statistic = mean / (std_dev / (n**0.5)) if std_dev > 0 else 0
            analysis["t_statistic"] = round(t_statistic, 3)
            analysis["significant"] = abs(t_statistic) > 2.0  # Simplified

        return f"Statistical Analysis: {analysis}"


class HypothesisGeneratorTool(Tool):
    """Generates research hypotheses"""

    def __init__(self):
        super().__init__(
            name="generate_hypothesis",
            description="Generate testable research hypotheses",
            parameters={
                "research_question": {"type": "string", "description": "Research question"},
                "background": {"type": "string", "description": "Background information"},
                "field": {"type": "string", "description": "Research field"},
            },
        )

    async def execute(self, research_question: str, background: str, field: str) -> str:
        """Generate hypotheses"""
        hypotheses = {
            "null_hypothesis": f"There is no significant effect or relationship in {research_question}",
            "alternative_hypothesis": f"There is a significant effect or relationship in {research_question}",
            "testable_predictions": [
                "Prediction 1: Measurable outcome A will differ from baseline",
                "Prediction 2: Variable X will correlate with Variable Y",
                "Prediction 3: Treatment group will show significant difference from control",
            ],
            "assumptions": [
                "Normal distribution of data",
                "Independent observations",
                "Homogeneity of variance",
            ],
            "falsifiability": "Hypothesis can be tested and potentially disproven through experimentation",
        }

        return f"Generated Hypotheses: {hypotheses}"


# Agent System Setup


async def create_research_system(llm_provider) -> AgentMind:
    """Create the scientific research agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Literature Review Agent
    literature_reviewer = Agent(
        name="Literature_Reviewer",
        role="literature_review",
        system_prompt="""You are an expert scientific literature reviewer. Your role is to:
        1. Search and analyze relevant scientific papers
        2. Synthesize findings from multiple sources
        3. Identify research gaps and opportunities
        4. Evaluate the quality and relevance of studies
        5. Summarize the current state of knowledge

        Be thorough and critical. Cite sources properly.""",
        tools=[LiteratureSearchTool()],
    )

    # Hypothesis Generator Agent
    hypothesis_generator = Agent(
        name="Hypothesis_Generator",
        role="hypothesis_generation",
        system_prompt="""You are a scientific hypothesis generator. Your role is to:
        1. Formulate testable research hypotheses
        2. Ensure hypotheses are specific and measurable
        3. Consider alternative explanations
        4. Generate null and alternative hypotheses
        5. Predict expected outcomes

        Make hypotheses clear, testable, and scientifically sound.""",
        tools=[HypothesisGeneratorTool()],
    )

    # Experiment Designer Agent
    experiment_designer = Agent(
        name="Experiment_Designer",
        role="experiment_design",
        system_prompt="""You are an experimental design specialist. Your role is to:
        1. Design rigorous scientific experiments
        2. Identify and control variables
        3. Determine appropriate sample sizes
        4. Plan proper controls and replication
        5. Consider ethical and safety issues

        Design experiments that are feasible, ethical, and scientifically valid.""",
        tools=[ExperimentDesignTool()],
    )

    # Data Analyst Agent
    data_analyst = Agent(
        name="Data_Analyst",
        role="data_analysis",
        system_prompt="""You are a scientific data analyst. Your role is to:
        1. Perform statistical analysis on experimental data
        2. Identify patterns and trends
        3. Test hypotheses with appropriate methods
        4. Assess statistical significance
        5. Visualize results effectively

        Use rigorous statistical methods. Report confidence intervals and p-values.""",
        tools=[DataAnalysisTool()],
    )

    # Research Writer Agent
    research_writer = Agent(
        name="Research_Writer",
        role="scientific_writing",
        system_prompt="""You are a scientific writer. Your role is to:
        1. Write clear, concise research reports
        2. Follow scientific writing conventions
        3. Present results objectively
        4. Discuss implications and limitations
        5. Suggest future research directions

        Write for a scientific audience. Be precise and objective.""",
    )

    # Add all agents
    mind.add_agent(literature_reviewer)
    mind.add_agent(hypothesis_generator)
    mind.add_agent(experiment_designer)
    mind.add_agent(data_analyst)
    mind.add_agent(research_writer)

    return mind


async def conduct_research_project(
    research_question: str, field: ResearchField, llm_provider
) -> ResearchReport:
    """Conduct a complete research project"""

    print(f"\n{'='*60}")
    print(f"Research Project: {research_question}")
    print(f"Field: {field.value}")
    print(f"{'='*60}\n")

    # Create the research system
    mind = await create_research_system(llm_provider)

    # Format the research request
    research_request = f"""
Scientific Research Project:

Research Question: {research_question}
Field: {field.value}

Please conduct a comprehensive research project including:

1. LITERATURE REVIEW
   - Search for relevant papers (last 5 years)
   - Synthesize current knowledge
   - Identify research gaps

2. HYPOTHESIS GENERATION
   - Formulate testable hypotheses
   - Generate predictions
   - Consider alternative explanations

3. EXPERIMENT DESIGN
   - Design rigorous experiments
   - Specify methodology and controls
   - Plan data collection

4. DATA ANALYSIS PLAN
   - Specify statistical methods
   - Plan for hypothesis testing
   - Consider potential confounds

5. RESEARCH REPORT
   - Synthesize all components
   - Discuss implications
   - Suggest future work

Provide a complete, publication-ready research plan.
"""

    # Collaborate to conduct research
    result = await mind.collaborate(task=research_request, max_rounds=5)

    print(f"\n{'='*60}")
    print("Research Project Complete")
    print(f"{'='*60}\n")
    print(result)

    # Create research report
    report = ResearchReport(
        title=research_question,
        research_question=research_question,
        literature_review="See detailed analysis",
        methodology="See detailed analysis",
        results="See detailed analysis",
        discussion="See detailed analysis",
        conclusions=["See detailed analysis"],
        future_work=["See detailed analysis"],
        references=[],
    )

    return report


# Example Research Projects


async def example_protein_folding():
    """Example: Protein folding research"""

    research_question = "Can machine learning predict protein folding patterns more accurately than traditional methods?"
    field = ResearchField.BIOLOGY

    llm = OllamaProvider(model="llama3.2")
    report = await conduct_research_project(research_question, field, llm)
    return report


async def example_drug_discovery():
    """Example: Drug discovery research"""

    research_question = (
        "What novel compounds show promise for treating antibiotic-resistant bacteria?"
    )
    field = ResearchField.CHEMISTRY

    llm = OllamaProvider(model="llama3.2")
    report = await conduct_research_project(research_question, field, llm)
    return report


async def example_quantum_computing():
    """Example: Quantum computing research"""

    research_question = "How can quantum algorithms improve optimization problems in logistics?"
    field = ResearchField.COMPUTER_SCIENCE

    llm = OllamaProvider(model="llama3.2")
    report = await conduct_research_project(research_question, field, llm)
    return report


async def main():
    """Run example research projects"""

    print("Scientific Research Automation System")
    print("=" * 60)

    # Example 1: Protein Folding
    print("\n\nExample 1: Protein Folding Research")
    await example_protein_folding()

    # Example 2: Drug Discovery
    print("\n\nExample 2: Drug Discovery Research")
    await example_drug_discovery()

    # Example 3: Quantum Computing
    print("\n\nExample 3: Quantum Computing Research")
    await example_quantum_computing()


if __name__ == "__main__":
    asyncio.run(main())
