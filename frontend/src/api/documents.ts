// 文档与会话相关的 REST 调用（SSE 流式问答见 chatStream.ts）
import { ApiError, http } from "./client";
import type { DocumentInfo, SessionInfo } from "../types";

export async function listDocuments(): Promise<DocumentInfo[]> {
  const data = await http.get<{ documents: DocumentInfo[] }>("/documents");
  return data.documents;
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  // 注意：不要手动设置 Content-Type —— 浏览器会自动带上 multipart boundary
  const resp = await fetch("/api/documents/upload", { method: "POST", body: form });
  if (!resp.ok) {
    let detail = `上传失败 (${resp.status})`;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (body?.detail) detail = String(body.detail);
    } catch {
      // 非 JSON 响应，保留默认信息
    }
    throw new Error(detail);
  }
  return (await resp.json()) as DocumentInfo;
}

export async function deleteDocument(docId: string): Promise<void> {
  await http.delete(`/documents/${encodeURIComponent(docId)}`);
}

export async function createSession(): Promise<string> {
  const data = await http.post<{ session_id: string }>("/sessions", {});
  return data.session_id;
}

/** 查询会话历史；会话不存在（后端重启后）返回 null，由调用方决定重建 */
export async function getSession(sessionId: string): Promise<SessionInfo | null> {
  try {
    return await http.get<SessionInfo>(`/sessions/${encodeURIComponent(sessionId)}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
