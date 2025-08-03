# AI Coding Agent - Python CLI

A sophisticated AI-powered coding assistant that can analyze, understand, and generate code across multiple programming languages. This agent combines the power of large language models with advanced code analysis tools to provide intelligent coding assistance.

## Features

- **Code Analysis**: Deep understanding of codebases using AST parsing and semantic analysis
- **Code Generation**: Generate high-quality code snippets, functions, and entire modules
- **Multi-Language Support**: Works with Python, JavaScript, TypeScript, Java, C++, and more
- **Git Integration**: Understands project structure and version control history
- **Interactive CLI**: Command-line interface for easy interaction
- **Context-Aware**: Maintains conversation context and project understanding
- **Code Quality**: Automated code formatting, linting, and quality checks

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ai-coding-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with the following variables:

```bash
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_MODEL=gpt-4  # or claude-3-sonnet-20240229

# Agent Configuration
MAX_TOKENS=4000
TEMPERATURE=0.1
DEBUG=false

# Project Settings
PROJECT_ROOT=.
IGNORE_PATTERNS=__pycache__,*.pyc,.git,node_modules
```

## Usage

### Command Line Interface

```bash
# Start interactive session
ai-agent chat

# Analyze a specific file
ai-agent analyze path/to/file.py

# Generate code from description
ai-agent generate "Create a FastAPI endpoint for user authentication"

# Review and suggest improvements for code
ai-agent review path/to/file.py

# Auto-fix code issues
ai-agent fix path/to/file.py

# Get project overview
ai-agent overview
```

### Python API

```python
from ai_coding_agent import CodingAgent

# Initialize the agent
agent = CodingAgent(model="gpt-4")

# Analyze code
result = await agent.analyze_file("main.py")
print(result.summary)

# Generate code
code = await agent.generate_code(
    description="Create a binary search function",
    language="python"
)
print(code)

# Chat with the agent
response = await agent.chat("How can I optimize this function?", context=code)
print(response)
```

## Architecture

The AI Coding Agent is built with a modular architecture:

- **Core Agent**: Main intelligence engine that coordinates all operations
- **Code Analyzer**: Parses and understands code structure using AST and tree-sitter
- **Context Manager**: Maintains conversation and project context
- **Tool System**: Extensible tools for various coding tasks
- **Provider Interface**: Abstracts different AI model providers
- **CLI Interface**: Command-line interface for user interaction

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.