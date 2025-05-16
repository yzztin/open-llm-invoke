import json
from json.decoder import JSONDecodeError
import logging
from typing import AsyncGenerator
import asyncio

from openai import AsyncOpenAI, AsyncStream, NOT_GIVEN
from openai.types.chat import ChatCompletionChunk

from utils.get_dict import get_dict
from utils.commons import get_uuid
from engines.llm.prompts.static.common_prompt_template import COMMON_SYSTEM_PROMPT
from engines.llm.llm_schema import HistoryMessages, ToolcallMessage, ChatMessage
from engines.tools import tool_functions
from engines.tools.tool_schema import ToolParam



logger = logging.getLogger(__name__)

# 用以实现流式会话的中断
global_conversation_events: dict[str, asyncio.Event] = {}


class OpenAILLMInvoke:
    def __init__(self, api_key:str, base_url:str):
        self.api_key = api_key
        self.base_url = base_url

        self.llm_client = self.get_llm_client()

        self.tools_history_message: HistoryMessages = HistoryMessages(messages=[])
        self.tool_origin_res: dict = {}

    def get_llm_client(self):
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def invoke(
        self,
        *,
        user_prompt: str,
        model_id: str,
        system_prompt: str = COMMON_SYSTEM_PROMPT,
        history_messages: HistoryMessages = None,
        tools: list[ToolParam] = None,
        is_stream: bool = False,
        temperature: float = 0.3,
        is_dict: bool = False,
        max_completion_tokens: int = None,
        conversation_id: str = None,
    ) -> dict | str | AsyncGenerator | None:
        """
        调用 LLM

        :param user_prompt: 用户提示词
        :param model_id: 模型 id，默认为 .env 中配置的 LLM_DEFAULT_MODEL_ID
        :param system_prompt: 系统提示词
        :param history_messages: 历史消息列表，用于模型记忆，如果为 None，则不使用历史消息
        :param tools: 工具列表，模型工具调用（原始工具调用方式）
        :param is_stream: 是否流式调用，默认为 False
        :param temperature: 模型调用 temperature 参数
        :param is_dict: 是否返回 dict 结果，如果是 False，返回原始结果，如果为 True 但是结果中不包含 dict，返回空 dict，如果 is_stream 为 True，该参数无效
        :param max_completion_tokens: 模型调用 max_completion_tokens 参数，返回结果的最大 token 数
        :param conversation_id: 会话 ID，用于流式调用时主动停止输出和历史记录写入
        :return: 模型推理结果
        """
        self.tools_history_message = HistoryMessages(messages=[])  # 每次调用都清空工具调用历史消息重新组装
        method = self.llm_client.chat.completions.create
        params = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": [tool.model_dump() for tool in tools] if tools else NOT_GIVEN,
            "temperature": temperature,
            "stream": is_stream,
            "max_completion_tokens": max_completion_tokens,
        }
        conversation_id = conversation_id or get_uuid()

        # 添加历史对话到 system prompt 和最新的 user 消息之间，放在 messages 的第二个位置
        # NOTE: history_messages 不应该存在当前最新的 user 消息
        if history_messages:
            params["messages"][1:1] = history_messages.model_dump().get("messages")

        retry_count = 0
        while retry_count < 3:
            retry_count += 1
            try:
                # 每次调用前都更新 messages 列表
                if self.tools_history_message.messages:
                    params["messages"].extend(self.tools_history_message.model_dump().get("messages"))

                llm_res = await method(**params)
                # 处理流式执行
                if is_stream:
                    # 创建会话 ID 对应的事件，用以主动停止输出
                    if conversation_id not in global_conversation_events:
                        global_conversation_events[conversation_id] = asyncio.Event()
                    async for chunk in llm_res:
                        # 通过第一个 chunk 判断是否是工具调用响应
                        tool_calls = chunk.choices[0].delta.tool_calls
                        if tool_calls:
                            await self._tool_call_process(tool_calls, True, llm_res)
                        else:
                            return self._stream_generator(chunk, llm_res, conversation_id)

                else:
                    assistant_message = llm_res.choices[0].message
                    tool_calls = assistant_message.tool_calls
                    if tool_calls:
                        await self._tool_call_process(tool_calls, False)
                    else:
                        answer = assistant_message.content
                        return get_dict(answer) if is_dict else answer

            except JSONDecodeError as e:
                logger.exception(f"JSON 解码错误：{str(e)}")
                return {}

            except Exception as e:
                logger.exception(f"LLM 调用出错：{str(e)}")
                return None

    async def exec_tool_func(self, func_name: str, func_args: dict, func_id: str):
        """
        原始方式执行工具函数，并把结果写入到 self.tools_history_message 里
        该方法独立维护
        """
        try:
            # 动态加载函数和执行
            func_obj = getattr(tool_functions, func_name)
            logger.info(f"执行工具函数：{func_name}, 参数：{func_args}")
            to_llm_content, origin_res = func_obj(**func_args)
            self.tool_origin_res[func_name] = origin_res
            self.tools_history_message.messages.append(
                ToolcallMessage(tool_call_id=func_id, name=func_name, content=to_llm_content)
            )

        except Exception as e:
            logger.exception(f"工具函数调用出错：{str(e)}")

    async def _tool_call_process(self, tool_calls, is_stream: bool, llm_res: AsyncStream = None):
        if is_stream:
            func_call_list = []
            current_tool = None

            def append_func_args(tool_part):
                nonlocal current_tool
                nonlocal func_call_list

                if tool_part.id and tool_part.id not in [tc.get("id") for tc in func_call_list if isinstance(tc, dict)]:
                    current_tool = {"id": tool_part.id, "function": {"name": "", "arguments": ""}}
                    func_call_list.append(current_tool)
                if tool_part.function.name:
                    if current_tool:
                        current_tool["function"]["name"] += tool_part.function.name
                if tool_part.function.arguments:
                    if current_tool:
                        current_tool["function"]["arguments"] += tool_part.function.arguments

            for first_tool_delta in tool_calls:
                append_func_args(first_tool_delta)

            async for chunk in llm_res:
                tool_calls_later = chunk.choices[0].delta.tool_calls
                if tool_calls_later:
                    for tool_delta in tool_calls_later:
                        append_func_args(tool_delta)

            # 将 assistant 的 tool_calls 添加到历史记录中
            self.tools_history_message.messages.append(
                ChatMessage(
                    role="assistant",
                    content=None,
                    tool_calls=func_call_list,
                )
            )
            # 执行工具函数
            for func_call in func_call_list:
                func_name = func_call["function"]["name"]
                func_args = func_call["function"]["arguments"]
                logger.info(f"LLM 执行原始工具调用（流式）：{func_name}，参数{func_args}")
                await self.exec_tool_func(func_name, json.loads(func_args), func_call["id"])
        else:
            for tool in tool_calls:
                func_name = tool.function.name
                func_args = tool.function.arguments
                func_id = tool.id

                logger.info(f"LLM 执行原始工具调用（非流式）：{func_name}，参数{func_args}")

                self.tools_history_message.messages.append(
                    ChatMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{"id": func_id, "function": {"name": func_name, "arguments": func_args}}],
                    )
                )
                await self.exec_tool_func(func_name, json.loads(func_args), func_id)

    @staticmethod
    async def _stream_generator(first_chunk: ChatCompletionChunk, llm_res: AsyncStream, conversation_id: str):
        yield first_chunk.choices[0].delta.content
        async for chunk in llm_res:
            if global_conversation_events[conversation_id].is_set():
                logger.info(f"LLM 主动停止流式输出 [会话ID: {conversation_id}]")
                break
            content = chunk.choices[0].delta.content
            if content:
                yield content

    @staticmethod
    async def set_event_stop(conversation_id: str) -> bool:
        if conversation_id in global_conversation_events:
            global_conversation_events[conversation_id].set()
            logger.info(f"LLM 已设置停止标志位 [会话ID: {conversation_id}]")
            return True
        else:
            logger.warning(f"LLM 会话不存在 [会话ID: {conversation_id}]，无法设置停止标志位")
            return False
