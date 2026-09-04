#API KEY Rate Limiter

##Overview

This project is an API key-based rate limiter build with FastAPI that limits the number of requests and endpoint can serve within a defined time period.

The system tracks requests made using a specific API key and applies a configured request limit to protect backend services from excessive traffic.

The project was built to demonstrate how rate limiting can be designed and implemented as part of a real-world backend architecture, usinf Redis for rate-limit and PostgreSQL for persistent application data.

## Features

- User registration and JWT-based authentication
- API key generation and management
- API key validation
- Sliding window Counter-based rate limiting
- Redis-backed request counters and rate-limit state
- PostgreSQL-based persistent data storage
- Request usage logging for API keys
- Dashboard endpoint for viewing API key usage
- Automated API testing with Pytest
- High-Level Design and Low-Level Design (LLD) documentation

## Tech Stack

| Technology | Purpose | 
| ---------- | ------- |
| Python     | Primay programming language | 
| FastAPI    | Backend Framework for building REST APIs |
| PosrgreSQL | Persistent storage for users, API keys, and request logs |
| Redis | Stores rate-limiting counters and temporary rate-limit state |
| SQLAlchemy | ORM for database access and data modelling |
| Alembic | Database schema migrations |
| JWT | User authentication |
| Pytest | Automated API and endpoint testing |
| Docker | Runs Redis locally in a container |


## System Design

The project follows a layered backend architecture with FastAPI as the application layer, PostgreSQL for persistent data, and Redis for rate-limiting state.

Detailed system design documentation is available in `docs/` directory.

## Authentication & API Key Flow

### User Authentication

The application uses JWT-based authentication

1. A user registers using an email, username, and password.
2. The password is hashed before storing in PostgreSQL.
3. The user logs in using their email and password.
4. After successful authentication, a JWT access token is generated.
5. The JWT token is used to authenticate subsequent requests.
6. Access tokens are valid for 30 minutes

### API Key Validation

API keys are associated with individuals user.

When a request is made to a protected endpoint:

1. The JWT token is validated to identify the current user.
2. The API key provided in the request is being hashed using SHA-256.
3. The hashed key is looked up in PostgreSQL.
4. The system verifies that the API key exists and is active.
5. The system verifies that the API key belongs to the authenticated user.
6. If validation succeeds, the request proceeds to the rate-limiting layer.

This ensures that a valid API key cannot be used by a different authenticated user.

## Rate Limiting

The application uses the **Sliding Window Counter** algorithm to limit requests made using an API key.

The current configuration allows **100 requests per 60-second window.

For each API key, the rate limiter maintains the counters for the current and previous time window. For every incoming request, the system identifies the current window, increments the current counter, retrieves the previous window count, and calculates how much of the previous window overlaps with the current sliding window.

The estimated request count is calculated as:

`estimated_count = current_window_count + (previous_window_count x overlap_percentage)`

where:

`overlap_percentage` = (window - elapsed_time) / window`

If the estimated request count is within the configured limit, the request is allowed. If the limit is exceeded, the request is rejected with HTTP `429 Too Many Requests`.

A Sliding Window Counter is used to reduce the boundary problem of a fixed-window counter. For example, with a limit of 100 requests per 60 seconds, a client could otherwise send 100 request at the end of one window and another 100 immediately after the next window begins.
Using the previous window's request count helps account for this overlap.

Redis is used to store the rate-limiting counters because the counters are frequently updated and required low-latency access. The Redis keys follow the format:

`rate_limit:api_key:{api_key_id}:{window}`

The rate-limit calculation is executed using a Redis Lua script, which increments the current counter, retrieves the previous counter, calculates the estimated request count, and determines whether the request should be allowed.

The current window key is configured with a **120-second TTL** so that the previous window's counter remains available for the sliding-window calculation.

## Redis Design

Redis is used to store the temporary rate-limiting state for each API key.

The rate limiter maintains seperate counters for previous and current 60-second windows. This allows the Sliding Window Counter algorithm to estimate the number of requsts within
the current sliding period without relying on PostgreSQL for every counter operation.

Redis keys follow the format:

`rate_limit:api_key:{api_key_id}:{window}`

For each request, the application:

1. Identifies the current time window.
2. Builds the current and previous Redis keys.
3. Increments the current window counter.
4. Retrieves the previous window counter.
5. Uses both counters to calculate the estimated request count.

The rate-limit operation is executed using a Redis Lua script so that the counter update and rate-limit calculation are performed within Redis.

The current window key is configured with a TTL of 120 seconds. This keep the previous window's counter available long enough for the Sliding Window Counter calculation while allowing old rate-limit state to expire automatically.

Redis is used instead of PostgreSQL for the request counters because rate-limiting state is temporary and requires frequent, low-latency read and write operations.

## Database Design

PostgreSQL is used as the persistent database for the application.

The application uses three main tables:

### User

Stores user account and authentication information

| Column | Description |
| ------ | ----------- |
| `id`   | Primary key |
| `email`| User email  |
| `hashed_password` | Hashed user password |
| `user_name` | Username |

### APIKey

Stores API keys associated with users

| Column | Description |
| ------ | ----------- |
| `id`   | Primary key |
| `user_id` | Foreign key referencing `User.id` |
| `hashed_key` | SHA-256 hash of the API key |
| `is_active` | Indicates whether the API key is active |
| `created_at` | Timestamp indicating when the API key was created |

A user can have multiple API keys, resulting in a one-to-many relationship between `User` and `APIKey`.

### RequestLog

Stores information about API requests made using an API key.
| Column | Description |
| ------ | ----------- |
| `id`   | Primary key |
| `user_id` | Foreign key referencing `User.id` |
| `api_key_id` | Foreign key referencing `APIKey.id` |
| `status_code` | HTTP status code returned for the request |
| `timestamp` | Time at which the request was recorded | 

Both `user_id` and `api_key_id` are stored in the request log so that request activity can be associated with both the authenticated user and the API key used for the request.

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/register` | Registers a new user |
| `POST` | `/login` | Authenticates a user and generates a JWT access token |
| `POST` | `/generate_api_key` | Generate an API key for the authenticated user |
| `GET` | `/demo` | Protected endpoint used to demonstrate API-key authentication and rate limiting |
| `GET` | `/dashboard` | Returns API-key usage information for the authenticated user |

## Project Structure 

api_rate_limiter/
    ├── app/            # Application source code
    ├── alembic/        # Database migrations
    ├── docs/           # HLD and LLD documentation
    ├── tests/          # Automated tests
├── dependencies.py/    # FastAPI dependencies
├── alembic.ini/        # Alembic configuration   
├── pytest.ini/         # Pytest configuration
├── requirements.text/  # Project dependencies
├── .gitignore/ 
├── README.md/ 

## Setup and Installation

Clone the repository and navigate to the project directory:

    git clone <repository-url>
    cd api_rate_limiter

Create and activate a virtual environment:

    python -m venv venv
    venv/Scripts/activate

Install the project dependencies:

    pip install -r requirements.txt

Create a `.env` file with the required application configuration.
Do not commit the `.env' file to the repository.

Start redis using Docker:

    docker compose up -d

Run the database migrations:

    alembic upgrade head

Start the FastAPI application:
    uvicorn app.main:app --reload

The application is now available locally through the FastAPI server.

## Testing

The project uses **Pytest** for automated testing of the API endpoints.

The test suite covers:

- Happy-path scenarios
- Edge cases
- Authentication and authroization
- API key validation
- API key ownership verification
- Rate-limiting behaviour
- Endpoint responses

Tests can be executed using:
    pytest-v

The tests are intended to verify both successful requests and failure scenarios across the API.








