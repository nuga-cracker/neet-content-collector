"""선택적 OpenAI 기반 AI 분석 모듈.

OPENAI_API_KEY 환경변수가 없거나 요청이 실패하면 None을 반환하며
전체 수집 흐름을 중단하지 않는다.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _get_client():
    """OpenAI 클라이언트를 반환한다. 패키지가 없거나 키가 없으면 None."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI  # noqa: PLC0415

        return OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("openai 패키지가 설치되어 있지 않습니다. AI 분석을 건너뜁니다.")
        return None


_SYSTEM_PROMPT = """\
당신은 니트족(NEET, 취업·교육·직업훈련에 참여하지 않는 청년층) 관련 뉴스를 분석하는 AI입니다.
주어진 기사 제목과 본문을 읽고 아래 형식의 JSON을 반환하세요.
절대로 JSON 이외의 텍스트를 출력하지 마세요.

{
  "summary": "2~3문장 한국어 요약",
  "tags": ["태그1", "태그2", "태그3"],
  "sentiment": "positive|neutral|negative"
}
"""


def analyze(title: str, body: str, model: str = "gpt-4o-mini") -> Optional[dict]:
    """기사를 AI로 분석하여 summary, tags, sentiment를 반환한다.

    실패 시 None을 반환하고 예외를 로그로 기록한다.
    """
    client = _get_client()
    if client is None:
        return None

    user_content = f"제목: {title}\n\n본문:\n{body[:1500]}"  # AI 비용 절감을 위해 2000자 미만으로 제한

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        raw = response.choices[0].message.content or ""
        result = json.loads(raw)
        # 기본값 보완
        return {
            "summary": str(result.get("summary", "")),
            "tags": result.get("tags", []),
            "sentiment": str(result.get("sentiment", "neutral")),
        }
    except json.JSONDecodeError as exc:
        logger.warning("AI 응답 JSON 파싱 실패: %s", exc)
    except Exception as exc:
        logger.warning("AI 분석 실패 (%s): %s", type(exc).__name__, exc)
    return None
