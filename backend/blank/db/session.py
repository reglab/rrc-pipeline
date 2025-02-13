import urllib.parse

import rl.utils.io
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


def get_postgres_uri(
    postgres_host: str = rl.utils.io.getenv("BLANK_PG_HOST"),
    postgres_port: str = rl.utils.io.getenv("BLANK_PG_PORT"),
    postgres_user: str = rl.utils.io.getenv("BLANK_PG_USER"),
    postgres_password: str = rl.utils.io.getenv("BLANK_PG_PASSWORD"),
    postgres_db: str = rl.utils.io.getenv("BLANK_PG_DB"),
):
    if any(
        [
            not postgres_host,
            not postgres_port,
            not postgres_user,
            not postgres_db,
        ]
    ):
        raise ValueError(
            "You must provide env variables BLANK_PG_HOST, BLANK_PG_PORT, "
            "BLANK_PG_USER, BLANK_PG_DB, and probably BLANK_PG_PASSWORD."
        )

    postgres_password = urllib.parse.quote_plus(postgres_password or "")
    return (
        f"postgresql://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}"
    )


def get_engine(
    **uri_kwargs,
):
    return sa.create_engine(
        get_postgres_uri(**uri_kwargs),
        echo=rl.utils.io.getenv("SA_ECHO", "false").lower() == "true",
        pool_size=int(rl.utils.io.getenv("SA_POOL_SIZE", "20")),
        max_overflow=int(rl.utils.io.getenv("SA_MAX_OVERFLOW", "30")),
    )


def new_session(
    **engine_kwargs,
):
    engine = get_engine(**engine_kwargs)
    return sessionmaker(bind=engine)()
