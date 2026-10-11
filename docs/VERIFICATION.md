# Verification evidence

Recorded 11 October 2026. The application was tested on Python 3.14.4. New changes are local working-tree files; no commit, push, cloud deployment, or hosted CI run was performed during this implementation.

| Check | Result |
| --- | --- |
| `bash scripts/test.sh` | 23 tests run: 21 passed, 2 Nginx integration tests skipped because Nginx is unavailable |
| New metrics tests | Cumulative histogram and totals, 800 concurrent observations without lost counts, bounded labels, real HTTP counters including 404/501, metrics HEAD, JSON request logs and omitted URL secrets passed |
| `scripts/validate-config.py` | Operational YAML, dashboard JSON, and metric exposition parsed successfully using PyYAML 6.0.3 and prometheus-client 0.21.1 |
| Terraform 1.11.2 format/validate | Passed with AzureRM 4.81.0; provider selection recorded in `.terraform.lock.hcl`; no Azure plan/apply performed |
| Helm 3.17.2 lint | Default and dev values passed; chart icon recommendation only |
| Helm rendering | Rendered Deployment and Service parsed; release-specific name and resource limits checked |
| Ansible Core 2.18.3 syntax check | Passed against the example inventory; no server connection made |
| Monitoring Compose config | `docker-compose -f compose.yaml -f monitoring/compose.yaml config --quiet` passed with a validation-only password |
| Elastic Compose config | `docker-compose -p service-status-logs -f logging/compose.yaml config --quiet` passed |
| Bandit 1.9.4 `-r app -ll` | All application files scanned, zero issues, zero files skipped |
| Python compilation / shell syntax / diff whitespace | Passed |

Temporary validation binaries and Python packages were downloaded into `/tmp` because Terraform/Helm/Ansible/pip/venv were initially unavailable. Terraform and Helm archive checksums were verified against their official distribution checksums. System packages and Docker permissions were not changed. HTTP tests and Terraform provider validation required execution outside the sandbox because they bind temporary local sockets. An initial Bandit 1.8.3 run skipped files under Python 3.14; it was replaced with 1.9.4 and rerun successfully, and CI uses that version.

## Remaining execution evidence

- Docker daemon access is denied for the current user. Application image build, container smoke test, monitoring stack, and Elastic ingestion could not run. Configuration validation does not establish runtime health.
- Nginx is absent in this environment. The two live proxy tests were skipped; CI requires Nginx and installs it explicitly.
- GitHub Actions configuration/security/release jobs have not run for these local changes. Gitleaks history scanning is configured but not locally executed.
- Azure credentials/subscription details are absent. A subscription-specific price quote, authenticated Terraform plan, provisioning, deployment, and teardown are pending. No billable cloud resources were created.
- Ansible VM installation, health check, rollback, and `changed=0` second run are pending.
- Prometheus target/query/alert and Grafana live panels are pending, along with Elastic failed-request search.
- Kubernetes/kind installation, pod replacement, Helm install/upgrade/rollback, and Jenkins execution are pending.

Use the linked lab runbooks in the README to collect each missing runtime result. Preserve this distinction when presenting the project in a portfolio.
