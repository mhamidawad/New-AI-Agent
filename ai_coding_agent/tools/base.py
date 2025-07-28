"""Base tool interface for extensible agent functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Tool(ABC):
    """Abstract base class for agent tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        pass
    
    def __str__(self) -> str:
        return f"Tool({self.name}): {self.description}"