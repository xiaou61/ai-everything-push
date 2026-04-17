from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.source import Source, SourceRule
from app.schemas.source_rule import SourceRuleUpsert


def get_rule_by_source(session: Session, source_id: int) -> Optional[SourceRule]:
    statement = select(SourceRule).where(SourceRule.source_id == source_id).limit(1)
    return session.scalar(statement)


def upsert_source_rule(session: Session, source: Source, payload: SourceRuleUpsert) -> SourceRule:
    rule = get_rule_by_source(session, source.id)
    data = payload.model_dump()
    if rule is None:
        rule = SourceRule(source_id=source.id, **data)
    else:
        for key, value in data.items():
            setattr(rule, key, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule

