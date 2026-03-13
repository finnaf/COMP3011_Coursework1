# UK Storm Overflow API

A RESTful API for querying real-time and historical storm overflow (sewage discharge) 
data across England's nine regional water companies. Built with FastAPI and SQLite.

**Live API:** https://comp3011-coursework1-vdc3.onrender.com/  
**API Documentation:** see `/docs`, `/redocs` or the included `api_docs.pdf`

## Setup

### Dependencies
```bash
pip install -r requirements.txt
```

### Data

The database is seeded automatically on first run. File names within `streamwaterdata`
directory are hardcoded within `main.py`.

## Running

### Locally
```bash
uvicorn app.main:app --reload
```

### Hosted (Render)
The API is deployed on Render's free tier at:
```
https://comp3011-coursework1-vdc3.onrender.com/
```
> Note: the instance spins down after 15 minutes of inactivity. Allow ~1 minute 
> for a cold start.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/outflows/` | List outflows, with optional filtering |
| GET | `/outflows/{id}` | Get a single outflow by ID |
| POST | `/outflows/` | Create an outflow (auth required) |
| PATCH | `/outflows/{id}` | Update an outflow (auth required) |
| DELETE | `/outflows/{id}` | Delete an outflow (auth required) |
| GET | `/companies/` | List water companies |
| GET | `/companies/{ticker}` | Get a company by ticker |
| POST | `/companies/` | Create a company (auth required) |
| PATCH | `/companies/{ticker}` | Update a company (auth required) |
| DELETE | `/companies/{ticker}` | Delete a company (auth required) |
| POST | `/auth/keys` | Create an API key (admin required) |
| PUT | `/auth/keys/{id}` | Rotate an API key (admin required) |
| DELETE | `/auth/keys/{id}` | Delete an API key (admin required) |
| GET | `/stats` | General dataset statistics |
| GET | `/stats/outflows/` | Outflow summary statistics |
| GET | `/stats/companies` | Per-company performance statistics |
| GET | `/stats/companies/{ticker}` | Statistics for a single company |

Full documentation available at `/docs` (Swagger UI) or `/redoc` (Redocly).

## Authentication

Protected endpoints require an `X-API_KEY` header. Keys are managed via `/auth/keys` 
using the admin key. See the API documentation for details.

## Testing

From the project root:
```bash
pytest test_api.py -v
```

Tests use an in-memory SQLite database and mock the startup data import.