import { useState } from "react";
import type { ChatMessage, SessionMeta } from "../types";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  sessions: SessionMeta[]; // 历史会话元信息（App 从 localStorage 加载）
  currentSessionId: string | null;
  onSend: (text: string) => void;
  onNewSession: () => void;
  onSwitchSession: (id: string) => void;
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return d.toDateString() === now.toDateString()
    ? hm
    : `${d.getMonth() + 1}/${d.getDate()} ${hm}`;
}

/** 右侧栏：聊天窗口（顶栏含历史会话切换 + 消息流 + 输入框） */
export default function ChatWindow({
  messages,
  isStreaming,
  sessions,
  currentSessionId,
  onSend,
  onNewSession,
  onSwitchSession,
}: Props) {
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-slate-800">🐾 PetCare AI</h1>
        <div className="flex items-center gap-2">
          {/* 历史会话下拉框 */}
          <div className="relative">
            <button
              onClick={() => setHistoryOpen((o) => !o)}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition-colors hover:bg-slate-50"
            >
              🗂 历史会话 ▾
            </button>
            {historyOpen && (
              <>
                {/* 透明遮罩：点击任意处关闭（也覆盖按钮，再次点击即关闭） */}
                <div className="fixed inset-0 z-10" onClick={() => setHistoryOpen(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 w-64 rounded-lg border border-slate-200 bg-white shadow-lg">
                  <ul className="max-h-64 overflow-y-auto py-1">
                    {sessions.length === 0 && (
                      <li className="px-3 py-2 text-xs text-slate-400">暂无历史会话</li>
                    )}
                    {sessions.map((s) => (
                      <li key={s.id}>
                        <button
                          onClick={() => {
                            setHistoryOpen(false);
                            onSwitchSession(s.id);
                          }}
                          className="block w-full px-3 py-2 text-left transition-colors hover:bg-slate-50"
                        >
                          <span className="flex items-center justify-between gap-2">
                            <span className="truncate text-xs text-slate-600">
                              {s.preview || "（空会话）"}
                            </span>
                            {s.id === currentSessionId && (
                              <span className="shrink-0 text-[10px] text-blue-500">当前</span>
                            )}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {formatTime(s.updated_at)}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
          <button
            onClick={onNewSession}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition-colors hover:bg-slate-50"
          >
            ＋ 新对话
          </button>
        </div>
      </header>
      <MessageList messages={messages} />
      <ChatInput disabled={isStreaming} onSend={onSend} />
    </main>
  );
}
