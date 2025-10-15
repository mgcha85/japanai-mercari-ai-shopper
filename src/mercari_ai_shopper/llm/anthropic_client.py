from __future__ import annotations

import os
from typing import Dict, Any, List, Callable

# anthropic SDK
try:
    import anthropic
except Exception:  # noqa: BLE001
    anthropic = None  # type: ignore[assignment]


class AnthropicClient:
    """
    Anthropic tool-use 루프 (Claude 3.5 Sonnet 등).
    - Anthropic는 OpenAI와 message 포맷이 다르므로 변환 어댑터를 둔다.
    """

    def __init__(self, model: str = None):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in environment.")
        if anthropic is None:
            raise RuntimeError("anthropic SDK is not available. Please install 'anthropic' package.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

    @staticmethod
    def _convert_to_anthropic_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        OpenAI 스타일 messages → Anthropic input 변환.
        - system은 별도 system 매개로
        - tool 메시지는 'tool_result'로
        """
        converted: List[Dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "system":
                # system은 별도 처리하므로 skip
                continue
            elif role == "user":
                converted.append({"role": "user", "content": m.get("content", "")})
            elif role == "assistant":
                # assistant가 tool_call을 제안하는 경우 Anthropic에서 자동으로 tool 사용 의도를 내보냄
                converted.append({"role": "assistant", "content": m.get("content", "")})
            elif role == "tool":
                # Anthropic 포맷: tool_result
                converted.append(
                    {
                        "role": "tool",
                        "content": m.get("content", ""),
                        "name": m.get("name"),
                        "tool_use_id": m.get("tool_call_id"),
                    }
                )
        return converted

    def run_loop(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_registry: Dict[str, Callable[[Dict[str, Any]], Any]],
        max_steps: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Anthropic tool-use 메시지 루프.
        - 단순화를 위해 최대 max_steps까지만 반복.
        """
        # system 추출
        system_texts = [m["content"] for m in messages if m.get("role") == "system"]
        system_prompt = "\n".join(system_texts) if system_texts else None

        converted = self._convert_to_anthropic_messages(messages)

        for _ in range(max_steps):
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.3,
                system=system_prompt,
                messages=converted,
                tools=[{"name": t["name"], "description": t.get("description", ""), "input_schema": t["parameters"]} for t in tools],
            )

            # Claude 응답 파싱
            # resp.content는 block들의 리스트 (text/tool_use 등)
            assistant_msg = {"role": "assistant", "content": "", "tool_calls": []}
            tool_uses = []
            text_chunks = []
            for block in resp.content:
                if block.type == "tool_use":
                    tool_uses.append(block)
                elif block.type == "text":
                    text_chunks.append(block.text or "")

            assistant_msg["content"] = "\n".join(text_chunks).strip()
            converted.append({"role": "assistant", "content": assistant_msg["content"]})

            if not tool_uses:
                # 최종 텍스트 응답
                messages.append(assistant_msg)
                break

            # 각 tool_use 실행하고 tool_result 추가
            for tu in tool_uses:
                name = tu.name
                args = tu.input or {}
                if name not in tool_registry:
                    output = {"error": f"Tool '{name}' not implemented"}
                else:
                    try:
                        output = {"ok": True, "result": tool_registry[name](args)}
                    except Exception as e:  # noqa: BLE001
                        output = {"ok": False, "error": str(e)}

                # Anthropic 형식의 tool_result
                converted.append(
                    {
                        "role": "tool",
                        "tool_use_id": tu.id,
                        "content": str(output),
                        "name": name,
                    }
                )

        return messages
