# 🐾 PetCare AI

基于 **RAG（检索增强生成）** 的宠物智能知识库问答系统。

上传宠物知识文档（PDF / TXT），系统自动完成解析 → 切片 → 向量化入库；提问时通过向量相似度检索召回相关内容，交由 DeepSeek 大模型生成回答，并展示答案的引用来源。支持多轮连续对话。

> 个人项目：全栈开发 + AI 应用开发求职演示。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 · TypeScript · Vite · Tailwind CSS 4 |
| 后端 | Python 3.12 · FastAPI · LangChain |
| AI | DeepSeek（对话生成，流式输出）· SiliconFlow BAAI/bge-m3（Embedding） |
| 向量数据库 | Chroma（本地持久化，无需 Docker） |
| 文档处理 | pypdf · 原生 TXT 解析（UTF-8/GBK 自动识别） |

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js **≥ 20.19**（Vite 7 / Tailwind 4 要求，终端执行 `node -v` 验证）
- 两个 API Key：
  - DeepSeek：https://platform.deepseek.com （用于问答生成）
  - SiliconFlow：https://siliconflow.cn （用于 Embedding，有免费额度）

### 2. 后端启动

```powershell
cd backend
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
Copy-Item .env.example .env   # 用记事本打开 .env，填入两个 API Key
python -m uvicorn app.main:app --reload --port 8000
```

验证：浏览器打开 http://localhost:8000/api/health

### 3. 前端启动

```powershell
cd frontend
npm install                  # 若下载慢：npm config set registry https://registry.npmmirror.com
npm run dev
```

浏览器打开 http://localhost:5173 （前端通过 Vite 代理访问后端 /api）

## 开发进度

- [x] 阶段 1：项目初始化和目录搭建
- [x] 阶段 2：文档上传、解析、切片和向量存储
- [x] 阶段 3：RAG 检索功能
- [ ] 阶段 4：大模型问答和引用来源（进行中）
- [ ] 阶段 5：前端聊天界面
- [ ] 阶段 6：测试、异常处理和项目完善

## 目录结构 / 架构说明

（阶段 6 完善）
