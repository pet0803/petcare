import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";

/** 消息流容器：新消息（含流式增量）自动滚动到底部 */
export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-slate-400">
        <p className="text-3xl">🐾</p>
        <p className="mt-2 text-sm">向 PetCare AI 提问吧，例如：</p>
        <p className="mt-1 text-xs">"幼猫可以喝牛奶吗？" / "狗狗的疫苗什么时候打？"</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
