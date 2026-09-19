# Perfect Team

Fantasy football draft boards are all built for somebody else's league. They assume half point PPR, they assume you don't start two flex spots, and they definitely don't assume your league gives four points for a defensive touchdown. So every August I ended up in a spreadsheet, hand weighting projections, trying to figure out who was actually worth a third round pick in *my* league.

Perfect Team does that for me. You tell it your scoring rules and your roster settings, it scores every projected player against those rules, and it hands back a CSV ranked by how much value each player gives you over the last startable player at their position.

## Why value over replacement and not raw points

Raw projected points are a trap. A quarterback who throws for 4,800 yards looks like a monster next to a running back projected for 900 total yards, right up until you remember that in a 12 team league the twelfth best quarterback is also pretty good, and the twelfth best running back is a backup.

So the app computes two numbers per player:

1. **Overall score**, which is the player's projection run through your league's scoring rules.
2. **Replacement score**, which is that player's score minus the score of the worst starter you'd expect to be drafted at that position.

The second number is the one worth drafting on. Getting it means knowing, for each position, the score of the Nth best player where N is teams multiplied by starters at that position. Sorting every position group would work but it's wasteful, since all I need is the bottom of the cutoff. I keep a fixed size min heap per position instead. Push until the heap holds N players, then replace the root whenever a better player shows up. The root is always the replacement level player, available in constant time, and the whole pass stays O(p log N) instead of O(p log p).

## How it fits together

```
frontend/   Next.js 16 + React 19 app. Tailwind, shadcn, Framer Motion.
backend/    Flask API. Scoring engine, Supabase queries, CSV generation.
tests/      Pytest suite for the scoring and validation logic.
```

The Flask side exposes four routes. Three of them (`/offense`, `/defense`, `/settings`) describe what the form should render, so the UI doesn't hardcode a list of stats. Add a stat to the dictionary on the backend and the button shows up on the frontend without touching React. The fourth, `/submit`, takes the filled out form and streams back a CSV.

Player projections live in Supabase. Pulling the whole table at once was the obvious first version and also the wrong one, since PostgREST caps rows per response and the payload gets big. `player_generator` pages through in batches of 1,000 and yields rows as they arrive, so the scoring loop starts working on the first page while later pages are still in flight and memory stays flat no matter how large the table gets. The query itself is built from the user's selections, so if you only score passing stats the app only ever asks Postgres for passing columns.

Scoring supports two directions, which is a thing most calculators skip. Some leagues award points per unit (six points per passing touchdown). Others award a point per so many units (one point per 25 passing yards). Those are multiplication and division respectively, and the form carries a toggle per stat to say which one you mean. That's also why validation rejects a zero on a toggled stat: it's about to become a divisor.

## The frontend

The interesting problem on this side was state. The form is generated from API responses, every field has its own validity rules, and the Calculate button needs to know whether *all* of them are currently valid. Threading callbacks down through three layers of generated components got ugly fast, so toggles and validity each live in their own React context and components publish upward into them. The page holds one map of stat values, one map of toggles, one map of per field validity, and the button just reads the validity map.

League settings are held in a ref rather than state on purpose. They're written on every keystroke and only read once at submit, so putting them in state was re rendering the entire form for no visible benefit.

While the backend crunches, the loading screen draws an actual football play: eleven X's and eleven O's stroked onto a whiteboard in sequence with RoughJS giving them a hand drawn look, plus a crowd in the stands. It has nothing to do with the math. I like it anyway.

## Running it

Backend:

```bash
pip install -e .
cd backend
flask --app app run --port 5000
```

You'll need a `.env.local` inside `backend/` with `SUPABASE_URL` and `SUPABASE_SECRET_KEY`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000.

If the frontend can't reach Flask, it doesn't just fail. It pings the backend on load, and again if a submit throws, and falls back to a demo mode that serves a precomputed CSV out of `frontend/public/`. That's what makes the Vercel deployment worth visiting: you can click through the whole form and download real output without standing up a server first.

Tests:

```bash
pytest
```

## Where it stands

The scoring engine, the pagination, the replacement level math, and the CSV export all work end to end, and there's a pytest suite covering query building and input validation. Things I'm still working on:

* `calculate()` currently overwrites its arguments with a known good payload so I could iterate on the scoring math in isolation. Removing that stub is the next commit.
* The error handling in `/submit` is a bare except that swallows the real reason a request failed. It needs to be specific and it needs to return something useful to the client.
* Projections are loaded into Supabase out of band. An ingest job belongs in this repo.

## Stack

Python, Flask, Supabase, pandas, pytest on the backend. TypeScript, Next.js, React, Tailwind, shadcn/ui, Framer Motion, RoughJS, Zod, and React Hook Form on the frontend.
