from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)

from db import BaseModel, TableCreatedAt, TableId
from pydantic import BaseModel as BM

import datetime
import json


class UserSettings(BM):
    start_time: datetime.time
    end_time: datetime.time
    notify: bool
    daynorm: int


class User(BaseModel):
    __tablename__ = "users"

    user_id = Column(Integer, index=True, unique=True, primary_key=True)
    chat_id = Column(Integer)
    created_at = TableCreatedAt()
    enabled = Column(Boolean, nullable=False)
    settings = Column(JSON, nullable=False)

    def get_settings(self) -> UserSettings:
        return UserSettings(**json.loads(self.settings))


class Drink(BaseModel):
    __tablename__ = "drinks"

    drink_id = TableId()
    created_at = TableCreatedAt()
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    mililitres = Column(Integer, nullable=False)

