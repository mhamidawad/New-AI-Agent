"""Type definitions and interfaces for the AI Coding Agent.

This module provides comprehensive type safety and validation using Pydantic models,
following the principle of strong typing and input validation.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, validator


class LanguageType(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript" 
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    GO = "go"
    RUST = "rust"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    BASH = "bash"
    POWERSHELL = "powershell"
    TEXT = "text"


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AnalysisType(str, Enum):
    """Types of code analysis."""
    GENERAL = "general"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPLEXITY = "complexity"


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolAction(str, Enum):
    """Tool action types."""
    READ = "read"
    WRITE = "write"
    LIST = "list"
    CREATE_DIR = "create_dir"
    DELETE = "delete"
    ANALYZE = "analyze"
    FORMAT = "format"
    LINT = "lint"


class GitAction(str, Enum):
    """Git action types."""
    STATUS = "status"
    ADD = "add"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    BRANCH = "branch"
    LOG = "log"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CHAT = "chat"
    PROJECT_ANALYSIS = "project_analysis"
    TOOL_EXECUTION = "tool_execution"


# Request/Response Models

class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    code: str = Field(..., min_length=1, description="Code to analyze")
    language: LanguageType = Field(default=LanguageType.PYTHON, description="Programming language")
    analysis_type: AnalysisType = Field(default=AnalysisType.GENERAL, description="Type of analysis")
    file_path: Optional[str] = Field(None, description="Optional file path for context")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate code input."""
        if not v.strip():
            raise ValueError("Code cannot be empty or whitespace only")
        return v


class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""
    description: str = Field(..., min_length=1, description="Description of code to generate")
    language: LanguageType = Field(default=LanguageType.PYTHON, description="Target programming language")
    context: Optional[str] = Field(None, description="Additional context for generation")
    max_tokens: Optional[int] = Field(4000, ge=1, le=8000, description="Maximum tokens for response")
    temperature: Optional[float] = Field(0.1, ge=0.0, le=2.0, description="Generation temperature")
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description input."""
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str = Field(..., min_length=1, description="User message")
    context: Optional[str] = Field(None, description="Additional context")
    include_history: bool = Field(True, description="Include conversation history")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message input."""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


# Response Models

class BasicStats(BaseModel):
    """Basic code statistics."""
    total_lines: int = Field(ge=0, description="Total number of lines")
    non_empty_lines: int = Field(ge=0, description="Non-empty lines")
    comment_lines: int = Field(ge=0, description="Comment lines")
    code_lines: int = Field(ge=0, description="Actual code lines")
    character_count: int = Field(ge=0, description="Total character count")
    average_line_length: float = Field(ge=0.0, description="Average line length")


class FunctionInfo(BaseModel):
    """Information about a function."""
    name: str = Field(..., description="Function name")
    line: int = Field(ge=1, description="Line number")
    args: List[str] = Field(default_factory=list, description="Function arguments")
    decorators: List[str] = Field(default_factory=list, description="Function decorators")
    docstring: Optional[str] = Field(None, description="Function docstring")
    complexity: Optional[int] = Field(None, ge=1, description="Cyclomatic complexity")


class ClassInfo(BaseModel):
    """Information about a class."""
    name: str = Field(..., description="Class name")
    line: int = Field(ge=1, description="Line number")
    bases: List[str] = Field(default_factory=list, description="Base classes")
    decorators: List[str] = Field(default_factory=list, description="Class decorators")
    docstring: Optional[str] = Field(None, description="Class docstring")
    methods: List[str] = Field(default_factory=list, description="Method names")


class ImportInfo(BaseModel):
    """Information about an import statement."""
    type: Literal["import", "from_import"] = Field(..., description="Import type")
    module: Optional[str] = Field(None, description="Module name")
    name: str = Field(..., description="Imported name")
    alias: Optional[str] = Field(None, description="Import alias")
    line: int = Field(ge=1, description="Line number")


class CodeStructure(BaseModel):
    """Code structure analysis."""
    functions: List[FunctionInfo] = Field(default_factory=list, description="Function definitions")
    classes: List[ClassInfo] = Field(default_factory=list, description="Class definitions")
    imports: List[ImportInfo] = Field(default_factory=list, description="Import statements")
    globals: List[str] = Field(default_factory=list, description="Global variables")
    docstrings: List[str] = Field(default_factory=list, description="Module docstrings")


class ComplexityMetrics(BaseModel):
    """Code complexity metrics."""
    cyclomatic_complexity: Union[int, str] = Field(..., description="Cyclomatic complexity")
    cognitive_complexity: Union[int, str] = Field(default=0, description="Cognitive complexity")
    nesting_depth: int = Field(ge=0, description="Maximum nesting depth")
    function_count: int = Field(ge=0, description="Number of functions")
    class_count: int = Field(ge=0, description="Number of classes")
    lines_of_code: int = Field(ge=0, description="Lines of code")


class QualityAnalysis(BaseModel):
    """Code quality analysis results."""
    ai_quality_analysis: str = Field(..., description="AI-generated quality analysis")
    score: Optional[int] = Field(None, ge=1, le=10, description="Quality score (1-10)")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""
    language: LanguageType = Field(..., description="Detected/specified language")
    basic_stats: BasicStats = Field(..., description="Basic code statistics")
    structure: Union[CodeStructure, Dict[str, Any]] = Field(..., description="Code structure analysis")
    quality: QualityAnalysis = Field(..., description="Quality analysis")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    complexity: ComplexityMetrics = Field(..., description="Complexity metrics")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class ProviderUsage(BaseModel):
    """AI provider usage statistics."""
    prompt_tokens: int = Field(ge=0, description="Tokens used in prompt")
    completion_tokens: int = Field(ge=0, description="Tokens used in completion")
    total_tokens: int = Field(ge=0, description="Total tokens used")
    
    @validator('total_tokens')
    def validate_total_tokens(cls, v, values):
        """Validate total tokens calculation."""
        prompt = values.get('prompt_tokens', 0)
        completion = values.get('completion_tokens', 0)
        expected_total = prompt + completion
        if v != expected_total:
            return expected_total
        return v


class ProviderResponse(BaseModel):
    """Response from an AI provider."""
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[ProviderUsage] = Field(None, description="Token usage statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    @property
    def tokens_used(self) -> int:
        """Get total tokens used."""
        if self.usage:
            return self.usage.total_tokens
        return 0


# Context and State Models

class MessageMetadata(BaseModel):
    """Metadata for chat messages."""
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens used in message")
    model: Optional[str] = Field(None, description="Model used for message")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time in seconds")
    source: Optional[str] = Field(None, description="Source of the message")


class ChatMessage(BaseModel):
    """Chat message with metadata."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: MessageMetadata = Field(default_factory=MessageMetadata, description="Message metadata")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate message content."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class FileContextInfo(BaseModel):
    """Context information about a file."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    language: LanguageType = Field(..., description="Programming language")
    last_modified: datetime = Field(..., description="Last modification time")
    size: int = Field(ge=0, description="File size in bytes")
    analysis: Optional[CodeAnalysisResponse] = Field(None, description="Code analysis results")
    checksum: Optional[str] = Field(None, description="File content checksum")


class GitInfo(BaseModel):
    """Git repository information."""
    branch: str = Field(..., description="Current branch")
    commit: str = Field(..., description="Latest commit hash")
    is_dirty: bool = Field(..., description="Whether working directory is dirty")
    remote_url: Optional[str] = Field(None, description="Remote repository URL")


class ProjectInfo(BaseModel):
    """Project context information."""
    root_path: Path = Field(..., description="Project root directory")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    languages: List[LanguageType] = Field(default_factory=list, description="Used languages")
    file_count: int = Field(ge=0, description="Total file count")
    total_size: int = Field(ge=0, description="Total project size in bytes")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Project structure")
    dependencies: List[str] = Field(default_factory=list, description="Project dependencies")
    git_info: Optional[GitInfo] = Field(None, description="Git repository information")
    last_analyzed: Optional[datetime] = Field(None, description="Last analysis timestamp")


# Tool System Models

class ToolParameter(BaseModel):
    """Tool parameter definition."""
    type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value")
    enum: Optional[List[str]] = Field(None, description="Allowed values")


class ToolSchema(BaseModel):
    """Tool schema definition."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, ToolParameter] = Field(..., description="Tool parameters")
    capabilities: List[AgentCapability] = Field(..., description="Required capabilities")


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool = Field(..., description="Whether execution was successful")
    output: Any = Field(None, description="Tool output")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time: Optional[float] = Field(None, ge=0.0, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Execution timestamp")


# Configuration Models

class ModelConfig(BaseModel):
    """AI model configuration."""
    name: str = Field(default="gpt-4", description="Model name")
    provider: ModelProvider = Field(default=ModelProvider.OPENAI, description="Model provider")
    max_tokens: int = Field(default=4000, ge=1, le=32000, description="Maximum tokens")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Generation temperature")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    
    @validator('name')
    def validate_model_name(cls, v, values):
        """Validate model name matches provider."""
        provider = values.get('provider')
        if provider == ModelProvider.OPENAI and not any(x in v.lower() for x in ['gpt', 'openai']):
            raise ValueError(f"Model '{v}' doesn't match OpenAI provider")
        elif provider == ModelProvider.ANTHROPIC and not any(x in v.lower() for x in ['claude', 'anthropic']):
            raise ValueError(f"Model '{v}' doesn't match Anthropic provider")
        return v


class ProjectConfig(BaseModel):
    """Project-specific configuration."""
    root: Path = Field(default=Path("."), description="Project root directory")
    ignore_patterns: List[str] = Field(
        default=["__pycache__", "*.pyc", ".git", "node_modules", "*.log"],
        description="Patterns to ignore"
    )
    include_patterns: List[str] = Field(
        default=["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"],
        description="File patterns to include"
    )
    max_file_size: int = Field(default=1024*1024, ge=1, description="Maximum file size in bytes")
    
    @validator('root')
    def validate_root_path(cls, v):
        """Validate root path exists."""
        if not v.exists():
            raise ValueError(f"Root path does not exist: {v}")
        return v


class AgentConfig(BaseModel):
    """Agent behavior configuration."""
    debug: bool = Field(default=False, description="Enable debug mode")
    verbose: bool = Field(default=False, description="Enable verbose output")
    auto_save: bool = Field(default=True, description="Auto-save context")
    context_window: int = Field(default=10, ge=1, le=100, description="Context window size")
    enable_tools: bool = Field(default=True, description="Enable tool usage")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    cache_enabled: bool = Field(default=True, description="Enable response caching")


class SecurityConfig(BaseModel):
    """Security configuration."""
    api_key_validation: bool = Field(default=True, description="Validate API keys")
    input_sanitization: bool = Field(default=True, description="Sanitize user inputs")
    max_input_size: int = Field(default=10000, ge=1, description="Maximum input size")
    allowed_file_types: List[str] = Field(
        default=[".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".md", ".txt"],
        description="Allowed file types for analysis"
    )
    
    @validator('allowed_file_types')
    def validate_file_types(cls, v):
        """Validate file type format."""
        for file_type in v:
            if not file_type.startswith('.'):
                raise ValueError(f"File type must start with dot: {file_type}")
        return v


class AgentStatus(BaseModel):
    """Current agent status."""
    model: str = Field(..., description="Current model")
    provider: str = Field(..., description="Current provider")
    capabilities: List[AgentCapability] = Field(..., description="Available capabilities")
    context: Dict[str, Any] = Field(..., description="Context summary")
    config: Dict[str, Any] = Field(..., description="Configuration summary")
    uptime: Optional[float] = Field(None, ge=0.0, description="Uptime in seconds")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    health_status: Literal["healthy", "degraded", "error"] = Field(default="healthy", description="Health status")


# Error Models

class AgentError(BaseModel):
    """Agent error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Error context")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ValidationResult(BaseModel):
    """Input validation result."""
    valid: bool = Field(..., description="Whether input is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    sanitized_input: Optional[Any] = Field(None, description="Sanitized input if valid")