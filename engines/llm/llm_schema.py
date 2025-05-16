from typing import Literal

from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessage


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    tool_calls: list | None = None  # 该字段表示模型响应的工具调用记录


class ToolcallMessage(ChatMessage):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    name: str
    # content 字段继承自 ChatMessage


class HistoryMessages(BaseModel):
    messages: list[ChatMessage | ChatCompletionMessage]
