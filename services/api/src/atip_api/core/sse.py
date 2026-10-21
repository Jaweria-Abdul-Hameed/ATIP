"""Server-Sent Events (SSE) formatting and stream helpers."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel, Field


class ServerSentEvent(BaseModel):
    event: str | None = Field(default=None, description="Event name/type")
    data: Any = Field(..., description="Payload data (dict, str, or Pydantic model)")
    id: str | None = Field(default=None, description="Unique event identifier")
    retry: int | None = Field(default=None, description="Reconnection delay in milliseconds")

    def encode(self) -> str:
        lines = []
        if self.id is not None:
            lines.append(f"id: {self.id}")
        if self.event is not None:
            lines.append(f"event: {self.event}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")

        if isinstance(self.data, (dict, list)):
            serialized = json.dumps(self.data)
        elif hasattr(self.data, "model_dump"):
            serialized = json.dumps(self.data.model_dump())
        else:
            serialized = str(self.data)

        # Multi-line data support
        for line in serialized.splitlines():
            lines.append(f"data: {line}")

        lines.append("\n")
        return "\n".join(lines)


async def sse_event_stream(
    generator: AsyncGenerator[ServerSentEvent, None],
) -> AsyncGenerator[str, None]:
    async for event in generator:
        yield event.encode()
