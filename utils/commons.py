from uuid import uuid4



def get_uuid() -> str:
    """
    生成 str 类型的 32 位 uuid
    """
    return uuid4().hex

