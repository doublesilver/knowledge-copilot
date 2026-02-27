from __future__ import annotations

from .. import db


def get_metrics(project_id: str | None = None) -> dict[str, float | int | None]:
    return db.metric_snapshot(project_id)
