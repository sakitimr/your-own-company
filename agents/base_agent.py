"""
Base Agent - 所有 Agent 的基类
"""
import time
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    DONE = "done"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class AgentMessage:
    role: str          # "user" | "assistant" | "system"
    content: str
    agent_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskResult:
    task_id: str
    agent_id: str
    agent_name: str
    status: str        # "success" | "error" | "pending"
    output: str = ""
    error: str = ""
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)


class BaseAgent:
    """所有 Agent 的抽象基类"""

    def __init__(self, agent_id: str, name: str, role: str, description: str, emoji: str = "🤖"):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.emoji = emoji
        self.status = AgentStatus.IDLE
        self.message_history: List[AgentMessage] = []
        self.task_history: List[TaskResult] = []
        self.current_task: Optional[str] = None
        self.logs: List[Dict[str, Any]] = []

    def log(self, message: str, level: str = "info"):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "level": level,
            "agent": self.name,
            "message": message
        }
        self.logs.append(entry)

    def set_status(self, status: AgentStatus):
        self.status = status
        self.log(f"状态变更为: {status.value}")

    def get_system_prompt(self) -> str:
        return f"""你是 {self.name}，{self.description}
你的角色是: {self.role}
请始终以专业、高效的方式完成被分配的任务。
用中文回复，保持简洁清晰。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        raise NotImplementedError("子类必须实现 execute 方法")

    def reset(self):
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.message_history = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "emoji": self.emoji,
            "status": self.status.value,
        }
