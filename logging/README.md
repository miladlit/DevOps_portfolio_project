# Local Elastic logging lab

The app writes one JSON request event per completed response to stderr. Events include UTC timestamp, request ID, method, normalized route, response status, and server duration. They exclude query strings and client addresses. Startup text stays on stdout. This is request logging, not distributed tracing.

Use `curl -i http://127.0.0.1:8000/health` to see the `X-Request-ID` response header. Match that value to `request_id` in the JSON logs, or search `request_id : "<returned-id>"` in Kibana after ingestion. The server generates a fresh ID for each request and ignores client-supplied IDs; IDs are not Prometheus labels.

This optional lab uses roughly 3 GB of container memory plus host overhead. Run it separately from other stacks on a small machine. Elasticsearch and Kibana host ports are loopback-only; Elasticsearch authentication is disabled for this isolated local exercise. Do not expose this configuration publicly. Docker daemon access is required.

From the repository root, start the app in one terminal:

```bash
mkdir -p logging/data
python3 -m app.server 2>>logging/data/requests.jsonl
```

In another terminal:

```bash
docker compose -p service-status-logs -f logging/compose.yaml config --quiet
docker compose -p service-status-logs -f logging/compose.yaml up -d
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/missing
```

Logstash reads the JSONL file and sends it to `service-status-YYYY.MM.dd`. Wait for Elasticsearch and Kibana startup, then open http://127.0.0.1:5601 and create a data view `service-status-*` with timestamp `@timestamp`. In Discover, query `event : "http_request" and status : 404`; inspect route `unknown`. If nothing appears, inspect `docker compose -p service-status-logs -f logging/compose.yaml logs logstash`. Elasticsearch may require the host's `vm.max_map_count` to be configured by its administrator; check its logs if startup fails.

```bash
docker compose -p service-status-logs -f logging/compose.yaml down
```

Use `down --volumes` to deliberately discard indexed history. Stop the Python app with Ctrl+C. The local JSONL file is ignored by Git. Runtime ingestion/search remains unverified here; this lab does not ship Docker or systemd logs automatically.
