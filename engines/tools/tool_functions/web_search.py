from engines.tools.tool_services.web_search_factory import WebSearchFactory
from engines.tools.tool_schema import ToolParam, ToolFunctionParam
from engines.tools.tool_services.tool_wrapper import tool_return, get_tool_param

search_instance = WebSearchFactory.get_search_instance("serper")


@tool_return
def web_search(query: str) -> tuple[str, dict]:
    """
    调用搜索引擎执行网络搜索
    :param query: 调用搜索引擎进行网络搜索的查询语句
    :return: 直接给到模型的结果、原始搜索结果列表
    """
    search_res = search_instance.search(query)
    search_res_list = [
        res.model_dump(include={"title", "content", "position", "date"}, exclude_none=True)
        for res in search_res.results
    ]
    return str(search_res_list), search_res.model_dump()


@get_tool_param
def get_web_search() -> ToolParam:
    web_search_tool = ToolParam(
        function=ToolFunctionParam(
            name="web_search",
            description="调用搜索引擎执行网络搜索",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "调用搜索引擎进行网络搜索的查询语句",
                    }
                },
                "required": ["query"],
            },
        )
    )
    return web_search_tool
