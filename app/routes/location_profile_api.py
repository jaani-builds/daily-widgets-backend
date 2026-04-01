from typing import Optional

from fastapi import APIRouter, Query

from app.services.location_profile_service import build_location_profile

router = APIRouter()


@router.get("/location-profile")
async def get_location_profile(
    city: str = Query(..., description="City name"),
    country: Optional[str] = Query(None, description="Country name"),
):
    profile = await build_location_profile(city=city, country=country)
    return {"city": city, "country": country, **profile}
