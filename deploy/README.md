# Linux service deployment

This is a deployment guide for a disposable Debian/Ubuntu VM with systemd, Python 3.10 or newer at `/usr/bin/python3`, Bash, and curl. The release-building machine needs Python 3.12 or newer. The unit is prepared and can be checked locally; a real VM installation has not been performed.

The layout is `/opt/service-status/releases/<commit>/app/`, with `/opt/service-status/current` pointing at the selected release directory. A dedicated `service-status` account runs the app. Release files belong to root; the service cannot modify them. The service listens on `127.0.0.1:8000`. It is intended for this learning stage using Python's built-in HTTP server.

## Prepare a release

On the development machine, from the repository root:

```bash
python3 scripts/release.py HEAD
```

Copy the generated archive and its `.sha256` file, `deploy/systemd/service-status.service`, and `scripts/check.sh` to a staging directory on the VM. Use your VM's actual SSH address. Run the following commands from that staging directory, replacing `<full-commit>` with the archive's full commit hash:

```bash
sha256sum -c service-status-<full-commit>.tar.gz.sha256
sudo useradd --system --user-group --no-create-home --shell /usr/sbin/nologin service-status
sudo mkdir -p /opt/service-status/releases/<full-commit>
sudo tar --no-same-owner -xzf service-status-<full-commit>.tar.gz -C /opt/service-status/releases/<full-commit>
sudo chmod -R a+rX /opt/service-status/releases/<full-commit>
sudo ln -s /opt/service-status/releases/<full-commit> /opt/service-status/current
sudo install -m 0644 service-status.service /etc/systemd/system/service-status.service
sudo systemd-analyze verify /etc/systemd/system/service-status.service
sudo systemctl daemon-reload
sudo systemctl enable --now service-status
bash check.sh
```

These are first-install commands: create the account and `current` symlink once. If the account already exists, inspect it with `id service-status` and skip `useradd`. For subsequent releases, extract into a new directory and follow the switching commands below. The app needs no pip packages. Keep existing releases until the replacement has been verified.

## Operate and inspect

```bash
sudo systemctl status service-status --no-pager
sudo journalctl -u service-status -n 50 --no-pager
bash check.sh http://127.0.0.1:8000
sudo systemctl restart service-status
bash check.sh
```

`Restart=on-failure` restarts a process that exits unsuccessfully, with a three-second delay and a limit of five starts per minute. It does not detect an unhealthy HTTP response from a still-running process. `check.sh` uses a five-second request timeout and fails for HTTP errors, malformed JSON, and unexpected health data. It can also check a locally running app before you have a VM.

If port 8000 is busy, inspect the competing process before changing settings. The unit's environment controls its bind address and port; after editing the unit, run `daemon-reload` and restart. Pass the matching base URL to `check.sh`. If repeated failures reach the start limit, resolve the cause, run `sudo systemctl reset-failed service-status`, and start it again.

## Deploy a replacement or roll back

Verify and extract the replacement archive into a new release directory first. Then replace `<target-commit>` with the desired release, either the candidate or a retained previous release:

```bash
sudo systemctl stop service-status
sudo ln -sfn /opt/service-status/releases/<target-commit> /opt/service-status/current
sudo systemctl start service-status
bash check.sh
```

The switch causes downtime. If the new release fails, inspect the journal and repeat these commands with the previous commit. `current` must be a symlink, not a directory. A health check confirms the process responds; the symlink and the selected release's `release.json` identify the deployed source commit.

To view the dashboard from your workstation, forward the VM's loopback port using `ssh -L 9000:127.0.0.1:8000 <vm-user>@<vm-address>` and open http://127.0.0.1:9000. Keep the SSH session running. Reverse proxy and public access configuration come in a later phase.

## Remove the service

```bash
sudo systemctl disable --now service-status
sudo rm /etc/systemd/system/service-status.service
sudo systemctl daemon-reload
```

The release directories and account remain for inspection. Remove those separately when no longer needed, and delete the disposable VM through its hosting provider to stop its charges.

Reference: [systemd service configuration](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
