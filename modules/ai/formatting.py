import re
from typing import Dict, List

import orjson as json

from core.utils.http import get_url, post_url

INSTRUCTIONS = """You are a helpful assistant and the chat mode of AkariBot (Chinese: 小可), developed by Teahouse Studios (Chinese: 茶馆工作室).

This is a fork project, the maintainer is Haiyuyouyan (Chinese: 海屿有燕).

Provide informative, logical, and engaging answers, covering multiple aspects of a question.

For command help, ask users to type “~help”.

Use LaTeX for math, physics, or chemistry expressions, enclosed in `$`, e.g., `$E=mc^2$`.

For professional topics (law, medicine, finance, etc.), advise to consult experts.

Do not answer questions on politics, geopolitics, politicians, political events, or ideologies. Decline immediately and state the question is inappropriate."""


def parse_markdown(md: str) -> List[Dict[str, str]]:
    code_block_pattern = r"```(\w+)?\n([\s\S]*?)\n```"  # 代码块
    block_latex_pattern = r"\$\$([\s\S]*?)\$\$"  # 块级 LaTeX
    inline_latex_pattern = r"(?<!\$)\$([^\n\$]+?)\$(?!\$)"  # 行内 LaTeX，避免 $$ 误伤
    text_split_pattern = r"(```[\s\S]*?```|\$\$[\s\S]*?\$\$|\$[^\n\$]+?\$)"  # 先分块

    blocks = []
    last_end = 0

    for match in re.finditer(text_split_pattern, md):
        start, end = match.span()
        content = match.group(0)

        if start > last_end:
            blocks.append({"type": "text", "content": md[last_end:start]})

        if content.startswith("```"):
            code_match = re.match(code_block_pattern, content)
            if code_match:
                language = code_match.group(1) or ""
                code = code_match.group(2).strip()
                blocks.append({"type": "code", "content": {"language": language, "code": code}})
        elif content.startswith("$$"):
            latex_match = re.match(block_latex_pattern, content)
            if latex_match:
                blocks.append({"type": "latex", "content": latex_match.group(1).strip()})
        elif content.startswith("$"):
            latex_match = re.match(inline_latex_pattern, content)
            if latex_match:
                blocks.append({"type": "latex", "content": latex_match.group(1).strip()})

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
