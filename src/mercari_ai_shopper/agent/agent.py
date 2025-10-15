from __future__ import annotations

import os
from typing import Dict, Any, List, Callable

from mercari_ai_shopper.agent.composer import system_prompt, user_prompt, tool_defs_for_llm
from mercari_ai_shopper.agent.tool_schema import get_tool_schemas
from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.scraping import mercari_client

# (옵션) Playwright 폴백도 원하면 등록 가능
# from mercari_ai_shopper.scraping.mercari_playwright import search_playwright

# LLM 클라이언트 선택
from mercari_ai_shopper.llm.openai_client import OpenAIClient
from mercari_ai_shopper.llm.anthropic_client import AnthropicClient


def _tool_search_mercari(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    LLM이 호출하는 실제 툴 구현.
    - args를 SearchQuery로 관대하게 매핑
    - mercari_client.search() 호출
    - JSON-serializable로 반환
    """
    # 관대한 파싱
    q = SearchQuery(
        raw_text="LLM structured",
        keywords=args.get("keywords", []),
        budget_min=args.get("budget_min"),
        budget_max=args.get("budget_max"),
        condition=args.get("condition", []) or [],
        brand=args.get("brand", []) or [],
        color=args.get("color", []) or [],
        category=args.get("category"),
        sort=args.get("sort", "relevance"),
        limit=min(100, max(1, int(args.get("limit", 30)))),
    )
    items = mercari_client.search(None, q)
    return [it.model_dump() for it in items]


def _tool_fetch_listing_detail(args: Dict[str, Any]) -> Dict[str, Any]:
    url = str(args.get("url", ""))
    if not url:
        raise ValueError("url is required")
    it = mercari_client.fetch_detail(None, url)
    return it.model_dump()


def _resolve_llm() -> Any:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return AnthropicClient()
    return OpenAIClient()


class Agent:
    """
    단일턴/멀티턴 상관없이 LLM ↔ 도구 호출을 중재하는 에이전트.
    - raw_text 입력 → LLM이 tool-call → 툴 실행 → 결과 전달 → 최종 응답
    """

    def __init__(self):
        self.client = _resolve_llm()
        self.tool_registry: Dict[str, Callable[[Dict[str, Any]], Any]] = {
            "search_mercari": _tool_search_mercari,
            "fetch_listing_detail": _tool_fetch_listing_detail,
        }
        self.tools = get_tool_schemas()

    def run(self, raw_text: str, max_steps: int = 3) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": user_prompt(raw_text)},
        ]
        tools = tool_defs_for_llm(self.tools)
        # OpenAI/Anthropic 공통 인터페이스(run_loop) 호출
        return self.client.run_loop(messages, tools, self.tool_registry, max_steps=max_steps)
