import anthropic
import os
from typing import List, Dict, Any


class AnthropicClient:
    def __init__(self, model: str | None = None, max_tokens: int = 1024):
        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
        self.max_tokens = max_tokens
        
    def _to_anthropic_tools(self, tools):
        """
        Normalize tool schema to Anthropic format: [{"name","description","input_schema"}...]
        Supports:
        - OpenAI: {"type":"function","function":{"name","description","parameters"}}
        - Flat:   {"name","description","parameters"}
        - Native: {"name","description","input_schema"}
        """
        anth_tools = []
        for t in (tools or []):
            if "function" in t:  # OpenAI-style wrapper
                fn = t["function"]
                anth_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object"}),
                })
            elif "parameters" in t:  # our flat/OpenAI-like
                anth_tools.append({
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object"}),
                })
            else:  # assume Anthropic-native
                # ensure input_schema exists
                schema = t.get("input_schema")
                if not schema:
                    raise ValueError(f"Anthropic tool '{t.get('name','<no-name>')}' missing input_schema")
                anth_tools.append({
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": schema,
                })
        return anth_tools
    
    def run_loop(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                 tool_registry, max_steps: int = 2):
        """
        messages: [{"role":"user"|"assistant", "content":[{"type":"text","text":...}, ...]}]
        tools: Anthropic 'tools' 스키마 (name/description/input_schema)
        """

        # 초기 호출 (user 메시지 + tools)
        for step in range(max_steps):
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,             # role: user/assistant only
                tools=self._to_anthropic_tools(tools)  # <-- 여기
            )
            # Anthropic SDK 응답은 resp.content = [blocks...], resp.stop_reason 등 포함
            assistant_msg = {
                "role": "assistant",
                "content": resp.content,
            }
            messages.append(assistant_msg)

            # tool_use 요청이 없으면 종료
            tool_uses = [b for b in resp.content if b.get("type") == "tool_use"]
            if not tool_uses:
                break

            # (1) 각 tool_use 실행
            tool_results_blocks = []
            for tu in tool_uses:
                tool_name = tu["name"]
                tool_input = tu.get("input", {})
                tool_use_id = tu["id"]

                # 실제 도구 실행
                result = tool_registry.call(tool_name, tool_input)

                # (2) 결과를 user 메시지의 tool_result 블록으로 전달
                # 주의: role="tool" 아님! role="user" + content=[{"type":"tool_result", ...}]
                # 여기에 추가 텍스트를 넣고 싶다면 반드시 tool_result 뒤에 위치시켜야 함.
                # 예: [{"type":"tool_result", ...}, {"type":"text","text":"...next"}]
                block = {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result) if not isinstance(result, list) else result
                }
                tool_results_blocks.append(block)

            # 모든 결과를 "단일 user 메시지"로 한 번에 붙이기(병렬 도구 사용에 권장)
            messages.append({
                "role": "user",
                "content": tool_results_blocks
            })

        return messages
