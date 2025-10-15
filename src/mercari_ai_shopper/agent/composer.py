from __future__ import annotations

from typing import List, Dict, Any


def system_prompt() -> str:
    """
    Mercari 쇼핑 어시스턴트용 시스템 프롬프트.
    - 한국어/영어 입력도 가능하지만, 검색 키워드는 가급적 일본어로 정규화하도록 유도.
    - 반드시 tool을 사용해 데이터 근거를 수집한 뒤 추천.
    """
    return (
        "You are an AI shopping assistant for Mercari Japan.\n"
        "- Understand user requests (ko/en/ja) and normalize them to concise **Japanese** keywords where possible.\n"
        "- Always use tools to search listings and (optionally) fetch details before recommending.\n"
        "- Summarize top 3 options with short, clear reasons that reference price, condition, brand/color match, and budget fit.\n"
        "- If user gives a raw sentence, infer filters (budget, condition) conservatively.\n"
        "- Output should be concise and structured.\n"
    )


def user_prompt(raw_text: str) -> str:
    """
    유저 입력을 프롬프트로 전달. 모델이 먼저 구조화 파라미터를 가정하고 tool을 호출하게 유도.
    """
    return (
        f"User request:\n"
        f"{raw_text}\n\n"
        "Steps:\n"
        "1) Extract keywords (Japanese preferred), and optional filters (budget_min/max, condition[], brand[], color[], category).\n"
        "2) Call `search_mercari` tool with best-effort parameters.\n"
        "3) If needed, call `fetch_listing_detail` for promising items.\n"
        "4) Produce top 3 recommendations with reasons.\n"
        "Return final answer in Korean if user input was Korean; otherwise in the input language.\n"
    )


def tool_defs_for_llm(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    OpenAI/Anthropic에 전달할 tool schema 리스트.
    (이미 dict 스키마 형태이므로 그대로 pass-through)
    """
    return tools
