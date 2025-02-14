import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

import rrc.utils.io
from rrc.db.models import Base

DB_PATH = rrc.utils.io.get_data_path("rrc.db")


def get_engine():
    return sa.create_engine(
        f"sqlite:///{DB_PATH}",
        echo=rrc.utils.io.getenv("RRC_SA_ECHO", "false").lower() == "true",
    )


ENGINE = get_engine()


def init_db():
    if not DB_PATH.parent.exists():
        raise FileNotFoundError(
            f"Parent directory of database file {DB_PATH} does not exist. "
            f"You may need to mount an empty Docker volume on the path {DB_PATH.parent}"
        )
    Base.metadata.create_all(ENGINE)


def init_db_if_needed():
    if not DB_PATH.exists():
        init_db()


def get_session():
    init_db_if_needed()
    return sessionmaker(bind=ENGINE)()
