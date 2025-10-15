from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# 정렬 옵션(머카리 UI에 맞춘 합리적 가정)
SortOption = Literal["relevance", "price_asc", "price_desc", "new"]

# 머카리 대표 상태 라벨(일본어 원문 유지: 파싱 일관성↑)
# - 필요 시 utils.text에서 ko/en → ja 매핑
MERCARI_CONDITION_WHITELIST = {
    "新品、未使用",
    "未使用に近い",
    "目立った傷や汚れなし",
    "やや傷や汚れあり",
    "傷や汚れあり",
    "全体的に状態が悪い",
}


class SearchQuery(BaseModel):
    """LLM이 사용자 자연어를 구조화한 검색 질의(툴 호출 파라미터)."""

    raw_text: str = Field(..., description="원본 사용자 입력")
    keywords: List[str] = Field(..., min_length=1, description="검색 키워드(일본어 권장)")
    budget_min: Optional[int] = Field(None, ge=0, description="최소 예산(JPY)")
    budget_max: Optional[int] = Field(None, ge=0, description="최대 예산(JPY)")
    condition: List[str] = Field(
        default_factory=list,
        description="머카리 상태(ja). 예: ['未使用に近い', '目立った傷や汚れなし']",
    )
    brand: List[str] = Field(default_factory=list, description="브랜드 필터")
    color: List[str] = Field(default_factory=list, description="색상 키워드")
    category: Optional[str] = Field(
        None, description="카테고리 라벨(자유 텍스트, 필요 시 정규화)"
    )
    sort: SortOption = Field(
        "relevance",
        description="정렬 옵션: relevance | price_asc | price_desc | new",
    )
    limit: int = Field(30, ge=1, le=100, description="최대 검색 개수(안전상 100 제한)")

    @field_validator("condition")
    @classmethod
    def _only_known_conditions(cls, v: List[str]) -> List[str]:
        """머카리 표준 라벨만 허용(빈 리스트면 필터 미사용)."""
        if not v:
            return v
        filtered = [c for c in v if c in MERCARI_CONDITION_WHITELIST]
        return filtered

    @field_validator("budget_max")
    @classmethod
    def _budget_range_check(cls, vmax: Optional[int], info):
        vmin = info.data.get("budget_min")
        if vmax is not None and vmin is not None and vmax < vmin:
            raise ValueError("budget_max must be >= budget_min")
        return vmax
