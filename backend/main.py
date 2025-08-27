from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime
from typing import List
import httpx
import greenstalk

import models
from database import engine, get_db
from models import Event, EventStatus

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    try:
        async with httpx.AsyncClient() as client:
            await client.post("https://httpbin.org/post", json={
                "title": db_event.title,
                "datetime": db_event.event_time.isoformat()
            })
    except httpx.RequestError as exc:
        print(f"Error calling httpbin: {exc}")

    try:
        queue = greenstalk.Client(('beanstalkd', 11300))
        queue.put(str(db_event.id))
        queue.close()
    except Exception as e:
        print(f"Could not put job in queue: {e}")

    return db_event


@app.get("/api/events", response_model=List[EventOut])
async def read_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Event).offset(skip).limit(limit))
    return result.scalars().all()


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