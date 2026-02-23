# 🧪 Coding Test -- Meeting Room Booking API

------------------------------------------------------------------------

# 📌 Executive Summary

**Language:** Python 3.10+\
**Framework:** Your choice (FastAPI, Flask, Django, etc.)\
**Database:** Your choice (SQLite allowed; PostgreSQL recommended for
advanced constraints)

## 🎯 Goal of the Assessment

Build a production-style backend API for a **Meeting Room Booking**
system.

This assessment evaluates:

-   REST API design
-   Data modeling
-   Business rule implementation
-   Concurrency-safe booking logic
-   Authentication & authorization
-   Automated testing
-   Code structure and maintainability

You are free to make architectural decisions as long as all requirements
are met.

------------------------------------------------------------------------

# 📖 Scenario & Problem Statement

You are building the backend for a company that needs a **Meeting Room
Booking** system.

Teams must be able to:

-   Register rooms
-   Create bookings for specific time ranges
-   Prevent overlapping bookings
-   Cancel and reschedule reservations
-   Query bookings with filters

The system must be reliable and prevent double-booking even under
concurrent requests.

------------------------------------------------------------------------

# 🚀 API Requirements

## 🔎 General Rules

-   All timestamps must use **ISO 8601 with timezone**
-   A booking must satisfy:
    -   `start_at < end_at`
    -   Minimum duration: **15 minutes**
    -   Maximum duration: **8 hours**
-   A room cannot have overlapping **active** bookings
-   Canceling a booking does **not** delete it

### Overlap definition

Two bookings overlap if:

    new_start < existing_end AND new_end > existing_start

Edge-touching bookings (e.g., 10:00--11:00 and 11:00--12:00) are
allowed.

------------------------------------------------------------------------

# 🔌 Endpoints

## GET /health

Returns:

``` json
{ "status": "ok" }
```

------------------------------------------------------------------------

## POST /rooms

Authentication required.

``` json
{
  "name": "Atlantic",
  "capacity": 10
}
```

Errors: - 400 invalid payload - 409 duplicate room name - 401
unauthorized

------------------------------------------------------------------------

## GET /rooms

Pagination supported.

------------------------------------------------------------------------

## POST /rooms/{room_id}/bookings

Authentication required.

``` json
{
  "title": "Sprint Planning",
  "start_at": "2026-02-23T10:00:00-03:00",
  "end_at": "2026-02-23T11:00:00-03:00"
}
```

Must prevent overlapping active bookings.

------------------------------------------------------------------------

# 🗄️ Database Schema (Example)

``` sql
CREATE TABLE rooms (
  id UUID PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  capacity INTEGER NOT NULL CHECK (capacity >= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE bookings (
  id UUID PRIMARY KEY,
  room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
  title VARCHAR(120) NOT NULL,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'canceled')),
  canceled_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (start_at < end_at)
);
```

------------------------------------------------------------------------

# 🔐 Authentication

Use:

    Authorization: Bearer <token>

Environment variable:

    API_TOKEN=your-token

------------------------------------------------------------------------

# 🧪 Testing Requirements

Minimum:

-   10 tests
-   Unit + integration tests
-   Overlap validation
-   Auth validation
-   Cancel/reschedule logic

------------------------------------------------------------------------

# 🎁 Bonus

Frontend SPA (React/Nextjs) consuming the API.

------------------------------------------------------------------------

# 📦 Submission

Submit:

-   A fork with the source code
-   Tests
-   README with setup instructions
