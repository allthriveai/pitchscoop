from typing import Dict, List, Literal, Any
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PitchScoop Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


class SetRoleRequest(BaseModel):
    user_id: str
    role: Literal["organizer", "individual"]


class SetRoleResponse(BaseModel):
    ok: bool


class UpsertEventRequest(BaseModel):
    event_id: str
    judges: List[str]
    rules: Dict[str, Any]
    goals: List[str]
    sponsor_tools: List[str]


class UpsertEventResponse(BaseModel):
    ok: bool


class LeaderboardResponse(BaseModel):
    leaderboard: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    ok: bool


@app.on_event("startup")
async def startup_event():
    await get_redis()


@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()


@app.get("/")
async def root():
    return {"message": "Hackathon MCP Backend", "docs": "/docs", "health": "/api/healthz"}


@app.get("/api/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(ok=True)


@app.post("/api/auth.set_role", response_model=SetRoleResponse)
async def set_role(request: SetRoleRequest):
    r = await get_redis()
    user_key = f"user:{request.user_id}"
    await r.hset(user_key, "role", request.role)
    return SetRoleResponse(ok=True)


@app.post("/api/events.upsert", response_model=UpsertEventResponse)
async def upsert_event(request: UpsertEventRequest):
    r = await get_redis()
    event_key = f"event:{request.event_id}"

    event_data = {
        "judges": json.dumps(request.judges),
        "rules": json.dumps(request.rules),
        "goals": json.dumps(request.goals),
        "sponsor_tools": json.dumps(request.sponsor_tools)
    }

    await r.hset(event_key, mapping=event_data)
    return UpsertEventResponse(ok=True)


@app.get("/api/leaderboard.generate", response_model=LeaderboardResponse)
async def generate_leaderboard(event_id: str = Query(...)):
    return LeaderboardResponse(leaderboard=[])