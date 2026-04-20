"""
Real - world Use Case: Legal Document Analysis

This example demonstrates a legal document analysis system using AgentMind.
The system assists legal professionals by analyzing contracts, identifying risks,
extracting key terms, and providing compliance recommendations.

DISCLAIMER: This is for educational purposes only. Not for actual legal advice.
Always consult qualified legal professionals for legal matters.

Features:
- Multi - agent legal analysis
- Contract clause extraction
- Risk identification
- Compliance checking
- Term comparison
- Legal precedent search
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class DocumentType(str, Enum):
    CONTRACT = "contract"
    NDA = "nda"
    EMPLOYMENT = "employment_agreement"
    LEASE = "lease_agreement"
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LegalDocument:
    """Represents a legal document for analysis"""

    doc_id: str
    title: str
    doc_type: DocumentType
    content: str
    parties: List[str] = field(default_factory=list)
    jurisdiction: str = "US"
    date: Optional[datetime] = None


@dataclass
class ClauseAnalysis:
    """Analysis of a specific clause"""

    clause_type: str
    content: str
    risk_level: RiskLevel
    issues: List[str]
    recommendations: List[str]


@dataclass
class DocumentAnalysisResult:
    """Complete document analysis result"""

    doc_id: str
    summary: str
    key_terms: Dict[str, str]
    clauses: List[ClauseAnalysis]
    risks: List[Dict[str, any]]
    compliance_issues: List[str]
    recommendations: List[str]
    overall_risk_score: float
    missing_clauses: List[str]


# Custom Tools for Legal Analysis


class ClauseExtractorTool(Tool):
    """Extracts and categorizes clauses from legal documents"""

    def __init__(self):
        super().__init__(
            name="extract_clauses",
            description="Extract and categorize clauses from legal documents",
            parameters={
                "document": {"type": "string", "description": "Document text"},
                "doc_type": {"type": "string", "description": "Document type"},
            },
        )

        # Common clause patterns
        self.clause_patterns = {
            "termination": ["termination", "terminate", "cancellation"],
            "liability": ["liability", "indemnification", "indemnify"],
            "confidentiality": ["confidential", "non - disclosure", "proprietary"],
            "payment": ["payment", "compensation", "fee", "price"],
            "intellectual_property": ["intellectual property", "ip rights", "copyright", "patent"],
            "dispute_resolution": ["arbitration", "dispute", "litigation", "mediation"],
            "warranty": ["warranty", "guarantee", "representation"],
            "force_majeure": ["force majeure", "act of god", "unforeseeable"],
            "assignment": ["assignment", "transfer", "delegate"],
            "governing_law": ["governing law", "jurisdiction", "venue"],
        }

    async def execute(self, document: str, doc_type: str) -> str:
        """Extract clauses from document"""
        found_clauses = {}
        doc_lower = document.lower()

        for clause_type, keywords in self.clause_patterns.items():
            for keyword in keywords:
                if keyword in doc_lower:
                    found_clauses[clause_type] = True
                    break

        return f"Extracted Clauses: {list(found_clauses.keys())}"


class RiskAnalyzerTool(Tool):
    """Analyzes legal risks in documents"""

    def __init__(self):
        super().__init__(
            name="analyze_risks",
            description="Analyze legal risks in document clauses",
            parameters={
                "clauses": {"type": "array", "description": "List of clauses to analyze"},
                "doc_type": {"type": "string", "description": "Document type"},
            },
        )

        # Risk indicators
        self.risk_indicators = {
            "high": [
                "unlimited liability",
                "no limitation of liability",
                "perpetual license",
                "automatic renewal",
                "unilateral modification",
                "waive all rights",
                "sole discretion",
            ],
            "medium": [
                "may terminate",
                "reasonable efforts",
                "as - is",
                "no warranty",
                "third party beneficiary",
            ],
        }

    async def execute(self, clauses: List[str], doc_type: str) -> str:
        """Analyze risks in clauses"""
        risks = []

        for clause in clauses:
            clause_lower = clause.lower()

            # Check for high - risk terms
            for term in self.risk_indicators["high"]:
                if term in clause_lower:
                    risks.append({"level": "high", "term": term, "clause": clause[:100]})

            # Check for medium - risk terms
            for term in self.risk_indicators["medium"]:
                if term in clause_lower:
                    risks.append({"level": "medium", "term": term, "clause": clause[:100]})

        return f"Identified Risks: {risks}"


class ComplianceCheckerTool(Tool):
    """Checks document compliance with regulations"""

    def __init__(self):
        super().__init__(
            name="check_compliance",
            description="Check document compliance with legal regulations",
            parameters={
                "doc_type": {"type": "string", "description": "Document type"},
                "jurisdiction": {"type": "string", "description": "Legal jurisdiction"},
                "clauses": {"type": "array", "description": "Document clauses"},
            },
        )

        # Required clauses by document type
        self.required_clauses = {
            "employment_agreement": [
                "compensation",
                "termination",
                "confidentiality",
                "intellectual_property",
                "dispute_resolution",
            ],
            "nda": ["confidentiality", "term", "return_of_materials", "remedies"],
            "contract": ["payment", "termination", "liability", "governing_law"],
            "privacy_policy": [
                "data_collection",
                "data_use",
                "data_sharing",
                "user_rights",
                "security",
            ],
        }

    async def execute(self, doc_type: str, jurisdiction: str, clauses: List[str]) -> str:
        """Check compliance"""
        required = self.required_clauses.get(doc_type, [])
        present_clauses = [c.lower() for c in clauses]

        missing = []
        for req in required:
            if not any(req in clause for clause in present_clauses):
                missing.append(req)

        compliance_status = {
            "jurisdiction": jurisdiction,
            "required_clauses": required,
            "missing_clauses": missing,
            "compliance_score": (len(required) - len(missing)) / len(required) if required else 1.0,
        }

        return f"Compliance Check: {compliance_status}"


class LegalPrecedentSearchTool(Tool):
    """Searches for relevant legal precedents"""

    def __init__(self):
        super().__init__(
            name="search_precedents",
            description="Search for relevant legal precedents and case law",
            parameters={
                "issue": {"type": "string", "description": "Legal issue to research"},
                "jurisdiction": {"type": "string", "description": "Legal jurisdiction"},
            },
        )

        # Simulated precedent database
        self.precedents = {
            "liability limitation": [
                "Smith v. Tech Corp (2020): Liability caps upheld in commercial contracts",
                "Jones v. Services Inc (2019): Unconscionable limitation struck down",
            ],
            "non - compete": [
                "Brown v. Employer (2021): 2 - year non - compete deemed reasonable",
                "Davis v. Company (2020): Geographic restriction too broad",
            ],
            "intellectual property": [
                "Tech Co v. Developer (2022): Work - for - hire doctrine applied",
                "Creator v. Platform (2021): IP assignment must be explicit",
            ],
        }

    async def execute(self, issue: str, jurisdiction: str) -> str:
        """Search for precedents"""
        issue_lower = issue.lower()
        relevant_precedents = []

        for key, cases in self.precedents.items():
            if key in issue_lower:
                relevant_precedents.extend(cases)

        if not relevant_precedents:
            return "No specific precedents found. Recommend legal research."

        return f"Relevant Precedents: {relevant_precedents}"


# Agent System Setup


async def create_legal_analysis_system(llm_provider) -> AgentMind:
    """Create the legal document analysis agent system"""

    mind = AgentMind(llm_provider=llm_provider)

    # Document Analyzer Agent
    document_analyzer = Agent(
        name="Document_Analyzer",
        role="document_analysis",
        system_prompt="""You are an expert legal document analyzer. Your role is to:
        1. Read and understand the document structure
        2. Identify the document type and parties involved
        3. Extract key terms and conditions
        4. Summarize the document's purpose and scope
        5. Note any unusual or non - standard provisions

        Be thorough and precise. Legal language matters.""",
        tools=[ClauseExtractorTool()],
    )

    # Risk Assessment Agent
    risk_assessor = Agent(
        name="Risk_Assessor",
        role="risk_assessment",
        system_prompt="""You are a legal risk assessment specialist. Your role is to:
        1. Identify potential legal risks and liabilities
        2. Assess the severity of each risk
        3. Evaluate one - sided or unfavorable terms
        4. Flag ambiguous or problematic language
        5. Consider worst - case scenarios

        Protect the client's interests. Be conservative in risk assessment.""",
        tools=[RiskAnalyzerTool()],
    )

    # Compliance Specialist Agent
    compliance_specialist = Agent(
        name="Compliance_Specialist",
        role="compliance_review",
        system_prompt="""You are a legal compliance specialist. Your role is to:
        1. Check compliance with applicable laws and regulations
        2. Identify missing required clauses
        3. Verify proper legal formalities
        4. Ensure regulatory requirements are met
        5. Flag potential compliance violations

        Stay current with legal requirements. Compliance is non - negotiable.""",
        tools=[ComplianceCheckerTool()],
    )

    # Legal Research Agent
    legal_researcher = Agent(
        name="Legal_Researcher",
        role="legal_research",
        system_prompt="""You are a legal research specialist. Your role is to:
        1. Research relevant case law and precedents
        2. Analyze how courts have interpreted similar clauses
        3. Identify legal trends and best practices
        4. Provide context from legal scholarship
        5. Support analysis with legal authority

        Ground recommendations in legal precedent.""",
        tools=[LegalPrecedentSearchTool()],
    )

    # Advisory Agent
    advisory_agent = Agent(
        name="Legal_Advisor",
        role="legal_advisory",
        system_prompt="""You are a senior legal advisor. Your role is to:
        1. Synthesize analysis from all specialists
        2. Provide clear, actionable recommendations
        3. Suggest specific clause modifications
        4. Prioritize issues by importance
        5. Offer strategic legal advice

        Provide practical, business - minded legal counsel.""",
    )

    # Add all agents
    mind.add_agent(document_analyzer)
    mind.add_agent(risk_assessor)
    mind.add_agent(compliance_specialist)
    mind.add_agent(legal_researcher)
    mind.add_agent(advisory_agent)

    return mind


async def analyze_legal_document(document: LegalDocument, llm_provider) -> DocumentAnalysisResult:
    """Analyze a legal document"""

    print(f"\n{'=' * 60}")
    print(f"Analyzing Legal Document: {document.title}")
    print(f"{'=' * 60}\n")

    # Create the legal analysis system
    mind = await create_legal_analysis_system(llm_provider)

    # Format the document for analysis
    analysis_request = """
Legal Document Analysis Request:

Document Information:
- Title: {document.title}
- Type: {document.doc_type.value}
- Parties: {', '.join(document.parties)}
- Jurisdiction: {document.jurisdiction}

Document Content:
{document.content}

Please provide comprehensive analysis including:
1. Document summary and key terms
2. Clause - by - clause analysis
3. Risk assessment (identify all potential risks)
4. Compliance review (check for required clauses)
5. Legal precedent research (for key issues)
6. Recommendations for improvements or modifications
7. Missing or recommended additional clauses
"""

    # Collaborate to analyze the document
    result = await mind.collaborate(task=analysis_request, max_rounds=5)

    print(f"\n{'=' * 60}")
    print("Analysis Complete")
    print(f"{'=' * 60}\n")
    print(result)

    # Parse result into structured format (simplified)
    analysis_result = DocumentAnalysisResult(
        doc_id=document.doc_id,
        summary="See detailed analysis",
        key_terms={},
        clauses=[],
        risks=[],
        compliance_issues=[],
        recommendations=[],
        overall_risk_score=0.5,
        missing_clauses=[],
    )

    return analysis_result


# Example Documents


async def example_employment_agreement():
    """Example: Employment agreement analysis"""

    document = LegalDocument(
        doc_id="DOC - 001",
        title="Software Engineer Employment Agreement",
        doc_type=DocumentType.EMPLOYMENT,
        parties=["TechCorp Inc.", "John Developer"],
        jurisdiction="California, US",
        content="""
EMPLOYMENT AGREEMENT

This Employment Agreement is entered into between TechCorp Inc. ("Company")
and John Developer ("Employee").

1. POSITION AND DUTIES
Employee shall serve as Senior Software Engineer and perform duties as assigned.

2. COMPENSATION
Employee shall receive annual salary of $150,000, payable bi - weekly.

3. BENEFITS
Employee is eligible for standard company benefits including health insurance,
401(k) matching, and 15 days paid time off annually.

4. INTELLECTUAL PROPERTY
All work product, inventions, and intellectual property created during employment
shall be the sole property of the Company. Employee agrees to assign all rights.

5. CONFIDENTIALITY
Employee agrees to maintain confidentiality of all proprietary information
during and after employment.

6. NON - COMPETE
Employee agrees not to work for direct competitors for 18 months after termination
within a 50 - mile radius.

7. TERMINATION
Either party may terminate employment with 2 weeks notice. Company may terminate
immediately for cause.

8. AT - WILL EMPLOYMENT
This is at - will employment. Either party may terminate at any time for any reason.

9. GOVERNING LAW
This agreement shall be governed by California law.
""",
    )

    llm = OllamaProvider(model="llama3.2")
    result = await analyze_legal_document(document, llm)
    return result


async def example_nda():
    """Example: Non - disclosure agreement analysis"""

    document = LegalDocument(
        doc_id="DOC - 002",
        title="Mutual Non - Disclosure Agreement",
        doc_type=DocumentType.NDA,
        parties=["StartupCo", "InvestorGroup LLC"],
        jurisdiction="Delaware, US",
        content="""
MUTUAL NON - DISCLOSURE AGREEMENT

This Agreement is made between StartupCo ("Disclosing Party") and
InvestorGroup LLC ("Receiving Party").

1. CONFIDENTIAL INFORMATION
Confidential Information includes all business, technical, and financial
information disclosed by either party.

2. OBLIGATIONS
Receiving Party agrees to:
- Maintain confidentiality
- Use information only for evaluation purposes
- Not disclose to third parties without written consent

3. EXCLUSIONS
Confidential Information does not include information that:
- Is publicly available
- Was known prior to disclosure
- Is independently developed

4. TERM
This Agreement shall remain in effect for 3 years from the date of execution.

5. RETURN OF MATERIALS
Upon request, Receiving Party shall return or destroy all Confidential Information.

6. NO LICENSE
No license or rights are granted except as expressly stated.

7. REMEDIES
Breach may cause irreparable harm. Disclosing Party may seek injunctive relief
in addition to other remedies.

8. GOVERNING LAW
Governed by Delaware law. Disputes resolved in Delaware courts.
""",
    )

    llm = OllamaProvider(model="llama3.2")
    result = await analyze_legal_document(document, llm)
    return result


async def main():
    """Run example document analyses"""

    print("Legal Document Analysis System - Example Cases")
    print("=" * 60)
    print("DISCLAIMER: For educational purposes only.")
    print("Not for actual legal advice. Always consult legal professionals.")
    print("=" * 60)

    # Example 1: Employment Agreement
    print("\n\nExample 1: Employment Agreement Analysis")
    await example_employment_agreement()

    # Example 2: NDA
    print("\n\nExample 2: Non - Disclosure Agreement Analysis")
    await example_nda()


if __name__ == "__main__":
    asyncio.run(main())
