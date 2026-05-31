# my_api

A RESTful API built with Python and FastAPI, containerized with Docker.

## Features
- User authentication with password hashing
- Database integration with SQLAlchemy
- Request/response validation using Pydantic schemas
- Logging support
- Dockerized for easy deployment

## Tech Stack
`Python` · `FastAPI` · `SQLAlchemy` · `Docker` · `PostgreSQL`

## How to Run
```bash
docker-compose up --build
```

## Project Structure
| File | Purpose |
|------|---------|
| `main.py` | API routes and entry point |
| `model.py` | Database models |
| `schemas.py` | Pydantic request/response schemas |
| `database.py` | DB connection setup |
| `password.py` | Password hashing utilities |
