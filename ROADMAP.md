# Project roadmap

Build on the same Service Status application in stages. Every planned phase now has application code, operational configuration, or documentation. Runtime completion is recorded separately: local HTTP/metrics tests pass, while Docker, hosted CI, VM/cloud, observability stacks, Jenkins, and cluster exercises still require their execution environments. A configuration file is not evidence of a successful deployment.

| Phase | Focus | Working result / completion check |
| --- | --- | --- |
| 1 | Basic application and Git structure | Local frontend, Python API, health endpoint, basic HTTP tests, and setup instructions. |
| 2 | Docker and Docker Compose | Configuration and a test-gated CI container smoke check added. Pending: build and run the container, verify `/health` and healthy status, then stop it cleanly. |
| 3 | Automated testing | HTTP tests cover normal requests, query strings, file-path rejection, error recovery, runtime status, HEAD, and port configuration; a Bash script runs the suite. |
| 4 | GitHub Actions CI | Workflow added for pushes, pull requests, and manual runs on Python 3.10 and 3.14. Pending: inspect passing hosted jobs and demonstrate a failing check. |
| 5 | CD/deployment pipeline | Added commit-versioned archives, SHA-256 checksums, and extracted-release HTTP smoke checks; added an automated previous/candidate/previous process-switch rehearsal on one temporary port. Added a test-gated CI package/checksum/artifact job. Pending: verify hosted artifact upload and download; connect a server in Phase 6. |
| 6 | Linux server deployment | Added a systemd unit, Bash health-check script, failure-path tests, and VM installation/rollback guide. Pending: install on a VM and verify startup, restart, logs, and rollback. |
| 7 | Nginx reverse proxy | Added loopback proxy configuration, setup guide, live forwarding/failure tests, and a dedicated CI job. Local proxy validation and both live tests passed with Nginx 1.28.3. Pending: hosted test execution and installed VM verification. |
| 8 | Terraform infrastructure | Azure VM/network/SSH resources and variables added; local format/validation checks. Pending: authenticated plan review. |
| 9 | Azure deployment | SSH-tunnel deployment guide, cost worksheet, and teardown commands added. Pending: dated pricing quote, provision/deploy/destroy exercise. |
| 10 | Ansible configuration | Verified-archive deployment, systemd/Nginx configuration, handlers, health check, and explicit rollback added. Pending: VM execution and changed=0 second run. |
| 11 | Prometheus monitoring | Thread-safe request counters, latency histogram, uptime, scrape and alert configuration added; HTTP/concurrency/exposition tests. Pending: live scrape/query/alert exercise. |
| 12 | Grafana dashboards | Provisioned Prometheus source and five-panel dashboard added. Pending: live dashboard verification. |
| 13 | Centralized logging with Elastic Stack | Structured request logs and optional file-to-Logstash/Elasticsearch/Kibana lab added, with resource/cleanup guide. Pending: ingestion and failed-request search. |
| 14 | Jenkins pipeline | Tests/container/package/checksum/archive pipeline and runner tradeoffs documented. Pending: actual Jenkins agent run. |
| 15 | Kubernetes | Two-replica deployment, internal Service, probes, limits, security context, and kind recovery guide added. Pending: local cluster execution. |
| 16 | Helm | Chart with default/dev values added; both linted and rendered locally. Pending: install/upgrade/rollback in a cluster. |
| 17 | Security improvements, secrets, and scanning | Response headers, restricted execution/access, secret exclusions, Bandit/Gitleaks CI, Dependabot, and security scope added. Pending: hosted scans and production access/TLS/secret-store review. |
| 18 | Documentation and portfolio cleanup | Architecture diagram, design decisions, upstream-branch incident, lab runbooks, and honest verification record added. Pending: runtime evidence/screenshots from external labs. |

Security basics apply throughout: do not commit secrets, avoid unnecessary public exposure, and review dependencies when adding them. Phase 17 deepens those practices.

These phases are a direction, not a requirement to run every tool at once. Revisit the scope before each stage. Add infrastructure folders only when there is actual infrastructure to put in them. Keep cloud resources temporary until their costs and cleanup are understood.

## Progress and remaining work

There are 18 planned phases. This is a learning roadmap, not a time estimate: later phases vary substantially in size.

- **Verified locally:** basic application and HTTP regression suite, metrics accounting/concurrency/HTTP logs, Helm default/dev lint and rendering, configuration parsing. See [verification evidence](docs/VERIFICATION.md) for final checks and exact limitations.
- **Built, awaiting runtime evidence:** Docker/Compose, hosted CI/artifacts/security scans, VM service/proxy, Azure/Terraform deployment, Ansible idempotence, Prometheus/Grafana, Elastic ingestion, Jenkins, Kubernetes and Helm runtime.
- **Cloud activity:** none. A cost worksheet and teardown steps exist; a subscription-specific quote and plan review are still required before provisioning.

The repository now contains the planned learning implementations. The project is not end-to-end deployment-verified until the pending runtime exercises above pass.

## Routine for each stage

1. Explain the problem and the one or two concepts being introduced.
2. Make the smallest useful change on a focused Git branch.
3. Run the tests and check the application manually where needed.
4. Update the README with setup, verification, and troubleshooting notes.
5. Review the diff and create a commit describing the change.
6. Record what was learned before starting the next phase.
