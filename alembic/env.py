"""Alembic environment.

Connection URL comes from DATABASE_URL via python-dotenv at runtime — never
hardcoded, never committed (see CLAUDE.md Environment Variables table).
"""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from rag.brokers.chunk_repository import Base

load_dotenv()

config = context.config

# pg8000 (the only driver in requirements.txt) needs an explicit "+pg8000"
# scheme — a bare "postgresql://" DATABASE_URL (as currently set in
# .env/.env.example) resolves to the psycopg2 dialect, which isn't
# installed. Normalized here rather than in .env(.example), which this
# migration wave doesn't own — see outbound notes.
database_url = os.environ["DATABASE_URL"]
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+pg8000://", 1)
# alembic.ini uses ConfigParser interpolation ("%(here)s") — escape a literal
# "%" (e.g. from a URL-encoded password) so set_main_option doesn't choke on it.
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
