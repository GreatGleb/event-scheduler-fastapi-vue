from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from pydantic import BaseModel
from datetime import datetime
from typing import List

import models
from database import engine, get_db
from models import Event, EventStatus

app = FastAPI()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


class EventCreate(BaseModel):
    title: str
    description: str
    event_time: datetime


class EventOut(BaseModel):
    id: int
    title: str
    description: str
    event_time: datetime
    status: EventStatus

    class Config:
        from_attributes = True



@app.post("/api/events", response_model=EventOut)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    db_event = models.Event(**event.dict())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


@app.get("/api/events", response_model=List[EventOut])
async def read_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Event).offset(skip).limit(limit))
    events = result.scalars().all()
    return events


@app.patch("/api/events/{event_id}", response_model=EventOut)
async def update_event_status(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    db_event = result.scalar_one_or_none()

    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    db_event.status = EventStatus.COMPLETED
    await db.commit()
    await db.refresh(db_event)

    return db_event