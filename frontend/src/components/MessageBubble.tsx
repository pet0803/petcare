import { useState } from "react";
import type { ChatMessage } from "../types";
import SourceList from "./SourceList";

/**
 * 单条消息（ChatGPT 风格）：
 * - 用户：右侧灰色圆角气泡
 * - 助手：左侧 🐾 头像 + 无气泡正文，下方挂引用来源卡片
 * - 回答中的 [n] 渲染为引用徽章：来源就绪后可点击定位并高亮对应卡片
 */
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
          className="mx-0.5 inline-block cursor-pointer rounded bg-emerald-100 px-1 align-super text-[10px] font-semibold text-emerald-700 hover:bg-emerald-300"
        >
          {num}
        </button>
      );
    });
  };

  if (isUser) {
    return (
      <div className="mb-6 flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-slate-200 px-4 py-2.5">
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-800">
            {message.content}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 flex gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-emerald-100 text-base">
        🐾
      </div>
      <div className="min-w-0 flex-1">
        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-800">
          {message.isStreaming && !message.content && (
            <span className="text-slate-400">思考中…</span>
          )}
          {renderContent(message.content)}
          {message.isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-slate-400 align-text-bottom" />
          )}
        </div>
        {message.error && (
          <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
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
