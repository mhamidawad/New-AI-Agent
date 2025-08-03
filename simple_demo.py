#!/usr/bin/env python3
"""
Simple demo of the AI Coding Agent structure and capabilities.
This demo works with standard library modules only.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional


class SimpleCodeAnalyzer:
    """Simple code analyzer using basic Python parsing."""
    
    def analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python code using basic string parsing."""
        lines = code.split('\n')
        
        analysis = {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Find function definitions
            if stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '')
                analysis["functions"].append({
                    "name": func_name,
                    "line": i + 1
                })
            
            # Find class definitions
            elif stripped.startswith('class '):
                class_name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                analysis["classes"].append({
                    "name": class_name,
                    "line": i + 1
                })
            
            # Find imports
            elif stripped.startswith('import ') or stripped.startswith('from '):
                analysis["imports"].append({
                    "statement": stripped,
                    "line": i + 1
                })
        
        # Calculate code lines
        analysis["code_lines"] = analysis["non_empty_lines"] - analysis["comment_lines"]
        
        return analysis


class SimpleCodeGenerator:
    """Simple code generator with templates."""
    
    def generate_function(self, name: str, description: str, language: str = "python") -> str:
        """Generate a function template."""
        if language == "python":
            return f'''def {name}():
    """
    {description}
    """
    # TODO: Implement {name}
    pass
'''
        elif language == "javascript":
            return f'''function {name}() {{
    /**
     * {description}
     */
    // TODO: Implement {name}
}}
'''
        else:
            return f"# {description}\n# TODO: Implement {name} in {language}"
    
    def generate_class(self, name: str, description: str, language: str = "python") -> str:
        """Generate a class template."""
        if language == "python":
            return f'''class {name}:
    """
    {description}
    """
    
    def __init__(self):
        """Initialize {name}."""
        pass
    
    def example_method(self):
        """Example method for {name}."""
        pass
'''
        elif language == "javascript":
            return f'''class {name} {{
    /**
     * {description}
     */
    constructor() {{
        // Initialize {name}
    }}
    
    exampleMethod() {{
        // Example method for {name}
    }}
}}
'''
        else:
            return f"# {description}\n# TODO: Implement {name} class in {language}"


class MockAIProvider:
    """Mock AI provider for demonstration purposes."""
    
    def __init__(self):
        self.responses = {
            "code_review": "This code looks good overall. Consider adding error handling and documentation.",
            "optimization": "The algorithm has O(n) time complexity. For better performance, consider using a hash table.",
            "explanation": "This function implements a binary search algorithm to find elements in a sorted array.",
            "best_practices": "Follow PEP 8 style guidelines, use type hints, and add comprehensive docstrings."
        }
    
    async def analyze_code(self, code: str, analysis_type: str = "general") -> str:
        """Mock code analysis."""
        await asyncio.sleep(0.1)  # Simulate API call
        
        response_key = "code_review"
        for key in self.responses:
            if key in analysis_type.lower():
                response_key = key
                break
        
        return self.responses[response_key]
    
    async def generate_code(self, prompt: str, language: str = "python") -> str:
        """Mock code generation."""
        await asyncio.sleep(0.1)  # Simulate API call
        
        if "factorial" in prompt.lower():
            return '''def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
        elif "fibonacci" in prompt.lower():
            return '''def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
        else:
            return f'''# Generated {language} code for: {prompt}
def example_function():
    """Example function based on prompt."""
    pass
'''


class SimpleCodingAgent:
    """Simple AI Coding Agent demonstration."""
    
    def __init__(self):
        self.analyzer = SimpleCodeAnalyzer()
        self.generator = SimpleCodeGenerator()
        self.provider = MockAIProvider()
        self.context = {"messages": [], "files": {}}
    
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a code file."""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            content = path.read_text(encoding='utf-8')
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Analyze code
            if language == "python":
                analysis = self.analyzer.analyze_python_code(content)
            else:
                analysis = {"message": f"Analysis not available for {language}"}
            
            # Store in context
            self.context["files"][file_path] = {
                "content": content,
                "language": language,
                "analysis": analysis
            }
            
            return {
                "file_path": file_path,
                "language": language,
                "analysis": analysis
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code based on description."""
        # Try AI provider first
        try:
            code = await self.provider.generate_code(description, language)
            return code
        except:
            # Fallback to simple template
            if "function" in description.lower():
                name = description.split()[-1] if description.split() else "example"
                return self.generator.generate_function(name, description, language)
            elif "class" in description.lower():
                name = description.split()[-1] if description.split() else "Example"
                return self.generator.generate_class(name, description, language)
            else:
                return f"# {description}\n# TODO: Implement in {language}"
    
    async def review_code(self, code: str, language: str = "python") -> str:
        """Review code and provide feedback."""
        try:
            review = await self.provider.analyze_code(code, "review")
            return review
        except:
            return "Code review not available - please check with a real AI provider."
    
    async def chat(self, message: str) -> str:
        """Simple chat functionality."""
        self.context["messages"].append({"role": "user", "content": message})
        
        # Simple response logic
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            response = "Hello! I'm a simple AI coding agent. I can help you analyze code, generate functions, and review your code."
        elif "help" in message_lower:
            response = """I can help you with:
- Analyzing code files
- Generating code from descriptions
- Reviewing code for issues
- Answering coding questions

Try asking me to generate a function or analyze some code!"""
        elif "generate" in message_lower and "function" in message_lower:
            response = "I can generate functions! Please provide a description of what the function should do."
        elif "analyze" in message_lower:
            response = "I can analyze Python files! Provide a file path and I'll analyze its structure."
        else:
            response = f"You said: '{message}'. I'm a simple demo agent, so my responses are limited. Try asking for help!"
        
        self.context["messages"].append({"role": "assistant", "content": response})
        return response
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
        }
        
        return language_map.get(suffix, 'text')
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_type": "Simple Demo Agent",
            "messages": len(self.context["messages"]),
            "files_analyzed": len(self.context["files"]),
            "capabilities": [
                "Code Analysis",
                "Code Generation", 
                "Code Review",
                "Basic Chat"
            ]
        }


async def run_demo():
    """Run the simple AI Coding Agent demo."""
    print("🤖 Simple AI Coding Agent Demo")
    print("=" * 50)
    
    # Initialize agent
    agent = SimpleCodingAgent()
    
    # Demo 1: Chat
    print("💬 Demo 1: Chat Interaction")
    print("-" * 30)
    
    responses = []
    for message in ["Hello!", "What can you help me with?", "Can you generate a function?"]:
        print(f"User: {message}")
        response = await agent.chat(message)
        print(f"Agent: {response}")
        print()
    
    # Demo 2: Code Generation
    print("📝 Demo 2: Code Generation")
    print("-" * 30)
    
    print("Generating a factorial function...")
    code = await agent.generate_code("Create a factorial function", "python")
    print("Generated Code:")
    print(code)
    
    # Demo 3: Code Analysis
    print("🔍 Demo 3: Code Analysis")
    print("-" * 30)
    
    # Create a sample Python file
    sample_code = '''# Sample Python code for analysis
import math

def calculate_area(radius):
    """Calculate area of a circle."""
    return math.pi * radius ** 2

class Circle:
    """A circle class."""
    
    def __init__(self, radius):
        self.radius = radius
    
    def area(self):
        return calculate_area(self.radius)

# Usage example
circle = Circle(5)
print(f"Area: {circle.area()}")
'''
    
    with open("sample_code.py", "w") as f:
        f.write(sample_code)
    
    print("Analyzing sample_code.py...")
    analysis = await agent.analyze_file("sample_code.py")
    
    if "error" not in analysis:
        print("Analysis Results:")
        print(f"Language: {analysis['language']}")
        print(f"Total lines: {analysis['analysis']['total_lines']}")
        print(f"Functions found: {len(analysis['analysis']['functions'])}")
        print(f"Classes found: {len(analysis['analysis']['classes'])}")
        print(f"Imports: {len(analysis['analysis']['imports'])}")
        
        for func in analysis['analysis']['functions']:
            print(f"  - Function '{func['name']}' at line {func['line']}")
        
        for cls in analysis['analysis']['classes']:
            print(f"  - Class '{cls['name']}' at line {cls['line']}")
    else:
        print(f"Error: {analysis['error']}")
    
    # Demo 4: Code Review
    print("\n🔎 Demo 4: Code Review")
    print("-" * 30)
    
    review_code = '''def divide(a, b):
    return a / b  # Potential division by zero!
'''
    
    print("Reviewing this code:")
    print(review_code)
    
    review = await agent.review_code(review_code)
    print("Review:")
    print(review)
    
    # Show final status
    print("\n📊 Final Status")
    print("-" * 20)
    status = agent.get_status()
    print(json.dumps(status, indent=2))
    
    # Cleanup
    try:
        Path("sample_code.py").unlink()
    except:
        pass
    
    print("\n✨ Demo completed successfully!")
    print("\n📋 Summary:")
    print("This simple demo shows the basic structure of the AI Coding Agent.")
    print("The full version includes:")
    print("- Real AI integration (OpenAI/Anthropic)")
    print("- Advanced code analysis with AST parsing")
    print("- Comprehensive tool system")
    print("- Project-wide analysis")
    print("- Rich CLI interface")
    print("- Context management and persistence")


if __name__ == "__main__":
    asyncio.run(run_demo())