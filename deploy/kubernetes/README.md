# Kubernetes and Helm lab

Requires Docker access, kind, kubectl, and Helm 3. All commands run from the repository root. Use a disposable local cluster; the Service is internal and no cloud load balancer is created.

```bash
kind create cluster --name service-status
docker build -t service-status:local .
kind load docker-image service-status:local --name service-status
kubectl --context kind-service-status create namespace service-status
kubectl --context kind-service-status -n service-status apply -f deploy/kubernetes/app.yaml
kubectl --context kind-service-status -n service-status rollout status deployment/service-status --timeout=120s
kubectl --context kind-service-status -n service-status port-forward service/service-status 9000:80
```

Keep port-forward running and check `curl http://127.0.0.1:9000/health`. In another terminal, delete one pod selected by `app=service-status` and watch `kubectl --context kind-service-status -n service-status get pods -w` create its replacement. Reconnect port-forward if its chosen pod was deleted. Startup, readiness, and liveness probes use `/health`; resource limits, a non-root UID, a read-only root filesystem, and dropped capabilities constrain the container.

To use Helm instead, remove the plain manifests first:

```bash
kubectl --context kind-service-status -n service-status delete -f deploy/kubernetes/app.yaml
helm lint deploy/helm/service-status
helm template demo deploy/helm/service-status -f deploy/helm/service-status/values-dev.yaml
helm --kube-context kind-service-status upgrade --install demo deploy/helm/service-status --namespace service-status -f deploy/helm/service-status/values-dev.yaml --wait --timeout 120s
kubectl --context kind-service-status -n service-status port-forward service/demo-service-status 9000:80
```

Default values use two replicas; dev values use one. For a real registry, supply `--set image.repository=YOUR_REGISTRY/service-status --set image.tag=COMMIT` and configure registry access. Use unique image tags for changes: loading a new image under `local` does not replace running pods automatically. `helm history demo -n service-status` shows revisions; after a second successful upgrade, `helm rollback demo 1 -n service-status --wait` rehearses rollback. Include `--kube-context kind-service-status` when operating outside this lab context.

```bash
kind delete cluster --name service-status
```

Manifest creation is complete; cluster recovery and Helm runtime verification remain pending. [Kubernetes probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/).
