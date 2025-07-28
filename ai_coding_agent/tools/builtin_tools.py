"""Built-in tools for common coding tasks."""

import os
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Tool, ToolResult


logger = logging.getLogger(__name__)


class FileSystemTool(Tool):
    """Tool for file system operations."""
    
    def __init__(self):
        super().__init__(
            name="filesystem",
            description="Read, write, and manage files and directories"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "enum": ["read", "write", "list", "create_dir", "delete"],
                "description": "Action to perform"
            },
            "path": {
                "type": "string",
                "description": "File or directory path"
            },
            "content": {
                "type": "string",
                "description": "Content to write (for write action)"
            }
        }
    
    async def execute(self, action: str, path: str, content: Optional[str] = None) -> ToolResult:
        """Execute file system operation."""
        try:
            path_obj = Path(path)
            
            if action == "read":
                if not path_obj.exists():
                    return ToolResult(False, None, f"File not found: {path}")
                
                with open(path_obj, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                return ToolResult(True, file_content)
            
            elif action == "write":
                if content is None:
                    return ToolResult(False, None, "Content is required for write action")
                
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                with open(path_obj, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return ToolResult(True, f"File written: {path}")
            
            elif action == "list":
                if not path_obj.exists():
                    return ToolResult(False, None, f"Directory not found: {path}")
                
                if path_obj.is_file():
                    return ToolResult(True, [str(path_obj)])
                
                files = [str(p) for p in path_obj.iterdir()]
                return ToolResult(True, files)
            
            elif action == "create_dir":
                path_obj.mkdir(parents=True, exist_ok=True)
                return ToolResult(True, f"Directory created: {path}")
            
            elif action == "delete":
                if path_obj.is_file():
                    path_obj.unlink()
                elif path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path_obj)
                else:
                    return ToolResult(False, None, f"Path not found: {path}")
                
                return ToolResult(True, f"Deleted: {path}")
            
            else:
                return ToolResult(False, None, f"Unknown action: {action}")
                
        except Exception as e:
            return ToolResult(False, None, str(e))


class GitTool(Tool):
    """Tool for Git operations."""
    
    def __init__(self):
        super().__init__(
            name="git",
            description="Perform Git version control operations"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "enum": ["status", "add", "commit", "push", "pull", "branch", "log"],
                "description": "Git action to perform"
            },
            "message": {
                "type": "string",
                "description": "Commit message (for commit action)"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to add (for add action)"
            }
        }
    
    async def execute(self, action: str, message: Optional[str] = None, 
                     files: Optional[List[str]] = None) -> ToolResult:
        """Execute Git operation."""
        try:
            if action == "status":
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if result.returncode != 0:
                    return ToolResult(False, None, result.stderr)
                
                return ToolResult(True, result.stdout)
            
            elif action == "add":
                if not files:
                    files = ["."]
                
                cmd = ["git", "add"] + files
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return ToolResult(False, None, result.stderr)
                
                return ToolResult(True, f"Added files: {', '.join(files)}")
            
            elif action == "commit":
                if not message:
                    return ToolResult(False, None, "Commit message is required")
                
                result = subprocess.run(
                    ["git", "commit", "-m", message],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return ToolResult(False, None, result.stderr)
                
                return ToolResult(True, result.stdout)
            
            elif action == "log":
                result = subprocess.run(
                    ["git", "log", "--oneline", "-10"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return ToolResult(False, None, result.stderr)
                
                return ToolResult(True, result.stdout)
            
            else:
                return ToolResult(False, None, f"Unsupported Git action: {action}")
                
        except Exception as e:
            return ToolResult(False, None, str(e))


class LinterTool(Tool):
    """Tool for code linting."""
    
    def __init__(self):
        super().__init__(
            name="linter",
            description="Run code linters to check for issues"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "file_path": {
                "type": "string",
                "description": "Path to the file to lint"
            },
            "language": {
                "type": "string",
                "description": "Programming language"
            }
        }
    
    async def execute(self, file_path: str, language: str = "python") -> ToolResult:
        """Execute linting."""
        try:
            if language == "python":
                # Try flake8 first
                result = subprocess.run(
                    ["flake8", file_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return ToolResult(True, "No linting issues found")
                else:
                    return ToolResult(True, result.stdout, metadata={"has_issues": True})
            
            else:
                return ToolResult(False, None, f"Linting not supported for {language}")
                
        except FileNotFoundError:
            return ToolResult(False, None, f"Linter not found for {language}")
        except Exception as e:
            return ToolResult(False, None, str(e))


class FormatterTool(Tool):
    """Tool for code formatting."""
    
    def __init__(self):
        super().__init__(
            name="formatter",
            description="Format code according to style guidelines"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "file_path": {
                "type": "string",
                "description": "Path to the file to format"
            },
            "language": {
                "type": "string",
                "description": "Programming language"
            },
            "dry_run": {
                "type": "boolean",
                "description": "Preview changes without applying them"
            }
        }
    
    async def execute(self, file_path: str, language: str = "python", 
                     dry_run: bool = False) -> ToolResult:
        """Execute code formatting."""
        try:
            if language == "python":
                cmd = ["black"]
                if dry_run:
                    cmd.append("--diff")
                cmd.append(file_path)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    if dry_run:
                        return ToolResult(True, result.stdout or "No changes needed")
                    else:
                        return ToolResult(True, "File formatted successfully")
                else:
                    return ToolResult(False, None, result.stderr)
            
            else:
                return ToolResult(False, None, f"Formatting not supported for {language}")
                
        except FileNotFoundError:
            return ToolResult(False, None, f"Formatter not found for {language}")
        except Exception as e:
            return ToolResult(False, None, str(e))