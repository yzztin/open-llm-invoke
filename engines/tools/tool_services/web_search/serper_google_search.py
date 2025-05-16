import http.client
import json

from engines.tools.tool_services.web_search.schemas import WebSearchResults, SearchResult
from engines.tools.tool_services.web_search.schemas import WebSearchEngineEnum
from engines.tools.tool_services.web_search.base_search import BaseSearch


class SerperGoogleSearch(BaseSearch):
    """
    doc: https://serper.dev/
    """

    default_extra_search_params = {
        "gl": "cn",
        "hl": "zh-cn",
        "num": 10,
    }

    def __init__(
        self,
        api_key: str,
        base_url="google.serper.dev",
        search_params: dict | None = None,
    ):
        self._api_key = api_key
        self.client = http.client.HTTPSConnection(base_url)

        self.search_params = search_params
        if self.search_params is None:
            self.search_params = {}

        self.search_params.update(self.default_extra_search_params)

    def search(self, query: str) -> WebSearchResults:
        payload = {"q": query}
        payload.update(self.search_params)

        headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}

        self.client.request("POST", "/search", json.dumps(payload), headers)
        response = self.client.getresponse()
        search_result = json.loads(response.read().decode("utf-8"))
        return WebSearchResults(
            search_engine=WebSearchEngineEnum.SERPER.value,
            results=[
                SearchResult(
                    title=res.get("title"),
                    link=res.get("link"),
                    content=res.get("snippet"),
                    position=res.get("position"),
                    date=res.get("date"),
                )
                for res in search_result["organic"]
            ],
        )
