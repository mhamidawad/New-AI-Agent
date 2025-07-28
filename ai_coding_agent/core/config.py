"""Configuration management for the AI Coding Agent."""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class ModelConfig(BaseModel):
    """Configuration for AI model settings."""
    
    name: str = Field(default="gpt-4", description="Model name to use")
    max_tokens: int = Field(default=4000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for response generation")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class ProjectConfig(BaseModel):
    """Configuration for project-specific settings."""
    
    root: Path = Field(default=Path("."), description="Project root directory")
    ignore_patterns: List[str] = Field(
        default=["__pycache__", "*.pyc", ".git", "node_modules", "*.log"],
        description="Patterns to ignore when analyzing code"
    )
    include_patterns: List[str] = Field(
        default=["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"],
        description="File patterns to include in analysis"
    )
    max_file_size: int = Field(default=1024 * 1024, description="Maximum file size to analyze in bytes")


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""
    
    debug: bool = Field(default=False, description="Enable debug mode")
    verbose: bool = Field(default=False, description="Enable verbose output")
    auto_save: bool = Field(default=True, description="Auto-save conversation context")
    context_window: int = Field(default=10, description="Number of previous messages to include in context")
    enable_tools: bool = Field(default=True, description="Enable tool usage")


class Config(BaseModel):
    """Main configuration class for the AI Coding Agent."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Model configuration
    model: ModelConfig = Field(default_factory=ModelConfig)
    
    # Project configuration
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    
    # Agent configuration
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        config_data = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": {
                "name": os.getenv("DEFAULT_MODEL", "gpt-4"),
                "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
                "temperature": float(os.getenv("TEMPERATURE", "0.1")),
                "timeout": int(os.getenv("TIMEOUT", "30")),
            },
            "project": {
                "root": Path(os.getenv("PROJECT_ROOT", ".")),
                "ignore_patterns": os.getenv("IGNORE_PATTERNS", "").split(",") if os.getenv("IGNORE_PATTERNS") else None,
                "max_file_size": int(os.getenv("MAX_FILE_SIZE", str(1024 * 1024))),
            },
            "agent": {
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "verbose": os.getenv("VERBOSE", "false").lower() == "true",
                "auto_save": os.getenv("AUTO_SAVE", "true").lower() == "true",
                "context_window": int(os.getenv("CONTEXT_WINDOW", "10")),
                "enable_tools": os.getenv("ENABLE_TOOLS", "true").lower() == "true",
            }
        }
        
        # Remove None values
        config_data = {k: v for k, v in config_data.items() if v is not None}
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    def save(self, path: str) -> None:
        """Save configuration to file."""
        import yaml
        
        config_dict = self.to_dict()
        # Remove sensitive data
        config_dict.pop("openai_api_key", None)
        config_dict.pop("anthropic_api_key", None)
        
        with open(path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    @classmethod
    def load(cls, path: str) -> "Config":
        """Load configuration from file."""
        import yaml
        
        with open(path, "r") as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)