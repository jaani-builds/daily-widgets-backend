from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.exchange_rates_api import router as exchange_rates_router
from app.routes.location_profile_api import router as location_profile_router
from app.routes.news_api import router as news_router
from app.routes.time_api import router as time_router
from app.routes.weather_api import router as weather_router

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(time_router)
app.include_router(weather_router)
app.include_router(exchange_rates_router)
app.include_router(news_router)
app.include_router(location_profile_router)
