# Publish-Automate
 Automation script for application publishing

## How to Use
1. In [Fine-grained PAT](https://github.com/settings/tokens?type=beta), renew the `Publish-Automate` the token, and update it to actions secrets as `PAT_TOKEN`
   - The token should have access to `Snap.Hutao` and `Snap.Hutao.Docs` repositories access
   - The token requires `rw` permission on `Contents`, `Issues`, `Pull requests`
2. Run GitHub Actions
