"""Context management for maintaining conversation and project state."""

import json
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(**data)


@dataclass
class FileContext:
    """Context information about a file."""
    path: str
    content: str
    language: str
    last_modified: float
    size: int
    analysis: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileContext":
        """Create from dictionary."""
        return cls(**data)


class ProjectContext(BaseModel):
    """Context information about the project."""
    
    root_path: Path
    name: str
    description: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    file_count: int = 0
    total_size: int = 0
    structure: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    git_info: Optional[Dict[str, Any]] = None
    last_analyzed: Optional[float] = None


class ContextManager:
    """Manages conversation context and project state."""
    
    def __init__(self, context_window: int = 10, auto_save: bool = True):
        self.context_window = context_window
        self.auto_save = auto_save
        
        self.messages: List[Message] = []
        self.files: Dict[str, FileContext] = {}
        self.project: Optional[ProjectContext] = None
        self.session_id = str(int(time.time()))
        self.metadata: Dict[str, Any] = {}
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Trim to context window
        if len(self.messages) > self.context_window * 2:  # Keep some extra for system messages
            # Keep system messages and trim user/assistant messages
            system_messages = [m for m in self.messages if m.role == "system"]
            other_messages = [m for m in self.messages if m.role != "system"]
            
            # Keep the most recent messages within context window
            recent_messages = other_messages[-self.context_window:]
            self.messages = system_messages + recent_messages
        
        if self.auto_save:
            self._auto_save()
    
    def add_file_context(self, file_path: str, content: str, language: str, 
                        analysis: Optional[Dict[str, Any]] = None) -> None:
        """Add or update file context."""
        path_obj = Path(file_path)
        
        file_context = FileContext(
            path=file_path,
            content=content,
            language=language,
            last_modified=path_obj.stat().st_mtime if path_obj.exists() else time.time(),
            size=len(content.encode('utf-8')),
            analysis=analysis
        )
        
        self.files[file_path] = file_context
        
        if self.auto_save:
            self._auto_save()
    
    def set_project_context(self, project: ProjectContext) -> None:
        """Set the project context."""
        self.project = project
        
        if self.auto_save:
            self._auto_save()
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history."""
        messages = self.messages
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_file_context(self, file_path: str) -> Optional[FileContext]:
        """Get context for a specific file."""
        return self.files.get(file_path)
    
    def get_relevant_files(self, query: str, limit: int = 5) -> List[FileContext]:
        """Get files most relevant to a query."""
        # Simple relevance scoring based on content similarity
        relevant_files = []
        
        for file_context in self.files.values():
            score = self._calculate_relevance(query, file_context)
            relevant_files.append((score, file_context))
        
        # Sort by relevance score and return top files
        relevant_files.sort(key=lambda x: x[0], reverse=True)
        return [file_context for _, file_context in relevant_files[:limit]]
    
    def _calculate_relevance(self, query: str, file_context: FileContext) -> float:
        """Calculate relevance score between query and file."""
        # Simple keyword-based relevance scoring
        query_words = set(query.lower().split())
        content_words = set(file_context.content.lower().split())
        
        # Jaccard similarity
        intersection = len(query_words.intersection(content_words))
        union = len(query_words.union(content_words))
        
        return intersection / union if union > 0 else 0.0
    
    def clear_context(self) -> None:
        """Clear all context data."""
        self.messages.clear()
        self.files.clear()
        self.project = None
        self.metadata.clear()
    
    def save_to_file(self, file_path: str) -> None:
        """Save context to a JSON file."""
        context_data = {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "files": {path: file_ctx.to_dict() for path, file_ctx in self.files.items()},
            "project": self.project.model_dump() if self.project else None,
            "metadata": self.metadata,
            "timestamp": time.time()
        }
        
        with open(file_path, 'w') as f:
            json.dump(context_data, f, indent=2, default=str)
    
    def load_from_file(self, file_path: str) -> None:
        """Load context from a JSON file."""
        with open(file_path, 'r') as f:
            context_data = json.load(f)
        
        self.session_id = context_data.get("session_id", self.session_id)
        
        # Load messages
        self.messages = [
            Message.from_dict(msg_data) 
            for msg_data in context_data.get("messages", [])
        ]
        
        # Load files
        self.files = {
            path: FileContext.from_dict(file_data)
            for path, file_data in context_data.get("files", {}).items()
        }
        
        # Load project
        project_data = context_data.get("project")
        if project_data:
            self.project = ProjectContext(**project_data)
        
        # Load metadata
        self.metadata = context_data.get("metadata", {})
    
    def _auto_save(self) -> None:
        """Auto-save context to a temporary file."""
        if not self.auto_save:
            return
            
        # Save to a session-specific file
        save_dir = Path(".ai_agent_context")
        save_dir.mkdir(exist_ok=True)
        
        save_path = save_dir / f"session_{self.session_id}.json"
        self.save_to_file(str(save_path))
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "file_count": len(self.files),
            "project_name": self.project.name if self.project else None,
            "last_activity": self.messages[-1].timestamp if self.messages else None,
        }