from datetime import date
from typing import Optional, List, Dict, Any
import httpx
import os
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def create_user(self, tg_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.post("/users", json={"tg_id": tg_id})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create user {tg_id}: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating user {tg_id}: {e}", exc_info=True)
            return None

    async def get_user(self, tg_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/users/{tg_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get user {tg_id}: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user {tg_id}: {e}", exc_info=True)
            return None

    async def attach_user_to_group(self, tg_id: int, group_name: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.put(f"/users/{tg_id}/group", params={"group_name": group_name})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to attach user {tg_id} to group {group_name}: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error attaching user {tg_id} to group {group_name}: {e}", exc_info=True)
            return None

    async def get_groups(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get("/groups")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get groups list: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting groups list: {e}", exc_info=True)
            return []

    async def get_lessons_by_date(self, tg_id: int, search_date: Optional[date] = None) -> List[Dict[str, Any]]:
        try:
            params = {}
            if search_date:
                params["search_date"] = search_date.isoformat()
            response = await self.client.get(f"/lessons/date/{tg_id}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get lessons for user {tg_id} on date {search_date}: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting lessons for user {tg_id}: {e}", exc_info=True)
            return []

    async def get_lessons_by_period(self, tg_id: int, start_date: date, end_date: date) -> Dict[str, List[Dict[str, Any]]]:
        try:
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            response = await self.client.get(f"/lessons/period/{tg_id}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get lessons for user {tg_id} for period {start_date} - {end_date}: HTTP {e.response.status_code} - {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting lessons for period for user {tg_id}: {e}", exc_info=True)
            return {}

    # Auditorium endpoints
    async def get_buildings(self) -> List[str]:
        try:
            response = await self.client.get("/auditoriums/buildings")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get buildings list: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting buildings list: {e}", exc_info=True)
            return []

    async def get_auditorium_types(self) -> List[str]:
        try:
            response = await self.client.get("/auditoriums/types")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get auditorium types: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting auditorium types: {e}", exc_info=True)
            return []

    async def get_free_auditoriums(
        self,
        lesson_number: int,
        search_date: Optional[date] = None,
        building: Optional[str] = None,
        auditorium_type: Optional[str] = None,
        tg_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            params = {"lesson_number": lesson_number}
            if search_date:
                params["search_date"] = search_date.isoformat()
            if building:
                params["building"] = building
            if auditorium_type:
                params["auditorium_type"] = auditorium_type
            if tg_id:
                params["tg_id"] = tg_id

            response = await self.client.get("/auditoriums/free", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get free auditoriums for lesson {lesson_number}: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting free auditoriums: {e}", exc_info=True)
            return []

    # User action logging
    async def log_user_action(
        self,
        user_id: int,
        action_type: str,
        command_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[int]:
        try:
            data = {
                "user_id": user_id,
                "action_type": action_type,
                "command_name": command_name,
                "metadata": metadata
            }
            response = await self.client.post("/user-actions", json=data)
            response.raise_for_status()
            return response.json()["action_id"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to log user action for user {user_id} ({action_type}): HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error logging user action for user {user_id}: {e}", exc_info=True)
            return None

    # Statistics endpoints
    async def get_user_stats(self, tg_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/stats/user/{tg_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get user stats for user {tg_id}: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user stats for user {tg_id}: {e}", exc_info=True)
            return None

    async def get_engagement_stats(self) -> Optional[Dict[str, int]]:
        try:
            response = await self.client.get("/stats/engagement")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get engagement stats: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting engagement stats: {e}", exc_info=True)
            return None

    async def get_command_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get("/stats/commands", params={"days": days})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get command stats: HTTP {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting command stats: {e}", exc_info=True)
            return []


# Global client instance
api_client = APIClient()
