// SSE 流式问答封装：POST /api/chat，按事件类型分发回调。
// EventSource 不支持 POST 请求体，因此使用 @microsoft/fetch-event-source。

import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { Source } from "../types";

export interface ChatStreamHandlers {
  onToken: (text: string) => void; // 流式增量文本
  onSources: (sources: Source[]) => void; // 引用来源（流结束前到达）
  onDone: () => void; // 流结束（无论成功/中断，都会调用以解锁输入框）
  onError: (message: string) => void; // 错误信息（展示在消息气泡中）
}

/** 服务端返回的业务错误（携带 detail 信息） */
class ChatStreamError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ChatStreamError";
  }
}

export async function streamChat(
  sessionId: string | null,
  question: string,
  handlers: ChatStreamHandlers
): Promise<void> {
  let receivedDone = false;
  try {
    await fetchEventSource("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question }),
      openWhenHidden: true,

      // 非流式响应（如 503 JSON 错误）：读取 detail 后抛出，进入 onerror
      async onopen(response) {
        const contentType = response.headers.get("content-type") ?? "";
        if (response.ok && contentType.includes("text/event-stream")) {
          return; // 正常：流已建立
        }
        let detail = `请求失败 (${response.status})`;
        try {
          const body = (await response.json()) as { detail?: unknown };
          if (body?.detail) detail = String(body.detail);
        } catch {
          // 忽略解析失败，保留默认信息
        }
        throw new ChatStreamError(detail);
      },

      onmessage(msg) {
        if (!msg.data) return;
        let data: Record<string, unknown>;
        try {
          data = JSON.parse(msg.data) as Record<string, unknown>;
        } catch {
          return; // 忽略无法解析的帧
        }
        switch (msg.event) {
          case "token":
            handlers.onToken(String(data.content ?? ""));
            break;
          case "sources":
            handlers.onSources((data.sources ?? []) as Source[]);
            break;
          case "done":
            receivedDone = true;
            handlers.onDone();
            break;
          case "error":
            handlers.onError(String(data.message ?? "生成回答失败"));
            break;
        }
      },

      // 网络错误 / 非 2xx / onopen 抛出的错误都在这里处理；不返回重试间隔 = 不重试
      onerror(err) {
        const message =
          err instanceof ChatStreamError
            ? err.message
            : "网络错误，请确认后端服务已启动";
        handlers.onError(message);
        return; // 返回 undefined → 停止重试，触发 onclose
      },

      // 流关闭（正常 done 后也会走到）：兜底解锁输入框
      onclose() {
        if (!receivedDone) {
          handlers.onDone();
        }
      },
    });
  } catch {
    // fetchEventSource 内部已通过 onerror 上报；此处兜底，避免未捕获异常
    handlers.onDone();
  }
}
