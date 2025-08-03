"""Main AI Coding Agent implementation."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..providers.base import BaseProvider, ProviderResponse
from ..providers.openai_provider import OpenAIProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..analyzers.code_analyzer import CodeAnalyzer
from ..generators.code_generator import CodeGenerator
from ..tools.manager import ToolManager
from .config import Config
from .context import ContextManager, ProjectContext


logger = logging.getLogger(__name__)


class CodingAgent:
    """Main AI Coding Agent that coordinates all functionality."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the coding agent."""
        self.config = config or Config.from_env()
        
        # Initialize provider
        self.provider = self._initialize_provider()
        
        # Initialize core components
        self.context_manager = ContextManager(
            context_window=self.config.agent.context_window,
            auto_save=self.config.agent.auto_save
        )
        
        self.code_analyzer = CodeAnalyzer(self.provider)
        self.code_generator = CodeGenerator(self.provider)
        self.tool_manager = ToolManager(self.provider) if self.config.agent.enable_tools else None
        
        # Set up logging
        self._setup_logging()
        
        logger.info(f"CodingAgent initialized with {self.provider.__class__.__name__}")
    
    def _initialize_provider(self) -> BaseProvider:
        """Initialize the AI provider based on configuration."""
        model_name = self.config.model.name.lower()
        
        if "gpt" in model_name or "openai" in model_name:
            if not self.config.openai_api_key:
                raise ValueError("OpenAI API key is required for GPT models")
            return OpenAIProvider(
                api_key=self.config.openai_api_key,
                model=self.config.model.name,
                timeout=self.config.model.timeout
            )
        elif "claude" in model_name or "anthropic" in model_name:
            if not self.config.anthropic_api_key:
                raise ValueError("Anthropic API key is required for Claude models")
            return AnthropicProvider(
                api_key=self.config.anthropic_api_key,
                model=self.config.model.name,
                timeout=self.config.model.timeout
            )
        else:
            raise ValueError(f"Unsupported model: {self.config.model.name}")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        level = logging.DEBUG if self.config.agent.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file."""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Analyze the code
            result = await self.code_analyzer.analyze_code(content, language)
            
            # Add to context
            self.context_manager.add_file_context(
                file_path, content, language, result
            )
            
            return {
                "file_path": file_path,
                "language": language,
                "analysis": result,
                "summary": result.get("summary", "Analysis completed")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            raise
    
    async def analyze_project(self, project_path: str = ".") -> Dict[str, Any]:
        """Analyze an entire project."""
        try:
            project_path_obj = Path(project_path)
            
            # Get project info
            project_info = await self._scan_project(project_path_obj)
            
            # Create project context
            project_context = ProjectContext(
                root_path=project_path_obj,
                name=project_path_obj.name,
                **project_info
            )
            
            self.context_manager.set_project_context(project_context)
            
            return {
                "project_path": str(project_path_obj),
                "analysis": project_info,
                "summary": f"Analyzed project with {project_info['file_count']} files"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project {project_path}: {str(e)}")
            raise
    
    async def generate_code(self, description: str, language: str = "python", 
                          context: Optional[str] = None) -> str:
        """Generate code based on description."""
        try:
            # Get relevant context
            if not context:
                context = self._get_relevant_context(description)
            
            # Generate code
            result = await self.code_generator.generate_code(
                description, language, context
            )
            
            # Add to conversation history
            self.context_manager.add_message(
                "user", f"Generate {language} code: {description}"
            )
            self.context_manager.add_message("assistant", result.content)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise
    
    async def chat(self, message: str, context: Optional[str] = None) -> str:
        """Chat with the agent."""
        try:
            # Add user message to history
            self.context_manager.add_message("user", message)
            
            # Get conversation history
            history = self.context_manager.get_conversation_history()
            
            # Build context
            full_context = self._build_chat_context(context)
            
            # Prepare messages for the provider
            messages = []
            
            if full_context:
                messages.append({
                    "role": "system",
                    "content": f"You are an expert AI coding assistant. Here's the current context:\n{full_context}"
                })
            
            # Add conversation history
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Get response
            response = await self.provider.generate_response(
                messages=messages,
                max_tokens=self.config.model.max_tokens,
                temperature=self.config.model.temperature
            )
            
            # Add assistant response to history
            self.context_manager.add_message("assistant", response.content)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise
    
    async def review_code(self, code: str, language: str) -> str:
        """Review code and provide feedback."""
        try:
            result = await self.provider.analyze_code(
                code, language, analysis_type="general"
            )
            
            self.context_manager.add_message(
                "user", f"Review this {language} code"
            )
            self.context_manager.add_message("assistant", result.content)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error reviewing code: {str(e)}")
            raise
    
    async def fix_code(self, code: str, error_message: str, language: str) -> str:
        """Fix code errors."""
        try:
            result = await self.provider.fix_errors(code, error_message, language)
            
            self.context_manager.add_message(
                "user", f"Fix {language} code error: {error_message}"
            )
            self.context_manager.add_message("assistant", result.content)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error fixing code: {str(e)}")
            raise
    
    async def explain_code(self, code: str, language: str) -> str:
        """Explain what code does."""
        try:
            result = await self.provider.explain_code(code, language)
            
            self.context_manager.add_message(
                "user", f"Explain this {language} code"
            )
            self.context_manager.add_message("assistant", result.content)
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error explaining code: {str(e)}")
            raise
    
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
            '.h': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sh': 'bash',
            '.ps1': 'powershell'
        }
        
        return language_map.get(suffix, 'text')
    
    async def _scan_project(self, project_path: Path) -> Dict[str, Any]:
        """Scan project directory and gather information."""
        file_count = 0
        total_size = 0
        languages = set()
        structure = {}
        dependencies = []
        
        # Scan files
        for pattern in self.config.project.include_patterns:
            for file_path in project_path.rglob(pattern):
                if self._should_ignore_file(file_path):
                    continue
                
                file_count += 1
                total_size += file_path.stat().st_size
                language = self._detect_language(str(file_path))
                languages.add(language)
        
        # Look for dependency files
        dep_files = ['requirements.txt', 'package.json', 'Cargo.toml', 'go.mod', 'pom.xml']
        for dep_file in dep_files:
            dep_path = project_path / dep_file
            if dep_path.exists():
                dependencies.append(dep_file)
        
        # Get git info if available
        git_info = await self._get_git_info(project_path)
        
        return {
            "file_count": file_count,
            "total_size": total_size,
            "languages": list(languages),
            "structure": structure,
            "dependencies": dependencies,
            "git_info": git_info
        }
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored based on patterns."""
        import fnmatch
        
        path_str = str(file_path)
        for pattern in self.config.project.ignore_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        
        return file_path.stat().st_size > self.config.project.max_file_size
    
    async def _get_git_info(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get git repository information."""
        try:
            import git
            repo = git.Repo(project_path)
            
            return {
                "branch": repo.active_branch.name,
                "commit": repo.head.commit.hexsha[:8],
                "is_dirty": repo.is_dirty(),
                "remote_url": repo.remotes.origin.url if repo.remotes else None
            }
        except Exception:
            return None
    
    def _get_relevant_context(self, query: str) -> str:
        """Get relevant context for a query."""
        relevant_files = self.context_manager.get_relevant_files(query, limit=3)
        
        context_parts = []
        
        # Add project context
        if self.context_manager.project:
            project = self.context_manager.project
            context_parts.append(f"Project: {project.name}")
            context_parts.append(f"Languages: {', '.join(project.languages)}")
        
        # Add relevant files
        for file_context in relevant_files:
            context_parts.append(f"\nFile: {file_context.path}")
            context_parts.append(f"Language: {file_context.language}")
            # Include first 500 characters of content
            content_preview = file_context.content[:500]
            if len(file_context.content) > 500:
                content_preview += "..."
            context_parts.append(f"Content: {content_preview}")
        
        return "\n".join(context_parts)
    
    def _build_chat_context(self, additional_context: Optional[str] = None) -> str:
        """Build context for chat interactions."""
        context_parts = []
        
        # Add project context
        if self.context_manager.project:
            project = self.context_manager.project
            context_parts.append(f"Working on project: {project.name}")
            if project.languages:
                context_parts.append(f"Primary languages: {', '.join(project.languages[:3])}")
        
        # Add recent files
        if self.context_manager.files:
            recent_files = list(self.context_manager.files.keys())[-3:]
            context_parts.append(f"Recent files: {', '.join(recent_files)}")
        
        # Add additional context
        if additional_context:
            context_parts.append(f"Additional context: {additional_context}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        return {
            "model": self.config.model.name,
            "provider": self.provider.__class__.__name__,
            "context": self.context_manager.get_context_summary(),
            "config": {
                "debug": self.config.agent.debug,
                "verbose": self.config.agent.verbose,
                "tools_enabled": self.config.agent.enable_tools
            }
        }