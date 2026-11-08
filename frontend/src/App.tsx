/**
 * 应用布局与全局状态中枢：
 * - 会话管理：session_id 持久化到 localStorage，刷新后恢复历史（后端重启后 404 则自动重建）
 * - 消息流：提问时乐观添加用户消息 + 空助手占位，SSE 增量 token 逐步填充
 * - 文档管理：上传（解析+向量化由后端完成）/ 列表 / 删除
 * - 错误提示：右上角 toast（上传失败、后端宕机等）
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSession,
  deleteDocument,
  getSession,
  listDocuments,
  uploadDocument,
} from "./api/documents";
import { streamChat } from "./api/chatStream";
import DocumentPanel from "./components/DocumentPanel";
import ChatWindow from "./components/ChatWindow";
import type { ChatMessage, DocumentInfo, SessionInfo, SessionMeta } from "./types";

const SESSION_KEY = "petcare_session_id";
const SESSION_LIST_KEY = "petcare_session_list";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [sessionList, setSessionList] = useState<SessionMeta[]>([]);

  // 流式回调是异步闭包，用 ref 保证拿到最新 session_id
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = sessionId;

  const showError = useCallback((e: unknown) => {
    setToast(e instanceof Error ? e.message : String(e));
  }, []);

  // 历史会话元信息：更新或新增并置顶，最多保留 20 条
  const upsertSessionMeta = useCallback((id: string, preview: string) => {
    setSessionList((prev) => {
      const next = [
        { id, preview: preview.slice(0, 30), updated_at: Date.now() },
        ...prev.filter((s) => s.id !== id),
      ].slice(0, 20);
      localStorage.setItem(SESSION_LIST_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const removeSessionMeta = useCallback((id: string) => {
    setSessionList((prev) => {
      const next = prev.filter((s) => s.id !== id);
      localStorage.setItem(SESSION_LIST_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  // 初始化：恢复会话（不存在则新建）+ 加载文档列表
  useEffect(() => {
    // 读取本地会话元信息列表（预览显示在历史会话下拉框中）
    try {
      const raw = localStorage.getItem(SESSION_LIST_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as SessionMeta[];
        if (Array.isArray(parsed)) setSessionList(parsed);
      }
    } catch {
      // 本地数据损坏时忽略
    }
    let cancelled = false;
    (async () => {
      try {
        let sid = localStorage.getItem(SESSION_KEY);
        let session: SessionInfo | null = null;
        if (sid) {
          try {
            session = await getSession(sid);
          } catch (e) {
            // 后端未启动等网络错误：保留旧 id 不致命，提示即可
            showError(e);
          }
        }
        if (!session) {
          // 本地没有 id，或后端已重启导致 404 → 新建会话
          sid = await createSession();
          localStorage.setItem(SESSION_KEY, sid);
        } else {
          setMessages(
            session.messages.map((m) => ({
              id: crypto.randomUUID(),
              role: m.role === "assistant" ? "assistant" : "user",
              content: m.content,
              sources: m.sources ?? undefined, // 历史消息还原引用卡片
            }))
          );
        }
        if (!cancelled) setSessionId(sid);
      } catch (e) {
        if (!cancelled) showError(e);
      }
      try {
        const docs = await listDocuments();
        if (!cancelled) setDocuments(docs);
      } catch (e) {
        if (!cancelled) showError(e);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [showError]);

  // 按 id 更新一条消息（流式 token 高频调用，用函数式 setState 避免闭包旧值）
  const updateMessage = useCallback((id: string, updater: (m: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? updater(m) : m)));
  }, []);

  const sendMessage = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || isStreaming) return;
      setToast(null);
      // 记住本次提问，用于历史会话列表的预览
      if (sessionIdRef.current) {
        upsertSessionMeta(sessionIdRef.current, q);
      }

      // 乐观更新：先上屏用户消息 + 空助手占位，token 到达后逐段填充
      const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: q };
      const assistantId = crypto.randomUUID();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      await streamChat(sessionIdRef.current, q, {
        onToken: (text) =>
          updateMessage(assistantId, (m) => ({ ...m, content: m.content + text })),
        onSources: (sources) => updateMessage(assistantId, (m) => ({ ...m, sources })),
        onDone: () => {
          updateMessage(assistantId, (m) => ({ ...m, isStreaming: false }));
          setIsStreaming(false);
        },
        onError: (msg) => {
          updateMessage(assistantId, (m) => ({ ...m, error: msg, isStreaming: false }));
          setIsStreaming(false);
        },
      });
    },
    [isStreaming, updateMessage, upsertSessionMeta]
  );

  const newSession = useCallback(async () => {
    if (isStreaming) return; // 生成回答期间禁止切换，避免消息状态错乱
    try {
      const sid = await createSession();
      localStorage.setItem(SESSION_KEY, sid);
      setSessionId(sid);
      setMessages([]);
      setToast(null);
    } catch (e) {
      showError(e);
    }
  }, [isStreaming, showError]);

  // 切换到历史会话：拉取该会话的完整历史并上屏
  const switchSession = useCallback(
    async (id: string) => {
      if (isStreaming || !id || id === sessionIdRef.current) return;
      try {
        const session = await getSession(id);
        if (!session) {
          // 后端重启后内存会话丢失：从列表中移除并提示
          removeSessionMeta(id);
          setToast("该会话已不存在（后端重启会清空内存会话）");
          return;
        }
        localStorage.setItem(SESSION_KEY, id);
        setSessionId(id);
        setMessages(
          session.messages.map((m) => ({
            id: crypto.randomUUID(),
            role: m.role === "assistant" ? "assistant" : "user",
            content: m.content,
          }))
        );
        // 保留原预览，刷新该会话的置顶时间
        const meta = sessionList.find((s) => s.id === id);
        const lastUser = [...session.messages].reverse().find((m) => m.role === "user");
        upsertSessionMeta(id, meta?.preview ?? lastUser?.content ?? "");
      } catch (e) {
        showError(e);
      }
    },
    [isStreaming, sessionList, upsertSessionMeta, removeSessionMeta, showError]
  );

  const handleUpload = useCallback(
    async (file: File) => {
      try {
        await uploadDocument(file);
        setDocuments(await listDocuments());
      } catch (e) {
        showError(e);
      }
    },
    [showError]
  );

  const handleDelete = useCallback(
    async (doc: DocumentInfo) => {
      if (!window.confirm(`删除文档《${doc.filename}》及其全部向量？`)) return;
      try {
        await deleteDocument(doc.doc_id);
        setDocuments(await listDocuments());
      } catch (e) {
        showError(e);
      }
    },
    [showError]
  );

  return (
    <div className="relative flex h-screen bg-slate-50 text-slate-800">
      {toast && (
        <div className="absolute right-4 top-4 z-50 max-w-sm rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-lg">
          <button
            className="float-right ml-3 font-bold text-red-400 hover:text-red-600"
            onClick={() => setToast(null)}
          >
            ×
          </button>
          {toast}
        </div>
      )}
      <DocumentPanel documents={documents} onUpload={handleUpload} onDelete={handleDelete} />
      <ChatWindow
        messages={messages}
        isStreaming={isStreaming}
        sessions={sessionList}
        currentSessionId={sessionId}
        onSend={sendMessage}
        onNewSession={newSession}
        onSwitchSession={switchSession}
      />
    </div>
  );
}
