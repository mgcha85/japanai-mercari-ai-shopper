from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

from .listing import Listing
from .query import SearchQuery


class RankedListing(BaseModel):
    """랭킹 점수와 추천 사유를 포함한 결과 단위."""

    listing: Listing
    score: float = Field(..., description="정규화된 점수(0~1 권장)")
    reasons: List[str] = Field(
        default_factory=list,
        description="설명 가능한 근거(예: '예산 근접', '미사용급', '정확한 색상 일치')",
    )


class RecommendationResponse(BaseModel):
    """최종 추천 응답(Top-N)."""

    query: SearchQuery
    top_k: int = Field(..., ge=1)
    items: List[RankedListing] = Field(
        ...,
        description="랭킹 순서 보장된 추천 목록",
        min_length=1,
    )
