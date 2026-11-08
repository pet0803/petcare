import type { Source } from "../types";

interface Props {
  messageId: string;
  sources: Source[];
  activeIndex?: number | null; // 点击徽章后高亮的引用编号
}

/** 引用来源卡片列表：回答中的 [n] 徽章点击后滚动定位并高亮对应条目 */
export default function SourceList({ messageId, sources, activeIndex }: Props) {
  return (
    <div id={`sources-${messageId}`} className="mt-3 border-t border-slate-100 pt-2">
      <p className="text-xs font-medium text-slate-400">📎 引用来源</p>
      <ul className="mt-1.5 space-y-1.5">
        {sources.map((s) => (
          <li
            key={`${messageId}-${s.index}`}
            id={`source-${messageId}-${s.index}`}
            className={`rounded-lg px-2.5 py-2 transition-colors duration-300 ${
              s.index === activeIndex ? "bg-amber-50 ring-1 ring-amber-300" : "bg-slate-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="shrink-0 rounded bg-emerald-100 px-1.5 text-[10px] font-semibold text-emerald-700">
                [{s.index}]
              </span>
              <span className="min-w-0 truncate text-xs font-medium text-slate-600">
                {s.filename}
              </span>
              {s.page != null && (
                <span className="shrink-0 text-xs text-slate-400">第{s.page}页</span>
              )}
              <span className="ml-auto shrink-0 text-[10px] text-slate-400">
                相似度 {(s.score * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-slate-500">
              {s.snippet}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
