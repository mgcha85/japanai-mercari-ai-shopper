from __future__ import annotations

import logging

from fastapi import FastAPI, Body
from pydantic import BaseModel

from mercari_ai_shopper.models.query import SearchQuery
from mercari_ai_shopper.models.recommendation import RecommendationResponse
from mercari_ai_shopper.scraping.mercari_client import search as http_search
from mercari_ai_shopper.scraping.mercari_playwright import search_playwright
from mercari_ai_shopper.agent.reasoning import rank_and_explain

logger = logging.getLogger(__name__)
app = FastAPI(title="Mercari AI Shopper", version="0.1.0")


class SearchRequest(BaseModel):
    """간단한 구조화 입력. LLM을 거치지 않아도 테스트 가능."""
    query: SearchQuery
    top_k: int = 3
    engine: str = "http"  # "http" | "playwright"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search", response_model=RecommendationResponse)
def search_endpoint(req: SearchRequest = Body(...)) -> RecommendationResponse:
    if req.engine == "playwright":
        items = search_playwright(req.query)
    else:
        items = http_search(None, req.query)

    ranked = rank_and_explain(items, req.query, top_k=req.top_k)
    return RecommendationResponse(query=req.query, top_k=req.top_k, items=ranked)
