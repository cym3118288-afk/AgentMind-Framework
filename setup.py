from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentmind",
    version="0.2.0",
    author="Terry Carson",
    author_email="cym3118288@gmail.com",
    description="Multi-Agent Collaboration Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cym3118288-afk/AgentMind-Framework",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0,<3.0.0",
        "httpx>=0.24.0",
    ],
    entry_points={
        "agentmind.plugins.llm": [],
        "agentmind.plugins.memory": [],
        "agentmind.plugins.tools": [],
        "agentmind.plugins.orchestrator": [],
        "agentmind.plugins.observer": [],
    },
)
