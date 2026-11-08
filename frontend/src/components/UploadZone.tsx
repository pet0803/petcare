import { useRef, useState } from "react";

interface Props {
  onUpload: (file: File) => Promise<void>;
}

/** 文件上传区：点击选择或拖拽上传（仅 PDF / TXT） */
export default function UploadZone({ onUpload }: Props) {
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | null) => {
    if (!file || busy) return;
    setBusy(true);
    try {
      await onUpload(file);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = ""; // 允许重复选择同一文件
    }
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files?.[0] ?? null);
      }}
      className={`cursor-pointer rounded-xl border-2 border-dashed px-4 py-5 text-center text-xs transition-colors ${
        dragOver
          ? "border-blue-400 bg-blue-50 text-blue-600"
          : "border-slate-200 bg-slate-50 text-slate-500 hover:border-blue-300 hover:text-slate-600"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />
      {busy ? (
        <span className="animate-pulse">⏳ 解析 + 向量化中，请稍候…</span>
      ) : (
        <>
          <p className="text-base">📤</p>
          <p className="mt-1">点击或拖拽上传 PDF / TXT</p>
        </>
      )}
    </div>
  );
}
