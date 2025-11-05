from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.models.listing import Listing
from mercari_ai_shopper.agent.reasoning import rank_and_explain


def test_rank_and_explain_simple():
    q = SearchQuery(raw_text="nintendo", keywords=["nintendo"], budget_max=30000)
    items = [
        Listing(title="Nintendo Switch OLED White", price_jpy=29800, condition="未使用に近い",
                shipping="送料込み", url="https://jp.mercari.com/item/1"),
        Listing(title="Random Item", price_jpy=50000, condition=None,
                shipping=None, url="https://jp.mercari.com/item/2"),
    ]
    ranked = rank_and_explain(items, q, top_k=2)
    assert ranked[0].listing.url.endswith("/1")
    assert ranked[0].score >= ranked[1].score
    assert ranked[0].reasons  # at least one reason
