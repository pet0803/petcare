import { useState } from "react";

interface Props {
  disabled: boolean; // 流式生成期间禁用，防止重复提问
  onSend: (text: string) => void;
}

/** 底部输入区（ChatGPT 风格：居中胶囊输入框 + 圆形发送按钮） */
export default function ChatInput({ disabled, onSend }: Props) {
  const [text, setText] = useState("");

  const submit = () => {
    const q = text.trim();
    if (!q || disabled) return;
    onSend(q);
    setText("");
  };

  return (
    <div className="px-6 pb-5">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex items-end gap-1 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm transition-all focus-within:border-slate-300 focus-within:shadow-md">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              // Enter 发送；中文输入法组词中的 Enter 不触发（isComposing）
              if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder={disabled ? "正在生成回答…" : "向 PetCare AI 提问，Enter 发送"}
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-slate-800 outline-none"
          />
          <button
            onClick={submit}
            disabled={disabled || !text.trim()}
            title="发送"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500 text-lg text-white transition-colors hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-200"
          >
            ↑
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-slate-400">
          PetCare AI 的回答由 DeepSeek 基于知识库文档生成，请注意核对
        </p>
      </div>
    </div>
  );
}
