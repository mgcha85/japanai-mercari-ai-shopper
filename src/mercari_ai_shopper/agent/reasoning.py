from __future__ import annotations

from typing import List, Tuple
from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.models.listing import Listing
from mercari_ai_shopper.models.recommendation import RankedListing


def _budget_score(price: int, q: SearchQuery) -> Tuple[float, str | None]:
    if q.budget_max is None and q.budget_min is None:
        return 0.5, None
    # 예산 상한만 주로 쓰이는 케이스
    if q.budget_max is not None:
        if price <= q.budget_max:
            # 예산에 가까울수록 높은 점수 (낭비 최소화)
            span = max(1, q.budget_max)  # 0 division 방지
            gap = q.budget_max - price
            s = 0.6 + 0.4 * (gap / span)  # [0.6, 1.0]
            return min(1.0, max(0.0, s)), "예산 이내"
        else:
            # 초과 시 패널티
            over = price - q.budget_max
            s = max(0.0, 0.6 - (over / (q.budget_max + 1)))
            return s, "예산 초과"
    # 최소 예산만 있는 경우
    if q.budget_min is not None:
        if price >= q.budget_min:
            # 가까울수록 높음
            span = max(1, price)  # 대충 정규화
            gap = price - q.budget_min
            s = 0.6 + 0.4 * (gap / span)
            return min(1.0, max(0.0, s)), "최소 예산 이상"
        else:
            return 0.2, "최소 예산 미만"
    return 0.5, None


def _condition_score(condition_text: str | None, q: SearchQuery) -> Tuple[float, str | None]:
    if not q.condition:
        # 조건 미요청 시 중립
        return 0.5, None
    cond = condition_text or ""
    # 가중 순서: 新品、未使用 > 未使用に近い > 目立った傷や汚れなし > 그 외
    order = ["新品、未使用", "未使用に近い", "目立った傷や汚れなし"]
    for i, tag in enumerate(order):
        if tag in cond:
            return (1.0 - i * 0.15), f"상태 우수({tag})"
    # 요청한 라벨 중 하나라도 포함되면 가산
    if any(c in cond for c in q.condition):
        return 0.75, "요청 상태 부합"
    return 0.4, "상태 정보 불명/일치 낮음"


def _keyword_score(title: str, q: SearchQuery) -> Tuple[float, str | None]:
    t = title.lower()
    hits = 0
    for kw in q.keywords:
        if kw.lower() in t:
            hits += 1
    if hits == 0:
        return 0.4, "키워드 일치 낮음"
    ratio = hits / max(1, len(q.keywords))
    return 0.6 + 0.4 * ratio, "키워드 일치"


def _brand_color_score(title: str, desc_snippet: str | None, q: SearchQuery) -> Tuple[float, list[str]]:
    reasons: list[str] = []
    hay = f"{title} {(desc_snippet or '')}".lower()
    s = 0.5

    if q.brand:
        ok = all(b.lower() in hay for b in q.brand)
        if ok:
            s += 0.2
            reasons.append("브랜드 일치")
        else:
            s -= 0.15
            reasons.append("브랜드 일부 불일치")

    if q.color:
        ok = all(c.lower() in hay for c in q.color)
        if ok:
            s += 0.1
            reasons.append("색상 일치")
        else:
            s -= 0.1
            reasons.append("색상 일부 불일치")

    return max(0.0, min(1.0, s)), reasons


def rank_and_explain(items: List[Listing], q: SearchQuery, top_k: int = 3) -> List[RankedListing]:
    """
    간단한 규칙 기반 스코어링으로 Top-K 추천.
    """
    ranked: list[RankedListing] = []
    for it in items:
        reasons: list[str] = []

        sb, rb = _budget_score(it.price_jpy, q)
        if rb:
            reasons.append(rb)

        sc, rc = _condition_score(it.condition, q)
        if rc:
            reasons.append(rc)

        sk, rk = _keyword_score(it.title, q)
        if rk:
            reasons.append(rk)

        sbc, rbc = _brand_color_score(it.title, it.description_snippet, q)
        reasons.extend(rbc)

        # 가중 합 (예: 예산/상태 비중↑)
        score = 0.35 * sb + 0.3 * sc + 0.25 * sk + 0.10 * sbc
        ranked.append(RankedListing(listing=it, score=round(score, 4), reasons=reasons))

    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:max(1, top_k)]
