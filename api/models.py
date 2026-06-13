"""Pydantic response models shared across API routes."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db: str
