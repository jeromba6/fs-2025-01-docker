# Future Skils Docker

**Kestra** - Look in to Kestra for automation

This project demonstrates a multi-container Dockerized application consisting of three main services: a static web server, a reverse proxy, and an API server. The services are orchestrated using Docker Compose and include health checks, SSL support, and a simple HTTP API.

## Services Overview

### 1. Static Web Server
- **Purpose**: Serves static HTML content.
- **Technology**: Nginx.
- **Health Check**: `/health` endpoint returns `{"status":"UP"}`.
- **Configuration**: Defined in `static-webserver/nginx.conf`.

### 2. Reverse Proxy
- **Purpose**: Acts as a reverse proxy for the static web server and API servers.
- **Technology**: Nginx with SSL support.
- **Health Check**: `/health` endpoint returns `{"status":"UP"}`.
- **Configuration**: Defined in `reverse-proxy/nginx.conf`.

### 3. API Server
- **Purpose**: Provides a simple HTTP API with endpoints for health checks, environment variables, and container management.
- **Technology**: Python-based HTTP server.
- **Endpoints**:
  - `/`: Basic container information.
  - `/env`: Returns environment variables.
  - `/health`: Returns container health status.
  - `/unhealthy`: Simulates an unhealthy state.
    - Option to restore after a preset time by adding `?time=40`
  - `/kill`: Terminates the container.
- **Health Check**: `/health` endpoint returns `{"status":"ok"}` or `{"status":"sick"}`.

## Prerequisites

- Docker
- Docker Compose

## How to Build and Run

### Build Docker Images
Run the docker compose command
```sh
VERSION=[desired_version] docker compose build
```

This will build the 3 docker images for:
- reverse-proxy
- static-webserver
- api-server

## Start Services
Use Docker Compose to start all services:
```sh
VERSION=[desired_version] docker compose up
```

This will start all te containers and expose them via the reverse proxy container. To start in the background add the `-d` option

## Stop Services
To stop the services, run:
```sh
docker compose down
```
Only needed when started in the background

## Health Checks
Each service includes a health check configuration in compose.yml. Docker Compose will monitor the health of the containers.

## GitHub Actions Workflows
- `merge_to_main.yml` Automatically bumps the version and creates a new tag when a pull request is merged into the main branch.
- `pull_request_tests.yml` Lints Dockerfiles, YAML files, and Python code.
Builds and pushes Docker images to GitHub Container Registry.
Runs integration tests to ensure all services are healthy.

