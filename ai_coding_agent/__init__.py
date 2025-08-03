"""
AI Coding Agent - An intelligent AI-powered coding assistant.

This package provides a comprehensive AI coding agent that can analyze,
understand, and generate code across multiple programming languages.
"""

from .core.agent import CodingAgent
from .core.config import Config
from .analyzers.code_analyzer import CodeAnalyzer
from .generators.code_generator import CodeGenerator
from .tools.base import Tool, ToolResult
from .providers.base import BaseProvider

__version__ = "1.0.0"
__author__ = "AI Coding Agent"
__email__ = "agent@example.com"

__all__ = [
    "CodingAgent",
    "Config",
    "CodeAnalyzer", 
    "CodeGenerator",
    "Tool",
    "ToolResult",
    "BaseProvider",
]