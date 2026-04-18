# 多智能体协同办公平台

> 基于大语言模型的 CEO 视角多 Agent 协作系统，三天内团队从零构建。

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境（可选）
```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

### 3. 启动平台
```bash
streamlit run app.py
```
然后打开浏览器访问 `http://localhost:8501`

---

## 🏗️ 项目架构

```
multi-agent-office/
├── app.py                   # Streamlit 前端主入口
├── requirements.txt
├── .env.example
└── agents/
    ├── __init__.py
    ├── base_agent.py        # Agent 基类 & 数据结构
    ├── llm_client.py        # LLM 调用封装
    ├── specialized_agents.py # 各专业 Agent 实现
    └── orchestrator.py      # CEO 视角调度引擎
```

## 🤖 Agent 团队

| Agent | 职责 |
|-------|------|
| 👔 CEO 总指挥 | 任务拆解、协调调度、综合报告 |
| 🔍 资深研究员 | 信息调研、行业分析 |
| ✍️ 资深文案 | 文案撰写、内容创作 |
| 💻 全栈工程师 | 代码实现、技术方案 |
| 📊 数据分析师 | 数据洞察、趋势分析 |
| 📋 文档整理专员 | 文档整合、格式化输出 |

## 🔧 支持的模型

- **OpenAI**: gpt-4o-mini, gpt-4o
- **DeepSeek**: deepseek-chat（修改 Base URL 为 `https://api.deepseek.com/v1`）
- 其他兼容 OpenAI API 格式的模型
