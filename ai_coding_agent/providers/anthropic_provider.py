"""Anthropic provider implementation."""

import asyncio
from typing import Any, Dict, List, Optional
import anthropic
from .base import BaseProvider, ProviderResponse


class AnthropicProvider(BaseProvider):
    """Anthropic provider for Claude models."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", timeout: int = 30):
        super().__init__(api_key, model, timeout)
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> ProviderResponse:
        """Generate a response using Anthropic's API."""
        try:
            # Convert messages format for Anthropic
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    if system_message is None:
                        system_message = msg["content"]
                    else:
                        system_message += "\n\n" + msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4000,
                temperature=temperature,
                system=system_message,
                messages=user_messages,
                **kwargs
            )
            
            content = ""
            if response.content:
                content = "".join([
                    block.text if hasattr(block, 'text') else str(block)
                    for block in response.content
                ])
            
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            } if response.usage else None
            
            return ProviderResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.stop_reason,
                metadata={"response_id": response.id}
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> ProviderResponse:
        """Generate code using Anthropic."""
        system_message = f"""You are an expert {language} programmer. Generate clean, efficient, and well-documented code based on the user's request.

Guidelines:
- Write production-ready code
- Include appropriate comments
- Follow best practices for {language}
- Handle edge cases
- Use meaningful variable names
- Include type hints where applicable"""
        
        messages = self._prepare_messages(prompt, system_message, context)
        return await self.generate_response(messages, **kwargs)
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "general",
        **kwargs
    ) -> ProviderResponse:
        """Analyze code using Anthropic."""
        analysis_prompts = {
            "general": "Analyze this code and provide insights about its structure, functionality, and quality.",
            "performance": "Analyze this code for performance issues and optimization opportunities.",
            "security": "Analyze this code for security vulnerabilities and potential issues.",
            "style": "Analyze this code for style and best practice adherence.",
            "complexity": "Analyze the complexity of this code and suggest simplifications."
        }
        
        system_message = f"""You are an expert code reviewer and {language} developer. 
        Provide a thorough analysis of the provided code focusing on {analysis_type} aspects.
        
        Structure your response with:
        1. Overall Assessment
        2. Specific Issues (if any)
        3. Recommendations
        4. Code Quality Score (1-10)"""
        
        prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['general'])}\n\n```{language}\n{code}\n```"
        
        messages = self._prepare_messages(prompt, system_message)
        return await self.generate_response(messages, **kwargs)
    
    async def explain_code(
        self,
        code: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Explain code using Anthropic."""
        system_message = f"""You are an expert {language} developer and teacher. 
        Explain the provided code in a clear, educational manner.
        
        Structure your explanation:
        1. High-level overview
        2. Step-by-step breakdown
        3. Key concepts used
        4. Purpose and use cases"""
        
        prompt = f"Please explain this {language} code:\n\n```{language}\n{code}\n```"
        
        messages = self._prepare_messages(prompt, system_message)
        return await self.generate_response(messages, **kwargs)
    
    async def suggest_improvements(
        self,
        code: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Suggest code improvements using Anthropic."""
        system_message = f"""You are an expert {language} developer and code reviewer.
        Analyze the provided code and suggest specific improvements.
        
        Focus on:
        - Performance optimizations
        - Code readability
        - Best practices
        - Error handling
        - Security considerations
        
        For each suggestion, provide:
        1. The issue/opportunity
        2. Why it matters
        3. Specific code changes"""
        
        prompt = f"Please suggest improvements for this {language} code:\n\n```{language}\n{code}\n```"
        
        messages = self._prepare_messages(prompt, system_message)
        return await self.generate_response(messages, **kwargs)
    
    async def fix_errors(
        self,
        code: str,
        error_message: str,
        language: str,
        **kwargs
    ) -> ProviderResponse:
        """Fix code errors using Anthropic."""
        system_message = f"""You are an expert {language} developer and debugger.
        Fix the error in the provided code and explain the solution.
        
        Provide:
        1. Root cause analysis
        2. Fixed code
        3. Explanation of the fix
        4. Prevention tips"""
        
        prompt = f"""Fix this {language} code that's producing an error:

Error message: {error_message}

Code:
```{language}
{code}
```"""
        
        messages = self._prepare_messages(prompt, system_message)
        return await self.generate_response(messages, **kwargs)