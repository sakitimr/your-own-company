# 你自己的公司 · 多智能体协同办公平台

> 基于大语言模型的 CEO 视角多 Agent 协作系统。

🌐 **在线体验**：[https://your-own-company.streamlit.app](https://your-own-company.streamlit.app)（需配置 API Key）

📦 **GitHub**：[https://github.com/sakitimr/your-own-company](https://github.com/sakitimr/your-own-company)

---

## ✨ 功能亮点

- **CEO 视角调度**：智能任务拆解，自动分配给最合适的 Agent
- **6 大专业 Agent**：研究员、文案、工程师、数据分析师、文档专员
- **实时协作**：多 Agent 按序执行，前序结果作为后序上下文
- **暗色 UI**：专业级 Streamlit 界面，支持实时日志、历史记录

---

## 🚀 快速启动

### 方式一：在线体验（推荐）
直接访问 [Streamlit Cloud 部署地址](https://your-own-company.streamlit.app)，填入你的 API Key 即可使用。

### 方式二：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/sakitimr/your-own-company.git
cd your-own-company

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（可选，也可在 UI 中配置）
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY

# 4. 启动平台
streamlit run app.py
```
然后打开浏览器访问 `http://localhost:8501`

---

## 🏗️ 项目架构

```
your-own-company/
├── app.py                   # Streamlit 前端主入口
├── requirements.txt
├── .env.example
├── .streamlit/config.toml   # Streamlit 主题配置
└── agents/
    ├── __init__.py
    ├── base_agent.py        # Agent 基类 & 数据结构
    ├── llm_client.py        # LLM 调用封装（兼容本地/云端）
    ├── specialized_agents.py # 6 个专业 Agent 实现
    └── orchestrator.py      # CEO 视角调度引擎
```

---

## 🤖 Agent 团队

| Agent | Emoji | 职责 | 擅长场景 |
|-------|-------|------|---------|
| CEO 总指挥 | 👔 | 任务拆解、协调调度、综合报告 | 所有场景 |
| 资深研究员 | 🔍 | 信息调研、背景分析、洞察提炼 | 市场调研、竞品分析 |
| 资深文案 | ✍️ | 文档撰写、内容创作 | 报告、邮件、方案 |
| 全栈工程师 | 💻 | 代码实现、技术方案 | 开发任务、算法设计 |
| 数据分析师 | 📊 | 数据洞察、趋势分析 | 数据报告、决策支持 |
| 文档整理专员 | 📋 | 文档整合、格式化输出 | 多源内容整合 |

---

## 🔧 支持的模型

- **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **DeepSeek**: `deepseek-chat`（Base URL: `https://api.deepseek.com/v1`）
- 其他兼容 OpenAI API 格式的本地/云端模型

---

## 🌐 Streamlit Cloud 部署指南

### 1. Fork 仓库
点击右上角 **Fork** 按钮，将仓库复制到你的 GitHub 账号下。

### 2. 登录 Streamlit Cloud
访问 [https://share.streamlit.io](https://share.streamlit.io)，用 GitHub 账号登录。

### 3. 创建新应用
- 点击 **New app**
- Repository: 选择 `your-username/your-own-company`
- Branch: `main`
- Main file path: `app.py`

### 4. 配置 Secrets（关键！）
在 **Advanced settings → Secrets** 中添加：

```toml
OPENAI_API_KEY = "your-api-key-here"
OPENAI_BASE_URL = "https://api.openai.com/v1"
MODEL_NAME = "gpt-4o-mini"
```

> 如果使用 DeepSeek，修改 `OPENAI_BASE_URL` 为 `https://api.deepseek.com/v1`

### 5. 部署
点击 **Deploy**，等待几分钟即可获得你的专属在线地址！

---

## 📝 使用示例

### 自动调度模式（推荐）
输入任务描述，CEO 会自动拆解并分配给最合适的 Agent：

> "调研国内 AI 大模型市场现状，分析主要竞争者的优劣势，撰写一份完整的市场调研报告"

### 指定单个 Agent
切换为特定模式，直接指定 Agent 类型：

- **仅代码模式**："用 Python 实现一个 RSA 加密工具，包含密钥生成、加密、解密功能"
- **仅写作模式**："写一封向客户道歉的商务邮件，语气诚恳专业"

---

## 📄 License

MIT License - 自由使用、修改和分发
