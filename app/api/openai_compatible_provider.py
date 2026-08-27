"""Server-only OpenAI-compatible adapter for bounded textbook QA generation."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Mapping

import httpx

from runtime import (
    ModelProviderInvalidResponseError,
    ModelProviderUnavailableError,
    ModelRequest,
    ModelResponse,
    ModelResponseValidationError,
)


_SYSTEM_MESSAGE = """你是教材问答模型。
只能依据用户消息中提供的当前问题、短期对话 history 和 evidence 数组回答；不得使用外部知识补全教材事实。
只能引用 evidence 数组中已经存在的 evidence_id，不得创建 source_id、页码、锚点或新的 evidence_id。
如果证据不足，设置 insufficient_evidence=true，并将 answer 设为 null、evidence_ids 设为空数组。
否则必须返回非空 answer，并至少引用一个提供的 evidence_id。
只返回一个 JSON 对象，字段必须且只能是 answer、evidence_ids、insufficient_evidence、answer_style；answer_style 只能取 brief、explain、compare、proof。"""


class OpenAICompatibleModelProvider:
    """Call a server-configured OpenAI-compatible chat/completions endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self._api_key = api_key.strip()
        if not self.base_url or not self._api_key or not self.model:
            raise ValueError("OpenAI-compatible provider configuration must be non-blank")
        if self.timeout_seconds <= 0:
            raise ValueError("OpenAI-compatible provider timeout must be positive")

    def answer(self, request: ModelRequest) -> ModelResponse:
        body = self._request_body(request)
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                for attempt in range(2):
                    try:
                        response = client.post(endpoint, headers=headers, json=body)
                        response.raise_for_status()
                    except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                        raise ModelProviderUnavailableError(
                            "Model provider is unavailable"
                        ) from None

                    try:
                        return self._parse_response(response)
                    except (ValueError, KeyError, IndexError, TypeError, ModelResponseValidationError):
                        if attempt == 0:
                            continue
                        raise ModelProviderInvalidResponseError(
                            "Model provider returned an invalid structured response"
                        ) from None
        except ModelProviderUnavailableError:
            raise
        except ModelProviderInvalidResponseError:
            raise
        except (httpx.TimeoutException, httpx.TransportError):
            raise ModelProviderUnavailableError("Model provider is unavailable") from None

        raise ModelProviderInvalidResponseError(
            "Model provider returned an invalid structured response"
        )

    @staticmethod
    def _request_body(request: ModelRequest) -> dict[str, object]:
        user_payload = {
            "question": request.question,
            "course_id": request.course_id,
            "book_id": request.book_id,
            "section_id": request.section_id,
            "history": [asdict(message) for message in request.history],
            "evidence": [asdict(item) for item in request.evidence],
            "allowed_answer_styles": list(request.allowed_answer_styles),
        }
        return {
            "model": None,
            "messages": [
                {"role": "system", "content": _SYSTEM_MESSAGE},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            "response_format": {"type": "json_object"},
        }

    def _parse_response(self, response: httpx.Response) -> ModelResponse:
        envelope = response.json()
        if not isinstance(envelope, Mapping):
            raise ValueError("Invalid upstream response envelope")
        choices = envelope["choices"]
        if not isinstance(choices, list) or not choices:
            raise ValueError("Invalid upstream choices")
        first = choices[0]
        if not isinstance(first, Mapping):
            raise ValueError("Invalid upstream choice")
        message = first["message"]
        if not isinstance(message, Mapping):
            raise ValueError("Invalid upstream message")
        content = message["content"]
        if not isinstance(content, str):
            raise ValueError("Invalid upstream content")
        parsed = json.loads(content)
        return ModelResponse.from_mapping(parsed)

    def _request_body(self, request: ModelRequest) -> dict[str, object]:
        body = self.__class__._request_body.__func__(request)  # type: ignore[attr-defined]
        body["model"] = self.model
        return body
