# Cassandra

Open-domain research assistant. Search scientific literature (OpenAlex + arXiv),
read results as progressive-disclosure cards — one-sentence fact → grounded
paragraph → real open-access PDF — save articles and track topics across
visits, and get a standing library refresh every ~2 days. Password-gated,
hosted on Vercel.

Built on CopilotKit + Next.js App Router, reusing the literature-search /
full-text / citation logic from the DASH project (`eirini-dash`), ported to
TypeScript and generalized from a fixed climate/planning corpus to open-topic
live search.

## Setup

```bash
git clone https://github.com/EiriniOr/Cassandra.git
cd Cassandra
npm install
cp .env.example .env   # fill in ANTHROPIC_API_KEY, SITE_PASSWORD, AUTH_SECRET
npm run dev
```

Open <http://localhost:3000>, log in with `SITE_PASSWORD`.

Library persistence (saved articles, tracked topics) and the refresh cron
need Upstash Redis (Vercel's current marketplace KV product — connect it from
the Vercel project's Storage tab, or `vercel install upstash` locally). Without
it, chat and search still work; the library API routes return errors.

## Environment variables

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `SITE_PASSWORD` | Password gate for the whole site |
| `AUTH_SECRET` | Signs the session cookie (`openssl rand -hex 32`) |
| `CRON_SECRET` | Verifies Vercel Cron's calls to `/api/cron/refresh` |
| `CASSANDRA_MODEL` | Optional, overrides the default chat model (`claude-fable-5`) |
| `CASSANDRA_FAST_MODEL` | Optional, overrides the summarizer model (`claude-haiku-4-5`) |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Set automatically by the Vercel Upstash integration |

## Architecture

```
Browser ──> middleware.ts (password gate, sets cassandra_uid cookie)
              │
              ├─ /                    chat UI (CopilotKit)
              │     └─ /api/copilotkit   CopilotRuntime + AnthropicAdapter → Claude
              │           search_literature tool (frontend) ──> /api/research/search
              │                                                     │
              │                                              lib/research/*.ts
              │                                          (search, fulltext, summarize)
              │
              ├─ /library             saved articles + tracked topics
              │     └─ /api/library/*     lib/library.ts (Upstash Redis)
              │
              └─ /api/cron/refresh    Vercel Cron, every 2 days
                    re-runs lib/research/search.ts per tracked topic,
                    appends new results via lib/library.ts
```

- `middleware.ts` — password gate (signed `cassandra_auth` cookie) and the
  opaque `cassandra_uid` cookie that scopes the library.
- `app/api/copilotkit/route.ts` — CopilotKit runtime, `AnthropicAdapter` talks
  to Claude directly (no separate agent backend needed for a stateless
  live-search tool, unlike DASH's LangGraph setup).
- `lib/research/search.ts` / `fulltext.ts` / `citations.ts` — TS ports of
  DASH's `scientific_search.py` / `fulltext.py` / `citations.py`: OpenAlex +
  arXiv search, open-access PDF resolution + text extraction (`unpdf`), and
  citation formatting. Framework-free, same separation DASH used.
- `lib/research/summarize.ts` — one Claude call per result producing the
  one-sentence + paragraph pair, grounded in real article text when an OA PDF
  is found.
- `components/ArticleCard.tsx` / `ArticleGrid.tsx` — the progressive-disclosure
  UI: a zoom control cycles sentence → paragraph → embedded PDF (only when a
  real OA PDF was resolved — never fabricated).
- `lib/library.ts` — Upstash-Redis-backed library (saved articles, tracked
  topics, cron-discovered new finds), keyed by `cassandra_uid`.
- `app/api/cron/refresh/route.ts` + `vercel.json` — the standing job: re-runs
  tracked-topic searches and appends unseen results; its scheduled invocation
  also keeps the deployment warm.

## Adding a research tool

Add a new module under `lib/research/`, export plain async functions (no
framework imports), then wire it as a `useFrontendTool` in
`app/(app)/page.tsx` if it needs to render custom UI, or call it directly from
an API route otherwise.
