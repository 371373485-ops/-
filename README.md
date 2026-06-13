# 小红书合规内容诊断与创作优化工具 v3

## 项目简介

本项目是一个面向内容创作者的“小红书合规内容诊断与创作优化工具”，用于在合规边界内辅助用户诊断和优化小红书笔记内容。

用户可以手动输入笔记信息，也可以上传自有、授权或可合法使用的 CSV 样本。系统会基于规则评分、原文证据、样本库统计和多 Agent 工作流，生成内容评分、证据型问题诊断、优先改法、相似案例参考、标题改写、正文重构、标签推荐、封面文案、评论区引导、风险审查和 Markdown 报告。

本项目定位是“合规内容诊断与创作辅助工具”，不是平台自动化工具。系统不接入小红书账号，不爬取平台内容，不调用小红书平台接口，不自动发布，不保证流量、涨粉、收藏、转化或爆款结果。

## 功能清单

- 诊断工作台：输入内容赛道、目标人群、发布目标、标题、正文、标签和封面文案。
- 规则评分：基于可解释规则输出总分、维度评分、问题和建议。
- 证据型诊断：引用或概括原文证据，说明具体问题为什么影响点击、完读、信任、互动或合规，并输出优先级和可执行改法。
- Mock AI 模式：无 API Key 时仍可本地演示诊断流程。
- OpenAI API 模式：配置 API Key 后可调用真实 AI 生成更自然的诊断和改写结果。
- 多 Agent 工作流：按职责拆分诊断、规律分析、案例匹配、标题改写、正文重构、标签封面、风险审查和最终报告。
- 样本库：支持 CSV 上传、列表查看、筛选、详情和删除。
- 爆款规律分析：基于样本库统计高频标题关键词、高频标签、标题结构、开头结构和高表现样本。
- 相似案例匹配：从用户导入的样本库中匹配 Top 3 相似案例，并提示可借鉴点。
- 诊断历史：保存 workflow 诊断输入和输出，支持查看详情、删除和 Markdown 导出。
- 前端页面：诊断工作台、样本库、爆款规律分析、历史记录、关于项目。

## 证据型诊断报告能力

诊断报告不是只返回改写文案，而是围绕用户输入的标题、正文、标签、封面文案和评论引导生成结构化证据报告。

核心输出包括：

- 一句话总评：说明当前内容的整体状态。
- 总分和分项分：覆盖标题、开头、结构、情绪、价值、互动、标签、风格和转化潜力。
- Top 3 核心阻碍：按严重程度和影响范围列出最优先处理的问题。
- 逐条证据型问题：每条包含对应字段、原文片段、问题判断、影响范围、严重程度、修改原则和示例改法。
- 读者视角模拟：模拟目标读者看到标题、开头和正文后的第一反应、可能流失原因和最强兴趣点。
- 内容结构分析：覆盖开头 3 秒、信息层次、信任建立、细节证据、情绪共鸣和行动引导。
- 可信度审查：检查内容是否过泛、是否像广告、缺少哪些信任信号、已有哪类可信表达。
- 需要用户补充的信息：当缺少真实使用周期、适用人群、真实对比体验、限制条件等细节时，系统只提示补充，不编造事实。
- 改写版本与改写理由：标题、正文、标签、封面文案、评论引导都会附带改动说明。
- 风险审查：识别绝对化表达、夸大功效、收益承诺、医疗健康、金融理财、未成年人、站外引流、诱导互动、虚假背书和 AI 内容披露提醒。

系统会尽量引用或概括用户原文证据，避免输出“增强吸引力”“优化表达”这类无证据支撑的泛化建议。

## 合规边界说明

本项目严格遵守以下边界：

- 不实现小红书爬虫。
- 不调用小红书平台接口。
- 不自动登录任何平台账号。
- 不自动发布任何内容。
- 不保证流量、爆款、涨粉、收藏、转化、成交或收益结果。
- 不绕过任何平台访问限制。
- 不批量采集、下载、解析或复制平台内容。
- 不保存用户 Cookie、Token、账号密码或平台会话信息。
- 不把 API Key、Token、Cookie、Secret 写入代码、README、测试文件或日志。
- 不声称 demo 样本是真实平台数据。
- 不建议直接照搬样本，只提供结构、表达和组织方式参考。
- 不生成违法、违规、虚假宣传、夸大承诺或诱导违规引流内容。

系统的数据来源只允许是：

- 用户手动输入的笔记内容。
- 用户上传的自有样本。
- 用户确认已获得授权或可合法使用的样本。
- 系统内置或用户导入的虚构演示样本。

## 技术栈

- Frontend: React + Vite + Tailwind
- Backend: FastAPI
- Database: SQLite
- AI: OpenAI API，支持 mock 模式
- Testing: pytest

## 项目结构

```text
.
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端 API 请求封装
│  │  ├─ components/          # 页面和展示组件
│  │  ├─ styles/              # Tailwind 与全局样式
│  │  ├─ App.jsx              # 前端入口组件
│  │  └─ main.jsx             # React 挂载入口
│  ├─ package.json
│  └─ vite.config.js
│
├─ backend/
│  ├─ app/
│  │  ├─ agents/              # 多 Agent 类
│  │  ├─ api/routes/          # FastAPI 路由
│  │  ├─ models/              # SQLite 初始化和连接
│  │  ├─ prompts/             # OpenAI prompt 模板
│  │  ├─ schemas/             # Pydantic 请求和响应结构
│  │  ├─ services/            # 业务服务、评分、AI 客户端、工作流
│  │  └─ main.py              # FastAPI 应用入口
│  ├─ tests/                  # pytest 测试
│  ├─ requirements.txt
│  └─ pytest.ini
│
├─ .env.example
├─ .gitignore
├─ AGENTS.md
└─ README.md
```

## 后端启动方式

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

默认后端地址：

```text
http://localhost:8000
```

## 前端启动方式

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:5173
```

如需构建前端：

```bash
cd frontend
npm run build
```

## 环境变量说明

可以复制 `.env.example` 作为本地环境变量模板：

```bash
copy .env.example .env
```

主要环境变量：

```text
USE_MOCK_AI=true
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=30
SAMPLE_DB_PATH=backend/data/samples.sqlite3
VITE_API_BASE_URL=http://localhost:8000
```

说明：

- `USE_MOCK_AI`：是否启用 mock AI 模式。默认建议为 `true`。
- `OPENAI_API_KEY`：真实 OpenAI API Key。不要提交到代码仓库，不要写入 README、测试或日志。
- `OPENAI_MODEL`：真实 AI 模式使用的模型名称。
- `OPENAI_TIMEOUT_SECONDS`：OpenAI API 请求超时时间。
- `SAMPLE_DB_PATH`：SQLite 数据库路径。
- `VITE_API_BASE_URL`：前端请求后端的基础地址。

## Mock AI 模式说明

Mock AI 模式用于本地演示、开发和测试。

启用方式：

```text
USE_MOCK_AI=true
```

行为：

- 不调用真实 OpenAI API。
- 不需要 `OPENAI_API_KEY`。
- 使用本地规则评分和 mock 文案生成诊断结果。
- 前端和后端流程都可以完整演示。

如果未配置 `OPENAI_API_KEY`，系统也会自动降级到 mock 或规则逻辑，避免本地演示中断。

mock 模式接口示例：

```bash
curl -X POST http://localhost:8000/api/diagnose/mock ^
  -H "Content-Type: application/json" ^
  -d "{\"category\":\"护肤\",\"target_audience\":\"护肤新手\",\"goal\":\"收藏\",\"title\":\"新手护肤避坑清单\",\"content\":\"第一，我会先看成分和肤质是否匹配。第二，我会记录真实体验。\",\"tags\":[\"护肤\",\"新手\"],\"cover_text\":\"新手护肤先看\",\"comment_guide\":\"你最困惑哪一步？欢迎评论区聊聊。\"}"
```

PowerShell 也可以使用：

```powershell
$body = @{
  category = "护肤"
  target_audience = "护肤新手"
  goal = "收藏"
  title = "新手护肤避坑清单"
  content = "第一，我会先看成分和肤质是否匹配。第二，我会记录真实体验。"
  tags = @("护肤", "新手")
  cover_text = "新手护肤先看"
  comment_guide = "你最困惑哪一步？欢迎评论区聊聊。"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/diagnose/mock" -ContentType "application/json" -Body $body
```

## 真实 OpenAI API 模式说明

如需启用真实 AI 输出，请在本地 `.env` 中配置：

```text
USE_MOCK_AI=false
OPENAI_API_KEY=你的本地私有密钥
OPENAI_MODEL=gpt-4.1-mini
```

注意：

- 不要把真实 API Key 写入代码、README、测试文件或日志。
- OpenAI API 调用失败时，后端会自动降级为本地规则诊断，并在响应 `mode`/`summary` 中说明 fallback 原因，不应导致服务崩溃。
- 当前系统仍会保留规则评分结果作为结构基础，AI 主要用于生成更自然的诊断、标题、正文、标签封面和风险提醒。
- 当前版本的多 Agent workflow 中，真实 AI 主要增强内容诊断生成；后续标题、正文、标签封面、风险审查等 Agent 仍保留本地规则/模板逻辑，以保证无 Key 或调用失败时仍可稳定演示。

真实 AI 相关响应模式：

- `ai`：已调用真实 OpenAI API，并成功合并 AI 输出。
- `ai_mock`：启用了 mock 模式或未配置 `OPENAI_API_KEY`，未调用真实 OpenAI API。
- `ai_fallback`：已尝试调用真实 OpenAI API，但请求失败或返回结构不符合预期，已自动降级为本地规则诊断。

## CSV 样本格式

样本库只支持用户手动上传 CSV，不支持爬虫或平台自动采集。

CSV 必须包含以下字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 是 | 样本标题 |
| `content` | 是 | 样本正文 |
| `tags` | 是 | 标签，多个标签用逗号分隔 |
| `category` | 是 | 内容赛道 |
| `likes` | 是 | 点赞数，非负整数 |
| `collects` | 是 | 收藏数，非负整数 |
| `comments` | 是 | 评论数，非负整数 |
| `cover_text` | 是 | 封面文案 |
| `publish_time` | 否 | 发布时间 |
| `source_note` | 是 | 来源说明 |
| `source_type` | 是 | 来源类型 |

`source_type` 可选值：

- `demo_generated`：虚构演示样本，不代表真实平台数据。
- `own_account_manual`：用户自有账号手动整理。
- `authorized_manual`：已授权样本手动整理。
- `third_party_export`：第三方合法导出。
- `public_dataset`：公开数据集。
- `structure_observation`：结构观察样本。

示例：

```csv
title,content,tags,category,likes,collects,comments,cover_text,publish_time,source_note,source_type
新手护肤避坑清单,第一步先看肤质,"护肤,新手,避坑",护肤,120,80,12,新手先看,2026-01-01,系统生成的虚构演示样本,demo_generated
```

导入限制：

- CSV 文件需使用 UTF-8 编码。
- CSV 文件大小当前限制为 1000KB。
- 单次最多导入 1000 行。
- `source_type` 缺失或非法会拒绝导入。
- `likes`、`collects`、`comments` 必须是非负整数。

## 主要接口说明

### 健康检查

```text
GET /health
```

### 诊断接口

```text
POST /api/diagnose/mock
POST /api/diagnose/rule
POST /api/diagnose/ai
GET /api/diagnose/ai/status
POST /api/diagnose/workflow
```

请求字段：

- `category`：内容赛道。
- `target_audience`：目标人群。
- `goal`：发布目标，可选值为 `涨粉`、`收藏`、`引流`、`转化`、`种草`。
- `title`：原始标题。
- `content`：原始正文。
- `tags`：原始标签数组。
- `cover_text`：封面文案，可选。
- `comment_guide`：用户已有评论区引导，可选；后端会纳入证据型诊断的行动引导分析。

请求示例：

```json
{
  "category": "AI工具",
  "target_audience": "职场办公人群",
  "goal": "收藏",
  "title": "一个好用的AI工具",
  "content": "这个工具挺好用，可以提高效率，大家可以试试。",
  "tags": ["AI", "工具"],
  "cover_text": "好用工具",
  "comment_guide": "你最想解决哪个办公场景？欢迎评论区聊聊。"
}
```

诊断响应包含：

- 爆款潜力总分。
- 各维度评分。
- `top_3_blockers`：Top 3 核心阻碍，包含字段、证据、严重程度、阻碍原因和建议重点。
- `evidence_based_issues`：证据型问题列表，每项包含 `field`、`original_excerpt`、`issue`、`why_it_matters`、`impact_area`、`severity`、`rewrite_principle`、`example_fix`。
- `reader_reaction_simulation`：读者视角模拟，包含标题第一印象、前三行反应、可能流失原因、最强兴趣点和需要前置的信息。
- `structure_analysis`：内容结构分析，覆盖开头钩子、信息层次、信任建立、细节证据、情绪共鸣和行动引导。
- `credibility_review`：可信度审查，判断是否过泛、是否像广告、缺少和已有的信任信号。
- `missing_user_inputs`：需要用户补充的真实信息。系统不得自行编造真实经历、数据、效果或案例。
- `rewritten_versions`：改写版本，包含标题、正文、标签、封面文案和评论引导。
- `rewrite_explanations`：改写理由，说明每个标题、正文、标签、封面文案、评论引导为什么这样改。
- 主要问题。
- 修改建议。
- 优化标题。
- 优化正文。
- 推荐标签。
- 封面文案建议。
- 评论区引导。
- 风险提醒。
- 证据型风险审查 `risk_review`：包含 `risk_level`、`risk_items`、`safe_alternatives`、`human_review_required`、兼容旧字段的 `risks` 和 `suggestions`。其中 `risk_items` 会标明触发字段、触发文本、风险类型、原因、严重程度和保守改法。
- AI 参与披露提醒 `ai_disclosure_notice`。
- 相似案例。

响应示例（节选）：

```json
{
  "diagnosis_id": "2f0f2e2d-0000-0000-0000-example",
  "overall_score": 63,
  "category": "AI工具",
  "summary": "当前内容有基础主题，但标题、可信细节和结构证据不足。",
  "scores": [
    {
      "key": "title_score",
      "name": "标题吸引力",
      "score": 57,
      "reason": "标题缺少数字、痛点或明确结果。"
    }
  ],
  "top_3_blockers": [
    {
      "rank": 1,
      "field": "title",
      "issue": "标题过于空泛，没有明确目标读者、具体场景或可获得的信息。",
      "evidence": "一个好用的AI工具",
      "severity": "high",
      "why_it_blocks": "读者难以判断这篇内容是否和自己有关。",
      "suggested_focus": "补充目标人群、场景和具体信息抓手。"
    }
  ],
  "evidence_based_issues": [
    {
      "field": "body.trust_details",
      "original_excerpt": "这个工具挺好用，可以提高效率，大家可以试试。",
      "issue": "可信细节不足，缺少使用时间、真实场景、对比过程、限制条件或体验细节。",
      "why_it_matters": "只有结论但缺少过程证据，会让读者怀疑这是泛经验或广告话术。",
      "impact_area": "trust",
      "severity": "high",
      "rewrite_principle": "只补充用户真实经历和可公开细节；不能由系统编造。",
      "example_fix": "请补充真实使用周期、适用人群和真实对比体验。"
    }
  ],
  "missing_user_inputs": [
    {
      "field": "真实使用周期",
      "reason": "原文没有提供真实使用周期，系统不能替用户编造。",
      "suggested_prompt": "请补充真实使用或观察的时间范围。"
    }
  ],
  "risk_review": {
    "risk_level": "low",
    "human_review_required": false,
    "risk_items": [
      {
        "field": "ai_disclosure_notice",
        "triggered_text": "AI 辅助生成内容未明确披露",
        "risk_type": "AI 生成内容披露提醒",
        "reason": "诊断和改写可能由 AI 辅助生成，发布前应由用户人工复核。",
        "severity": "low",
        "suggested_rewrite": "如平台或场景要求披露，可补充“本文经 AI 辅助整理，已人工核对”。"
      }
    ],
    "safe_alternatives": []
  },
  "ai_disclosure_notice": "当前为规则诊断结果，未调用小红书平台接口；AI 或规则输出仅供参考，发布前请人工复核。"
}
```

`GET /api/diagnose/ai/status` 用于检查当前 AI 配置状态，只返回是否启用 mock、是否已配置 OpenAI Key、模型名、是否具备真实 AI 调用条件和 fallback 说明，不返回任何 API Key 或敏感信息。

### 样本库接口

```text
POST /api/samples/import
GET /api/samples
GET /api/samples?category=护肤
GET /api/samples?source_type=demo_generated
GET /api/samples/{sample_id}
DELETE /api/samples/{sample_id}
```

### 爆款规律分析接口

```text
GET /api/patterns/analyze
GET /api/patterns/analyze?category=护肤
```

返回内容包括高频标题关键词、高频标签、标题长度分布、平均点赞数、平均收藏数、平均评论数、收藏率、评论率、高表现样本 Top 10、常见标题结构、常见开头结构和赛道风格总结。

## 风险审查说明

`RiskReviewAgent` 会对用户输入和系统改写结果进行保守审查。当前覆盖：

- 绝对化表达：如“绝对”“百分百”“任何人”“全网最好”。
- 夸大功效：如“立刻见效”“包治”“根治”“一招解决”。
- 收益承诺：如“稳赚”“保证变现”“必涨粉”“7天涨粉10万”。
- 医疗健康风险：涉及治疗、诊断、处方、替代医生等表达。
- 金融理财风险：涉及保本、无风险、荐股、确定收益等表达。
- 未成年人相关风险：涉及未成年人消费、身体焦虑或不适当建议。
- 站外引流：如“加微信”“私信领”“扫码”“进群”。
- 诱导互动：如“点赞抽奖”“关注后领取”“不点赞就...”。
- 虚假背书：如“官方认证”“医生推荐”“销量第一”“万人验证”。
- AI 生成内容披露提醒：提示 AI 辅助输出需要人工复核，必要时按平台或场景要求披露。

高风险内容处理策略：

- `risk_level` 会升为 `high`。
- `human_review_required` 会设为 `true`。
- 系统不会继续生成营销化标题。
- 正文会切换为保守替代表达和人工复核建议。
- 不得替用户编造资质、效果、数据、身份背书或案例。

## AI 参与内容披露提醒

系统支持规则、mock 和真实 OpenAI API 三类生成路径。无论使用哪种路径，诊断和改写结果都仅供内容优化参考，发布前需要用户人工复核。

当输出用于公开发布时，应根据平台规则、内容场景和用户自身合规要求判断是否需要披露 AI 辅助参与。系统默认在响应中返回 `ai_disclosure_notice`，并在 `risk_review.risk_items` 中保留 AI 生成内容披露提醒。

### 相似案例匹配接口

```text
POST /api/cases/match
```

匹配逻辑：

- 优先匹配相同 `category`。
- 再匹配标题关键词。
- 再匹配标签。
- 再匹配正文关键词。
- 最后结合 `likes`、`collects`、`comments` 计算样本表现分。

结果仅供结构参考，不建议照搬。

### 历史记录与报告导出接口

```text
GET /api/history
GET /api/history/{history_id}
GET /api/history/{history_id}/export
DELETE /api/history/{history_id}
```

`/api/history/{history_id}/export` 会返回 Markdown 格式报告，包含原始标题、正文摘要、总分、维度评分、证据型诊断、优先改法、问题诊断、修改建议、优化标题、优化正文、推荐标签、封面文案、评论区引导、风险审查、相似案例和生成时间。

## 多 Agent 工作流说明

前端诊断工作台默认调用：

```text
POST /api/diagnose/workflow
```

工作流由 `backend/app/services/workflow.py` 编排，不引入复杂 Agent 框架。当前包含以下 Agent：

- `ContentDiagnosisAgent`：调用规则评分或 AI，输出各维度评分、问题和建议。
- `ViralPatternAgent`：读取样本规律分析结果，提供爆款规律参考。
- `SimilarCaseAgent`：从样本库匹配相似案例，输出可借鉴点和禁止照搬提醒。
- `TitleRewriteAgent`：生成强钩子版、干货收藏版、反差冲突版、新手友好版、职场人版标题。
- `BodyRewriteAgent`：重构正文，保持用户原意，不编造用户未提供的事实。
- `TagAndCoverAgent`：推荐标签、封面文案、评论区第一条和发布时间建议。
- `RiskReviewAgent`：检查夸大承诺、虚假宣传、违规引流、侵权照搬和过度营销风险。
- `FinalReportAgent`：汇总各 Agent 输出，形成最终诊断报告。

工作流容错策略：

- 任一 Agent 失败时，workflow 不应整体崩溃。
- 失败信息会写入诊断问题列表。
- 系统会尽量返回其它 Agent 的可用结果。

## 测试命令

后端测试：

```bash
cd backend
pytest
```

如果 `pytest` 不在 PATH 中：

```bash
cd backend
python -m pytest
```

前端构建检查：

```bash
cd frontend
npm run build
```

前端 smoke test：

```bash
cd frontend
npm test
```

推荐提交前至少执行：

```bash
cd backend
python -m pytest
cd ../frontend
npm test
npm run build
```

## 临时分享演示版

临时分享演示版适合把本机运行的前端和后端通过 Cloudflare Tunnel 或 ngrok 暂时暴露成公网链接，发给少量可信用户试用。它不是正式部署方案，不提供账号权限、访问鉴权或数据隔离。

### 本地启动

后端示例，假设使用 `8001` 端口：

```powershell
cd D:\codex\测试1\backend
$env:FRONTEND_ORIGINS="https://你的前端临时域名"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

前端示例，必须把 `VITE_API_BASE_URL` 指向后端临时公网地址：

```powershell
cd D:\codex\测试1\frontend
$env:VITE_API_BASE_URL="https://你的后端临时域名"
npm run dev
```

Mac/Linux：

```bash
cd /path/to/project/backend
export FRONTEND_ORIGINS="https://你的前端临时域名"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

```bash
cd /path/to/project/frontend
export VITE_API_BASE_URL="https://你的后端临时域名"
npm run dev
```

### Cloudflare Tunnel

建议开两个 tunnel：一个给后端，一个给前端。

后端：

```bash
cloudflared tunnel --url http://127.0.0.1:8001
```

记录输出的后端公网地址，例如：

```text
https://backend-demo.trycloudflare.com
```

前端：

```bash
cloudflared tunnel --url http://127.0.0.1:5173
```

记录输出的前端公网地址，例如：

```text
https://frontend-demo.trycloudflare.com
```

然后重启后端时设置：

```powershell
$env:FRONTEND_ORIGINS="https://frontend-demo.trycloudflare.com"
```

重启前端时设置：

```powershell
$env:VITE_API_BASE_URL="https://backend-demo.trycloudflare.com"
```

最终只把前端公网地址发给试用者。

### ngrok

ngrok 同样建议开两个 tunnel：

```bash
ngrok http 8001
```

记录后端公网地址。

```bash
ngrok http 5173
```

记录前端公网地址。

然后和 Cloudflare Tunnel 一样：

- `FRONTEND_ORIGINS` 填前端公网地址。
- `VITE_API_BASE_URL` 填后端公网地址。

### 环境变量说明

- `VITE_API_BASE_URL`：前端调用后端的基础地址。本地默认是 `http://127.0.0.1:8000`，临时分享时必须改为后端公网地址。
- `FRONTEND_ORIGINS`：后端允许访问的前端来源，多个地址用英文逗号分隔。
- `CORS_ORIGINS`：可覆盖默认 CORS 来源。
- `CORS_ORIGIN_REGEX`：可用正则临时放行一类域名，例如 Cloudflare Tunnel 域名。

API Key 仍然只保存在本地后端 `.env` 或本机环境变量中，不能放入前端、README、测试文件、截图或分享链接。前端只知道后端 API 地址，不应该知道任何模型密钥。

### 安全注意事项

- 临时公网链接拿到的人都可以访问，不要公开发布。
- AI 模式会消耗你的模型额度。
- 不要上传真实隐私数据、敏感样本或未授权内容。
- 演示期间请关注终端日志和模型用量。
- 分享结束后，在运行 tunnel、前端和后端的终端中按 `Ctrl+C` 关闭访问。

## 常见问题

### 1. 没有 OpenAI API Key 可以运行吗？

可以。默认 `USE_MOCK_AI=true`，系统不会调用真实 OpenAI API，可以完整演示前端页面、规则评分、样本库、规律分析、案例匹配和历史导出。

### 2. 这个项目会抓取小红书内容吗？

不会。本项目不提供爬虫、自动登录、自动发布、平台接口调用或批量采集功能。样本只能由用户手动上传，且必须是自有、授权或可合法使用的数据。

### 3. Demo 样本是真实平台数据吗？

不是。`demo_generated` 表示虚构演示样本，不代表真实平台数据。

### 4. 为什么相似案例提示“不建议照搬”？

样本匹配只用于参考结构、选题角度和表达组织方式。直接复制他人内容可能产生侵权、重复内容或合规风险。

### 5. 诊断结果能保证爆款吗？

不能。系统只提供规则评分、样本统计和改写建议，不能保证流量、涨粉、收藏、转化或商业结果。

### 6. 历史记录保存在哪里？

当前默认保存在本地 SQLite 数据库中，路径为：

```text
backend/data/samples.sqlite3
```

也可以通过 `SAMPLE_DB_PATH` 修改。

## 后续规划

- 增强前端复制成功/失败提示。
- 增加更细的风险审查规则和测试样例。
- 为历史记录增加更明确的数据留存和清空能力。
- 支持更多样本统计维度和轻量图表展示。
- 增加前端基础自动化测试。
- 后续如需多人部署，可引入用户权限、数据隔离和 PostgreSQL。
