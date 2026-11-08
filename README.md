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
- [x] 阶段 4：大模型问答和引用来源
- [x] 阶段 5：前端聊天界面
- [x] 阶段 6：测试、异常处理和项目完善

## 系统架构

```
┌──────────────┐   上传 PDF/TXT      ┌──────────────────────────────────────┐
│  浏览器       │ ─────────────────▶ │  FastAPI 后端                        │
│  React 19    │                    │  ① 解析（pypdf 逐页 / TXT 编码兜底）   │
│  Vite + TW   │ ◀───────────────── │  ② 切片（600 字 / 重叠 120 / 中文标点）│
│              │   SSE 流式问答      │  ③ 向量化（bge-m3，1024 维）          │
│  聊天界面     │                    │  ④ 写入 Chroma（本地持久化）           │
│  引用定位     │                    │                                      │
└──────────────┘                    │  提问链路：                            │
                                    │  向量检索 Top-K（阈值 0.45 过滤）      │
                                    │  → RAG Prompt（参考资料 + 规则约束）   │
                                    │  → DeepSeek 流式生成 → SSE 推送        │
                                    │  → sources 事件（文件名/页码/相似度）   │
                                    └──────────────┬───────────────────────┘
                                                   │
                     ┌─────────────────────────────┼──────────────────────────┐
                     │                             │                          │
           ┌─────────▼─────────┐         ┌─────────▼──────────┐    ┌─────────▼─────────┐
           │ SiliconFlow       │         │ Chroma             │    │ DeepSeek          │
           │ BAAI/bge-m3       │         │ 余弦相似度          │    │ 流式生成          │
           │（Embedding）      │         │ 本地持久化          │    │（LLM，模型名可配） │
           └───────────────────┘         └────────────────────┘    └───────────────────┘
```

会话存储：后端内存 dict（多轮对话 + 历史裁剪 8 条），演示场景足够，生产可平滑替换为 Redis / 数据库（接口不变）。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 装配 + CORS + 全局异常处理
│   │   ├── core/config.py        # 全部配置项（.env，pydantic-settings）
│   │   ├── models/schemas.py     # 请求/响应 Pydantic 模型
│   │   ├── services/             # document（入库）/ retrieval（检索）
│   │   │                         # chat（SSE 问答）/ session（会话）
│   │   ├── routers/              # documents / search / chat / sessions
│   │   ├── prompts/rag_prompt.py # RAG 系统提示词 + 编号格式化
│   │   └── utils/text_utils.py   # 编码兜底 + 关键词窗口摘要
│   ├── scripts/                  # 一键验证脚本（upload/retrieval/chat/smoke）
│   ├── tests/test_services.py    # 纯逻辑单元测试（pytest，可选）
│   └── data/                     # 运行时生成：uploads/ chroma/ documents.json
│                                 # sample/ 内含中文样例文档
└── frontend/
    └── src/
        ├── App.tsx               # 状态中枢（会话/消息流/文档管理）
        ├── api/                  # REST 封装 + SSE 流式客户端
        ├── components/           # 聊天界面 8 个组件（引用定位等）
        └── types.ts              # 与后端 JSON 字段一一对应的 TS 类型
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/health | 健康检查 + 两个 API Key 配置状态 |
| POST | /api/documents/upload | 上传 PDF/TXT（≤20MB）→ 解析切片向量化，返回 chunk_count |
| GET | /api/documents | 文档列表 |
| DELETE | /api/documents/{doc_id} | 删除文档及其向量 |
| POST | /api/search | 检索 {query, top_k} → 相关片段 + 相似度（不调用 LLM） |
| POST | /api/sessions | 新建会话 |
| GET | /api/sessions/{sid} | 会话历史（含引用来源，前端刷新/切换恢复） |
| DELETE | /api/sessions/{sid} | 删除会话 |
| POST | /api/chat | **SSE 流式问答** {session_id, question} |

SSE 事件顺序：`token`（增量文本，多个）→ `sources`（引用来源数组）→ `done`；流中出错发 `error`。

## 测试

后端保持运行，在 backend/ 目录执行：

```powershell
python scripts\smoke_test.py   # 一键端到端冒烟测试：上传→检索→流式问答→引用持久化→清理
```

可选单元测试（纯逻辑，不需要后端运行）：

```powershell
python -m pip install pytest
python -m pytest tests -v
```

## 面试演示话术（5 分钟）

1. **一分钟讲架构**：前后端分离；FastAPI + LangChain 搭建 RAG 管线；Chroma 本地向量库；DeepSeek 生成。数据流：上传 → 中文标点感知切片 → bge-m3 向量化 → 余弦检索（阈值过滤）→ 规则化 Prompt → 流式生成 + 引用溯源。
2. **两分钟现场演示**：上传 PDF → 问"幼猫可以喝牛奶吗？"→ 流式回答 + 点击 `[1]` 定位引用来源（文件名/页码/相似度/片段）→ 追问"那疫苗呢？"（多轮上下文）→ 问知识库外的问题（诚实回答"没有找到"，不编造）→ 删除文档后再问（回答随知识库实时变化）。
3. **一分钟讲工程细节**：自定义 SSE 事件协议（token→sources→done）；引用编号与检索顺序强一致（零文本匹配）；引用随会话持久化、历史切换可恢复；上传原子性 + 索引并发锁；关键词窗口摘要（引用卡片展示真正相关的段落）。
4. **一分钟讲取舍**：会话内存存储（演示够用，可换 Redis）；检索阈值 0.45 平衡召回与误召；collection 名绑定 embedding 模型避免维度冲突；全部密钥走环境变量。

## 演示前检查清单

- [ ] `backend/.env` 两个 Key 有效且账户有余额
- [ ] Node ≥ 20.19（`node -v`）
- [ ] 后端已启动（backend/ 目录：`python -m uvicorn app.main:app --reload --port 8000`）
- [ ] 前端已启动（frontend/ 目录：`npm run dev`）
- [ ] `python scripts\smoke_test.py` 全绿
- [ ] 知识库中有文档（左侧面板可见）

## FAQ

**1. 上传的 TXT 出现乱码？**
解析时按 UTF-8 → GBK 顺序自动识别编码（text_utils.decode_text_bytes）；仍乱码说明是其他编码，把文件另存为 UTF-8 再上传。

**2. 换 embedding 模型后报维度不匹配？**
collection 名与模型绑定（如 petcare_bge_m3），换模型自动使用新 collection，旧数据不再参与检索属正常。需要清库：停后端后删除 backend/data/chroma 目录。

**3. 前端启动报 Node 版本错误？**
Vite 7 要求 Node ≥ 20.19，安装 Node 22 LTS 即可。

**4. 调用 DeepSeek 报"模型不存在"？**
deepseek-chat 是兼容别名；若平台完成模型名迁移，把 .env 中 LLM_MODEL 改为新 ID 即可，代码零改动。

**5. 偶发 429 / 超时？**
LLM 与 Embedding 客户端均带自动重试（2 次 / 3 次）；仍限流说明账户额度或并发受限，降低提问频率或充值。

**6. 检索结果太少 / 太多？**
调整 .env：RETRIEVAL_THRESHOLD（默认 0.45，调低召回更多、调高更严格）、TOP_K（默认 4）、CHUNK_SIZE（默认 600）。

**7. 后端重启后会话不见了？**
会话存内存（无数据库的演示取舍），重启即清空；前端会自动新建会话，历史列表中的失效会话点击时会有明确提示。
