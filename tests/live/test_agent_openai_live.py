import os
import pytest
from mercari_ai_shopper.agent.agent import Agent

pytestmark = pytest.mark.skipif(os.getenv("LIVE_LLM") != "1", reason="Set LIVE_LLM=1")

def test_openai_live_tool_call_and_text_output():
    # 전제: .env에 OPENAI_API_KEY, (선택) LLM_PROVIDER=openai
    a = Agent()
    msgs = a.run("ニンテンドー スイッチ OLED ホワイト 30000円 以下 おすすめ", max_steps=2)

    # LLM이 실제로 tool을 호출했는가?
    assert any(m.get("tool_calls") for m in msgs if m.get("role") == "assistant")

    # 최종 응답 텍스트가 비어있지 않은가?
    final = msgs[-1].get("content", "")
    assert isinstance(final, str) and len(final) > 0
