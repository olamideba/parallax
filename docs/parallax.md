# Parallax

Next steps Jun 23, 2026

- [x] ~~Study and define the problem~~  
- [x] ~~Read the research materials~~

In astronomy, a parallax is the apparent shift in an object's position when viewed from different vantage points. The object stays the same, but the perspective changes. 

In fact, multi-agent debate and cooperation directly reflects the core properties of a parallax (looking at things from a different viewpoint because relying on a single perspective can introduce bias and instability in the results ([Chan et al., 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/25cc3adf8c85f7c70989cb8a97a691a7-Abstract-Conference.html)).)

# Problem definition

## What is the problem?

Professors and faculty members alike are overwhelmed by generic AI slop academic cold emails and outreach. They must filter out thousands of automated, generic student inquiries to find the few candidates who possess genuine prerequisite skills, understand their recent publications, and have secured viable external funding. The noise to signal ratio is extremely high as we are in the age of AI. \[Need highly relevant stats to back claim\]

A whole lot of solutions are being developed for students to continue this mass mailing but little to no solution is designed for professors \[Need highly relevant stats to back claim\]

## What is the evidence?

On community forums like [r/Professors](https://www.reddit.com/r/Professors/comments/xs69sh/main_reason_why_you_dont_answer_prospective/), faculty members note that they routinely ignore emails that look mass-mailed or superficial. They explicitly complain about applicants who claim interest in their field but showcase an entirely unrelated background.  \[Need highly relevant stats to back claim\]

### The Problem (Global)

* Global higher education enrollment has grown to **269 million students**, more than doubling over the past two decades. ([UNESCO](https://www.unesco.org/en/articles/number-students-higher-education-more-doubled-20-years-inequalities-remain?hub=343&utm_source=chatgpt.com))  
* International student mobility has **tripled in 20 years**, reaching approximately **7.3 million students studying abroad worldwide**. ([UNESCO](https://www.unesco.org/en/articles/number-students-higher-education-more-doubled-20-years-inequalities-remain?hub=343&utm_source=chatgpt.com))  
* Student mobility continues to grow across regions, with increasing flows not only to North America and Europe but also to destinations such as China, India, Egypt, Japan, and Türkiye. ([ICEF Monitor](https://monitor.icef.com/2026/05/unesco-confirms-growing-trend-of-intra-regional-student-mobility/?utm_source=chatgpt.com))  
* China alone hosted approximately **380,000 international students from 191 countries and regions** during the 2024-2025 academic year. ([Reddit](https://www.reddit.com/r/Sino/comments/1snpr8k/a_total_of_380000_international_students_from_191/?utm_source=chatgpt.com))  
* Faculty members internationally report a sharp increase in unsolicited graduate-student outreach, with some reporting growth from only a few emails per year to multiple emails per day. ([Reddit](https://www.reddit.com/r/Professors/comments/17xmrqa?utm_source=chatgpt.com))  
* Professors increasingly report receiving AI-generated outreach emails that appear personalized but demonstrate little genuine research alignment. ([Reddit](https://www.reddit.com/r/Professors/comments/1gvq108?utm_source=chatgpt.com))

### The Gap

* Admissions systems manage **applications**.  
* Recruiting systems manage **hiring**.  
* Research tools manage **papers**.  
* No widely adopted platform is designed to help professors evaluate **research-fit, intent, and authenticity** across large volumes of graduate outreach before formal admission decisions occur. ([UNESCO](https://www.unesco.org/en/articles/number-students-higher-education-more-doubled-20-years-inequalities-remain?hub=343&utm_source=chatgpt.com))

### One-Liner

As global student mobility surpasses 7 million students and AI makes mass outreach effortless, professors face a growing challenge: identifying genuinely aligned researchers among thousands of increasingly automated inquiries. Parallax helps them see the other side of admissions. ([UNESCO](https://www.unesco.org/en/articles/number-students-higher-education-more-doubled-20-years-inequalities-remain?hub=343&utm_source=chatgpt.com))

## What are the symptoms?

* Professors reflexively ignore or delete high-potential student inquiries that look slightly generic.  
* Qualified applicants from unconventional backgrounds are missed because they cannot pierce the noise.  
* Faculty waste hours manually skimming through generic, AI-generated academic spam emails every day.

## What is the root cause?

* The friction-free nature of LLMs allows applicants to flood faculty inboxes with highly polished, mass-produced cold emails that look hyper-personalized but lack genuine academic alignment.

## Research on the multi-agent debate framework (agents society: collab, negotiate)

* [CHATEVAL](https://proceedings.iclr.cc/paper_files/paper/2024/hash/25cc3adf8c85f7c70989cb8a97a691a7-Abstract-Conference.html): TOWARDS BETTER LLM-BASED EVALUA-TORS THROUGH MULTI-AGENT DEBATE  
  * Chan, C. M., Chen, W., Su, Y., Yu, J., Xue, W., Zhang, S., ... & Liu, Z. (2024, May). Chateval: Towards better llm-based evaluators through multi-agent debate. In *International conference on learning representations* (Vol. 2024, pp. 9079-9093).   
  * Multi agents perform better than single agents  
  * Introduce communication strategies  
  * There are a thousand Hamlets in a thousand people’s eyes

* [Encouraging Divergent Thinking in Large Language Models Through Multi Agent Debate](https://aclanthology.org/2024.emnlp-main.992/)  
  * Liang, T., He, Z., Jiao, W., Wang, X., Wang, Y., Wang, R., ... & Tu, Z. (2024, November). Encouraging divergent thinking in large language models through multi-agent debate. In *Proceedings of the 2024 conference on empirical methods in natural language processing* (pp. 17889-17904).   
  * Self reflection techniques lead to the Degeneration of Thought (DOT) problem  
  * They introduce the Multi Agent Debate framework with CHATEVAL builds upon.  
  * One of the hackathon requirements is to show how agents society (MAD) performs better than single agents systems, Liang et al did something very similar in Figure 2 of this paper  
  * ![][image1]

# Product definition

**Parallax** — an agent society for faculty Hackathon: Global AI Hackathon with Qwen Cloud · Track 3 (Agent Society) Team: Olamide, David

Parallax flips graduate admissions to the professor's vantage point. Inbound student outreach arrives as noise; a society of agents debates each promising candidate against the professor's *own* publications and *own* declared capacity, and returns a grounded signal — a triaged decision with receipts — instead of another inbox to skim.

---

## 1\. Scope guardrails

The product's job is narrow on purpose: **take away the noise, give the professor a signal.** Everything below either serves that or is explicitly deferred so it stops resurfacing mid-build.

| In scope (building) | Out of scope (not building) | Deferred (good, but not now) |
| :---- | :---- | :---- |
| Professor onboarding: publications \+ capacity | Student-facing accounts or login | Per-recruiting-call publication sets (CRM-bridge feature) |
| Reactive intake of inbound outreach | Student-side faculty discovery / outreach tooling | Multi-channel intake beyond email (LinkedIn, forms, portals) |
| Gatekeeper triage (cheap reject) | Sending email on the professor's behalf without approval | Auto-reply / full mailbox automation |
| Deep ingestion of survivors | Formal admissions decisioning / integration with Slate etc. | Analytics dashboards, longitudinal reporting |
| Multi-round simultaneous debate society | Scoring a student's actual bank account / private finances | Mobile app |
| Arbitrator decision \+ staged draft |  | Team/multi-professor org accounts |
| Professor review with human-in-the-loop |  |  |

**The one principle that kills scope creep:** if a proposed feature is not required by a flow in §5, it does not get built. Surfaces (§7) are *derived from* flows, never added for their own sake.

---

## 2\. Users & roles

| Role | Logs in? | What they do |
| :---- | :---- | :---- |
| **Professor** (primary) | Yes | Onboards, declares capacity, reviews triaged outreach, approves/edits/overrides decisions. The only true user. |
| **Student / applicant** (subject) | **No** | Never touches Parallax. They are the *subject* being evaluated, not a user. Their email is the trigger; their CV is an input. |

Naming the student explicitly as a non-user is the guardrail against accidentally rebuilding the student-side tool we cut.

---

## 3\. Core value & principles

Every decision downstream — design and engineering — must obey these. They are the test a feature passes or fails.

1. **Grounded, not hallucinated.** Agents reason from indexed content — the professor's real publications and real declared constraints — not from general model knowledge. Every claim about research fit or authenticity must carry a receipt (source \+ location in the corpus). This is the entire reason Parallax is not "an LLM with extra steps."  
2. **Reactive.** The system acts on a trigger (inbound outreach). It does not go fishing proactively.  
3. **The agent is the product; the UI is scaffolding.** This is a full-stack app, but the core value is the society. UI exists only to onboard the professor, surface the debate, and capture the human-in-the-loop decision. No feature crowding.  
4. **A society, not a pipeline.** Agents hold opposing positions and genuinely influence each other across rounds. Sequential hand-offs would be a multi-agent system wearing a costume; the debate is what earns "Agent Society."  
5. **The professor is always the final authority.** No outbound action (such as responses of scheduling a meeting) is taken without an explicit human-in-the-loop approval.

---

## 4\. Data model — the two corpora

The architecture rests on two distinct bodies of data, ingested at different times by different mechanisms. Agents consume these; this contract therefore precedes the agent spec.

### 4.1 Professor corpus — the yardstick (set at onboarding, editable in-app)

The standard everything is measured against. Loaded ahead of any outreach at onboarding, and editable in-app thereafter — the professor can add/remove publications and update capacity & constraints as slots fill, budgets change, or recruiting focus shifts. Edits re-index and apply to subsequent outreach.

- **Publications** — links and/or uploaded PDFs of the work the professor wants applicants measured against. Chunked, embedded, indexed into a vector store for retrieval. `[CONFIRM AT BUILD]` — store \+ embedding model.  
- **Capacity & constraints** (structured, professor-declared, professor-owned):  
  - open slots / how many students can be taken  
  - declared budget context (department / personal / school) — *as entered by the professor*, never inferred about the student  
  - students already committed  
  - projects / topics currently recruiting for  
- **Thresholds / preferences** — e.g. how aggressive the gatekeeper should be. `[CONFIRM AT BUILD]` — which knobs are exposed vs. hard-coded.

### 4.2 Outreach object — the thing measured (ingested per-event, at runtime)

Created when outreach arrives. **Deliberately channel-agnostic** so the build can ship email-only while remaining trivially extensible:

Outreach {

  channel        // "email" is the only IMPLEMENTED adapter; field exists so

                 //   LinkedIn / form / portal are future adapters, not rewrites

  sender         // identity of the applicant

  body           // raw message text

  attachments\[\]  // e.g. CV / PDF

  received\_at

  // populated progressively as it moves through triage \-\> ingestion:

  extracted\_profile?   // interests, credentials, prerequisites, funding/country context

  extracted\_claims\[\]?  // discrete, checkable assertions the student makes about

                       //   the professor's work ("inspired by your 2025 paper on X")

  triage\_verdict?      // reject | promote

  debate\_trace?        // the society's transcript \+ receipts

  decision?            // arbitrator output \+ staged draft

}

Email is documented as the only implemented channel. The channel-agnostic object is the *design principle* that answers "does this generalise?" without building the other channels.

---

## 5\. Flows

Each flow: **trigger · actors · steps · human-in-the-loop gate · acceptance criteria.** This is the spine design and engineering both branch from.

### 5.1 Onboarding flow (professor)

- **Trigger:** professor sets up Parallax.  
- **Steps:** professor pastes a batch list of DOIs or paper URLs (optionally seeded from ORCID import) → system resolves to full text via Unpaywall / Semantic Scholar API / direct fetch where open-access; paywalled or unresolvable papers prompt professor to upload PDF directly → system chunks, embeds, indexes into the professor corpus → professor declares capacity & constraints (§4.1) → professor sets thresholds `[CONFIRM AT BUILD]`.  
- **Acceptance criteria:** publications are retrievable from the index with source \+ location; resolved full text is confirmed indexed; broken links and paywalled papers fail gracefully with a clear message and fallback to PDF upload prompt; capacity fields persist and are queryable by agents; professor sees a confirmation of what was successfully indexed before proceeding.

### 5.2 Outreach intake flow (the reactive trigger)

- **Trigger:** inbound outreach (email) arrives.  
- **Steps:** create Outreach object → **Gatekeeper** runs cheap, light extraction (just enough to read it) → triage verdict.  
- **Branch:** `reject` → logged, no further spend. `promote` → to ingestion (5.3).  
- **Acceptance criteria:** obvious slop is rejected *without* incurring deep-ingestion cost; every reject is logged and visible to the professor (nothing silently disappears); the cheap/expensive split is demonstrable in the trace.

### 5.3 Ingestion flow (survivors only)

- **Trigger:** a promoted outreach object.  
- **Steps:** deep-parse body \+ attachments → populate `extracted_profile` → extract `extracted_claims[]` as discrete, individually checkable assertions.  
- **Acceptance criteria:** claims about the professor's work are isolated cleanly enough for the Authenticity agent to verify them one by one; parsing failures degrade gracefully rather than crashing the run.

### 5.4 Society / debate flow (the technical showcase)

- **Trigger:** a fully ingested outreach object.  
- **Pattern:** multi-round **simultaneous** debate — each agent produces its turn in parallel each round, then all agents see all responses before the next round (per ChatEval / MAD).  
- **Debaters:** Research-Fit Advocate · Authenticity Auditor · Capacity & Funding Assessor (§6).  
- **Termination:** hard round cap **`[CONFIRM AT BUILD]` — provisional default 3 rounds**, plus the Arbitrator as decisive stop. Non-negotiable: there must be a termination condition, or the debate loops / degenerates (the Degeneration-of-Thought failure mode).  
- **HITL gate:** none mid-debate — the human enters at decision (5.5).  
- **Acceptance criteria:** agents demonstrably reference each other's prior-round arguments (evidence it's a society, not parallel monologues); every factual assertion carries a receipt into the professor's corpus; the debate always terminates within the cap; the full transcript is captured as `debate_trace`.

### 5.5 Decision & human-in-the-loop flow

- **Trigger:** debate terminates.  
- **Steps:** **Arbitrator** weighs the debate → produces a decision (e.g. invite / request-more-info / decline `[CONFIRM AT BUILD]` — final label set) → drafts a staged response → queues for the professor.  
- **Async by nature:** the agent processes outreach whenever it arrives, whether or not the professor is at the UI. Clear-cut, no-outbound outcomes (e.g. logging a decline) may auto-resolve so the professor isn't bothered; anything that sends an outbound communication or makes a positive commitment waits in a pending-approval queue. The exact auto-resolve boundary is `[CONFIRM AT BUILD]` (decision \#9) and must respect Principle 5 — no outbound action without explicit approval.  
- **HITL gate:** professor approves / edits / overrides on the pending items. **Nothing is sent or finalised without this.**  
- **Acceptance criteria:** the decision is traceable back to specific debate points and receipts; the professor can override any verdict; an overridden decision is logged as such; auto-resolved items are visible and reversible, never silent.

### 5.6 Review / dashboard flow

- **Trigger:** professor opens Parallax (typically returning after async processing has happened).  
- **Steps:** view the triaged queue — pending-approval items distinguished from auto-resolved and rejected → open any item to **replay** its debate and receipts → act on staged drafts.  
- **Acceptance criteria:** the professor can reconstruct *why* any decision was made by replaying the debate alone; pending vs. auto-resolved vs. rejected are clearly separated; rejects and auto-resolved items are reviewable, not hidden.

---

## 6\. Agent society specification

Behavioral contracts. Internals are specified to the level of *what each agent is accountable for and how the debate is governed* — exact prompts, message schemas, model-per-agent, and framework are **`[CONFIRM AT BUILD]`** because neither of us is writing that code yet.

**Ecosystem direction (provisional, not locked):** Qwen models on Alibaba Cloud; Qwen-Agent as the likely agent framework; MCP for tool/data access; **custom Skills** to encapsulate each agent's specialized capability (e.g. publication retrieval, per-claim verification, live mobility lookup) as reusable, testable units rather than ad-hoc prompt logic. `[CONFIRM AT BUILD]` for all of these — chosen to align with the sponsor, not yet validated against the orchestration needs of simultaneous multi-round debate.

| Agent | In the debate? | Role | Grounding source | Argues / outputs |
| :---- | :---- | :---- | :---- | :---- |
| **Gatekeeper** | No — pre-filter | Cheap triage; reject obvious slop before any expensive work | Light read of the outreach itself | `reject` / `promote` \+ reason |
| **Research-Fit Advocate** | Yes | Make the strongest *honest* case the candidate genuinely aligns | RAG over professor's publications | Argues *for*; cites specific matched work |
| **Authenticity Auditor** | Yes | Cross-examine the student's claims about the professor's work; flag generic / AI-inflated / hallucinated alignment | Same publication index; the `extracted_claims[]` | Argues *against* where claims don't hold; per-claim receipts |
| **Capacity & Funding Assessor** | Yes | Check the student's situation against the professor's *declared* capacity & constraints | Professor's declared capacity (§4.1); **live, date-stamped** lookup for volatile facts (e.g. visa/mobility) | Raises feasibility objections (e.g. "no funded slot"); may veto |
| **Arbitrator** | No — resolver | Weigh the debate, decide, draft the staged response | The full `debate_trace` | Decision \+ drafted reply; final authority before HITL |

**Orchestration contract:**

- Turn-taking: **simultaneous** (parallel generation per round, shared visibility between rounds).  
- Round cap: `[CONFIRM AT BUILD]` — provisional 3\.  
- Termination: round cap reached **or** Arbitrator calls it.  
- Arbitrator authority: resolves disagreement; debaters advise, Arbitrator decides, professor overrides.

**On the Capacity agent's volatile lookups:** facts like the Nigeria→US travel restriction are real but politically volatile and change with administrations. This agent must present them as *"found via live lookup, dated X, source Y,"* never as an asserted truth from model memory. This keeps the agent accurate and judge-defensible.

---

## 7\. Surfaces (minimal UI inventory)

Derived strictly from the flows. If a screen isn't demanded by §5, it doesn't exist. This is what feeds Claude Design.

Might change to pixelated(minimal) though

Inspiration \- [github.com/W17ant/Claude-Office](http://github.com/W17ant/Claude-Office) 

| Surface | Serves flow | Must show |
| :---- | :---- | :---- |
| Onboarding / setup | 5.1 | Publication upload/connect; capacity & constraint fields; corpus confirmation |
| Triaged inbox / queue | 5.6, 5.2 | Promoted vs. rejected; per-item entry point |
| Outreach detail \+ **debate replay** | 5.4, 5.5 | Matches [github.com/W17ant/Claude-Office](http://github.com/W17ant/Claude-Office)  A *replayable*, step-through view of the debate: each agent's position per round, receipts surfacing as claims are verified/refuted, visible cross-references between rounds, then the arbitrator's decision. The "wow" surface. Replay (not static history) is the right frame because processing is async — the professor reviews after the fact, not live (see §5.5–5.6). Presentation style — structured step-through vs. animated personas — is `[CONFIRM AT BUILD]` (decision \#11). |
| Decision / draft review | 5.5 | Staged draft; approve / edit / override controls |

Four surfaces. The debate-replay view is the centrepiece — it's where the invisible (a grounded multi-agent argument) becomes visible and re-watchable.

Something similar to this  
![][image2]

---

## 8\. Acceptance criteria & demo beats

### The "wow" beat

The professor returns to a queue and opens a borderline candidate to **replay** what the society decided while they were away. Step by step: the **Research-Fit Advocate** champions a genuine-looking alignment → the **Authenticity Auditor** tears into a specific inflated claim, the contradicting receipt surfacing from the professor's own papers → the **Capacity Assessor** flags there's no funded slot → across rounds the agents visibly reference each other → the **Arbitrator** resolves and drafts the response → the professor overrides or approves. The wow is *legibility*: a real, grounded, multi-agent argument made visible and re-watchable, every claim carrying a receipt — not a chat log, and not theatre.

### Rubric map (engineering-weighted: depth 30 / innovation 30 / problem value 25 / presentation 15\)

Weights confirmed against the official FAQ (2026-06-30). Track: **Agent Society**.

| Rubric dimension | Where Parallax earns it |
| :---- | :---- |
| Innovation & AI creativity (30) | Perspective flip to the professor; society that *disagrees* and resolves; channel-agnostic intake abstraction; non-trivial structural logic and code modularity |
| Technical depth & engineering (30) | Multi-round simultaneous debate with termination control; grounded RAG over two corpora; cheap/expensive triage split. **FAQ explicitly rewards: custom skills, MCP tools, and performance profiling** — the in-process MCP tool bus (§6) and skill-shaped agent tools are direct depth signals to build out |
| Problem value & impact (25) | Documented, growing pain (§ problem definition); a side no existing tool serves; commercial/productization or open-source adoption path (revenue not required, but the scaling logic must be argued) |
| Presentation & documentation (15) | The debate-replay surface; the wow beat; clean before/after of noise→signal; clarity of the architecture diagram |

### Hard deliverable criteria (hackathon)

**Submission deadline: 2026-07-09, 2:00 PM PT — submit on Devpost.** No codebase edits after the boundary; judges evaluate the repo exactly as it stands at the deadline (fork if you want to keep optimizing). All items below are mandatory judging gates:

- [ ] **Public source repo** with a detectable **open-source license file** visible in the About section (cloning another repo is banned).
- [ ] **Live video demo, 1–3 min** on YouTube (public or unlisted), showing the multi-agent workflow running live.
- [ ] **System architecture diagram** — data routes, model dependencies, tool calls, node structure.
- [ ] **Written functional summary** — features, runtime behaviors, practical uses.
- [ ] **Alibaba Cloud deployment verification** — console screenshot proving the backend runs live on Alibaba Cloud **ECS or SAS**. Capture early, not on the last day.

**Mandatory tech constraint:** all core model calls must hit Qwen Cloud managed APIs (`dashscope-intl.aliyuncs.com`, or the Token-Plan routing host for `sk-sp-*` keys) — self-hosting Qwen weights or calling non-Qwen model endpoints is disqualifying. Orchestration frameworks (LangChain, LangGraph, Dify, MaxKB) are **explicitly permitted** as long as the model brain routes through the Qwen Cloud key.

---

## 9\. Open decisions log

| \# | Decision | Status | Provisional default |
| :---- | :---- | :---- | :---- |
| 1 | Nigeria eligibility | **DONE** | — |
| 2 | Agent framework (Qwen-Agent vs. alternative) | **OPEN — now unblocked** | FAQ (2026-06-30) explicitly permits LangChain / LangGraph / Dify / MaxKB, provided the model brain routes through the Qwen Cloud key. Pick one and wire `NegotiationEngine` on top of it |
| 3 | Debate round cap | `[CONFIRM AT BUILD]` | 3 |
| 4 | Model per agent | `[CONFIRM AT BUILD]` | — |
| 5 | Vector store \+ embedding model | `[CONFIRM AT BUILD]` | — |
| 6 | Final decision label set | `[CONFIRM AT BUILD]` | invite / request-more-info / decline |
| 7 | Delegate/assistant role model | `[CONFIRM AT BUILD]` | shared login, no separate perms |
| 8 | Which onboarding thresholds are user-exposed | `[CONFIRM AT BUILD]` | — |
| 9 | Auto-resolve boundary — which outcomes resolve without HITL vs. always queue | `[CONFIRM AT BUILD]` — must respect Principle 5 | only no-outbound / reject auto-resolves |
| 10 | What happens if the professor *is* at the UI while an item processes — live view vs. replay-only | **OPEN** | replay-only (treat all review as after-the-fact) |
| 11 | Debate-replay presentation style — structured step-through vs. animated personas | **OPEN — design** | structured step-through |

## 10\. Infrastructure & stack

This section documents the resolved infrastructure decisions. The principle governing all choices: put on Alibaba Cloud only what the hackathon requires; keep stateful managed services on their own perpetual free tiers to avoid the 60-day credit clock.

| Layer | Technology | Hosting | Rationale |
| :---- | :---- | :---- | :---- |
| **Backend API** | FastAPI \+ Pydantic | Alibaba Cloud ECS | Hackathon hard requirement; satisfies "backend runs on Alibaba Cloud" |
| **Background workers** | Celery | Same ECS instance | Debate jobs are async by nature (§5.5); Celery drives the task queue |
| **Message broker** | Redis | Redis Cloud free tier (fallback: Alibaba ApsaraDB for Redis if covered by trial credits) | Celery broker \+ result backend; Redis Cloud has a perpetual free tier that avoids the 60-day Alibaba credit window |
| **Primary database** | PostgreSQL | Supabase | Structured storage for Outreach objects, decisions, professor corpus metadata |
| **Authentication** | Supabase Auth | Supabase | Professor login only (students are never users — §2); shares the Supabase project |
| **Vector store** | pgvector extension | Supabase (same Postgres instance) | Closes decision \#5; one datastore for structured \+ vector data, no additional moving part |
| **Object storage** | Cloudflare R2 | Cloudflare | Publication PDFs (§5.1) and CV attachments (§4.2); perpetual free tier, no egress fees |
| **LLM inference** | Qwen models via DashScope (OpenAI-compatible) | Alibaba Cloud managed API | **Mandatory** — core model calls must hit `dashscope-intl.aliyuncs.com`; self-hosting weights or non-Qwen endpoints is disqualifying. **Token-Plan gotcha:** `sk-sp-*` keys must target `https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` or every call 401s. Also toggle **off** the free-quota mode in the console or coupon credits never spend |
| **Email intake** | Dedicated intake address \+ inbound parse webhook | Cloudflare Email Routing (preferred) or Postmark Inbound (fallback) | Every email to the intake address is definitionally outreach-intent — the professor publishes this address, not their personal inbox. Webhook POSTs parsed payload to FastAPI, which creates the Outreach shell and fires the Gatekeeper. A `POST /outreach` endpoint also accepts raw payloads directly for demo replay without live mail delivery. |
| **Frontend** | Next.js / React | Vercel | Hobby tier; four surfaces only (§7) |