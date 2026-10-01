# DevOps Portfolio Project

A project I am building in small stages to learn how to run an application reliably, from local development to cloud deployment.

The application is **Service Status**: a small web page that displays the service name, version, and health. Keeping the application simple leaves room to focus on testing, delivery, infrastructure, and troubleshooting.

## Current stage

Phase 2: Docker and Docker Compose configuration added. Container runtime verification is pending local Docker access. There are no pipelines or cloud resources yet. Future work is tracked in [ROADMAP.md](ROADMAP.md).

## Run locally

You need Python 3.10 or newer and Git. The application and tests use only Python's standard library; there are no packages to install.

From the repository root (the directory containing this README):

```bash
python3 --version
python3 -m app.server
```

Open **http://127.0.0.1:8000** in a browser. Use **Check again** to refresh the status. Stop the server with `Ctrl+C`.

In a second terminal, you can check the API directly:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/api/info
```

The health endpoint should return HTTP `200` and `{"status": "ok"}`.

## Run with Docker Compose

You need Docker Engine and Compose v2. The commands below use `docker compose`. If your installation provides the standalone v2 executable (as on this development machine), use `docker-compose` instead.

Stop any local Python copy first so port 8000 is free. From the repository root:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl -i http://127.0.0.1:8000/health
docker compose logs --tail=20 app
```

Open **http://127.0.0.1:8000**. The health response should be HTTP `200` with `{"status": "ok"}`. After the first health check, `docker compose ps` should show `healthy`.

Stop and remove this project's containers and network when finished:

```bash
docker compose down
```

The built image stays cached. After editing application files, run `docker compose up --build -d` again: the code is copied into the image, not mounted from your working folder.

### What the new files do

- `Dockerfile` describes an image containing Python and our application. It runs the app as a non-root user and sends Python output straight to the container logs.
- `.dockerignore` limits the build context to application files and build instructions, excluding Python caches and `.env` files.
- `compose.yaml` records how to build and run one app container, publish its port, and check `/health` periodically. An unhealthy status is a diagnostic signal; it does not automatically restart the app.

An **image** is the packaged application; a **container** is a running instance. Compose saves the run settings in Git so we do not have to remember a long command.

Inside the container, `APP_HOST=0.0.0.0` makes Python listen on all container interfaces. Compose publishes container port 8000 as `127.0.0.1:8000` on the host, keeping browser access local. Direct Python runs default to `127.0.0.1`. `EXPOSE 8000` documents the port; Compose's `ports` setting actually publishes it. See the [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) and [Compose service reference](https://docs.docker.com/reference/compose-file/services/).

### Verification status

The Python tests and Compose configuration can be checked without Docker daemon access. On this development machine, Docker is installed and standalone Compose v2 is available, but the current user cannot access the Docker socket and sudo requires interactive authentication. Image build, container health, browser access through Docker, and cleanup still need to be verified once Docker access is available. This remains a local learning server, not a production deployment.

## How it works

1. The Python server receives a browser request for `/` and returns `app/static/index.html`.
2. JavaScript in that page requests `/api/info` and `/health` from the same server.
3. The API returns JSON, and the page displays the values.

| Route | Purpose |
| --- | --- |
| `GET /` | Serve the frontend |
| `GET /api/info` | Return the application name and version |
| `GET /health` | Report that the HTTP service can respond |

Unknown routes return HTTP `404` with a JSON error. Requests are logged to the terminal.

The health check only checks this process. It does not check a database or external service, because there are none yet. Python's built-in HTTP server is suitable for this local learning stage; we will revisit the server before deployment. Direct Python runs listen only on the local machine; the container uses the networking settings explained above.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

The tests start their own server on a temporary local port, make real HTTP requests, and stop it afterward. You do not need to start the application first. They check the health endpoint, application info, homepage response, and an unknown route. Browser JavaScript is checked manually for now: open the page and confirm the name, version, and `ok` status appear.

## Project structure

```text
app/
  __init__.py           Python package marker
  server.py             HTTP routes and local server entry point
  static/
    index.html          Frontend, styles, and browser JavaScript
tests/
  test_server.py        Basic HTTP tests
Dockerfile             Package the application with Python
compose.yaml           Container run settings and health check
.dockerignore          Limit files sent to the image build
.gitignore             Keep generated files and local secrets out of Git
README.md              Setup and project explanation
ROADMAP.md             Future phases
```

## Git workflow

Keep each change small, run the tests, and inspect the diff before committing. For the Docker change:

```bash
git status
git add Dockerfile compose.yaml .dockerignore app/server.py README.md ROADMAP.md
git diff --cached
git commit -m "feat: containerize service status app with Docker Compose"
```

For later work, use a focused branch, for example `feat/docker-compose`. Write commit messages describing the actual change, such as `docs: explain local troubleshooting`. Never commit credentials or `.env` files; ignoring a file does not remove secrets already tracked by Git.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `python3: command not found` | Install Python 3 through your operating system's package manager. |
| `No module named app` | Run the command from the repository root. |
| `Address already in use` | Another process uses port 8000. Check for another running copy and stop it with `Ctrl+C`. |
| `docker: unknown command: docker compose` | Try `docker-compose version`; standalone Compose v2 uses a hyphen. Otherwise follow the [Compose installation guide](https://docs.docker.com/compose/install/linux/). |
| Permission denied for `/var/run/docker.sock` | Docker daemon access needs host administrator configuration. Do not make the socket world-writable. |
| Compose reports the port is already allocated | Stop the local Python app or another container using port 8000. |
| Container is unhealthy | Run `docker compose logs --tail=20 app` and check the health URL. |
| Browser cannot connect | Confirm the server is running and use `http://127.0.0.1:8000`. |
| Page says it cannot reach the service | Inspect the server terminal and try the health URL directly. |

## Phase 1 learning checkpoint

Before moving on, be able to explain what an HTTP route is, why the frontend requests JSON, what the health endpoint proves, and how a test detects a broken response. Try changing the page description, run the tests, and review the change with `git diff`.

## Phase 2 learning checkpoint

Explain the difference between an image and a container, why the server needs a different bind address inside Docker, and how to inspect logs and health. Before moving on, complete the container checks above and stop the stack with `docker compose down`.
