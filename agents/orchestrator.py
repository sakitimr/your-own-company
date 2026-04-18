"""
Orchestrator - CEO 视角的全局调度与监控引擎
"""
import re
import time
import uuid
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass, field

from .base_agent import AgentStatus, TaskResult
from .specialized_agents import (
    CEOAgent, ResearchAgent, WriterAgent,
    CoderAgent, DataAnalystAgent, DocumentAgent
)
from .llm_client import LLMClient


@dataclass
class WorkflowTask:
    """工作流中的单个子任务"""
    task_id: str
    agent_type: str
    description: str
    status: str = "pending"   # pending / running / done / error / skipped
    result: Optional[TaskResult] = None
    depends_on: List[str] = field(default_factory=list)


@dataclass
class WorkflowRun:
    """一次完整的工作流执行记录"""
    run_id: str
    user_request: str
    tasks: List[WorkflowTask] = field(default_factory=list)
    final_report: str = ""
    status: str = "pending"   # pending / running / done / error
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    @property
    def duration(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

    @property
    def progress(self) -> int:
        if not self.tasks:
            return 0
        done = sum(1 for t in self.tasks if t.status in ("done", "error", "skipped"))
        return int(done / len(self.tasks) * 100)


class Orchestrator:
    """
    CEO 视角的调度引擎：
    - 解析 CEO 的任务规划，动态构建工作流
    - 按依赖顺序调度各 Agent 执行
    - 实时推送状态更新给前端
    - 汇总最终报告
    """

    AGENT_KEYWORD_MAP = {
        "研究员": "researcher",
        "研究":   "researcher",
        "调研":   "researcher",
        "写作":   "writer",
        "文案":   "writer",
        "撰写":   "writer",
        "代码":   "coder",
        "编程":   "coder",
        "开发":   "coder",
        "数据分析": "analyst",
        "分析":   "analyst",
        "文档":   "doc",
        "整理":   "doc",
    }

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agents: Dict[str, Any] = {
            "ceo":        CEOAgent(),
            "researcher": ResearchAgent(),
            "writer":     WriterAgent(),
            "coder":      CoderAgent(),
            "analyst":    DataAnalystAgent(),
            "doc":        DocumentAgent(),
        }
        self.ceo: CEOAgent = self.agents["ceo"]
        self.run_history: List[WorkflowRun] = []
        self.current_run: Optional[WorkflowRun] = None
        self._on_update: Optional[Callable] = None  # 状态变更回调

    def register_callback(self, fn: Callable):
        """注册状态更新回调（供前端实时刷新）"""
        self._on_update = fn

    def _notify(self, message: str, level: str = "info"):
        if self._on_update:
            self._on_update({"message": message, "level": level,
                             "time": time.strftime("%H:%M:%S")})

    # ──────────────────────────────────────────────────────────────
    # 任务规划解析
    # ──────────────────────────────────────────────────────────────
    def _parse_plan(self, plan_text: str) -> List[WorkflowTask]:
        """将 CEO 生成的任务计划文本解析为 WorkflowTask 列表"""
        tasks = []
        lines = plan_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 匹配格式：[Agent类型] 任务描述  或  数字. [Agent类型] 任务描述
            m = re.search(r'\[([^\]]+)\]\s*(.+)', line)
            if m:
                agent_keyword = m.group(1).strip()
                description = m.group(2).strip()
                agent_type = self._resolve_agent_type(agent_keyword)
                tasks.append(WorkflowTask(
                    task_id=str(uuid.uuid4())[:8],
                    agent_type=agent_type,
                    description=description
                ))
        # 如果解析不到结构化任务，默认创建单个研究任务
        if not tasks:
            tasks.append(WorkflowTask(
                task_id=str(uuid.uuid4())[:8],
                agent_type="researcher",
                description=plan_text[:200]
            ))
        return tasks

    def _resolve_agent_type(self, keyword: str) -> str:
        for k, v in self.AGENT_KEYWORD_MAP.items():
            if k in keyword:
                return v
        return "researcher"

    # ──────────────────────────────────────────────────────────────
    # 主调度入口
    # ──────────────────────────────────────────────────────────────
    def run(self, user_request: str,
            on_update: Optional[Callable] = None) -> WorkflowRun:
        """执行完整工作流"""
        if on_update:
            self._on_update = on_update

        run = WorkflowRun(
            run_id=str(uuid.uuid4())[:8],
            user_request=user_request
        )
        self.current_run = run
        self.run_history.append(run)
        run.status = "running"

        # ① CEO 规划
        self._notify("🧠 CEO 正在分析任务并制定执行计划...")
        self.agents["ceo"].set_status(AgentStatus.THINKING)
        plan_text = self.ceo.plan_tasks(user_request, self.llm_client)
        self._notify(f"📋 CEO 制定计划完成，开始任务拆解")
        run.tasks = self._parse_plan(plan_text)

        if not run.tasks:
            run.status = "error"
            run.final_report = "任务规划失败，无法生成子任务"
            return run

        # ② 按序执行各子任务
        collected_results = []
        for idx, task in enumerate(run.tasks):
            agent = self.agents.get(task.agent_type, self.agents["researcher"])
            self._notify(
                f"▶ [{idx+1}/{len(run.tasks)}] {agent.emoji} {agent.name} 开始执行: {task.description[:50]}..."
            )
            task.status = "running"

            # 构造上下文（把已完成任务的结果作为背景）
            context = ""
            if collected_results:
                context = "已完成的前序任务结果：\n" + "\n\n".join(
                    [f"[{r['agent']}]: {r['output'][:500]}" for r in collected_results]
                )

            result = agent.execute(task.description, context, self.llm_client)
            task.result = result

            if result.status == "success":
                task.status = "done"
                collected_results.append({
                    "agent": agent.name,
                    "output": result.output
                })
                self._notify(
                    f"✅ {agent.name} 完成，耗时 {result.duration}s", "success"
                )
            else:
                task.status = "error"
                self._notify(f"❌ {agent.name} 执行失败: {result.error}", "error")

        # ③ CEO 综合汇总
        self._notify("📝 CEO 正在综合所有结果，生成最终报告...")
        self.agents["ceo"].set_status(AgentStatus.WORKING)
        run.final_report = self.ceo.summarize(user_request, collected_results, self.llm_client)
        self.agents["ceo"].set_status(AgentStatus.DONE)

        run.status = "done"
        run.end_time = time.time()
        self._notify(
            f"🎉 工作流执行完毕！总耗时 {run.duration}s，共 {len(run.tasks)} 个子任务", "success"
        )
        return run

    # ──────────────────────────────────────────────────────────────
    # CEO 视角：全局状态查询
    # ──────────────────────────────────────────────────────────────
    def get_agent_statuses(self) -> List[Dict]:
        return [
            {
                **agent.to_dict(),
                "task_count": len(agent.task_history),
                "last_task": agent.task_history[-1].task_id if agent.task_history else "-",
            }
            for agent in self.agents.values()
        ]

    def get_run_summary(self, run: WorkflowRun) -> Dict:
        total = len(run.tasks)
        done = sum(1 for t in run.tasks if t.status == "done")
        error = sum(1 for t in run.tasks if t.status == "error")
        return {
            "run_id": run.run_id,
            "status": run.status,
            "progress": run.progress,
            "total_tasks": total,
            "done_tasks": done,
            "error_tasks": error,
            "duration": run.duration,
        }

    def reset_agents(self):
        """重置所有 Agent 状态"""
        for agent in self.agents.values():
            agent.reset()
