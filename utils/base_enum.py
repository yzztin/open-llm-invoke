from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def list(cls) -> list:
        """
        获取所有枚举值
        """
        return list(map(lambda c: c.value, cls))
