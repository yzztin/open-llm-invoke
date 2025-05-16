from abc import ABC, abstractmethod

from engines.tools.tool_services.web_search.schemas import WebSearchResults


class BaseSearch(ABC):
    @abstractmethod
    def search(self, query: str) -> WebSearchResults:
        raise NotImplementedError
