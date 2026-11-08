"""
RAG Prompt 模板。

编号规则（引用来源正确性的关键）：
    检索结果列表的第 i 条（i 从 1 起）在参考资料中编号为 [i]；
    SSE sources 事件的 index 按同一顺序生成；
    模型回答中标注的 [i] 与前端引用卡片一一对应，无需任何文本匹配。
"""
from langchain_core.documents import Document

# 系统提示词：约束模型行为，防止编造
RAG_SYSTEM_PROMPT = (
    "你是 PetCare AI，一个宠物知识问答助手。请严格遵守以下规则：\n"
    "1. 只依据【参考资料】中的内容回答问题，不得使用资料之外的知识；\n"
    "2. 如果资料中没有答案，直接回答：'抱歉，当前知识库中没有找到相关的内容。'，禁止编造；\n"
    "3. 回答使用简体中文，条理清晰；引用资料时在对应句末标注编号，如 [1]、[2]，多处引用写 [1][3]；\n"
    "4. 编号只对应本轮【参考资料】中的编号，与对话历史无关。"
)

# 用户消息模板：context 由 format_context 生成，question 为本轮问题
RAG_USER_TEMPLATE = (
    "【参考资料】\n"
    "{context}\n\n"
    "【用户问题】\n"
    "{question}"
)


def format_context(docs: list[Document]) -> str:
    """把检索结果格式化为带编号的参考资料文本。

    第 i 条文档编号 [i]，与检索顺序一致；页码随来源一起展示。
    """
    blocks = []
    for i, doc in enumerate(docs, start=1):
        page = doc.metadata.get("page")
        filename = doc.metadata.get("filename", "未知文档")
        origin = f"来源《{filename}》" + (f"第{page}页" if page else "")
        blocks.append(f"[{i}] {origin}：\n{doc.page_content.strip()}")
    return "\n\n".join(blocks)
