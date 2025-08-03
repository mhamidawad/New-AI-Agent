"""Code generation functionality."""

import logging
from typing import Any, Dict, List, Optional
from jinja2 import Template

from ..providers.base import BaseProvider, ProviderResponse


logger = logging.getLogger(__name__)


class CodeGenerator:
    """Generates code using AI providers with templates and context."""
    
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        self.templates = self._load_templates()
    
    async def generate_code(self, description: str, language: str = "python", 
                          context: Optional[str] = None, **kwargs) -> ProviderResponse:
        """Generate code based on description."""
        try:
            # Use template if available
            template_key = f"{language}_generation"
            if template_key in self.templates:
                prompt = self._render_template(template_key, {
                    "description": description,
                    "context": context,
                    "language": language,
                    **kwargs
                })
            else:
                prompt = self._build_generation_prompt(description, language, context)
            
            result = await self.provider.generate_code(
                prompt, language, context, **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise
    
    async def generate_function(self, name: str, description: str, parameters: List[Dict[str, str]], 
                              return_type: str = "Any", language: str = "python") -> str:
        """Generate a specific function."""
        try:
            prompt = self._build_function_prompt(name, description, parameters, return_type, language)
            
            result = await self.provider.generate_code(prompt, language)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating function: {str(e)}")
            raise
    
    async def generate_class(self, name: str, description: str, methods: List[Dict[str, Any]], 
                           base_classes: List[str] = None, language: str = "python") -> str:
        """Generate a class with specified methods."""
        try:
            prompt = self._build_class_prompt(name, description, methods, base_classes, language)
            
            result = await self.provider.generate_code(prompt, language)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating class: {str(e)}")
            raise
    
    async def generate_test(self, code: str, language: str = "python", 
                          test_framework: str = "pytest") -> str:
        """Generate tests for existing code."""
        try:
            prompt = self._build_test_prompt(code, language, test_framework)
            
            result = await self.provider.generate_code(prompt, language)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating tests: {str(e)}")
            raise
    
    async def generate_documentation(self, code: str, language: str = "python", 
                                   doc_format: str = "sphinx") -> str:
        """Generate documentation for code."""
        try:
            prompt = self._build_documentation_prompt(code, language, doc_format)
            
            result = await self.provider.generate_response([
                {"role": "user", "content": prompt}
            ])
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            raise
    
    async def refactor_code(self, code: str, refactor_type: str, language: str = "python") -> str:
        """Refactor existing code."""
        try:
            prompt = self._build_refactor_prompt(code, refactor_type, language)
            
            result = await self.provider.generate_code(prompt, language)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error refactoring code: {str(e)}")
            raise
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load code generation templates."""
        templates = {}
        
        # Python generation template
        templates["python_generation"] = Template("""
Generate Python code for the following request:

Description: {{ description }}

{% if context %}
Context: {{ context }}
{% endif %}

Requirements:
- Write clean, readable Python code
- Include appropriate type hints
- Add docstrings for functions and classes
- Follow PEP 8 style guidelines
- Handle edge cases and errors appropriately
- Include example usage if relevant

Generate the code:
        """.strip())
        
        # JavaScript generation template
        templates["javascript_generation"] = Template("""
Generate JavaScript code for the following request:

Description: {{ description }}

{% if context %}
Context: {{ context }}
{% endif %}

Requirements:
- Write modern JavaScript (ES6+)
- Use appropriate JSDoc comments
- Follow JavaScript best practices
- Handle errors appropriately
- Include example usage if relevant

Generate the code:
        """.strip())
        
        return templates
    
    def _render_template(self, template_key: str, context: Dict[str, Any]) -> str:
        """Render a template with given context."""
        template = self.templates[template_key]
        return template.render(**context)
    
    def _build_generation_prompt(self, description: str, language: str, context: Optional[str]) -> str:
        """Build a general code generation prompt."""
        prompt_parts = [
            f"Generate {language} code for the following request:",
            f"Description: {description}"
        ]
        
        if context:
            prompt_parts.append(f"Context: {context}")
        
        prompt_parts.extend([
            "",
            "Requirements:",
            f"- Write clean, readable {language} code",
            "- Follow best practices and conventions",
            "- Include appropriate comments",
            "- Handle edge cases",
            "- Include example usage if applicable"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_function_prompt(self, name: str, description: str, parameters: List[Dict[str, str]], 
                             return_type: str, language: str) -> str:
        """Build a function generation prompt."""
        param_strs = []
        for param in parameters:
            param_str = f"{param['name']}: {param.get('type', 'Any')}"
            if 'description' in param:
                param_str += f" - {param['description']}"
            param_strs.append(param_str)
        
        prompt = f"""Generate a {language} function with the following specification:

Function Name: {name}
Description: {description}
Parameters:
{chr(10).join(f"  - {param}" for param in param_strs)}
Return Type: {return_type}

Requirements:
- Include appropriate type hints (if {language} supports them)
- Add comprehensive docstring
- Implement error handling
- Include input validation where appropriate
- Write clean, readable code
"""
        
        return prompt
    
    def _build_class_prompt(self, name: str, description: str, methods: List[Dict[str, Any]], 
                          base_classes: List[str], language: str) -> str:
        """Build a class generation prompt."""
        prompt_parts = [
            f"Generate a {language} class with the following specification:",
            f"Class Name: {name}",
            f"Description: {description}"
        ]
        
        if base_classes:
            prompt_parts.append(f"Base Classes: {', '.join(base_classes)}")
        
        if methods:
            prompt_parts.append("Methods:")
            for method in methods:
                method_str = f"  - {method['name']}: {method.get('description', 'No description')}"
                if 'parameters' in method:
                    method_str += f" (params: {', '.join(method['parameters'])})"
                prompt_parts.append(method_str)
        
        prompt_parts.extend([
            "",
            "Requirements:",
            "- Include constructor (__init__) method",
            "- Add appropriate docstrings",
            "- Implement all specified methods",
            "- Follow class design best practices",
            "- Include type hints where applicable"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_test_prompt(self, code: str, language: str, test_framework: str) -> str:
        """Build a test generation prompt."""
        return f"""Generate comprehensive tests for the following {language} code using {test_framework}:

Code to test:
```{language}
{code}
```

Requirements:
- Generate thorough test cases covering normal operation
- Include edge cases and error conditions
- Test boundary conditions
- Use appropriate {test_framework} features
- Include setup and teardown if needed
- Add descriptive test names and docstrings
- Achieve high code coverage

Generate the test code:
"""
    
    def _build_documentation_prompt(self, code: str, language: str, doc_format: str) -> str:
        """Build a documentation generation prompt."""
        return f"""Generate comprehensive documentation for the following {language} code in {doc_format} format:

Code:
```{language}
{code}
```

Include:
- Overview and purpose
- Detailed API documentation
- Parameter descriptions
- Return value documentation
- Usage examples
- Error handling information
- Notes about implementation details

Format the documentation appropriately for {doc_format}:
"""
    
    def _build_refactor_prompt(self, code: str, refactor_type: str, language: str) -> str:
        """Build a code refactoring prompt."""
        refactor_instructions = {
            "extract_method": "Extract repetitive code into separate methods",
            "simplify": "Simplify complex logic and reduce complexity",
            "optimize": "Optimize for better performance and efficiency",
            "modernize": "Update to use modern language features and patterns",
            "clean": "Clean up code style and improve readability"
        }
        
        instruction = refactor_instructions.get(refactor_type, f"Refactor using {refactor_type} approach")
        
        return f"""Refactor the following {language} code to {instruction}:

Original code:
```{language}
{code}
```

Refactoring goals:
- {instruction}
- Maintain original functionality
- Improve code quality and maintainability
- Follow {language} best practices
- Add comments explaining changes

Provide the refactored code:
"""