"""
具体 Agent 实现 - CEO、研究员、写作、代码、数据分析、文档整理 Agent
"""
import time
import uuid
from typing import Optional
from .base_agent import BaseAgent, AgentStatus, TaskResult, AgentMessage


def _execute_with_llm(agent: BaseAgent, task: str, context: str, llm_client) -> TaskResult:
    """通用 LLM 执行逻辑"""
    task_id = str(uuid.uuid4())[:8]
    start = time.time()
    agent.set_status(AgentStatus.THINKING)
    agent.current_task = task
    agent.log(f"接收任务: {task[:80]}...")

    messages = [{"role": "system", "content": agent.get_system_prompt()}]
    if context:
        messages.append({"role": "user", "content": f"背景信息：\n{context}"})
    messages.append({"role": "user", "content": task})

    try:
        agent.set_status(AgentStatus.WORKING)
        output = llm_client.chat(messages, temperature=0.7)
        agent.set_status(AgentStatus.DONE)
        agent.log(f"任务完成，耗时 {time.time()-start:.1f}s")
        result = TaskResult(
            task_id=task_id,
            agent_id=agent.agent_id,
            agent_name=agent.name,
            status="success",
            output=output,
            duration=round(time.time() - start, 2)
        )
    except Exception as e:
        agent.set_status(AgentStatus.ERROR)
        agent.log(f"任务失败: {e}", level="error")
        result = TaskResult(
            task_id=task_id,
            agent_id=agent.agent_id,
            agent_name=agent.name,
            status="error",
            error=str(e),
            duration=round(time.time() - start, 2)
        )

    agent.task_history.append(result)
    agent.set_status(AgentStatus.IDLE)
    return result


# ─────────────────────────────────────────────────────────────────
# CEO Agent：任务拆解与协调调度
# ─────────────────────────────────────────────────────────────────
class CEOAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="ceo",
            name="CEO 总指挥",
            role="任务拆解与多 Agent 协调调度",
            description=(
                "你是公司的 CEO，负责理解用户的高层目标，将复杂任务拆解为子任务，"
                "并分配给合适的专业 Agent 执行。你需要综合所有 Agent 的输出，形成最终报告。"
            ),
            emoji="👔"
        )

    def get_system_prompt(self) -> str:
        return """你是多智能体协同办公平台的 CEO，职责是：
1. 分析用户需求，识别任务类型
2. 将复杂任务拆解为若干子任务（每个子任务一行，格式：[Agent类型] 任务描述）
3. 综合所有 Agent 的执行结果，输出清晰的总结报告

Agent 类型说明：
- [研究员] 负责信息调研、资料收集
- [写作] 负责文案撰写、报告生成
- [代码] 负责代码编写、技术实现
- [数据分析] 负责数据处理、图表分析
- [文档整理] 负责文档整合、格式化输出

请用中文回复，保持专业简洁。"""

    def plan_tasks(self, user_request: str, llm_client) -> str:
        """将用户请求拆解为子任务列表"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"请将以下任务拆解为子任务计划：\n\n{user_request}"}
        ]
        self.set_status(AgentStatus.THINKING)
        self.log(f"正在规划任务: {user_request[:60]}...")
        try:
            plan = llm_client.chat(messages, temperature=0.5)
            self.set_status(AgentStatus.IDLE)
            return plan
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            return f"任务规划失败: {e}"

    def summarize(self, task: str, results: list, llm_client) -> str:
        """综合所有 Agent 结果生成最终报告"""
        results_text = "\n\n".join(
            [f"### {r['agent']} 的执行结果\n{r['output']}" for r in results]
        )
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": (
                f"原始任务：{task}\n\n"
                f"各 Agent 执行结果如下：\n{results_text}\n\n"
                "请综合以上结果，生成一份完整、专业的最终报告。"
            )}
        ]
        self.set_status(AgentStatus.WORKING)
        try:
            summary = llm_client.chat(messages, temperature=0.6, max_tokens=3000)
            self.set_status(AgentStatus.DONE)
            return summary
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            return f"总结失败: {e}"

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)


# ─────────────────────────────────────────────────────────────────
# 研究员 Agent
# ─────────────────────────────────────────────────────────────────
class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="researcher",
            name="资深研究员",
            role="信息调研与资料整合",
            description=(
                "你是一位经验丰富的研究员，擅长快速检索和整合各类信息，"
                "提供深度背景资料、行业分析和关键洞察。"
            ),
            emoji="🔍"
        )

    def get_system_prompt(self) -> str:
        return """你是一位专业的研究员，职责是：
1. 深度分析研究主题，梳理关键背景信息
2. 提供数据支撑、行业案例和趋势分析
3. 识别潜在风险和机会
4. 给出有价值的洞察和建议

输出格式要求：
- 使用清晰的标题层级
- 关键数据用**加粗**标注
- 结尾附上核心结论（3-5条）
用中文回复。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)


# ─────────────────────────────────────────────────────────────────
# 写作 Agent
# ─────────────────────────────────────────────────────────────────
class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="writer",
            name="资深文案",
            role="文案撰写与内容创作",
            description=(
                "你是一位资深文案专家，擅长撰写各类商业文档、营销文案、"
                "报告、邮件和演讲稿，风格专业且有感染力。"
            ),
            emoji="✍️"
        )

    def get_system_prompt(self) -> str:
        return """你是一位专业文案撰写专家，职责是：
1. 根据需求撰写高质量文案、报告、邮件或文档
2. 确保内容逻辑清晰、语言流畅、表达准确
3. 根据受众调整文风（正式/轻松/学术等）
4. 使用合适的结构（标题、段落、列表）增强可读性

请直接输出最终文案内容，无需解释写作思路。用中文回复。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)


# ─────────────────────────────────────────────────────────────────
# 代码 Agent
# ─────────────────────────────────────────────────────────────────
class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="coder",
            name="全栈工程师",
            role="代码编写与技术实现",
            description=(
                "你是一位全栈工程师，精通 Python、JavaScript、SQL 等主流语言，"
                "能够快速实现功能模块、解决技术问题并编写清晰注释。"
            ),
            emoji="💻"
        )

    def get_system_prompt(self) -> str:
        return """你是一位资深全栈工程师，职责是：
1. 理解需求，编写高质量、可运行的代码
2. 添加清晰的注释和使用说明
3. 考虑边界情况和错误处理
4. 提供简洁的技术说明和使用示例

输出格式：代码块 + 简要说明。用中文注释和说明。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)


# ─────────────────────────────────────────────────────────────────
# 数据分析 Agent
# ─────────────────────────────────────────────────────────────────
class DataAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="analyst",
            name="数据分析师",
            role="数据处理与分析洞察",
            description=(
                "你是一位专业的数据分析师，擅长从数据中挖掘规律、"
                "制作分析报告、提供数据驱动的决策建议。"
            ),
            emoji="📊"
        )

    def get_system_prompt(self) -> str:
        return """你是一位专业数据分析师，职责是：
1. 理解数据分析需求，制定分析方案
2. 分析数据规律、趋势和异常
3. 提供数据驱动的洞察和建议
4. 必要时给出可视化方案（说明图表类型和关键指标）

输出格式：分析结论 + 关键发现（要点形式）+ 建议行动。用中文回复。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)


# ─────────────────────────────────────────────────────────────────
# 文档整理 Agent
# ─────────────────────────────────────────────────────────────────
class DocumentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="doc",
            name="文档整理专员",
            role="文档整合与格式化输出",
            description=(
                "你是一位专注于文档整理的专员，擅长将多方信息整合为"
                "结构清晰、格式规范的最终文档。"
            ),
            emoji="📋"
        )

    def get_system_prompt(self) -> str:
        return """你是一位专业文档整理专员，职责是：
1. 整合多个来源的内容，形成统一文档
2. 确保格式规范、层级清晰
3. 消除重复内容，保持逻辑连贯
4. 添加目录、摘要等结构性元素

请输出格式规范的 Markdown 文档。用中文。"""

    def execute(self, task: str, context: str = "", llm_client=None) -> TaskResult:
        return _execute_with_llm(self, task, context, llm_client)
