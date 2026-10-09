# Nginx reverse proxy

Nginx receives requests on `127.0.0.1:8080` and forwards them to the Python app on `127.0.0.1:8000`. Both remain local to the VM. The browser still requests the same routes; Nginx passes the path and query string to the app. This configuration adds no domain, TLS certificate, or public listener.

```mermaid
flowchart LR
    Browser[Browser or curl] -->|localhost:8080| Nginx[Nginx]
    Nginx -->|localhost:8000| Python[Service Status Python app]
```

## Install on the learning VM

First complete the [Linux service setup](../README.md) and check that `bash scripts/check.sh` passes on the VM. From a checkout of this repository on a disposable Debian/Ubuntu VM:

```bash
sudo apt-get update
sudo apt-get install nginx
sudo install -m 0644 deploy/nginx/service-status.conf /etc/nginx/sites-available/service-status
sudo ln -s /etc/nginx/sites-available/service-status /etc/nginx/sites-enabled/service-status
sudo nginx -t
sudo systemctl reload nginx
bash scripts/check.sh http://127.0.0.1:8080
curl -I http://127.0.0.1:8080/
curl -i 'http://127.0.0.1:8080/api/status?source=proxy'
```

The symlink command is needed once. On later edits, replace the configuration file, run `nginx -t`, and reload only after it passes. The distribution may enable a separate default site on port 80; inspect that site's listener and disable its symlink if you do not want the default page exposed. This project's site listens only on loopback.

`nginx -t` validates the complete installed configuration, including existing sites, and checks referenced files. The health check must pass through port 8080 as well as directly through port 8000. HEAD should return headers without a body, and the status response should contain startup time and uptime.

For browser access from your workstation:

```bash
ssh -L 9000:127.0.0.1:8080 <vm-user>@<vm-address>
```

Open http://127.0.0.1:9000 while the SSH session is running.

## Rehearse an upstream failure

On the disposable learning VM, stop the app while leaving Nginx running:

```bash
sudo systemctl stop service-status
curl -i http://127.0.0.1:8080/health
sudo tail -n 20 /var/log/nginx/service-status-error.log
sudo systemctl start service-status
bash scripts/check.sh http://127.0.0.1:8080
```

With no process listening on upstream port 8000, expect `502 Bad Gateway` and an upstream connection error in the Nginx log. The check script fails on that response. Restarting the app should restore HTTP 200. A connected upstream that stops responding can produce `504 Gateway Timeout`; the three-second proxy timeouts limit individual waits, rather than guaranteeing a total request deadline.

Inspect access logs with `sudo tail -n 20 /var/log/nginx/service-status-access.log`. An app-generated missing route returns JSON 404 through the proxy; a proxy-generated failure normally returns Nginx's HTML error page. These distinguish application errors from upstream connection failures.

To remove only this site:

```bash
sudo rm /etc/nginx/sites-enabled/service-status
sudo nginx -t
sudo systemctl reload nginx
```

The app service and other Nginx sites remain available.

## Verification status

`tests/test_proxy.py` runs an isolated Nginx instance using this site's configuration with temporary ports and log paths. It validates syntax, checks homepage/health forwarding, query strings, cache headers, HEAD, application JSON 404, and a proxy 502 after stopping the upstream. It cleans up the app, proxy, and temporary files. The tests require an Nginx executable and skip if it is absent.

```bash
python3 -m unittest discover -s tests -p test_proxy.py -v
```

Use `NGINX_BINARY=/path/to/nginx` to select a standalone executable. The GitHub Actions **Nginx integration tests** job installs Nginx on its disposable runner and explicitly requires the executable before running these tests. Local verification passed with an Ubuntu Nginx 1.28.3 executable extracted into `/tmp`: both proxy tests and all 19 tests passed. No system Nginx service was installed. Hosted execution is pending a push and a successful Actions run. Actual VM installation, systemd operation, and recovery remain separate checks.

Reference: [official Nginx proxy module documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
