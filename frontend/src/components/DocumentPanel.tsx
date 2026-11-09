import type { DocumentInfo } from "../types";
import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";

interface Props {
  documents: DocumentInfo[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (doc: DocumentInfo) => void;
}

/** 知识库文档区（侧边栏底部）：上传入口 + 文档列表 */
export default function DocumentPanel({ documents, onUpload, onDelete }: Props) {
  return (
    <div className="shrink-0 border-t border-slate-200">
      <p className="px-4 pb-1 pt-3 text-xs font-medium text-slate-500">📚 知识库文档</p>
      <div className="px-2 pb-2 pt-1">
        <UploadZone onUpload={onUpload} />
      </div>
      <div className="max-h-56 overflow-y-auto pb-2">
        <DocumentList documents={documents} onDelete={onDelete} />
      </div>
    </div>
  );
}
