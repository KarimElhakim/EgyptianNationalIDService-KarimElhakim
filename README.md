# Egyptian National ID Service

A small FastAPI backend that validates Egyptian National ID numbers, extracts useful details, and keeps per-key usage metrics suitable for subscription billing scenarios.

## Features

- Validates the structure of 14-digit Egyptian National ID numbers.
- Extracts birth date, gender, and issuing governorate.
- Authenticates requests with API keys supplied through the `X-API-Key` header.
- Enforces per-key rate limiting (default: 60 requests per minute).
- Records cumulative request counts for later billing or analytics.
- Provides an endpoint to retrieve the request total associated with the current API key.

## Getting Started

### Prerequisites

- Python 3.11+
- `pip` for installing dependencies

### Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### Configuration

The service reads several optional environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_PATH` | `data/app.db` | Location of the SQLite database file. |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | Requests allowed per API key during a one-minute window. |
| `DEFAULT_API_KEYS` | `demo-key-123:Demo account` | Comma-separated list of `key:owner` pairs created on startup. |

Example of defining custom keys and rate limit:

```bash
export DATABASE_PATH=data/app.db
export API_RATE_LIMIT_PER_MINUTE=120
export DEFAULT_API_KEYS="my-secret-key:Primary Account,analytics-key:Analytics"
```

## Running the Service

Start the API with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The service will listen on `http://127.0.0.1:8000` by default. Use the interactive docs at `http://127.0.0.1:8000/docs` to explore the endpoints.

## API Reference

### Inspect a National ID

`POST /v1/national-ids/inspect`

Request headers:

```
X-API-Key: demo-key-123
Content-Type: application/json
```

Request body:

```json
{
  "national_id": "30101012100013"
}
```

Successful response (`200 OK`):

```json
{
  "national_id": "30101012100013",
  "valid": true,
  "details": {
    "birth_date": "2001-01-01",
    "gender": "male",
    "governorate_code": "21",
    "governorate_name": "Giza"
  }
}
```

Error response (`400 Bad Request`):

```json
{
  "national_id": "10101012100013",
  "valid": false,
  "error": "Unsupported century digit in National ID"
}
```

### Retrieve Usage Metrics

`GET /v1/usage`

Returns the total number of requests performed with the supplied API key (not counting the retrieval call itself).

Example response:

```json
{
  "api_key": "demo-key-123",
  "owner": "Demo account",
  "total_requests": 42
}
```

## Testing

Run the automated test suite with:

```bash
pytest
```

## Project Structure

```
app/
├── config.py          # Environment-aware settings
├── database.py        # SQLite helpers and request counters
├── main.py            # FastAPI application and routing
├── national_id.py     # National ID parsing and validation
└── security.py        # API key authentication and rate limiting
```

Test cases live under `tests/` and exercise the core API behaviour, including authentication and rate limiting.
