Simple point system and Discord bot for a community server.

## Features
- Guild-scoped points (messages, games, voice activity)
- Slash commands for points, rankings, transfers, and moderation
- Role purchase and clan registration support

## Run
```bash
python -m app
```

## Setup
1. Create a `.env` file or export environment variables.
2. Required variables:
   - `DS_SECRET_TOKEN` (Discord Bot token)
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Notes
- First run initializes the points schema in Supabase.
