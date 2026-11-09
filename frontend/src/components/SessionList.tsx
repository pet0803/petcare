import type { SessionMeta } from "../types";

interface Props {
  sessions: SessionMeta[];
  currentSessionId: string | null;
  onSwitch: (id: string) => void;
  onDelete: (id: string) => void;
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return d.toDateString() === now.toDateString()
    ? hm
    : `${d.getMonth() + 1}/${d.getDate()} ${hm}`;
}

/** 历史会话列表：常驻左侧边栏，点击切换；悬停出现删除按钮 */
export default function SessionList({ sessions, currentSessionId, onSwitch, onDelete }: Props) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className="px-4 pb-2 text-xs font-medium text-slate-500">历史会话</p>
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {sessions.length === 0 ? (
          <p className="px-3 py-2 text-xs text-slate-400">
            暂无历史会话，点击上方"新对话"开始提问
          </p>
        ) : (
          <ul className="space-y-0.5">
            {sessions.map((s) => {
              const active = s.id === currentSessionId;
              return (
                <li key={s.id} className="group relative">
                  <button
                    onClick={() => onSwitch(s.id)}
                    className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
                      active ? "bg-slate-200" : "hover:bg-slate-200/60"
                    }`}
                  >
                    <span className="block truncate text-sm text-slate-700">
                      {s.preview || "（空会话）"}
                    </span>
                    <span className="block text-[11px] text-slate-400">
                      {formatTime(s.updated_at)}
                    </span>
                  </button>
                  <button
                    onClick={() => onDelete(s.id)}
                    title="删除会话"
                    className="absolute right-1.5 top-1/2 hidden -translate-y-1/2 rounded p-1 text-slate-400 hover:bg-slate-300 hover:text-red-600 group-hover:block"
                  >
                    ✕
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
