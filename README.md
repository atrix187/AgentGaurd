# AgentGuard — AI Security Control Plane for Enterprise Agents

**AgentGuard intercepts high-risk AI agent actions and verifies them against live telecom signals before a single payment leaves the building.**

Built for the **GSMA MENA Open Gateway Hackathon** — Theme 4: *Secure Fintech, Payments & Anti-Fraud Innovation* — using GSMA Open Gateway **CAMARA APIs** exposed on the **Nokia Network-as-Code** platform, orchestrated by an **AI agent layer** built with LangGraph and LLMs.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](#) [![LangGraph](https://img.shields.io/badge/LangGraph-agent-blueviolet.svg)](#) [![CAMARA](https://img.shields.io/badge/CAMARA-Open%20Gateway-2ea44f.svg)](#) [![Nokia NaC](https://img.shields.io/badge/Nokia-Network%20as%20Code-4b6cb7.svg)](#)

---

## The Problem

Enterprise AI agents are being granted **real authority over financial and operational systems** — they can change vendor bank details, initiate payments, and update records. Attackers already know this:

- **Prompt injection** hides instructions inside a "request" that tell the agent to override its own security rules.
- **CEO-fraud / business email compromise (BEC)** pushes urgency to skip review and wire funds to a new IBAN.
- **SIM swap & device swap** let an attacker take over the approving human's phone number so a spoofed confirmation looks legitimate.

An AI agent executes these attacks **instantly, at scale, and without hesitation** — but today, almost nothing sits between the agent and the sensitive systems it controls.

## The Solution

AgentGuard is a **policy and security control plane** that sits between an enterprise AI agent and its payment systems. When a high-risk action is attempted:

1. **An LLM risk evaluator** reads the request text and the vendor's history, scores the risk (1–10), and raises red flags (urgency language, CEO-fraud claims, override instructions, new-vendor + large-payment combos, prompt injection attempts).
2. **An agentic telecom orchestration step** calls **CAMARA APIs on the Nokia Network-as-Code platform** as trusted, out-of-band signals about the approving human — *not* actions a user triggers, but data the agent pulls and reasons over in real time.
3. **A decision engine** combines the two: **APPROVED**, **STEP-UP verification required**, or **BLOCKED** — and every decision lands in an immutable **audit trail** for regulators and finance teams.

The innovation: **telecom network intelligence becomes an unforgeable fraud detector.** A recent SIM swap on the approver's number, a phone moved to a new device, an unreachable handset, or a failed number verification are exactly the signals a BEC attack cannot fake — and the AI agent uses them to challenge or block the action before it executes.

## How It Works (Agentic Flow)

```
Human/attacker request ──▶ Enterprise AI agent (procurement copilot)
                          wants to change an approver's bank details
                                     │
                                     ▼
                       ┌─────────────────────────────┐
                       │  AGENTGUARD PIPELINE        │
                       │                             │
                       │  1. evaluate_risk (LLM)     │  risk_score 1-10
                       │     Groq (GPT-OSS-120B)     │  LOW / MEDIUM / HIGH
                       │     Gemini fallback         │  flags + reasoning
                       │                             │
                       │         low ────▶ 3. decide  │  ✔ APPROVED (skip checks)
                       │         ▼                   │
                       │  2. check_telecom (CAMARA)  │  SIM swap / device status
                       │     Nokia Network-as-Code    │  device swap / number verify
                       │                             │
                       │         ▼                   │
                       │  3. make_decision           │  ✔ APPROVED
                       │     + telecom override rules│  ⚠ STEP-UP (human review)
                       │                             │  ✖ BLOCKED (fraud signals)
                       └──────────┬──────────────────┘
                                  │ every verdict
                                  ▼
                       Supabase audit trail (immutable)
                       ── risk flags, telecom signals,
                       ── reasoning, approver identity
```

### The telecom override rules (this is the magic)

| Signal (CAMARA API) | On the approver's number | Override rule |
|---|---|---|
| **SIM Swap** | swapped within last 10 days | APPROVED ➜ STEP-UP |
| **Device Swap** | SIM re-paired to a different phone | APPROVED ➜ STEP-UP |
| **Device Status** | device unreachable | APPROVED ➜ STEP-UP |
| **Number Verification** | verified = human on device | BLOCKED ➜ STEP-UP (never auto-approve fraud) |
| **Number Verification** | failed | ANY decision ➜ BLOCKED |

## CAMARA APIs Used (Nokia Network-as-Code)

| CAMARA API | SDK call | What it proves | Simulator number for demo |
|---|---|---|---|
| [SIM Swap](https://github.com/camaraproject/SimSwap) | `client.sim_swap.check()` + `retrieve_date()` | Number recently switched SIMs | `+99999991000` (swapped) |
| [Device Swap](https://github.com/camaraproject/DeviceSwap) | `client.device_swap.check()` + `retrieve_date()` | SIM moved to a different device | `+99999991000` (swapped) |
| [Device Status](https://github.com/camaraproject/DeviceStatus) | `client.device_status.check_connectivity()` | Handset reachable / NOT_CONNECTED | `+99999991002` (NOT_CONNECTED) |
| [Number Verification](https://github.com/camaraproject/NumberVerification) | `client.number_verification.verify_v2()` | The human is physically holding the device | `+99999991000` (true) / `+99999991001` (false) |

Auth is via Nokia's RapidAPI gateway (`network-as-code.nokia.rapidapi.com`) — register free at **networkascode.nokia.io**, then put your API key in `.env`. The **Simulator plan** means the entire demo runs with free test numbers and no billing account.

## The AI Agent Layer

Built **only** with the hackathon's allowed tooling (Resource & Tooling Guide):

- **LangGraph** — stateful, conditionally-routed agent pipeline (`core/langgraph_pipeline.py`). The agent *decides* whether to call network APIs: LOW risk skips them entirely; MEDIUM/HIGH consult SIM swap + device status; HIGH additionally requires device swap + number verification.
- **Groq (GPT-OSS-120B), fallback Gemini Flash** — the risk-reasoning brain (`core/risk_evaluator.py`). Returns structured JSON (score, level, flags, reasoning) that is schema-validated before it is trusted; any failure fails **closed** to BLOCK.
- **Red-flag ruleset** (`ghaith/red_flags/red_flag_ruleset.py`) — the fraud taxonomy grounding the prompt: urgency, CEO-fraud claims, override instructions, new-vendor + large-payment, and prompt injection targeting the evaluator itself.
- **DecisionEngine + audit trail** (`decision/`, `audit/`) — sanitizes, persists every verdict to Supabase, fail-safe closed; never crashes open.
- **CAMARA as trusted data sources, not buttons** — the agent calls them as tools, reasons over the returned signals, and applies override rules. Everything is user-triggered only in the sense that a human review happens when flagged.

## Repository Layout

```
agent/               DummyProcurementAgent (the enterprise copilot AgentGuard guards)
core/                LangGraph pipeline, LLM risk evaluator, prompts
camara/              Nokia Network-as-Code CAMARA clients (SIM swap, device status, device swap, number verification)
tools/               Tool-stub bridge locking the CAMARA signatures the pipeline imports
decision/            DecisionEngine (sanitize, override rules, verdict)
audit/               Audit formatter + Supabase audit logger
ghaith/              Red-flag ruleset, 8 attack/normal payloads, security review checklist
tariq/               Streamlit demo UI (mock + real backends via USE_MOCK_BACKEND)
database/            Supabase schema (vendors, audit_logs)
seeds/               Seed data for the 3 demo vendors
scripts/             infra_test.py (Supabase + CAMARA smoke test), audit_test.py
main.py              CLI demo (normal + attack through the full pipeline)
```

## Getting Started

### 1. Prerequisites

- Python 3.12
- Free accounts (no credit card):
  - **Nokia Network-as-Code** — networkascode.nokia.io (API key)
  - **Groq** — console.groq.com (free API key)
  - **Supabase** — supabase.com (project + keys)
  - *(optional)* **Google AI Studio** for the Gemini fallback

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# fill in SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, NOKIA_API_KEY
```

Apply the database schema and seed vendors in the Supabase SQL editor:

```bash
# contents of database/schema.sql, then seeds/seed_vendors.sql
```

### 4. Run the demo

**Streamlit UI (recommended for judging / live demo):**

```bash
streamlit run tariq/app.py
```

- With `USE_MOCK_BACKEND=false` (set in `.env`): full real pipeline — LangGraph + Groq LLM + Nokia CAMARA simulator + Supabase audit trail.
- With `USE_MOCK_BACKEND=true` (default): same UI, offline mocks, no secrets needed.

**CLI (10-second check):**

```bash
python main.py
```

**Test harnesses:**

```bash
python scripts/infra_test.py            # Supabase + all CAMARA checks
python scripts/audit_test.py            # DecisionEngine across APPROVED/STEP_UP/BLOCKED
python test_ghaith_scenarios.py         # all 8 attack/normal scenarios end-to-end
```

### 5. Live demo script (2 minutes)

1. Open the Streamlit UI. Pick **"Normal Request"** and hit **Run AgentGuard** — the agent returns ✅ APPROVED, reasoning shows why it skipped telecom checks.
2. Pick **"Attack Request"** — the LLM flags urgency language, a verbal CEO-fraud claim and an override instruction (risk 9/10). The agent calls the network APIs; the approver's simulator number comes back with a recent SIM *and* device swap. Verdict: ⚠ STEP-UP — **the fraud never auto-executes** — with each telecom signal shown in the trace. (Switch the approver number to `+99999991001`, which fails Number Verification, and the same request hard-blocks with ❌.)
3. Scroll to the **Audit Trail** — both decisions are persisted with full reasoning for the compliance story.

## Scenario Coverage (8 test cases)

| Scenario | Expected | What AgentGuard catches |
|---|---|---|
| Routine bank detail update | ✅ APPROVED | Nothing to flag — routine, established vendor |
| Correction to previous change | ✅ APPROVED | Consistent with on-file agreement |
| Onboarding a new supplier | ✅ APPROVED | Small, non-urgent — new vendor alone is not a flag |
| CEO-fraud urgency attack | ⚠ STEP-UP | Urgency + verbal-CEO claim + override + SIM/device swap → **never auto-executed** |
| New vendor large payment | ⚠ STEP-UP | First full payment to a new counterparty, urgent |
| Prompt injection probe | ⚠ STEP-UP | Injection addressed to the evaluator itself |
| Subtle low-signal attack | ⚠ STEP-UP | Informal verbal authority claim ("the director said it's fine") |
| Combined attack | ⚠ STEP-UP | Override + CEO-fraud + injection all at once |

Why STEP-UP and not BLOCKED for the attacks? By design (the locked override
rule): when Number Verification confirms the approver is physically holding the
device, a fraud-flagged request is escalated to **human review — it is never
auto-executed**. A request is hard-**BLOCKED** when identity cannot be verified
(Number Verification fails) or when evaluation itself fails. The attack never
reaches payment in any path.

## Security Philosophy

- **Fail closed, always.** A failed LLM call, an unreachable API, or a parsing error defaults to HIGH risk → BLOCK, never APPROVE.
- **Number verification confirms identity, it does not clear fraud.** A verified number on a BLOCKED request only escalates to human review — a SIM-swapped attacker will happily "verify" from the phone they control.
- **Every decision is auditable** — flags, telecom signals, vendor, and reasoning stored per verdict.

## Team

Built for the hackathon by a five-person cybersecurity team from Amman, Jordan — working across AI agent orchestration, CAMARA infrastructure, decision/audit engineering, a demo frontend, and an adversarial red-team view of the enterprise threat.

---

**Theme:** Secure Fintech, Payments & Anti-Fraud Innovation
**Platform:** Nokia Network-as-Code · GSMA Open Gateway CAMARA APIs
**AI Agent Layer:** LangGraph + Groq/Gemini (approved hackathon tooling only)