"""Example: Multi - modal agent with document processing.

This example demonstrates how to use AgentMind with document processing
capabilities for PDF, DOCX, and text file analysis.
"""

import asyncio
from pathlib import Path

from agentmind.multimodal import DocumentProcessor
from agentmind import Agent, AgentMind
from agentmind.llm import LiteLLMProvider


async def example_pdf_extraction():
    """Extract text from PDF."""
    print("=== PDF Text Extraction Example ===\n")

    processor = DocumentProcessor()

    pdf_path = "path / to / document.pd"
    if Path(pdf_path).exists():
        # Extract all text
        text = processor.extract_text_from_pdf(pdf_path)
        print(f"Extracted text (first 500 chars):\n{text[:500]}...\n")

        # Extract specific pages
        text_pages = processor.extract_text_from_pdf(pdf_path, pages=[0, 1, 2])
        print(f"First 3 pages (first 300 chars):\n{text_pages[:300]}...\n")
    else:
        print(f"PDF not found: {pdf_path}\n")


async def example_docx_extraction():
    """Extract text from DOCX."""
    print("=== DOCX Text Extraction Example ===\n")

    processor = DocumentProcessor()

    docx_path = "path / to / document.docx"
    if Path(docx_path).exists():
        text = processor.extract_text_from_docx(docx_path)
        print(f"Extracted text (first 500 chars):\n{text[:500]}...\n")
    else:
        print(f"DOCX not found: {docx_path}\n")


async def example_document_metadata():
    """Get document metadata."""
    print("=== Document Metadata Example ===\n")

    processor = DocumentProcessor()

    # PDF metadata
    pdf_path = "path / to / document.pd"
    if Path(pdf_path).exists():
        metadata = processor.get_pdf_metadata(pdf_path)
        print("PDF Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
    else:
        print(f"PDF not found: {pdf_path}\n")

    # DOCX metadata
    docx_path = "path / to / document.docx"
    if Path(docx_path).exists():
        metadata = processor.get_docx_metadata(docx_path)
        print("DOCX Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
    else:
        print(f"DOCX not found: {docx_path}\n")


async def example_document_chunking():
    """Chunk documents for processing."""
    print("=== Document Chunking Example ===\n")

    processor = DocumentProcessor()

    text = "This is a sample document. " * 100  # Create long text

    chunks = processor.chunk_text(text, chunk_size=200, overlap=50)
    print(f"Created {len(chunks)} chunks")
    print(f"First chunk: {chunks[0][:100]}...")
    print(f"Last chunk: {chunks[-1][:100]}...\n")


async def example_document_analysis_agent():
    """Agent that analyzes documents."""
    print("=== Document Analysis Agent Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    analyzer = Agent(
        name="DocumentAnalyzer",
        role="analysis",
        system_prompt="You analyze documents and extract key information.",
    )
    mind.add_agent(analyzer)

    doc_path = "path / to / report.pd"
    if Path(doc_path).exists():
        # Extract text
        text = doc_processor.extract_text(doc_path)

        # Analyze with agent
        result = await mind.collaborate(
            f"Analyze this document and provide a summary with key points:\n\n{text[:2000]}",
            max_rounds=1,
        )
        print(f"Analysis:\n{result.final_output}\n")
    else:
        print(f"Document not found: {doc_path}\n")


async def example_multi_document_comparison():
    """Compare multiple documents."""
    print("=== Multi - Document Comparison Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    comparer = Agent(
        name="DocumentComparer",
        role="comparison",
        system_prompt="You compare documents and identify similarities and differences.",
    )
    mind.add_agent(comparer)

    docs = ["path / to / doc1.pd", "path / to / doc2.pd"]
    if all(Path(doc).exists() for doc in docs):
        # Extract text from both
        texts = [doc_processor.extract_text(doc) for doc in docs]

        # Compare
        comparison_prompt = (
            "Compare these two documents:\n\n"
            f"Document 1:\n{texts[0][:1000]}\n\n"
            f"Document 2:\n{texts[1][:1000]}"
        )

        result = await mind.collaborate(comparison_prompt, max_rounds=1)
        print(f"Comparison:\n{result.final_output}\n")
    else:
        print("One or more documents not found\n")


async def example_research_paper_analyzer():
    """Analyze research papers with multiple agents."""
    print("=== Research Paper Analyzer Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    # Create specialized agents
    summarizer = Agent(
        name="Summarizer",
        role="summarization",
        system_prompt="You create concise summaries of research papers.",
    )

    methodology_expert = Agent(
        name="MethodologyExpert",
        role="methodology",
        system_prompt="You analyze research methodologies and experimental design.",
    )

    results_analyst = Agent(
        name="ResultsAnalyst",
        role="results",
        system_prompt="You analyze research results and their implications.",
    )

    mind.add_agent(summarizer)
    mind.add_agent(methodology_expert)
    mind.add_agent(results_analyst)

    paper_path = "path / to / research_paper.pd"
    if Path(paper_path).exists():
        # Extract text
        text = doc_processor.extract_text(paper_path)

        # Analyze with multiple agents
        result = await mind.collaborate(
            f"Analyze this research paper comprehensively:\n\n{text[:3000]}", max_rounds=3
        )

        print(f"Comprehensive Analysis:\n{result.final_output}\n")
    else:
        print(f"Paper not found: {paper_path}\n")


async def example_contract_reviewer():
    """Review legal contracts."""
    print("=== Contract Reviewer Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    reviewer = Agent(
        name="ContractReviewer",
        role="legal_review",
        system_prompt=(
            "You review contracts and identify key terms, obligations, "
            "and potential issues. You are thorough and detail - oriented."
        ),
    )
    mind.add_agent(reviewer)

    contract_path = "path / to / contract.pd"
    if Path(contract_path).exists():
        # Extract text
        text = doc_processor.extract_text(contract_path)

        # Review
        result = await mind.collaborate(
            "Review this contract and identify:\n"
            "1. Key terms and conditions\n"
            "2. Obligations for each party\n"
            "3. Potential risks or concerns\n\n"
            f"Contract:\n{text}",
            max_rounds=1,
        )

        print(f"Contract Review:\n{result.final_output}\n")
    else:
        print(f"Contract not found: {contract_path}\n")


async def example_document_qa():
    """Question - answering over documents."""
    print("=== Document Q&A Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    qa_agent = Agent(
        name="QAAgent",
        role="qa",
        system_prompt="You answer questions based on document content accurately.",
    )
    mind.add_agent(qa_agent)

    doc_path = "path / to / manual.pd"
    if Path(doc_path).exists():
        # Extract text
        text = doc_processor.extract_text(doc_path)

        # Ask questions
        questions = [
            "What is the main purpose of this document?",
            "What are the key requirements mentioned?",
            "Are there any warnings or cautions?",
        ]

        for question in questions:
            result = await mind.collaborate(
                f"Based on this document, answer: {question}\n\nDocument:\n{text[:2000]}",
                max_rounds=1,
            )
            print(f"Q: {question}")
            print(f"A: {result.final_output}\n")
    else:
        print(f"Document not found: {doc_path}\n")


async def example_batch_document_processing():
    """Process multiple documents in batch."""
    print("=== Batch Document Processing Example ===\n")

    doc_processor = DocumentProcessor()
    llm = LiteLLMProvider(model="gpt - 4")
    mind = AgentMind(llm_provider=llm)

    processor = Agent(
        name="BatchProcessor",
        role="processing",
        system_prompt="You extract key information from documents efficiently.",
    )
    mind.add_agent(processor)

    doc_dir = Path("path / to / documents")
    if doc_dir.exists():
        # Process all PDFs in directory
        pdf_files = list(doc_dir.glob("*.pd"))

        for pdf_file in pdf_files[:5]:  # Process first 5
            text = doc_processor.extract_text(pdf_file)
            result = await mind.collaborate(
                f"Extract key information from: {pdf_file.name}\n\n{text[:1000]}", max_rounds=1
            )
            print(f"File: {pdf_file.name}")
            print(f"Summary: {result.final_output}\n")
    else:
        print(f"Directory not found: {doc_dir}\n")


async def main():
    """Run all examples."""
    print("Document Processing Examples\n")
    print("=" * 50 + "\n")

    print("Note: Update document paths and ensure required packages are installed.\n")
    print("Required packages: PyPDF2, python - docx\n")

    # Run examples that don't require files
    await example_document_chunking()

    # Uncomment to run examples with document files
    # await example_pdf_extraction()
    # await example_docx_extraction()
    # await example_document_metadata()
    # await example_document_analysis_agent()
    # await example_multi_document_comparison()
    # await example_research_paper_analyzer()
    # await example_contract_reviewer()
    # await example_document_qa()
    # await example_batch_document_processing()


if __name__ == "__main__":
    asyncio.run(main())
