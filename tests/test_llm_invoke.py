from engines.llm.openai_llm_invoke import OpenAILLMInvoke
from engines.tools.tool_functions import get_web_search

llm_invoke = OpenAILLMInvoke(api_key="xxx", base_url="xxx")
model_id = "xxx"


async def test_llm_tool_call():
    tool = get_web_search()

    res_no_stream = await llm_invoke.invoke(
        user_prompt="网络搜索一下北京海淀今天的天气情况", tools=[tool], model_id=model_id
    )
    print(res_no_stream)

    res = await llm_invoke.invoke(
        user_prompt="网络搜索一下北京海淀今天的天气情况", tools=[tool], model_id=model_id, is_stream=True
    )
    async for i in res:
        print(i)


async def test_llm_no_tool():
    tool = get_web_search()

    res_no_stream = await llm_invoke.invoke(user_prompt="写一首20字的诗词", tools=[tool], model_id=model_id)

    print(res_no_stream)

    res = await llm_invoke.invoke(user_prompt="写一首20字的诗词", tools=[tool], is_stream=True, model_id=model_id)
    async for i in res:
        print(i)


async def test_llm_stop():
    import asyncio
    from engines.llm.openai_llm_invoke import global_conversation_events

    full_res = ""

    async def stream_res():
        nonlocal full_res

        res = await llm_invoke.invoke(user_prompt="写一首2000字的诗词", is_stream=True, model_id=model_id)
        async for i in res:
            full_res += i
            print(i)

    async def sopt_stream():
        await asyncio.sleep(2)
        while True:
            if global_conversation_events:
                conversation_id = list(global_conversation_events.keys())[0]
                await llm_invoke.set_event_stop(conversation_id)
                break
            else:
                await asyncio.sleep(1)

    await asyncio.gather(*[stream_res(), sopt_stream()])

    assert len(full_res) < 100

