"""Base provider interface for AI models."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class ProviderResponse:
    """Response from an AI provider."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    
    @property
    def tokens_used(self) -> int:
        """Get total tokens used."""
        if self.usage:
            return self.usage.get("total_tokens", 0)
        return 0


class BaseProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(self, api_key: str, model: str = "", timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> ProviderResponse:
        """Generate a response from the AI model."""
        pass
    
    @abstractmethod
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> ProviderResponse:
        """Generate code based on a prompt."""
        pass
    
    @abstractmethod
    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "general",
        **kwargs
    ) -> ProviderResponse:
        """Analyze code and provide insights."""
        pass
    
    @abstractmethod
    async def explain_code(
        self,
        code: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Explain what the code does."""
        pass
    
    @abstractmethod
    async def suggest_improvements(
        self,
        code: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Suggest improvements for the code."""
        pass
    
    @abstractmethod
    async def fix_errors(
        self,
        code: str,
        error_message: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Fix errors in the code."""
        pass
    
    def _prepare_messages(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for the AI model."""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def test_connection(self) -> bool:
        """Test if the provider connection is working."""
        try:
            response = await self.generate_response(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.content)
        except Exception:
            return False