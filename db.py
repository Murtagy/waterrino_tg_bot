import datetime
from typing import Generator, Optional, Type, TypeVar

from sqlalchemy import Column, DateTime, Integer, create_engine

# from sqlalchemy.orm import declarative_base  # 2.0 style
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

engine = create_async_engine(
    "sqlite+aiosqlite:///./sql_app.db",
    connect_args={"check_same_thread": False},
    future=True,
)
sync_engine = create_engine(
    "sqlite:///./sql_app.db", connect_args={"check_same_thread": False}, future=True
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
BaseModel = declarative_base()


def TableId() -> Column[Integer]:
    return Column(Integer, primary_key=True, index=True, unique=True)


def TableCreatedAt() -> Column[DateTime]:
    return Column(DateTime(timezone=True), default=func.now())
