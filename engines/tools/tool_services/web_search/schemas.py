from utils.base_enum import BaseEnum

from pydantic import BaseModel, Field


class WebSearchEngineEnum(BaseEnum):
    ZHIPU = "zhipu"
    SERPER = "serper"


# 参考：from zhipuai.types.web_search.web_search_resp import SearchResultResp
class SearchResult(BaseModel):
    title: str = Field(...)  # 标题
    link: str  # 链接
    content: str  # 大致内容
    icon: str | None = None  # 链接图标
    media: str | None = None  # 来源媒体
    position: int | None = None  # 结果序号
    date: str | None = None  # 时间


class WebSearchResults(BaseModel):
    search_engine: str  # 搜索引擎
    results: list[SearchResult]
