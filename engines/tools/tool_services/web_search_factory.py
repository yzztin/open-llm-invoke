from engines.tools.tool_services.web_search.zhipu_search import ZhipuSearch
from engines.tools.tool_services.web_search.serper_google_search import SerperGoogleSearch
from engines.tools.tool_services.web_search.schemas import WebSearchEngineEnum


class WebSearchFactory:
    @staticmethod
    def get_search_instance(engine_name: str) -> ZhipuSearch | SerperGoogleSearch:
        engine_name = engine_name.lower()
        if engine_name == WebSearchEngineEnum.ZHIPU.value:
            return ZhipuSearch(api_key="xxx")
        elif engine_name == WebSearchEngineEnum.SERPER.value:
            return SerperGoogleSearch(api_key="xxx")
        else:
            raise ValueError(f"未知的搜索引擎: {engine_name}, 仅支持: {WebSearchEngineEnum.list()}")
