"""
Artifact storage.

Writes to Cloud Storage when GCS_BUCKET is set (the deployed path, PRD §9), and
to a local directory otherwise so the service is fully exercisable offline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
GCS_BUCKET = os.environ.get("GCS_BUCKET")


class Storage:
    def __init__(self) -> None:
        self._bucket = None
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if GCS_BUCKET:
            try:
                from google.cloud import storage as gcs  # lazy — optional dependency

                self._bucket = gcs.Client().bucket(GCS_BUCKET)
            except Exception as exc:  # noqa: BLE001 — deliberate degrade-to-local
                print(f"[notice] Cloud Storage unavailable ({exc}); writing locally.")

    @property
    def backend(self) -> str:
        return "gcs" if self._bucket else "local"

    def write(self, filename: str, data: bytes, content_type: str) -> str:
        """Persist an artifact and return a URI describing where it landed."""
        if self._bucket:
            blob = self._bucket.blob(f"notices/{filename}")
            blob.upload_from_string(data, content_type=content_type)
            return f"gs://{GCS_BUCKET}/notices/{filename}"

        path = OUTPUT_DIR / filename
        path.write_bytes(data)
        return str(path)

    def read(self, filename: str) -> Optional[bytes]:
        if self._bucket:
            blob = self._bucket.blob(f"notices/{filename}")
            return blob.download_as_bytes() if blob.exists() else None

        path = OUTPUT_DIR / filename
        return path.read_bytes() if path.is_file() else None

    def exists(self, filename: str) -> bool:
        if self._bucket:
            return self._bucket.blob(f"notices/{filename}").exists()
        return (OUTPUT_DIR / filename).is_file()


storage = Storage()
