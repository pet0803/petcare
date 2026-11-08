import { useState } from "react";

interface Props {
  disabled: boolean; // 流式生成期间禁用，防止重复提问
  onSend: (text: string) => void;
}

export default function ChatInput({ disabled, onSend }: Props) {
  const [text, setText] = useState("");

  const submit = () => {
    const q = text.trim();
    if (!q || disabled) return;
    onSend(q);
    setText("");
  };

  return (
    <div className="border-t border-slate-200 bg-white px-6 py-4">
      <div className="flex items-end gap-2">
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
          placeholder={disabled ? "正在生成回答…" : "输入你的宠物问题，Enter 发送"}
          className="max-h-40 flex-1 resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="rounded-xl bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          发送
        </button>
      </div>
    </div>
  );
}
