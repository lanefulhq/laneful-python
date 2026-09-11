# Laneful Python examples

Copy `env.example` to `.env` and fill in your values.

Email sending uses a send host (`LANEFUL_BASE_URL`). Domain, unsubscribe-group,
and analytics examples use the organization API host
(`LANEFUL_ORG_BASE_URL`, default `https://api.laneful.net`; development is
`https://api.dev.laneful.net`).

## Run locally

```bash
cp env.example .env
# edit .env

python mail_settings_example.py
python domains_example.py
python unsubscribe_groups_example.py
python analytics_example.py
```

## Examples

| Script | Description |
|--------|-------------|
| `mail_settings_example.py` | Sandbox send with `from_header`, tracking, and mail settings |
| `domains_example.py` | List, create, verify, and update sending domains |
| `unsubscribe_groups_example.py` | Create, update, and list unsubscribe groups |
| `analytics_example.py` | Spam-ratio radar, Google Postmaster, and Microsoft SNDS |

## Environment variables

| Variable | Description |
|----------|-------------|
| `LANEFUL_BASE_URL` | Send host (`https://your-subdomain.z1.send.dev.laneful.net`) |
| `LANEFUL_AUTH_TOKEN` | Auth token (send token for mail examples, org token for org APIs) |
| `LANEFUL_FROM_EMAIL` | Verified sender address |
| `LANEFUL_TO_EMAILS` | Comma-separated recipients |
| `LANEFUL_ORG_BASE_URL` | Organization API host (`https://api.laneful.net`) |
| `LANEFUL_WORKSPACE_ID` | Workspace ID for org API examples |
