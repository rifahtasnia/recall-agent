# RecallAgent Documentation

This document explains the project decisions behind RecallAgent step by step. This file is the deeper technical and design reference.

## 1. Project Purpose

RecallAgent is an AI customer retention system for local service businesses.

The core problem is simple: service businesses often lose repeat customers because follow-up is manual, inconsistent, or forgotten. A customer may need another car wash, deep cleaning, pest control visit, carpet cleaning, or lawn service after a predictable amount of time, but business owners usually do not track every customer manually.

RecallAgent is designed to store service history, identify when customers may be due for another service, create a follow-up reminder, and log why the system made that decision.

## 2. Product Design Decision

### Decision

Build RecallAgent as a simple multi-agent workflow.

### Why

The system has several clear responsibilities:

- Understand the customer and service history
- Decide whether a reminder is needed
- Generate a personalized reminder message
- Schedule or queue the reminder
- Log the decision

Splitting these responsibilities keeps the project easier to understand, test, and extend.

### Current Planned Agents

1. **Service Insight Agent**
   Reviews the customer's service history and service type.

2. **Reminder Decision Agent**
   Decides whether the customer should receive a reminder.

3. **Message Writer Agent**
   Creates a personalized reminder message.

4. **Reminder Scheduler Agent**
   Adds the reminder to a queue for review or delivery.


## 3. Repository Structure 

```text
AI Agent Builder/
  README.md
  DOCUMENTATION.md
  .github/
    workflows/
      ci.yml
  recall-agent/
    app/
    dashboard/
    tests/
    alembic/
    Dockerfile
    docker-compose.yml
    pyproject.toml
```

## 4. Technology Stack Decisions

### Python

RecallAgent is Python-first because Python backend development is reliable and widely used for AI agent development.

### FastAPI

FastAPI is used as the backend API framework.

Necessity:

- Creates API endpoints
- Provides automatic API documentation
- Works well with Pydantic
- Is production-ready for real systems

Current endpoints:

```text
GET /health
GET /health/db
```

### Streamlit

Streamlit is used for the dashboard.

Necessity:

- Keeps the whole project Python-based
- Avoids React/frontend complexity in the first version
- Makes it easy to build a dashboard for customers, services, reminders, and agent logs

Current dashboard behavior:

- Calls the FastAPI health endpoint
- Shows whether the API is running

### PostgreSQL

PostgreSQL is used as the database.

Necessity:

- Stores relational data clearly
- Supports production-style database design
- Works well with service businesses because the data has natural relationships:
  customers, services, service records, reminders, and logs

### SQLAlchemy

SQLAlchemy is used as the ORM (Object Relational Mapper).

Necessity:

- Lets us represent database tables as Python classes
- Reduces raw SQL in application code
- Makes relationships between tables easier to model

Example mental model:

```text
Customer Python class <-> customers database table
```

### Alembic

Alembic is used for database migrations.

Necessity:

- Tracks database schema changes over time
- Lets us version database structure like code
- Creates and updates tables in a repeatable way

Alembic creates an internal table named:

```text
alembic_version
```

That table records which migration has already been applied.

### psycopg

`psycopg` is the PostgreSQL driver.

Necessity:

- SQLAlchemy builds database queries
- `psycopg` performs the actual connection to PostgreSQL

Mental model:

```text
SQLAlchemy = ORM/query layer
psycopg = PostgreSQL connection driver
PostgreSQL = actual database
```

### Docker

Docker is used to package services.

Necessity:

- Avoids manually installing PostgreSQL
- Makes the app easier to run on another machine
- Makes local development more production-like

### Docker Compose

Docker Compose runs multiple services together.

Current services:

```text
api        FastAPI backend
dashboard  Streamlit dashboard
db         PostgreSQL database
```

### Ruff

Ruff is used for linting and formatting.

Necessity:

- Keeps imports organized
- Catches style issues
- Keeps code formatting consistent

### Pytest

Pytest is used for tests.

Necessity:

- Verifies app behavior
- Gives confidence before pushing code
- Supports future tests for database logic and agent decisions

### GitHub Actions

GitHub Actions is used for CI.

Necessity:

- Runs checks automatically on push and pull requests
- Verifies linting, formatting, tests, and Docker builds

Current CI checks:

```text
ruff check
ruff format --check
pytest
docker build
```

## 5. Database Design

The database is designed around the main RecallAgent workflow:

```text
Business defines services
Customer receives a service
Service record is stored
Agent reviews service history
Reminder is created if needed
Agent decision is logged
```

## 6. Data Models

### businesses

Stores the business using RecallAgent.

Example:

```text
Fresh Auto Spa
Sparkle Home Cleaning
Green Lawn Care
```

Important fields:

```text
id
name
industry
created_at
```

Why it exists:

This table makes the design ready for multiple businesses.

Relationship:

```text
One business -> many customers
One business -> many service types
```

### customers

Stores customers belonging to a business.

Important fields:

```text
id
business_id
full_name
email
phone
preferred_channel
is_opted_in
created_at
```

Why it exists:

The system needs customer contact details and communication preferences to create reminders later.

`is_opted_in` is included early because reminder systems should not contact customers who did not agree to be contacted.

Relationship:

```text
One customer -> many service records
One customer -> many reminders
```

### service_types

Stores the services offered by each business.

Example:

```text
Business: Fresh Auto Spa

Services:
- Basic Car Wash
- Interior Detailing
- Full Exterior Detailing
- Ceramic Coating Checkup
```

Important fields:

```text
id
business_id
name
description
recommended_interval_days
created_at
```

Why it exists:

One business can provide multiple services. Each service can have a different recommended repeat interval.

Example:

```text
Car Wash -> 30 days
Interior Detailing -> 60 days
Home Deep Cleaning -> 90 days
Carpet Cleaning -> 180 days
```

The future Reminder Decision Agent will use `recommended_interval_days`.

Relationship:

```text
One service type -> many service records
One service type -> many reminders
```

### service_records

Stores completed services.

Example:

```text
Sarah received Interior Detailing on 2026-07-01
Daniel received Home Deep Cleaning on 2026-06-15
```

Important fields:

```text
id
customer_id
service_type_id
service_date
notes
created_at
```

Why it exists:

This is the historical data the agents analyze. Without service records, the system cannot know when a customer last received a service.

Relationship:

```text
One service record -> many reminders
```

In practice, we may usually create one reminder per service record, but the model allows more flexibility.

### reminders

Stores reminders created by the system.

Important fields:

```text
id
customer_id
service_type_id
service_record_id
scheduled_for
channel
message
status
created_at
```

Status values:

```text
pending
scheduled
sent
skipped
failed
```

Why it exists:

The agent should not only make a decision in memory. It should create a database record that can be reviewed, shown in the dashboard, sent later, or audited.

### agent_logs

Stores the reasoning and decision history from agents.

Important fields:

```text
id
customer_id
reminder_id
agent_name
decision
reason
created_at
```

Decision values:

```text
created
skipped
failed
```

Why it exists:

Agent systems should be explainable. This table lets the dashboard show why a reminder was created or skipped.

Example:

```text
Agent: Reminder Decision Agent
Decision: created
Reason: Customer received interior detailing 61 days ago. Recommended interval is 60 days.
```

## 7. Database Relationship Summary

```text
businesses
  ├── customers
  │     ├── service_records
  │     └── reminders
  │
  └── service_types
        ├── service_records
        └── reminders

service_records
  └── reminders

reminders
  └── agent_logs
```

Core logic supported by this design:

```text
One business can provide multiple services.
One business can have many customers.
One customer can receive many services over time.
One completed service can generate a reminder.
One reminder can have agent logs explaining why it exists.
```

## 8. Why The Tables Are Separated

We intentionally did not use one large table.

One large table would duplicate data:

```text
customer name
phone
service type
recommended interval
reminder status
agent reason
```

across many rows.

The current design separates concepts:

```text
businesses = who owns the customer base
customers = who receives services
service_types = what services are offered
service_records = what happened
reminders = what should happen next
agent_logs = why the system made a decision
```

This makes the database easier to understand, query, and extend.

## 9. Milestone History

### Milestone 1: Project Foundation

What was added:

- FastAPI app
- Streamlit dashboard placeholder
- Dockerfile
- Docker Compose
- Pytest
- Ruff
- GitHub Actions CI

Why:

Before building agents or database logic, the project needed a stable runnable foundation.

Verification:

```text
ruff check passed
ruff format --check passed
pytest passed
docker build passed
docker compose started API and dashboard
GitHub Actions passed
```

### Milestone 2: Database Setup

What was added:

- PostgreSQL Docker service
- SQLAlchemy models
- SQLAlchemy session setup
- Alembic configuration
- Initial migration
- `/health/db` endpoint
- Model registration test

Why:

The agent workflow needs structured service history and reminder data. The database is the source of truth for that workflow.

Verification:

```text
ruff check passed
ruff format --check passed
pytest passed
docker build passed
docker compose started API, dashboard, and database
alembic upgrade head passed
/health/db returned database connected
GitHub Actions passed
```

## 10. Failures And Fixes

This section records problems we encounter and how we solve them.

### GitHub Actions Workflow Push Rejected

Problem:

Pushing `.github/workflows/ci.yml` failed.

Error:

```text
refusing to allow an OAuth App to create or update workflow without workflow scope
```

Cause:

The GitHub CLI token did not have permission to create or update workflow files.

Fix:

Refreshed GitHub CLI authentication with the `workflow` scope, then pushed again.

### Local Dependency Install Failed In Sandbox

Problem:

Installing Python dependencies failed at first.

Cause:

The sandbox could not reach PyPI without explicit network permission.

Fix:

Reran the dependency installation with approved network access.

### Docker Daemon Permission Issue

Problem:

The first Docker build attempt failed because the environment could not access the Docker daemon socket.

Cause:

Docker requires elevated access outside the default sandbox.

Fix:

Reran Docker commands with approved Docker daemon access.

### Local curl Could Not Reach Docker Port In Sandbox

Problem:

The first `curl http://localhost:8000/health` attempt failed.

Cause:

The sandboxed command could not connect to the local Docker-exposed port.

Fix:

Reran the health check with approved local network access.

### PostgreSQL Enum Duplicate Error

Problem:

The first Alembic migration failed with:

```text
type "reminder_status" already exists
```

Cause:

The migration explicitly created the PostgreSQL enum type, and SQLAlchemy also tried to create the same enum while creating the table.

Fix:

Changed the migration to create the enum once and reuse it in table columns with `create_type=False`.

Lesson:

PostgreSQL enum types are database-level objects. When using Alembic and SQLAlchemy together, enum creation must be handled carefully to avoid duplicate type creation.

## 11. Next Planned Step

The next step is to build API endpoints for the database models.

Likely endpoints:

```text
POST /businesses
GET /businesses
POST /customers
GET /customers
POST /service-types
GET /service-types
POST /service-records
GET /service-records
GET /reminders
GET /agent-logs
```

Why this comes next:

Before adding LangGraph and agents, we need a way to create and read the core data through the API.

After CRUD endpoints are working, we can add seed data and then build the rule-based reminder workflow.
