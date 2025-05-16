"""
所有可以被调用的工具函数都需要在此处声明导入
"""

from engines.tools.tool_functions.web_search import web_search, get_web_search

__all__ = ["web_search", "get_web_search"]
