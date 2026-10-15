# Red-Blue — Product & Build Plan (v1)

_A Duolingo-style web app for learning offensive **and** defensive security.
Users progress through skills (one vulnerability class each), alternating between
attacking a target and defending against that same attack._

Owners: Henry & Ryan · Repo: `Red-Blue`

---

## 1. Product summary

A web-first, installable (PWA) learning app. A user picks a starting difficulty
(Beginner / Intermediate / Advanced), then works a linear path of **skills**.
Each skill is one OWASP vulnerability class (SQL injection, XSS, insecure upload,
broken auth, SSRF, …). Within a skill, the first half of levels are **structured**
(guided payloads, pick/fill answers); mastering the skill requires **open-ended**
levels (free-form attack, real patching). Users **alternate attack and defense**,
earn XP, keep streaks, and periodically re-encounter earlier skills (spaced review).

The vulnerable environments run in a **hybrid** model: most levels are simulated /
guided in the browser (cheap, instant, phone-friendly); only harder "boss" levels
spin up a real isolated container on our servers.

---

## 2. Locked decisions

| Area | Decision |
|------|----------|
| Architecture | **Hybrid** — simulated/guided levels in-browser; live containers only for boss levels |
| Delivery | **Web-first PWA**, installable to home screen; native app later if ever |
| Auth | **GitHub OAuth** first (pluggable — add Google/email for schools later) |
| Teams | **Yes, from day one** — data model supports orgs/cohorts (instructor assigns to students) |
| Taxonomy | **OWASP** — each skill = one vuln class |
| Difficulty | Beginner / Intermediate / Advanced entry points; **linear unlock** enforced |
| Exercise style | **Structured** first half of a skill → **open-ended** to master it |
| Attack grading | **Automated detection** of a machine-checkable win condition |
| Defense grading | **Dual gate** — exploit must now fail **and** functional test must still pass (validation-based in MVP; live code-exec grader with container tier) |
| Gamification | XP + streaks (keep Duolingo-style for now, tweak later) + spaced review |
| Content | Scales via a **challenge-package schema** (one spec per level) |
| Monetization | Later — rewarded ads for hints; likely a no-ads/subscription tier for schools |
| Liability | Educational-use ToS gate; all exploitation sandboxed; egress-locked labs; LLC before public launch |

---

## 3. Architecture (hybrid)

Three tiers of level, cheapest to most expensive:

1. **Simulated** — no live target. A scripted playground (e.g. a fake login that
   reacts to injection client-side, or a "fill in the payload" exercise).
   Instant, free, works great on a phone. Most Beginner/Intermediate levels.
2. **Guided real-ish** — server validates a submitted answer against a known
   win-condition without running user code (pattern/AST checks, fixed test inputs).
   Used for early defense grading.
3. **Live container (boss)** — a real isolated vulnerable service (our Red-Blue
   Docker targets) spun up per-user, time-boxed and egress-locked. Used to *master*
   a skill and for the authentic attack/defense payoff. Rare, by design.

The existing Red-Blue terminal targets become the **live-lab images** for tier 3,
and the **reference implementations** the tier-1/2 levels are modeled on. Nothing
built so far is wasted.

```
Home-screen PWA  ──►  Web frontend (lessons, skill tree, streak, exercises)
                         │
                         ▼
                     App backend / API  ──►  Postgres (users, progress, content)
                         │
                         ▼ (only for boss levels)
                     Lab orchestrator  ──►  per-user Docker container (egress-locked)
```

---

## 4. Recommended tech stack

Chosen for: PWA support, free hosting at MVP scale, and reuse of our Python targets.

- **Frontend:** Next.js (React) + Tailwind, as a **PWA**. Deploys free on Vercel.
- **Auth:** Auth.js (NextAuth) with the GitHub provider. Pluggable for Google/email.
- **App backend:** Next.js API routes for MVP app logic (progress, XP, content serving).
- **Database:** Postgres via **Supabase** or **Neon** (both have generous free tiers).
- **Grader + lab service (later):** a **Python/FastAPI** worker — natural fit, reuses
  our Flask-target knowledge, runs the exploit/functional-test engine and talks to
  the container orchestrator.
- **Live labs (Phase 3):** our Docker target images, orchestrated on a small VPS /
  lightweight orchestrator, **egress-locked** (the `internal: true` pattern we already use).

> **Open decision:** Next.js means a React/TypeScript learning investment. If staying
> in Python is faster for you both, Django + HTMX is a viable alternative, at some cost
> to frontend richness. Pick based on what you and Ryan actually know — confirm before Phase 1.

---

## 5. Core data model

Entities to design now (even if some UI is deferred):

- **User** — id, github_id, display name, email, difficulty entry point, created_at.
- **Org / Team** — id, name, owner. **Membership** — user↔org, role (owner/instructor/student).
- **Skill** — id, title, OWASP class, difficulty, order index, prerequisite skill(s).
- **Level** — id, skill_id, order, type (simulated/guided/live), the challenge package (§6).
- **Progress** — user_id, level_id, status, score, attempts, completed_at.
- **Streak / XP** — user_id, xp_total, current_streak, longest_streak, last_active_date.
- **Review schedule** — user_id, skill_id, next_review_at (spaced repetition).
- **Attempt log** — user_id, level_id, submitted payload/patch, result, timestamp (also feeds analytics & anti-cheat).

Designing Org/Team now (even hidden) is far cheaper than retrofitting multi-tenancy later.

---

## 6. The challenge-package schema (content engine)

Every level is one package conforming to a single spec. The platform renders any
package; authoring a level = filling out the spec, not writing app code. This is
what makes content scale and lets you and Ryan build in parallel.

Draft shape (JSON/YAML per level):

```yaml
id: sqli-01
skill: sql-injection
difficulty: beginner
type: simulated            # simulated | guided | live
phase: attack              # attack | defense
lesson: "..."              # the teaching text shown first
target:                    # the vulnerable thing (code snippet, or live-image ref)
  ...
attack_grader:             # how we detect the attack succeeded
  win_condition: ...
defense:                   # (defense levels only)
  exploit_to_defeat: ...   # must now fail
  functional_test: ...     # must still pass
hints: [ "...", "..." ]    # progressive; may be ad-gated later
solution: "..."            # revealed after success / on request
```

Locking this schema early is the highest-leverage decision in the whole project.

---

## 7. Exercise loop & grading engine

**Attack phase:** structured levels take a selected/filled payload; open-ended levels
take free-form input (against a live or simulated target). Success = a
**machine-checkable win condition** (flag captured, exploit signature detected).
Principle carried from the terminal build: *a level isn't done until we know the exact
input that beats it and have verified it lands.*

**Defense phase (dual gate):**
1. Re-run the original exploit → it must now **fail**.
2. Run a functional/regression test → legit use must still **pass**.
Both green = skill defended. (MVP: validation-based, no user-code execution. Container
tier: real execution of the user's patch in a sandbox, then both gates run for real.)

This grader is **one reusable engine** every live-code level plugs into — build it once, well.

---

## 8. Progression & gamification

- **Path:** units → skills → levels. Linear unlock (beat level N to open N+1; beat a
  skill to open the next). Three entry points set where a user starts.
- **Mastery:** structured levels first, then open-ended levels to fully clear a skill.
- **XP & streaks:** XP per level; daily streak with a grace mechanic. Revisit the exact
  scoring later — keep it close to Duolingo for now, differentiate once the loop is proven.
- **Spaced review:** cleared skills resurface inside later lessons on a schedule
  (`next_review_at`), reinforcing retention.
- **Onboarding notifications:** during setup, prompt the user to enable at least two —
  (a) **daily practice reminder** and (b) **streak-at-risk** alert. (PWA push: works on
  Android/desktop; on iOS only after the user adds the app to their home screen.)

---

## 9. Safety, liability & legal (minimize to near-zero)

- **ToS acceptance gate** at signup: educational use only, authorized targets only,
  no use against systems you don't own.
- **All exploitation is confined to sandboxes we provide.** The app never instructs or
  enables attacks against real external systems.
- **Egress-locked labs:** live containers have no route to the internet (our existing
  `internal: true` design) — nobody can use our infra to attack third parties. This is
  the single biggest liability control once we host containers.
- **Per-user isolation, concurrency caps, idle teardown** on the lab tier.
- **Account rate-limiting & abuse monitoring.**
- **Form an LLC before public launch** — caps personal liability and keeps the project
  cleanly separate from employers. (Relevant given Henry's defense-sector day job; keep
  this project personal and separate.)
- Consider minimal cyber/general-liability insurance once there's real traffic.

---

## 10. Monetization (later, not MVP)

- **Rewarded ads for hints** — watch an ad to earn a hint. Known pattern, modest revenue.
  Adds an ad-network SDK + approval; defer past MVP.
- **No-ads / subscription tier** — important for the schools audience (schools dislike
  ads). Keep ads skippable and plan a clean paid/edu tier.
- **Team/classroom licensing** — the natural revenue once the teams feature is real.

---

## 11. MVP — the vertical slice

Ruthlessly small. Goal: **prove the entire loop end to end for one vulnerability.**

In scope:
- GitHub OAuth login; basic profile.
- **One skill: SQL injection.** 3–4 levels: structured attack → structured defense →
  open-ended attack → open-ended defense.
- Attack grading (win-condition detection) + **validation-based** defense grading.
- XP + streak + linear unlock.
- Skill-tree / lesson UI as a **PWA** (installable, one real push notification wired).
- Data model includes Org/Team tables (no team UI yet).

Out of scope for MVP: live containers, real code-execution grading, ads, team UI,
multiple skills, spaced review scheduling (stub it).

Done = a stranger logs in with GitHub, plays the SQLi skill on their phone from the
home screen, attacks and defends, earns XP, and the app correctly grades all of it.

---

## 12. Phased roadmap

**Phase 0 — Foundations (now):** confirm stack; scaffold Next.js + Postgres + Auth.js;
design & lock the challenge-package schema (§6) and data model (§5). _Deliverable: repo
skeleton + schema doc._

**Phase 1 — MVP vertical slice (the "few weeks" target):** build §11. _Deliverable: one
playable, gradable SQLi skill, accounts, PWA._

**Phase 2 — Content scale + structure:** author more skills against the schema; teams UI;
spaced-review scheduling; richer gamification. _Deliverable: a real curriculum spine
(several OWASP skills), classroom-ready._

**Phase 3 — Live labs + hardening + launch:** Python grader + container orchestrator;
real code-execution dual-gate grading; egress-locked boss levels; LLC + ToS; monetization;
public launch. _Deliverable: the full public product._

**Timeline, honest:** Phase 1 is achievable in a few weeks if scoped as tightly as §11.
Phases 2–3 are a multi-month arc for two part-time people. Quality-over-speed means: nail
the Phase 1 loop completely before expanding — everything after it is content and scale on
a proven foundation.

---

## 13. Suggested division of labor

- **Shared / pair:** schema + data model (Phase 0) — too foundational to split.
- **Henry:** backend/API, grading logic, data model, the Python grader later (Python strength).
- **Ryan:** frontend/PWA, skill-tree UX, lesson rendering, gamification feel.
- Author levels **in parallel** once the schema is locked.

---

## 14. Open decisions still needed

1. **Confirm the stack** (Next.js vs a Python-first alternative) based on your/Ryan's comfort.
2. **Name** — still owed; check against existing security tools before committing.
3. **First skill's exact 3–4 levels** — write them out concretely as the first schema test.
4. **Difficulty placement** — a short quiz to place users, or self-select? (MVP: self-select.)
5. **Hosting choices** — Vercel + Supabase vs Neon, confirm.
