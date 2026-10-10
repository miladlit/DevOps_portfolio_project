#!/usr/bin/env bash
# Build and verify an isolated container; remove only resources created here.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
docker info >/dev/null
image="service-status-smoke:$(python3 -c 'import uuid; print(uuid.uuid4().hex)')"
container="${image/:/-}"
cleanup() {
  result=$?
  trap - EXIT
  if (( result != 0 )); then
    docker logs "$container" >&2 || true
  fi
  if docker container inspect "$container" >/dev/null 2>&1; then
    if ! docker rm --force "$container" >/dev/null; then
      echo "Could not remove temporary container: $container" >&2
      result=1
    fi
  fi
  if ! docker image rm "$image" >/dev/null 2>&1; then
    echo "Could not remove temporary image: $image" >&2
    result=1
  fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
docker build --tag "$image" .
docker run --detach --name "$container" --publish 127.0.0.1::8000 \
  --health-cmd "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).close()\"" \
  --health-interval 1s --health-timeout 3s --health-retries 3 \
  "$image" >/dev/null
healthy=false
for (( attempt=0; attempt<30; attempt++ )); do
  state="$(docker inspect --format '{{.State.Status}} {{.State.Health.Status}}' "$container")"
  if [[ "$state" == 'running healthy' ]]; then
    healthy=true
    break
  fi
  if [[ "$state" != running* || "$state" == 'running unhealthy' ]]; then
    echo "Container failed readiness: $state" >&2
    exit 1
  fi
  sleep 1
done
if [[ "$healthy" != true ]]; then
  echo "Container did not become healthy within 30 checks" >&2
  exit 1
fi
[[ "$(docker exec "$container" id -u)" == 10001 ]]
address="$(docker port "$container" 8000/tcp)"
[[ "$address" == 127.0.0.1:* ]]
bash scripts/check.sh "http://$address"
curl --fail --silent --show-error --max-time 5 "http://$address/" |
  python3 -c 'import sys; assert "<h1>Service Status</h1>" in sys.stdin.read(), "Missing homepage"'
echo "Container smoke check passed (health, homepage, non-root user)"
