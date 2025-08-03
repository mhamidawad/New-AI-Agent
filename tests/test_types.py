"""Tests for type definitions and validation.

This module tests all Pydantic models and ensures proper validation,
following Test-Driven Development principles.
"""

import pytest
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from ai_coding_agent.core.types import (
    # Enums
    LanguageType, ModelProvider, AnalysisType, MessageRole, ToolAction,
    GitAction, AgentCapability,
    
    # Request Models
    CodeAnalysisRequest, CodeGenerationRequest, ChatRequest,
    
    # Response Models
    BasicStats, FunctionInfo, ClassInfo, ImportInfo, CodeStructure,
    ComplexityMetrics, QualityAnalysis, CodeAnalysisResponse,
    ProviderUsage, ProviderResponse,
    
    # Context Models
    MessageMetadata, ChatMessage, FileContextInfo, GitInfo, ProjectInfo,
    
    # Tool Models
    ToolParameter, ToolSchema, ToolResult,
    
    # Configuration Models
    ModelConfig, ProjectConfig, AgentConfig, SecurityConfig,
    
    # Status and Error Models
    AgentStatus, AgentError, ValidationResult
)


class TestEnums:
    """Test enum definitions."""
    
    def test_language_type_values(self):
        """Test LanguageType enum has expected values."""
        assert LanguageType.PYTHON == "python"
        assert LanguageType.JAVASCRIPT == "javascript"
        assert LanguageType.TYPESCRIPT == "typescript"
        assert len(LanguageType) >= 20  # Should have many supported languages
    
    def test_model_provider_values(self):
        """Test ModelProvider enum values."""
        assert ModelProvider.OPENAI == "openai"
        assert ModelProvider.ANTHROPIC == "anthropic"
    
    def test_analysis_type_values(self):
        """Test AnalysisType enum values."""
        assert AnalysisType.GENERAL == "general"
        assert AnalysisType.SECURITY == "security"
        assert AnalysisType.PERFORMANCE == "performance"


class TestRequestModels:
    """Test request model validation."""
    
    def test_code_analysis_request_valid(self):
        """Test valid CodeAnalysisRequest creation."""
        request = CodeAnalysisRequest(
            code="def hello(): pass",
            language=LanguageType.PYTHON,
            analysis_type=AnalysisType.GENERAL
        )
        
        assert request.code == "def hello(): pass"
        assert request.language == LanguageType.PYTHON
        assert request.analysis_type == AnalysisType.GENERAL
    
    def test_code_analysis_request_empty_code(self):
        """Test CodeAnalysisRequest validation fails with empty code."""
        with pytest.raises(ValidationError) as exc_info:
            CodeAnalysisRequest(code="")
        
        assert "Code cannot be empty" in str(exc_info.value)
    
    def test_code_analysis_request_whitespace_only(self):
        """Test CodeAnalysisRequest validation fails with whitespace-only code."""
        with pytest.raises(ValidationError) as exc_info:
            CodeAnalysisRequest(code="   \n  \t  ")
        
        assert "Code cannot be empty" in str(exc_info.value)
    
    def test_code_generation_request_valid(self):
        """Test valid CodeGenerationRequest creation."""
        request = CodeGenerationRequest(
            description="Create a hello world function",
            language=LanguageType.PYTHON,
            max_tokens=2000,
            temperature=0.2
        )
        
        assert request.description == "Create a hello world function"
        assert request.language == LanguageType.PYTHON
        assert request.max_tokens == 2000
        assert request.temperature == 0.2
    
    def test_code_generation_request_validates_description(self):
        """Test CodeGenerationRequest validates description."""
        with pytest.raises(ValidationError) as exc_info:
            CodeGenerationRequest(description="")
        
        assert "Description cannot be empty" in str(exc_info.value)
    
    def test_code_generation_request_validates_tokens(self):
        """Test CodeGenerationRequest validates token limits."""
        with pytest.raises(ValidationError):
            CodeGenerationRequest(
                description="Test",
                max_tokens=0  # Invalid: too low
            )
        
        with pytest.raises(ValidationError):
            CodeGenerationRequest(
                description="Test", 
                max_tokens=9000  # Invalid: too high
            )
    
    def test_code_generation_request_validates_temperature(self):
        """Test CodeGenerationRequest validates temperature range."""
        with pytest.raises(ValidationError):
            CodeGenerationRequest(
                description="Test",
                temperature=-0.1  # Invalid: too low
            )
        
        with pytest.raises(ValidationError):
            CodeGenerationRequest(
                description="Test",
                temperature=2.1  # Invalid: too high
            )
    
    def test_chat_request_valid(self):
        """Test valid ChatRequest creation."""
        request = ChatRequest(
            message="Hello, how can you help?",
            context="Working on a Python project",
            include_history=True
        )
        
        assert request.message == "Hello, how can you help?"
        assert request.context == "Working on a Python project"
        assert request.include_history is True
    
    def test_chat_request_strips_message(self):
        """Test ChatRequest strips whitespace from message."""
        request = ChatRequest(message="  Hello world  ")
        assert request.message == "Hello world"
    
    def test_chat_request_validates_empty_message(self):
        """Test ChatRequest validates empty message."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="")
        
        assert "Message cannot be empty" in str(exc_info.value)


class TestResponseModels:
    """Test response model creation and validation."""
    
    def test_basic_stats_valid(self):
        """Test BasicStats model creation."""
        stats = BasicStats(
            total_lines=100,
            non_empty_lines=80,
            comment_lines=20,
            code_lines=60,
            character_count=2000,
            average_line_length=20.0
        )
        
        assert stats.total_lines == 100
        assert stats.code_lines == 60
        assert stats.average_line_length == 20.0
    
    def test_basic_stats_negative_values(self):
        """Test BasicStats validates non-negative values."""
        with pytest.raises(ValidationError):
            BasicStats(
                total_lines=-1,  # Invalid
                non_empty_lines=80,
                comment_lines=20,
                code_lines=60,
                character_count=2000,
                average_line_length=20.0
            )
    
    def test_function_info_valid(self):
        """Test FunctionInfo model creation."""
        func = FunctionInfo(
            name="test_function",
            line=10,
            args=["self", "param1", "param2"],
            decorators=["@property"],
            docstring="Test function docstring",
            complexity=3
        )
        
        assert func.name == "test_function"
        assert func.line == 10
        assert len(func.args) == 3
        assert func.complexity == 3
    
    def test_function_info_validates_line_number(self):
        """Test FunctionInfo validates positive line numbers."""
        with pytest.raises(ValidationError):
            FunctionInfo(name="test", line=0)  # Invalid: must be >= 1
    
    def test_provider_usage_calculates_total(self):
        """Test ProviderUsage automatically calculates total tokens."""
        usage = ProviderUsage(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=250  # Incorrect total
        )
        
        # Should auto-correct to 300
        assert usage.total_tokens == 300
    
    def test_provider_response_valid(self):
        """Test ProviderResponse model creation."""
        response = ProviderResponse(
            content="Generated code here",
            model="gpt-4",
            usage=ProviderUsage(
                prompt_tokens=50,
                completion_tokens=100,
                total_tokens=150
            ),
            finish_reason="stop"
        )
        
        assert response.content == "Generated code here"
        assert response.tokens_used == 150
        assert response.model == "gpt-4"


class TestContextModels:
    """Test context and state models."""
    
    def test_chat_message_valid(self):
        """Test ChatMessage model creation."""
        message = ChatMessage(
            role=MessageRole.USER,
            content="Hello, world!",
            metadata=MessageMetadata(
                tokens_used=10,
                model="gpt-4",
                processing_time=1.5
            )
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.metadata.tokens_used == 10
        assert isinstance(message.timestamp, datetime)
    
    def test_chat_message_validates_content(self):
        """Test ChatMessage validates non-empty content."""
        with pytest.raises(ValidationError) as exc_info:
            ChatMessage(role=MessageRole.USER, content="")
        
        assert "Message content cannot be empty" in str(exc_info.value)
    
    def test_file_context_info_valid(self):
        """Test FileContextInfo model creation."""
        file_info = FileContextInfo(
            path="/path/to/file.py",
            content="def hello(): pass",
            language=LanguageType.PYTHON,
            last_modified=datetime.now(),
            size=1024
        )
        
        assert file_info.path == "/path/to/file.py"
        assert file_info.language == LanguageType.PYTHON
        assert file_info.size == 1024
    
    def test_git_info_valid(self):
        """Test GitInfo model creation."""
        git_info = GitInfo(
            branch="main",
            commit="abc123",
            is_dirty=False,
            remote_url="https://github.com/user/repo.git"
        )
        
        assert git_info.branch == "main"
        assert git_info.commit == "abc123"
        assert git_info.is_dirty is False


class TestToolModels:
    """Test tool system models."""
    
    def test_tool_parameter_valid(self):
        """Test ToolParameter model creation."""
        param = ToolParameter(
            type="string",
            description="File path parameter",
            required=True,
            enum=["read", "write", "delete"]
        )
        
        assert param.type == "string"
        assert param.required is True
        assert len(param.enum) == 3
    
    def test_tool_schema_valid(self):
        """Test ToolSchema model creation."""
        schema = ToolSchema(
            name="file_tool",
            description="File operations tool",
            parameters={
                "action": ToolParameter(
                    type="string",
                    description="Action to perform"
                )
            },
            capabilities=[AgentCapability.TOOL_EXECUTION]
        )
        
        assert schema.name == "file_tool"
        assert "action" in schema.parameters
        assert AgentCapability.TOOL_EXECUTION in schema.capabilities
    
    def test_tool_result_valid(self):
        """Test ToolResult model creation."""
        result = ToolResult(
            success=True,
            output="Operation completed",
            execution_time=0.5,
            metadata={"files_processed": 3}
        )
        
        assert result.success is True
        assert result.output == "Operation completed"
        assert result.execution_time == 0.5
        assert result.metadata["files_processed"] == 3


class TestConfigurationModels:
    """Test configuration models."""
    
    def test_model_config_valid(self):
        """Test ModelConfig creation with valid data."""
        config = ModelConfig(
            name="gpt-4",
            provider=ModelProvider.OPENAI,
            max_tokens=4000,
            temperature=0.1,
            timeout=30
        )
        
        assert config.name == "gpt-4"
        assert config.provider == ModelProvider.OPENAI
        assert config.max_tokens == 4000
    
    def test_model_config_validates_provider_model_match(self):
        """Test ModelConfig validates model matches provider."""
        # Valid: OpenAI model with OpenAI provider
        ModelConfig(name="gpt-4", provider=ModelProvider.OPENAI)
        
        # Valid: Anthropic model with Anthropic provider  
        ModelConfig(name="claude-3-sonnet", provider=ModelProvider.ANTHROPIC)
        
        # Invalid: OpenAI model with Anthropic provider
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(name="gpt-4", provider=ModelProvider.ANTHROPIC)
        
        assert "doesn't match Anthropic provider" in str(exc_info.value)
    
    def test_model_config_validates_ranges(self):
        """Test ModelConfig validates parameter ranges."""
        with pytest.raises(ValidationError):
            ModelConfig(max_tokens=0)  # Too low
        
        with pytest.raises(ValidationError):
            ModelConfig(max_tokens=50000)  # Too high
        
        with pytest.raises(ValidationError):
            ModelConfig(temperature=-0.1)  # Too low
        
        with pytest.raises(ValidationError):
            ModelConfig(temperature=2.1)  # Too high
    
    def test_project_config_validates_path(self):
        """Test ProjectConfig validates root path exists."""
        # Valid path
        config = ProjectConfig(root=Path("."))
        assert config.root.exists()
        
        # Invalid path - should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            ProjectConfig(root=Path("/nonexistent/path"))
        
        assert "Root path does not exist" in str(exc_info.value)
    
    def test_security_config_validates_file_types(self):
        """Test SecurityConfig validates file type format."""
        # Valid file types
        config = SecurityConfig(allowed_file_types=[".py", ".js", ".ts"])
        assert len(config.allowed_file_types) == 3
        
        # Invalid file types (missing dot)
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(allowed_file_types=["py", "js"])
        
        assert "File type must start with dot" in str(exc_info.value)
    
    def test_agent_config_validates_ranges(self):
        """Test AgentConfig validates parameter ranges."""
        # Valid config
        config = AgentConfig(context_window=10, max_retries=3)
        assert config.context_window == 10
        
        # Invalid ranges
        with pytest.raises(ValidationError):
            AgentConfig(context_window=0)  # Too low
        
        with pytest.raises(ValidationError):
            AgentConfig(context_window=200)  # Too high
        
        with pytest.raises(ValidationError):
            AgentConfig(max_retries=-1)  # Too low


class TestStatusAndErrorModels:
    """Test status and error models."""
    
    def test_agent_status_valid(self):
        """Test AgentStatus model creation."""
        status = AgentStatus(
            model="gpt-4",
            provider="OpenAI",
            capabilities=[AgentCapability.CODE_ANALYSIS, AgentCapability.CHAT],
            context={"messages": 5, "files": 2},
            config={"debug": False},
            uptime=3600.0,
            health_status="healthy"
        )
        
        assert status.model == "gpt-4"
        assert len(status.capabilities) == 2
        assert status.health_status == "healthy"
        assert status.uptime == 3600.0
    
    def test_agent_error_valid(self):
        """Test AgentError model creation."""
        error = AgentError(
            code="VALIDATION_ERROR",
            message="Input validation failed",
            details={"field": "code", "issue": "empty"},
            suggestion="Provide non-empty code"
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Input validation failed"
        assert error.details["field"] == "code"
        assert isinstance(error.timestamp, datetime)
    
    def test_validation_result_valid(self):
        """Test ValidationResult model creation."""
        result = ValidationResult(
            valid=False,
            errors=["Field is required", "Invalid format"],
            warnings=["Deprecated syntax"],
            sanitized_input="cleaned_input"
        )
        
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.sanitized_input == "cleaned_input"


class TestModelIntegration:
    """Test model integration and relationships."""
    
    def test_code_analysis_response_complete(self):
        """Test complete CodeAnalysisResponse creation."""
        response = CodeAnalysisResponse(
            language=LanguageType.PYTHON,
            basic_stats=BasicStats(
                total_lines=50,
                non_empty_lines=40,
                comment_lines=10,
                code_lines=30,
                character_count=1000,
                average_line_length=20.0
            ),
            structure=CodeStructure(
                functions=[
                    FunctionInfo(name="test_func", line=10)
                ],
                classes=[
                    ClassInfo(name="TestClass", line=20)
                ],
                imports=[
                    ImportInfo(type="import", name="os", line=1)
                ]
            ),
            quality=QualityAnalysis(
                ai_quality_analysis="Good code quality",
                score=8,
                issues=["Missing docstring"],
                recommendations=["Add type hints"]
            ),
            complexity=ComplexityMetrics(
                cyclomatic_complexity=5,
                cognitive_complexity=3,
                nesting_depth=2,
                function_count=1,
                class_count=1,
                lines_of_code=30
            )
        )
        
        assert response.language == LanguageType.PYTHON
        assert response.basic_stats.total_lines == 50
        assert len(response.structure.functions) == 1
        assert response.quality.score == 8
        assert response.complexity.function_count == 1
        assert isinstance(response.timestamp, datetime)
    
    def test_project_info_with_git(self):
        """Test ProjectInfo with GitInfo."""
        project = ProjectInfo(
            root_path=Path("."),
            name="test-project",
            description="A test project",
            languages=[LanguageType.PYTHON, LanguageType.JAVASCRIPT],
            file_count=25,
            total_size=50000,
            dependencies=["pytest", "pydantic"],
            git_info=GitInfo(
                branch="main",
                commit="abc123",
                is_dirty=False
            )
        )
        
        assert project.name == "test-project"
        assert len(project.languages) == 2
        assert project.git_info.branch == "main"
        assert project.file_count == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])