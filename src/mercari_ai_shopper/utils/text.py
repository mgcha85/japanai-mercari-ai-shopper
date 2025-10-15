from __future__ import annotations

import re
from typing import List


def normalize_keywords(raw_text: str) -> List[str]:
    """
    아주 단순한 규칙 기반 키워드 추출/정규화.
    - 불필요한 기호 제거
    - 공백/쉼표 기준 토큰
    - 2자 이상 토큰만
    """
    s = re.sub(r"[^\w\s\-]+", " ", raw_text)
    toks = [t.strip() for t in re.split(r"[\s,]+", s) if len(t.strip()) >= 2]
    return list(dict.fromkeys(toks))  # 순서 유지 중복 제거
