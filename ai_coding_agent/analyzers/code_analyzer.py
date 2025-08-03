"""Code analysis functionality."""

import ast
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..providers.base import BaseProvider


logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code structure, quality, and provides insights."""
    
    def __init__(self, provider: BaseProvider):
        self.provider = provider
    
    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and return comprehensive insights."""
        try:
            analysis = {
                "language": language,
                "basic_stats": self._get_basic_stats(code),
                "structure": await self._analyze_structure(code, language),
                "quality": await self._analyze_quality(code, language),
                "suggestions": await self._get_suggestions(code, language),
                "complexity": self._calculate_complexity(code, language)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {"error": str(e)}
    
    def _get_basic_stats(self, code: str) -> Dict[str, Any]:
        """Get basic statistics about the code."""
        lines = code.split('\n')
        
        stats = {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
            "code_lines": 0,
            "character_count": len(code),
            "average_line_length": 0
        }
        
        # Calculate code lines (non-empty, non-comment)
        stats["code_lines"] = stats["non_empty_lines"] - stats["comment_lines"]
        
        # Calculate average line length
        if stats["total_lines"] > 0:
            stats["average_line_length"] = stats["character_count"] / stats["total_lines"]
        
        return stats
    
    async def _analyze_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code structure."""
        if language == "python":
            return self._analyze_python_structure(code)
        else:
            # Use AI provider for other languages
            result = await self.provider.analyze_code(
                code, language, analysis_type="general"
            )
            return {"ai_analysis": result.content}
    
    def _analyze_python_structure(self, code: str) -> Dict[str, Any]:
        """Analyze Python code structure using AST."""
        try:
            tree = ast.parse(code)
            
            structure = {
                "functions": [],
                "classes": [],
                "imports": [],
                "globals": [],
                "docstrings": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(dec) for dec in node.decorator_list],
                        "docstring": ast.get_docstring(node)
                    }
                    structure["functions"].append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases],
                        "decorators": [ast.unparse(dec) for dec in node.decorator_list],
                        "docstring": ast.get_docstring(node),
                        "methods": []
                    }
                    
                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append(item.name)
                    
                    structure["classes"].append(class_info)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append({
                            "type": "import",
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        structure["imports"].append({
                            "type": "from_import",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
            
            return structure
            
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}
        except Exception as e:
            return {"error": f"Analysis error: {str(e)}"}
    
    async def _analyze_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality."""
        result = await self.provider.analyze_code(
            code, language, analysis_type="style"
        )
        
        return {
            "ai_quality_analysis": result.content,
            "score": self._extract_quality_score(result.content)
        }
    
    async def _get_suggestions(self, code: str, language: str) -> List[str]:
        """Get improvement suggestions."""
        result = await self.provider.suggest_improvements(code, language)
        
        # Extract suggestions from AI response
        suggestions = self._extract_suggestions(result.content)
        
        return suggestions
    
    def _calculate_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        if language == "python":
            return self._calculate_python_complexity(code)
        else:
            # Basic metrics for other languages
            lines = code.split('\n')
            return {
                "cyclomatic_complexity": "Not available",
                "cognitive_complexity": "Not available",
                "lines_of_code": len([line for line in lines if line.strip()]),
                "nesting_depth": self._estimate_nesting_depth(code)
            }
    
    def _calculate_python_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate Python-specific complexity metrics."""
        try:
            tree = ast.parse(code)
            
            complexity = {
                "cyclomatic_complexity": 1,  # Start with 1
                "cognitive_complexity": 0,
                "nesting_depth": 0,
                "function_count": 0,
                "class_count": 0
            }
            
            for node in ast.walk(tree):
                # Cyclomatic complexity
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                   ast.With, ast.AsyncWith, ast.Try)):
                    complexity["cyclomatic_complexity"] += 1
                
                elif isinstance(node, ast.BoolOp):
                    complexity["cyclomatic_complexity"] += len(node.values) - 1
                
                # Function and class counts
                elif isinstance(node, ast.FunctionDef):
                    complexity["function_count"] += 1
                
                elif isinstance(node, ast.ClassDef):
                    complexity["class_count"] += 1
            
            # Estimate nesting depth
            complexity["nesting_depth"] = self._calculate_nesting_depth(tree)
            
            return complexity
            
        except Exception as e:
            return {"error": f"Complexity calculation error: {str(e)}"}
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in AST."""
        max_depth = 0
        
        def calculate_depth(node: ast.AST, current_depth: int = 0) -> int:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With,
                                    ast.Try, ast.FunctionDef, ast.ClassDef)):
                    calculate_depth(child, current_depth + 1)
                else:
                    calculate_depth(child, current_depth)
            
            return max_depth
        
        return calculate_depth(tree)
    
    def _estimate_nesting_depth(self, code: str) -> int:
        """Estimate nesting depth by counting indentation."""
        lines = code.split('\n')
        max_indent = 0
        
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        return max_indent // 4  # Assuming 4-space indentation
    
    def _extract_quality_score(self, analysis_text: str) -> Optional[int]:
        """Extract quality score from AI analysis."""
        import re
        
        # Look for score patterns like "Score: 8/10" or "Quality: 7"
        patterns = [
            r'score[:\s]+(\d+)(?:/10)?',
            r'quality[:\s]+(\d+)(?:/10)?',
            r'rating[:\s]+(\d+)(?:/10)?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_suggestions(self, suggestions_text: str) -> List[str]:
        """Extract suggestions from AI response."""
        lines = suggestions_text.split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            # Look for numbered lists or bullet points
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*', '•')) or
                line.startswith(('Suggestion', 'Recommendation', 'Consider'))):
                suggestions.append(line)
        
        return suggestions[:10]  # Limit to top 10 suggestions