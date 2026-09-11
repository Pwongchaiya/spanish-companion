"""Shared SQLAlchemy declarative base for api-layer models.

One Base/metadata per data-model-skill's "shared across all models" rule —
mirrors `rag/brokers/chunk_repository/chunk_repository_broker.py`'s `Base`
for the `rag` package. MistakePattern and TopicCovered (separate Broker
Agent tasks, same wave) import this same `Base` so their `profile_id`
foreign keys resolve against one metadata object as `learner_profile.id`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
