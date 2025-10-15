from __future__ import annotations

import os
import re
import time
import logging
from typing import Iterable, List, Optional
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

from mercari_ai_shopper.models.listing import Listing, SellerInfo
from mercari_ai_shopper.models.query import SearchQuery

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 환경설정 (필요 시 config.py에서 불러오도록 바꿔도 OK)
# ──────────────────────────────────────────────────────────────────────────────
MERCARI_BASE_URL = os.getenv("MERCARI_BASE_URL", "https://jp.mercari.com/search")
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)
ACCEPT_LANGUAGE = os.getenv("ACCEPT_LANGUAGE", "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))
HTTP_BACKOFF_SECONDS = float(os.getenv("HTTP_BACKOFF_SECONDS", "0.5"))

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": ACCEPT_LANGUAGE,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "no-cache",
}

ITEM_URL_PREFIX = "https://jp.mercari.com/item/"

# Yen price pattern (ex: ¥12,345)
YEN_PRICE_RE = re.compile(r"[¥￥]\s?([\d,]+)")


# ──────────────────────────────────────────────────────────────────────────────
# HTTP 유틸
# ──────────────────────────────────────────────────────────────────────────────
def _request(session: requests.Session, url: str, params: Optional[dict] = None) -> requests.Response:
    """
    간단한 재시도/백오프 포함 GET 요청.
    """
    last_exc = None
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, headers=DEFAULT_HEADERS, timeout=HTTP_TIMEOUT)
            # 일부 사이트는 403/429 발생 가능 → 백오프
            if resp.status_code in (429, 403, 503):
                raise requests.HTTPError(f"Status {resp.status_code}")
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("GET failed (attempt %s/%s): %s", attempt, HTTP_MAX_RETRIES, exc)
            if attempt < HTTP_MAX_RETRIES:
                time.sleep(HTTP_BACKOFF_SECONDS * attempt)
    # 최종 실패
    raise last_exc  # type: ignore[misc]


# ──────────────────────────────────────────────────────────────────────────────
# 검색 URL 빌더
# ──────────────────────────────────────────────────────────────────────────────
def build_search_url(q: SearchQuery) -> str:
    """
    머카리의 공식 쿼리 파라미터는 비공식/변동 가능성이 있으므로
    최소한의 'keyword' 기반 검색만 확실히 구성한다.
    가격/정렬/상태 등은 이후 고도화 시 server-side 지원이 확인될 때 확장.

    예: https://jp.mercari.com/search?keyword=nintendo%20switch%20oled
    """
    keywords = " ".join(k.strip() for k in q.keywords if k.strip())
    params = {"keyword": keywords}

    # (참고) 일부 파라미터는 사이트 변경에 민감하므로 기본적으로는 붙이지 않는다.
    # if q.budget_min is not None:
    #     params["price_min"] = str(q.budget_min)
    # if q.budget_max is not None:
    #     params["price_max"] = str(q.budget_max)

    return f"{MERCARI_BASE_URL}?{urlencode(params)}"


# ──────────────────────────────────────────────────────────────────────────────
# 파싱 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
def _extract_price_int(text: str) -> Optional[int]:
    """
    텍스트에서 '¥12,345' 형태를 찾아 int로 변환.
    """
    if not text:
        return None
    m = YEN_PRICE_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except Exception:  # noqa: BLE001
        return None


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _clean_text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


# ──────────────────────────────────────────────────────────────────────────────
# 리스트 파서 (검색결과)
# ──────────────────────────────────────────────────────────────────────────────
def _parse_listing_cards(soup: BeautifulSoup) -> List[Listing]:
    """
    검색 결과 페이지에서 상품 카드들을 최대한 관대한 방식으로 파싱.
    여러 CSS 선택자 후보를 두고 일치하는 것들만 추출한다.
    """
    cards: list = []

    # 후보 컨테이너 선택자(머카리 UI 변경에 대비)
    container_selectors = [
        "section",  # 넓은 범위
        "div",
        "ul",
    ]
    item_selectors = [
        "a[data-testid='ItemCell']",
        "a[data-testid='itemCell']",
        "a[data-item-id]",
        "li a[href^='/item/']",
        "a[href^='/item/']",
        "a[href^='https://jp.mercari.com/item/']",
    ]

    for cont_sel in container_selectors:
        containers = soup.select(cont_sel)
        for cont in containers:
            for item_sel in item_selectors:
                for a in cont.select(item_sel):
                    href = a.get("href")
                    if not href:
                        continue
                    # 절대 URL 변환
                    url = href if href.startswith("http") else urljoin("https://jp.mercari.com", href)
                    if not url.startswith(ITEM_URL_PREFIX):
                        continue

                    # 타이틀 후보
                    title = _first_non_empty(
                        a.get("aria-label"),
                        a.get("title"),
                        _clean_text(a),
                    )
                    # 이미지 후보
                    img_el = a.select_one("img")
                    image_url = img_el.get("src") if img_el and img_el.get("src") else None

                    # 가격 후보 (링크 내부 또는 부모 영역)
                    price_text = None
                    price_candidates = [
                        a.select_one("[data-testid='ItemPrice']"),
                        a.select_one("div:matches(:contains('¥'))"),  # lxml css4 pseudo 미지원 → fallback
                        a,
                    ]
                    for pc in price_candidates:
                        if not pc:
                            continue
                        t = _clean_text(pc)
                        if "¥" in t or "￥" in t:
                            price_text = t
                            break
                    price = _extract_price_int(price_text or "")

                    # 상태/배송 텍스트(있으면)
                    condition = None
                    shipping = None
                    meta_candidates = [
                        a.select_one("[data-testid='ItemStatus']"),
                        a.select_one("[data-testid='ItemShipping']"),
                        a.parent,
                    ]
                    for mc in meta_candidates:
                        if not mc:
                            continue
                        txt = _clean_text(mc)
                        # 너무 긴 텍스트는 제외
                        if "未使用" in txt or "傷" in txt or "汚れ" in txt:
                            condition = condition or txt
                        if "送料込" in txt or "送料込み" in txt or "着払い" in txt:
                            shipping = shipping or txt

                    # 가격이 없으면 스킵(추천/정렬이 어려움)
                    if price is None:
                        continue

                    listing = Listing(
                        title=title or "No title",
                        price_jpy=price,
                        condition=condition,
                        shipping=shipping,
                        url=url,
                        image_url=image_url,
                        seller=None,
                        sold=None,
                        likes=None,
                        description_snippet=None,
                    )
                    cards.append(listing)

    # 중복 제거(같은 URL)
    unique: dict[str, Listing] = {}
    for it in cards:
        unique[it.url] = it
    return list(unique.values())


# ──────────────────────────────────────────────────────────────────────────────
# 상세 페이지 파서 (선택적)
# ──────────────────────────────────────────────────────────────────────────────
def _parse_listing_detail(html: str, url: str) -> Listing:
    """
    단일 상세 페이지에서 Listing을 완성(가능한 필드 보강).
    """
    soup = BeautifulSoup(html, "lxml")

    # 타이틀
    title_el = soup.select_one("h1, [data-testid='ItemTitle']")
    title = _clean_text(title_el) if title_el else "No title"

    # 가격
    price_el = soup.select_one("[data-testid='Price'], [class*='price'], span:contains('¥')")
    price = _extract_price_int(_clean_text(price_el) if price_el else "")

    # 상태/배송
    condition = None
    shipping = None
    detail_text = _clean_text(soup)
    if "未使用" in detail_text or "傷" in detail_text or "汚れ" in detail_text:
        # 너무 길면 일부만 보관
        condition = detail_text[:120]
    if "送料込" in detail_text or "送料込み" in detail_text or "着払い" in detail_text:
        shipping = "送料込み" if "送料" in detail_text else None

    # 이미지(대표 1장)
    img = soup.select_one("img")
    image_url = img.get("src") if img and img.get("src") else None

    # 판매자 정보(가능한 경우)
    seller_name = None
    seller_rating = None
    sales_count = None
    seller_block = soup.find(string=re.compile("出品者|評価|出品数"))  # heuristics
    if seller_block:
        # 아주 단순한 휴리스틱
        near = seller_block.parent
        txt = _clean_text(near) if near else ""
        # rating 4.8 같은 숫자 추출 시도
        m = re.search(r"(\d\.\d)\s*/\s*5", txt)
        if m:
            try:
                seller_rating = float(m.group(1))
            except Exception:  # noqa: BLE001
                seller_rating = None
        m2 = re.search(r"出品数\s*:?(\d+)", txt)
        if m2:
            try:
                sales_count = int(m2.group(1))
            except Exception:  # noqa: BLE001
                sales_count = None

    listing = Listing(
        title=title,
        price_jpy=price or 0,
        condition=condition,
        shipping=shipping,
        url=url,
        image_url=image_url,
        seller=SellerInfo(name=seller_name, rating=seller_rating, sales_count=sales_count),
        sold=None,
        likes=None,
        description_snippet=None,
    )
    return listing


# ──────────────────────────────────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────────────────────────────────
def search(session: Optional[requests.Session], q: SearchQuery) -> List[Listing]:
    """
    키워드 기반 검색 → Listing 목록 반환.
    - 서버 필터가 불확실하므로 client-side에서 budget/brand/color/condition을 2차 필터링.
    """
    url = build_search_url(q)
    owns_session = False
    if session is None:
        session = requests.Session()
        owns_session = True

    try:
        resp = _request(session, url)
        soup = BeautifulSoup(resp.text, "lxml")
        items = _parse_listing_cards(soup)

        # 클라이언트 사이드 필터링 (best-effort)
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

        # 간단 정렬 (best-effort)
        if q.sort == "price_asc":
            items.sort(key=lambda x: x.price_jpy)
        elif q.sort == "price_desc":
            items.sort(key=lambda x: x.price_jpy, reverse=True)
        elif q.sort == "new":
            # 신상 기준 정보가 없으므로 일단 상단 결과 유지
            pass
        else:
            # relevance: 검색 결과 순서를 그대로 둔다
            pass

        # limit 적용 (안전상 최대 100)
        limit = max(1, min(100, q.limit))
        return items[:limit]

    finally:
        if owns_session:
            session.close()


def fetch_detail(session: Optional[requests.Session], url: str) -> Listing:
    """
    단일 상세 정보 요청.
    """
    owns_session = False
    if session is None:
        session = requests.Session()
        owns_session = True

    try:
        resp = _request(session, url, params=None)
        return _parse_listing_detail(resp.text, url)
    finally:
        if owns_session:
            session.close()
