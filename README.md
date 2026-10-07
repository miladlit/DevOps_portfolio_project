# DevOps Portfolio Project

A project I am building in small stages to learn how to run an application reliably, from local development to cloud deployment.

The application is **Service Status**: a small web page that displays the service name, version, and health. Keeping the application simple leaves room to focus on testing, delivery, infrastructure, and troubleshooting.

## Current stage

Phase 5: local release packaging and extracted-release smoke checks are added. Phase 4 GitHub Actions CI configuration is added for the automated HTTP tests. Its first hosted run is pending a push to GitHub. Phase 2 container runtime verification is still pending local Docker access. There are no cloud resources yet. Future work is tracked in [ROADMAP.md](ROADMAP.md).

## Run locally

You need Python 3.10 or newer and Git. The application and tests use only Python's standard library; there are no packages to install.

From the repository root (the directory containing this README):

```bash
python3 --version
python3 -m app.server
```

Open **http://127.0.0.1:8000** in a browser. Use **Check again** to refresh the status, or enable **Refresh every 10 seconds**. The page shows server uptime and the last successful check time. Requests time out after five seconds, allowing you to retry if the service stops responding. Stop the server with `Ctrl+C`.

In a second terminal, you can check the API directly:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/api/info
```

The health endpoint should return HTTP `200` and `{"status": "ok"}`.

### Review recent checks

The dashboard measures each complete check (all three API requests and JSON parsing) and displays its duration in milliseconds. The recent-check table keeps the last 20 results in the current tab, including failures and five-second timeouts. A summary counts successful checks in that window; it is not a long-term availability metric.

Use **Clear history** to reset the table and summary. Reloading the page also resets history. Check duration includes browser and network time, so it is not a server-only latency measurement. Unexpected API data is recorded as a failed check.

### Use a different local port

Set `APP_PORT` when port 8000 is busy:

```bash
APP_PORT=9000 python3 -m app.server
curl -I http://127.0.0.1:9000/health
```

Open **http://127.0.0.1:9000** for this run. The default port is 8000; invalid values outside the integer range 1–65535 stop startup with a clear message. `APP_HOST` still controls the bind address. The supplied Docker Compose configuration uses container port 8000; changing the container port also requires updating its port mapping and health check.

`curl -I` sends a `HEAD` request. All GET routes also support HEAD, returning the same status and headers without a response body. Unknown HEAD routes return `404` without a body.

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
| `GET /api/status` | Return UTC startup time and uptime in seconds |
| `GET /health` | Report that the HTTP service can respond |

Uptime is measured with a monotonic clock and resets when the server restarts. `/api/status` returns `started_at` (an ISO 8601 UTC timestamp) and `uptime_seconds` (a number). Responses include `Cache-Control: no-store` so checks use fresh data.

Unknown routes return HTTP `404` with a JSON error. Requests are logged to the terminal.

The health check only checks this process. It does not check a database or external service, because there are none yet. Python's built-in HTTP server is suitable for this local learning stage; we will revisit the server before deployment. Direct Python runs listen only on the local machine; the container uses the networking settings explained above.

## Run the tests

From the repository root:

```bash
bash scripts/test.sh
```

The script locates the repository using its own path and runs Python's built-in test runner. You can also call it by its full path from another directory. A failure produces a nonzero exit code, which the CI workflow uses to mark a check as failed.

The underlying command is still available:

```bash
python3 -m unittest discover -s tests -v
```

The HTTP tests start their own server on a temporary local port, make real HTTP requests, and stop it afterward. You do not need to start the application first, and port 8000 is not used by the tests.

| Behavior | Why test it? |
| --- | --- |
| Health, application info, and homepage | Confirm normal requests return the expected content. |
| HEAD requests | Confirm successful and missing routes send headers without a body. |
| Port configuration | Confirm default/custom ports and reject invalid values before startup. |
| Runtime status and cache headers | Confirm elapsed time, timezone-aware startup time, and fresh status responses. |
| Unknown route | Confirm a missing page returns `404` with a JSON error. |
| API requests with query strings | A query such as `?source=test` should not break route matching. |
| Requests for source files and parent paths | The server should only expose its explicit routes, not repository files. |
| Unsupported POST followed by GET | The server should reject the method and still answer a health request. |

The current standard-library handler returns `501` with an HTML error for unsupported methods; our unknown GET routes return JSON `404` errors. The tests document both behaviors. The file-path cases are regression checks, not a full security audit.

To run only the error-recovery test:

```bash
python3 -m unittest discover -s tests -v -k unsupported_method
```

Read `FAIL` as an assertion mismatch and `ERROR` as an unexpected exception. Start with the named test and traceback. For a small learning exercise, temporarily change the expected health value in `test_health` from `ok` to `broken`, run the tests, then undo that edit and confirm they pass. Do not commit the deliberate failure.

Browser JavaScript and Docker networking are not covered by these tests. Check the page manually and complete the container verification separately.

## GitHub Actions CI

`.github/workflows/ci.yml` runs `bash scripts/test.sh` on pushes and pull requests. Two independent jobs check Python 3.10 (the documented minimum) and 3.14 (the Docker image version). Each uses a fresh Ubuntu runner, read-only repository permissions, and a five-minute timeout. No packages or secrets are needed.

The workflow follows the official [Python CI guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) and [setup-python instructions](https://github.com/actions/setup-python). CI means the same automated checks run for every proposed change; a failing test produces a failed job.

After committing and pushing this change, open the repository's **Actions** tab, select **CI**, and inspect **Run HTTP tests** in both jobs. A successful local run does not prove the hosted workflow has run. After the workflow exists on the default branch, **Run workflow** also allows a manual run.

To practice diagnosing a failed check, use a temporary branch: change the expected health value in `test_health` from `ok` to `broken`, confirm the local tests fail, and push the branch. Inspect the failed assertion in Actions, restore `ok`, and push again to see the jobs pass. Keep the deliberate failure out of the default branch.

The workflow checks Python HTTP behavior. Browser behavior and Docker build/runtime verification remain separate checks. Local Docker access is still denied by the socket permissions; adding CI does not complete Phase 2. Hosted success and the failed-check exercise remain pending until performed on GitHub.

## Package and rehearse a release locally

Phase 5 starts with a release package that can run independently of the working folder. Use Python 3.12 or newer for this script (the application still supports Python 3.10).

```bash
python3 scripts/release.py HEAD
```

The script packages only committed `app/` files, extracts them into a temporary directory, and checks the real HTTP health endpoint and homepage on a temporary port. It stops the temporary server afterward. Uncommitted edits are excluded. A failed smoke check stops packaging.

The resulting `dist/service-status-<full-commit>.tar.gz` contains the application and `release.json` recording the source commit. A neighboring `.sha256` file allows checking the archive before extraction. Existing archives are never overwritten. `dist/` is ignored by Git.

To run a packaged release, replace `<full-commit>` with the commit printed in the archive filename:

```bash
cd dist
sha256sum -c service-status-<full-commit>.tar.gz.sha256
mkdir release-<full-commit>
tar -xzf service-status-<full-commit>.tar.gz -C release-<full-commit>
cd release-<full-commit>
APP_PORT=9000 python3 -m app.server
```

Open http://127.0.0.1:9000 and check `/health`. Stop it with Ctrl+C. Keep the previous extracted release directory. To rehearse rollback, stop the new process, switch to the previous directory, and start it with the same command and port; verify health again. This is a manual local deployment rehearsal, with downtime while switching processes.

You can package an earlier commit with `python3 scripts/release.py HEAD~1`. Packages from commits `a2c9616` and `d10e55f` were verified locally: both passed health and homepage checks, and their archive contents and SHA-256 checksums were checked. Smoke checks confirm each package can start and serve its files independently. A server deployment pipeline, hosted release artifacts, and automated rollback come later; this step creates no cloud resources.

### Automated deployment and rollback rehearsal

On Linux with Python 3.12 or newer, run:

```bash
python3 scripts/rehearse.py
```

This packages `HEAD~1` and `HEAD`, verifies their checksums, and extracts them into separate temporary directories. It starts the previous release, stops it, starts the candidate on the same localhost port, then stops it and starts the previous release again. Each step must pass health and homepage checks. The script prints the source commit for each step and removes its temporary files and processes afterward, including on failure.

Choose two other committed revisions with:

```bash
python3 scripts/rehearse.py --previous d10e55f --candidate HEAD
```

The revisions must resolve to different commits. Even if their application files are identical, this checks packaging and switching processes; it does not prove a behavior change. The port is chosen automatically, so the rehearsal does not stop an existing app or use port 8000. A failed candidate stops the rehearsal with a nonzero exit code; this is a controlled exercise, not automatic recovery of a live service. Persistent storage, traffic switching, and VM deployment remain future work.

## Project structure

```text
.github/workflows/
  ci.yml                GitHub Actions HTTP test workflow
app/
  __init__.py           Python package marker
  server.py             HTTP routes and local server entry point
  static/
    index.html          Frontend, styles, and browser JavaScript
tests/
  test_server.py        HTTP success, error, and regression tests
scripts/
  test.sh               Repeatable local test command
  release.py            Package and smoke-test a committed application
  rehearse.py           Rehearse local deployment and rollback
Dockerfile             Package the application with Python
compose.yaml           Container run settings and health check
.dockerignore          Limit files sent to the image build
.gitignore             Keep generated files and local secrets out of Git
README.md              Setup and project explanation
ROADMAP.md             Future phases
```

## Git workflow

Keep each change small, run the tests, and inspect the diff before committing. For the testing change:

```bash
git status
git add tests/test_server.py scripts/test.sh README.md ROADMAP.md
git diff --cached
git commit -m "test: expand HTTP regression coverage and add test runner"
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

## Phase 3 learning checkpoint

Explain why an error response can be a passing test, how `subTest` identifies a failing input, and why test commands must return a failure exit code. Run the full suite before each commit. Container verification remains a separate unfinished check alongside CI setup.

## Phase 4 learning checkpoint

Explain the difference between a workflow, a job, and a step, why CI calls the same script as local development, and why testing two Python versions is useful. Inspect a passing hosted run and practice the failing-check exercise above before treating this phase as verified.
