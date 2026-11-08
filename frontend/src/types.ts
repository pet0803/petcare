// 与后端 app/models/schemas.py 及 SSE 事件数据一一对应的 TS 类型

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  file_type: string; // "pdf" | "txt"
  size_bytes: number;
  chunk_count: number;
  uploaded_at: string;
}

/** SSE sources 事件中的一条引用来源 */
export interface Source {
  index: number; // 与回答中 [n] 编号对应
  doc_id: string;
  filename: string;
  page: number | null; // TXT 无页码为 null
  snippet: string;
  score: number; // 相似度 = 1 - 余弦距离
}

/** 聊天界面中的一条消息（前端状态） */
export interface ChatMessage {
  id: string; // 前端生成，React key
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean; // 是否正在流式生成
  error?: string; // 生成失败时的错误文本
}

/** 后端会话历史中的消息 */
export interface HistoryMessage {
  role: string;
  content: string;
  created_at: string | null;
  /** assistant 消息的引用来源（后端随会话历史持久化，恢复后还原引用卡片） */
  sources?: Source[] | null;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  messages: HistoryMessage[];
}

/** 会话元信息（仅前端 localStorage 持久化）：用于"历史会话"下拉列表 */
export interface SessionMeta {
  id: string;
  preview: string; // 最近一次提问的摘要
  updated_at: number; // Unix 毫秒时间戳
}
