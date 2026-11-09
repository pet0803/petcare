import type { DocumentInfo, SessionMeta } from "../types";
import SessionList from "./SessionList";
import DocumentPanel from "./DocumentPanel";

interface Props {
  sessions: SessionMeta[];
  currentSessionId: string | null;
  documents: DocumentInfo[];
  onNewSession: () => void;
  onSwitchSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onUpload: (file: File) => Promise<void>;
  onDeleteDocument: (doc: DocumentInfo) => void;
}

/** 左侧边栏（ChatGPT 风格）：新对话 + 历史会话常驻列表 + 知识库文档区 */
export default function Sidebar({
  sessions,
  currentSessionId,
  documents,
  onNewSession,
  onSwitchSession,
  onDeleteSession,
  onUpload,
  onDeleteDocument,
}: Props) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-slate-200 bg-slate-100">
      {/* 新对话 */}
      <div className="p-3">
        <button
          onClick={onNewSession}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
        >
          ＋ 新对话
        </button>
      </div>
      {/* 历史会话：自动显示，无需点击展开 */}
      <SessionList
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSwitch={onSwitchSession}
        onDelete={onDeleteSession}
      />
      {/* 知识库文档 */}
      <DocumentPanel documents={documents} onUpload={onUpload} onDelete={onDeleteDocument} />
    </aside>
  );
}
