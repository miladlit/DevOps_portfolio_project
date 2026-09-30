# Project roadmap

Build on the same Service Status application one small stage at a time. Only Phase 1 is implemented. Each later phase should add one or two concepts, leave the application working, and update the README with commands that have been verified.

| Phase | Focus | Working result / completion check |
| --- | --- | --- |
| 1 | Basic application and Git structure | Local frontend, Python API, health endpoint, basic HTTP tests, and setup instructions. |
| 2 | Docker and Docker Compose | Build a container and run the app with Compose; verify `/health`. |
| 3 | Automated testing | Expand failure-case coverage and document a repeatable test workflow. |
| 4 | GitHub Actions CI | Run tests automatically on pushes and pull requests; demonstrate a failing check. |
| 5 | CD/deployment pipeline | Package a versioned release and rehearse deployment and rollback locally; connect a server in Phase 6. |
| 6 | Linux server deployment | Deploy to a Linux VM, manage the service, and use a small Bash script for repeatable checks. |
| 7 | Nginx reverse proxy | Route traffic through Nginx and explain ports, proxy settings, and request failures. |
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

## Routine for each stage

1. Explain the problem and the one or two concepts being introduced.
2. Make the smallest useful change on a focused Git branch.
3. Run the tests and check the application manually where needed.
4. Update the README with setup, verification, and troubleshooting notes.
5. Review the diff and create a commit describing the change.
6. Record what was learned before starting the next phase.
