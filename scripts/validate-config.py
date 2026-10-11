"""Parse operational YAML/JSON and check metric exposition (dev dependencies only)."""
from pathlib import Path
import json
import yaml
from prometheus_client.parser import text_string_to_metric_families
from app.metrics import Metrics

ROOT = Path(__file__).resolve().parents[1]
paths = list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml"))
for path in paths:
    if any(part in {".git", ".venv", ".terraform", "templates"} for part in path.parts):
        continue
    with path.open() as source:
        list(yaml.safe_load_all(source))
for path in (ROOT / "monitoring/grafana/dashboards").glob("*.json"):
    dashboard = json.loads(path.read_text())
    assert dashboard["panels"], f"No dashboard panels: {path}"
metrics = Metrics()
metrics.observe("GET", "/health", 200, 0.02)
families = list(text_string_to_metric_families(metrics.render(10).decode()))
assert {family.type for family in families} == {"gauge", "counter", "histogram"}
print("Operational YAML, dashboard JSON, and Prometheus exposition validated.")
