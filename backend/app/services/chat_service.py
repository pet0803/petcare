"""
问答服务：RAG Prompt 组装 + DeepSeek 流式生成 + SSE 事件流。

RAG 流程的"生成"环节：
    检索片段（由路由层预先完成）→ 组装消息列表
    [System 规则] + 历史消息 + [Human(编号化参考资料 + 本轮问题)]
    → DeepSeek 流式生成 → 逐 token 推送 SSE
    → 结束时推送 sources（引用来源）与 done，并把本轮问答写入会话

SSE 事件顺序固定：多个 token → 一个 sources → done；流内出错发 error。

编号一致性设计：
    参考资料中的 [n] 编号 = 检索结果列表顺序；
    sources 事件的 index 同样按该顺序生成，前端零匹配逻辑。
"""
import asyncio
import json
from typing import Any, AsyncGenerator

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.prompts.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE, format_context
from app.services.session_service import Session

# ===== LLM 单例（懒加载，首次问答时初始化）=====
_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    """DeepSeek 对话客户端（OpenAI 兼容协议，流式模式）。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.llm_base_url,
            temperature=0.3,  # 知识问答场景：低温度更稳定，减少编造
            streaming=True,
            # langchain-openai 1.x 直接接受 timeout / max_retries
            timeout=60,
            max_retries=2,
        )
    return _llm


def _sse(event: str, data: dict[str, Any]) -> str:
    """把事件封装为 SSE 帧。ensure_ascii=False 保持中文原样传输。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ChatService:
    """RAG 问答服务（路由层先检索，再把结果交给本服务生成）。"""

    @staticmethod
    def build_messages(
        session: Session, question: str, docs: list[Document]
    ) -> list[Any]:
        """组装送入 LLM 的消息列表。

        关键点：参考资料只注入最后一轮 Human 消息 → 回答中的 [n] 编号
        只对应本轮检索结果；历史消息是独立消息、不参与编号
        （system 提示词第 4 条规则再加一道保险）。
        """
        messages: list[Any] = [SystemMessage(content=RAG_SYSTEM_PROMPT)]
        for m in session.history():
            if m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))
            else:
                messages.append(HumanMessage(content=m["content"]))
        messages.append(
            HumanMessage(
                content=RAG_USER_TEMPLATE.format(
                    context=format_context(docs), question=question
                )
            )
        )
        return messages

    async def stream_answer(
        self,
        session: Session,
        question: str,
        hits: list[tuple[Document, float]],
    ) -> AsyncGenerator[str, None]:
        """SSE 事件流：token* → sources → done（流内出错发 error）。

        hits 由路由层预先检索好：检索失败在流建立前就返回普通 JSON 错误；
        本方法只处理"流已建立之后"的生成过程。
        """
        docs = [doc for doc, _ in hits]
        messages = self.build_messages(session, question, docs)

        answer_parts: list[str] = []
        failed = False
        try:
            # 流式生成：astream 逐 chunk 产出，chunk.content 为增量文本
            async for chunk in _get_llm().astream(messages):
                piece = chunk.content
                if isinstance(piece, str) and piece:
                    answer_parts.append(piece)
                    yield _sse("token", {"content": piece})
        except (GeneratorExit, asyncio.CancelledError):
            raise  # 客户端中断：走 finally 保存已生成的部分回答
        except Exception as e:
            failed = True
            yield _sse("error", {"message": f"生成回答失败：{e}"})
        finally:
            # 无论成功 / 失败 / 中断，已生成的内容都写入会话历史
            answer = "".join(answer_parts)
            if answer:
                session.append("user", question)
                session.append("assistant", answer)

        if failed:
            return

        # 引用来源：index 与参考资料中的 [n] 编号一一对应
        sources = [
            {
                "index": i,
                "doc_id": doc.metadata.get("doc_id", ""),
                "filename": doc.metadata.get("filename", ""),
                "page": doc.metadata.get("page"),
                "snippet": doc.page_content.strip()[:200],
                "score": round(score, 4),
            }
            for i, (doc, score) in enumerate(hits, start=1)
        ]
        yield _sse("sources", {"sources": sources})
        yield _sse("done", {})


# 模块级单例：路由直接使用
chat_service = ChatService()
