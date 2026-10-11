# Metrics and dashboards

The application exposes `/metrics` using Prometheus text format. It records completed requests (including 404 and unsupported methods), a cumulative duration histogram, and uptime. Counters reset at restart. A scrape shows requests completed before that scrape; `/metrics` requests themselves contribute to the next scrape. HEAD records a request but sends no body. Unknown paths use `route="unknown"`, and unknown methods use `method="OTHER"`, keeping label cardinality bounded. Query strings never become labels.

From the repository root, after obtaining Docker daemon access:

```bash
export GRAFANA_ADMIN_PASSWORD='choose-a-local-password'
docker compose -f compose.yaml -f monitoring/compose.yaml config --quiet
docker compose -f compose.yaml -f monitoring/compose.yaml up --build -d
curl http://127.0.0.1:8000/metrics
```

Open http://127.0.0.1:9090/targets and confirm `service-status` is UP. In Prometheus, query `service_status_http_requests_total` and `service_status_uptime_seconds`. Open http://127.0.0.1:3000, sign in as `admin` using your supplied password, and open the provisioned **Service Status** dashboard. Generate traffic with `curl http://127.0.0.1:8000/health` and generate a 404 with `curl http://127.0.0.1:8000/missing`. Rate panels need at least two scrapes; the latency histogram includes health checks and monitoring requests.

The alerts are evaluated in Prometheus, without notification delivery. Stop the app with the same Compose files and `stop app`; after a minute, `ServiceStatusDown` should fire in `/alerts`. Start the app again and confirm the alert resolves. Prometheus and Grafana share the application's Compose network. Their host ports listen only on loopback.

```bash
docker compose -f compose.yaml -f monitoring/compose.yaml down
# Add --volumes only when you intend to delete local monitoring history.
```

Runtime verification is pending Docker access. The exposition is regression-tested and can be parsed independently with `PYTHONPATH=. python3 scripts/validate-config.py` after installing `requirements-dev.txt`. Image versions are explicit learning baselines; review security updates before public deployment.

References: [Prometheus format](https://prometheus.io/docs/instrumenting/exposition_formats/) and [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).
