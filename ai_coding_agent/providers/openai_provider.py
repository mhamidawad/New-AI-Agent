"""OpenAI provider implementation."""

import asyncio
from typing import Any, Dict, List, Optional
import openai
from .base import BaseProvider, ProviderResponse


class OpenAIProvider(BaseProvider):
    """OpenAI provider for GPT models."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 30):
        super().__init__(api_key, model, timeout)
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> ProviderResponse:
        """Generate a response using OpenAI's API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            choice = response.choices[0]
            usage = response.usage.model_dump() if response.usage else None
            
            return ProviderResponse(
                content=choice.message.content or "",
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason,
                metadata={"response_id": response.id}
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> ProviderResponse:
        """Generate code using OpenAI."""
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
        """Analyze code using OpenAI."""
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
        """Explain code using OpenAI."""
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
        """Suggest code improvements using OpenAI."""
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
        """Fix code errors using OpenAI."""
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