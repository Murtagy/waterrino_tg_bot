import datetime
import json

from pydantic import BaseModel as BM
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer

from db import BaseModel, TableCreatedAt, TableId


class UserSettings(BM):
    start_time: datetime.time = datetime.time(hour=9)
    end_time: datetime.time = datetime.time(hour=21)
    daynorm: int = 2000
    utc_offset: int = 3
    skip_notification_days: list[int] = [6, 7]


class User(BaseModel):
    __tablename__ = "users"

    user_id = Column(Integer, index=True, unique=True, primary_key=True)
    chat_id = Column(Integer)
    created_at = TableCreatedAt()
    enabled = Column(Boolean, nullable=False)  # notify or not
    settings = Column(
        JSON, nullable=False
    )

    def get_settings(self) -> UserSettings:
        return UserSettings(**self.settings)


class Drink(BaseModel):
    __tablename__ = "drinks"

    drink_id = TableId()
    created_at = TableCreatedAt()
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    mililitres = Column(Integer, nullable=False)
