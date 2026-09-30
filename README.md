# DevOps Portfolio Project

A project I am building in small stages to learn how to run an application reliably, from local development to cloud deployment.

The application is **Service Status**: a small web page that displays the service name, version, and health. Keeping the application simple leaves room to focus on testing, delivery, infrastructure, and troubleshooting.

## Current stage

Phase 1: basic application and Git structure. There are no containers, pipelines, or cloud resources yet. Future work is tracked in [ROADMAP.md](ROADMAP.md).

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

The health check only checks this process. It does not check a database or external service, because there are none yet. Python's built-in HTTP server is suitable for this local learning stage; we will revisit the server before deployment. It currently listens only on the local machine.

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
.gitignore             Keep generated files and local secrets out of Git
README.md              Setup and project explanation
ROADMAP.md             Future phases
```

## Git workflow

Keep each change small, run the tests, and inspect the diff before committing. For the first commit:

```bash
git status
git add .gitignore README.md ROADMAP.md app/ tests/
git diff --cached
git commit -m "feat: add service status app with health endpoint and basic tests"
```

For later work, use a focused branch, for example `feat/docker-compose`. Write commit messages describing the actual change, such as `docs: explain local troubleshooting`. Never commit credentials or `.env` files; ignoring a file does not remove secrets already tracked by Git.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `python3: command not found` | Install Python 3 through your operating system's package manager. |
| `No module named app` | Run the command from the repository root. |
| `Address already in use` | Another process uses port 8000. Check for another running copy and stop it with `Ctrl+C`. |
| Browser cannot connect | Confirm the server is running and use `http://127.0.0.1:8000`. |
| Page says it cannot reach the service | Inspect the server terminal and try the health URL directly. |

## Phase 1 learning checkpoint

Before moving on, be able to explain what an HTTP route is, why the frontend requests JSON, what the health endpoint proves, and how a test detects a broken response. Try changing the page description, run the tests, and review the change with `git diff`.
