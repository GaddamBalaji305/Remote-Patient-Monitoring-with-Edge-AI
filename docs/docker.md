# Docker Operations & Multi-Container Deployment Guide

This document provides instructions for containerizing, building, starting, configuring, and troubleshooting the complete **Remote Patient Monitoring with Edge AI** platform using Docker and Docker Compose.

---

## 1. Multi-Container Architecture Overview

The system consists of 4 interconnected Docker microservices:

```text
┌─────────────────┐       ┌─────────────────┐
│    frontend     │       │    edge-ai      │
│  (React SPA &   │       │  (Sensor & ML   │
│ Nginx / :3000)  │       │    Pipeline)    │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │   HTTP / WebSockets     │ HTTP POST
         ▼                         ▼
┌───────────────────────────────────────────┐
│                  backend                  │
│           (FastAPI / Uvicorn / :8000)     │
└────────────────────┬──────────────────────┘
                     │
                     │  SQL Connection
                     ▼
┌───────────────────────────────────────────┐
│                 database                  │
│        (PostgreSQL 15 / Port 5432)        │
└───────────────────────────────────────────┘
```

| Service | Container Name | Base Image | Port | Description |
| :--- | :--- | :--- | :---: | :--- |
| **`frontend`** | `rpm_frontend` | `nginx:alpine` | `3000` | Nginx web server serving React SPA with reverse proxy for `/api` and `/ws`. |
| **`backend`** | `rpm_backend` | `python:3.12-slim` | `8000` | FastAPI REST API & WebSocket manager with Uvicorn ASGI server. |
| **`edge-ai`** | `rpm_edge_ai` | `python:3.12-slim` | N/A | Physiological sensor simulator, 12-feature Random Forest classifier, and offline queue. |
| **`database`** | `rpm_database` | `postgres:15-alpine` | `5432` | Relational database with persistent volume storage (`postgres_data`). |

---

## 2. Docker Prerequisites & Installation

### Requirements
- **Docker Engine**: Version `24.0+`
- **Docker Compose**: Version `v2.20+`

### Installation Links
- **Windows / macOS**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y docker.io docker-compose-plugin
  sudo systemctl enable --now docker
  ```

---

## 3. Starting the Application

To build and start all 4 services with a single command:

```bash
docker compose up --build
```

### Starting in Detached Mode (Background)
```bash
docker compose up -d --build
```

### Accessing Running Services
- **React SPA Telemetry Dashboard**: Open `http://localhost:3000`
- **FastAPI Interactive API Documentation (Swagger)**: Open `http://localhost:8000/docs`
- **Backend Health Check**: Open `http://localhost:8000/api/health`

---

## 4. Stopping the Application

### Graceful Shutdown
To stop and remove all running containers and networks:

```bash
docker compose down
```

### Complete Reset (Including Database Volume Purge)
To stop containers and wipe persistent PostgreSQL database volumes:

```bash
docker compose down -v
```

---

## 5. Environment Variables Configuration

Environment variables can be customized in `.env.docker` or passed directly to Docker Compose:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `POSTGRES_USER` | `rpm_user` | Database username for PostgreSQL container. |
| `POSTGRES_PASSWORD` | `rpm_secure_password_123` | Database password for PostgreSQL container. |
| `POSTGRES_DB` | `rpm_db` | Database schema name. |
| `DATABASE_URL` | `postgresql://rpm_user:rpm_secure_password_123@database:5432/rpm_db` | SQLAlchemy connection string. |
| `SECRET_KEY` | *(256-bit Hex String)* | JWT secret signature key. Override in production! |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token lifetime in minutes. |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | `10` | Rate limiting threshold for `/api/auth/login`. |
| `BACKEND_URL` | `http://backend:8000/api/edge/events` | Ingestion endpoint URL used by Edge AI container. |
| `CORS_ORIGINS` | `http://localhost:3000,http://frontend:3000` | Allowed CORS origins for browser security. |

---

## 6. Container Monitoring & Troubleshooting

### Checking Container Health Status
```bash
docker compose ps
```

### Viewing Live Container Logs
```bash
# View all container logs simultaneously
docker compose logs -f

# View Edge AI pipeline logs
docker compose logs -f edge-ai

# View Backend API logs
docker compose logs -f backend

# View Frontend Nginx web server logs
docker compose logs -f frontend
```

### Shell Access to Running Containers
```bash
# Open interactive bash prompt inside backend container
docker compose exec backend bash

# Inspect PostgreSQL database via psql
docker compose exec database psql -U rpm_user -d rpm_db
```

### Common Issues & Resolution

1. **Port `3000` or `8000` already in use**:
   - Ensure local dev server (Uvicorn or Node) is stopped before running `docker compose up`.
   - Or change mapped host port in `docker-compose.yml` (e.g. `"3001:3000"`).

2. **Backend fails to connect to database**:
   - The `backend` container waits for PostgreSQL health checks (`pg_isready`). Verify database logs: `docker compose logs database`.

3. **Edge AI events fail to reach backend**:
   - Ensure `BACKEND_URL` points to `http://backend:8000/api/edge/events` (using the container service name `backend` instead of `localhost`).
