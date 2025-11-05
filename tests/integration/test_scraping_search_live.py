import os
import pytest
from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.scraping.mercari_client import search

LIVE = os.getenv("LIVE_WEB") == "1"


@pytest.mark.skipif(not LIVE, reason="Set LIVE_WEB=1 to run live web tests")
def test_live_search_smoke():
    q = SearchQuery(raw_text="nintendo", keywords=["ニンテンドー"], limit=5)
    items = search(None, q)
    assert isinstance(items, list)
    # 결과가 0일 수도 있으니 타입만 체크
    for it in items[:2]:
        assert it.url.startswith("https://jp.mercari.com/item/")
