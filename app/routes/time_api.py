from fastapi import APIRouter

from app.utils.time_utils import utc_timestamp

router = APIRouter()


@router.get("/time")
def get_time():
    return {"time": utc_timestamp()}