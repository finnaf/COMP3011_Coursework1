# England Storm Overflow API

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

| Method | Path | Description | Authorisation |
|--------|------|-------------|------|
| GET | `/` | Health check | No |
| GET | `/outflows/` | List outflows, with optional filtering | No |
| GET | `/outflows/{id}` | Get a single outflow by ID | No |
| POST | `/outflows/` | Create an outflow | Yes |
| PATCH | `/outflows/{id}` | Update an outflow | Yes |
| DELETE | `/outflows/{id}` | Delete an outflow | Yes |
| GET | `/companies/` | List water companies | No |
| GET | `/companies/{ticker}` | Get a company by ticker | No |
| POST | `/companies/` | Create a company | Yes |
| PATCH | `/companies/{ticker}` | Update a company | Yes |
| DELETE | `/companies/{ticker}` | Delete a company | Yes |
| POST | `/auth/keys` | Create an API key | Admin |
| PUT | `/auth/keys/{id}` | Rotate an API key | Admin |
| DELETE | `/auth/keys/{id}` | Delete an API key | Admin |
| GET | `/stats` | General dataset statistics | No |
| GET | `/stats/outflows/` | Outflow summary statistics | No |
| GET | `/stats/companies` | Per-company performance statistics | No |
| GET | `/stats/companies/{ticker}` | Statistics for a single company | No |

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