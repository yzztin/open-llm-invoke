import re
import json


def get_dict(text: str) -> dict | None:
    """
    尝试从一段包含 json 格式的文本中提取 dict 数据
    """
    # 方式1：find
    start_pos = text.find("{")
    end_pos = text.rfind("}") + 1
    if 0 <= start_pos < end_pos:
        json_str = text[start_pos:end_pos]
        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError:
            pass

    # 方式2，正则
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        potential_json = match.group(0)
        try:
            # 验证是否是有效的JSON
            parsed = json.loads(potential_json)
            return parsed
        except json.JSONDecodeError:
            pass

    # 方式3：遍历
    brace_count = 0
    start_pos = None

    for i, char in enumerate(text):
        if char == "{":
            if brace_count == 0:
                # 第一个 { 位置
                start_pos = i
            # 遇到 {，所有存在一层{}，数量 +1
            brace_count += 1
        elif char == "}":
            # 遇到 }，所有从存放 {} 数量的 brace_count 中 -1
            brace_count -= 1
            # 减到最后，已经遍历了所有的 {}
            if brace_count == 0 and start_pos is not None:
                # 找到第一个 { 到最后一个 } 之间的内容
                json_candidate = text[start_pos : i + 1]
                try:
                    parsed = json.loads(json_candidate)
                    return parsed
                except json.JSONDecodeError:
                    pass

    raise ValueError("无法从文本中提取到有效的 JSON 数据")
