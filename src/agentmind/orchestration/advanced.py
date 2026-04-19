"""Advanced orchestration patterns for multi-agent systems.

Provides consensus mechanisms, dynamic agent spawning, and parallel task decomposition.
"""

from .consensus import ConsensusOrchestrator, VotingMechanism
from .dynamic import DynamicAgentSpawner
from .parallel import ParallelTaskDecomposer
from .specialization import SkillMatcher, SpecializationEngine

__all__ = [
    "ConsensusOrchestrator",
    "DynamicAgentSpawner",
    "ParallelTaskDecomposer",
    "SkillMatcher",
    "SpecializationEngine",
    "VotingMechanism",
]
