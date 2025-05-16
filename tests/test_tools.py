from engines.tools.tool_services.web_search_factory import WebSearchFactory


def test_search_factory():
    query = "北京海淀今天天气"
    search_instance = WebSearchFactory.get_search_instance("zhipu")
    result = search_instance.search(query)
    print(result)
    assert result.search_engine == "zhipu"
    assert len(result.results) > 0

    search_instance = WebSearchFactory.get_search_instance("serper")
    result = search_instance.search(query)
    print(result)
    assert result.search_engine == "serper"
    assert len(result.results) > 0

