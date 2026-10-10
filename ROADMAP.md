# Project roadmap

Build on the same Service Status application one small stage at a time. Phase 1 is complete. Phase 2 configuration is added; image build and runtime verification are pending Docker daemon access. Phase 3 adds HTTP regression tests and a Bash test runner. Phase 4 adds a GitHub Actions workflow; hosted verification is pending. Each later phase should add one or two concepts, leave the application working, and update the README with commands that have been verified.

| Phase | Focus | Working result / completion check |
| --- | --- | --- |
| 1 | Basic application and Git structure | Local frontend, Python API, health endpoint, basic HTTP tests, and setup instructions. |
| 2 | Docker and Docker Compose | Configuration added. Pending: build and run the container, verify `/health` and healthy status, then stop it cleanly. |
| 3 | Automated testing | HTTP tests cover normal requests, query strings, file-path rejection, error recovery, runtime status, HEAD, and port configuration; a Bash script runs the suite. |
| 4 | GitHub Actions CI | Workflow added for pushes, pull requests, and manual runs on Python 3.10 and 3.14. Pending: inspect passing hosted jobs and demonstrate a failing check. |
| 5 | CD/deployment pipeline | Added commit-versioned archives, SHA-256 checksums, and extracted-release HTTP smoke checks; added an automated previous/candidate/previous process-switch rehearsal on one temporary port. Added a test-gated CI package/checksum/artifact job. Pending: verify hosted artifact upload and download; connect a server in Phase 6. |
| 6 | Linux server deployment | Added a systemd unit, Bash health-check script, failure-path tests, and VM installation/rollback guide. Pending: install on a VM and verify startup, restart, logs, and rollback. |
| 7 | Nginx reverse proxy | Added loopback proxy configuration, setup guide, live forwarding/failure tests, and a dedicated CI job. Local proxy validation and both live tests passed with Nginx 1.28.3. Pending: hosted test execution and installed VM verification. |
| 8 | Terraform infrastructure | Describe the intended infrastructure in code and review its plan before provisioning. |
| 9 | Azure deployment | Provision and deploy to Azure with a cost estimate and documented teardown. |
| 10 | Ansible configuration | Configure the server repeatably; a second run should make no unnecessary changes. |
| 11 | Prometheus monitoring | Expose and scrape useful application metrics; verify a query. |
| 12 | Grafana dashboards | Create a small dashboard for traffic, errors, and latency using real metrics. |
| 13 | Centralized logging with Elastic Stack | Ship structured application logs, search for a failed request, and document resource needs. |
| 14 | Jenkins pipeline | Reproduce the existing build/test workflow in Jenkins and explain its tradeoffs against GitHub Actions. |
| 15 | Kubernetes | Deploy to a local cluster with health probes and demonstrate recovery from a stopped pod. |
| 16 | Helm | Package the working Kubernetes deployment with environment-specific values. |
| 17 | Security improvements, secrets, and scanning | Review access, move deployment secrets into an appropriate secret store, and add useful scanning checks. |
| 18 | Documentation and portfolio cleanup | Verify setup instructions, add an architecture diagram, and document a troubleshooting incident and design decisions. |

Security basics apply throughout: do not commit secrets, avoid unnecessary public exposure, and review dependencies when adding them. Phase 17 deepens those practices.

These phases are a direction, not a requirement to run every tool at once. Revisit the scope before each stage. Add infrastructure folders only when there is actual infrastructure to put in them. Keep cloud resources temporary until their costs and cleanup are understood.

## Progress and remaining work

There are 18 planned phases. This is a learning roadmap, not a time estimate: later phases vary substantially in size.

- **2 complete locally:** Phase 1 application and Phase 3 automated testing.
- **5 built or partly built, awaiting further work:** Phase 2 Docker runtime verification; Phase 4 hosted CI and failed-check exercise; Phase 5 hosted release delivery; Phase 6 VM installation and recovery checks; Phase 7 hosted proxy tests and installed VM checks (local proxy tests pass).
- **11 later phases not started:** Phases 8–18, covering Terraform, Azure, Ansible, monitoring, centralized logging, Jenkins, Kubernetes, Helm, deeper security, and portfolio cleanup.

The next useful milestone is verifying the existing Docker, CI, Linux service, and proxy setup. A working deployment with CI and basic monitoring can be a useful portfolio milestone before attempting every later tool. Do not treat a configuration file as a completed runtime deployment.

## Routine for each stage

1. Explain the problem and the one or two concepts being introduced.
2. Make the smallest useful change on a focused Git branch.
3. Run the tests and check the application manually where needed.
4. Update the README with setup, verification, and troubleshooting notes.
5. Review the diff and create a commit describing the change.
6. Record what was learned before starting the next phase.
