# Simple API App

A small FastAPI service with two endpoints:

- `GET /time`: Returns the current UTC time.
- `GET /weather?city=<name>`: Returns current weather for a city using Open-Meteo.

## Tech Stack

- Python + FastAPI
- HTTPX for external API calls
- Docker

## API Endpoints

### `GET /time`

Response example:

```json
{
  "time": "2026-03-30T02:12:48.254511Z"
}
```

### `GET /weather?city=London`

Response example:

```json
{
  "city": "London",
  "country": "United Kingdom",
  "temperature_c": 12.3,
  "windspeed_kmh": 10.1,
  "time": "2026-03-30T10:00"
}
```

## Run Locally (Without Docker)

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/docs`
- `http://localhost:8000/time`
- `http://localhost:8000/weather?city=London`

## Run With Docker

Build image:

```bash
docker build -t simple-api-app .
```

Run container:

```bash
docker run -d -p 8000:8000 --name simple-api-app simple-api-app
```

Stop/remove container:

```bash
docker stop simple-api-app
docker rm simple-api-app
```

## Tests

```bash
python3 -m pip install pytest pytest-asyncio
pytest tests/
```

## Deploy on Render

This repo includes `render.yaml` and `Dockerfile.prod`.

1. Push this project to GitHub.
2. In Render, choose **New > Blueprint**.
3. Connect the GitHub repo and apply the blueprint.
4. Render deploys the Docker service on the free tier.

After deployment, use:

- `/time`
- `/weather?city=London`
- `/docs`

## Notes

- Free Render services spin down after inactivity.
- Weather data is fetched from Open-Meteo APIs.
