# tests/e2e/test_cli_e2e.py  (교체)
from mercari_ai_shopper.models.listing import Listing
from mercari_ai_shopper.models.query import SearchQuery
import mercari_ai_shopper.scraping.mercari_client as mc
from mercari_ai_shopper.run import main
import io
import sys


def test_cli_e2e_monkeypatched(monkeypatch, capsys):
    # fake search 결과 주입
    def fake_search(session, q: SearchQuery):
        return [
            Listing(
                title="Nintendo Switch OLED White",
                price_jpy=29800,
                condition="未使用に近い",
                shipping="送料込み",
                url="https://jp.mercari.com/item/1",
            ),
            Listing(
                title="Nintendo Switch (used)",
                price_jpy=25000,
                condition="目立った傷や汚れなし",
                shipping=None,
                url="https://jp.mercari.com/item/2",
            ),
        ]

    monkeypatch.setattr("mercari_ai_shopper.run.http_search", fake_search)

    # CLI 인자 구성 (엔진은 http로 고정)
    argv = [
        "--query", "ニンテンドー スイッチ OLED ホワイト",
        "--keywords", "Nintendo", "Switch", "OLED", "White",   # ← 키워드로 1위 유도
        "--condition", "未使用に近い",                           # ← 상태 가중치도 1위 쪽에 유리
        "--budget-max", "30000",
        "--limit", "10",
        "--top-k", "2",
        "--engine", "http",
    ]
    # main() 실행
    rc = main(argv)
    assert rc == 0

    # 출력 확인
    out = capsys.readouterr().out
    assert "1. Nintendo Switch OLED White" in out
    assert "¥29800" in out or "¥29,800" in out
    assert "점수" in out or "근거" in out
