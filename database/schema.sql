
create table if not exists vendors (
    id                     bigserial primary key,
    name                   text not null,
    relationship_months    integer not null default 0,
    bank_detail_changes    integer not null default 0,
    last_bank_change_date  text,
    total_volume_usd       integer not null default 0
);

create table if not exists audit_logs (
    id                     bigserial primary key,
    timestamp              timestamptz not null default now(),
    decision               text,
    decision_display       text,
    risk_score             integer,
    risk_level             text,
    action_type            text,
    vendor_name            text,
    agent_id               text,
    raw_request_snippet    text,
    reasoning              text,
    flags_summary          text,
    telecom_summary        text,
    risk_flags             jsonb,
    telecom_signals        jsonb,
    approver_phone         text
);
