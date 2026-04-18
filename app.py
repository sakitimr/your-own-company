"""
Multi-Agent Office Platform
基于大模型的多智能体协同办公平台
主入口 - Streamlit 前端界面
"""
import time
import threading
import streamlit as st
from agents.llm_client import LLMClient
from agents.orchestrator import Orchestrator, WorkflowRun
from agents.base_agent import AgentStatus

# ──────────────────────────────────────────────────────────────────
# 页面配置
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="多智能体协同办公平台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────
# 自定义 CSS
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 整体背景 */
.stApp { background: #0f1117; }

/* 卡片样式 */
.agent-card {
    background: linear-gradient(135deg, #1e2130 0%, #252a3a 100%);
    border: 1px solid #2d3347;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 6px 0;
    transition: all 0.3s ease;
}
.agent-card:hover { border-color: #4f6fff; transform: translateY(-2px); }

/* 状态徽章 */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-idle    { background: #2d3347; color: #8890a8; }
.badge-thinking { background: #2d3a52; color: #6ab0ff; }
.badge-working { background: #2d4535; color: #4ecb71; animation: pulse 1.5s infinite; }
.badge-done    { background: #1e3a2d; color: #52c97e; }
.badge-error   { background: #3a1e1e; color: #ff6b6b; }

@keyframes pulse {
    0%,100% { opacity:1; } 50% { opacity:.6; }
}

/* 进度条 */
.progress-wrap {
    background: #1e2130;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, #4f6fff, #7c5cfc);
    transition: width 0.4s ease;
}

/* 日志条目 */
.log-entry {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    padding: 4px 8px;
    border-left: 3px solid #2d3347;
    margin: 2px 0;
    color: #c8cfe8;
}
.log-entry.success { border-left-color: #4ecb71; color: #4ecb71; }
.log-entry.error   { border-left-color: #ff6b6b; color: #ff6b6b; }
.log-entry.info    { border-left-color: #4f6fff; }

/* 任务卡片 */
.task-item {
    background: #1a1f30;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    border-left: 4px solid #2d3347;
    font-size: 13px;
}
.task-done    { border-left-color: #4ecb71; }
.task-running { border-left-color: #ffa94d; }
.task-error   { border-left-color: #ff6b6b; }
.task-pending { border-left-color: #3d4460; }

/* 最终报告区域 */
.report-box {
    background: #141824;
    border: 1px solid #2d3d60;
    border-radius: 12px;
    padding: 20px 24px;
    line-height: 1.8;
}

/* 侧边栏标题 */
.sidebar-section {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #6b7498;
    text-transform: uppercase;
    margin: 16px 0 8px;
}

/* 顶部标题 */
.header-title {
    background: linear-gradient(135deg, #4f6fff 0%, #9c6fff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Session State 初始化
# ──────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "llm_client": None,
        "orchestrator": None,
        "current_run": None,
        "run_history": [],
        "live_logs": [],
        "is_running": False,
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
        "selected_run_idx": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ──────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────
def get_orchestrator() -> Orchestrator:
    if st.session_state.orchestrator is None:
        client = LLMClient()
        client.api_key = st.session_state.api_key
        client.base_url = st.session_state.base_url
        client.model = st.session_state.model_name
        client._client = None
        st.session_state.llm_client = client
        st.session_state.orchestrator = Orchestrator(client)
    return st.session_state.orchestrator


def status_badge(status: str) -> str:
    icons = {
        "idle": "⚪", "thinking": "💭", "working": "⚡",
        "done": "✅", "error": "❌", "waiting": "⏳"
    }
    icon = icons.get(status, "•")
    return f'<span class="badge badge-{status}">{icon} {status.upper()}</span>'


def task_status_icon(status: str) -> str:
    return {"pending": "⬜", "running": "🔄", "done": "✅", "error": "❌", "skipped": "⏭"}.get(status, "•")


# ──────────────────────────────────────────────────────────────────
# 侧边栏：配置 & Agent 总览
# ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-title">🤖 Multi-Agent</div>', unsafe_allow_html=True)
    st.caption("多智能体协同办公平台 · CEO Edition")
    st.divider()

    # API 配置
    st.markdown('<div class="sidebar-section">⚙️ 模型配置</div>', unsafe_allow_html=True)
    api_key = st.text_input("API Key", value=st.session_state.api_key,
                            type="password", placeholder="sk-...")
    base_url = st.text_input("Base URL", value=st.session_state.base_url)
    model_name = st.selectbox("模型", ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo",
                                       "gpt-3.5-turbo", "deepseek-chat", "custom"],
                               index=0)
    if model_name == "custom":
        model_name = st.text_input("自定义模型名称", placeholder="your-model-name")

    if st.button("💾 保存配置", use_container_width=True):
        st.session_state.api_key = api_key
        st.session_state.base_url = base_url
        st.session_state.model_name = model_name
        st.session_state.orchestrator = None  # 强制重建
        st.success("配置已保存！")

    st.divider()

    # CEO 视角：Agent 状态总览
    st.markdown('<div class="sidebar-section">👔 CEO 视角 · Agent 状态</div>', unsafe_allow_html=True)

    orch = get_orchestrator()
    agent_statuses = orch.get_agent_statuses()
    for agent in agent_statuses:
        badge = status_badge(agent["status"])
        st.markdown(
            f'<div class="agent-card">'
            f'<span style="font-size:18px">{agent["emoji"]}</span> '
            f'<strong style="color:#e0e6ff">{agent["name"]}</strong><br>'
            f'<span style="font-size:11px;color:#6b7498">{agent["role"]}</span><br>'
            f'{badge} &nbsp; <span style="font-size:11px;color:#6b7498">执行任务: {agent["task_count"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    if st.button("🔄 重置所有 Agent", use_container_width=True):
        orch.reset_agents()
        st.rerun()

    st.divider()
    # 历史记录
    if st.session_state.run_history:
        st.markdown('<div class="sidebar-section">📜 执行历史</div>', unsafe_allow_html=True)
        for i, run in enumerate(reversed(st.session_state.run_history)):
            icon = "✅" if run.status == "done" else "❌"
            label = f"{icon} {run.user_request[:25]}..." if len(run.user_request) > 25 else f"{icon} {run.user_request}"
            if st.button(label, key=f"hist_{i}", use_container_width=True):
                st.session_state.selected_run_idx = len(st.session_state.run_history) - 1 - i
                st.rerun()


# ──────────────────────────────────────────────────────────────────
# 主区域
# ──────────────────────────────────────────────────────────────────
st.markdown('<h1 class="header-title">🤖 多智能体协同办公平台</h1>', unsafe_allow_html=True)
st.markdown("*让 AI 团队替你完成复杂任务 — 研究、写作、代码、数据分析，一站搞定*")
st.divider()

# Tab 布局
tab_main, tab_ceo, tab_history, tab_help = st.tabs([
    "🚀 任务中心", "👔 CEO 控制台", "📜 执行历史", "❓ 使用指南"
])


# ──────────────────────────────────────────────────────────────────
# Tab1: 任务中心
# ──────────────────────────────────────────────────────────────────
with tab_main:
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("📝 任务输入")
        user_task = st.text_area(
            "描述你的任务",
            height=160,
            placeholder=(
                "示例：\n"
                "• 帮我调研当前 AI 大模型市场格局，并撰写一份竞品分析报告\n"
                "• 分析我们上季度的销售数据，找出增长机会\n"
                "• 开发一个 Python 爬虫，抓取电商平台的商品价格"
            )
        )

        # 快捷任务示例
        st.caption("💡 快捷示例")
        c1, c2, c3 = st.columns(3)
        if c1.button("📊 市场调研报告", use_container_width=True):
            user_task = "调研国内 AI 大模型市场现状，分析主要竞争者的优劣势，撰写一份完整的市场调研报告，包含数据分析和趋势预测"
        if c2.button("💻 代码+文档", use_container_width=True):
            user_task = "编写一个 Python 实现的 TODO List 命令行工具，包含增删改查功能，并输出完整的使用说明文档"
        if c3.button("✍️ 产品方案", use_container_width=True):
            user_task = "设计一个面向中小企业的 SaaS 项目管理工具产品方案，包含功能规划、用户故事和技术选型建议"

        st.divider()

        # Agent 选择（可选手动指定）
        st.caption("🎯 Agent 模式")
        mode = st.radio(
            "执行模式",
            ["🤖 自动调度（推荐）", "🔬 仅研究员", "✍️ 仅写作", "💻 仅代码", "📊 仅数据分析"],
            horizontal=False,
            label_visibility="collapsed"
        )

        # 运行按钮
        run_disabled = st.session_state.is_running or not user_task.strip() or not st.session_state.api_key
        btn_label = "⏳ 执行中..." if st.session_state.is_running else "🚀 启动 AI 团队"

        if not st.session_state.api_key:
            st.warning("⚠️ 请先在左侧配置 API Key")

        run_clicked = st.button(btn_label, disabled=run_disabled,
                                use_container_width=True, type="primary")

    with col_output:
        st.subheader("📡 实时执行日志")
        log_container = st.empty()

        def render_logs():
            if not st.session_state.live_logs:
                log_container.markdown(
                    '<div style="color:#4a5080;font-size:13px;padding:20px">🕐 等待任务启动...</div>',
                    unsafe_allow_html=True
                )
                return
            html = '<div style="max-height:320px;overflow-y:auto">'
            for entry in st.session_state.live_logs[-30:]:
                cls = entry.get("level", "info")
                html += f'<div class="log-entry {cls}">[{entry["time"]}] {entry["message"]}</div>'
            html += '</div>'
            log_container.markdown(html, unsafe_allow_html=True)

        render_logs()

    # ── 执行任务 ──────────────────────────────────────────────────
    if run_clicked:
        st.session_state.is_running = True
        st.session_state.live_logs = []
        st.session_state.current_run = None

        # 根据模式修改任务前缀
        if "仅研究员" in mode:
            user_task = "[研究员] " + user_task
        elif "仅写作" in mode:
            user_task = "[写作] " + user_task
        elif "仅代码" in mode:
            user_task = "[代码] " + user_task
        elif "仅数据分析" in mode:
            user_task = "[数据分析] " + user_task

        orch = get_orchestrator()
        # 更新 client 配置
        orch.llm_client.api_key = st.session_state.api_key
        orch.llm_client.base_url = st.session_state.base_url
        orch.llm_client.model = st.session_state.model_name
        orch.llm_client._client = None

        def on_update(entry):
            st.session_state.live_logs.append(entry)

        with st.spinner("AI 团队正在协作处理中..."):
            try:
                run = orch.run(user_task, on_update=on_update)
                st.session_state.current_run = run
                st.session_state.run_history.append(run)
            except Exception as e:
                st.session_state.live_logs.append({
                    "time": time.strftime("%H:%M:%S"),
                    "level": "error",
                    "message": f"执行异常: {e}"
                })
            finally:
                st.session_state.is_running = False

        st.rerun()

    # ── 展示当前执行结果 ──────────────────────────────────────────
    current = st.session_state.current_run
    if current:
        st.divider()

        # 进度概览
        summary = get_orchestrator().get_run_summary(current)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("执行状态", "✅ 完成" if current.status == "done" else "❌ 错误")
        m2.metric("子任务数", summary["total_tasks"])
        m3.metric("成功任务", summary["done_tasks"])
        m4.metric("耗时", f"{summary['duration']}s")

        # 进度条
        progress = summary["progress"]
        st.markdown(
            f'<div class="progress-wrap"><div class="progress-bar" style="width:{progress}%"></div></div>',
            unsafe_allow_html=True
        )

        # 子任务列表
        st.subheader("📋 子任务执行详情")
        for task in current.tasks:
            icon = task_status_icon(task.status)
            cls = f"task-{task.status}"
            agent = get_orchestrator().agents.get(task.agent_type)
            agent_name = agent.name if agent else task.agent_type
            st.markdown(
                f'<div class="task-item {cls}">'
                f'{icon} <strong>{agent_name}</strong> &nbsp;|&nbsp; {task.description}'
                f'</div>',
                unsafe_allow_html=True
            )

        # 展开查看各 Agent 详细输出
        with st.expander("🔍 查看各 Agent 详细输出", expanded=False):
            for task in current.tasks:
                if task.result and task.result.output:
                    agent = get_orchestrator().agents.get(task.agent_type)
                    agent_name = agent.name if agent else task.agent_type
                    st.markdown(f"#### {agent_name}")
                    st.markdown(task.result.output)
                    st.divider()

        # 最终报告
        st.subheader("📄 最终综合报告")
        st.markdown(
            f'<div class="report-box">{current.final_report.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

        # 下载按钮
        st.download_button(
            "⬇️ 下载报告（Markdown）",
            data=current.final_report,
            file_name=f"report_{current.run_id}.md",
            mime="text/markdown"
        )


# ──────────────────────────────────────────────────────────────────
# Tab2: CEO 控制台
# ──────────────────────────────────────────────────────────────────
with tab_ceo:
    st.subheader("👔 CEO 视角 · 全局控制台")
    st.caption("实时监控所有 Agent 的状态、任务分配和执行结果")

    orch = get_orchestrator()
    agent_statuses = orch.get_agent_statuses()

    # Agent 状态卡片
    st.markdown("#### 🧩 Agent 状态总览")
    cols = st.columns(3)
    for i, agent in enumerate(agent_statuses):
        with cols[i % 3]:
            status = agent["status"]
            badge = status_badge(status)
            task_cnt = agent["task_count"]
            st.markdown(
                f'<div class="agent-card">'
                f'<div style="font-size:32px;text-align:center">{agent["emoji"]}</div>'
                f'<div style="text-align:center;font-weight:700;color:#e0e6ff;margin:6px 0">{agent["name"]}</div>'
                f'<div style="text-align:center;font-size:11px;color:#6b7498">{agent["role"]}</div>'
                f'<div style="text-align:center;margin-top:8px">{badge}</div>'
                f'<div style="text-align:center;font-size:12px;color:#6b7498;margin-top:6px">历史任务: {task_cnt}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # CEO 直接指令
    st.markdown("#### 💬 向 CEO 发出指令")
    ceo_cmd = st.text_input("指令内容", placeholder="例：评估当前任务进度 / 为团队制定下周工作计划")
    if st.button("📤 发送指令给 CEO", type="primary") and ceo_cmd and st.session_state.api_key:
        orch.llm_client.api_key = st.session_state.api_key
        orch.llm_client.base_url = st.session_state.base_url
        orch.llm_client.model = st.session_state.model_name
        orch.llm_client._client = None
        with st.spinner("CEO 正在思考..."):
            result = orch.ceo.execute(ceo_cmd, llm_client=orch.llm_client)
        if result.status == "success":
            st.markdown(
                f'<div class="report-box">👔 <strong>CEO 回复</strong><br><br>{result.output}</div>',
                unsafe_allow_html=True
            )
        else:
            st.error(f"CEO 执行失败: {result.error}")

    st.divider()

    # 工作流历史统计
    if st.session_state.run_history:
        st.markdown("#### 📈 工作流统计")
        total_runs = len(st.session_state.run_history)
        done_runs = sum(1 for r in st.session_state.run_history if r.status == "done")
        avg_time = round(
            sum(r.duration for r in st.session_state.run_history) / total_runs, 1
        ) if total_runs > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("总执行次数", total_runs)
        c2.metric("成功次数", done_runs)
        c3.metric("平均耗时", f"{avg_time}s")


# ──────────────────────────────────────────────────────────────────
# Tab3: 执行历史
# ──────────────────────────────────────────────────────────────────
with tab_history:
    st.subheader("📜 执行历史记录")
    if not st.session_state.run_history:
        st.info("暂无执行记录，快去任务中心执行第一个任务吧！")
    else:
        for idx, run in enumerate(reversed(st.session_state.run_history)):
            status_icon = "✅" if run.status == "done" else "❌"
            with st.expander(
                f"{status_icon} [{run.run_id}] {run.user_request[:60]}  |  耗时: {run.duration}s",
                expanded=False
            ):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.caption("**任务详情**")
                    for task in run.tasks:
                        icon = task_status_icon(task.status)
                        st.write(f"{icon} `{task.agent_type}` {task.description[:50]}")
                with col_b:
                    st.caption("**最终报告摘要**")
                    st.write(run.final_report[:500] + ("..." if len(run.final_report) > 500 else ""))

                st.download_button(
                    "⬇️ 下载完整报告",
                    data=run.final_report,
                    file_name=f"report_{run.run_id}.md",
                    mime="text/markdown",
                    key=f"dl_{run.run_id}"
                )


# ──────────────────────────────────────────────────────────────────
# Tab4: 使用指南
# ──────────────────────────────────────────────────────────────────
with tab_help:
    st.subheader("❓ 使用指南")
    st.markdown("""
### 🚀 快速开始

1. **配置 API Key**：在左侧边栏填入你的 OpenAI API Key（或兼容接口的 Key）
2. **描述任务**：在「任务中心」的输入框中描述你想完成的任务
3. **启动团队**：点击「启动 AI 团队」，多个 Agent 将自动协作执行
4. **查看结果**：实时日志追踪进度，执行完成后查看综合报告

---

### 🤖 Agent 团队介绍

| Agent | 职责 | 擅长场景 |
|-------|------|---------|
| 👔 CEO 总指挥 | 任务规划、分工调度、综合汇总 | 所有场景 |
| 🔍 资深研究员 | 信息调研、背景分析 | 市场调研、竞品分析 |
| ✍️ 资深文案 | 文档撰写、内容创作 | 报告、邮件、方案 |
| 💻 全栈工程师 | 代码实现、技术方案 | 开发任务、算法设计 |
| 📊 数据分析师 | 数据洞察、趋势分析 | 数据报告、决策支持 |
| 📋 文档整理专员 | 文档整合、格式化 | 多源内容整合 |

---

### 💡 任务示例

**自动调度（推荐）**：
- `调研 AI 办公软件市场，分析机会点，给出进入策略建议`
- `设计一个电商平台的推荐算法，输出技术方案和核心代码`
- `整理上季度项目复盘，生成 PPT 大纲和正式报告`

**指定单个 Agent**：
- 切换为「仅代码」模式，输入：`用 Python 实现一个 RSA 加密工具`
- 切换为「仅写作」模式，输入：`写一封向客户道歉的商务邮件`

---

### ⚙️ 兼容的模型接口

支持所有 OpenAI API 格式的模型：
- OpenAI 官方：`gpt-4o-mini`, `gpt-4o`
- DeepSeek：`deepseek-chat`（Base URL 改为 `https://api.deepseek.com/v1`）
- 其他兼容 OpenAI 格式的本地/云端模型
""")
