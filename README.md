# Cassandra

Open-domain research assistant. Ask a question; the answer renders as a
visual hub-and-spoke node — synthesized answer in the center, its 1-6
supporting sources fanned out and connected on expand, each source its own
progressive-disclosure card (one-sentence fact → grounded paragraph → real
open-access PDF). Expanding an answer also lets you branch a follow-up
question into a connected child node, so a topic explores as a small tree.
Full conversation history stays reachable as a hover-reveal panel behind the
input bar. Save articles and track topics across visits, with a standing
library refresh every ~2 days. Password-gated, hosted on Vercel.

Built on Next.js App Router + the Anthropic SDK directly, reusing the
literature-search / full-text / citation logic from the DASH project
(`eirini-dash`), ported to TypeScript and generalized from a fixed
climate/planning corpus to open-topic live search.

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
| `CASSANDRA_MODEL` | Optional, overrides the default chat model (`claude-sonnet-5`) |
| `CASSANDRA_FAST_MODEL` | Optional, overrides the summarizer model (`claude-haiku-4-5`) |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Set automatically by the Vercel Upstash integration |

## Architecture

```
Browser ──> middleware.ts (password gate, sets cassandra_uid cookie)
              │
              ├─ /                    app/page.tsx — canvas UI
              │     └─ /api/ask          Anthropic SDK direct, runs the
              │                          tool-call loop server-side
              │                              │
              │                       lib/research/*.ts
              │                   (search, fulltext, summarize)
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
- `app/api/ask/route.ts` — the model loop: one Anthropic SDK call, and if
  Claude calls `search_literature`, executes it in-process (calling
  `lib/research/*` directly, no HTTP round-trip) and feeds the result back for
  a final synthesized answer. Returns `{answerText, facts, history}` per
  question; `history` round-trips from the client so context persists across
  turns without server-side session state.
- `lib/research/search.ts` / `fulltext.ts` / `citations.ts` — TS ports of
  DASH's `scientific_search.py` / `fulltext.py` / `citations.py`: OpenAlex +
  arXiv search, open-access PDF resolution + text extraction (`unpdf`), and
  citation formatting. Framework-free, same separation DASH used.
- `lib/research/summarize.ts` — one Claude call per result producing the
  one-sentence + paragraph pair, grounded in real article text when an OA PDF
  is found.
- `app/page.tsx` — owns the answer tree (`Record<id, AnswerNode>` + insertion
  order + linear `history`), `submitQuestion()` for both root and branch
  questions, and which node is currently focused.
- `components/canvas/{Canvas,AnswerHub,FactSpokes,ConnectorLines,BranchComposer}.tsx`
  — the visualization: `AnswerHub` renders the focused node (breadcrumb up to
  its parent, answer text, expand toggle); expanding fans out `ArticleCard`s
  as spokes with `ConnectorLines` (ref-measured SVG, not hardcoded
  coordinates) and reveals `BranchComposer` for follow-ups.
- `components/ArticleCard.tsx` — the progressive-disclosure source card: a
  zoom control cycles sentence → paragraph → embedded PDF (only when a real OA
  PDF was resolved — never fabricated).
- `components/{BottomBar,HistoryDrawer}.tsx` — the always-visible input;
  `HistoryDrawer` wraps it and reveals the full session as a white panel on
  hover, each row jumping the canvas back to that node.
- `lib/library.ts` — Upstash-Redis-backed library (saved articles, tracked
  topics, cron-discovered new finds), keyed by `cassandra_uid`.
- `app/api/cron/refresh/route.ts` + `vercel.json` — the standing job: re-runs
  tracked-topic searches and appends unseen results; its scheduled invocation
  also keeps the deployment warm.

## Adding a research tool

Add a new module under `lib/research/`, export plain async functions (no
framework imports), then wire it into the tool loop in `app/api/ask/route.ts`
(add to the `tools` array + handle its `tool_use` block).
