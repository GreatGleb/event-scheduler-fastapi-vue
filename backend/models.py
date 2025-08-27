from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.types import DateTime
from database import Base
import enum

class EventStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    event_time = Column(DateTime(timezone=True))
    status = Column(SQLAlchemyEnum(EventStatus), default=EventStatus.PENDING)