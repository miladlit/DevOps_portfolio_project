# Repeatable VM configuration

Use an Ubuntu/Debian VM you control, SSH key access, and an account with sudo privileges. Install Ansible on your workstation. Runtime deployment and second-run idempotence have not yet been verified against a VM.

From the repository root, build a committed release and verify its checksum (new uncommitted application changes are excluded):

```bash
python3 scripts/release.py HEAD
cp deploy/ansible/inventory.example.ini deploy/ansible/inventory.ini
```

Edit the ignored `inventory.ini` with the VM's real IP and SSH user. Record the full commit and archive SHA-256 printed by `sha256sum`; supply these values below:

```bash
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/deploy.yaml --syntax-check
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/deploy.yaml --check --diff -e release_commit=FULL_COMMIT -e release_sha256=ARCHIVE_SHA256
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/deploy.yaml -e release_commit=FULL_COMMIT -e release_sha256=ARCHIVE_SHA256
```

Use `--ask-become-pass` if sudo requires a password. On a fresh VM, check mode cannot simulate every task that needs a directory/file created by an earlier task; syntax checking and reviewing the diff remain useful. The playbook installs packages, creates the dedicated account, verifies the copied archive's SHA-256, extracts it once, selects the release symlink, and installs systemd/Nginx. Handlers restart only when configuration or the selected release changes. Health is checked through the loopback proxy after handlers run.

Repeat the same real command: confirm `changed=0` and a passing health check. To roll back, rerun with a previously verified commit and checksum whose archive remains in local `dist/`; the previous release stays on the VM. There is brief downtime on restart. Failure of the health check fails the playbook; it does not automatically roll back. Do not run this against an unmanaged server without reviewing existing Nginx sites and service paths.
