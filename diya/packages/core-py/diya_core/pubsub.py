"""
Pub/Sub ingestion.

Department feeds arrive asynchronously on a topic rather than being pushed
synchronously into the API (PRD §9: "handle heavy lifting asynchronously").
Malformed messages go to a dead-letter topic instead of being silently dropped
(PRD §10).

Without GOOGLE_CLOUD_PROJECT set this degrades to a local no-op publisher that
records what it would have sent, so the ingestion path is exercisable offline.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

TOPIC_DEPARTMENT_FEED = os.environ.get("PUBSUB_TOPIC_FEED", "diya-department-feed")
TOPIC_DEAD_LETTER = os.environ.get("PUBSUB_TOPIC_DLQ", "diya-department-feed-dlq")


class Publisher:
    """Publishes ingestion messages, or records them locally when GCP is absent."""

    def __init__(self, project: Optional[str] = None) -> None:
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._client = None
        self.local_log: list[dict[str, Any]] = []

        if self.project:
            try:
                from google.cloud import pubsub_v1  # lazy — optional dependency

                self._client = pubsub_v1.PublisherClient()
            except Exception as exc:  # noqa: BLE001 — deliberate degrade-to-local
                print(f"[diya_core] Pub/Sub unavailable ({exc}); publishing locally.")

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _topic_path(self, topic: str) -> str:
        return f"projects/{self.project}/topics/{topic}"

    def publish(self, topic: str, message: dict[str, Any]) -> str:
        payload = json.dumps(message).encode("utf-8")

        if not self._client:
            record = {"topic": topic, "message": message, "mode": "local"}
            self.local_log.append(record)
            del self.local_log[:-200]
            return f"local-{len(self.local_log)}"

        future = self._client.publish(self._topic_path(topic), payload)
        return future.result(timeout=10)

    def publish_department_feed(self, dept_id: str, works: list[dict]) -> str:
        return self.publish(
            TOPIC_DEPARTMENT_FEED,
            {"deptId": dept_id, "recordCount": len(works), "works": works},
        )

    def publish_dead_letter(self, reason: str, raw: Any) -> str:
        return self.publish(TOPIC_DEAD_LETTER, {"reason": reason, "raw": repr(raw)})


_publisher: Optional[Publisher] = None


def get_publisher() -> Publisher:
    global _publisher
    if _publisher is None:
        _publisher = Publisher()
    return _publisher
