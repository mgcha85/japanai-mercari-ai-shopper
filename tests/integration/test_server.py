from fastapi.testclient import TestClient
from mercari_ai_shopper.server import app
from mercari_ai_shopper.models.listing import Listing
from mercari_ai_shopper.models.query import SearchQuery
import mercari_ai_shopper.scraping.mercari_client as mc


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_search_endpoint_monkeypatch(monkeypatch):
    def fake_search(session, q: SearchQuery):
        return [
            Listing(title="A", price_jpy=1000, condition="未使用に近い", shipping="送料込み",
                    url="https://jp.mercari.com/item/abc"),
            Listing(title="B", price_jpy=2000, condition=None, shipping=None,
                    url="https://jp.mercari.com/item/def"),
        ]

    monkeypatch.setattr(mc, "search", fake_search)

    c = TestClient(app)
    payload = {
        "query": {
            "raw_text": "test",
            "keywords": ["テスト"],
            "budget_max": 3000,
            "limit": 10
        },
        "top_k": 2,
        "engine": "http"
    }
    r = c.post("/search", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["top_k"] == 2
    assert len(data["items"]) >= 1
    assert data["items"][0]["listing"]["url"].startswith("https://jp.mercari.com/item/")
