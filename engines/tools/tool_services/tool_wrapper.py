from functools import wraps

from engines.tools.tool_schema import ToolParam


def tool_return(func):
    """
    装饰器对象，用来强制要求所有工具函数必须返回一个 tuple[str, any]
    如果返回的结果只有一个 str, 则会自动包装成 (result, None)

    使用：
    @tool_return()
    def tool_func():
        return "result"
    被装饰后，tool_func() 返回的结果为 ("result", None)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result, None
        elif isinstance(result, tuple):
            if len(result) == 1:
                return result[0], None
            elif len(result) == 2:
                return result
            else:
                raise ValueError("工具函数必须返回一个 tuple[str, any] 或者 (str, None)")
        else:
            raise ValueError("工具函数返回的的第一个参数类型必须是 str")

    return wrapper


def get_tool_param(func):
    """
    对获取工具函数参数的方法的装饰器，要求方法名必须以 get_ 开头，返回必须是 ToolParam 类型
    """
    if not func.__name__.startswith("get_"):
        raise ValueError(f"获取工具函数参数的方法名必须以 'get_' 开头，但当前函数名为 '{func.__name__}'")

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not isinstance(result, ToolParam):
            raise TypeError(
                f"{func.__name__} 返回的类型必须是 ToolParams，但实际返回了 {type(result).__name__}"
            )
        return result

    return wrapper
