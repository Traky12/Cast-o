# -*- coding: utf-8 -*-
"""Celery app para tareas asíncronas (certificaciones, IoT, webhooks)."""
from __future__ import annotations

import os
from celery import Celery

app = Celery(
    "backend",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["backend.tasks_worker"],
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
)
