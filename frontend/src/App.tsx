/**
 * 阶段 1 占位页：用于验证前后端链路打通。
 * 阶段 5 将替换为完整聊天界面（左：文档管理，右：流式对话 + 引用来源）。
 */
export default function App() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-slate-800">🐾 PetCare AI</h1>
        <p className="mt-3 text-slate-500">基于 RAG 的宠物智能知识库问答系统</p>
        <p className="mt-1 text-sm text-slate-400">
          项目初始化成功 · 打开{" "}
          <a className="underline" href="/api/health" target="_blank" rel="noreferrer">
            /api/health
          </a>{" "}
          验证后端连通
        </p>
      </div>
    </div>
  );
}
