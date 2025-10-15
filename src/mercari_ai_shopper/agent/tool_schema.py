from __future__ import annotations

"""
LLM tool-calling에 사용할 JSON 스키마 정의.
OpenAI(Function calling)/Anthropic(Tool use) 모두 호환되는 dict 형태로 제공.
"""

search_mercari = {
    "name": "search_mercari",
    "description": "Search items on Mercari Japan with optional filters and return a list of listings.",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Japanese (preferred) or translated keywords for search.",
            },
            "budget_min": {"type": "integer", "description": "Minimum price (JPY)."},
            "budget_max": {"type": "integer", "description": "Maximum price (JPY)."},
            "condition": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Mercari condition labels in Japanese. Example: ['未使用に近い']",
            },
            "brand": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional brand names to match.",
            },
            "color": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional color keywords to match.",
            },
            "category": {
                "type": "string",
                "description": "Optional category name (free text).",
            },
            "sort": {
                "type": "string",
                "enum": ["relevance", "price_asc", "price_desc", "new"],
                "description": "Sorting strategy (best-effort on client side).",
            },
            "limit": {
                "type": "integer",
                "default": 30,
                "description": "Number of items to fetch (client will cap to 100).",
            },
        },
        "required": ["keywords"],
    },
}

fetch_listing_detail = {
    "name": "fetch_listing_detail",
    "description": "Fetch detail information for a single Mercari listing URL.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Absolute URL of a Mercari item (https://jp.mercari.com/item/...).",
            }
        },
        "required": ["url"],
    },
}


def get_tool_schemas() -> list[dict]:
    """
    에이전트 초기화 시 도구 목록으로 주입하기 위한 헬퍼.
    """
    return [search_mercari, fetch_listing_detail]
