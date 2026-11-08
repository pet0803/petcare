// 统一的 fetch 封装：BASE=/api（由 Vite 代理到 FastAPI :8000）
// 非 2xx 响应时读取后端 {"detail": "..."} 中的错误信息并抛出

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`/api${path}`, options);
  if (!resp.ok) {
    let detail = `请求失败 (${resp.status})`;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (body?.detail) detail = String(body.detail);
    } catch {
      // 非 JSON 响应，保留默认信息
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
