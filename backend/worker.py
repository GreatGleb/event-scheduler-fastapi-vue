import asyncio
import greenstalk
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import concurrent.futures

from models import Event, EventStatus
from database import DATABASE_URL

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


async def mark_event_as_completed(event_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                update(Event)
                .where(Event.id == event_id)
                .values(status=EventStatus.COMPLETED)
            )
        print(f"Event {event_id} marked as completed.")


async def main():
    print("Worker started... Waiting for jobs.")
    queue = greenstalk.Client(('beanstalkd', 11300))
    loop = asyncio.get_running_loop()

    while True:
        try:
            job = await loop.run_in_executor(executor, queue.reserve)

            event_id = int(job.body)
            print(f"Processing job for event ID: {event_id}")

            await asyncio.sleep(10)

            await mark_event_as_completed(event_id)

            await loop.run_in_executor(executor, queue.delete, job)
            print(f"Job for event {event_id} deleted.")

        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        executor.shutdown(wait=False)