# Barakah — TRMNL Plugin API

> A FastAPI microservice that turns a MongoDB content library into a calm,
> once-a-day reflection on a [TRMNL](https://usetrmnl.com/) e-ink display.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED)](https://www.docker.com/)

Barakah serves Islamic personal-development content — **Values**, **Mindsets**,
and **Rituals** (each with an English name, an Arabic translation, and a
description) — and feeds it to a TRMNL e-ink device as a **private plugin**. The
device shows a **daily trio**: one Value + one Mindset + one Ritual, deterministic
and stable for the whole calendar day in the viewer's own timezone.

The repo spans the full path from data to glass: an async API, the device-side
Liquid templates (including bilingual RTL rendering), and a production container
deployed to DigitalOcean App Platform.

---

## Highlights

- **Deterministic, timezone-aware daily selection** — the "trio of the day" is
  derived from the calendar date in the viewer's IANA timezone, so it stays
  stable all day and rolls over at *their* midnight — no per-request randomness,
  no server-side cron or stored state. ([routes.py:63](routes.py#L63))
- **Async end to end** — `AsyncMongoClient` created once in a FastAPI **lifespan**
  context manager and shared via app state, not per-request. ([main.py:15](main.py#L15))
- **DRY route generation** — list/detail endpoints for all three collections are
  produced by a single factory rather than copy-paste. ([routes.py:21](routes.py#L21))
- **Typed boundaries** — Pydantic models validate every response; a normalized
  `DailyItem`/`DailyBundle` shape keeps the device template simple. ([models.py](models.py))
- **Production container** — multi-stage `uv` build, non-root runtime user,
  health-checked, deployed via `deploy_on_push`. ([Dockerfile](Dockerfile), [.do/app.yaml](.do/app.yaml))
- **Bilingual e-ink rendering** — Arabic (RTL, web-font) alongside English on a
  1-bit display, with a documented English-only fallback.

---

## Architecture at a glance

```
MongoDB ──► FastAPI (this repo) ──HTTP poll──► TRMNL cloud ──► e-ink device
            /barakah/daily?tz=…   (JSON)        Liquid markup    rendered screen
```

- **FastAPI** returns JSON only. It does **not** render HTML.
- **TRMNL** polls `/barakah/daily` on a schedule and renders the JSON into a
  screen using Liquid templates that live in the TRMNL dashboard. Versioned
  copies of those templates are kept in [`trmnl/`](trmnl/).

---

## Routes

All content routes are mounted under the `/barakah` prefix
([main.py](main.py) → `app.include_router(api_router, prefix="/barakah")`).

| Method & path | Description |
|---|---|
| `GET /health` | Liveness probe. Returns `{"status": "ok"}`. Used by the DigitalOcean health check. |
| `GET /barakah/values` · `/mindsets` · `/rituals` | List all document IDs in a collection (capped at 100). |
| `GET /barakah/value/{id}` · `/mindset/{id}` · `/ritual/{id}` | Fetch one document by its Mongo `ObjectId`. `404` if not found. |
| `GET /barakah/random` | One **random** document from each collection, returned as a 3-element array. Changes on every call. |
| `GET /barakah/daily?tz=<IANA>` | The **daily trio** the TRMNL plugin consumes. Deterministic per day. |

### How the routes are wired

[routes.py](routes.py) avoids repetition by generating the per-collection
list/detail endpoints with a factory:

- `register_collection(...)` ([routes.py:21](routes.py#L21)) registers both the
  list-IDs route and the get-by-ID route for a collection, then is called once
  per collection ([routes.py:35-37](routes.py#L35-L37)).
- Each handler reads from `request.app.state.mongodb[<collection>]`. The Mongo
  client is created once at startup in the lifespan handler
  ([main.py:15-20](main.py#L15-L20)) and shared via app state.
- Responses are validated/serialized through the Pydantic models in
  [models.py](models.py).

### `GET /barakah/daily` — the plugin endpoint

This is the one TRMNL polls. It returns a **keyed object** (not the bare array
that `/random` returns) so the Liquid template can use readable variables like
`value.name`, and it is **deterministic per calendar day** so the device shows a
calm, stable trio rather than re-rolling on every refresh.

**Query param**

- `tz` — an IANA timezone name (e.g. `America/New_York`). TRMNL supplies the
  installed user's zone via `{{ trmnl.user.time_zone_iana }}`. Missing or invalid
  values fall back to **UTC** rather than erroring.

**Selection logic** ([routes.py:63-94](routes.py#L63-L94))

1. Resolve `tz` to a `ZoneInfo`; compute "today" in that zone and take its
   ordinal day number (`today.toordinal()`).
2. For each collection, fetch the document `_id`s and **sort them** — `ObjectId`s
   sort by their bytes, giving a stable ordering.
3. Pick the index `(ordinal + offset) % len(ids)`, where `offset` differs per
   collection so the three don't rotate in lockstep. The same day always yields
   the same document — no MongoDB `$sample` randomness.
4. Normalize each document's type field (`value`/`mindset`/`ritual`) onto a
   common `name` key so the template treats all three uniformly.

Because the result only changes once per day, and TRMNL skips re-rendering when
merge variables are unchanged, the device naturally redraws roughly once a day.

**Response shape**

```json
{
  "date": "2026-06-12",
  "value":   { "name": "...", "arabic": "...", "description": "..." },
  "mindset": { "name": "...", "arabic": "...", "description": "..." },
  "ritual":  { "name": "...", "arabic": "...", "description": "..." }
}
```

---

## Environment variables

Configuration is read from the environment (and a local `.env`) by
[config.py](config.py) using `pydantic-settings`. The app validates these on
import and **fails fast** if a required one is missing.

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | ✅ | Mongo connection string (e.g. an Atlas `mongodb+srv://…` URI). Treat as a secret. |
| `MONGODB` | ✅ | The database name to use (e.g. `barakah`). |

Copy [`.env.example`](.env.example) to `.env` and fill in the values:

```bash
cp .env.example .env
```

In production (DigitalOcean App Platform), these are set as app-level env vars —
`MONGODB_URI` as an encrypted secret — see [.do/app.yaml](.do/app.yaml).

---

## Running locally

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # install dependencies from uv.lock
cp .env.example .env          # then edit .env with your Mongo details
uv run fastapi dev main.py    # http://127.0.0.1:8000  (auto-reload)
```

Interactive API docs: <http://127.0.0.1:8000/docs>

Quick check:

```bash
curl 'http://127.0.0.1:8000/barakah/daily?tz=America/New_York'
```

### Docker

```bash
docker build -t barakah-api .
docker run -p 8000:8000 --env-file .env barakah-api
```

The image runs `fastapi run main.py` as a non-root user on port `8000`
([Dockerfile](Dockerfile)).

---

## TRMNL display (the Liquid plugin)

These notes describe the device-side half. The markup files are the source of
truth and live in [`trmnl/`](trmnl/) — they are pasted into the TRMNL dashboard
and are **not** served by this API.

### Data source

The plugin uses TRMNL's **Polling** strategy against the daily endpoint:

```
GET /barakah/daily?tz=<IANA timezone>
```

### Dashboard setup

1. **New Private Plugin** → Strategy: **Polling**.
2. **Polling URL** (TRMNL interpolates the user's timezone):
   ```
   https://<your-do-host>/barakah/daily?tz={{ trmnl.user.time_zone_iana }}
   ```
   Verb: `GET`. No headers, no body, no auth.
3. **Refresh rate:** set generously (e.g. several hours). Content only changes
   once per day; TRMNL also skips redraws when merge variables are unchanged.
4. Paste the markup into the matching layout tabs:
   | File | Dashboard tab |
   |------|---------------|
   | [trmnl/shared.liquid](trmnl/shared.liquid) | **Shared** |
   | [trmnl/full.liquid](trmnl/full.liquid) | **Full** |
   | [trmnl/half_horizontal.liquid](trmnl/half_horizontal.liquid) | **Half Horizontal** |
5. Save and use **Force Refresh** / preview to render.

### What the markup does

- **`shared.liquid`** is prepended to every layout. It loads the **Amiri** Arabic
  web font via `@font-face` and defines the `.barakah-*` CSS used by both layouts
  (the stacked bands, the RTL Arabic styling, the description line-clamp).
- **`full.liquid`** (800×480) renders three stacked bands — Value / Mindset /
  Ritual — each showing the English `name`, the `arabic` (with `dir="rtl"`), and
  the `description`, plus a `title_bar` footer showing the date.
- **`half_horizontal.liquid`** is a condensed variant (name + Arabic per item)
  for mashups where the plugin shares the screen.

### Merge variables available in markup

- `{{ date }}`, `{{ value.* }}`, `{{ mindset.* }}`, `{{ ritual.* }}`
  (each item: `.name`, `.arabic`, `.description`)
- TRMNL globals: `{{ trmnl.user.time_zone_iana }}`, `{{ trmnl.user.first_name }}`,
  `{{ trmnl.device.* }}`, `{{ trmnl.system.timestamp_utc }}`.

### Arabic rendering — verify on device

Arabic uses the **Amiri** web font loaded in `shared.liquid`. TRMNL renders via a
headless browser to 1-bit e-ink, so confirm glyphs render (not tofu boxes) in the
preview/on device. If they don't:

- Self-host the `.woff2` and reference it via `@font-face`, **or**
- Fall back to English-only by setting `--barakah-show-arabic: none` on the
  `.barakah-arabic` rule in `shared.liquid`.

---

## Project layout

```
.
├── main.py                     # FastAPI app, lifespan (Mongo client), /health
├── routes.py                   # /barakah routes incl. /daily
├── models.py                   # Pydantic models (Barakah* + DailyItem/DailyBundle)
├── config.py                   # env-var settings (MONGODB_URI, MONGODB)
├── documents/                  # source CSVs / seed data
├── trmnl/                      # TRMNL Liquid markup (pasted into the dashboard)
│   ├── shared.liquid
│   ├── full.liquid
│   └── half_horizontal.liquid
├── Dockerfile
├── .do/app.yaml                # DigitalOcean App Platform spec
└── .env.example
```
