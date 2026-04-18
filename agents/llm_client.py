"""
LLM 客户端封装 - 统一管理与大模型的交互
"""
import os
import time
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """优先从 Streamlit secrets 读取，其次从环境变量读取"""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


class LLMClient:
    """大模型调用客户端"""

    def __init__(self):
        self.api_key = _get_secret("OPENAI_API_KEY", "")
        self.base_url = _get_secret("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = _get_secret("MODEL_NAME", "gpt-4o-mini")
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """调用大模型进行对话"""
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            if stream:
                return response  # 返回流式对象
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {str(e)}")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_openai_api_key_here")


# 全局单例
llm_client = LLMClient()
