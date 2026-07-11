"""Python teaching toolkit for agentic knowledge graphs with KuzuDB."""

from .agent import AgentResponse, GraphAgent
from .domains import DOMAINS, DomainSpec, get_domain

__all__ = ["AgentResponse", "DOMAINS", "DomainSpec", "GraphAgent", "get_domain"]
__version__ = "0.1.0"
