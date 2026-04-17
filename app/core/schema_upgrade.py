from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def apply_lightweight_schema_upgrades(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "sources" in table_names:
        _upgrade_sources_table(engine, inspector)


def _upgrade_sources_table(engine: Engine, inspector) -> None:
    existing_columns = {item["name"] for item in inspector.get_columns("sources")}
    dialect_name = engine.dialect.name

    statements: list[str] = []
    if "last_crawled_at" not in existing_columns:
        statements.append("ALTER TABLE sources ADD COLUMN last_crawled_at DATETIME NULL")
    if "last_crawl_status" not in existing_columns:
        statements.append("ALTER TABLE sources ADD COLUMN last_crawl_status VARCHAR(32) NULL")
    if "consecutive_failures" not in existing_columns:
        statements.append("ALTER TABLE sources ADD COLUMN consecutive_failures INTEGER NOT NULL DEFAULT 0")
    if "last_crawl_error" not in existing_columns:
        column_type = "LONGTEXT" if dialect_name == "mysql" else "TEXT"
        statements.append(f"ALTER TABLE sources ADD COLUMN last_crawl_error {column_type} NULL")
    if "last_crawl_processed_count" not in existing_columns:
        statements.append("ALTER TABLE sources ADD COLUMN last_crawl_processed_count INTEGER NOT NULL DEFAULT 0")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
