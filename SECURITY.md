# Security scope

This is a learning project. Report a vulnerability privately to the repository owner through GitHub rather than posting credentials or sensitive logs in a public issue.

Implemented controls include explicit HTTP routes, fresh status responses, `nosniff` and referrer headers, a non-root container, a restricted systemd account, loopback port bindings, SSH-key-only Azure access restricted to one /32, Kubernetes security contexts/resource limits, checksum verification before VM extraction, bounded metric labels, and request logs that omit URL queries and client addresses.

The configuration/security workflow runs Bandit against the application and Gitleaks against Git history. Dependabot checks GitHub Actions, the application Dockerfile, and Terraform. Passing a scan is not a security audit. Pinned monitoring/Elastic/Jenkins tooling baselines need periodic review; Compose image updates are manual.

Keep credentials in environment variables or a secret manager. Never commit private keys, `.env`, state, plans, or inventory with sensitive details. For a future cloud deployment, prefer GitHub-to-Azure OIDC with restricted roles and environment protections; no long-lived deployment credential is configured here. Terraform state must be protected separately even though it is ignored by Git. Before public access, add TLS, authentication where needed, rate limiting, an appropriate production HTTP server, image vulnerability scanning, and threat/load testing. The Elastic configuration deliberately disables authentication for an isolated local lab and must not be exposed publicly.
