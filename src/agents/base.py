# src/agents/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import os
from openai import OpenAI


@dataclass
class LLMConfig:
    model: str = "gpt-4o-mini"   # 你可以改成你有的 model
    temperature: float = 0.3


class LLMAgent:
    """
    通用的 LLM Agent：
    - 每個 Agent 有自己的 system prompt（角色與任務）
    - 用同一個 OpenAI client 發 request
    """

    def __init__(self, name: str, system_prompt: str, config: LLMConfig | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.config = config or LLMConfig()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def run(self, messages: List[Dict[str, Any]]) -> str:
        """
        messages: 不包含 system；這裡會自動加上 system prompt。
        """
        full_messages = [
            {"role": "system", "content": self.system_prompt},
        ] + messages

        resp = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            messages=full_messages,
        )
        return resp.choices[0].message.content or ""
