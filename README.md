# Project Malthis

A self-hosted tool that turns recorded tabletop RPG sessions into a searchable campaign record. A Dungeon Master uploads a session's audio; the server transcribes it with Whisper, summarizes it with a local LLM through Ollama, and extracts the named characters, places, monsters, and items that appeared. Those become entities in a per-campaign lore database, linked to one another by typed relationships ("Located In", "Allies", "Betrayed", and so on).

Everything runs locally in Docker, including the AI models, so recordings and campaign data never leave the machine.

## Transparency

- Some code was taken directly from the FastAPI, FastAPI Users, SQLAlchemy, and Celery documentation, and is labeled as such where it appears.
- Some pieces, such as the Vite + React frontend, were set up from their official templates.
- Claude Code was used mainly as a learning aid and debugging assistant.

## How it works

```
 DM uploads audio ──► FastAPI ──► validate type, save to shared volume,
                                  create session row (status: Pending)
                                         │
                                         ▼ queue job (Redis)
                                  Celery worker (GPU)
                                         │
                     ┌───────────────────┼───────────────────┐
                     ▼                   ▼                   ▼
              Whisper: audio      Ollama: session      Ollama: entity
              → transcript        summary              extraction (JSON)
                     └───────────────────┼───────────────────┘
                                         ▼
                        save transcript + summary to PostgreSQL
                        status → Needs Review   (or Failed on error)
```

1. **Accounts.** Users register and log in through FastAPI Users, which issues JWT bearer tokens.
2. **Campaigns.** Creating a campaign makes you its owner and assigns you the Dungeon Master role automatically.
3. **Invites.** The DM generates an invite token (`secrets.token_urlsafe`). A player submits a join request with that token. The DM approves or rejects it, and approval creates a Player membership.
4. **Sessions.** The DM uploads an audio file for a numbered session. The API checks the file type and that the session number isn't already used, saves the audio to a volume shared with the worker, and queues a Celery job.
5. **Processing.** The worker transcribes the audio with Whisper, asks Ollama for a session summary, and asks Ollama for a JSON list of entities. The parser tolerates the model wrapping its list in an object. The session's `job_status` moves through Pending → Processing → Needs Review, or → Failed.
6. **Lore.** Entities (Player, Player Character, NPC, Monster, Location, Item) can be created, edited, and linked with 23 relationship types. Creating an entity whose name already exists returns the existing record plus the incoming data, so the two can be merged. Merging asks the LLM to combine the old description with the new information.

### Design notes

- **Swappable AI providers.** Transcription and LLM access sit behind abstract base classes (`TranscriptionProvider`, `LLMProvider`), so Whisper or Ollama can be replaced without touching the pipeline. Whisper and Ollama are intended as the defaults, with other transcription services and LLMs anticipated as drop-in alternatives.
- **Async API, sync worker.** The API uses async SQLAlchemy (`asyncpg`). Celery tasks are synchronous, so the worker opens its own `psycopg2` connection to the same database.
- **Long work off the request path.** Transcription can take minutes, so the upload endpoint returns immediately and the client checks `job_status`.

## Tech stack

| Layer | Tools |
|---|---|
| API | Python 3.11, FastAPI, Pydantic, FastAPI Users (JWT) |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async), Adminer for inspection |
| Background jobs | Celery with Redis as broker and result backend |
| AI | OpenAI Whisper (local), Ollama running Llama 3 |
| Frontend | React + Vite (template only so far) |
| Infrastructure | Docker Compose, NVIDIA GPU passthrough for the worker and Ollama |

## Data model

- `user`: FastAPI Users' default table.
- `campaigns`: name, description, owner.
- `campaign_members`: user ↔ campaign with a role (Dungeon Master, Player, Spectator).
- `campaign_invites`: one token per campaign, with an optional expiry and an active flag.
- `campaign_join_requests`: Pending / Approved / Rejected, with review timestamps.
- `campaign_sessions`: session number, audio path, job status, transcript, summary.
- `entities`: name, class, description, aliases, notes, and the session where it first appeared.
- `entity_relationships`: entity A, relationship type, entity B.

## Project layout

```
backend/
  main.py               FastAPI app, router registration, auth routes
  worker.py             Celery app and the audio-processing / entity-merge tasks
  core/                 SQLAlchemy models, Pydantic schemas, and business logic per resource
  routers/              HTTP endpoints per resource
  providers/
    transcription/      TranscriptionProvider base class + Whisper implementation
    llm/                LLMProvider base class + Ollama implementation
frontend/               Vite + React app (starter template)
docker-compose.yml      web, db, adminer, redis, worker, ollama, frontend
```

## Running locally

Requirements: Docker with Docker Compose, and assumes an NVIDIA GPU with the NVIDIA Container Toolkit (the worker and Ollama reserve the GPU).

```
cp .env.example .env      # then set POSTGRES_PASSWORD, SECRET_KEY, and DATABASE_URL to match
docker compose up --build
docker compose exec ollama ollama pull llama3
```

- API and interactive docs: http://localhost:8000/docs
- Adminer: http://localhost:8080
- Frontend: http://localhost:5173

Whisper and Ollama model sizes are set with `WHISPER_MODEL` and `OLLAMA_MODEL` in `.env`.

## Current status

Development paused in June 2026 after 24 commits. The backend API and processing pipeline are largely built; the frontend has not been started.

| Area | Status |
|---|---|
| Docker stack, database, auth | Working |
| Campaigns, roles, invites, join requests | Working (see permission gaps below) |
| Session upload and job queueing | Working |
| Transcription and summary | Working; output saved to the session |
| Entity extraction | Runs, but results are only logged, not saved |
| Entity and relationship CRUD | Working through the API |
| Entity merge | Endpoint is broken (see below) |
| Player-facing access | Not started; only the DM can read campaign data |
| Frontend | Vite template only |
| Tests | None |

### Next steps

1. Save extracted entities, routing duplicates through the merge flow.
2. Split long transcripts into chunks for summarizing and extraction.
3. Fix the merge endpoint and the permission gaps below.
4. Add role-based read access for players, including DM-hidden entities.
5. Build the frontend: campaign list, session upload and status, transcript review, entity browser.

## Known limitations

**Pipeline**
- Extracted entities are printed by the worker but never written to the database, so the transcript-to-lore loop isn't closed yet.
- The whole transcript is sent to the LLM in one prompt. Llama 3's context window (about 8K tokens) is far shorter than a multi-hour session, so most of a long transcript would be cut off. Transcripts need to be chunked and the results combined.
- The Whisper model is reloaded for every job instead of once per worker.
- Redis's address is hardcoded in `worker.py` rather than read from the environment.

**API**
- The merge endpoint reads a field that `EntityCreate` doesn't have, and it calls the Celery task directly (running it inside the web process) instead of queuing it with `.delay()`.
- Almost every read requires campaign ownership, so players can't see sessions or entities in campaigns they've joined.
- Deleting a campaign removes only its memberships first, so it fails once the campaign has sessions, entities, invites, or join requests.

**Permissions and security**
- `POST /campaign_members/{campaign_id}/` lets any logged-in user add themselves to any campaign with any role, which bypasses the invite flow.
- Fetching a campaign's invite link doesn't check ownership, and deleting it requires no login.
- Invite expiry dates are stored but never checked, and repeat join requests aren't prevented.
- Relationship update and delete look rows up by ID without confirming they belong to the campaign in the URL.

**Housekeeping**
- Tables are created with `create_all` on startup; there are no migrations (Alembic).
- `__pycache__` folders are committed, and `.gitignore` covers only `.env`.
- No automated tests.

## Future design intents

- **DM review before publishing.** The `Needs Review` job status exists so the DM can check and correct a transcript, summary, and extracted entities before the session is marked `Completed` and its lore is shared with players.
- **Role-based visibility.** Right now, only the Dungeon Master can view campaign data. Player and Spectator access is planned for a later stage: members would see the public lore for campaigns they've joined, and the DM could keep certain entities hidden until they come up in play.
- **Entities that grow over time.** Each entity records the session where it first appeared and keeps a list of aliases. New sessions are meant to add to an existing entity, through aliases and LLM-merged descriptions, instead of creating duplicates.
- **Interchangeable AI backends.** Whisper and Ollama are the defaults, but the provider interfaces are meant to accept other transcription services and LLMs, including hosted APIs for anyone without a local GPU.
- **Account email flows.** The registration, password-reset, and verification hooks are in place to send welcome, reset, and verification emails.
- **Schema migrations.** Moving from `create_all` to Alembic so the database can change without being rebuilt.
- **Self-hosting first.** The whole stack is meant to run on a single home server, so a group's recordings and campaign data stay under their control.
