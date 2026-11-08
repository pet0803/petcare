import type { DocumentInfo } from "../types";
import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";

interface Props {
  documents: DocumentInfo[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (doc: DocumentInfo) => void;
}

/** 左侧栏：知识库文档管理 */
export default function DocumentPanel({ documents, onUpload, onDelete }: Props) {
  return (
    <aside className="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-4 py-4">
        <h2 className="text-sm font-semibold text-slate-700">📚 知识库文档</h2>
        <p className="mt-0.5 text-xs text-slate-400">
          上传后自动解析、切片、向量化
        </p>
      </div>
      <div className="p-3">
        <UploadZone onUpload={onUpload} />
      </div>
      <div className="flex-1 overflow-y-auto pb-2">
        <DocumentList documents={documents} onDelete={onDelete} />
      </div>
    </aside>
  );
}
