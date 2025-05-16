from pydantic import BaseModel, Field


class ToolFunctionParam(BaseModel):
    name: str
    description: str
    parameters: dict = {}  # json schema 规范结构，文档：https://json-schema.org/understanding-json-schema/reference


class ToolParam(BaseModel):
    type: str = Field("function", choices=["function"])
    function: ToolFunctionParam = Field(...)
