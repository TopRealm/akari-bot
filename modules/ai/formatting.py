import re
from typing import Dict, List

import orjson as json

from core.utils.http import get_url, post_url

INSTRUCTIONS = """You are a helpful assistant and the chat mode of AkariBot (Chinese: 小可), developed by Teahouse Studios (Chinese: 茶馆工作室).

Provide informative, logical, and engaging answers, covering multiple aspects of a question.

For command help, ask users to type “~help”.

Use LaTeX for math, physics, or chemistry expressions, enclosed in `$`, e.g., `$E=mc^2$`.

For professional topics (law, medicine, finance, etc.), advise to consult experts.

Do not answer questions on politics, geopolitics, politicians, political events, or ideologies. Decline immediately and state the question is inappropriate."""


def parse_markdown(md: str) -> List[Dict[str, str]]:
    code_block_pattern = r"```(?:([\w+-]*)\n)?([\s\S]*?)```"
    latex_block_pattern = r"\$\$(.*?)\$\$"
    latex_inline_pattern = r"(?<!\\|\w)\$(.*?)(?<!\\)\$(?!\w)"

    pattern = f"({code_block_pattern})|({latex_block_pattern})|({latex_inline_pattern})"

    blocks = []
    last_end = 0

    for match in re.finditer(pattern, md, re.DOTALL):
        start, end = match.span()
        
        if start > last_end:
            blocks.append({"type": "text", "content": md[last_end:start]})

        if match.group(2):  
            language = match.group(2) or None
            code = match.group(3)
            blocks.append({"type": "code", "content": {"language": language, "code": code}})
        
        elif match.group(4):
            blocks.append({"type": "latex", "content": match.group(4).strip()})

        elif match.group(5):
            blocks.append({"type": "latex", "content": match.group(5).strip()})
        last_end = end
        
    if last_end < len(md):
        blocks.append({"type": "text", "content": md[last_end:]})

    return blocks
    

async def generate_latex(formula: str):
    resp = await post_url(
        url="https://wikimedia.org/api/rest_v1/media/math/check/inline-tex",
        data=json.dumps({"q": formula}),
        headers={"content-type": "application/json"},
        fmt="headers",
    )
    if resp:
        location = resp.get("x-resource-location")
        if not location:
            raise ValueError("Cannot get LaTeX resource location")

    return await get_url(
        url=f"https://wikimedia.org/api/rest_v1/media/math/render/png/{location}",
        fmt="content",
    )


async def generate_code_snippet(code: str, language: str):
    return await post_url(
        url="https://sourcecodeshots.com/api/image",
        data=json.dumps(
            {
                "code": code,
                "settings": {
                    "language": language,
                    "theme": "night-owl",
                },
            }
        ),
        headers={"content-type": "application/json"},
        fmt="content",
    )
