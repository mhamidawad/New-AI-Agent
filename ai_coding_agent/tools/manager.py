"""Tool manager for coordinating tool usage."""

import logging
from typing import Any, Dict, List, Optional

from .base import Tool, ToolResult
from .builtin_tools import FileSystemTool, GitTool, LinterTool, FormatterTool
from ..providers.base import BaseProvider


logger = logging.getLogger(__name__)


class ToolManager:
    """Manages and coordinates tool usage."""
    
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        builtin_tools = [
            FileSystemTool(),
            GitTool(),
            LinterTool(),
            FormatterTool()
        ]
        
        for tool in builtin_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools."""
        return {name: tool.description for name, tool in self.tools.items()}
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool with given parameters."""
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Tool '{tool_name}' not found"
                )
            
            result = await tool.execute(**kwargs)
            
            logger.info(f"Tool '{tool_name}' executed: {'success' if result.success else 'failure'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    async def suggest_tools(self, query: str) -> List[str]:
        """Suggest relevant tools for a query."""
        # Use AI to suggest relevant tools
        tool_descriptions = self.get_tool_descriptions()
        
        prompt = f"""Given the following query and available tools, suggest which tools would be most relevant:

Query: {query}

Available tools:
{chr(10).join(f"- {name}: {desc}" for name, desc in tool_descriptions.items())}

Suggest the most relevant tools (return tool names only, one per line):"""
        
        try:
            response = await self.provider.generate_response([
                {"role": "user", "content": prompt}
            ])
            
            # Extract tool names from response
            suggested_tools = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line and line in self.tools:
                    suggested_tools.append(line)
            
            return suggested_tools[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting tools: {str(e)}")
            return []