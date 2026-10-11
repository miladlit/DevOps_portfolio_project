# Incident: new branch could not be pushed

## Symptom

On the `feat/container-smoke-check` branch, `git push` returned: `fatal: The current branch feat/container-smoke-check has no upstream branch.`

## Cause and resolution

The local branch had no tracking relationship to a remote branch. Running `git push --set-upstream origin feat/container-smoke-check` publishes the branch and records that relationship. Later inspection showed `feat/container-smoke-check...origin/feat/container-smoke-check`, confirming the tracking relationship exists locally.

## Verification and learning

Use `git branch -vv` to inspect upstreams and `git status --short --branch` to check divergence. A clean working tree does not prove a branch was pushed, and a remote tracking reference is a cached observation. Verify the live GitHub branch and Actions run separately. Setting an upstream fixes the Git configuration error; it does not resolve credentials, DNS, or CI failures.
