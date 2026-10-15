from fastapi import FastAPI
from models import user
from database import Base, engine

# router
from routers.users import router as users_router
from routers.seats import router as seats_router
from routers.events import router as events_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users_router)
app.include_router(seats_router)
app.include_router(events_router)