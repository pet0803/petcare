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

/** 文档卡片列表 + 删除按钮 */
export default function DocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return (
      <p className="px-4 py-6 text-center text-xs text-slate-400">
        暂无文档，先上传一个吧
      </p>
    );
  }
  return (
    <ul className="divide-y divide-slate-100">
      {documents.map((doc) => (
        <li key={doc.doc_id} className="flex items-start gap-2 px-4 py-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-700" title={doc.filename}>
              {doc.file_type === "pdf" ? "📄" : "📃"} {doc.filename}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              {doc.chunk_count} 个切片 · {formatSize(doc.size_bytes)} · {doc.uploaded_at}
            </p>
          </div>
          <button
            onClick={() => onDelete(doc)}
            className="shrink-0 rounded px-1 text-slate-300 hover:text-red-500"
            title="删除文档及其向量"
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
