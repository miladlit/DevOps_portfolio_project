# DevOps Portfolio Project

A hands-on DevOps project that takes a small web service through the same stages used in a real delivery workflow: development, testing, containerization, CI/CD, Linux deployment, reverse proxying, infrastructure, monitoring, logging, and orchestration.

The application itself is intentionally simple. **Service Status** exposes health and runtime information through a small Python API and browser dashboard, so the main focus stays on DevOps engineering rather than application complexity.

## What this project demonstrates

**Working or implemented now**

- Python service with health and status endpoints
- Automated HTTP and regression tests
- Bash test and health-check scripts
- Dockerfile and Docker Compose configuration
- GitHub Actions CI across Python versions
- Nginx integration tests in CI
- Versioned release packaging with SHA-256 checksums
- CI release artifacts after successful tests
- Deployment and rollback rehearsal
- Linux `systemd` service configuration
- Nginx reverse proxy configuration
- Documentation and troubleshooting notes

**Planned next**

Terraform → Azure → Ansible → Prometheus → Grafana → Elastic Stack → Jenkins → Kubernetes → Helm → security hardening.

See the full [project roadmap](ROADMAP.md).

## Current status

The project is currently around **Phase 7** of the roadmap.

| Area | Status |
| --- | --- |
| Application | Working locally |
| Automated tests | Working locally |
| Docker configuration | Added; runtime verification still pending |
| GitHub Actions CI | Added; hosted verification still being completed |
| Release packaging | Implemented and smoke-tested locally |
| Linux deployment | Configuration and guide ready; VM installation pending |
| Nginx reverse proxy | Configuration and local integration tests added |
| Cloud infrastructure | Not started yet |
| Monitoring / logging | Planned for later phases |

I deliberately keep unfinished work marked as unfinished. A configuration file is not treated as a completed deployment until it has been run and verified.

## Architecture today

```mermaid
flowchart LR
    U[Browser / curl] --> N[Nginx reverse proxy]
    N --> A[Python Service Status app]
    A --> H[/health]
    A --> I[/api/info]
    A --> S[/api/status]

    G[GitHub push / pull request] --> CI[GitHub Actions CI]
    CI --> T[Automated tests]
    CI --> P[Release packaging]
    P --> R[Verified release artifact]
```

The target architecture will expand gradually as Terraform, Azure, Ansible, Prometheus, Grafana, centralized logging, Kubernetes, and Helm are introduced.

## Why I built it this way

The goal is to understand each part instead of adding many tools at once. Every phase should leave the project working, add one or two useful DevOps concepts, and include a clear way to verify the result.

That means the project grows in small steps:

1. build something simple
2. test it
3. package it
4. automate the checks
5. create repeatable releases
6. deploy and operate it
7. add infrastructure and observability
8. move toward orchestration and stronger security

## Quick start

Requirements:

- Python 3.10+
- Git
- Bash and `curl` for operational checks

Run the service from the repository root:

```bash
python3 -m app.server
```

Open:

```text
http://127.0.0.1:8000
```

Check the API:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/api/info
curl -i http://127.0.0.1:8000/api/status
```

A healthy service returns:

```json
{"status": "ok"}
```

Use a different port when needed:

```bash
APP_PORT=9000 python3 -m app.server
```

## Automated tests

Run the full local test suite with:

```bash
bash scripts/test.sh
```

Or directly with Python:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover normal HTTP behavior as well as failure and regression cases, including:

- health, info, status, and homepage responses
- `HEAD` requests
- configurable ports
- unknown routes
- query strings
- source-file and parent-path rejection
- unsupported methods followed by successful recovery
- operational health-check behavior
- Nginx forwarding and upstream-failure behavior when Nginx is available

The HTTP tests start their own temporary server, make real requests, and stop it afterwards.

## Docker and Docker Compose

The repository includes a `Dockerfile`, `.dockerignore`, and `compose.yaml`.

Expected workflow:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl -i http://127.0.0.1:8000/health
docker compose logs --tail=20 app
docker compose down
```

The image runs the application as a non-root user and Compose includes a health check.

**Verification note:** the configuration exists, but full container runtime verification is still pending on the current development environment because Docker socket access is restricted. I keep that distinction visible rather than marking the phase complete prematurely.

## CI/CD with GitHub Actions

`.github/workflows/ci.yml` runs on pushes, pull requests, and manual dispatches.

The pipeline currently contains:

1. HTTP tests on Python 3.10
2. HTTP tests on Python 3.14
3. Nginx integration tests
4. release packaging after required tests pass
5. SHA-256 checksum verification
6. upload of the verified release artifact

The workflow uses read-only repository permissions for normal CI work and does not require deployment secrets at this stage.

The release artifact is named from the tested commit so a package can be traced back to its source revision.

## Release and rollback practice

Create and smoke-test a release package:

```bash
python3 scripts/release.py HEAD
```

The script packages committed application files, extracts the result into a temporary directory, starts the application, checks the real HTTP endpoints, and creates a SHA-256 checksum.

Rehearse switching from a previous release to a candidate and back again:

```bash
python3 scripts/rehearse.py
```

This is deliberately a local rehearsal rather than pretending to be a production deployment. Real server deployment is the next step.

## Linux service deployment

The [Linux deployment guide](deploy/README.md) documents installation on Debian/Ubuntu with:

- a dedicated service account
- packaged releases
- `systemd`
- service restart behavior
- log inspection
- health checks
- release switching and rollback

The service configuration keeps the Python application on loopback rather than exposing it directly.

Run a repeatable health check against a running service with:

```bash
bash scripts/check.sh
```

Or specify another local address:

```bash
bash scripts/check.sh http://127.0.0.1:9000
```

## Nginx reverse proxy

The [Nginx setup guide](deploy/nginx/README.md) places Nginx in front of the application.

```text
Client → Nginx → Python application
```

The repository includes:

- proxy configuration
- request forwarding
- access/error logging
- upstream failure testing
- integration tests
- a dedicated CI job

Local Nginx integration testing has passed. Verification on the eventual VM is still pending.

## Project structure

```text
.github/workflows/
  ci.yml                     GitHub Actions CI and release workflow

app/
  __init__.py
  server.py                  HTTP service
  static/
    index.html               Status dashboard

tests/
  test_server.py             HTTP and regression tests
  test_check.py              Operational health-check tests
  test_proxy.py              Nginx integration tests

scripts/
  test.sh                    Repeatable test command
  check.sh                   Health check for a running service
  release.py                 Build and smoke-test a release
  rehearse.py                Deployment and rollback rehearsal

deploy/
  README.md                  Linux deployment guide
  systemd/
    service-status.service   systemd unit
  nginx/
    service-status.conf      Reverse proxy configuration
    README.md                Nginx setup and verification

Dockerfile                   Container image definition
compose.yaml                 Docker Compose configuration
.dockerignore                Docker build exclusions
.gitignore                   Local/generated file exclusions
README.md                    Portfolio overview and usage
ROADMAP.md                   Project phases and progress
```

## Roadmap

| Phase | Focus |
| ---: | --- |
| 1 | Basic application and Git structure |
| 2 | Docker and Docker Compose |
| 3 | Automated testing |
| 4 | GitHub Actions CI |
| 5 | Release / deployment pipeline |
| 6 | Linux server deployment |
| 7 | Nginx reverse proxy |
| 8 | Terraform infrastructure |
| 9 | Azure deployment |
| 10 | Ansible configuration |
| 11 | Prometheus monitoring |
| 12 | Grafana dashboards |
| 13 | Elastic Stack centralized logging |
| 14 | Jenkins pipeline |
| 15 | Kubernetes |
| 16 | Helm |
| 17 | Security, secrets, and scanning |
| 18 | Final documentation and portfolio cleanup |

Detailed completion criteria and current progress are kept in [ROADMAP.md](ROADMAP.md).

## What I am learning

This project is not only about collecting tools. I want to be able to explain why each part exists and troubleshoot it when something fails.

Examples of the concepts covered so far:

- health checks and failure signals
- repeatable automated testing
- container images vs. running containers
- CI jobs, steps, and dependencies
- artifact traceability
- release checksums
- smoke testing
- deployment and rollback concepts
- Linux service management
- reverse proxies and upstream failures

Later stages will add infrastructure as code, cloud deployment, configuration management, metrics, dashboards, centralized logs, orchestration, and secret management.

## Security principles

Security is considered throughout the project rather than saved only for the final phase:

- no credentials or `.env` files should be committed
- containers should avoid unnecessary root privileges
- services should avoid unnecessary public exposure
- CI permissions should stay minimal
- releases should be traceable to source commits
- checksums are used to detect changed release archives

Phase 17 will expand this with secret storage and automated security scanning.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `python3: command not found` | Install Python 3 using the operating system package manager. |
| `No module named app` | Run commands from the repository root. |
| `Address already in use` | Stop the process already using the selected port or choose another port. |
| Docker Compose command missing | Check whether the system uses `docker compose` or standalone `docker-compose`. |
| Permission denied for `/var/run/docker.sock` | Fix Docker access through normal host administration; do not make the socket world-writable. |
| Container is unhealthy | Inspect `docker compose logs --tail=20 app` and test `/health`. |
| Browser cannot connect | Confirm the service is running and verify the health endpoint directly. |
| Nginx returns an upstream error | Confirm the backend service is running and listening on the configured loopback port. |

## Project philosophy

I am building this repository gradually and verifying each stage before calling it complete. The goal is a project I can explain in an interview, rebuild from documentation, and troubleshoot when something breaks — not simply a repository containing many DevOps tool names.
