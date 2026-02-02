"""
EdgeMind Agent - Main Package
"""

from .core import EdgeMindAgent, AgentResponse
from .core import ContextBuilder, SystemContext
from .core import DecisionEngine, Decision, RiskLevel, ExecutionMode
from .gateway import SecurityGateway, ExecutionResult
from .api import GeminiClient, GeminiResponse

__version__ = "1.0.0"
__author__ = "EdgeMind Team"

__all__ = [
    "EdgeMindAgent",
    "AgentResponse",
    "ContextBuilder",
    "SystemContext",
    "DecisionEngine",
    "Decision",
    "RiskLevel",
    "ExecutionMode",
    "SecurityGateway",
    "ExecutionResult",
    "GeminiClient",
    "GeminiResponse",
]
