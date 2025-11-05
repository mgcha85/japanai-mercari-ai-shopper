from __future__ import annotations

import argparse
from typing import List

from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.scraping.mercari_client import search as http_search
from mercari_ai_shopper.scraping.mercari_playwright import search_playwright
from mercari_ai_shopper.agent.reasoning import rank_and_explain


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Mercari AI Shopper CLI")
    p.add_argument("--query", required=True, help="자연어 또는 키워드 (일본어 권장)")
    p.add_argument("--keywords", nargs="*", default=None, help="키워드 배열. 미지정 시 --query 그대로 1개로 사용")
    p.add_argument("--budget-max", type=int, default=None)
    p.add_argument("--budget-min", type=int, default=None)
    p.add_argument("--condition", nargs="*", default=None)
    p.add_argument("--brand", nargs="*", default=None)
    p.add_argument("--color", nargs="*", default=None)
    p.add_argument("--category", default=None)
    p.add_argument("--sort", default="relevance", choices=["relevance", "price_asc", "price_desc", "new"])
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--engine", default="http", choices=["http", "playwright"])

    args = p.parse_args(argv)

    kws = args.keywords if args.keywords else [args.query]

    q = SearchQuery(
        raw_text=args.query,
        keywords=kws,
        budget_min=args.budget_min,
        budget_max=args.budget_max,
        condition=args.condition or [],
        brand=args.brand or [],
        color=args.color or [],
        category=args.category,
        sort=args.sort,
        limit=args.limit,
    )

    if args.engine == "playwright":
        items = search_playwright(q)
    else:
        items = http_search(None, q)

    ranked = rank_and_explain(items, q, top_k=args.top_k)

    # 보기 좋게 출력
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r.listing.title}  ¥{r.listing.price_jpy}")
        if r.listing.condition:
            print(f"   - 상태: {r.listing.condition}")
        print(f"   - URL: {r.listing.url}")
        print(f"   - 점수: {r.score}")
        if r.reasons:
            print(f"   - 근거: {', '.join(r.reasons)}")
        print()

    # JSON 출력이 필요하면 아래 주석 해제
    # print(json.dumps([r.model_dump() for r in ranked], ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
