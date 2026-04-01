# Daily Widgets Backend

A small FastAPI service with three endpoints:

- `GET /time`: Returns the current UTC time.
- `GET /weather?city=<name>`: Returns current weather for a city using Open-Meteo.
- `GET /exchange-rates?base=USD&target=EUR`: Returns the latest exchange rate.
- `GET /exchange-rates?base=USD&target=EUR&period_value=7&period_unit=days`: Returns historical exchange-rate data for a trailing period.

Live deployment:

- `https://daily-widgets-backend.onrender.com/`

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

### `GET /exchange-rates?base=USD&target=EUR`

Response example:

```json
{
  "base": "USD",
  "target": "EUR",
  "date": "2026-03-30",
  "rate": 0.92
}
```

### `GET /exchange-rates?base=USD&target=EUR&period_value=7&period_unit=days`

Valid `period_unit` values:

- `days`
- `months`
- `years`

Response example:

```json
{
  "base": "USD",
  "target": "EUR",
  "period": {
    "value": 7,
    "unit": "days",
    "start_date": "2026-03-23",
    "end_date": "2026-03-30"
  },
  "rates": [
    {
      "date": "2026-03-28",
      "rate": 0.91
    },
    {
      "date": "2026-03-29",
      "rate": 0.92
    },
    {
      "date": "2026-03-30",
      "rate": 0.93
    }
  ]
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
- `http://localhost:8000/exchange-rates?base=USD&target=EUR`
- `http://localhost:8000/exchange-rates?base=USD&target=EUR&period_value=30&period_unit=days`

## Run With Docker

Build image:

```bash
docker build -t daily-widgets-backend .
```

Run container:

```bash
docker run -d -p 8000:8000 --name daily-widgets-backend daily-widgets-backend
```

Stop/remove container:

```bash
docker stop daily-widgets-backend
docker rm daily-widgets-backend
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

- `https://daily-widgets-backend.onrender.com/time`
- `https://daily-widgets-backend.onrender.com/weather?city=London`
- `https://daily-widgets-backend.onrender.com/exchange-rates?base=USD&target=EUR`
- `https://daily-widgets-backend.onrender.com/exchange-rates?base=USD&target=EUR&period_value=3&period_unit=months`
- `https://daily-widgets-backend.onrender.com/docs`

## Notes

- Free Render services spin down after inactivity.
- Weather data is fetched from Open-Meteo APIs.
- Exchange-rate data is fetched from Frankfurter.
