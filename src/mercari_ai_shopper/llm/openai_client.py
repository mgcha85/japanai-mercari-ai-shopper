from __future__ import annotations

import os
from typing import Dict, Any, List, Callable, Optional

# OpenAI SDK는 requirements에 포함되어 있음
try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]


class OpenAIClient:
    """
    OpenAI function-calling 루프.
    - messages: [{"role": "system"|"user"|"assistant"|"tool", "content": "..."}]
    - tools: function schema list
    - tool_registry: {"tool_name": callable}
    """

    def __init__(self, model: str = None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment.")
        if OpenAI is None:
            raise RuntimeError("openai SDK is not available. Please install 'openai' package.")
        self.client = OpenAI(api_key=api_key)
        # gpt-4o / gpt-4.1 / o3-mini 등 최신 모델 환경에 맞게 교체 가능
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def run_loop(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_registry: Dict[str, Callable[[Dict[str, Any]], Any]],
        max_steps: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        function-calling을 수행하고, 필요 시 tool 호출 → 결과를 대화에 append.
        최종 assistant 메시지가 나오면 종료.
        """
        for _ in range(max_steps):
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[{"type": "function", "function": t} for t in tools],
                tool_choice="auto",
                temperature=0.3,
            )
            choice = resp.choices[0]
            msg = choice.message
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

            # tool_calls가 없으면 최종 답변으로 간주
            if not msg.tool_calls:
                break

            # 여러 개의 도구 호출을 순차 처리
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = tc.function.arguments
                if fn_name not in tool_registry:
                    tool_output = {"error": f"Tool '{fn_name}' not implemented"}
                else:
                    # JSON 문자열 → dict 파싱은 SDK가 해주거나 직접 처리 필요
                    import json
                    try:
                        parsed = json.loads(fn_args or "{}")
                    except Exception:
                        parsed = {}
                    try:
                        result = tool_registry[fn_name](parsed)
                        tool_output = {"ok": True, "result": result}
                    except Exception as e:  # noqa: BLE001
                        tool_output = {"ok": False, "error": str(e)}
                # tool 결과를 assistant에게 전달
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": str(tool_output),
                    }
                )

        return messages
