# AI Coding Agent

A sophisticated AI-powered coding assistant available as both a Python CLI tool and a VS Code extension. This project combines the power of large language models with advanced code analysis tools to provide intelligent coding assistance across multiple platforms.

## 🚀 Available Versions

### 📦 Python CLI Tool
A command-line interface for terminal-based AI coding assistance.

**Features:**
- Interactive CLI for coding assistance
- Code analysis and generation
- Project overview and insights
- Multi-language support
- Git integration

**[View Python CLI Documentation →](./README-python.md)**

### 🔧 VS Code Extension
A fully-integrated Visual Studio Code extension with rich UI components.

**Features:**
- Interactive AI chat sidebar
- Code analysis with visual feedback
- One-click code generation and fixes
- Project overview dashboard
- Context menu integration
- Beautiful webview interfaces

**[View VS Code Extension →](./vscode-extension/)**

## 🏗️ Repository Structure

```
ai-coding-agent/
├── 📁 ai_coding_agent/          # Python CLI source code
│   ├── core/                    # Core agent functionality
│   ├── analyzers/              # Code analysis tools
│   ├── generators/             # Code generation
│   └── tools/                  # Additional tools
├── 📁 vscode-extension/         # VS Code extension
│   ├── src/                    # TypeScript source
│   ├── package.json            # Extension manifest
│   └── README.md               # Extension documentation
├── 📁 tests/                   # Python tests
├── pyproject.toml              # Python project config
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### For Python CLI Users

```bash
# Clone the repository
git clone <repository-url>
cd ai-coding-agent

# Install Python dependencies
pip install -r requirements.txt

# Start using the CLI
python -m ai_coding_agent chat
```

### For VS Code Extension Users

```bash
# Clone the repository
git clone <repository-url>
cd ai-coding-agent/vscode-extension

# Install dependencies
npm install

# Build the extension
npm run compile

# Package for installation
npm run package
```

Or install directly from the VS Code Marketplace (when published).

## 🔧 Configuration

Both versions support the same AI providers and models:

- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude-3 Sonnet, Claude-3 Opus, Claude-3 Haiku

### Python CLI Configuration
Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_MODEL=gpt-4
```

### VS Code Extension Configuration
Configure through VS Code Settings:
- `aiCodingAgent.openaiApiKey`
- `aiCodingAgent.anthropicApiKey`
- `aiCodingAgent.defaultModel`

## 🌟 Features Comparison

| Feature | Python CLI | VS Code Extension |
|---------|------------|------------------|
| Code Analysis | ✅ Terminal output | ✅ Rich webview panels |
| Code Generation | ✅ Text output | ✅ Direct insertion |
| Project Overview | ✅ Terminal display | ✅ Interactive dashboard |
| Chat Interface | ✅ Terminal chat | ✅ Sidebar panel |
| Context Menu | ❌ | ✅ Right-click integration |
| History Tracking | ❌ | ✅ Conversation history |
| Multi-file Support | ✅ CLI commands | ✅ Workspace integration |

## 🛠️ Development

### Python CLI Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black .
isort .
```

### VS Code Extension Development

```bash
cd vscode-extension

# Install dependencies
npm install

# Start development mode
npm run watch

# Run tests
npm test

# Package extension
npm run package
```

## 📋 Requirements

### Python CLI
- Python 3.9+
- OpenAI API key and/or Anthropic API key
- Internet connection

### VS Code Extension
- Visual Studio Code 1.74.0+
- OpenAI API key and/or Anthropic API key
- Internet connection

## 🤝 Contributing

We welcome contributions to both the Python CLI and VS Code extension!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (for Python CLI: pytest, for VS Code: npm test)
5. Submit a pull request

### Development Guidelines

- **Python CLI**: Follow PEP 8, use type hints, add docstrings
- **VS Code Extension**: Use TypeScript, follow VS Code extension guidelines
- **Documentation**: Update relevant README files
- **Tests**: Ensure all tests pass before submitting

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Python CLI Documentation**: [README-python.md](./README-python.md)
- **VS Code Extension**: [vscode-extension/](./vscode-extension/)
- **Issues**: [GitHub Issues](https://github.com/ai-coding-agent/ai-coding-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-coding-agent/ai-coding-agent/discussions)

---

**Choose your preferred interface and start coding with AI assistance!** ⚡