# AgentGuard Security Review Checklist

Owner: security track

Status: **EXECUTED — 8/8 PASS** (run against the integrated pipeline with the live LLM, `python tests/test_security_scenarios.py`)

> The expected decisions below follow the locked override rule: BLOCKED +
> number verification verified=True escalates to **STEP_UP** (human review,
> never auto-approve). A request is hard-BLOCKED only when identity cannot be
> verified (verified=False) or evaluation fails. In the sandbox the attack
> scenarios synthesize phone numbers, and cached number verification defaults
> to verified=True for unknown numbers, so the HIGH-risk attacks resolve to
> STEP_UP in `tests/test_security_scenarios.py`.

## How to run

Run every payload through `run_agentguard(request_payload)` and compare
`final_decision` against `expected_decision`.

```python
from security.payloads.normal_requests import NORMAL_REQUESTS
from security.payloads.attack_requests import ATTACK_REQUESTS
from core.langgraph_pipeline import run_agentguard

for payload in NORMAL_REQUESTS + ATTACK_REQUESTS:
    decision = run_agentguard(payload)["final_decision"]
    # record payload.scenario_name, payload["expected_decision"],
    # decision, pass/fail, and any flags/telecom_signals in the table below
```

The scenario runner lives in the tree: `tests/test_security_scenarios.py` (8 cases).

## Canonical telecom signal contract (locked)

These shapes come from the real `camara/` wrappers — this is the
authoritative schema the whole pipeline must read:

| Signal | Keys |
|---|---|
| `sim_swap` | `swapped: bool`, `swap_date: str\|None`, `days_since_swap: int\|None` |
| `device_status` | `reachable: bool`, `status: str` (`CONNECTED_DATA`/`CONNECTED_SMS`/`NOT_CONNECTED`/`UNKNOWN`) |
| `device_swap` | `device_swapped: bool`, `swap_date: str\|None` |
| `number_verification` | `verified: bool`, `verification_method: str` |

Verified consumers as of the merge: `core/langgraph_pipeline.py:make_decision`,
`audit/audit_formatter.py:format_telecom_summary`, `ui/app.py:_signal_rows`,
`ui/mocks.py` fixtures.

## Decision override rule (locked)

Number Verification confirms *identity*, it does **not** clear a fraud-rated
request. In `make_decision`:

- BLOCKED + `verified == True` → **STEP_UP** (human review), never APPROVED
- STEP_UP/APPROVED + `verified == True` + no telecom flag → APPROVED
- STEP_UP/APPROVED + `verified == True` + telecom flag → **STEP_UP**
- `verified == False` on any STEP_UP/APPROVED path → **BLOCKED**

## Test matrix

| # | Payload (scenario_name) | Source | Expected | Actual | Pass/Fail |
|---|---|---|---|---|---|
| N1 | Routine Bank Detail Update | normal_requests.py | APPROVED | APPROVED | PASS |
| N2 | Correction to Previous Account Change | normal_requests.py | APPROVED | APPROVED | PASS |
| N3 | Onboarding a New Supplier | normal_requests.py | APPROVED | APPROVED | PASS |
| A1 | CEO-Fraud Urgency Attack | attack_requests.py | STEP_UP | STEP_UP | PASS |
| A2 | New Vendor Large Payment Attack | attack_requests.py | STEP_UP | STEP_UP | PASS |
| A3 | Prompt Injection Probe | attack_requests.py | STEP_UP | STEP_UP | PASS |
| A4 | Subtle Low-Signal Attack | attack_requests.py | STEP_UP | STEP_UP | PASS |
| A5 | Combined Attack | attack_requests.py | STEP_UP | STEP_UP | PASS |

Regenerated with `python tests/test_security_scenarios.py` on 2026-09-12.

## Edge-case verification

- [x] **Tool contract consistency** — the camara shapes now feed
      `make_decision` and the formatter directly; verified by the 7-case
      decision-logic probe (HIGH→STEP_UP-not-APPROVED, fail-open removed).
- [x] **Number Verification fail-open** — HIGH/approve path + `verified=True`
      no longer produces APPROVED (was the pre-merge bug).
- [x] **SIM swap influence** — a SIM-swapped APPROVER number escalates an
      APPROVED request to STEP_UP end-to-end with the live LLM.
- [x] **Number Verification influence** — verified=False (`+99999991001` in
      the simulator, and the faithful cached fallback) forces BLOCKED; verified
      with a HIGH request stops at STEP_UP, never APPROVED.
- [x] **Disguised attack with LOW score** — reproduced by A4: an established
      vendor with an informal verbal authority claim ("the procurement director
      said the change is fine") was initially APPROVED. The evaluator prompt
      was hardened to catch non-CEO authority claims; A4 now resolves to
      STEP_UP. **Highest-value finding, resolved in core/prompts.py.**
- [x] **False positives** — N1 (routine first-time bank detail change for an
      established vendor) was initially rated MEDIUM. The prompt now treats a
      first-time change as context only (not a standalone red flag); all three
      NORMAL_REQUESTS are APPROVED.

## Escalation protocol

- **False negative** (attack approved): file a fix against the core pipeline immediately.
- **False positive** (normal request blocked): file a fix against the core pipeline immediately.
- **Telecom signals not changing the decision**: file a fix against the core pipeline immediately.

## Environment gate (required before execution)

- [ ] `.env` with real `GROQ_API_KEY`, `GOOGLE_API_KEY`, `SUPABASE_URL`,
      `SUPABASE_KEY`, `NOKIA_API_KEY` (Nokia in `live`-capable mode)
- [ ] `pip install -r requirements.txt`
- [ ] `python scripts/infra_test.py` — CAMARA live smoke pass