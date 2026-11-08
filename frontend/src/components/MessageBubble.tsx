import { useState } from "react";
import type { ChatMessage } from "../types";
import SourceList from "./SourceList";

/** 单条消息气泡：把回答中的 [n] 编号渲染为引用徽章，来源卡片就绪后可点击定位 */
export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  // 当前高亮的引用编号（点击徽章后短暂高亮来源卡片）
  const [activeSource, setActiveSource] = useState<number | null>(null);

  const sources = message.sources ?? [];
  const sourcesReady = !isUser && sources.length > 0;

  // 点击徽章：滚动到对应来源卡片并短暂高亮
  const handleCiteClick = (num: number) => {
    const target = document.getElementById(`source-${message.id}-${num}`);
    if (!target) {
      // 编号越界等异常情况：退而滚动到本消息的引用卡片区
      document
        .getElementById(`sources-${message.id}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    setActiveSource(num);
    window.setTimeout(() => {
      setActiveSource((cur) => (cur === num ? null : cur));
    }, 2000);
  };

  // 按 [数字] 切分文本：编号段渲染为徽章
  const renderContent = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (!match) return <span key={i}>{part}</span>;
      const num = Number(match[1]);
      // 来源尚未到达（流式生成中）或编号超出范围：渲染为不可点击的普通徽章
      if (!sources.some((s) => s.index === num)) {
        return (
          <span
            key={i}
            title={sourcesReady ? undefined : "引用来源将在回答完成后可点击"}
            className="mx-0.5 inline-block rounded bg-emerald-100 px-1 align-super text-[10px] font-semibold text-emerald-700"
          >
            {num}
          </span>
        );
      }
      return (
        <button
          key={i}
          onClick={() => handleCiteClick(num)}
          title={`查看引用来源 ${num}`}
          className="mx-0.5 inline-block cursor-pointer rounded bg-emerald-100 px-1 align-super text-[10px] font-semibold text-emerald-700 hover:bg-emerald-200"
        >
          {num}
        </button>
      );
    });
  };

  return (
    <div className={`mb-4 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "rounded-br-sm bg-blue-500 text-white"
            : "rounded-bl-sm border border-slate-200 bg-white text-slate-800 shadow-sm"
        }`}
      >
        {message.isStreaming && !message.content && (
          <span className="text-sm text-slate-400">思考中…</span>
        )}
        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
          {renderContent(message.content)}
          {message.isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-slate-400 align-text-bottom" />
          )}
        </div>
        {message.error && (
          <p className="mt-2 rounded bg-red-50 px-2 py-1 text-xs text-red-600">
            ⚠️ {message.error}
          </p>
        )}
        {sourcesReady && (
          <SourceList messageId={message.id} sources={sources} activeIndex={activeSource} />
        )}
      </div>
    </div>
  );
}
