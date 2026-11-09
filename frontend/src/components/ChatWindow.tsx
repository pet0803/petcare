import type { ChatMessage } from "../types";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (text: string) => void;
}

/** 主聊天区（ChatGPT 风格：无顶栏，居中消息列 + 底部输入框） */
export default function ChatWindow({ messages, isStreaming, onSend }: Props) {
  return (
    <main className="flex min-w-0 flex-1 flex-col bg-white">
      <MessageList messages={messages} onSend={onSend} />
      <ChatInput disabled={isStreaming} onSend={onSend} />
    </main>
  );
}
