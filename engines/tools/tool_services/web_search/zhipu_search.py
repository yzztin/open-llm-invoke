from typing import Literal

from zhipuai import ZhipuAI
from zhipuai.types.web_search.web_search_resp import SearchResultResp

from engines.tools.tool_services.web_search.schemas import WebSearchResults, SearchResult
from engines.tools.tool_services.web_search.schemas import WebSearchEngineEnum
from engines.tools.tool_services.web_search.base_search import BaseSearch


class ZhipuSearch(BaseSearch):
    """
    doc: https://bigmodel.cn/dev/api/search-tool/web-search
    """

    def __init__(
        self,
        api_key: str,
        search_engine: Literal[
            "search_std", "search_pro", "search_pro_sogou", "search_pro_quark", "search_pro_jina"
        ] = "search_std",
    ):
        self.search_engine = search_engine
        self.client = ZhipuAI(api_key=api_key)

    def search(self, query: str) -> WebSearchResults:
        response = self.client.web_search.web_search(search_query=query, search_engine=self.search_engine)
        return WebSearchResults(
            search_engine=WebSearchEngineEnum.ZHIPU.value,
            results=[
                SearchResult(
                    title=search_result.title,
                    link=search_result.link,
                    content=search_result.content,
                    icon=search_result.icon,
                    media=search_result.media,
                    position=int(search_result.refer.split("_")[-1]),
                )
                for search_result in response.search_result
                if isinstance(search_result, SearchResultResp)
            ],
        )
