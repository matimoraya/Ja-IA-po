"""SOC investigation orchestration.

The public entry point is :func:`run_investigation`.  The optional factory
arguments exist for the application integrator and for deterministic tests;
the model never receives a scenario identifier as a tool argument.
"""

from .core import (
    AgentLimits,
    InvestigationModel,
    ModelDecision,
    ToolCall,
    run_investigation,
)

__all__ = [
    "AgentLimits",
    "InvestigationModel",
    "ModelDecision",
    "ToolCall",
    "run_investigation",
]
