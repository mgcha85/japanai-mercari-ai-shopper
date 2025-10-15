from __future__ import annotations

import os
import logging
from typing import List, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.models.listing import Listing
from .mercari_client import build_search_url, _parse_listing_cards  # 재활용

logger = logging.getLogger(__name__)

PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("1", "true", "yes")


def _launch():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
    context = browser.new_context(locale="ja-JP")
    page = context.new_page()
    return p, browser, context, page


def search_playwright(q: SearchQuery, wait_selector: str = "img") -> List[Listing]:
    """
    Playwright 기반 검색 (동적 로딩 대비).
    - wait_selector: 결과 안정화 대기용 셀렉터 (기본 이미지 로드)
    """
    url = build_search_url(q)
    logger.info("Playwright search: %s", url)

    p = browser = context = page = None
    try:
        p, browser, context, page = _launch()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector(wait_selector, timeout=7000)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        items = _parse_listing_cards(soup)

        # client-side 필터는 mercari_client.search와 동일 정책
        def ok_budget(x: Listing) -> bool:
            if q.budget_min is not None and x.price_jpy < q.budget_min:
                return False
            if q.budget_max is not None and x.price_jpy > q.budget_max:
                return False
            return True

        def ok_condition(x: Listing) -> bool:
            if not q.condition:
                return True
            return any(c in (x.condition or "") for c in q.condition)

        def ok_brand_color(x: Listing) -> bool:
            title = (x.title or "").lower()
            desc = (x.description_snippet or "").lower()
            hay = f"{title} {desc}"
            for b in q.brand or []:
                if b.lower() not in hay:
                    return False
            for c in q.color or []:
                if c.lower() not in hay:
                    return False
            return True

        items = [it for it in items if ok_budget(it) and ok_condition(it) and ok_brand_color(it)]

        if q.sort == "price_asc":
            items.sort(key=lambda x: x.price_jpy)
        elif q.sort == "price_desc":
            items.sort(key=lambda x: x.price_jpy, reverse=True)
        # relevance/new → 그대로

        limit = max(1, min(100, q.limit))
        return items[:limit]
    finally:
        try:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
            if p:
                p.stop()
        except Exception:  # noqa: BLE001
            pass
