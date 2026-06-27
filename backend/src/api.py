from datetime import date
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from db import database_manager
from config import now_local

app = FastAPI(title="SchedBot API", version="1.0.0")


class UserCreate(BaseModel):
    tg_id: int


class UserResponse(BaseModel):
    id: int
    tg_id: int
    group_id: Optional[int]
    is_admin: bool


class GroupResponse(BaseModel):
    id: int
    name: str


class LessonResponse(BaseModel):
    lesson_number: int
    lesson_type: str
    lesson_start_time: str
    lesson_end_time: str
    subject_name: str


class AuditoriumResponse(BaseModel):
    name: str
    number: str
    building: str
    floor: int
    capacity: Optional[int]
    type: str


class UserStatsResponse(BaseModel):
    total_lessons: int
    lectures: int
    practices: int
    labs: int
    workload_by_day: Dict[str, int]


class EngagementStatsResponse(BaseModel):
    dau: int
    wau: int
    mau: int


class CommandStatsResponse(BaseModel):
    command: str
    count: int


class UserActionCreate(BaseModel):
    user_id: int
    action_type: str
    command_name: Optional[str] = None
    metadata: Optional[dict] = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    user_id = database_manager.create_user(tg_id=user.tg_id)
    created_user = database_manager.get_user_by_tg_id(user.tg_id)
    if not created_user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    database_manager.log_user_action(
        user_id=created_user.id,
        action_type="REGISTRATION",
        command_name=None,
        metadata=None
    )

    return {
        "id": created_user.id,
        "tg_id": created_user.tg_id,
        "group_id": created_user.group_id,
        "is_admin": created_user.is_admin
    }


@app.get("/users/{tg_id}", response_model=UserResponse)
async def get_user(tg_id: int):
    user = database_manager.get_user_by_tg_id(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "tg_id": user.tg_id,
        "group_id": user.group_id,
        "is_admin": user.is_admin
    }


@app.put("/users/{tg_id}")
async def attach_user_to_group(tg_id: int, group_name: str):
    database_manager.attach_user_to_group(tg_id, group_name)

    user = database_manager.get_user_by_tg_id(tg_id)
    if user:
        database_manager.log_user_action(
            user_id=user.id,
            action_type="GROUP_CHANGE",
            command_name=None,
            metadata={"group_name": group_name}
        )

    return {"status": "success"}


@app.get("/groups", response_model=List[GroupResponse])
async def get_groups():
    groups = database_manager.get_groups()
    return [{"id": g.id, "name": g.name} for g in groups]


@app.get("/lessons/date/{tg_id}", response_model=List[LessonResponse])
async def get_lessons_by_date(
    tg_id: int,
    search_date: Optional[date] = Query(None)
):
    if search_date is None:
        search_date = now_local().date()

    user = database_manager.get_user_by_tg_id(tg_id)
    if user:
        database_manager.log_user_action(
            user_id=user.id,
            action_type="API_CALL",
            command_name="get_lessons_by_date",
            metadata={"search_date": str(search_date)}
        )

    lessons = database_manager.get_user_lessons_on_date(tg_id, search_date)
    if not lessons:
        return []
    return lessons


@app.get("/lessons/period/{tg_id}")
async def get_lessons_by_period(
    tg_id: int,
    start_date: date,
    end_date: date
):
    user = database_manager.get_user_by_tg_id(tg_id)
    if user:
        database_manager.log_user_action(
            user_id=user.id,
            action_type="API_CALL",
            command_name="get_lessons_by_period",
            metadata={"start_date": str(start_date), "end_date": str(end_date)}
        )

    lessons = database_manager.get_user_lessons_on_period(tg_id, start_date, end_date)
    if not lessons:
        return {}
    return {str(k): v for k, v in lessons.items()}


@app.get("/auditoriums/buildings", response_model=List[str])
async def get_buildings():
    return database_manager.get_all_buildings()


@app.get("/auditoriums/types", response_model=List[str])
async def get_auditorium_types():
    return database_manager.get_auditorium_types()


@app.get("/auditoriums/free", response_model=List[AuditoriumResponse])
async def get_free_auditoriums(
    lesson_number: int,
    search_date: Optional[date] = Query(None),
    building: Optional[str] = None,
    auditorium_type: Optional[str] = None,
    tg_id: Optional[int] = Query(None)
):
    if search_date is None:
        search_date = now_local().date()

    if tg_id:
        user = database_manager.get_user_by_tg_id(tg_id)
        if user:
            database_manager.log_user_action(
                user_id=user.id,
                action_type="API_CALL",
                command_name="get_free_auditoriums",
                metadata={
                    "lesson_number": lesson_number,
                    "search_date": str(search_date),
                    "building": building,
                    "auditorium_type": auditorium_type
                }
            )

    auditoriums = database_manager.get_free_auditoriums_at_lesson(
        lesson_number=lesson_number,
        searching_date=search_date,
        building=building,
        auditorium_type=auditorium_type
    )
    return auditoriums


@app.post("/user-actions")
async def log_user_action(action: UserActionCreate):
    action_id = database_manager.log_user_action(
        user_id=action.user_id,
        action_type=action.action_type,
        command_name=action.command_name,
        metadata=action.metadata
    )
    return {"action_id": action_id}


@app.get("/stats/user/{tg_id}", response_model=UserStatsResponse)
async def get_user_stats(tg_id: int):
    stats = database_manager.get_user_stats_this_week(tg_id)
    if not stats:
        raise HTTPException(status_code=404, detail="User not found or no data")

    workload_serializable = {
        str(k): v for k, v in stats['workload_by_day'].items()
    }

    return {
        "total_lessons": stats["total_lessons"],
        "lectures": stats["lectures"],
        "practices": stats["practices"],
        "labs": stats["labs"],
        "workload_by_day": workload_serializable
    }


@app.get("/stats/engagement", response_model=EngagementStatsResponse)
async def get_engagement_stats():
    stats = database_manager.get_dau_wau_mau()
    return stats


@app.get("/stats/commands", response_model=List[CommandStatsResponse])
async def get_command_stats(days: int = Query(7, ge=1, le=365)):
    return database_manager.get_most_used_commands(days=days)
