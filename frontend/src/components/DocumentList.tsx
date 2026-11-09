import type { DocumentInfo } from "../types";

interface Props {
  documents: DocumentInfo[];
  onDelete: (doc: DocumentInfo) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** 文档条目列表（侧边栏）：悬停显示删除按钮 */
export default function DocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return (
      <p className="px-4 py-3 text-center text-xs text-slate-400">
        暂无文档，先上传一个吧
      </p>
    );
  }
  return (
    <ul className="px-2">
      {documents.map((doc) => (
        <li
          key={doc.doc_id}
          className="group flex items-start gap-2 rounded-lg px-2 py-2 transition-colors hover:bg-slate-200/60"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-slate-700" title={doc.filename}>
              {doc.file_type === "pdf" ? "📄" : "📃"} {doc.filename}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {doc.chunk_count} 个切片 · {formatSize(doc.size_bytes)}
            </p>
          </div>
          <button
            onClick={() => onDelete(doc)}
            className="shrink-0 rounded p-1 text-slate-400 opacity-0 transition-opacity hover:bg-slate-300 hover:text-red-600 group-hover:opacity-100"
            title="删除文档及其向量"
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
