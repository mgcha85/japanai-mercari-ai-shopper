from mercari_ai_shopper.models.query import SearchQuery


def test_search_query_budget_range_ok():
    q = SearchQuery(raw_text="t", keywords=["a"], budget_min=1000, budget_max=2000)
    assert q.budget_min == 1000 and q.budget_max == 2000


def test_search_query_budget_range_invalid():
    try:
        SearchQuery(raw_text="t", keywords=["a"], budget_min=3000, budget_max=1000)
    except Exception as e:
        assert "budget_max must be >=" in str(e)
    else:
        assert False, "Expected validation error"


def test_condition_whitelist():
    q = SearchQuery(
        raw_text="t",
        keywords=["a"],
        condition=["未使用に近い", "INVALID"],
    )
    assert q.condition == ["未使用に近い"]
