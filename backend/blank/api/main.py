from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from blank.api.interfaces import (
    ProxyPatternCreate,
    ProxyPatternRead,
    ProxyPatternUpdate,
)
from blank.db.models import (
    ProxyPattern,
)
from blank.db.session import new_session

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# region Dependencies


def get_db() -> Session:
    session = new_session()
    try:
        yield session
    finally:
        session.close()


def get_proxy_pattern(
    db: Annotated[Session, Depends(get_db)], pattern_id: int
) -> ProxyPattern:
    proxy_pattern = db.get(ProxyPattern, pattern_id)
    if not proxy_pattern:
        raise HTTPException(status_code=404, detail="Proxy pattern not found")
    return proxy_pattern


# endregion


@app.get(
    "/proxy_patterns",
    response_model=list[ProxyPatternRead],
    operation_id="listProxyPatterns",
)
def list_proxy_patterns(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(ProxyPattern)).all()


@app.post(
    "/proxy_patterns",
    response_model=ProxyPatternRead,
    operation_id="createProxyPattern",
)
def create_proxy_pattern(
    pattern: ProxyPatternCreate, db: Annotated[Session, Depends(get_db)]
):
    db_pattern = ProxyPattern(**pattern.model_dump())
    db.add(db_pattern)
    db.commit()
    db.refresh(db_pattern)
    return db_pattern


@app.get(
    "/proxy_patterns/{pattern_id}",
    response_model=ProxyPatternRead,
    operation_id="readProxyPattern",
)
def read_proxy_pattern(
    proxy_pattern: Annotated[ProxyPattern, Depends(get_proxy_pattern)],
):
    return proxy_pattern


@app.patch(
    "/proxy_patterns/{pattern_id}",
    response_model=ProxyPatternRead,
    operation_id="updateProxyPattern",
)
def update_proxy_pattern(
    pattern_update: ProxyPatternUpdate,
    proxy_pattern: Annotated[ProxyPattern, Depends(get_proxy_pattern)],
    db: Annotated[Session, Depends(get_db)],
):
    for field, value in pattern_update.model_dump(exclude_unset=True).items():
        setattr(proxy_pattern, field, value)

    db.commit()
    db.refresh(proxy_pattern)
    return proxy_pattern


@app.delete(
    "/proxy_patterns/{pattern_id}",
    status_code=204,
    operation_id="deleteProxyPattern",
)
def delete_proxy_pattern(
    proxy_pattern: Annotated[ProxyPattern, Depends(get_proxy_pattern)],
    db: Annotated[Session, Depends(get_db)],
):
    db.delete(proxy_pattern)
    db.commit()
