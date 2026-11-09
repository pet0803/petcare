import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  onSend: (text: string) => void;
}

const EXAMPLES = [
  "幼猫可以喝牛奶吗？",
  "狗狗的疫苗什么时候打？",
  "狗吃巧克力会怎么样？",
];

/** 消息流：居中列展示；空状态为欢迎页（含示例问题）；自动滚动到底部 */
export default function MessageList({ messages, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center px-6 text-center">
          <p className="text-4xl">🐾</p>
          <h2 className="mt-3 text-lg font-semibold text-slate-700">
            你好，我是 PetCare AI
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            基于知识库的宠物问答助手，试试这些问题：
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {EXAMPLES.map((q) => (
              <button
                key={q}
                onClick={() => onSend(q)}
                className="rounded-full border border-slate-200 bg-white px-4 py-1.5 text-sm text-slate-600 transition-colors hover:border-emerald-300 hover:text-emerald-600"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-3xl px-6 py-6">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
