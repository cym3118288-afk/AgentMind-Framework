"""
Hugging Face Transformers Integration

This example demonstrates how to integrate AgentMind with Hugging Face Transformers
for using local models, custom pipelines, and specialized NLP tasks.

Combines:
- Hugging Face Transformers: Local models, pipelines, and NLP tasks
- AgentMind: Multi - agent orchestration and collaboration
"""

import asyncio

from agentmind import Agent, AgentMind
from agentmind.llm import OllamaProvider
from agentmind.tools import Tool


class HuggingFacePipelineTool(Tool):
    """Wraps a Hugging Face pipeline as an AgentMind tool"""

    def __init__(self, pipeline, task_name: str, description: str):
        self.pipeline = pipeline
        self.task_name = task_name
        super().__init__(
            name=f"hf_{task_name}",
            description=description,
            parameters={"text": {"type": "string", "description": "Input text to process"}},
        )

    async def execute(self, text: str) -> str:
        """Execute the Hugging Face pipeline"""
        try:
            result = await asyncio.to_thread(self.pipeline, text)
            return str(result)
        except Exception as e:
            return f"Error executing {self.task_name}: {str(e)}"


# Example 1: Sentiment analysis tool
async def example_sentiment_analysis():
    """Use Hugging Face sentiment analysis in AgentMind"""
    print("\n=== Example 1: Sentiment Analysis ===\n")

    try:
        from transformers import pipeline

        # Create sentiment analysis pipeline
        sentiment_pipeline = pipeline(
            "sentiment - analysis",
            model="distilbert - base - uncased - finetuned - sst - 2 - english",
        )

        # Wrap as AgentMind tool
        sentiment_tool = HuggingFacePipelineTool(
            pipeline=sentiment_pipeline,
            task_name="sentiment_analysis",
            description="Analyze the sentiment of text (positive / negative)",
        )

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create analyst agent
        analyst = Agent(
            name="Sentiment_Analyst",
            role="sentiment_analyst",
            system_prompt="You analyze customer feedback and provide insights based on sentiment analysis.",
            tools=[sentiment_tool],
        )

        mind.add_agent(analyst)

        # Analyze feedback
        feedback = [
            "I love this product! It's amazing!",
            "Terrible experience, very disappointed.",
            "It's okay, nothing special.",
        ]

        for text in feedback:
            print(f"\nFeedback: {text}")
            result = await mind.collaborate(
                f"Analyze this feedback and provide insights: {text}", max_rounds=2
            )
            print(f"Analysis: {result}\n")

    except ImportError:
        print("Transformers not installed. Install with: pip install transformers torch")


# Example 2: Named Entity Recognition (NER)
async def example_ner():
    """Extract entities using Hugging Face NER"""
    print("\n=== Example 2: Named Entity Recognition ===\n")

    try:
        from transformers import pipeline

        # Create NER pipeline
        ner_pipeline = pipeline(
            "ner", model="dslim / bert - base - NER", aggregation_strategy="simple"
        )

        # Wrap as tool
        ner_tool = HuggingFacePipelineTool(
            pipeline=ner_pipeline,
            task_name="entity_extraction",
            description="Extract named entities (people, organizations, locations) from text",
        )

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create extraction agent
        extractor = Agent(
            name="Entity_Extractor",
            role="information_extractor",
            system_prompt="You extract and organize information from text using entity recognition.",
            tools=[ner_tool],
        )

        mind.add_agent(extractor)

        # Extract entities
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California. Microsoft is headquartered in Redmond, Washington."  # noqa: E501

        print(f"Text: {text}\n")
        result = await mind.collaborate(
            f"Extract all entities from this text and organize them: {text}", max_rounds=2
        )
        print(f"Extracted Information: {result}")

    except ImportError:
        print("Transformers not installed. Install with: pip install transformers torch")


# Example 3: Text summarization
async def example_summarization():
    """Summarize documents using Hugging Face models"""
    print("\n=== Example 3: Text Summarization ===\n")

    try:
        from transformers import pipeline

        # Create summarization pipeline
        summarizer = pipeline("summarization", model="facebook / bart - large - cnn")

        # Wrap as tool
        class SummarizationTool(Tool):
            def __init__(self, pipeline):
                self.pipeline = pipeline
                super().__init__(
                    name="summarize",
                    description="Summarize long text into concise summaries",
                    parameters={
                        "text": {"type": "string", "description": "Text to summarize"},
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum summary length",
                            "default": 130,
                        },
                        "min_length": {
                            "type": "integer",
                            "description": "Minimum summary length",
                            "default": 30,
                        },
                    },
                )

            async def execute(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
                try:
                    result = await asyncio.to_thread(
                        self.pipeline,
                        text,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False,
                    )
                    return result[0]["summary_text"]
                except Exception as e:
                    return f"Error summarizing: {str(e)}"

        summarization_tool = SummarizationTool(summarizer)

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Create summarizer agent
        summarizer_agent = Agent(
            name="Summarizer",
            role="content_summarizer",
            system_prompt="You create concise, informative summaries of long documents.",
            tools=[summarization_tool],
        )

        mind.add_agent(summarizer_agent)

        # Long article
        article = """
        Artificial intelligence has made remarkable progress in recent years, with breakthroughs in
        natural language processing, computer vision, and reinforcement learning. Large language models
        like GPT - 4 and Claude have demonstrated impressive capabilities in understanding and generating
        human - like text. These models are trained on vast amounts of data and can perform a wide range
        of tasks, from answering questions to writing code. However, challenges remain in areas such as
        reasoning, factual accuracy, and ethical considerations. Researchers continue to work on making
        AI systems more reliable, interpretable, and aligned with human values.
        """

        print(f"Original article length: {len(article)} characters\n")
        result = await mind.collaborate(f"Summarize this article: {article}", max_rounds=2)
        print(f"Summary: {result}")

    except ImportError:
        print("Transformers not installed. Install with: pip install transformers torch")


# Example 4: Multi - task NLP pipeline
async def example_multi_task():
    """Combine multiple Hugging Face tasks in a multi - agent system"""
    print("\n=== Example 4: Multi - task NLP Pipeline ===\n")

    try:
        from transformers import pipeline

        # Create multiple pipelines
        sentiment_pipeline = pipeline("sentiment - analysis")
        ner_pipeline = pipeline("ner", aggregation_strategy="simple")

        # Create tools
        sentiment_tool = HuggingFacePipelineTool(
            sentiment_pipeline, "sentiment", "Analyze sentiment"
        )

        ner_tool = HuggingFacePipelineTool(ner_pipeline, "ner", "Extract named entities")

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # Sentiment analyst
        sentiment_agent = Agent(
            name="Sentiment_Analyst",
            role="sentiment_specialist",
            system_prompt="You analyze emotional tone and sentiment in text.",
            tools=[sentiment_tool],
        )

        # Entity extractor
        entity_agent = Agent(
            name="Entity_Extractor",
            role="entity_specialist",
            system_prompt="You extract and categorize named entities from text.",
            tools=[ner_tool],
        )

        # Synthesizer
        synthesizer = Agent(
            name="Synthesizer",
            role="information_synthesizer",
            system_prompt="You combine insights from sentiment and entity analysis into comprehensive reports.",
        )

        mind.add_agent(sentiment_agent)
        mind.add_agent(entity_agent)
        mind.add_agent(synthesizer)

        # Analyze text
        text = "Elon Musk announced that Tesla will open a new factory in Berlin. Investors are excited about the expansion."  # noqa: E501

        print(f"Text: {text}\n")
        result = await mind.collaborate(
            f"Perform complete analysis of this text including sentiment and entities: {text}",
            max_rounds=3,
        )
        print(f"Complete Analysis: {result}")

    except ImportError:
        print("Transformers not installed. Install with: pip install transformers torch")


# Example 5: Question answering with context
async def example_question_answering():
    """Use Hugging Face QA models with AgentMind"""
    print("\n=== Example 5: Question Answering ===\n")

    try:
        from transformers import pipeline

        # Create QA pipeline
        qa_pipeline = pipeline(
            "question - answering", model="distilbert - base - cased - distilled - squad"
        )

        # Create QA tool
        class QATool(Tool):
            def __init__(self, pipeline):
                self.pipeline = pipeline
                super().__init__(
                    name="answer_question",
                    description="Answer questions based on provided context",
                    parameters={
                        "question": {"type": "string", "description": "Question to answer"},
                        "context": {
                            "type": "string",
                            "description": "Context containing the answer",
                        },
                    },
                )

            async def execute(self, question: str, context: str) -> str:
                try:
                    result = await asyncio.to_thread(
                        self.pipeline, question=question, context=context
                    )
                    return f"Answer: {result['answer']} (confidence: {result['score']:.2f})"
                except Exception as e:
                    return f"Error: {str(e)}"

        qa_tool = QATool(qa_pipeline)

        # Create AgentMind system
        llm = OllamaProvider(model="llama3.2")
        mind = AgentMind(llm_provider=llm)

        # QA agent
        qa_agent = Agent(
            name="QA_Agent",
            role="qa_specialist",
            system_prompt="You answer questions accurately based on provided context.",
            tools=[qa_tool],
        )

        mind.add_agent(qa_agent)

        # Context and questions
        context = """
        AgentMind is a lightweight multi - agent framework for Python. It was created in 2024 and
        supports multiple LLM providers including Ollama, OpenAI, and Anthropic. The framework
        features async - first architecture, built - in memory management, and an extensible tool system.
        """

        questions = [
            "When was AgentMind created?",
            "What LLM providers does it support?",
            "What are the key features?",
        ]

        for question in questions:
            print(f"\nQ: {question}")
            result = await mind.collaborate(
                f"Answer this question using the context: Question: {question}, Context: {context}",
                max_rounds=2,
            )
            print(f"A: {result}")

    except ImportError:
        print("Transformers not installed. Install with: pip install transformers torch")


async def main():
    """Run all Hugging Face integration examples"""
    print("=" * 60)
    print("AgentMind + Hugging Face Transformers Integration")
    print("=" * 60)

    await example_sentiment_analysis()
    await example_ner()
    await example_summarization()
    await example_multi_task()
    await example_question_answering()

    print("\n" + "=" * 60)
    print("Hugging Face integration examples completed!")
    print("=" * 60)
    print("\nNote: These examples require Transformers to be installed:")
    print("  pip install transformers torch")


if __name__ == "__main__":
    asyncio.run(main())
