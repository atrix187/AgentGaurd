"""AgentGuard - demo interface.

Built to the specification in Tariq's document. Three sections: request input,
live pipeline trace, audit trail. No logic lives here - this layer calls what
Amer and Noor built and displays the result.
"""

import streamlit as st

from config import (
    AGENT_ID,
    SCENARIO_PHONE_NUMBERS,
    SCENARIO_TEXTS,
    SCENARIOS,
    USE_MOCK_BACKEND,
)





if USE_MOCK_BACKEND:
    from mocks import DecisionEngine, DummyProcurementAgent, run_agentguard
else:
    from agent.procurement_agent import DummyProcurementAgent
    from core.langgraph_pipeline import run_agentguard
    from decision.decision_engine import DecisionEngine


SIDE_BY_SIDE = True

st.set_page_config(
    page_title="AgentGuard — AI Security Control Plane",
    page_icon="▮",
    layout="wide",
)




STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink: #121821;
    --panel: #1A222E;
    --panel-2: #212B39;
    --line: #2C3849;
    --text: #E2E8F0;
    --muted: #8B9AAE;
    --approved: #46A47B;
    --stepup: #D19A3E;
    --blocked: #D4574F;
}

.stApp { background: var(--ink); }

html, body, [class*="css"], .stMarkdown, p, span, div, label {
    font-family: 'Archivo', system-ui, sans-serif;
    color: var(--text);
}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden;
}

.block-container { padding-top: 2.2rem; max-width: 1400px; }

/* Masthead */
.ag-mast {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.9rem;
    margin-bottom: 1.8rem;
}
.ag-mast h1 {
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0;
    color: var(--text);
}
.ag-mast .ag-sub {
    font-size: 0.9rem;
    color: var(--muted);
    margin: 0;
}

/* Section headings */
.ag-head {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 0.15rem 0;
}
.ag-note {
    font-size: 0.82rem;
    color: var(--muted);
    margin: 0 0 0.9rem 0;
    max-width: 62ch;
    line-height: 1.5;
}

/* Panels */
.ag-panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.8rem;
}

/* Telecom signal rows */
.ag-signal {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 0.62rem 0;
    border-bottom: 1px solid var(--line);
}
.ag-signal:last-child { border-bottom: none; }
.ag-signal .ag-name { font-size: 0.88rem; font-weight: 500; }
.ag-signal .ag-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    text-align: right;
}
.ag-signal .ag-val.ag-hit { color: var(--blocked); }
.ag-signal .ag-val.ag-ok { color: var(--approved); }

/* Flags */
.ag-flag {
    display: inline-block;
    background: var(--panel-2);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 0.22rem 0.55rem;
    margin: 0 0.35rem 0.35rem 0;
    font-size: 0.78rem;
    color: var(--text);
}

.ag-prose {
    font-size: 0.9rem;
    line-height: 1.62;
    color: var(--text);
    max-width: 72ch;
}
.ag-label {
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 0.3rem;
}
.ag-mono {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
}

.ag-empty {
    border: 1px dashed var(--line);
    border-radius: 6px;
    padding: 2.4rem 1.2rem;
    text-align: center;
    color: var(--muted);
    font-size: 0.88rem;
}

/* Streamlit widget overrides */
.stTextArea textarea {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-size: 0.88rem !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: var(--muted) !important;
    box-shadow: none !important;
}

div[data-baseweb="select"] > div {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
}

.stButton > button {
    background: var(--text);
    color: var(--ink);
    border: none;
    border-radius: 6px;
    font-family: 'Archivo', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.55rem 1.5rem;
    width: 100%;
}
.stButton > button:hover { background: #FFFFFF; color: var(--ink); }
.stButton > button:focus-visible { outline: 2px solid var(--muted); outline-offset: 2px; }

.stButton > button p, .stButton > button div, .stButton > button span {
    color: var(--ink) !important;
    font-family: 'Archivo', sans-serif !important;
    font-weight: 600 !important;
}
.stButton > button:hover p, .stButton > button:hover div, .stButton > button:hover span {
    color: var(--ink) !important;
}

[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.1rem !important;
    font-weight: 500 !important;
    color: var(--text) !important;
}

/* The decision band. Streamlit already colours success/warning/error green,
   orange and red as the spec requires; currentColor picks that up so one rule
   covers all three states. */
[data-testid="stAlert"] {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-left: 3px solid currentColor !important;
    border-radius: 6px !important;
    padding: 1rem 1.15rem !important;
}
[data-testid="stAlert"] p {
    font-size: 1.02rem !important;
    font-weight: 600 !important;
    color: currentColor !important;
}
[data-testid="stAlert"] svg { display: none; }

hr { border-color: var(--line); margin: 2rem 0 1.4rem 0; }

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

st.markdown(
    """
    <div class="ag-mast">
      <h1>AgentGuard</h1>
      <p class="ag-sub">Verifies high-risk AI agent actions against live telecom signals
      before they reach your payment systems.</p>
    </div>
    """,
    unsafe_allow_html=True,
)




if "request_text" not in st.session_state:
    st.session_state.request_text = SCENARIO_TEXTS[SCENARIOS[0]]
if "pipeline_output" not in st.session_state:
    st.session_state.pipeline_output = None
if "final_response" not in st.session_state:
    st.session_state.final_response = None


def _prefill_scenario() -> None:
    """Load the chosen scenario's text into the input box."""
    st.session_state.request_text = SCENARIO_TEXTS[st.session_state.scenario]




def render_input_panel() -> bool:
    st.markdown('<p class="ag-head">Incoming request</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ag-note">A procurement agent is asking to change a vendor\'s bank '
        'details. Pick a scenario or paste your own text.</p>',
        unsafe_allow_html=True,
    )

    st.selectbox(
        "Demo scenario",
        SCENARIOS,
        key="scenario",
        on_change=_prefill_scenario,
    )
    st.text_area("Request text", key="request_text", height=210)
    return st.button("Run AgentGuard")


def _signal_rows(signals: dict) -> str:
    """Build the rows for the telecom checks that actually ran."""
    labels = {
        "sim_swap": "SIM swap",
        "device_status": "Device status",
        "device_swap": "Device swap",
        "number_verification": "Number verification",
    }
    rows = []
    for key, label in labels.items():
        signal = signals.get(key)
        if signal is None:
            continue

        if key == "sim_swap":
            hit = signal["swapped"]
            value = (
                f"swapped {signal['days_since_swap']}d ago" if hit else "no recent swap"
            )
        elif key == "device_status":
            hit = not signal["reachable"]
            value = signal["status"].replace("_", " ").lower()
        elif key == "device_swap":
            hit = signal["device_swapped"]
            value = "device changed" if hit else "unchanged"
        else:
            hit = not signal["verified"]
            value = f"{'verified' if signal['verified'] else 'failed'} · {signal['verification_method']}"

        tone = "ag-hit" if hit else "ag-ok"
        rows.append(
            f'<div class="ag-signal"><span class="ag-name">{label}</span>'
            f'<span class="ag-val {tone}">{value}</span></div>'
        )
    return "".join(rows)


def render_trace(pipeline_output: dict, final_response: dict) -> None:
    st.markdown('<p class="ag-head">Pipeline trace</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ag-note">Each step the agent took, and what it found.</p>',
        unsafe_allow_html=True,
    )


    score_col, level_col = st.columns([1, 2])
    with score_col:
        st.metric(label="Risk Score", value=f"{pipeline_output['risk_score']}/10")
    with level_col:
        flags = pipeline_output["risk_flags"]
        chips = (
            "".join(f'<span class="ag-flag">{flag}</span>' for flag in flags)
            if flags
            else '<span class="ag-mono">none raised</span>'
        )
        st.markdown(
            f'<div class="ag-label">Risk level</div>'
            f'<div class="ag-prose" style="margin-bottom:.7rem;">'
            f'{pipeline_output["risk_level"]}</div>'
            f'<div class="ag-label">Flags</div><div>{chips}</div>',
            unsafe_allow_html=True,
        )


    st.markdown('<div class="ag-label" style="margin-top:1.2rem;">Network checks</div>',
                unsafe_allow_html=True)
    rows = _signal_rows(pipeline_output["telecom_signals"])
    if rows:
        st.markdown(f'<div class="ag-panel">{rows}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="ag-panel"><span class="ag-mono">No checks run — the agent '
            'judged the request low risk and skipped verification.</span></div>',
            unsafe_allow_html=True,
        )


    decision = final_response["decision"]
    display = final_response["decision_display"]
    if decision == "APPROVED":
        st.success(display)
    elif decision == "STEP_UP":
        st.warning(display)
    else:
        st.error(display)

    st.markdown(
        f'<div class="ag-label" style="margin-top:.9rem;">Reasoning</div>'
        f'<div class="ag-prose">{final_response["reasoning"]}</div>'
        f'<div class="ag-label" style="margin-top:1rem;">Telecom summary</div>'
        f'<div class="ag-prose">{final_response["telecom_summary"]}</div>',
        unsafe_allow_html=True,
    )


def render_audit_trail() -> None:
    st.markdown("---")
    st.markdown('<p class="ag-head">Audit Trail</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ag-note">Every decision is recorded with the reasoning that '
        'produced it.</p>',
        unsafe_allow_html=True,
    )

    entries = DecisionEngine().get_audit_trail(limit=10)
    if not entries:
        st.markdown('<div class="ag-empty">No decisions logged yet</div>',
                    unsafe_allow_html=True)
        return

    rows = [
        {
            "Timestamp": entry["timestamp"],
            "Vendor": entry["vendor_name"],
            "Decision": entry["decision"],
            "Risk Score": entry["risk_score"],
            "Reasoning": entry["reasoning"],
        }
        for entry in entries
    ]
    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn(width="small"),
            "Vendor": st.column_config.TextColumn(width="small"),
            "Decision": st.column_config.TextColumn(width="small"),
            "Risk Score": st.column_config.NumberColumn(width="small"),
            "Reasoning": st.column_config.TextColumn(width="large"),
        },
    )




if SIDE_BY_SIDE:
    left, right = st.columns([5, 7], gap="large")
else:
    left, right = st.container(), st.container()

with left:
    run_clicked = render_input_panel()

if run_clicked:
    raw_text = st.session_state.request_text
    phone_number = SCENARIO_PHONE_NUMBERS[st.session_state.scenario]

    with st.spinner("AgentGuard is analyzing the request..."):
        request_payload = DummyProcurementAgent().receive_request(
            raw_text, AGENT_ID, phone_number
        )
        pipeline_output = run_agentguard(request_payload)
        final_response = DecisionEngine().process(pipeline_output)

    st.session_state.pipeline_output = pipeline_output
    st.session_state.final_response = final_response

with right:
    if st.session_state.final_response:
        render_trace(st.session_state.pipeline_output, st.session_state.final_response)
    else:
        st.markdown(
            '<div class="ag-empty">Run a request to see how AgentGuard decides.</div>',
            unsafe_allow_html=True,
        )

render_audit_trail()
