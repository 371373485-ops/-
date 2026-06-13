# 临时在线 Demo 部署说明

本项目推荐用 Render 部署 FastAPI 后端，用 Vercel 部署 React 前端。当前配置适合临时演示，不建议直接作为长期生产环境。

## 1. 部署后端到 Render

1. 将项目推送到你自己的 GitHub 仓库。
2. 打开 Render，选择 New -> Blueprint，连接该仓库。
3. Render 会读取仓库根目录的 `render.yaml`。
4. 首次部署完成后，记录后端地址，例如：

```text
https://xhs-agent-v3-backend.onrender.com
```

默认后端环境变量：

```text
USE_MOCK_AI=true
SAMPLE_DB_PATH=/tmp/xhs-agent-v3.sqlite3
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=30
```

如果要使用真实 OpenAI API，在 Render 后台添加：

```text
USE_MOCK_AI=false
OPENAI_API_KEY=你的私有密钥
```

不要把真实 API Key 写入代码、README、测试文件或日志。

## 2. 部署前端到 Vercel

1. 打开 Vercel，导入同一个 GitHub 仓库。
2. Root Directory 选择：

```text
frontend
```

3. 添加环境变量：

```text
VITE_API_BASE_URL=https://你的-render-后端地址
```

4. 部署完成后，记录前端地址，例如：

```text
https://xhs-agent-v3-demo.vercel.app
```

## 3. 回填后端 CORS

拿到 Vercel 前端地址后，到 Render 后端服务环境变量中设置：

```text
CORS_ORIGINS=https://你的-vercel-前端地址
```

如果同时允许本地调试，可以用逗号分隔：

```text
CORS_ORIGINS=https://你的-vercel-前端地址,http://localhost:5173,http://127.0.0.1:5173
```

保存后重新部署后端。

## 4. 验证

后端健康检查：

```text
https://你的-render-后端地址/health
```

前端打开：

```text
https://你的-vercel-前端地址
```

建议演示流程：

1. 打开诊断工作台，使用工作流模式诊断一篇笔记。
2. 上传根目录的 `demo_samples.csv`。
3. 查看样本库、爆款规律分析、相似案例。
4. 查看历史记录并导出 Markdown 报告。

## 5. 临时 Demo 注意事项

- 不提供爬虫、自动登录、自动发布或平台接口调用。
- 不要上传真实 Cookie、Token、账号密码或敏感样本。
- Render 免费实例和 `/tmp` SQLite 数据可能重启后丢失，只适合临时演示。
- 如果要长期多人使用，建议改用 PostgreSQL、用户权限、数据隔离和明确的数据删除机制。
