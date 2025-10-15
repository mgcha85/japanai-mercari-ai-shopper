from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class SellerInfo(BaseModel):
    name: Optional[str] = Field(None, description="판매자 닉네임")
    rating: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="판매자 평점(0~5, 가용 시)"
    )
    sales_count: Optional[int] = Field(
        None, ge=0, description="거래(판매) 횟수(가용 시)"
    )


class Listing(BaseModel):
    """머카리 검색/상세 결과의 핵심 상품 엔티티."""

    title: str = Field(..., description="상품 제목")
    price_jpy: int = Field(..., ge=0, description="가격(JPY)")
    condition: Optional[str] = Field(
        None,
        description="상품 상태(ja 원문 유지: '未使用に近い' 등)",
    )
    shipping: Optional[str] = Field(
        None, description="배송 정보(送料込み/着払い 등, 원문 보존)"
    )
    url: HttpUrl = Field(..., description="상품 상세 페이지 URL")
    image_url: Optional[HttpUrl] = Field(None, description="대표 이미지 URL")
    seller: Optional[SellerInfo] = Field(None, description="판매자 정보(옵션)")
    sold: Optional[bool] = Field(
        None, description="판매 완료 여부(가용 시 true/false)"
    )
    likes: Optional[int] = Field(None, ge=0, description="좋아요 수(가용 시)")
    description_snippet: Optional[str] = Field(
        None, description="상세 페이지 일부 또는 요약(옵션)"
    )

    @field_validator("title")
    @classmethod
    def _normalize_title(cls, v: str) -> str:
        return v.strip()

    @field_validator("condition")
    @classmethod
    def _normalize_condition(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v
