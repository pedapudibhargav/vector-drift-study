# L4 Human Review Pack — HIGH priority (62 rows)

## How to use this pack

You are auditing **document Hit@10** for an IEEE Access study on vector retrieval drift.

### Two checks (do not mix)
1. **ID membership (L1):** Is the gold `doc_id` in retrieved top-10? (already computed as `hit_at_10`)
2. **Answer quality (L4 human):** Does the gold **text** actually answer the question?

Primary paper metrics use (1). Your labels document (2) and failure modes.

### Label options (enter for each row)
| Field | Allowed values |
|-------|----------------|
| `human_label_correct` | `y` = auto Hit@10 fair as ID check **and** gold text is a plausible answer; `n` = disagree; `unsure` = need second look |
| `human_failure_mode` | one of the modes below (required if `n` or on clear miss with bad gold) |
| `human_notes` | short free text |

### Failure modes
- **`embedding_near_miss`** — Gold is semantically close but wrong doc / near-miss crowding
- **`lexical_mismatch`** — Wording overlap but not the right fact/answer
- **`semantic_near_miss`** — Same topic neighborhood; answer not actually present
- **`wrong_source_type`** — Wrong document class / source_type for the question
- **`stale_gold`** — Gold ID points to outdated or superseded content
- **`chunk_too_thin`** — Chunk too short / truncated / missing the needed section
- **`label_noise`** — Gold ID is labeled but text does NOT answer the question (ERB label weak)
- **`multi_gold_partial`** — Partial multi-doc gold; incomplete coverage
- **`metadata_needed`** — Would need metadata filter / type constraint to find gold
- **`other`** — Does not fit above — explain in notes

### Guidance (common cases)
- Gold ID in top-10 but text does **not** answer Q → often `n` + **`label_noise`** (not a Hit@10 math error).
- Gold ID missing from top-10 → Hit@10 miss is ID-correct; skim top-k for near-miss; mode often `embedding_near_miss` / `semantic_near_miss` / `metadata_needed`.
- You do **not** need to deeply read all 10 on every miss; skim titles/first lines; open full text only if unsure.
- Closest lexical chunk ≠ correct answer. Prefer honesty (`label_noise`) over forcing a due-date that is not there.
- Chunks are **dataset documents** (EnterpriseRAG-Bench), not LLM-written. Previews may be truncated at ~4k chars in the UI; this pack truncates further for upload size.

**Rows in this file:** 62

---

## Row 1: `qst_0002::metadata` · N=20000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`other`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The gold chunk is non-empty but unrelated to the question about a new metric for SRE tracking. Retrieved chunks are also non-empty but off-topic, focusing on audit logs and security rather than server-side streaming metrics. The hit flag is incorrectly set to true, indicating a pipeline issue.

### Question

Who was the internal organizer listed for the security review call about an on-prem backup and audit log retention discussion with a healthcare customer in February 2025?

### Gold document(s)

#### GOLD `dsid_aa97b7293f9f4f3c8180f645e4fe5911`

```
MedData Systems - on-prem backup/restore + audit log retention security review

Meeting header
Date: 2025-02-11
Start time: 1:00 PM ET
Duration: 53 minutes
Title: MedData Systems - on-prem backup/restore + audit log retention security review
Organizer: Markus Klein (Redwood)
Attendees (Redwood): Markus Klein, Aisha Rahman, Hanae Suzuki
Attendees (MedData): Dana Wright, Priya Shah, Eli Brooks, Nina Gomez

Auto-summary (Fireflies)
- MedData asked detailed questions on on-prem backup encryption, retention, audit log export, and audit evidence.
- Redwood clarified that backups are encrypted (envelope encryption) and can be configured for customer-managed keys; in air-gapped mode, keys can be handled via on-prem KMS/HSM depending on integration.
- Redwood explained scope: control-plane state and configuration are backed up; data plane is treated as stateless; Kubernetes cluster recovery (etcd) is a separate procedure.
- Discussion covered audit log retention/export format, immutability options, and what operational evidence Redwood can generate (manifests, checksums, restore validation reports).

Topics
1) On-prem backup scope and retention ownership
2) Encryption at rest, KMS/HSM, key rotation, and KMS outage behavior
3) Audit log export + retention (long-term, immutable/WORM)
4) Evidence needs for regulated audits (restore drill proof, reports)
5) Operational boundaries: cluster recovery vs app-level restore

Action items (recap)
- Redwood to send written security note re: envelope encryption + KMS/HSM availability behavior.
- Redwood to send example backup manifest + restore validation report outline.
- MedData to confirm retention + immutability requirements and storage target.

Transcript

[00:00] Markus Klein: Alright, I think we’re good. Thanks everyone for joining. This is Markus from Redwood. We’ve got Aisha from security and Hanae from our secrets and key management side. Uh, Dana, Priya, Eli, Nina — thanks for making time.

[00:13] Dana Wright: Yep. Thanks Markus.

[00:15] Priya Shah: Hi.

[00:16] Eli Brooks: Hey.

[00:18] Markus Klein: Cool. The goal today is to go through the on-prem backup and restore story for Redwood Private and then specifically audi
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_52dc2b5dcfe44149b98a30b4345ee03e`

```
AxiomCare Guardian Networks

AxiomCare wants a VPC-hosted agent assist + ticket summarization solution that preserves PHI/PCI confidentiality, provides immutable audit logs exported to SIEM, integrates with their CRM via tool-calling, and remains reliable under large bursty spikes. Evaluation focuses on latency SLOs, HSM/KMS compatibility, and retention/audit controls.
Primary pain: agent desktop latency + compliance overhead — ~12k monthly support interactions, mix of PHI and cardholder data
Wanted: agent assist + automated post-call summaries to reduce AHT and speed triage. Also need tool-calling for case updates in their CRM.
Latency target: <200ms token latency for interactive agent assist during peak (6k concurrent agents spikes unpredictable). Throughput: burstable to 500 rps for short windows.
Cost sensitivity: mid — will trade incremental cost for deterministic latency and audited controls. Interested in Optimize recommendations for batching/quantization.
Security notes: must run in VPC w/ no public egress for KV cache. KMS/HSM required for key management. Data residency requirement: US-only processing and retention controls configurable per-tenant.
Quote from Director of S
…[truncated]
```

#### #2 `dsid_b896f53a79d44d3e821d793922b445df`

```
HolisticSpark Care Co

2026-03-05: Inbound signup via marketing site. Self-serve trial started (free credits). — Product lead (Maya Singh) filled trial form: 'looking to add AI triage to therapist portal, must avoid long-term PHI storage.'
2026-03-08: Qual call (Jordan Myers + Maya). Discovery. Use-case: chat-first teletriage + embeddings for intake docs + summarization for session notes. Volume: initial PoC ~50 active providers, ~10 reqs/sec peak, low concurrency expected. Latency target: sub-300ms for turn responses. Cost sensitivity: 'we're small — need predictable unit cost; prefer hosted to avoid infra ops.'
Asked about: data retention controls, ability to purge transcripts, audit logs for clinical review, SSO for admin UI. They are HIPAA-adjacent (not a covered entity yet) but legal wants HIPAA-like controls.
2026-03-09: Sent security FAQ and SOC2/attestation summary. Included standard hosted API data flow diagram. Maya: 'nice overview, but need explicit retention window and deletion API.'
2026-03-10: Legal asked for written guarantee on retention and whether Redwood stores request/response bodies longer than X days. Also asked whether PII is written to logs and how long. SE 
…[truncated]
```

#### #3 `dsid_4dc77de6649d4e0799648a18290d96b5`

```
BlueCrest Secure Support

Account background: BlueCrest runs payments reconciliation + telehealth billing support for a set of regional clinics and a payments gateway. Heavy PCI + PHI scope; central support org handles escalations and chargeback disputes.

Call highlights (2026-01-15):
- CISO (R. Gomez): "cannot leave payment PANs or PHI in external storage; need KMS + HSM, full audit trail to SIEM."
- Head of Support Ops (L. Chen): looking for agent assist to reduce AHT by 20%, live suggestion latency <150ms, and summarization that produces 3-4 sentence TL;DRs with configurable retention windows.
- Platform Lead (M. Patel): asks for VPC deployment, private control plane, and the ability to pin model versions + automatic fallbacks during capacity events.

Technical constraints / must-haves:
- VPC/private deployment mandatory for POC.
- SAML SSO + SCIM provisioning integrated into Okta.
- Audit logging forwarded to Splunk/SIEM with 90-day hot retention, 7-year cold retention for payment dispute records.
- KMS/HSM integration for envelope encryption; customer will not allow Redwood-managed keys without HSM-backed KMS.
- Tokenization or redaction pipeline for PAN/PHI before model expo
…[truncated]
```

#### #4 `dsid_23899e82cf1c443e94b7d2cde199f08f`

```
Admin telemetry extraction & retention sync - Cascade Financial

Focused review of Redwood's admin activity and audit telemetry: what events are captured, export delivery options (S3, BigQuery, webhook), log schema, retention controls, and how this maps to Cascade Financial's SOC2/ISO requirements. Agreed next steps: share artifacts, run a sample export, and decide on retention window.
What admin activity is logged (logins, API keys, role changes, model deploys, dataset access)
Export mechanisms: batch S3 export, streaming webhook, Pub/Sub/BigQuery sinks
Retention windows and legal hold / exportable archives
KMS / key rotation and how encrypted logs are stored
RBAC/SSO integration impact on auditability
Private/VPC deployment nuances and on-prem audit forwarding
[00:00:00] Maya Chen: Hey everyone, thanks for carving out the time. We wanted to walk through the admin telemetry story end-to-end so you can validate it against Cascade's controls.
[00:00:12] Priya Rao: Thanks Maya. High level — we need to confirm that changes to admin roles, API tokens, model rollouts, and access to sensitive datasets are captured and exportable. SOC 2 says we need immutable audit trails for those action
…[truncated]
```

#### #5 `dsid_573ca1fc195e450e85e3f10d1a068cf6`

```
HelmBridge Healthcare

Account background:
- Enterprise healthcare SaaS provider, strong on PHI workflows. Interested in on-prem/VPC option early (HIPAA concerns).
- Initial intro 2025-09-12 (AE: Priya). Demo delivered 2025-10-05 (SE: Marcus) — focus on low-latency clinical assistant and secure embeddings for document search.
- 2025-11-20 security kickoff w/ InfoSec (paperwork: NDA + data flow diagram). Requested SOC2 + HIPAA articulation and KMS/HSM details.
- POC (2025-12-18 -> 2026-01-08): small clinical assistant POC using hosted variant; we demonstrated latency and cost estimates. POC passed functional tests but security team required VPC endpoints + SIEM integration.
- Procurement review 2026-01-25: finance ran TCO vs hyperscaler-managed endpoints. Their pricing model (with committed AWS discounts) made AWS Bedrock managed endpoints ~25-30% cheaper operationally given no additional ops headcount.
- Final decision 2026-02-10: chose AWS native managed endpoints + PrivateLink for data in transit; quote from CTO: "We can't add a new ops surface right now — exec mandate is to consolidate on existing cloud services."
- Post-mortem notes: timeline slipped on private deployment timel
…[truncated]
```

#### #6 `dsid_e312cfbed0c149f39f147813ace0ff09`

```
Sapphire Harbor Ops

2026-02-09 - Inbound self-serve signup (trial) via marketing form
2026-02-18 - Automated welcome email + docs sent
2026-02-20 - Intro call: AE (Avery) + CTO (Maya Chen). Rapid discovery.
2026-03-02 - Security Q&A w/ legal (requested retention SLA info). Fireflies link above.
2026-03-04 - Technical deep-dive scheduled; SE (Ravi) to demo retention controls
Lead profile: SMB, product = fleet ops + customer support, want LLM to summarize incident reports and triage tickets.
Primary concern: data privacy + retention. Legal wants explicit controls, ability to opt-out and to delete prompt history on demand.
Asked: "Do you persist raw prompts? For how long? Can we disable storage per workspace/user?"
AE notes: prefers hosted_api for speed of rollout; price-sensitive but willing to pay for retention guarantees.
SE notes: walked through hosted defaults - suggested short-term retention + redact PII at ingestion layer. Customer asked for examples of API flags to opt-out.
Customer quote on call: "We cannot have our customers' PII show up in training or logs - lawyers will not approve otherwise."
Requested artifacts: retention SLA language, sample API params for prompt-scrub
…[truncated]
```

#### #7 `dsid_ea23b1139d4141c483f46443089031e0`

```
Sable Counsel LLC

Inbound SMB lead from legaltech vertical. Small team (20 ppl), building a contract review assistant and internal knowledge search. Priority: keep all audit logs for 12 months, must store logs in US region only — "must not leave US" (quote from CTO).

Security checklist: interested in SSO/SAML, KMS for key wrapping, and per-request audit entries (requestor, route, model, prompt hash, token counts). Concerned about PII in prompts and want guidance on redaction or client-side hashing.

Cost sensitivity: price matters, will start with low-volume self-serve but expects bursts during monthly review cycles.

Current status: discovery — signed up for trial but hasn't started heavy testing. Asking for: sample audit-log schema, retention options + costs, confirmation of US region hosting, and a short doc on how Redwood handles prompt retention vs. ephemeral KV cache.

Notes from call (shorthand):
- CTO Samir: 'we cannot send raw SSNs or client identifiers to non-US servers'
- Legal ops lead wants example SOC2 language for procurement package
- AE action: send hosted-api security FAQ + sample logs schema; loop in SE for technical call

Next step: schedule technical deep-div
…[truncated]
```

#### #8 `dsid_97c88c6d322d4a09b28cbd9b294c8035`

```
Baycrest Care Coaching

SMB wellness app building 'CareCoach' — chat-first coaching + light triage. Interested in Redwood hosted API (self-serve) to avoid infra ops. HIPAA-adjacent: not a covered entity but ingests PHI-like fields (names, appointment notes). Key ask: can we ensure transient storage and have a data deletion endpoint + explicit retention controls?

Latency/throughput: small traffic today (~50-200 reqs/day), peak expectations 10-20 reqs/min during business hours. Target p95 latency <= 500ms for chat responses; cost-sensitive — prefer smaller open models or efficient quantized variants.

Security needs: Okta SSO for admin console, audit logs for user actions (1yr retention), ability to restrict data to US regions. KMS integration would be nice but not a blocker if hosted encryption at rest + strict retention available.

POC asks from call: 1) sample retention policy snippets showing automatic token/log purge; 2) example payloads for delete-by-customer API; 3) pricing scenarios for 100k-500k tokens/month; 4) short tech session for SE to validate prompt handling and embeddings privacy.

Quotes from call: "We just want to be careful with names and notes — we won't store r
…[truncated]
```

#### #9 `dsid_22938cefdddd421fad44fecd5fddef95`

```
Sensitive logs intake: prioritization ladder & legal routing for redaction, retention, export

Goal: define a deterministic intake and prioritization ladder for customer requests that involve sensitive logs (PII, regulated identifiers, or security telemetry) and the downstream handling: redaction, retention adjustments, and audit exports. This ticket scopes the prioritized decision matrix, routing rules to Legal/Compliance, required evidence for exec approvals, and per-customer runbooks for safe execution. We will produce: 1) a triage ladder mapping risk categories to response paths and SLAs; 2) routing matrix (self-serve -> PM -> Legal -> Engineering) with automation triggers; 3) templates for customer-facing responses and internal runbooks; 4) a checklist for engineering change requests (RBAC, encryption, k-anonymization), and 5) observability/QA tests for regression on redaction pipelines. Out of scope: bulk data migration tooling and on-prem install packaging (handled by Private infra team).
A documented prioritization ladder that maps request types (retention change, export, PII redaction, legal hold) to risk tiers and required approvals.
A routing matrix with automated trigge
…[truncated]
```

#### #10 `dsid_a89e842138d4471ea632c42f5d8c33b4`

```
Sunshadow Health Solutions

Inbound SMB lead from wellness app (consumer-facing triage + coach chat). Currently 2 engineers + 1 product working on POC. Wants self-serve hosted API but with tight retention controls. HIPAA-adjacent — not a covered entity but plan to collect health symptoms and appointment details; client legal wants clarity on PHI handling. Key quotes: "We need to be sure nothing that looks like PHI is persisted in logs by default"; "Can we set retention to 0 days for message bodies?". Primary concerns: auditability for incidents, encryption keys, token-level cost sensitivity for chat workloads (short sessions, spikes during clinic hours). Not asking for private deployment yet; prefers fast time-to-value and predictable costs. Asked about: BAA stance for hosted API (they expect we may require Private for BAA), log retention options, ability to disable telemetry, request-level tags for CS/engineering tracing, and whether cached prefixes are ever persisted to long-term storage.

Action items: share hosted API security FAQ + retention options (drive doc), clarify default log retention and opt-out, provide sample SDK code to strip PII before send, send quick cost calc fo
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 2: `qst_0002::metadata` · N=100000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The retrieved chunks are on-topic regarding security and audit logs but do not address the specific question about a new metric for server-side streaming sessions. The gold chunk is relevant to the question but does not contain the expected document ID in the retrieved list, indicating a lexical mismatch. The hit flag is incorrectly set to True, causing a mismatch.

### Question

Who was the internal organizer listed for the security review call about an on-prem backup and audit log retention discussion with a healthcare customer in February 2025?

### Gold document(s)

#### GOLD `dsid_aa97b7293f9f4f3c8180f645e4fe5911`

```
MedData Systems - on-prem backup/restore + audit log retention security review

Meeting header
Date: 2025-02-11
Start time: 1:00 PM ET
Duration: 53 minutes
Title: MedData Systems - on-prem backup/restore + audit log retention security review
Organizer: Markus Klein (Redwood)
Attendees (Redwood): Markus Klein, Aisha Rahman, Hanae Suzuki
Attendees (MedData): Dana Wright, Priya Shah, Eli Brooks, Nina Gomez

Auto-summary (Fireflies)
- MedData asked detailed questions on on-prem backup encryption, retention, audit log export, and audit evidence.
- Redwood clarified that backups are encrypted (envelope encryption) and can be configured for customer-managed keys; in air-gapped mode, keys can be handled via on-prem KMS/HSM depending on integration.
- Redwood explained scope: control-plane state and configuration are backed up; data plane is treated as stateless; Kubernetes cluster recovery (etcd) is a separate procedure.
- Discussion covered audit log retention/export format, immutability options, and what operational evidence Redwood can generate (manifests, checksums, restore validation reports).

Topics
1) On-prem backup scope and retention ownership
2) Encryption at rest, KMS/HSM, key rotation, and KMS outage behavior
3) Audit log export + retention (long-term, immutable/WORM)
4) Evidence needs for regulated audits (restore drill proof, reports)
5) Operational boundaries: cluster recovery vs app-level restore

Action items (recap)
- Redwood to send written security note re: envelope encryption + KMS/HSM availability behavior.
- Redwood to send example backup manifest + restore validation report outline.
- MedData to confirm retention + immutability requirements and storage target.

Transcript

[00:00] Markus Klein: Alright, I think we’re good. Thanks everyone for joining. This is Markus from Redwood. We’ve got Aisha from security and Hanae from our secrets and key management side. Uh, Dana, Priya, Eli, Nina — thanks for making time.

[00:13] Dana Wright: Yep. Thanks Markus.

[00:15] Priya Shah: Hi.

[00:16] Eli Brooks: Hey.

[00:18] Markus Klein: Cool. The goal today is to go through the on-prem backup and restore story for Redwood Private and then specifically audi
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_03bea1fa6f944d479b97f6c30123c252`

```
MedData Systems

Deployment: On-prem Kubernetes, fully air-gapped (no external calls, no container pulls during install/restore). Customer requires deterministic Day-2 procedures for backup/restore + DR with documented RPO/RTO targets. Backup scope expectations: Redwood Private control-plane state (config DB/control-plane datastore), Helm values/manifests needed for deterministic redeploy, and audit log export/retention. They explicitly do NOT want backup artifacts to contain raw secret material unless encrypted with customer-managed keys; preference is backing up references + rehydrate via their secret manager where possible.

Backup storage preferences: primary preference is NFS to an internal backup network (with their existing enterprise backup tooling); secondary acceptable option is on-prem S3-compatible object store (MinIO) provided the workflow works without public cloud IAM/KMS. They asked for clear guidance on access control patterns and expected permissions (least privilege) for the backup job/service account.

Encryption & key management: encryption-at-rest required for all backup artifacts; strong preference for envelope encryption with customer-managed keys. They ment
…[truncated]
```

#### #2 `dsid_e5307f0e837d43cbbf8fc9c954e198cf`

```
Northbridge Health

Private deployment for regulated workloads (HIPAA). Use cases: clinical note summarization, internal doc Q&A, and contact-center agent assist. Strong emphasis on enterprise security posture.

Audit logging (must-have):
- Canonical, versioned schema (customer asked specifically for schema_version and stable event_id).
- Coverage for sensitive actions across Console/admin + control plane + Private installer/upgrade actions.
- Actor semantics: must capture who did it (user/service principal), when impersonation is used, and source IP / user agent when available.
- Target semantics: must identify resource type + id (tenant/project/user/role/api_key/policy/export_destination) and include before/after summaries for config changes.
- Export to SIEM: Splunk HEC is primary; customer also asked about Azure Sentinel/Log Analytics. Wants guidance on de-dupe and idempotency behavior.

RBAC/SSO (must-have):
- Okta SAML SSO for Console/admin; MFA enforcement is on customer side.
- RBAC needs: granular roles for Security Ops vs Platform Ops vs App teams; audit logs must reflect role membership and policy changes.

Data controls:
- Data residency: US-only for audit data; wants e
…[truncated]
```

#### #3 `dsid_ee0c47a803054794ac6aec50a360d537`

```
Meridian Patient Analytics

Account snapshot: stalled / closed-lost to on-prem focused competitor. Last official status: procurement; security review failed to sign-off HIPAA BAA in time.\n\nTimeline (concise):\n- 2025-11-20: Lead created via webinar signup (Alicia).\n- 2025-12-02: Intro discovery call (AE + SE) — requirements: PHI processing, SSO, 7-day audit log retention, data residency in US-only.\n- 2025-12-15: Technical deep-dive with Infra + CISO. Provided security pack + SOC2 docs. CISO requested explicit BAA + HSM/KMS architecture diagram.\n- 2026-01-05: 2-week POC kickoff (on Dedicated cluster) — demo dataset (de-identified) used for latency benchmarks.\n- 2026-01-08: Recorded call (Fireflies FF-20260108-1723) with CISO — they expressed \"need signed BAA + proof of encryption at rest with HSM.\"\n- 2026-01-10: Procurement informs AE that internal legal/security will not approve vendor without either: (a) completed BAA + independent HIPAA attestation, or (b) a fully air-gapped on-prem appliance. Competitor offered on-prem appliance and signed required contracts faster.\n\nKey technical notes / requirements:\n- Workloads: clinical note summarization, triage chat for patient
…[truncated]
```

#### #4 `dsid_ef4636bb7f1a419f82eed955664238f8`

```
Obsidian Health Vault

Prospect: large national telehealth provider. Priorities: keep PHI in-customer VPC, strict audit trail, and customer-managed keys.
- Security says: must see SOC 2 control IDs + mapping to Redwood hosted/private features.
- Legal: wants BAA + explicit PCI scoping statement for payment card capture on appointment flows.
- Architecture ask: show AWS VPC peering model or PrivateLink option, egress controls, and how flow logs/audit logs are exported to customer's Splunk.
- KMS: customer requires BYOK with AWS KMS and HSM-backed key; needs rotation policy and proof of zero-access key material by Redwood.
- Data residency: primary need EU region for storage and logs, backups to be retained in-region unless explicit approval.
- Quote from InfoSec: "We cannot accept any unmanaged backups or plain-text token storage."
- POC success criteria: demonstrate model serving within customer VPC, show audit log stream with event types (auth, request metadata, token counts), and validate KMS-encrypted model artifacts.
Next steps: deliver compliance mapping (SOC 2/ISO/ HIPAA/PCI) by 2026-02-18, architecture diagram by 2026-02-20, schedule legal follow-up week of 2026-02-23.
Relat
…[truncated]
```

#### #5 `dsid_ffe615af6fe74ea7a98d5b9e365c1972`

```
Valencia Health Regulatory Partners

Primary workload: clinician-facing summarization of visit notes (PHI), conversational triage tool for nurses, and fast document search across EMR attachments. Requirements: on-prem/VPC deployment, data residency within US, strict audit logs, BAA required. Latency SLOs: 150-300ms token for chat, batch embedding throughput for nightly indexing. High cost-sensitivity for infra procurement.
2025-09-10 - Initial discovery with CTO + Head of Data. Use-case: PHI-enabled summarization and clinician assistant. Asked about on-prem option.
2025-10-05 - Demo of hosted API (no PHI) with latency targets: <200ms token for short chat. Interested but flagged compliance concerns.
2025-11-18 - SE deep-dive: presented private deployment options, KMS flow, drive links shared. Security questionnaire requested.
2025-12-12 - Submitted security questionnaire + network diagram. Security team responded with additional controls requested (HSM, audit export cadence).
2026-01-22 - Valencia security vendor ran third-party assessment; flagged potential egress on batch jobs. Legal requested HIPAA attestation and business associate agreement (BAA).
2026-02-02 - Final commercial 
…[truncated]
```

#### #6 `dsid_645197711b374a9bbfb1a49013cc2219`

```
Ironroot ComplianceCare

VPC deploy or on-prem appliance; HSM + KMS; SAML SSO; immutable audit logs; retention export; stress test to 3x baseline; fallback to hosted with opt-in telemetry
Lead: Senior Dir of Support Ops (K. Alvarez). Use-case = payment support for patient billing platform; handles PHI + card data; tickets include sensitive payment tokens.
- Wants agent assist: real-time suggestion snippets in voice & web chat, source attribution for snippets.
- Ticket summarization: end-of-shift summaries + compact SOAP-style summaries for downstream accounting.
- Tool-calling: webhook/callout to internal CRM + payment gateway to pull masked transaction info; needs strict audit trail for every tool call.
- Reliability: critical spikes during insurance cycle month-end and open enrollment peaks; must survive 3x baseline load for 48h with graceful degradation.
- Latency targets: interactive suggestions p95 < 150ms, end-to-end ticket summarization job < 60s for batch of 500 tickets.
- Throughput estimate: baseline 200 rps; peak planning 3000 rps; bursty voice request patterns.
- Cost sensitivity: moderate; willing to pay premium for VPC/HSM guarantees but expects Optimize recommendatio
…[truncated]
```

#### #7 `dsid_26f5cb5024fa4ff68dc6cf0a8caabf61`

```
Helio Health Systems

Account summary
- Large provider network + analytics org. Primary concern is PHI handling + operational safety; they’re pushing hard for Private (on-prem) or at minimum a tightly controlled VPC with explicit PHI boundaries.
- Their security team is treating “optimization config changes” (batching/caching/quant profiles) as production changes that must be auditable and reversible, not “tuning knobs.”

Workload / use-case
- Internal clinician note summarization + discharge instruction drafting (high sensitivity).
- Patient portal search / retrieval over clinical content (embeddings + reranking).
- Contact center agent assist (summarize prior encounters, suggest next steps). They called out streaming as “nice to have,” but predictable p95 is mandatory.

Target requirements captured (from POC check-ins + security review)
- Latency: p95 <= 900ms for short prompts; p99 <= 2.5s. They have periodic spikes from EHR batch jobs and want stable tail latency.
- Throughput: wants ability to reserve predictable capacity during clinic hours; can tolerate slower batch processing overnight.
- Deployment: prefers on-prem for first phase (existing GPU cluster). If VPC: must be si
…[truncated]
```

#### #8 `dsid_a8e91c51c409404cbd58310e3cb1c860`

```
Summit Telehealth

Summit is exploring a patient support assistant for appointment logistics + benefits questions, with escalation to live agents. They are explicitly trying to keep the assistant "PHI-light" but acknowledge that free-text messages may contain PHI. They asked for (a) VPC/private deployment option, (b) retention controls (ideally 0-day for request/response payloads; logs retained separately), (c) audit logs exportable to their SIEM, (d) SSO/SAML for console access, and (e) US-only processing/residency. They are cost-sensitive and expect spiky traffic (weekday peaks) and want predictable latency for chat responses.
Key question: will the workflow ever process/store PHI (likely yes due to patient free-text). Their stated goal is "PHI-adjacent" but Security will treat it as PHI until proven otherwise. They want to separate (1) application payload retention (prefer 0-day / no storage) from (2) audit/security logs (need retention for compliance + investigations). Asked if Redwood supports configurable retention and if audit logs can exclude prompt/response bodies while still preserving access + admin events. Also asked about data residency (US) and whether any sub-process
…[truncated]
```

#### #9 `dsid_6917f17be3d64f609026f972dc35eb93`

```
Lumen MedInsights

Inbound lead (Nov 2025). AE Maya Chen assigned.
- Discovery 2025-12-02: stakeholders: CTO Arun Singh, Sr Data Eng Priya Rao, Clinical lead Dr. Ellen Park.
- Use-case: ingest EMR notes + triage assistant for nursing staff. High sensitivity (PHI) — HIPAA scope. Need auditable inference and retention controls.
- Demo held 2026-01-18 (screen share): showed hosted API, dedicated pools, and private VPC/on-prem options. Emphasized Redwoods' audit logs and KMS integration.
- Demo feedback: liked private runbook, asked detailed HSM/KMS integration examples and audit-log retention SLAs.
- Action items: Maya -> send security FAQ + POC architecture; Ravi (SE) -> scope 2-week POC + cost; Legal -> finalize NDA (done).
- Security questionnaire sent 2026-01-20. Lumen security team returned with follow-ups specifically on key management (HSM) and on-prem deployment steps.
- Follow-ups: tailored POC & pricing sent 2026-01-25 (drive link above). CC: Priya, Arun. No reply.
- Outreach cadence: 2x calls + 3x emails between Feb 1-5. Voicemail left for Arun 2026-02-03. No response.
- Support ticket RED-1987 opened to get SOC2 artifacts and HSM references; support resolved on 2026-02-04 
…[truncated]
```

#### #10 `dsid_9b199ee0d27242749095cda255f8bc3f`

```
Security Criteria Declaration & Acceptance Framework for Private Deploy

This ticket establishes a declarative acceptance framework and endorsement checklist for security and compliance controls required for Private (VPC/on-prem) deployments. The goal is to make acceptance criteria explicit for SSO (SAML/OIDC), RBAC role surfaces, immutable audit logging, and customer-managed key integrations (KMS/HSM), and to capture scope clarifications, trade-offs, and sign-off owners. This is part of the Private Deploy Security project and complements the operator runbooks and onboarding flow.

Background: Customers require a predictable, auditable onboarding path that demonstrates the Private control plane satisfies enterprise security requirements (federated identity, least-privilege access, encrypted key management, tamper-evident logs). Past ambiguities around which audit events are considered "sensitive" and whether KMS key rotation must be synchronous caused onboarding delays. This document clarifies those points and defines the acceptance flow for product, security, compliance, and operations teams to endorse readiness.
Identity federation: End-to-end SAML 2.0 flow with Okta, OneLogin, o
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 3: `qst_0003::metadata` · N=5000 · raw · priority=high

- **auto Hit@10:** `True`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs include the expected document ID, confirming the Hit@10. However, the content of the gold and retrieved chunks is unrelated to the question about UI color states and elevation scales, indicating a lexical mismatch. The chunks discuss office inventory and keycard cleanup, which is off-topic. The chunk quality is low due to irrelevance, despite being non-empty.

### Question

In the engineering ops cleanup ticket about reconciling office equipment and deactivating old access cards, what is the due date?

### Gold document(s)

#### GOLD `dsid_c5288dd4874345adb80f4a71c9a18773`

```
misc-chores-office-inventory-and-keycard-cleanup

Background: Office moved desks last quarter; several untagged peripherals, old keycards, and leftover badge holders in storage. This ticket collects misc chores to reconcile inventory and tidy shared spaces.

Goals:
- Produce a concise inventory of unassigned equipment (monitors, keyboards, spare GPUs boxes, dongles)
- Audit and deactivate lost/old keycards in the access system and return/reenroll active ones
- Clean and label community storage shelves and mark disposal candidates

Acceptance criteria:
- CSV inventory uploaded to Drive with columns: item_id, type, location, status, owner_hint
- Keycards deactivated or reassigned; list of card IDs with status documented
- Disposal list handed to Facilities with approval note

Notes / messy log:
- Found box labeled "quantization-experiments-2019" that might contain ancient NVMe; hold for review before E-waste.
- Some badge IDs appear in the access logs for 2024 despite being in the lost-and-found — need cross-check (security notified).
- Short timeline requested by Facilities: prefer completion before holiday break.

Planned steps:
1) Quick sweep team (1-2 engs + facilities) to inventory storage (2 days)
2) Collate CSV, tag physically (labels on boxes) (1 day)
3) Keycard audit with security (Omar to coordinate) (2 days)
4) Disposal / reallocation decisions and update asset tracker (1 day)

This ticket is intentionally lightweight and is a catch-all for small physical tasks that don't merit a formal facilities request. If any item is sensitive (hard drives, HSM parts, private compute media) escalate to security and open a separate INT ticket.
2025-11-10 - Maya Chen: Created initial ticket after impromptu storage sweep. I'll coordinate volunteers.
2025-11-11 - Omar Singh: Reached out to Security about keycard audit; they suggested exporting access logs for the last 18 months.
2025-11-12 - Facilities Bot: Tentative sweep scheduled 2025-11-18 10:00 in 3A storage room. RSVP required.
```

### Retrieved top-10

#### #1 `dsid_c5288dd4874345adb80f4a71c9a18773` **← GOLD ID**

```
misc-chores-office-inventory-and-keycard-cleanup

Background: Office moved desks last quarter; several untagged peripherals, old keycards, and leftover badge holders in storage. This ticket collects misc chores to reconcile inventory and tidy shared spaces.

Goals:
- Produce a concise inventory of unassigned equipment (monitors, keyboards, spare GPUs boxes, dongles)
- Audit and deactivate lost/old keycards in the access system and return/reenroll active ones
- Clean and label community storage shelves and mark disposal candidates

Acceptance criteria:
- CSV inventory uploaded to Drive with columns: item_id, type, location, status, owner_hint
- Keycards deactivated or reassigned; list of card IDs with status documented
- Disposal list handed to Facilities with approval note

Notes / messy log:
- Found box labeled "quantization-experiments-2019" that might contain ancient NVMe; hold for review before E-waste.
- Some badge IDs appear in the access logs for 2024 despite being in the lost-and-found — need cross-check (security notified).
- Short timeline requested by Facilities: prefer completion before holiday break.

Planned steps:
1) Quick sweep team (1-2 engs + facilities) to invent
…[truncated]
```

#### #2 `dsid_03b2db544a6d4cf886fb9869058a05f2`

```
Office inventory + keycard audit + disposal request (storage shelves + access system cleanup)

Request type: Internal support / facilities + security coordination

Background
Office moved desks last quarter; storage now contains untagged peripherals, old keycards, and leftover badge holders. This ticket consolidates the remaining cleanup work so we can reconcile inventory, tidy shared spaces, and reduce risk from stray credentials.

Scope / Goals
- Produce a concise inventory of unassigned equipment (monitors, keyboards, spare GPU boxes, dongles)
- Audit and deactivate lost/old keycards in the access system and return/re-enroll active ones
- Clean and label community storage shelves and identify disposal candidates for Facilities pickup

Updates vs earlier plan
- Security requested we export access logs for the last 12 months (not 18) for the initial cross-check; they will expand the window only if anomalies are found.
- Anything that could contain data-bearing media (NVMe/SSDs/USBs) must be separated into a "Security review" bin and cannot go directly to e-waste.
- Facilities asked that disposal candidates be grouped into: e-waste, donation, recycle, landfill, and "needs approval"
…[truncated]
```

#### #3 `dsid_463573b2edfe492ca27878c2ef9bc640`

```
Temporary dual-desk setup and outbound equipment shipments for hybrid onboarding in SF North Tower

Issue summary:
- New hire cohort starting 2026-03-15 will be hybrid; several team members need temporary dual-desk access (hot-desk + assigned desk) in SF North Tower. Simultaneously, a number of legacy laptops and peripherals need to be scheduled for outbound return and RMA pickup to our asset vendor.

Impact:
- If badge provisioning and desk setup are not completed by 2026-03-14, 6 engineers will be unable to access office resources on day one, impacting onboarding and scheduled kickoffs. Delays in shipping returns will push asset reconciliation for finance and could result in license and warranty gaps.

Environment:
- Site: SF North Tower (building A)
- Floor: 8th
- Date constraints: desks required by 2026-03-14; pickups ideally 2026-03-16 to align with vendor schedule.

Request / Acceptance criteria:
1) Temporary badge profiles created for 6 employees with dual-desk access window 2026-03-14 through 2026-04-30 (auto-expire).
2) 3 desks pre-staged with monitor stands, power adapters, and docking cables labeled with employee shortcodes.
3) Outbound shipment: 5 laptops and 8 peripher
…[truncated]
```

#### #4 `dsid_3d1b7e13cb98482a98efe6833cf44d85`

```
Dock-to-desk equipment migration + temporary badge access for contractor onboarding (Bldg A, 3rd floor)

Issue summary: We need to move a set of docked developer workstations and peripherals from temporary storage to assigned desks for a 2-week contractor engagement. Request includes temporary badge provisioning for contractor, shipments for two spare monitors and one docking station, and pickup/return logistics.

Impact: Contractors cannot start desk-based work until monitors/docks are installed and badge access is granted. This impacts a short-term engagement with a vendor starting 2026-03-02.

Location: Redwood HQ, Building A, 3rd floor (desks 3A-3D). Asset tags referenced in inventory: RW-DEV-2042, RW-MON-3317, RW-MON-3318, RW-DOCK-118.

Requested outcome: Temporary badge active 2026-03-02 to 2026-03-16 for contractor user "contractor.j.smith@vendor.com", monitors and dock delivered and installed on assigned desks by 2026-03-02 morning, and clear return instructions with pre-paid shipping labels for equipment pickup on 2026-03-17.
2026-02-28 10:12 - Facilities intake: Received asset list and requested delivery window. Confirmed assets present in facilities storage locker A3.
20
…[truncated]
```

#### #5 `dsid_a49b2f5e6fee49b998b5188b80885c42`

```
Satellite office desk: mismatched EU/UK adapter, missing ergonomic footrest, and 48-hour temp badge request

Issue summary:
- New hire (contractor) arriving at Redwood satellite hub (London, Unit 3) needs desk fully provisioned. Outbound shipment arrived with incorrect power adapters (EU two-pin instead of UK three-pin) for monitor and docking station. Ordered ergonomic footrest (SKU FR-21) is missing from the pallet.

Impact:
- Contractor starts Monday 2026-03-15 and requires working desk and temporary building badge for 48 hours. Without UK adapters the monitor/dock won't power; missing footrest is a comfort/ergonomics risk for long sessions and must be provided prior to first day if possible.

Location:
- London satellite hub, Unit 3, Desk cluster B, row 2 (assigned desk B2-07). Courier manifest (DHL AWB 1234-5678-GB) indicates items delivered but packaging mismatch noted in intake photo.

Requested outcome:
- Confirm and ship two UK three-pin power adapters to Unit 3 by 2026-03-13 end of day.
- Locate/ship ergonomic footrest (FR-21) or provide a local loaner by 2026-03-14.
- Issue a temporary building badge active 2026-03-15 08:00–2026-03-16 18:00 for contractor (Name: Jordan R
…[truncated]
```

#### #6 `dsid_8138b96e181940418cc5067b2630064e`

```
Clarify provisional license reclaim window and equipment-return grace period for immediate offboarding

Issue summary:
HR received reports from Finance and IT that when an employee is placed on Immediate Termination (ITerm) in Workday, the seat/license in third-party SaaS (notably the design/legal tool vendor) remains billable for up to 14 days and the assigned corporate laptop sometimes remains tagged as 'active' in our asset management inventory. This ticket seeks clarification of the intended policy (grace windows) and the operational mechanics (which systems enforce the reclaim/return windows).

Impact:
- Potential short-term double-billing for SaaS seats when seats are quickly re-assigned.
- Delays in device recovery leading to inventory inaccuracies and security exposure for high-risk departures.
- Confusion between HR, IT, and Finance on expected timelines and required manual steps.

Environment:
- Identity sync: Okta -> SCIM -> downstream SaaS (prod)
- Asset tracking: FleetOps (prod) with inventory sync to ITSM
- HR system: Workday (prod)

Observed behavior / Steps to reproduce:
1) Create an employee termination in Workday with 'Immediate' flag at 09:00 UTC.
2) Workday emit
…[truncated]
```

#### #7 `dsid_da7e13b65f8a42b4975b44b2db0a36e4`

```
Post-evacuation badge suspension + temporary workstation redistribution and inbound courier hold

Issue summary: During a scheduled building evacuation drill on 2026-03-12, the access control system flagged and automatically suspended a batch of employee badges on floors 6-8. Impact: 9 employees were unable to re-enter after the drill and 2 incoming contractor laptops on an outbound courier manifest were placed on hold by building security. Request: coordinate reactivation of legitimate badges, issue temporary visitor tokens where appropriate, verify asset custody for the held shipments, and perform a short-notice redistribution of two workstations to a shared hotdesk area while badge access is validated.

Impact: Productivity disruption for affected staff (engineering and research), potential missed standups and customer calls, and risk of asset hold/escalation from courier if not cleared same-day.

Environment/details: Access control: OnPrem HID/Cobranet system integrated with Okta SSO for badge-to-identity mapping. Affected floors: 6, 7, 8 (main campus). Shipping vendor: RapidParcel (manifest RP-7621), courier hold at loading dock A. Assets on hold: LPC-ENG-101 (contractor lapto
…[truncated]
```

#### #8 `dsid_d9ac03742f2f4c769507c987d6045436`

```
Cross-site elevator badge not granting floor access after desk relocation; coordinated ergonomic equipment shipment and return

Issue summary: After relocating desk and assigned hotdesk for new hire (L. Novak) from 3rd floor to temporary workspace on 6th floor, their company badge allows door entry but does not grant elevator access to the 6th floor. Concurrently, an ergonomic chair and external monitor shipment intended for the 6th-floor desk was split across two couriers and only the monitor arrived; chair is missing. This ticket coordinates facilities, security, and shipping to restore access and reconcile missing hardware.
New hire onboarding delayed (workspace not fully usable). Facilities team needs to escalate elevator access provisioning to security; missing chair may require overnight replacement. Potential OSHA/ergonomics risk if employee uses unsuitable seating for extended periods.
1) New hire swipes badge at 6th-floor elevator keypad -> elevator panels show "access denied" to floor 6.
2) Badge works for ground floor turnstile and office doors.
3) Inventory check shows monitor delivered (asset tag D-4123) but chair (asset tag C-9780) not in desk area or shipping bin.
4)
…[truncated]
```

#### #9 `dsid_8692c99abe3d4ccdb158cf1abf37ae17`

```
Reassign unused SaaS seats + onboard new identity vendor for engineering org

Issue summary:
Maya requests reallocation of 25 unused seats from inactive project teams to cover a new contractor cohort, and concurrent onboarding of a new identity provider (OneLogin) for SSO across engineering apps. This includes procurement approval, license transfer or cancellation where possible, and updating SSO connections in the central Okta/OneLogin proxy.

Impact:
- Short term: 15 contractors cannot access paid tools this month (CI runners, internal analytics).
- Financial: potential savings if we cancel underused seats; however we must avoid double-spend on overlapping IdP integrations.
- Security/Compliance: IdP change requires security review and SCIM provisioning configuration to ensure least-privilege provisioning.

Environment:
- Internal apps: CI (Jenkins/Buildkite), Analytics (Metabase), Internal Dashboard (Next.js).
- Affected tenant: redwood-engineering@redwood.ai org.

Steps to reproduce / action items (requested):
1) Inventory current seat assignments and license expiry dates for target vendors (Atlassian Confluence/Jira, Metabase, Sentry).
2) Identify 25 reusable seats (inactive u
…[truncated]
```

#### #10 `dsid_562213b6a37e4912add20e642b9f9a15`

```
people-ops

Lila (People Ops): FYI Paulina submitted notice earlier today, last day Thu 4/15. We need to coordinate benefits end date, HSA rollover instructions, device return, and deprovision schedule. Sam can you own the KT plan?
Paulina Ramos: thanks all. Last day is correct. prefer a prepaid ship label for the MacBook. also curious about HSA -- will that stay with me?
Sam (Eng Manager): I'll schedule two 90-min handoff sessions next week and a short doc checklist. will tag owners on active issues.
Priya (IT): noted. options for device: 1) FedEx prepaid label (we email it) or 2) SF office drop. will open ticket and queue the remote wipe for 4/15 18:00 PT after confirm.
Marisol (Payroll): final paycheck includes prorated salary + unused PTO payout. We'll run it on payroll cycle 4/30 so funds hit 5/1. Please confirm bank on file.
Paulina Ramos: bank is same as payroll; use paulina.personal@mail.com for final tax forms and COBRA.
Lila (People Ops): COBRA packet goes out to that email on 4/16. coverage termination is 4/30 (end of month), COBRA election window 60 days. HSA: the HSA account is portable and remains in your name; opt-in/transfer instructions linked in the packet.
Alex (
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 4: `qst_0010::metadata` · N=5000 · meta · priority=high

- **auto Hit@10:** `True`
- **LLM triage (optional):** label=`n` mode=`label_noise`
- **LLM note:** The retrieved document matches the expected document ID, confirming the Hit@10=True label. However, the content of the gold chunk is unrelated to the question about alerting approaches and model-serving requests. This indicates label noise, as the retrieved content does not address the question. The chunk quality is low due to irrelevance, despite being non-empty.

### Question

In the weekly internal sync about a hardware tuning profile pack, what was the due date for the action item assigned to Irene Choi about compiling GPU SKU string variants including MIG suffixes?

### Gold document(s)

#### GOLD `dsid_1415c2463492415693a3d4758847630b`

```
Hardware tuning profiles pack - weekly sync

Meeting: Hardware tuning profiles pack - weekly sync
Date: 2025-12-03
Start time: 17:00 UTC
Duration: 47 minutes
Recorded by: Fireflies.ai

Attendees (Redwood): Talia Benson, Hiro Tanaka, Sofia Ivanova, Irene Choi, Rina Kobayashi, Claire Dubois, Ethan Park, Benji Okafor, Omar El-Sayed, Kira Volkov, Sean Gallagher, Vanessa Ortiz

Auto-summary (generated)
- H100 preset looks net-positive on throughput with a tail-latency caveat that improved after the fairness patch; need one more matrix run to confirm.
- L40S remains the main stability risk due to long-context OOM; KV-cache budgeting guardrails are close but need validation.
- B200 stays behind experimental flag; limited fleet access + driver/CUDA constraints; need stricter gating and region-level disable.
- Perf-canary gates are noisy; plan to adjust thresholds and use multi-run aggregation.

Topics
1) Milestone check: profile pack v0.3.0 content
2) H100 benchmark deltas (balanced vs throughput-first)
3) L40S OOMs + KV cache guardrails
4) B200 experimental profile status and fleet constraints
5) Override order / loader edge cases (SKU strings, MIG)
6) Perf-canary + rollout guardrails

[00:00] Talia Benson: Alright, we’ll get started. This is the hardware tuning profiles weekly. Goal today: quick status from Kernels, Scheduling, Infra, Bench. Then blockers and next steps. We’re aiming for v0.3 pack content freeze end of week-ish, depending on the last matrix run.

[00:22] Talia Benson: Hiro, can you start with H100 kernel side? What changed since last week.

[00:28] Hiro Tanaka: Yeah. So kernel autoselect heuristics by sequence length buckets are in good shape. We adjusted the cutoffs. Previously we were switching too early and it hurt prefill on the mid bucket—like 2k to 4k tokens. Now it’s more stable.

[00:45] Hiro Tanaka: Also, the “balanced” preset is basically stable, but we still have a couple knobs I’m not sure we should freeze in the profile. Specifically the block size toggle—um the one that picks the fused attention variant. It’s safe on H100 SXM, less sure on PCIe.

[01:03] Irene Choi: And we do have both in fleet. The hosted pools are mostly SXM, dedicated
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_1415c2463492415693a3d4758847630b` **← GOLD ID**

```
Hardware tuning profiles pack - weekly sync

Meeting: Hardware tuning profiles pack - weekly sync
Date: 2025-12-03
Start time: 17:00 UTC
Duration: 47 minutes
Recorded by: Fireflies.ai

Attendees (Redwood): Talia Benson, Hiro Tanaka, Sofia Ivanova, Irene Choi, Rina Kobayashi, Claire Dubois, Ethan Park, Benji Okafor, Omar El-Sayed, Kira Volkov, Sean Gallagher, Vanessa Ortiz

Auto-summary (generated)
- H100 preset looks net-positive on throughput with a tail-latency caveat that improved after the fairness patch; need one more matrix run to confirm.
- L40S remains the main stability risk due to long-context OOM; KV-cache budgeting guardrails are close but need validation.
- B200 stays behind experimental flag; limited fleet access + driver/CUDA constraints; need stricter gating and region-level disable.
- Perf-canary gates are noisy; plan to adjust thresholds and use multi-run aggregation.

Topics
1) Milestone check: profile pack v0.3.0 content
2) H100 benchmark deltas (balanced vs throughput-first)
3) L40S OOMs + KV cache guardrails
4) B200 experimental profile status and fleet constraints
5) Override order / loader edge cases (SKU strings, MIG)
6) Perf-canary + rollout guardrails

[0
…[truncated]
```

#### #2 `dsid_672bd385942a466798c7764d484e10d8`

```
GPU Runtime Profiling: kernel selection & TensorRT-LLM vs vLLM deep dive

Header: 2025-03-11 15:30 PT | Duration ~72m | Recording generated by Fireflies.ai
Attendees: Samira Cho (Redwood AE), Miguel Alvarez (Redwood SE), Priya Nair (Redwood Infra), Anika Rao (Helios SRE), Derek Lin (Helios ML Eng), Jason Park (Helios CTO), Lina Gomez (Helios Platform), Oliver (intern)

Summary: quick deep dive into GPU runtime perf profiling. Focus areas: kernel selection heuristics, TensorRT-LLM vs vLLM throughput/latency tradeoffs, CUDA Graphs and warmup, KV-cache evictions, batching strategies, quantization effects on kernel choice, and implications for VPC/on-prem Dedicated runs.

00:00 Samira (AE): okay folks thanks for joining, we were told there was a heavy perf question set from Helios after your initial POC runs, so Miguel and Priya are here to do a deep dive into the GPU runtime stuff.
02:15 Miguel (SE): cool yeah, quick agenda: show microbenchmarks, kernel selection notes (cuBLAS/cuDNN vs custom CUDA kernels), compare TensorR-T LLM flows to v-llm baseline, talk about CUDA Graph warmup and reuse, then open Q&A.
04:02 Derek (ML Eng): quick context — we're running a 8xA100 DGX-ish setup on-
…[truncated]
```

#### #3 `dsid_c8895fca3f6b48c4abc2c926a6e3d671`

```
Kernel Scheduler & CUDA Graph Stability Deep Dive - TRT vs vLLM

Meeting Header:
- Date/Time: 2025-09-10 14:30 UTC
- Duration: ~62 minutes
- Attendees: Jordan Lee (Redwood AE), Priya Nair (Redwood SE), Marco Alvarez (Redwood), Sofia Tran (Redwood); Lisa Chen (Nimbus ML), Arjun Patel (Nimbus Infra), Emily Rogers (CTO), Samir Khatri (SRE)

Auto Summary (auto-generated, may be rough):
Redwood and Nimbus dug into GPU runtime profiling: kernel scheduler behavior, CUDA graph stability under long prompt/large KV cache conditions, and practical differences observed between TensorRT-LLM (TRT-LLM) and vLLM styles of execution. Key risks discussed: CUDA graph instability when kernels are JITed differently across devices, memory fragmentation causing OOMs on longer sequences, and eviction/backpressure patterns with KV cache. Consensus to run targeted stability matrix and a short Dedicated canary.

Topics Covered:
- Kernel scheduler heuristics and how Redwood's runtime chooses kernels
- CUDA graphs: warmup, replay, and deterministic replay failure modes
- TensorRT-LLM vs vLLM: op fusion, padding-handling, and memory layout implications
- KV cache: eviction heuristics, prefix caching, and hit-ra
…[truncated]
```

#### #4 `dsid_0ffeb7f0c944478a86d90f31250abd0d`

```
Gimbal POC Weekly Latency Standup

Weekly POC sync for Gimbal Systems focused on TTFT and streaming latency. Reviewed latest microburst and streaming traces, compared kernel variants, discussed sequence length distributions and KV caching behavior. Agreed next test matrix and action owners; security questions deferred to separate doc share.
TTFT (time-to-first-token)
streaming/handshake latency
kernel selection and fast-paths
sequence length profile
KV cache/prefix caching
VPC/scc/keys and audit logs
Priya to run 1k-sample streaming test (seq_len=512, batch_size=4) with 'fastpath-v2' kernel and share traces by 2026-07-20
Alex to send updated Dedicated + burst pricing and include guidance on autoscale policies by 2026-07-18
Jordan to provide production traffic histogram for sequence lengths and percentiles by 2026-07-19
Redwood and Gimbal to schedule SOC2/KMS follow-up with security docs link (target 2026-07-22)
Priya Desai: Re-run TTFT microburst test with batch_size=8 and kernel=fastpath-v2 (due 2026-07-20)
Alex Kim: Attach Dedicated pricing, burst capacity options, and a simple autoscale policy example (due 2026-07-18)
Jordan Lee: Export and share sequence length histogram (p50/p
…[truncated]
```

#### #5 `dsid_1f590b50d6f94d5793e8a4a09dd6f28a`

```
Pilot: Latency Tuning Weekly - Redwood & Aureus

Header:
Date: 2025-02-07
Start time: 14:00 PST
Duration: 48m
Recording id: ff-20250207-0093
Artifacts referenced: https://redwood.share/benchmarks/aureus-ttft-2025-02 (benchmark sheet), https://redwood.share/configs/aureus-pilot.yaml

Summary (auto): weekly pilot check-in focusing on latency metrics (TTFT), streaming behavior, sequence length effects, and kernel selection. Team agreed to a focused microbenchmark (8k seq streaming) and to enable KV prefix caching. Next steps and owners assigned.

Transcript:
00:00 Erin: hey everyone thanks for hopping on, we'll give it 45 minutes but we've got some specific numbers to walk through. How's everyone doing?
00:07 Carlos: good, thanks. running a little behind with infra but we pulled the latest artifacts you shared.
00:12 Samir: cool, i'll open the bench spreadsheet and jump straight into the TTFT charts. heads up the sheet has two tabs, p50 and p95 by seq length.
00:22 Priya: we tried the client streaming last night — saw partial tokens arriving but the client reassembly had a jitter issue around chunk boundaries.
00:28 Lian: that's probably because we were doing 512 token chunking on the
…[truncated]
```

#### #6 `dsid_521d3db1645c486ab156092611d16435`

```
POC FastPath Convergence Check-in

Weekly check-in for BlueCove POC focusing on fastpath/first-token improvements. Reviewed last week's TTFT numbers, streaming handshake variance, sequence-length profiling, and kernel hedging choices. Agreed on a targeted bench run for microburst 95th percentile and to share kernel selection matrices and bench spreadsheet.
TTFT improvements and median vs 95th
streaming handshake and early-token path
sequence length distribution and caching impact
kernel selection / hedging strategy
microburst mitigation and priority routing
next steps and bench runs
00:00 Lydia Park: Hi everyone, thanks for joining. Can you hear me ok?
00:04 Maya Chen: Yeah, loud and clear. We'll kick off — we got Tomás and Ivy on as well.
00:10 Lydia Park: Great. Quick agenda: run through last week's TTFT numbers, look at streaming variance, sequence length profile, then kernel hedging decisions. Samir will walk the microbench results.
00:22 Samir Kapoor: Hey all. Quick preface, numbers are from the dedicated pool with the new prefix cache enabled, and we used the int8 quant profile for the fastpath experiments.
00:35 Tomás Rivera: Just flag — our traffic shape during peak is pret
…[truncated]
```

#### #7 `dsid_5a936db99e324072ba9522a7a365edae`

```
Northforge - Dedicated Reserve Qualification and Surge Strategy

Discovery call to qualify Northforge's need for reserved GPU capacity. Covered isolation requirements, warm-pool prewarm strategy, eviction tolerances, fallback to hosted variants, compliance (KMS/SOC2), and next steps to run a surge simulation and share pricing + security pack.
Meeting header: 2026-11-25 15:00 PST, Duration: ~58 minutes\nAttendees: Maya (Redwood AE), Ravi (Redwood SE), Lena (Redwood Solutions), Jordan (Redwood CS), Ethan (Northforge HoML), Priya (Platform Eng), Sam (SRE), Tanya (Security), Lee (Product)\n\n00:00 - Maya: ok hey everyone thanks for carving out time, um quick intros on our side, i'm maya ae, ravi is our se who focuses on dedicated runtime and prewarm strategies.\n00:12 - Ethan: yeah hi thanks, i'm ethan, head of ml at northforge, we run a mix of retrieval+generation workloads, mostly inference for chat assistants and some batch embeddings.\n00:22 - Priya: hey i'm priya, platform, we're owning infra side and want to understand isolation and eviction behavior.\n00:30 - Maya: great, high level we wanted to qualify if dedicated reserved capacity makes sense vs hosted, and dig into burst pat
…[truncated]
```

#### #8 `dsid_ef612b48ab244b2ba146e52faf2e4423`

```
Asteria Labs - post-launch stability and budget retune

Quick check-in after their public launch: usage spiked, a subset of routes showing higher p95 latency, FinOps wants immediate cost levers. Discussed batching/kv cache settings, fallback models, and private routing for sensitive requests. Agreed to run a 24h synthetic load and provide per-route cost breakdown + security docs.
[00:00] Maya Chen: Hey everyone thanks for carving out time today, um we wanted to do a short post-launch check in and make sure the performance/cost story is working for you.
[00:08] Ravi Patel: Yeah thanks Maya, busy week. Usage basically doubled the first 48 hours after launch, which is great but we've seen, uh, some tail latency spikes on the /generate-order-summary route.
[00:18] Sofia Gomez: For us the main thing is those p95s — usually fine but during the morning batch we saw 2 to 3 second jumps, and it's impacting the frontend.
[00:28] Diego Alvarez: thanks for the detail Sofia, quick clarifying q; are those requests using the long context model or the 8k?
[00:35] Liam Brooks: It's mixed — product set them to the 32k fallback because of some edge cases but most traffic is 8k.
[00:41] Diego Alvarez:
…[truncated]
```

#### #9 `dsid_6ea8b40caf094294a1b322486d254818`

```
POC SDK & tooling alignment — output hardening

Weekly POC sync focused on SDK integration, function/tool calling reliability, structured-output schema stability, and defining acceptance criteria for output correctness. Agreed to run two targeted benchmarks and tighten fallback behavior for tool calls.
SDK instrumentation and error hooks
function calling edge cases and timeouts
structured JSON output validation and schema enforcement
KV cache/prefix caching oddities
routing to dedicated vs hosted for latency-sensitive endpoints
security: KMS and audit logs
Maya Chen: Share sandbox routing config and sample traffic script by 2026-08-28
Jordan Patel: Run deterministic function-calling stress test (500 concurrent invokes) and upload logs to shared folder by 2026-08-31
Arjun Rao + Jordan Patel: Compare model variant outputs on same prompt set and note regressions by 2026-09-02
Priya Singh: Provide final acceptance criteria doc (pass/fail for structured output) by 2026-08-30
Michael O'Neal: Confirm KMS key rotation policy constraints and send on-call contact by 2026-08-29
Redwood to deliver routing config + traffic generator
Customer to provide canonical prompt set and golden outputs
SE
…[truncated]
```

#### #10 `dsid_79e25f2ba8ac47ec8cfe436691cb4b64`

```
Kestrel Dynamics — Capacity heuristics & prewarm scenario review

Discovery focused on reserved GPU sizing, tenant isolation needs for regulated models, burst/pre-warm strategy, and tradeoffs between Dedicated and Hosted. Customer wants predictable p99 latency for inference, on-prem-like isolation for certain models, and a clear SLA for burst scenarios. Action items include provisioning a small benchmark run, security docs, and a follow-up pilot proposal.
Header: 2026-12-20 16:00 UTC | Duration 52m | Recording started automatically
Attendees: Maya (Redwood AE), Jonah (SE), Iris (SE), Tom (CS); Priya (Head of ML), Carlos (Infra), Luke (CTO), Samir (SRE), Zoe (Product)

00:00 Maya: Hey everyone, thanks for joining. quick intro — I'm Maya, AE on the Redwood Dedicated team. Jonah's gonna go deep on the capacity questions.
00:12 Priya: Thanks, Maya. We wanted to go through how you think about reserved GPU sizing, isolation for some of our sensitive models, and how burst works — we have unpredictable spikes during release cycles.
00:22 Jonah: cool. To kick off, can you give a sense of baseline QPS today and the p95/p99 you need? also sequence lengths — are most of these <512 tokens or lo
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 5: `qst_0010::metadata` · N=40000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty and relevant to technical discussions but do not address the specific question about alerting approaches for model-serving requests. This indicates a lexical mismatch failure mode. No pipeline issues like empty texts or mangled IDs were found, but the ID membership is incorrect.

### Question

In the weekly internal sync about a hardware tuning profile pack, what was the due date for the action item assigned to Irene Choi about compiling GPU SKU string variants including MIG suffixes?

### Gold document(s)

#### GOLD `dsid_1415c2463492415693a3d4758847630b`

```
Hardware tuning profiles pack - weekly sync

Meeting: Hardware tuning profiles pack - weekly sync
Date: 2025-12-03
Start time: 17:00 UTC
Duration: 47 minutes
Recorded by: Fireflies.ai

Attendees (Redwood): Talia Benson, Hiro Tanaka, Sofia Ivanova, Irene Choi, Rina Kobayashi, Claire Dubois, Ethan Park, Benji Okafor, Omar El-Sayed, Kira Volkov, Sean Gallagher, Vanessa Ortiz

Auto-summary (generated)
- H100 preset looks net-positive on throughput with a tail-latency caveat that improved after the fairness patch; need one more matrix run to confirm.
- L40S remains the main stability risk due to long-context OOM; KV-cache budgeting guardrails are close but need validation.
- B200 stays behind experimental flag; limited fleet access + driver/CUDA constraints; need stricter gating and region-level disable.
- Perf-canary gates are noisy; plan to adjust thresholds and use multi-run aggregation.

Topics
1) Milestone check: profile pack v0.3.0 content
2) H100 benchmark deltas (balanced vs throughput-first)
3) L40S OOMs + KV cache guardrails
4) B200 experimental profile status and fleet constraints
5) Override order / loader edge cases (SKU strings, MIG)
6) Perf-canary + rollout guardrails

[00:00] Talia Benson: Alright, we’ll get started. This is the hardware tuning profiles weekly. Goal today: quick status from Kernels, Scheduling, Infra, Bench. Then blockers and next steps. We’re aiming for v0.3 pack content freeze end of week-ish, depending on the last matrix run.

[00:22] Talia Benson: Hiro, can you start with H100 kernel side? What changed since last week.

[00:28] Hiro Tanaka: Yeah. So kernel autoselect heuristics by sequence length buckets are in good shape. We adjusted the cutoffs. Previously we were switching too early and it hurt prefill on the mid bucket—like 2k to 4k tokens. Now it’s more stable.

[00:45] Hiro Tanaka: Also, the “balanced” preset is basically stable, but we still have a couple knobs I’m not sure we should freeze in the profile. Specifically the block size toggle—um the one that picks the fused attention variant. It’s safe on H100 SXM, less sure on PCIe.

[01:03] Irene Choi: And we do have both in fleet. The hosted pools are mostly SXM, dedicated
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_25adb0559afc49b6baa8bec5a796df32`

```
Cross-stage microbatch steering and adaptive kernel routing to maximize NCCL overlap

Problem: On the current multi-GPU serving runtime we see sustained GPU stalls during prefill/decode transitions and large variance in decode p99s when model shapes and request mixes shift. Root causes identified in spikes: (1) monolithic microbatch placement that forces synchronized NCCL collectives across tensor/pipeline stages, (2) kernel selection that ignores per-microbatch sequence length and KV cache hotness, and (3) attention kernels that fail to exploit small-headed token windows for fused attention paths. Goals: design and implement a scheduler that (A) steers microbatches across stages to create opportunistic NCCL windows (overlap comms with compute), (B) adaptively selects attention kernels per microbatch based on shape+KV footprint, and (C) staggers prefill->decode handoffs to avoid global blocking. Success metrics: reduce end-to-end decode p99 by 30% on mixed-length workloads, increase sustained throughput by 18% on 8xA100 baseline, and reduce observed GPU idle time during prefill spikes by 25%.
Design summary: (1) Rendezvous coordinator: lightweight cross-stage scheduler that tags mi
…[truncated]
```

#### #2 `dsid_b01446526c8b4549bbfcd4f9d00dc8a3`

```
SKU certification catalog and onboarding runbook for HW-specific performance

Create a canonical SKU Certification Catalog and an operational onboarding runbook that standardizes how models are validated and published per GPU family (A100/H100/L40S/MI300). The catalog will capture deterministic benchmark signatures, quantization sensitivity notes, cold/warm startup envelopes, and required artifact links. The runbook will be the prescriptive sequence for model engineers to follow when bringing a new model or variant into production, including gating thresholds for auto-pin, rollback criteria, and publishing steps for the public performance profile manifest.
A canonical SKU catalog (Confluence) exists and documents per-GPU baseline p50/p95 token latency, memory/KV footprint, and throughput for the representative sample suite
Runbook in docs repo with step-by-step checklist: calibration, microbench, full-sample regression, quant-sensitivity sweep, canary plan, and profile publication
Automation scripts (bench harness + signature generator) hooked to CI that produce a signed performance artifact for a model build
Gating thresholds defined: p95 latency regression <= 10% vs baseline OR a
…[truncated]
```

#### #3 `dsid_a9e031dea0724ffa9d2682a9d0d826ae`

```
Investigate dynamic kernel recompile thrash causing p95 latency spikes for mixed-quant workloads

During a capacity surge on 2026-03-09 we observed repeated p95 latency spikes for customers using mixed-precision/quantized model variants. The spikes correlated with short bursts of kernel JIT/variant recompilation and kernel cache churn. This ticket tracks investigation findings and post-incident action items to prevent future thrash when the scheduler probes or routes mixed-quant traffic.
Run a mixed workload with alternating requests: float16/FP32 model variants and int8 quantized variants with varying sequence lengths (16, 256, 1024).
Simulate scheduler probe window by sending small bursts from new connections that exercise different kernel code paths (attention fused vs unfused, tiled vs untiled).
Measure p95/p99 latency and check GPU-side logs for kernel compile events and CPU-side mutex contention metrics.
Verify kernel cache entries shrink/grow rapidly under load and observe allocator churn on the device-side.
Confirm that disabling the runtime's dynamic kernel recompiler or increasing kernel cache capacity eliminates the spikes in the synthetic test.
2026-03-09 14:03 UTC - Fi
…[truncated]
```

#### #4 `dsid_fb6a04eeac3a43d78bc2760430a5f28d`

```
Variant granularization, fallback ranking, and published profile matrix for GPU families

Summary: Create a reproducible process and published artifact set for hardware-specific performance profiles across A100/H100/L40S/MI300 that supports: (1) fine-grained variant granularization (memory/clock/driver bins), (2) explicit fallback ranking for runtime routing and graceful degradation, (3) signed profile publication and automated canary calibration. Goals: enable model onboarding to surface deterministic latency/cost expectations per GPU family, reduce live re-pinning incidents, and provide a machine-readable profile matrix consumed by the serving runtime and Console.
Authoritative profile JSON produced for each model+variant on A100/H100/L40S/MI300 with fields: sku, driver_hash, seq_length_buckets, p50/p95 generation latency (ms), tokens_per_sec, batch_efficiency, warm_cold_delta, memory_headroom_percent, quantization_compatibility_tags
Runtime can ingest profile JSON and compute fallback ordering for a given request within 50ms of decision time in unit tests
Canary calibration job that compares live p95 vs published p95 and marks profiles as STABLE/DEGRADED with thresholds (p95 inc
…[truncated]
```

#### #5 `dsid_35e80f9394cc48279e4c8a10ec6e1946`

```
eng-runtime

Ana: quick RFC follow-up — after landing the grouped-attn kernels I noticed CI artifacts are ~38% bigger on master. cc @Mike @Sophie
Mike: saw the CI bump. digging into the fatbin: looks like every TU pulled in PTX for multiple sm targets instead of linking a single cubin per arch.
Sophie: that would happen if we compile each kernel TU with the full -gencode list. LTO + -fuse-linker-plugin seems to stop dead-code removal in some cases too.
Jamal: I grabbed the build log, keybits: nvcc invoked with three gencode entries (sm_80, sm_86, sm_90) and we also run -flto at link. attaching snippet.
dl-bot: build #4721: link step: /usr/local/cuda/bin/nvcc -O3 -gencode arch=compute_80,code=sm_80 -gencode arch=compute_86,code=sm_86 -gencode arch=compute_90,code=sm_90 -Xlinker -plugin -flto ...
Ana: exact. That multiplies device code across TUs. Two quick proposals: 1) split kernel TUs so arch-specific compilation happens only once and ship per-arch static libs; 2) try relocatable device code + device link (-dc / -dlink) to let link-time dedupe. tradeoffs?
Mike: split-TU approach is simplest for CI matrix — we already build per-arch packages for Dedicated. downside: duplication of 
…[truncated]
```

#### #6 `dsid_62469a0762814236aae1cf861191a615`

```
Optimize CPU-GPU handshake and threadpool to reduce host overhead during prefill/decode

Goal: Reduce host-side CPU overhead and wall-clock latency from prefill->decode pipeline by minimizing memory copies, lowering threadpool contention, and aligning kernel selection with real workload slices.

Background: Production traces show 20-30% of per-request latency at low-to-medium batch sizes is spent on host work: staging prefill buffers, scheduling kernels, cudaMemcpy roundtrips, and lock contention in the global threadpool. This is most visible for short sequences and multi-tenant shared GPU pools where we repeatedly submit small prefill chunks and immediately follow with decode kernels.

Scope: Changes target three areas: (1) CPU-GPU handshake (async submissions and fewer sync points), (2) memory-copy reduction (zero-copy / pinned buffers / reuse), and (3) threadpool behavior (per-device / affinity / lock-free queues). Work includes microbenchmarks, runtime changes, integration tests, and dashboarding.

Proposed approach (high level):
- Kernel submission batching: merge prefill chunk submissions where safe (same model config and device) to reduce kernel-launch overhead. Add a small 
…[truncated]
```

#### #7 `dsid_515cfde3929d42efafcffe5c79c65b56`

```
SKU-aware wake scheduler for prefill/decode on H100, L40S, A10

Design and implement a SKU-aware 'wake scheduler' that coordinates prefill and decode workloads across H100, L40S and A10 devices (including MIG partitions). The scheduler combines a short-horizon burst predictor, a hardware capability vector, and a kernel scoring function to decide: 1) when to start prefill for a request to reduce p95 tail, 2) which kernel variant to pick (fused attention vs. sequence-sliced) given current clocks/MIGing, and 3) whether to pin workload to a specific MIG slice or fall back to cross-slice execution. Goal: reduce p95 latency for mixed synchronous workloads by 20–30% and reduce unnecessary clock ramping/burn for low-density request patterns.
1) Nightly benchmark shows >=15% p95 improvement for mixed length workloads on H100 and >=10% on L40S and A10 for the PL-and-PL+prefill scenarios; 2) No more than 5% regressed throughput for high-throughput batch workloads; 3) Telemetry surfaces SKU and MIG-level kernel choices per-request; 4) Feature gated and toggled via runtime-config; 5) Rollout plan documented with safe fallback to existing scheduler.
Core components:
- Burst predictor: lightweigh
…[truncated]
```

#### #8 `dsid_17d162cfdc254d71b08c73af1c923e86`

```
Runtime oncall scratchpad - Ishaan

Morning quick dump (03/13/2026) - ongoing oncall/logs and experiments

Context: woke up to elevated error rate on prod-east for long-seq customer (seq len ~ 8192). Alerts pointed at model-serving worker restarts + tail OOMs. Was able to repro locally with --seq-length=8192 + quantized-8bit profile.

Immediate triage notes:
- Symptom: sudden spike in `cudaHostAlloc` failures, worker restart loop for processes pinned to GPU-3. Thundering after GC-heavy requests.
- Impact: 3 dedicated shards (dedicated-cust-7) experienced ~7% request failure rate for ~20 minutes. Autoscale didn't kick because reserved capacity flagged as full.
- Initial mitigation: temporarily route customer to model-variant: llama-2-70b-fp16-fallback (higher mem but more stable). Reduced failures to <0.5%.

Repro steps I ran locally (put here so I don't forget):
1) checkout sha: 8f7c1c3 (branch: ish/kernel-trace-wip)
2) build with CUDA 12.2 + ROCm off
3) run repro script: tools/repro/oom_long_seq.sh --model-path ./models/llama-2-70b-q8 --gpu 0 --seq 8192 --batch 1
4) tail logs: logs/runtime.log | grep "cudaHostAlloc"

Observations from local repro:
- KV-cache allocation pattern: lo
…[truncated]
```

#### #9 `dsid_943113c0d3114ce89257a8f46f13e1c2`

```
Per-model kernel selection matrix and pin/publish workflow for MHA/GQA/MoE onboarding

Create a reproducible workflow and data model for publishing a per-model kernel selection matrix and pinned compilation profile for multi-headed attention (MHA), grouped-query attention (GQA) and mixture-of-experts (MoE) variants. This ticket covers: defining the matrix schema, integrating the kernel autotuner outputs, adding metadata to the model catalog, specifying pin semantics for model+kernel bundles, CI gating for deterministic builds, and publishing a performance profile page used by Console and Optimize to drive routing and rollouts.
Matrix schema defined and documented in Confluence with field-level semantics (model_family, model_version, kernel_bundle_id, compile_flags, hardware_tags, expected_latency_p50/p95, cost_per_token_estimate)
Autotuner output is consumed and mapped into the matrix for existing MHA/GQA/MoE onboarding runs (at least 6 models: bert-large-MHA, llama-2-gqa, llama-2-moe-experimental, redwood-mix-1, gpt-neox-gqa, custom-cust-moex)
Published kernel bundles are pinned in the model catalog and referenced by model_version metadata via stable kernel_bundle_id strings
CI jo
…[truncated]
```

#### #10 `dsid_466645b7fc644ed8b349b623d256fdea`

```
Lease-free atomic unpin: prefetch-safe aging for GPU KV cache

Problem: Continuous batching and aggressive prefetching improve throughput but complicate eviction correctness on GPU-resident KV caches. Existing approaches (pure LRU, TTL, prefix-aware trimming) rely on leases or heavy coordination to prevent races between prefetch, use, and eviction. Leases add allocation overhead and introduce tail latency when lease renewal contends with hot prefixes. Goal: design a lease-free, atomic unpin and aging protocol that preserves correctness invariants (no use-after-evict, prefix coherence, bounded staleness) while enabling aggressive prefetch and compact eviction to free GPU memory.
Introduce an optimistic atomic-unpin protocol combined with a two-phase aging window and small per-shard shadow queues. Key ideas: 1) Each cached prefix entry has a 1-bit live flag and an 8-bit epoch counter (wrap-aware). Prefetch sets live=1 and increments epoch locally. 2) Eviction proceeds in two phases: a soft-age pass (mark candidates and move to shard-local shadow queue) and a hard-evict pass where entries in the shadow queue are atomically tested against current epoch and live flag before actual recla
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 6: `qst_0016::basic` · N=40000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, indicating a lexical mismatch. The retrieved chunks are somewhat relevant but do not directly address the specific question about contractor access expiration policies. The hit flag is consistent with the ID membership check, but the retrieved documents do not match the expected document ID, leading to a label correction.

### Question

What is the company policy for how long contractor access should last by default before it expires, according to the access and permissions playbook?

### Gold document(s)

#### GOLD `dsid_ba7d1565b0694e359983bccaa4bf5977`

```
entitlements-and-purchase-pathways-playbook-2030

Overview
=======

Purpose: This playbook consolidates company-wide procedures for entitlements (access and permissions), change governance, data handling expectations, procurement and expense approvals, vendor lifecycle management, and travel approvals. It is intended for all Redwood employees and contractors who request or approve resources, commit changes to production, or manage third-party relationships.

Scope: Applies to hosted, dedicated, and private deployment teams, platform and infra teams, procurement interactions, people-ops travel arrangements, and any third party that will access Redwood systems or customer data.

Quick links: Access Portal (Okta + Access Request), VendorHub (procurement back-end), ExpenseFlow (employee expenses), Legal intake form, Security questionnaire (security.redwood.local).

Roles and responsibilities
--------------------------

- Requestor: person initiating an access, change, purchase, vendor relationship, or travel booking. Responsible for completeness and business justification.
- Manager/Approver: direct manager who validates business need and budget availability.
- Approving Officer (Finance/Procurement): validates procurement thresholds, tax, and vendor classification.
- Security Reviewer: evaluates data access risk and mandatory controls (SOC2, encryption, contract clauses).
- Legal Reviewer: reviews contract terms for vendor agreements above threshold or with custom IP/data terms.
- Proc Ops (Vendor Onboarding): completes supplier setup, obtains W-9/COI as applicable.

Principles
----------

- Least privilege: grant minimal entitlements required for the job and set automatic expiration where practical.
- Segregation of duties: approval and provisioning paths must not be owned by the same individual for medium/high risk requests.
- Evidence-first approvals: all approvals must be attached to the request in VendorHub or Access Portal.
- Risk proportionality: stricter controls for vendors with data access, privileged infra access, or requests above financial thresholds.

Access & permissions (entitlement lifecycle)
-------------------------------------------

1) Request 
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_11b4dc5c498c472b9827a245f5a0720e`

```
Equitable Onboarding and Role Access Playbook

Overview:\n\nThis playbook defines a standardized, equity-focused process for onboarding new hires and contractors, assigning role ladders, and granting access to internal tools and benefits at Redwood. It consolidates checklists, role-to-access mappings, escalation paths, and temporary-access policies so teams can deliver consistent experiences while minimizing security risk and administrative overhead.\n\nPrinciples:\n- Fast and predictable: new team members should have core access within 24 hours of start for standard hires and 72 hours for contractors requiring background checks.\n- Least privilege by default: grant the minimum access necessary for the role, with clear escalation paths for additional privileges.\n- Equity-first: ensure accommodations and benefit enrollments are automatic where possible and that managers are notified of outstanding tasks.\n- Auditability: every access grant and exception must have an owner, a justification, and an expiration.\n\nScope:\n- Applies to all full-time employees (FTE), part-time employees (PTE), and long-term contractors (>30 days).\n- Excludes short contractors (<30 days) who receive a r
…[truncated]
```

#### #2 `dsid_fdc9b77a90a5434d8c576afdcc0c8a72`

```
Onboarding Toolchain Access and Career Checkpoints

Overview:

This playbook documents the standard onboarding toolchain, the recommended access matrix by role, and the career progression checkpoints that People Ops and managers should use during the first 12 months. The goal is to reduce friction for new hires, make access predictable (time-to-provision target = 48 hours for core tools), and align early work with clear growth milestones.

Scope and audience:
- Scope: All full-time employees and long-term contractors at Redwood Inference. Includes hosted product teams and platform/infrastructure teams.
- Audience: Hiring managers, people-ops, IT/tooling engineers, team leads, and new hires.

Quick summary / SLAs:
- Standard provisioning SLA: 48 business hours for core tools (Okta, Slack, GitHub, GCP/Azure/AWS read access, Confluence).
- Elevated access (admin credentials, production secrets): additional approvals required; target: 5 business days.
- Escalation: people-ops on-call -> IT tooling group -> Security (if access requested to production secrets).

Access matrix (selected tools):
| Role | Okta Groups | GitHub | Slack | Cloud Console | Datadog | Vault | JIRA | Notes |
| Engi
…[truncated]
```

#### #3 `dsid_c1df83bebd3142bcbd2153c0d9a293b2`

```
Access, Change & Procurement Playbook — Compact Guide

  Purpose
  This compact playbook consolidates Redwood Inference company-wide policies and operational patterns for access & permissions, change management, data handling, procurement & expenses, vendor onboarding, travel expense handling, and the canonical templates teams should reuse. It is designed for day-to-day reference by engineering, product, security, people-ops, and finance teams. Use this as an operational checklist and a set of enforced thresholds; it links to detailed procedures where required.

  Scope
  - Applies to all full-time employees (FTEs), contractors, and vendors with company accounts or physical access.
  - Covers lifecycle from request -> approval -> provisioning -> review for access; request -> approval -> rollout -> post-change verification for changes; request -> approval -> purchase -> invoice for procurement; and vendor security/contract checks before onboarding.
  - Exceptions must follow the Risk & Exceptions workflow (security-and-compliance/risk-and-exceptions) and be timeboxed.

  Owners and escalation
  - Policy owner: Finance & Legal (owner_team)
  - Day-to-day steward: Security (access ope
…[truncated]
```

#### #4 `dsid_3bbea346f853491abd6e9615a41f1c77`

```
Access Provisioning and Spend Journeys (Company Playbook)

Overview

Purpose
This playbook centralizes company-wide routines for: access and permissions, change control, data handling, procurement and expense requests, vendor onboarding, and travel approvals. It is intended for requestors, approvers, finance, security, and operations teams.

Scope
Applies to all Redwood employees, contractors, and vendors that require systems access, make purchases on behalf of Redwood, or manage configuration changes to production or corporate systems. Exceptions must be approved by Finance + Security.

Principles (short)
- Least privilege: grant the minimum permissions required.
- Clear ownership: every access/expense/change has a named owner.
- Auditability: decisions and artifacts are retained for 3 years (longer for regulated customers).
- Separation of duties: requester ≠ approver for material spend and production changes.
- Risk-based controls: higher-risk assets require additional validation.

Roles & Responsibilities
- Requestor: submits request with business justification and expiry.
- Approver: validates business need and policy compliance.
- Provisioner: implements the access, change or
…[truncated]
```

#### #5 `dsid_84edaffcb234432fae7577eeabb7d893`

```
Role-based access, vendor onboarding, and spend workflows — Playbook

Overview

This playbook defines the end-to-end operational patterns that tie together: role-based access control (RBAC), change management for identity and permissions, data stewardship, procurement & expense approvals, vendor onboarding, and travel/expense templates. It is intended for requesters, managers, IT Security, Finance, Procurement, Data Stewards, and People Ops. The goal is predictable, auditable, and least-privilege-aligned decisions for any access, spend, or vendor request.

Scope

- Applies to all full-time employees, contractors, and third-party vendors who require systems access, vendor contracts, or reimbursable travel.
- Covers SSO groups, cloud account roles, privileged access, software procurement, vendor onboarding, and expense reimbursement.
- Does NOT replace product-specific onboarding docs; it defines the company-wide lifecycle and templates.

Key principles

1) Least privilege by default. Grant the minimum role necessary for 14 days for trial requests unless manager explicitly justifies longer duration.
2) Separation of duties. Approvals for spend and access must come from different appr
…[truncated]
```

#### #6 `dsid_96dfbf0c384a47a6b460adbd2b84dfbe`

```
Satellite Team Tool Access and Mentor Pairing Playbook

Overview

Purpose
This playbook defines the process, roles, SLAs, and artifacts required to onboard and support satellite teams, project rotations, and short-term contractors who require scoped access to Redwood systems. It pairs an access lifecycle with a mentor pairing program to accelerate impact while maintaining security and cost controls.

Scope
- Applies to any transient or temporary team event lasting between 2 days and 12 months: rotations, shadowing, pilot squads, contractor engagements, and hackweeks.
- Not intended for full-time hire onboarding (see new-hire orientation).
- Covers tool access (Okta, Redwood Console, GCP projects, Vault, Jira, GitHub org), mentor pairing, and deprovisioning.

Goals
- Reduce time-to-first-meaningful-commit for satellite contributors to under 2 business days for standard access and 4 hours for urgent business-critical cases.
- Ensure least-privilege with automated expiry and quarterly auditability.
- Provide explicit mentor ownership to reduce support load on platform teams.

Ownership and Roles
- Requestor: Team lead sponsoring the satellite access (manager or product owner). Respons
…[truncated]
```

#### #7 `dsid_6418143d8b5342cd80b308fdab0b726d`

```
Permissioning Journeys and Expense Approval Patterns

Overview:
This playbook defines end-to-end permissioning journeys (how employees and services receive, change, and relinquish access) and the expense-approval patterns that govern purchasing, travel reimbursements, and delegated procurement at Redwood Inference. The goal is to provide clear, auditable, and efficient processes that minimize risk while enabling velocity for product and business teams.

Scope:
- Applies to all Redwood employees, contractors, and third-party agents who require access to company systems or submit expenses and procurement requests.
- Covers five core domains: access & permissions, change management, data handling, procurement/expenses, and travel.
- Does not replace team-level runbooks for product services; it sets companywide guardrails and approval matrices.

Permissioning journeys (high level):
1) New hire / contractor onboarding:
   - Trigger: HR creates an onboard record and issues role template in HRIS.
   - Action: People Ops triggers access provisioning workflow in Identity System (IDP).
   - Approval: Role-based templates auto-approve standard tool access. Any deviation requires manager + sec
…[truncated]
```

#### #8 `dsid_a5646b96187c4c6db01319035f56dc3d`

```
Company Access, Change, and Supplier Playbook

Overview

This playbook consolidates company-wide policies and standard procedures for access and permissions, change management, data handling, procurement and expenses, vendor lifecycle management, travel policy, and the canonical internal templates used by cross-functional teams. It is intended as the single operational reference for requesters, approvers, and operational teams.

Scope

- Applies to all Redwood employees, contractors, and contingent workers.
- Covers corporate systems (G Suite, Okta, Redwood Console), infrastructure systems (redwood-iam, cluster-admin, provisioner), procurement and expense approvals, vendor onboarding and offboarding, and employee travel booked on company funds.
- Does NOT replace team-specific technical runbooks; it complements them by defining approval flows, classification, and control gates.

Roles and Responsibilities

- Requester: initiates access/change/procurement/travel requests and provides justification and cost estimates.
- Approver: designated person(s) in the approval matrix (see table) who validate business need, least-privilege fit, and budget.
- Security Owner: reviews data classifi
…[truncated]
```

#### #9 `dsid_d9671df790c14a618908e8a054276d55`

```
Authorization Lifecycle and Procurement Patterns Playbook

Overview

This playbook consolidates company-wide patterns for authorization lifecycles, change approvals, data handling during procurement, vendor relationship checkpoints, and travel allowances. It is intended for managers, approvers, finance partners, security reviewers, and people-ops staff who operate or approve access, purchases, and vendor onboarding.

Scope

- Applies to all employees, contractors, and vendors interacting with Redwood systems or purchasing on behalf of the company.
- Covers: access requests and deprovisioning, change-management approvals for infrastructure and service procurement, data classification applied to vendor contracts, expense and travel allowances, and operational templates used by approvers.

Definitions

- Authorization lifecycle: request → approval → provisioning → periodic review → deprovisioning.
- Owner: the functional manager who is accountable for a role or resource.
- Approver: the person empowered to grant access or spend (could be manager, director, finance, or security).
- Sensitive data: any data marked Confidential or Restricted under Data Management policy.

1) Access & Per
…[truncated]
```

#### #10 `dsid_2bb2dc1bbe734759964baadd3d166db3`

```
Onboarding Security Handoff for Customer‑Facing Hires

A focused playbook that defines a repeatable security and data‑readiness handoff for new hires whose role requires early access to customer data, accounts, or PII. Includes timeline, owner matrix, access checklists, training requirements, and audit evidence templates.
Purpose:
This document defines the required steps and owner responsibilities for onboarding customer‑facing hires (Support, CSM, Solutions, Sales Eng, Account Teams, and early-product pilots) who require access to production customer data, accounts, or other restricted resources during their first 30 days. The goal is to reduce risk while enabling a fast time to impact through a clear, auditable security handoff.

Scope and applicability:
- Applies to any role that requires read or write access to customer PII, production databases, live logs, or customer tenant environments within the first 30 days.
- Exclusions: strictly marketing-only hires, contractors with strictly non‑prod access (see contractor onboarding policy).

Why this exists:
- Customer‑facing roles often need access early to do demos, troubleshooting, or account work. Uncoordinated access creates sec
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 7: `qst_0024::metadata` · N=15000 · raw · priority=high

- **auto Hit@10:** `True`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs include the expected document ID, confirming Hit@10=True. However, the content of the gold and retrieved chunks is unrelated to the question about expiring guest or contractor accounts, indicating a lexical mismatch. The chunks are non-empty but off-topic, leading to low relevance and chunk quality scores.

### Question

In the eng-sre space, which internal published runbook by Rishi Malhotra covers verification steps to follow after rotating production credentials?

### Gold document(s)

#### GOLD `dsid_74ebb73359364bc791707a92a3227e3a`

```
Post-rotation verification checklist (production credentials)

# Purpose
This checklist defines the required verification steps after rotating production secrets to ensure all consumers have updated and service health is stable.

# Checklist (execute in order)
## 1) Confirm consumer rollout completion
- Verify all services that consume the rotated secret have been restarted/redeployed if required.
- For services that hot-reload, confirm at least one reload interval has passed.
- Confirm there are no straggler instances on old revisions.

## 2) Monitor auth and dependency metrics
Watch for 30 minutes minimum (60 minutes for Tier 0):
- 401/403 rates for service-to-service calls
- database authentication failures
- third-party provider invalid key errors
- sudden increases in retry rate

## 3) Validate critical user journeys
Run canary requests against:
- Hosted API chat completion (streaming and non-streaming)
- embeddings endpoint
- console login (if SSO secrets rotated)
- model registry artifact fetch

## 4) Audit checks
- Confirm audit logs show only expected actors accessed the secret during rotation window.
- Confirm break-glass access (if used) has been revoked.

## 5) Decommission old credential
If using a dual-valid window:
- disable the old credential at the issuer
- confirm no consumer is still using it (errors should not spike)
- remove old secret version from Vault after the defined window

# Exit criteria
Rotation is considered complete when:
- all consumers are updated
- error rates are at baseline
- no unexplained auth failures occur for the observation window
- old credential is disabled or scheduled for disablement

# What to do if problems occur
- Identify the failing dependency (which service, which endpoint, which credential).
- Check the dependency inventory for missing consumers.
- If customer impact is increasing, revert or temporarily re-enable the old credential where possible and then retry rotation with tighter coordination.
```

### Retrieved top-10

#### #1 `dsid_74ebb73359364bc791707a92a3227e3a` **← GOLD ID**

```
Post-rotation verification checklist (production credentials)

# Purpose
This checklist defines the required verification steps after rotating production secrets to ensure all consumers have updated and service health is stable.

# Checklist (execute in order)
## 1) Confirm consumer rollout completion
- Verify all services that consume the rotated secret have been restarted/redeployed if required.
- For services that hot-reload, confirm at least one reload interval has passed.
- Confirm there are no straggler instances on old revisions.

## 2) Monitor auth and dependency metrics
Watch for 30 minutes minimum (60 minutes for Tier 0):
- 401/403 rates for service-to-service calls
- database authentication failures
- third-party provider invalid key errors
- sudden increases in retry rate

## 3) Validate critical user journeys
Run canary requests against:
- Hosted API chat completion (streaming and non-streaming)
- embeddings endpoint
- console login (if SSO secrets rotated)
- model registry artifact fetch

## 4) Audit checks
- Confirm audit logs show only expected actors accessed the secret during rotation window.
- Confirm break-glass access (if used) has been revoked.

## 5) Decommis
…[truncated]
```

#### #2 `dsid_cf06e75be4f94156ac338f62e3ee028b`

```
Production secret rotation runbook

# Purpose
This runbook provides a repeatable procedure for rotating production secrets used by Redwood services. It covers both planned and emergency rotation patterns.

# Preconditions
- Identify the secret name/path and all consumers (see Credential Dependencies page).
- Confirm rotation type: planned vs emergency.
- Ensure appropriate access (normal approvals or break-glass for emergencies).

# Rotation patterns
## Pattern A: Dual-valid window (preferred)
Use when the downstream system can accept two credentials temporarily (e.g., JWT verification keys, API keys with overlap).

Steps:
1. Generate new credential.
2. Store new credential in Vault under a new version (do not delete old).
3. Update consumers to read the latest version and accept both old+new if applicable.
4. Deploy changes.
5. Observe auth success metrics for at least 30 minutes.
6. Disable old credential at the issuer (or mark old as deprecated).
7. Remove old credential from Vault after the deprecation window (default 7 days unless otherwise specified).

## Pattern B: Cutover (use with caution)
Use when only one credential can be active (e.g., some database passwords).

Steps:

…[truncated]
```

#### #3 `dsid_93cf47bd2c3944ff92569797f07ea724`

```
oncall-rotation-onboarding-and-slo-ownership-runbook-2024

Overview:
This runbook describes the standard onboarding flow for engineers joining the SRE on-call rotation and the concrete handoff for SLO ownership and error-budget stewardship. It is written for new rotation members, rotation leads, and managers who need a repeatable checklist to verify readiness to carry SLO responsibilities in production.

Purpose:
- Ensure consistent knowledge transfer for SREs joining or re-joining rotation.
- Reduce time-to-first-independent-incident-handling while protecting customer-facing SLOs.
- Establish a clear sign-off process for SLO ownership and capacity remediation privileges.

Scope:
Applies to: core inference platform services (api-gateway, runtime-router, kv-cache, model-host-pool) and SREs who will be primary or secondary on-call. Does NOT replace service-specific runbooks — those remain authoritative for service-level troubleshooting.

Definitions:
- SLO owner: rotation engineer accountable for monitoring, first-response and initiating mitigation for a target SLO.
- Error budget: rolling 30-day percentage (or per-SLO window) of allowable user-impacting failures.

Before you start (
…[truncated]
```

#### #4 `dsid_c790406c34ce484b8d00a19dbeb476a6`

```
Quarterly Private/VPC Ops Readiness & Governance Playbook

Goal: produce a single, executable playbook that operationalizes quarterly readiness for Private/VPC/On‑Prem customer rollouts. The playbook will align product, SRE, sales engineering, and customer success on gating criteria, governance checkpoints, rollback windows, and runbook templates so that enterprise customers can be onboarded or upgraded within a predictable SLA window. Scope includes: deployment pre-checklist, access/KMS verification, compatibility matrix for supported models and kernels, SLO validation procedures, canary & rollback criteria, compliance signoffs (SOC2/GDPR), and post-rollout telemetry and billing reconciliation steps. Out of scope: changes to underlying runtime code and deep infra provisioning automation—those will be tracked under engineering epics. Success criteria: repeatable onboarding that meets the defined SLOs and reduces manual steps by at least 40% compared to baseline pilots.
Written playbook doc with step-by-step runbooks for canary, full rollout, and rollback
Checklist templates for SE/CS handoff including KMS and network validation
Two pilot rollouts (internal or partner) executed with
…[truncated]
```

#### #5 `dsid_2fb1fa3db2234ae7aec1d8195f016829`

```
ingress-gateway-client-cert-rotation-and-ssl-ops-playbook-2026

Overview

This playbook describes the safe, auditable process for rotating TLS certificates and client (mutual TLS) certificates used by enterprise ingress gateways during onboarding and later maintenance windows. It covers hosted/Dedicated/Private deployment patterns, impacts to customers, verification steps, rollback guidance, monitoring queries, and automation snippets. Intended readers: Customer Success engineers, SREs, Onboarding engineers, and Enterprise security contacts.

Scope and intent

- Scope: ingress gateways (edge load balancers, ingress-controller layer, API gateway proxies) and their associated client certs used for tenant mTLS or upstream service authentication.
- Intent: minimize customer downtime and avoid failed requests during cert rotation while preserving auditability for regulated customers.

When to use this playbook

1. Scheduled certificate rotation (regular maintenance cycle).
2. Emergency rotation because of suspected key compromise.
3. Changing CA (e.g., moving from customer-supplied certs to managed PKI or vice versa).

Roles & ownership

- Owner: Customer Success (Onboarding pillar) — p
…[truncated]
```

#### #6 `dsid_7a9d6810cee2497f93113afa7feb0076`

```
Enterprise Onboarding — Post-Provisioning Stability & Fallback Checklist

Overview
This playbook defines the post-provisioning stability and fallback verification steps we run for enterprise customers after Dedicated or Private (VPC / on-prem) environments are provisioned and before handing back to Product/Engineering for live traffic. The goal is to validate functional correctness, confirm SLOs and capacity assumptions, exercise fallback and routing policies, and confirm monitoring/alerting is wired end-to-end. This document is intended for Customer Success Engineers (CSEs), Solutions Engineers, and the Redwood SRE/Platform teams.

Key objectives
- Verify baseline latency and throughput for representative workloads.
- Confirm automatic fallback paths and model variant switchover behave as expected.
- Validate KV/prefix cache priming and persistence (where applicable).
- Ensure observability: dashboards, tracing, and alerting triggerable and readable by customer ops.
- Document owners, rollback criteria, and escalation steps.

When to run
- Immediately after dedicated/private environment provisioning completes and the control plane shows "provisioned" state.
- After canary deploys 
…[truncated]
```

#### #7 `dsid_546e110c14144ff9a1a02d9145c43177`

```
Rotations and Break-Glass Cheatsheet

Purpose:\nThis is a compact operational cheat sheet for secrets vaulting, rotation, break-glass handling, and the evidence automation pipeline that proves rotations happened. Meant for on-call security, SREs, and devs who own credentials. Keep this page as the quick reference; longer runbooks live on Confluence (see linked artifacts).\n\nScope:\n- Applies to all service credentials stored in HashiCorp Vault (kv-v2 and transit) and KMS-managed keys used for signing.\n- Covers rotation cadence, automated proof collection (evidence artifacts), SIEM export fields, and emergency break-glass flows.\n- Excludes user-facing password resets (handled by IAM/IDP team).\n\nHigh-level flow (typical rotation):\n1) Rotation trigger: scheduled job (cron on infra repo) or manual request (SEC JIRA ticket).\n2) Pre-checks: confirm consumer services have pull-ready deploy windows and feature flags for canary rollout.\n3) Perform rotation in Vault (kv write / kv/… or transit rotate).\n4) Update dependents (k8s secrets, config stores) via controlled rollout.\n5) Post-checks: smoke requests, metric validation, audit event collection pushed to SIEM.\n6) Emit evidence 
…[truncated]
```

#### #8 `dsid_8270b31acc864a05abc0d5196281feca`

```
RBAC Policy Rewind & SIEM Validation — On-Call Runbook

Purpose and scope:\nThis runbook describes fast, repeatable steps for an on-call security engineer to: detect RBAC policy drift or unintended privilege changes, capture tamper-evident evidence (audit logs + snapshot), validate SIEM export integrity, and perform a policy rollback (policy-rewind) with minimal blast radius. It assumes RBAC v2 is in use and audit logs emit the canonical schema (see Audit schema summary).\n\nWhen to use this runbook (triggers):\n- Alert from RBAC-drift detector: sudden spike in 'allow' decisions for previously-denied operations.\n- User or service account granted a high-privilege role unexpectedly.\n- Detection from anomaly model (e.g., new principal performing cross-account operations).\n- Direct report from infra team: "we pushed a policy change and observed access escalation".\n\nHigh-level goals (SLOs during incident):\n- Evidence snapshot created within 10 minutes of triage start.\n- SIEM export validation complete within 20 minutes.\n- Policy rollback validated within 30–45 minutes.\n- Communication to incident channel within 5 minutes.\n\nImmediate actions (first 0–10 minutes):\n1) Create in
…[truncated]
```

#### #9 `dsid_190d9732b59b411d8a6bcc59fd61b309`

```
Runbook: Rollback and Post-change Validation (Hosted API + Console)

h1. Purpose
This runbook defines the required steps to rollback a production change and the required post-change validation steps (including after a rollback). It applies to Hosted API and Console.

h1. Guiding principles
* Prefer fast rollback over extended debugging when customer impact is ongoing.
* Rollback should return the system to a known-good state with minimal risk.
* Always leave a trace: update the change record and incident timeline.

h1. Preconditions
* Identify the last known-good build (image digest or build number).
* Identify what changed: code deploy, config/policy bundle, schema migration, feature flags.

h1. Rollback decision criteria
Rollback immediately if:
* Canary or post-deploy gates fail (error/latency regression beyond thresholds)
* New Sev2+ customer impact appears plausibly correlated
* Data correctness, billing, auth, or routing correctness is in question

h1. Rollback steps (generic)
1. Stop further rollout
   * Pause deployments and disable automated promotions.
2. Revert highest-leverage toggles first
   * Disable or revert feature flags / routing policy bundles associated with th
…[truncated]
```

#### #10 `dsid_8c92178c254d467c9854db67aac7c9be`

```
Secret management standard (production)

# Overview
This standard defines how Redwood Inference stores, uses, and rotates **secrets and credentials** for production services. The objective is to reduce the blast radius of credential compromise and ensure rotation is routine and low-risk.

# Definitions
- **Secret**: any value that grants access (API keys, database passwords, service tokens, signing keys, OAuth client secrets, private keys).
- **Credential rotation**: replacing a secret with a new value and updating all consumers.
- **Emergency rotation**: accelerated rotation performed due to suspected compromise or active incident.

# Approved storage systems
Production secrets must be stored in one of the following:
- Redwood Vault (primary)
- Cloud KMS/HSM-backed secret store where required by compliance (Private deployments may vary)

Prohibited:
- plaintext in Git repositories
- plaintext in Confluence/Google Docs
- long-lived secrets in CI logs
- hard-coded values in container images

# Secret classification
- **Tier 0**: root/admin credentials, signing keys, KMS master operations.
- **Tier 1**: service-to-service auth tokens, database credentials, message bus credentials.
- 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 8: `qst_0025::metadata` · N=75000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The retrieved document IDs do not include the expected document ID, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant to the topic of latency and streaming issues but do not directly address the specific question about latency thresholds and escalation criteria. The failure mode is likely an embedding near miss due to the thematic similarity but lack of specific content match. The hit flag inconsistency is a critical issue.

### Question

In the customer-support bug about synchronized retry backoff causing streaming reconnect storms, what production environment is listed for the incident?

### Gold document(s)

#### GOLD `dsid_4a2ce3e1be4d4f00a089ccc00ac92b8c`

```
Synchronized client retry window causing burst reconnections and high tail latency for streaming requests

Issue summary:
Customer reports a sudden increase in end-to-end inference latency and frequent streaming disconnects for long responses starting 2026-03-10T17:00Z. Symptoms are most pronounced for streaming chat sessions; non-streamed short responses show minor impact.

Impact:
- ~15% of customer streaming requests hit >5s tail latency, up from baseline ~200ms.
- Customer-visible streaming stalls and reconnects causing bad UX for real-time transcription product.
- Impacts 2 of the customer's Dedicated GPU pools in us-east.

Environment:
- Customer using Redwood SDK v2.4.1 (node) with default retry/backoff config.
- Dedicated cluster: dedicated-prod-us-east-2 (rwid-13b-v2 pinned).

Initial hypothesis:
Client SDKs with near-identical backoff defaults lost jitter (observed after SDK minor rollout) and therefore retried in lockstep when transient 429/503 responses occurred, causing a spike of simultaneous new connections and requests that overloaded NAT/proxy and produced head-of-line queuing at the API gateway. This produced apparent latency regressions and streaming stalls rather than a sustained higher error rate.

Additional context:
- Customer has a large fleet of ephemeral workers (autoscaling pods) that cycle frequently; many workers had identical SDK config and similar clock drift due to container start patterns during a deployment window.
- No scheduled Redwood platform maintenance at the time; our metrics show a short spike in 5xx/429 from 17:11–17:20Z concurrent with retry surge.

1) Deploy a fleet of clients using SDK v2.4.1 with default backoff settings.
2) Induce transient 429 responses by throttling a backend model pool (short circuit or simulate reduced capacity).
3) Observe client retry attempts aligning within a narrow window (few hundred ms) and resulting in a large simultaneous connection attempt count to the API gateway.
4) Observe streaming sessions stall or disconnect as server begins queueing and timing out.

- API gateway NewRelic: spike in connection attempts and 503s 2026-03-10T17:11:34Z -> 17:19:58Z.
- Support trace id sample: trace-
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_8401a32f4d644ecab18ee24ad6149873`

```
Customer reports streaming disconnects + elevated 5xx (Hosted API us-east)

Issue summary: Customer reports intermittent streaming disconnects and timeouts starting ~16:05 UTC.

Impact: Some Hosted API streaming requests disconnect mid-stream; customer sees retries and elevated error rates.

Environment: prod us-east.

Initial signals: Support sees related tickets and #incidents thread references spike in runtime restarts.

Comments:
- Camila Reyes (Support): Opened P0; linking #incidents and requesting IC assignment.
- Grace O'Connor (SRE/IC): Incident declared INC-2025-07-18-02. Mitigation: disable experimental scheduler feature flag; canary in us-east.
- Ethan Park (Release Eng): Deployed config flip canary-first; metrics improved; expanded to full us-east.
- Hiro Tanaka (Runtime): Prepared hotfix PR 28417 to auto-disable experimental scheduler at high stream concurrency; queued for rollout after stability window.

Resolution: Config mitigation reduced disconnect rate; hotfix merged for safer gating; no further customer reports after stabilization.

Follow-ups: Add regression test for high stream concurrency path; ensure guardrails enforce canary hold time during error budget bu
…[truncated]
```

#### #2 `dsid_23ad614501964d5a98fd576afcffa23b`

```
Intermittent evening 5xx surge from streaming fanout + keepalive mismatch causing upstream worker preemptions

Issue summary:
- Customer BlueArc reports elevated 5xx rate (502/503) on streaming routes during evening business hours. Errors began ~2026-03-13 18:05 UTC and show repeated short spikes (1–3 minutes) with increased tail-latency for streaming sessions.

Impact:
- Multiple long-lived streaming client sessions observed disconnecting and failing to resume. Customer reports degraded UX for interactive analytics feature; estimated 12% of streaming calls in the hour experienced errors.

Timeline / Observed pattern:
- 2026-03-13 18:02 UTC: first error cluster; apigw error rate to this tenant increased to 5xx ~18%.
- 18:05–18:12 UTC: short oscillations of 5xx with concurrent rise in upstream preempt events and runtime worker restarts.
- 18:20 UTC: transient decrease, then another cluster at 19:10 UTC with similar pattern.

Environment:
- Dedicated pool serving BlueArc (tenant id: ta-9043) in us-east-1, running model variants redwood/gptx-7b and redwood/gptx-13b-int8.
- Streaming route: /v1/stream/chat (http2). TLS termination at edge, keepalive proxied through streaming-proxy.

St
…[truncated]
```

#### #3 `dsid_70124860f38d4604981c3c41c45308ce`

```
Streaming responses reset mid-generation in prod us-east (Acme AI) — connection resets / truncated streams

Issue summary
- Customer (Acme AI) reports streaming responses intermittently resetting mid-generation in prod us-east.
- Symptoms: SSE stream terminates unexpectedly (client sees ECONNRESET / "stream ended" / truncated output). Non-streaming requests complete successfully.

Customer impact
- Tier: Enterprise. Customer reports elevated error rate for streaming usage (~2–5% of streaming requests) and increased customer-visible failures in their app.
- Impact window: observed since 2026-02-03 16:50Z.
- Scope: prod us-east only per customer (eu-west appears stable).

Environment
- API: /v1/chat/completions with stream=true (SSE)
- Customer SDK: redwood-sdk-python 0.9.2 (also reproduced via curl)
- Regions tested: us-east (failures), eu-west (no failures reported)
- Models: redwood-chat-large-v3, redwood-chat-medium-v3

Steps to reproduce (customer-provided)
1) Run a streaming chat completion with long-ish generations (customer reports failures more common > ~60s wall time).
2) Observe that the stream ends early (no final "[DONE]" / missing end-of-stream event).

Example request 
…[truncated]
```

#### #4 `dsid_146aa71c437f4d37bf5c91b8d176d180`

```
Interleaved streaming fallback and tenant priority reshuffle triggered elevated 5xx error rate

Issue summary: Starting 2026-03-12 09:10 UTC we observed a sudden, sustained rise in 5xx responses for a single dedicated-tenant (BrightDocs) originating from streaming endpoints and elevated retry traffic from the API gateway. Impact: Customer-facing streaming sessions saw ~20-30% failure rate (502/503) for 45 minutes; non-streaming requests experienced increased latency and occasional 504s. Environment: prod | us-east | dedicated pool brd-east-1.

Observed behavior appears correlated with a tenant priority weight change (internal autoscaler action) followed by streaming failovers that caused the runtime to enter a cyclical fallback and connection churn loop. This amplified retries at the API gateway and led to upstream runtime process restarts under memory pressure.

Steps to reproduce (investigation runbook):
1) On a dedicated tenant with mixed streaming & short-polling traffic, change route weight to shift 30% of traffic to a lower-cost replica pool.
2) Initiate a sustained mix of long-lived streaming sessions (20 concurrent, ~1-2 tokens/sec) and bursts of short generation requests.

…[truncated]
```

#### #5 `dsid_a5bea569752c420a9b198ebd56289baa`

```
Edge proxy retry loop causes SSE stream freeze during long chat sessions

Issue summary: Customer reports repeated streaming chat sessions (SSE) that begin normally but freeze mid-generation after ~30-120s. The client observes no final event and connection remains open; eventually client-side times out. This appears correlated with bursts of 502/504 responses from an edge proxy in front of Redwood’s API and aggressive automatic retries by that proxy.

Impact: Several paid customers on Dedicated capacity experienced degraded UX for long multi-turn chats. Affected customers reported multiple sessions where partial output is delivered then stalls; some sessions recovered after forcing a client reconnect, others required server-side fix. No data exfiltration suspected.

Why this ticket: Customer asked for root cause, mitigation, and permanent fix. Ticket captures investigation and resolution plan.
Partial streaming output for long chats, client-visible stalls, increased support load. Customer reported ~12 impacted sessions across two accounts in the last 48h.
prod | dedicated | us-east (edge-proxy-3) and eu-west (edge-proxy-7)
1) Use a dedicated customer account with reserved capacity 
…[truncated]
```

#### #6 `dsid_4ff51390e491448f95348062bc239d1c`

```
Intermittent streaming disconnect / stops mid-stream across multiple client networks (NexLayer)

Customer reports that some streaming requests 'stop mid-stream' and they end up with partial outputs. They are seeing it from a few different ISPs and can reproduce from two office networks.

Symptoms described:
- Sometimes the stream ends early (client receives [DONE] sooner than expected)
- Sometimes the stream appears to stall and then the client disconnects

Asks:
- confirm whether this is related to known SSE stalling behavior (keepalive / flushing)
- guidance for client retry/backoff

Customer provided request_ids (redacted):
- req_aa01...
- req_aa07...

No formal incident declared.
Rishi Malhotra (2026-03-12): Logged after customer chat. They used the term 'stops mid-stream' and 'ends early'.
Connor O'Brien (2026-03-12): Might be same class as the stall reports. Need to check if keepalive enabled in us-west. Also verify client is not mishandling HTTP/2 resets.
Rishi Malhotra (2026-03-13): Asked customer for raw headers + whether they see HTTP/2 GOAWAY/RST. Waiting on reply.
```

#### #7 `dsid_ba8530d59b1448218b4c54abcd266a31`

```
Streaming session stalls mid-generation after transient latency spike (mobile carrier)

Issue summary: Customer reports streaming chat sessions (SSE) stall mid-generation after ~15-40s, client receives no more chunks but TCP connection remains ESTABLISHED. Impact: Several customers on dedicated cluster observed partial outputs and manual reconnects, user-facing UIs show hanging 'typing' indicator. Environment: Dedicated capacity for OptiCart in prod-us-west running our streaming API via HTTP/1.1 SSE proxy. Steps to reproduce: 1) Customer sends multi-turn prompt causing long generation (~600 tokens). 2) Stream starts and emits tokens for ~15-40s. 3) Stream stops emitting further data while connection stays open; no final event. 4) Client reconnects and requests fallback but receives duplicate tokens or must restart generation. Logs: See attached snippets and trace ids below. Additional context: Incident coincided with mobile carrier RTT spike reported by customer; customer is primarily mobile web users. This started after rolling proxy tuning change (kernel TCP offload flags and proxy buffering) deployed 2026-03-09.
Affects interactive chat UX for OptiCart mobile users; estimated ~1
…[truncated]
```

#### #8 `dsid_d4319ac5979642dfb0612c4f35cd4668`

```
SundialHealth: partial conversation fragmentation, duplicate followups and rollback action plan

Issue summary:
- On 2025-11-12 09:03 UTC SundialHealth began seeing partial conversation responses: first chunk delivered, subsequent chunks truncated or duplicated across parallel streams. Some sessions produced duplicate follow-ups (same assistant message sent twice) and others showed missing closing tokens causing downstream truncation in customer UI.

Impact:
- Affected ~4% of requests from SundialHealth between 09:03 and 10:24 UTC.
- High business impact: clinical note-generation workflows failed reconciliation checks; SundialHealth reported patient-facing delays and raised an executive escalation.

Environment:
- Production (us-west). Requests routed to Dedicated pool (dedicated-gpu-pool-12). Models: redwood-open-34b-v1 (primary), redwood-open-8b-quantized (fallback).

Steps to reproduce (internal):
1) Replay customer session trace ID sundial:20251112:09:17:34 with streaming=true, chunk_size=4096.
2) Observe first event with tokens stream, then duplicate chunk with identical token ids on second websocket connection.
3) Repeat under high concurrency (~250 rps) to reproduce amplific
…[truncated]
```

#### #9 `dsid_faec551805a649d69c8ce0849c05c907`

```
Concurrent streaming requests trigger cascading 5xx amplification due to throttle/starvation

Issue summary:
Customer (NovaDocs Inc.) reported a sharp increase in 5xx errors observed from streaming endpoints during a morning processing window. Errors began at ~09:12 UTC and continued in waves correlated with spikes of concurrent long-lived streaming sessions.

Impact:
- Customer streaming sessions experience dropped responses (5xx) and reconnect loops for ~12 minutes.
- Production latency increased for other tenants in same us-east pool by ~150ms.
- Customer reported degraded UX: failed transcripts and duplicate partial outputs.

Observed behavior:
- API Gateway returned 502/503 on ~18% of streaming handshake attempts during the window.
- Downstream serving-runtime processes showed fast crash/restart cycles (OOM-adjacent) and elevated KV cache eviction rates.

Context and recent changes:
- No customer-driven model rollouts in the 24h preceding the incident.
- Autoscaler pushed up replicas before the spike but observed thrashing afterwards.
- We had a scheduler change deployed to prod 48h prior that adjusted priority scheduling thresholds for streaming paths.

1) Customer opens ~120
…[truncated]
```

#### #10 `dsid_9cfd5e3dc9e341b58bb1fbd1bcc79b33`

```
Elevated 5xx wave during long-lived streaming sessions due to proxy retry spin

Issue summary:
Customers (notably NovaDocs) reported a sudden spike in 5xx responses beginning ~2026-03-13T22:10 PDT affecting long-lived streaming sessions. Errors are primarily 502/503 observed at the API gateway with upstream runtimes reporting transient disconnects. Impact: multiple customers on Dedicated pools experienced degraded streaming reliability; some sessions aborted mid-stream causing client-visible failures and retries.

Impact:
- 5xx rate rose from baseline ~0.2% to peak ~7.8% for streaming endpoints between 22:10 and 23:15 PDT.
- Several enterprise customers reported high error counts and restart loops in their client telemetry.
- Affected features: streaming chat, function-calling streaming, and long-poll embedding streams.

Environment:
- prod - us-west (dedicated pools).
- Affected node types: proxy frontends and streaming runtime pods on gpu-pool-12.
- Autoscaler: enabled with warmup; dedicated capacity pinned for customers.

Steps to reproduce (as observed by customer):
1) Open a streaming session with a request that uses streaming+tool-calls and keeps a long-lived connection (~>3 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 9: `qst_0036::basic` · N=20000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are related to streaming issues but do not specifically address telemetry events and alert thresholds for monitoring degraded outputs as described in the gold chunk. This indicates a lexical mismatch between the query and retrieved documents. The gold chunk is relevant and non-empty, while the retrieved chunks are somewhat relevant but not directly on-topic.

### Question

What telemetry events and alert threshold are required to monitor streaming responses when a downstream tool call fails but the system continues with degraded output?

### Gold document(s)

#### GOLD `dsid_f94b93a4bc7948ddab45c371187dc6c6`

```
Emission Stability and Tool-Orchestration: Soft-Fail & Streaming Acceptance

PRD-style acceptance and behavioral specification for: (A) deterministic structured output envelopes during streaming, (B) robust tool/function-orchestration semantics when downstream tool calls fail or time out (soft-fail modes), and (C) observable signal set for debugging degraded emissions. This ticket captures requirements, tradeoffs, and concrete acceptance tests for engineering to implement and QA to validate.
Teams integrating function-calls and streaming structured output have encountered brittle failure modes: partial JSON emissions, stuck streams when a tool times out, and unclear signals in telemetry for root-cause. Previous specs focused on schema handshakes but did not fully specify soft-fail policies (when to continue vs abort), how to surface partial-but-valid objects, or required observability for production troubleshooting.
1) Define deterministic envelope semantics so consumers can parse incrementally and resume/reconcile partial objects. 2) Specify soft-fail modes for tool invocation: best-effort, fallback-only, and abort. 3) Establish acceptance tests for streaming + tool failures that exercise backpressure, resumability, and idempotent retries. 4) Define telemetry and SLI/alert thresholds to detect degraded emission reliability.
- Streaming text and structured frames emitted from Redwood API. - Function/tool invocation lifecycle (invoke, success, failure, retry). - Soft-fail policies and configuration. - Acceptance criteria and end-to-end test matrix (simulated tool latencies/failures).
- Changes to client SDKs beyond minimal parsing guidance. - New RPC transport protocols. - Billing/quotas changes related to retries (handled by a separate billing review).
- Strict abort-on-tool-failure yields highest data correctness but reduces availability; soft-fail increases availability at the cost of accuracy. We recommend defaulting to best-effort-with-degraded-indicators for hosted API and offering strict-abort configuration for enterprise Dedicated/Private deployments. - Emitting placeholder fields vs removing the field: placeholder maintains schema shape for parsers but m
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_acb6ff8b0afc4f7ba9ef45714f50fa86`

```
Keepalive ping storm — playbook draft

Between 2029-06-14T00:22 and 2029-06-14T01:05 UTC we experienced a significant degradation of hosted API streaming and short-generation latencies caused by an influx of client keepalive pings from a misbehaving SDK cohort. Symptoms included p95/p99 latency increases, a burst of 502/504s at the edge, and an elevated rate of streaming fragment reassembly failures. The burst affected ~18% of streaming sessions in US-west and produced service errors for several high-traffic customers.
~18% of active streaming sessions experienced mid-request disconnects or fragmented responses; non-streaming short generations saw p95 latency increase from 120ms to 550ms for ~10 minutes. No data loss was detected in user payloads. Several customers reported degraded UX; a small set triggered automated retries that amplified load on acceptor queues.
Alert: ephemeral-acceptor-queue-depth > 80% for multiple edge pods (alert rule: sre.edge.acceptor.queue.depth.high). Additional signal from streaming-fragment-errors metric and a spike in edge TCP resets. Oncall page had an automated alert at 2029-06-14T00:24 UTC.
2029-06-14T00:22 UTC - First acceptor-queue-depth alert t
…[truncated]
```

#### #2 `dsid_5f884c5669194d698c0be56a1df92b33`

```
Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling

Issue summary: Starting ~2026-03-13 11:20 UTC, ChatMetrics reported a rising error floor of 5xx responses for streaming requests. The API Gateway returned 502/503 intermittently and a subset of streaming sessions observed immediate fallback to short-polling which then triggered additional gateway throttling and elevated error rates. Impact: Customer-facing degradation for ChatMetrics (dedicated tier) — streaming API errors for ~40% of active sessions, visible increase in token cost due to retries. Environment: prod-us-east, dedicated tenant cluster. Observed with model redwood/text-xt-3b. Steps to reproduce: 1) Initiate ~600 concurrent streaming sessions from a single ChatMetrics vCPU-based client to the /v1/streams endpoint; 2) Hold long-lived streams with occasional small writes (~1-2 tokens every 2s); 3) Observe on the client: intermittent 502/503 during handshake period followed by server-initiated fallback and then 429s after gateway backoff. Recent changes: nightly keystore rotation completed at 11:05 UTC and an autoscaler policy sweep was applied at 11:10 UTC. Logs/metr
…[truncated]
```

#### #3 `dsid_5dfe1a03b30b4e728de8fa999bdf88dd`

```
Intermittent 5xx spike from delayed HTTP/2 ACKs causing streaming sessions to half-close and upstream restarts

Issue summary: Beginning ~2026-03-13 09:10 UTC GreenLeaf AI observed a sustained elevation in 5xx responses on streaming routes. Error pattern shows many short-lived streaming sessions ending with upstream connection resets or 502/503 responses. Impact: customer is seeing ~18% failed requests on high-concurrency streaming workloads (conversational chat) leading to degraded UX and increased retry traffic. Environment: prod us-east tenant on Dedicated pool (pool-id d-12).
1) Send concurrent streaming chat requests (50 concurrent streams) against /v1/stream with model=gptx-13b using their websocket-based SDK
2) Maintain each stream with small intermittent client-side pings (keepalive every 10s) for ~30s
3) Observe occasional immediate 502 response from API gateway, or stream resets with HTTP/2 RST_STREAM codes
4) Reproduce more reliably during tenant burst (~>80% of provisioned concurrency)
[apigw-2026-03-13T09:12:21Z] route=/v1/stream tenant=d-12 upstream=10.2.5.83:8443 status=502 msg=upstream_reset reason=half_closed_ack_delay
[runtime-2026-03-13T09:12:21Z] pid=23914 SIGCH
…[truncated]
```

#### #4 `dsid_15a9d93cc59c4241a97a7e72f749a216`

```
Postmortem: Streaming stalls during peak traffic (2026-01-12)

## Summary
On 2026-01-12, streaming responses intermittently stalled for a subset of chat completion requests. Affected clients observed streams that paused mid-response for 10–45 seconds, then resumed or timed out. The incident correlated with a traffic surge and increased concurrent connections on the edge streaming gateway.

## Customer impact
- Duration: 41 minutes (peak impact window)
- Symptoms: stalled Server-Sent Events (SSE) streams; elevated client timeouts
- Scope: ~9% of streaming requests in us-east-1

## Detection
- Alert: "stream-gateway open connections" exceeded threshold
- Secondary signals: increased 499/504 rates at the edge; elevated p95 time-to-first-token

## Timeline (UTC)
- 16:02: First alerts triggered (p95 TTFT + edge 5xx)
- 16:07: On-call confirms stalled streams in synthetic checks
- 16:15: Mitigation: reduce max concurrent streams per gateway pod; scale gateway
- 16:29: Runtime team rolls back a connection reuse optimization
- 16:43: Metrics return to baseline

## Root cause
A recently enabled connection reuse optimization increased head-of-line blocking within the streaming gateway under h
…[truncated]
```

#### #5 `dsid_c22869a06d0a4cb89e595c2caea91299`

```
Streaming stutter detection and continuity recovery playbook

Summary: During a capacity pressure event on 2026-03-09 we observed a class of streaming failures that manifests as short "stutter" bursts (clients receive duplicated offsets, truncated tokens, or repeated partial-frames) and intermittent silent pauses before reconnect. Affected tenants experienced incomplete responses and elevated reconnect rates. Root-cause signals point to a combination of (1) worker-level write stalls when kernel scheduling thrash coincided with large batch spikes and (2) client-facing backpressure semantics that do not preserve sequence continuity across reconnects. This ticket captures the detection rules, immediate mitigations, and a concrete set of follow-up engineering tasks to eliminate recurrence.
2026-03-09 10:12 UTC: First alert - streaming p50 latency spike on region us-west-2.
2026-03-09 10:18 UTC: Support reports increased reconnect rate from a high-volume customer.
2026-03-09 10:32 UTC: Oncall traces show repeated "stutter" windows (0.5-2s) where tokens are duplicated or truncated; KV cache offsets misaligned in ~30% of traces.
2026-03-09 11:05 UTC: Rolling scale-up and emergency throttl
…[truncated]
```

#### #6 `dsid_24422ce3ea2a4f53b9175e9e82d0e493`

```
Known issue: Streaming responses stall (SSE stream stops mid-response)

## Overview
Some customers have reported that **streaming responses (SSE)** can **stall mid-response**: the HTTP connection remains open, but **no additional tokens arrive** and the client may never receive a terminal completion event (e.g., "[DONE]" in OpenAI-compat mode).

This page documents symptoms, impacted configurations, mitigation steps, and how to triage.

## Symptoms (customer-reported)
- "Stream hangs" / "freezes" / "stalls" partway through generation
- Client shows an open connection but stops receiving chunks
- More frequent on longer outputs or when client-side consumption is slow
- Non-streaming requests often complete successfully (worse UX)

## Where it has been observed
- Hosted API: prod (us-east)
- Dedicated: prod (eu-west)

## Suspected root cause
In older runtime versions, an edge case in the streaming flush/backpressure path can result in the generator loop failing to emit additional chunks (including the terminal event).

## Mitigations / Workarounds
1. **Upgrade serving runtime** to a version that includes the streaming keepalive + backpressure fix (runtime **2.18.3** or newer).
2. If 
…[truncated]
```

#### #7 `dsid_1b5456e3574541148333459ac1344098`

```
Known issue: Streaming responses may freeze mid-generation (SSE stalls)

## Overview
Some customers have reported that streaming responses stop emitting tokens mid-generation while the HTTP connection remains open. The client may not receive an error or a terminal [DONE] event. This is typically described as a *freeze* or *stall* in server-sent events (SSE).

## Symptoms
- Streaming completion stops mid-sentence.
- TCP/TLS connection remains open.
- No final event (e.g., [DONE]) is observed by the client.
- Client UI shows an infinite spinner or hangs waiting for more tokens.

## Where weve seen it
- Dedicated and Hosted API traffic, primarily under higher concurrency or with intermediaries (proxies/LBs).
- Internal reproduction was easiest when response compression (gzip) was applied to text/event-stream.

## Primary contributing factors (current understanding)
1. Buffering/backpressure in intermediaries when payload chunks are small (token-by-token).
2. gzip/compression on SSE causing chunk coalescing and delayed flush.
3. Client implementations that wait indefinitely without a read timeout.

## Mitigations / Workarounds
### Customer-side recommended configuration
- Set a client-
…[truncated]
```

#### #8 `dsid_b0de57c71e834d2680538e64658e9bc9`

```
Unexpected streaming connection interruption mid-response after worker eviction/autoscale

Issue summary: Customer reports streaming chat sessions (SSE and websocket flavors) abruptly stop producing tokens mid-response during periods of increased load and concurrent autoscaling activity. Impact: Ongoing user-visible interruptions for AtlasSearch's chat product resulting in degraded UX and several failed transactions. Environment: production cluster in us-west running Dedicated capacity pool 'atlas-dedicated-1' with mixed quantized and float worker fleet.

Observed behavior: Streaming response begins normally, several token chunks stream to the client, then the connection stops emitting further data without a final '[DONE]' frame or explicit HTTP error. Client-side shows persistent TCP connection but no bytes for 8-30 seconds; some clients see immediate connection close. This happens across both SSE and WebSocket endpoints.

Expected behavior: Continuous token stream until completion with explicit end-of-stream marker or proper error code and retry guidance.
1) Use AtlasSearch production account with workload profile that submits 20 concurrent streaming chat requests to /v1/chat/str
…[truncated]
```

#### #9 `dsid_504460b1f5884382b02eb3af329ab4fc`

```
P0 hostedAPI stream churn + memory pressure retro

On 2029-12-12 at ~11:04 UTC we observed a P0 impact to the hosted API streaming surface: sustained client streaming stalls and elevated p50/p95 TTFB for streaming sessions in us-west-2. The user-facing symptoms were stalled streaming responses (no token traffic) and connection reconnects. The incident lasted ~62 minutes for the bulk of traffic before controlled mitigation, with complete cleanup following autoscaler and cache tuning over the next 3 hours.
Approximately 18% of streaming sessions in us-west-2 experienced stalls lasting 10–45s; overall hosted streaming error-rate spiked from baseline 0.02% to 1.8% during the window. A subset of high-throughput partners saw multiple reconnects and increased token costs due to repeated replays. No data loss was detected; requests eventually resumed or were retried by clients.
11:02 UTC — minor uptick in ephemeral connection churn detected by edge metrics
11:04 UTC — synthetic streaming check alerts (SRE-runbook) for elevated TTFB and stall count
11:07 UTC — oncall paged; initial hypothesis: edge TLS session churn or upstream edge autoscaler thrash
11:12 UTC — SREs observe high memory RSS
…[truncated]
```

#### #10 `dsid_46b0bc1e97ae4d8792d08e6f4122b948`

```
P1 Incident Postmortem: Streaming responses intermittently hang

## Summary
On 2026-02-03, some customers reported that streaming chat completions would start normally and then stop producing tokens. Requests remained open until client-side timeouts. The incident impacted hosted API streaming routes for ~27 minutes.

## Severity
P1

## Customer impact
- ~3.1% of streaming requests in us-east experienced a stall > 30s.
- Non-streaming requests were not affected.

## Timeline (UTC)
- 18:06: Incident starts (increased reports, elevated open connections).
- 18:11: On-call acknowledges; partial mitigation by lowering max concurrent streams per pod.
- 18:20: Hotfix: disable experimental backpressure setting in the stream proxy.
- 18:33: Metrics return to baseline.

## Root cause
A recent runtime upgrade changed the stream chunk flush behavior, which interacted badly with the gateway's backpressure configuration. Under specific token burst patterns, the stream proxy would stop forwarding chunks while keeping the connection open.

## Detection
Detected via customer reports and a delayed spike in "open_streams". No direct alert on "stalled_stream_ratio" existed.

## Follow-up action items (
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 10: `qst_0038::metadata` · N=40000 · meta · priority=high

- **auto Hit@10:** `True`
- **LLM triage (optional):** label=`unsure` mode=`other`
- **LLM note:** llm_error: OpenAI HTTP 429: {
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-XSSQmWIx80t1tvfOCV1hxO4V on tokens per min (TPM): Limit 30000, Used 27507, Requested 2528. Please try again in 70ms. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

### Question

In the redwood repo, which base branch was the merged PR that added GPU queue depth metrics and a scheduler sampling probe targeting?

### Gold document(s)

#### GOLD `dsid_d04ffbe63ea44224892533eb0fe95bc6`

```
Instrument GPU queue-depth counters and scheduler sampling probes

Motivation: We need lightweight visibility into real-time GPU submission queue depth and scheduler backpressure to diagnose latency spikes under mixed workloads. This PR adds a low-overhead queue-depth counter set, a periodic sampling probe for the scheduler hot path, NVTX range helpers for correlating samples to kernel submissions, and a small microbenchmark/harness and dashboard for triage. Summary of changes: added queue_counters.h/cc with atomic counters and scoped increment helpers; added scheduler sampling probe that captures queue depth, epoch-id, and active-batch-size at 250Hz; wired counters into the existing Prometheus exporter and exposed new metrics (redwood_gpu_queue_depth_{min,max,avg,p50,p95,p99}, redwood_scheduler_sample_total); added an NVTX-friendly scoped range wrapper to avoid repeated callsites; added a microbench tool (tools/microbench/gpu_queue_sampler.cc) that exercises submission patterns and exports a JSON summary; added a Grafana dashboard template (docs/perf/grafana_gpu_queue_dashboard.json) and a short README with run instructions and recommended alert thresholds; added unit and integration tests for counter rollover and multi-threaded increments. Checklist: [x] unit tests, [x] integration test in CI, [x] perf microbench added, [x] dashboard JSON, [x] changelog entry. Testing: CI: full build + unit tests passed; integration tests exercise a synthetic workload that mimics our batching distribution and show stable counters. Local perf: in our synthetic mixed-latency workload the scheduler sampling probe identified two submission hotspots and the microbench shows an 80% reduction in observed queue-spin time after reducing unnecessary submission retries (this PR does not change retry behavior; we used the tool to validate impact of a follow-up tuning change). Backwards compatibility: metrics are additive and guarded by config flags; default behavior is unchanged. Related: complements ENG-4892 (batch scheduling visibility) and ENG-5021 (kvcache instrumentation).
Adds low-overhead GPU queue-depth counters, a scheduler sampling probe, and Prometheus/Grafana instrumentation f
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_d04ffbe63ea44224892533eb0fe95bc6` **← GOLD ID**

```
Instrument GPU queue-depth counters and scheduler sampling probes

Motivation: We need lightweight visibility into real-time GPU submission queue depth and scheduler backpressure to diagnose latency spikes under mixed workloads. This PR adds a low-overhead queue-depth counter set, a periodic sampling probe for the scheduler hot path, NVTX range helpers for correlating samples to kernel submissions, and a small microbenchmark/harness and dashboard for triage. Summary of changes: added queue_counters.h/cc with atomic counters and scoped increment helpers; added scheduler sampling probe that captures queue depth, epoch-id, and active-batch-size at 250Hz; wired counters into the existing Prometheus exporter and exposed new metrics (redwood_gpu_queue_depth_{min,max,avg,p50,p95,p99}, redwood_scheduler_sample_total); added an NVTX-friendly scoped range wrapper to avoid repeated callsites; added a microbench tool (tools/microbench/gpu_queue_sampler.cc) that exercises submission patterns and exports a JSON summary; added a Grafana dashboard template (docs/perf/grafana_gpu_queue_dashboard.json) and a short README with run instructions and recommended alert thresholds; added unit and integrat
…[truncated]
```

#### #2 `dsid_e4c9e2896967401f8da2dfca247bba09`

```
add-async-kernel-latency-sampler-and-batching-simulator-microbench

Context and motivation: We need lower-overhead, continuous visibility into per-kernel submission and queueing latency across the runtime's async execution path to diagnose intermittent tail latency regressions observed in Dedicated. This PR introduces two complementary pieces: 1) an async kernel latency sampler that attaches lightweight samples to the kernel submission path and aggregates histograms for export; and 2) a microbenchmarking binary (batching-simulator) that models continuous batching + KV-cache warmup behavior to validate scheduler heuristics.

What changed (high level): added a low-cost sampling ring buffer and histogram aggregation in runtime/metrics, instrumented major async submission points with conditional NVTX ranges (behind a runtime flag to avoid production overhead), and added a standalone microbench under tools/batch-sim to simulate mixed-size requests, KV-cache hits, and different batching window sizes. Also added Grafana dashboard json and Prometheus scrape hooks to visualize the new histograms.

Why this approach: previous profiling artifacts were either too heavy (full-trace CUPTI captur
…[truncated]
```

#### #3 `dsid_13875eadc7d14beb99742d8b1ef48608`

```
Introduce async-prefetch rotary-aware attention kernel with hybrid-striping and adaptive KV cache gating

Context: Production chat and short-sequence workloads show high per-token overhead from attention kernel dispatch and excessive KV cache churn when multiple low-latency requests are interleaved. This PR introduces a new rotary-aware attention kernel that performs asynchronous prefetching of Q/K/V tiles and a hybrid-striping scheduler that balances warp-level striping with bank-coalesced micro-tiles. In addition, an adaptive KV cache gating mechanism is added to reduce memory thrash for streaming workloads.

What this PR does (high level): - Adds a new CUDA kernel (async_prefetch_attn) that prefetches rotated KV prefixes asynchronously while computing QK product, avoiding a strict blocking fetch for common rotary/rope layouts. The kernel is rotary-aware (computes sin/cos transforms fused into the prefetch path). - Implements a hybrid-striping scheduler that chooses between warp-striping and micro-tile striping based on sequence length distribution and batch shape heuristics. This reduces bank conflicts on medium-short sequences (<=512) while preserving throughput on long sequenc
…[truncated]
```

#### #4 `dsid_c9a1ca32dae14498a89c2ae1b1d5bfa8`

```
compact attention core: token-aware scheduler + shadow-kv prefetch to reduce tail latency

Motivation: customer workloads with highly skewed request sizes (short chat messages interleaved with long context generations) were exposing p95/p99 latency spikes despite aggressive batching. Investigation showed two contributing factors: (1) the scheduler was coalescing tokens without awareness of prefix-hotness leading to oversized batches that pushed some requests into longer KV read paths, and (2) KV cache cold-misses for recently-used key ranges created stalls while the decoder waited on memory transfer.

This PR introduces two complementary runtime improvements to reduce tail latency and improve throughput: (A) a token-aware continuous batching scheduler (CompactScheduler) that maintains small fast-path batches for low-token requests while opportunistically coalescing larger requests, and (B) a shadow-KV prefetcher that tracks recent token window footprints and proactively stages KV shards into GPU-local memory for predicted next-chunk accesses. Together these reduce p95 by ~28% and p99 by ~41% on mixed chat/long-gen workloads in our internal canary.

What changed (high level):
- runt
…[truncated]
```

#### #5 `dsid_0559f1f4179e432ab8e48ce2afeeac35`

```
Introduce contextual token-latency drilldown, kernel-queue sampler, and alert squelcher

Context and motivation: We frequently see sporadic tail latency spikes attributed to kernel queueing and cross-route warmup effects. Existing dashboards surface aggregate token latency, but lack an anchored, per-invocation drilldown that attributes time to phases (network, KV lookup, kernel queue, decode). This PR adds: 1) a kernel-queue sampler metric that captures queue depth/inflight-per-gpu-bucket and correlates with token latency; 2) a token-latency drilldown dashboard (per-route, per-model, per-sequence-shape) with phase attribution and example trace links; 3) an "alert squelcher" operator for noisy token-latency alerts that applies quiet windows and cross-invocation deduplication to reduce pager churn. Approach: metric instrumentation is lightweight (O(1) per scheduling tick) and uses reservoir sampling for representative trace correlation. Dashboard changes are additive JSON panels; backend changes include a sampler and an alerting middleware that can be toggled per-team. Migration notes: this adds a new metric (redwood.kernel_queue.depth_bucket) and a new label on token latency spans (
…[truncated]
```

#### #6 `dsid_0c70f57be1bd4e30b01adf979c51a8cf`

```
Chronological scratch compaction and ephemeral KV binning

Background: Production workloads with mixed sequence lengths were showing elevated transient GPU memory usage due to long-lived scratch allocations and conservative KV retention. Motivation: Reduce peak working set without regressing latency SLOs by compacting scratch buffers along a chronological lifetime axis and introducing an ephemeral KV binning layer to enable low-overhead short-term eviction. Design summary: 1) Chronological scratch compaction: a micro-slab allocator subdivides large scratch arenas into thin chronological slabs keyed to request arrival time windows. Slabs are compacted (coalesced and zeroed) once all active kernels referencing that slab have completed; we prioritized an optimistic fast-path for single-kernel consumers and a fallback slow-path that defers compaction for multi-kernel overlap. 2) Ephemeral KV binning: add a short-lived in-GPU bin layer for KV cache entries produced by streaming/continuous-batching traffic. Bins are sized by recent token reuse statistics and are evicted in short time windows (seconds) before falling back to the regular LRU eviction policy. 3) Kernel handshake and schedul
…[truncated]
```

#### #7 `dsid_3c86346bb2e2408e93e740f9877f254e`

```
Scheduler metrics: prefill/decode split, queue depth histograms, and backpressure counters

Context: For the FP8/INT8 kernel benchmarking sprint we keep seeing cases where microbench wins don’t show up end-to-end. The primary missing piece has been scheduler-level visibility into (a) how much wall time is spent in prefill vs decode, (b) how deep the internal queues get under mixed workloads, and (c) when we’re applying backpressure (and why). This PR adds low-overhead instrumentation to make benchmark runs interpretable and to support perf-canary gating by workload regime.

What’s in this PR: 1) Prefill/decode split metrics: We now record scheduler-attributed time and token counters separately for prefill and decode paths. This is emitted both as per-request spans (when tracing is enabled) and as runtime histograms/counters (always on). New metrics: runtime.scheduler.prefill.duration_ms (histogram), runtime.scheduler.decode.duration_ms (histogram), runtime.scheduler.prefill.tokens (counter), runtime.scheduler.decode.tokens (counter), runtime.scheduler.prefill.batch_size (histogram), runtime.scheduler.decode.batch_size (histogram). 2) Queue depth histograms: Adds queue-depth trackin
…[truncated]
```

#### #8 `dsid_6a27b963a92c41d8b8d7e5b6bbb79fc1`

```
windowed allreduce aggregation and kernel scheduler tuning

Motivation: multi-GPU small-message overheads and poor overlap between NCCL collectives and lightweight compute kernels were a recurring source of tail latency for short sequences and KV-cache dominated workloads. This change introduces a windowed allreduce aggregation layer and a scheduling heuristic that co-schedules small fused kernels with pending communication windows to improve overlap and reduce per-request latency. The PR touches runtime kernel selection, NCCL stream/priority handling, KV-cache aggregation alignment, and adds microbenchmarks + a canary test for heterogeneous GPU setups. Key ideas: 1) Windowed aggregation: group small allreduce ops into time-bounded windows and issue a single fused allreduce (reduces NCCL small-kernel overhead and launch cost). 2) Agg-aware scheduler: runtime observes pending communication windows and routes short compute kernels onto low-latency streams that can run while collective is in-flight, using stream priorities and barriers to avoid reordering. 3) KV-cache alignment: when shard-prefetch triggers many tiny reductions, we align prefetches to aggregation windows to avoid thun
…[truncated]
```

#### #9 `dsid_0ba6ff723dd9400ea5c5aabb8098eeae`

```
Unify CPU hotpath: lightweight scheduler, zero-copy request path, and KV prefetch to reduce serialization

Motivation: production workloads hitting inference control-plane observed sustained CPU saturation in the request hotpath even when GPU utilization was moderate. Root causes traced to (1) cyclical memcpy/parse steps copying request buffers between IO thread, dispatcher, and worker threads; (2) a single global dispatch mutex that serialized fast-path requests during bursts; (3) synchronous KV cache lookups that blocked worker threads and caused head-of-line stalls; (4) thread pool oversubscription and excessive spinning for short critical sections. This PR implements a series of coordinated CPU-side optimizations aimed at reducing serialization and context-switching friction while preserving correctness and fallbacks.Key changes (single-line summary): unified per-core cooperative scheduler, zero-copy request header handoff, KV-cache prefetch + lock-free read-path, striped dispatch slots and seqlock fallback, adjusted default thread pool sizing and soft-yield policy.Implementation details: - Introduced a lightweight per-core work scheduler (runtime/scheduler.cc) that keeps a sma
…[truncated]
```

#### #10 `dsid_986e4ae80b894812b093da87368a41ea`

```
hierarchical-comm-scheduler-with-layer-aware-kernel-selection-and-kv-prefetch-pipelining

Motivation: large tensor-parallel workloads continue to see tail-latency and suboptimal bandwidth utilization on multi-socket multi-node clusters when model layer shapes vary. Existing static ring/allreduce placement and uniform chunking interact poorly with KV-cache prefetch windows and per-layer kernel performance characteristics. This PR introduces a hierarchical communication scheduler plus two complementary runtime optimizations: (1) layer-aware kernel selection that picks fused vs unfused kernels per-layer and preempts long-running kernels when small low-latency requests arrive, and (2) a KV-prefetch pipelining manager that overlaps eager shard transfers with compute at per-layer granularity. Summary of changes and goals: implement a two-level communicator partitioning (intra-socket local rings + inter-socket bridges) with adaptive chunk sizing based on recent per-link throughput; introduce a windowed send schedule that staggers chunk launches to avoid head-of-line blocking; add a layer profiler that collects microbenchmarks to choose attention/ffn kernels and a cooperative preemption pa
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 11: `qst_0041::metadata` · N=50000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`other`
- **LLM note:** The expected document ID is not present in the top-10 retrieved document IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty but do not address the specific question about cross-region failover for AWS Marketplace LLM inference services. The failure mode is 'other' as the retrieved documents do not relate to the question's context, indicating a possible retrieval issue unrelated to embedding or lexical mismatch.

### Question

For the North America based SMB prospect evaluating a hosted API for a support chatbot and summarization, what month is the deal forecast to close?

### Gold document(s)

#### GOLD `dsid_4c1c5fb53ca2432995ea42adc4330fca`

```
SparkBarrel Systems

Inbound SMB lead from organic signup (self-serve). App: conversational support bot + ticket summarization for e‑commerce merchants. Onboarded via quickstart; ran initial tests in us-east-1. 

Primary pain: observed high tail latency (200-900ms/token) and several timeouts for multi-turn chat sessions. Customer reports "bursty slowdowns" during midday traffic and poorer performance for EU customers. They think it's 'our API' but likely region mismatch + some long prompts.

AE call 2026-03-01 (first discovery): Maya intro, asked about workload shape & SLOs. They want ~150ms median, 350ms p95 for single-turn replies; throughput small (10-40 reqs/min) but spikes with campaign. Cost sensitive — wants hosted API pricing cap.

Tech notes from SE sync 2026-03-03 (Diego):
- They are calling default endpoint in us-east-1 from EU users (latency ~70-160ms network + 150-600ms compute).
- Timeouts set low in client (500ms) and then client retries create extra load.
- Prompts include full ticket threads (avg 1.2k tokens) — causing long decode times.
- Not using streaming; whole-response waits increase observed tail.

Recommendations shared: region routing to eu-west-1 for EU traffic; enable streaming (chunked responses) for perceived latency; reduce prompt context via extractive summary (pre-trim ticket body), use system-level instruction templates; set request timeout to 10s and use exponential backoff on client; cap max_tokens per reply where appropriate; experiment with smaller model variant for low-cost fallbacks. Also suggested using prefix caching for repeated system prompts and batching embeddings for nightly rerank jobs.

Progress and artifacts:
- Sent sample config + perf checklist 2026-03-05 (drive link above).
- Diego provided a tuned client sample (region header + streaming example) 2026-03-06.
- Customer ran AB test 2026-03-07 switching EU traffic -> eu-west-1: median latency improved ~110ms, p95 down ~260ms but still above desired.

Customer quotes: "Switching region helped a lot — but mid-day spikes still bite us. We need guardrails so our UI doesn't show 'spinning' to users.'"

Open risks / blockers:
- Need to finalize SSO + audit controls b
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_b9feabcc616a441dadb2e6237166b316`

```
Silvercove Inbound Solutions

SMB e-commerce SaaS evaluating Redwood Hosted API for support chatbot + summarization. Early discovery, cost-optimization focused: batching, caching, prompt compression, token audits. Public cloud only, SOC2 required. AE: Maya Patel; SE: Liam O'Connor.
Inbound SMB from e-commerce personalization space. Signed up to Hosted API for trial — primary goal: power a support chatbot + product Q&A and summarization of order threads. Very cost sensitive: small margins, "need predictable hosting costs" stated by CTO Ramon Mendes. Current traffic: ~1k unique users/month, expect to double after Q2 campaign. Expected steady-state qps: 3-8 (peak ~20 qps), latency target: <500ms for 95th pctl on chat responses.

Key asks from discovery call:
- Token usage audit: customer wants a breakdown of where tokens are being spent (system vs user vs assistant) across sample prompts. Wants a CSV template to drop in their raw logs.
- Batching & caching recommendations: they run 70% of requests with small context windows (~300 tokens) and think batching could help reduce cost on background embedding/rerank jobs.
- Prompt compression / truncation guidance: asks for best practices to
…[truncated]
```

#### #2 `dsid_3ad63e1b88fe489b8e6ca8a586915565`

```
Banyan Inkworks Systems

SMB marketing platform needs hosted API. Key asks: predictable per-token pricing, token-level cost & latency dashboards, automatic prefix caching and batching recommendations, ability to pin model variants for preview vs bulk generation, SSO for admin, SOC2 + audit logging. POC to validate throughput and unit economics.
Quick CRM notes / call highlights:
- Company: Banyan Inkworks Systems — marketing automation platform for SMB publishers and agencies. High-volume campaign generator + churn of campaign variants.
- Traffic estimate: ~8-12M tokens/month now, could grow 3x in 6 months. Typical request size 50-300 tokens. Peak bursts 150-200 req/s during campaigns.
- Primary asked: hosted (self-serve) API for fast onboarding. Cost is a major constraint — they asked about per-token unit economics and billing visibility.
- Performance targets: tail latency for short prompts <300ms, steady-state throughput ~150 req/s, allow spikes to 200 req/s.
- Model preference: flexible to use curated open models; want lower-cost quantized variants for bulk generation and higher-quality variant for customer-facing preview.
- Ops interest: automatic prefix/KV caching, request ba
…[truncated]
```

#### #3 `dsid_5591b2d92c864adb8551a34c6af33056`

```
Salubrex Health Labs

Inbound SMB lead via self-serve signup — marketing form followed by quick demo request. Small telehealth startup building a chat-first triage + summarization layer for therapists. Early-stage POC: web chat for intake, backend summarization to send session notes to EHR. Primary ask: hosted API (fast time-to-value) but with clear controls for retention and de-identification.

Key quotes: "We need something we can get running in a week — but legal will kill it if we can’t promise data controls." — Head of Ops.

Quick timeline / activity log:
- 2026-03-02: Self-serve sign-up, tried quickstart examples (chat + embeddings). Received form answers: approx 15k tokens/month target for POC.
- 2026-03-03: Intro call (30m) with AE Evelyn + SE Ravi. Fireflies ff_20260302_0132 transcript attached. Demo of hosted inference and batching notes.
- 2026-03-04: Sent security questionnaire and SOC2 cert link; asked about BAAs and retention controls.
- 2026-03-06: Customer ran sample through hosted API; reported good latencies (~120-180ms per token for short prompts) but wants accuracy checks on medical summarization.
- 2026-03-08: Follow-up email thread (gmail_thread_17f3ab2026) as
…[truncated]
```

#### #4 `dsid_4775b0714f064b6ea5875c519857dd77`

```
NectarLoop HostedAI

Inbound SMB lead from developer community sign-up. Self-serve trial started 2026-02-24. Primary ask: reduce per-request cost for chat + embeddings. Key points:
- Wants hosted API (self-serve) with predictable monthly bill; high sensitivity to token spend.
- Use-cases: customer support bot (chat), product recommendations (embeddings), nightly summarization job (batch).
- Asks for specific guidance: batching/caching best practices, prompt compression strategies, and a token usage audit of their initial 5k requests.
- Quote from call: "We can show value quickly but finance will shut us down if cost spikes. Need guardrails."
- Security: SOC2 required for procurement; SSO later but not blocking initial trial.
- Performance targets: median chat latency under 500ms for 90% of requests; embeddings throughput ~50 reqs/sec during peak.
- Model preference: open models first (cost), fallback to verified LLM if quality regression. Routing: region=us-east preferred.
- Internal stakeholders: CTO (Eva Lin), Lead ML Eng (Ravi Shah), Head of Ops (Maya Torres).
- Requested sample config: batching window 20ms vs 100ms tradeoffs; want recommended cache TTLs for prefix caching.
- Ac
…[truncated]
```

#### #5 `dsid_6ded6cb1fa2d4dfeb489e0e9e3095d16`

```
Mapleridge AssistWorks

Inbound SMB lead; very price sensitive but cares about quality for customer-facing chat. Wants to start on hosted API (self‑serve) and keep option to move to Dedicated if traffic grows. Key asks: 1) short list of recommended models for chat + embeddings (Llama-2-13B, Mistral-7B, Qwen-7B noted) with expected quality delta and token-cost delta; 2) latency/throughput baselines for public cloud (gcp/us-west1); 3) example batching and caching knobs to control cost; 4) SSO + audit logging overview for later procurement.
- They run a commerce chatbot that handles order status / returns (sensitive PII in context). Data residency not strict but retention controls required.
- Dev quote: "We need something that feels as good as the current hosted model at half the cost — happy to trade a bit of finesse for speed and cost savings."
- SE notes: target p95 < 200ms for 1-2 concurrent requests, expect bursty traffic (10-50 rps during promos). Embedding volume low-medium (5k/month) but reranking will spike during seasonal sales.
- Model preferences: prefer smaller/efficient variants if quality delta < 3-5% on intent/response correctness. Curious about q4/mixed quantization r
…[truncated]
```

#### #6 `dsid_3d2300add2f94ce7b8fa97aada4a10d4`

```
Sandbar Analytics

Founder wants an MVP support assistant + doc search for SMB customers. Priorities: minimize monthly cost for low traffic, fast dev time, decent summarization quality. Will prototype with hosted API first.
Send hosted API pricing breakdown and example cost calc; schedule 30m SDK walkthrough with founder
needs clear pricing vs OpenAI/Anthropic
want low-cost small-business tier for prototyping
uncertainty about rate limits/concurrency
Inbound from founder after self-serve signup. Founder-led discovery call 2026-03-05. Wants straightforward pricing comparison to OpenAI + Anthropic. Mentioned: 'We need to know whether we can ship MVP for <$200/month in cloud costs.' Interested in hosted API only for now; may consider Dedicated later if predictable throughput needed. Technical bias toward public cloud and fast time-to-value. Asks about token rounding, hidden fees, and concurrency bursting. Security is moderate: SOC2 preferred, SSO later. Founder willing to sign TOS but wants data isolation assurances. Quick POC desired (1 week) with small sample dataset and conversational support bot. Shortlist vendor choices: OpenAI, Anthropic, Redwood (ask: can Redwood match low-cost
…[truncated]
```

#### #7 `dsid_8e3a782937134f83a06e6d961cb40be0`

```
Mariner Sprocket Digital

2026-03-02: inbound signup via blog post + tried hosted API free tier (signup token: gfr-89)
2026-03-04: intro email from Maya — customer replied asking about invoicing for 12 month forecast
2026-03-06: quick demo (30m) w/ Diego — walked through quickstart, embeddings, streaming responses
2026-03-08: security questionnaire started — SSO requirement flagged; provided SOC2 link
2026-03-11: internal review call — finance prefers invoice if ARR > $10k; engineering will own integration
SMB ecom startup — core product is a headless storefront + customer chat widget.
Primary ask: low-friction hosted API to power chat + embeddings for search and upsell rules.
Latency target: median < 300ms for chat, 95th < 700ms for critical flows (fast checkout support).
Throughput: small bursts (50-200 QPS per tenant) expected during promotions — cost sensitivity high.
Model prefs: open models acceptable; want Redwood verified perf profiles. Interested in token-level cost breakdown.
Procurement: founder prefers credit-card self-serve for first 3 months. Finance may switch to invoice if ARR commitment >= $12k/yr.
Startup: they are part of a regional incubator — asked about startu
…[truncated]
```

#### #8 `dsid_0cb53fb9b05e42c7a69bd7db8de6012e`

```
VerbaChat Labs

Lead origin: self-serve signup (free credits) -> inbound email to sales@redwood.

Quick summary:
- SMB conversational SaaS (customer support bots) focusing on quick replies and searchable conversation history.
- Signed up for Hosted API trial to avoid infra ops; wants aggressive cost control.
- Key asks: batching recommendations (per-turn vs multi-turn), prefix KV caching, prompt compression examples, token usage audit for initial 100k requests.

Timeline / recent activity:
- 2026-02-18: Trial sign-up via website (auto-created company).
- 2026-02-22: Auto onboarding email + quickstart used; connected workspace and ran sample chat flows.
- 2026-03-02: 30m discovery call (ff_20260302_verbachat_initialcall) — attended: Jonas (Head Product), Priya (Eng lead). AE: Maya, SE: Ethan.
- 2026-03-04: Sent quick token-usage snapshot from trial (attached in drive).
- 2026-03-08: Follow-up from Jonas asking for concrete cost projection and examples of prompt compression; asked if Redwood does automated batching or if they need code changes.
- 2026-03-09: SE created RED-3421 asking runtime for best-practice code snippets for batching, plus small POC config.

Notes from calls / quo
…[truncated]
```

#### #9 `dsid_c73df6b8cc0645439edeabed43cce6d2`

```
BentoAssist Cloud

SMB support automation vendor. Primary goal: hosted API for fast self-serve POC to auto-summarize inbound tickets, extract structured fields (issue_type, priority, customer_tier), and perform function/tool calls to their ticket system to set status/assign. Expect to start on public cloud; low initial security friction but SOC2 and SAML planned. If POC shows performance/cost benefits, move to higher commit or Dedicated plan.
- Lead source: docs signup + chat widget. Wants a self-serve path first.\n- Use case: automatic ticket summarization and structured extraction for downstream routing + tool-calling to update status in their system.\n- Latency/throughput: avg ticket body length ~300-600 tokens; peak 6 reqs/sec during business hours; target median latency <200ms for summary-only path, <450ms for tool-calling flow.\n- Cost sensitivity: SMB margins, looking for predictable per-token pricing; interested in suggestions on batching and prefix caching to cut costs.\n- Model preferences: open to smaller open models for summarization; wants ability to route to higher-quality model for high-priority tickets.\n- Security: SOC2 required within 6 months; currently use Okta 
…[truncated]
```

#### #10 `dsid_0e553d2eb09c406bb90fd873d112c787`

```
Lodestone Frugal AI

2026-02-12: Self-serve signup (free credits) - initial API keys created
2026-02-19: Automated cost alert — trial usage spiked (embeddings-heavy)
2026-02-23: Intro call (AE Avery Chen) — demo of hosted API, pricing overview
2026-03-02: Deep-dive with SE Jordan Patel (ff_20260302_5641) — discussed batching and cacheable prefixes
2026-03-09: Security questionnaire submitted (SOC2 + audit logs) — follow-up needed
Inbound SMB lead from trade newsletter; heavy focus on immediate cost reduction. Using hosted API for in-app support assistant and product search (dense embeddings + chat sessions). CTO quote: "We burned ~$1.2k last month during initial index builds — want to get to <$400/mo for steady state." Short-term asks: 1) quick wins for token reduction, 2) sample batching configs, 3) guidance on prefix/KV caching for chat sessions and embeddings reuse. 

Call summary 03/02 (Jordan): recommended - use continuous batching on ingestion, enable prefix caching for repeated system messages, apply prompt compression on templates, and run a 2-week token audit (sample script attached). Customer wants code examples in Node + Python for: batching client, cache key patterns, a
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 12: `qst_0044::metadata` · N=25000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty and relevant to SaaS and API trials but do not address the specific question about Acme's support response time commitments. This indicates a lexical mismatch failure mode. No pipeline issues were detected.

### Question

Who is the sales owner for the mid-market product analytics SaaS account that is evaluating Dedicated after a hosted trial and has a next step scheduled for early March 2025?

### Gold document(s)

#### GOLD `dsid_676625b7b7064b30a00da4f53fd24f88`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_fd49ed2b9f0b45c4b2a50ff391dd8e2c`

```
Sunboard Digital Platforms

Summary: mid-market B2B product analytics company experimenting with LLM-powered in-app assistant + search. Ran a 30-day hosted API trial Jan-Feb 2026. Wants Dedicated after proving unit economics and predictable latency.

Trial metrics (hosted API):
- Average QPS: 2.3 req/s across trial (non-peak).
- Peak sustained QPS: 12 req/s during Monday morning syncs (observed 10x baseline).
- Typical concurrency (active websocket streams): 6 concurrent chat sessions; spikes to 28 during release notes send.
- Token mix: ~40% short prompts (10-40 tokens), 50% chat exchanges (avg 180 prompt + 220 completion tokens), 10% long-batch embeddings (median 512 tokens).
- Avg token size per request: ~280 tokens.
- 95th p99 latency (hosted): 420ms server-side for small chat completions, 1.2s for long generation paths. Target for production: sub-300ms for short-inference paths, sub-800ms for long flows.
- Model preference: open models with strong throughput (Llama 2 variants, quantized FP16), interested in Redwood-verified m models with fallback to smaller quantized versions for cost control.

Use-case detail:
- Primary: in-product conversational assistant that summarizes use
…[truncated]
```

#### #2 `dsid_a6ac5e583105485fa029e9f9b18fdc3e`

```
Brookline Inference Solutions

Summary: Mid-market SaaS vendor (product analytics + in-app insights). Completed 2-week Hosted API trial; now evaluating Dedicated for predictable latency and data isolation. Trial outcomes and next-phase asks below.

Top-level highlights:
- Trial run (2026-02-01 -> 2026-02-14): ran 120k total requests, ~18M tokens. Typical call pattern: short prompts (10-40 tokens) + medium completions (80-220 tokens). Token mix ~ 15% prompt / 85% completion by token count; by request ~ 1:1.
- Observed baseline QPS on Hosted: 6 QPS sustained; peak bursts to 32 QPS during internal demo times. 95th latency target from product: <= 200ms for short-turn conversational messages; they saw 95th ~ 180-250ms depending on model variant and length.
- Concurrency notes: concurrent sessions ~ 20 active users hitting API during peak demo; expected prod concurrency ~ 60-120 (concurrent user sessions producing parallel requests) when they roll to 2nd feature cohort.
- Cost sensitivity: cost per 1M tokens is a key metric for finance; they want predictable slot-based pricing (hence Dedicated).

Customer quotes / call snippets:
- "Hosted trial was fast to integrate, but we need predicta
…[truncated]
```

#### #3 `dsid_1b679d7a5cd54d50b4c86aea8af42ac9`

```
Moonshore Inference Labs

Summary: Mid-market product analytics SaaS w/ interactive query assistant + support bot proof-of-value. Trial started on hosted API; now evaluating Dedicated for predictable latency and data isolation.

Hosted trial results (observed):
- Baseline QPS: 10-14 steady across business hours (EU+NA), typical weekday patterns.
- Peak QPS observed during feature release: ~48 QPS for 12m window.
- Avg concurrency per region: 5-8 active streams (chat sessions) with spikes to 18 during rollouts.
- Token mix (by volume): prompt ~60%, completion ~40% (prompt avg ~110 tokens, completion avg ~220 tokens).
- Monthly token burn (approx during trial month): 120M input tokens, 80M output tokens -> total ~200M tokens.
- Latency: 95th percentile generation latency on hosted trial ~420ms (prompt len 100-150, model: open-llama-family).

POC objectives:
- Move from Hosted -> Dedicated to guarantee 99th percentile latency <500ms under production QPS, and to meet compliance (VPC + audit logs).
- Reduce per-token unit cost via batching + KV caching for repeated analytic queries.
- Support model routing: primary open model + fallback to smaller quantized variant when latency spikes.

…[truncated]
```

#### #4 `dsid_85961c2d71ed4e77978c304ed29c929c`

```
AstraCove Product Labs

Summary: Mid-market product analytics vendor. Started with Hosted API quickstart for 14-day trial; now moving to evaluation for Dedicated reserved capacity. Team: VP Product (Maya Singh), Eng Manager (Noah Reed), ML Lead (Priya Das).

Trial outcomes (hosted API):
- 2026-02-02: Kickoff demo + architecture review (Aisha + Diego + Maya). Maya: 'need sub-300ms median policy for 1st-turn chat in mobile flows'
- 2026-02-03 to 2026-02-17: 14-day Hosted API trial. Instrumented token logging and traces.
- 2026-02-18: Fireflies call ff_20260218_astro-demo-9842 — product walkthrough + question on KV-caching.
- Observed metrics (hosted trial): baseline QPS 4-8, weekday peak bursts up to 25 QPS (on product launches), average concurrency observed 18-42, peak concurrency 68 (short spike during marketing campaign).
- Token mix during trial: chat flows ~62% of requests, embeddings 18%, reranking 12%, misc/summarization 8%. Median tokens per chat session (single request) ~720 tokens; 95th pct ~2,600 tokens (long conversation retains history). Embedding requests median 512 tokens per doc; rerank requests small ~120 tokens each.
- Latency: hosted API median token-latency ~120ms
…[truncated]
```

#### #5 `dsid_2e8c2f98895a40aaa007c6c060dbe12c`

```
Solaris Arc Cloudware

Overview: mid-market collaboration/product analytics SaaS (B2B). Looking to add LLM-powered assist and search to product and support flows.
Primary drivers: improve search relevance (embeddings + rerank), agent augmentation (chat + summarize), reduce time-to-resolution in support.
Initial path: Hosted API trial -> Dedicated POC -> Dedicated reserved capacity (VPC) if security checks pass.
Stakeholders: CTO (Lara Meng), Head of Product (Daniel Cho), SecOps (Evan Brooks), Procurement lead (Maya Singh).
Workload profile: mix of retriever-backed chat and short-form agent completions. Peak throughput expected ~80-150 qps for embeddings service; chat latency p95 target < 300ms for US region.
Model preferences: prefer open-weight models for cost control; interested in quantized GGML-like variants on Dedicated. Wants model fallback chain (largest -> mid -> small) when capacity constrained.
Cost sensitivity: moderate-high. Willing to pay for predictable Dedicated capacity but needs clear unit economics and batching/caching suggestions (Optimize recommendations desirable).
Security requirements summary: must support SSO/SAML via Okta, SOC2 attestation required, audit l
…[truncated]
```

#### #6 `dsid_2cff5b6b11ce43a3a574e0982637aef2`

```
KiteAnchor Labs

Product/Business overview: KiteAnchor builds product analytics SDK + in-app assistant for B2B SaaS products. Primary value prop is contextual guidance inside product and deep semantic search across event+session data.

Engagement summary: did 4-week Hosted API trial (Jan 20 - Feb 17). Goal: validate latency, cost, and correctness for in-app assistant + reranking pipeline before committing to Dedicated capacity. AE/SE-led POC. Several demo sessions, one live run with ~50 internal users.

Hosted trial observations (quantitative):
- Traffic observed during trial: avg QPS ~28 (steady-state), peak sustained QPS 95 during internal load test. Typical concurrency observed: 8-12 active sessions, bursts up to 48.
- Token mix: ~35% short queries (<50 tokens), ~50% medium (50-500 tokens), ~15% long (>500 tokens) due to session context re-sends. Average request: 120 input tokens / 220 output tokens.
- Latency: p50 ~85ms, p95 ~220ms on redwood-hosted baseline model; embeddings requests p95 ~40ms.
- Cost signals: generated cost per heavy-chat session higher than expected; team is sensitive to per-token cost for long-form explanations and multi-turn contexts.

Requirements for Ded
…[truncated]
```

#### #7 `dsid_c887f6ded8174824a9b88620e603924d`

```
Sunerra Product Intelligence

Summary: Mid-market product analytics company building an AI-first in-app product assistant + document/FAQ search. Completed 30-day Hosted API trial; moving toward Dedicated for predictable latency and isolation. Key ask: realistic Dedicated capacity estimate based on observed Hosted metrics and expected growth.

Hosted POC findings (high-level):
- Trial period: 2026-02-11 to 2026-03-10 (pilot across 3 product teams: search, assistant, recommendations).
- Observed average steady QPS: ~18 qps during business hours (NA), baseline concurrency ~12.
- Peak observed QPS (spikes during launches): 85 qps (short bursts), peak concurrency measured: 48.
- Token mix (observed): ~60% short prompts (<128 tokens), ~30% medium (128-512), ~10% long (>512). Avg token length: ~210 tokens/request.
- Latency targets: p95 <= 350ms for assistant short-turns; p95 <= 800ms for long-run retrieval+rerank flows.
- Cost sensitivity: wants to reduce per-token $ by 30-50% vs hosted plan; prefers predictable reserved pricing.

Requirements discussed:
- Must support SSO + audit logs + KMS integration; data residency: US only for now.
- Routing: primary region NA, fallback EU for DR.
-
…[truncated]
```

#### #8 `dsid_9324383a7b574c5eb732640f07d12eb9`

```
AutumnRidge Reorder Labs

Intro: 2024-12-18 inbound trial sign-up, AE (Maya Chen) intro call; they run search for mid-market ecommerce platform.
Discovery: strong emphasis on relevance for conversions; currently using Elastic + in-house ML reranker; want to improve NDCG without large infra lift.
Primary ask: reranking endpoint (online) + offline scoring for large eval sets (100k queries) -> ability to run batch/offline rerank for evaluation.
Latency/throughput targets: p50 <100ms for single-shot rerank of top-50, sustained throughput target ~100-150 req/s during peak, willing to trade slight latency for cost in some traffic tiers.
Cost sensitivity: mid-market budget, looking for hosted to validate gains, then move to Dedicated once ROI proven; target ARR impact threshold ~5-8% conversion uplift to justify Dedicated commit.
Model preferences: prefer open models (Llama2-ish), favor quantized variants for Dedicated; want option to fallback to a smaller distilled model for cheap queries.
Routing/fallback needs: route interactivity-critical traffic to low-latency pool; experimental traffic to cheaper batch-optimized pool; need canary rollout for rerank model changes.
Eval plan / POC: 2-
…[truncated]
```

#### #9 `dsid_6ee6ef4ce1c84921aec1a07b506541fb`

```
AeroVerge Labs

2025-09-15 - Intro call (AE Maya) — high-level product fit, use cases: support bot + doc search
2025-09-18 - Demo with SE (Diego) — showed hosted API integration, streaming, function calls
2025-09-22 - Started 2-week Hosted API trial (trial keys issued). Fireflies ff_20250922_847
2025-09-29 - Hosted trial mid-point review — observed token profiles, initial QPS baseline
2025-10-01 - Security questionnaire submitted; redwood security FAQ link shared
2025-10-02 - Pricing sensitivity call with finance (requested committed capacity pricing)
2025-10-03 - Sizing workshop with SE — requested Dedicated sizing and quote
Context: mid-market SaaS (product analytics) adding AI-first support assistant + semantic doc search. Started with Hosted API to validate latency/quality; now sizing Dedicated for predictable throughput and cost savings.

Hosted trial summary (2 weeks):
- Integration: backend service -> Redwood hosted API via SDK (ok). No major code changes.
- Observed traffic (sample window): typical sustained QPS ~18, peak burst QPS ~95 during internal load tests.
- Concurrency measured from client pool: avg concurrency ~12, p95 ~28.
- Token mix (sample aggregated): avg prom
…[truncated]
```

#### #10 `dsid_a032658b571d4562a1a98485c5adba4d`

```
Skyline Scribe Solutions

Summary: Mid-market SaaS (content automation for product teams). Ran Hosted API trial; now evaluating Dedicated for predictable throughput and residency. Interested in Dedicated capacity sizing + traffic forecast after Hosted trial.

POC highlights and customer quotes:
- 'Hosted response quality is fine; main ask is predictable latency for scheduled marketing bursts.' — VP Eng
- Trial telemetry: baseline daytime traffic ~12 QPS, sustained spikes up to 75 QPS during scheduled campaign windows (approx 10-15 mins), typical concurrency measured at ~40-50 during spikes. Overnight baseline QPS 2-3.

Token mix observed during trial:
- 70% short prompts (user messages + context) ~40-150 tokens each
- 20% medium-context templates + product doc snippets ~300-800 tokens
- 10% long-context summarization jobs extracted from product docs ~1500-3000 tokens
- Measured average tokens per request (trial): ~420 tokens (weighted) -> average tokens/sec during peak bursts ~31.5k tokens/sec at 75 QPS.

Customer requirements (explicit):
- Latency SLO: p95 < 350ms for short prompts, < 1.2s for medium, asynchronous OK for long jobs
- Concurrency target: support 120 concurrent activ
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 13: `qst_0048::metadata` · N=10000 · meta · priority=high

- **auto Hit@10:** `True`
- **LLM triage (optional):** label=`unsure` mode=`other`
- **LLM note:** llm_error: OpenAI HTTP 429: {
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-XSSQmWIx80t1tvfOCV1hxO4V on tokens per min (TPM): Limit 30000, Used 28245, Requested 2534. Please try again in 1.558s. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

### Question

In the engineering project about bridging a Responses-style API into a runtime event model with streaming and tool-call handling, what release version is this P0 ticket targeting?

### Gold document(s)

#### GOLD `dsid_f3af4a0db68c4b15983439460cc73006`

```
Responses API bridge: handshake mapping, partial streaming behavior and parity remediation roadmap

Deliver a pragmatic bridge that maps OpenAI Responses semantics into Redwood's runtime event model with minimum behavioral surprises for customers. Key focus areas: (1) handshake and initial metadata mapping (response.id, model variants, content-type headers), (2) streaming delta semantics vs event stream framing (role/author events, token deltas, partial structured outputs), (3) tool/function-calling interactions during mid-stream (when tool requests are emitted and how call results are re-integrated), (4) structured output attachments and schema enforcement for the Console and Optimize pipelines, and (5) safe fallbacks when parity gaps are detected (e.g., missing stop sequences, unknown tool schemas, or truncated tool responses). This ticket covers design, a reference implementation in the runtime translation layer, integration tests, and a staged canary rollout with observability hooks.
Handshake fields from an OpenAI Responses 'response.create' event are mapped to Redwood request/response metadata with 1:1 mapping for id, model, and role when present
Streaming deltas produce token-level events that preserve role boundaries and sequence ordering, verified by the stream-replay harness
Tool/function call events emitted by OpenAI Responses are translated to Redwood's tool-call API with preserved call_id, argument payload, and a deterministic re-integration path for tool results
Structured output attachments are parsed against provided JSON Schemas; invalid attachments are surfaced as 'structured-output-error' with graceful degradation to raw output
Fallbacks: when a parity mismatch is detected the runtime emits a compatibility warning metric and routes to a pre-configured fallback model variant without dropping requests
Integration tests (unit + e2e) covering 95% of mapped event permutations are added to CI and gate the canary rollout
Canary rollout demonstrates <1% increase in error budget burn and less than 80ms p50 additional latency on instrumented endpoints at 10% traffic shift
2025-02-18: Kickoff meeting with Runtime, SDK, Console and QA. Decided to prioriti
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_f3af4a0db68c4b15983439460cc73006` **← GOLD ID**

```
Responses API bridge: handshake mapping, partial streaming behavior and parity remediation roadmap

Deliver a pragmatic bridge that maps OpenAI Responses semantics into Redwood's runtime event model with minimum behavioral surprises for customers. Key focus areas: (1) handshake and initial metadata mapping (response.id, model variants, content-type headers), (2) streaming delta semantics vs event stream framing (role/author events, token deltas, partial structured outputs), (3) tool/function-calling interactions during mid-stream (when tool requests are emitted and how call results are re-integrated), (4) structured output attachments and schema enforcement for the Console and Optimize pipelines, and (5) safe fallbacks when parity gaps are detected (e.g., missing stop sequences, unknown tool schemas, or truncated tool responses). This ticket covers design, a reference implementation in the runtime translation layer, integration tests, and a staged canary rollout with observability hooks.
Handshake fields from an OpenAI Responses 'response.create' event are mapped to Redwood request/response metadata with 1:1 mapping for id, model, and role when present
Streaming deltas produce toke
…[truncated]
```

#### #2 `dsid_7c6f649b898746079dcd66302c50f8f8`

```
Typed output sentinel: compatibility & constrained-decoding benchmark

Objective: Build a reproducible benchmark and test harness to validate schema adherence across streaming, function/tool-calling, and constrained-decoding modes. This ticket covers test generation, CI integration, metrics, and a playbook for classifying failures. The goal is to detect regressions introduced by kernel changes, KV cache tweaks, or streaming reassembly logic. Scope excludes end-to-end customer prompts — we will use synthetic and anonymized seed prompts and property-based inputs.
A deterministic test harness that runs nightly and on PRs for runtime changes
Covering matrix: streaming vs non-streaming, toolcall interleaving vs no-tools, model family variants (Llama- and MPT-like), and constrained-decoder toggles
Pass/fail metrics: schema-pass-rate >= 99% on baseline models; categorized failure buckets for partial-JSON, extra-fields, missing-required-fields, and malformed-types
CI dashboard with historical trends and alerting when drop > 2 percentage points vs baseline
Runbook describing rollback and temporary decoder-backoff policy to apply in flight
Harness design: 1) Corpus: 1k templated prompts + 50
…[truncated]
```

#### #3 `dsid_8db16dd149b74972ae947d5525043b45`

```
OpenAI Responses compatibility: mapping plan and parity gaps for streaming, function/tool calling, and structured outputs

Analyze and implement a pragmatic compatibility layer that maps Redwood's Core API semantics to the OpenAI Responses API surface. Focus areas: streaming semantics, tool/function calling ergonomics, and structured output (JSON schema) parity. Produce a shim in the request gateway that preserves Redwood guarantees (latency SLOs, typed tool args, KV/cache behavior) while maximizing compatibility for customers migrating existing OpenAI Responses integrations.
Gateway exposes a toggle 'openai_responses_mode' that enables request/response transformation to/from OpenAI Responses shapes
Streaming: server-sent events produced to clients mimic OpenAI delta stream format (role/content/delta and finalization events) for text + tool-invocation sequences
Function/tool calling: incoming OpenAI-style function_call requests are mapped to Redwood tool invocation model with parameter validation, and tool responses stream back using expected events
Structured outputs: Redwood’s structured output config supports OpenAI-style JSON schema validation and validation errors are surfaced
…[truncated]
```

#### #4 `dsid_1c9140e818384efca371611858fffcdf`

```
Launch runbook: SDK + API surface (function-calling, structured output, streaming) — docs & samples handoff

Goal: Coordinate cross-team launch activities for the SDK and API surface additions that enable first-class function calling, structured output schemas, and streaming across supported SDKs (python, js, go). Deliverables: launch runbook, finalized release notes, canonical docs, 3 sample apps (chat + tool-calling, structured invoice parser, streaming-transcribe example), and CI smoke tests. This ticket centralizes orchestration tasks, assigns owners for each deliverable, records trade-offs, and tracks blockers for the release cadence.
Finalize release notes draft and canonical changelog entry (owner: Priya) — Due 2026-03-08
Publish SDK sample apps to samples.redwood.ai repo with README and minimal deploy scripts (owner: DevRel) — Due 2026-03-10
Docs: Expand function-calling guide with error handling, retries, and structured output examples (owner: Docs: Lara Singh) — Due 2026-03-09
Engineering: Verify streaming semantics and backpressure handling in Python SDK; create compatibility matrix for server-side streaming (owner: Mateo Chen) — Due 2026-03-07
QA: Create end-to-end smok
…[truncated]
```

#### #5 `dsid_a3954582c60442ddb1924caa03bed22e`

```
Contract evolution runbook for streaming + tool interfaces and structured outputs

Objective: produce an actionable runbook and deliverables to evolve the Core API contract for streaming responses, tool/function calling, and structured outputs with minimal customer disruption. Scope covers behavior flag orchestration, graduated deprecation windows, deterministic regression harnesses, and telemetry-driven rollback criteria. Non-goals: changes to model weights or model-internal tokenization algorithms, and client SDK refactors beyond thin compatibility shims. Deliverables: (1) runbook for staged toggles and canary criteria, (2) migration guide for clients and partners, (3) regression test suite and replay harness, (4) telemetry dashboards and alert thresholds, (5) sample SDK compatibility adapter. Rationale: recent experiments to tighten structured-output schema and to normalize streaming chunk headers broke a subset of legacy clients in shadow runs. We need a repeatable, low-risk path to roll forward these contract changes while collecting guardrail metrics and offering clear migration steps for integrators.
Runbook published and reviewed by Eng/UX/SRE/Legal
Canary flow implemented 
…[truncated]
```

#### #6 `dsid_e48cba98a7764fa8bc47f32f2837b0b6`

```
Sync sheet & cut-criteria framework for API/Console/Runtime release

Create a single-source-of-truth sync sheet and decision framework that defines milestone gating, scope-lock rules, and cut criteria for the combined API / Console / Runtime release. This ticket coordinates who publishes release notes, owners for each feature/product area, cross-team go-to-market tasks (docs, marketing assets, support runbooks), and a lightweight escalation path for last-minute quality regressions. Deliverables: 1) canonical sync sheet (CSV/Drive), 2) cut-criteria checklist with acceptance examples, 3) release notes owner matrix and template, 4) kickoff notes and communication calendar.
Canonical sync sheet exists in Drive with read/write access to PM/ENG/Design/Docs leads
Cut criteria checklist (pass/fail with examples) approved by ENG, PM, and QA
Release notes owner matrix assigned for each feature and verified with owners
GTM tasks and owners (docs, marketing, support) are listed with due dates
A communication calendar and single release coordinator are named
Scope lock date set to 2026-03-18 23:59 UTC; only P0 regressions or security fixes allowed after
Cut criteria includes: automated e2e pass
…[truncated]
```

#### #7 `dsid_e813c7bf78644243a06f834d0ab92a78`

```
continuous-json-safety-truncation-retries-procedures

Problem: Streaming LLM responses that encode structured JSON objects can be truncated mid-object, contain escaped characters that are interpreted differently by downstream tools, or be retransmitted on retry leading to duplicate partial objects. This ticket defines a pragmatic, backward-compatible set of procedures for the Redwood API and SDKs to: (1) preserve structured output semantics for consumers (including function/tool callers), (2) minimize latency and cost regressions, and (3) enable safe retries and resumptions across client and server implementations.
We have sporadic customer reports where streaming responses used for tool calling or JSON ingestion either fail JSON parsing on the client, produce duplicated partial objects after network retries, or lose critical escape sequences (e.g., embedded JSON strings, backslashes). Existing tickets touch on framing and resume but don't cover a complete, deployable procedure that balances latency and correctness across hosted, dedicated, and Private deployments. This work intends to standardize the approach so SDKs and server-side routers implement interoperable semantics.
Defin
…[truncated]
```

#### #8 `dsid_d6777ded64504da3813a6b6871c7766f`

```
Live Stream Assertor, Telemetry, and Fallback Playbook for Constrained-Decoding

Add a runtime 'Live Stream Assertor' component that continuously validates emitted token streams against active JSON-mode schemas and constrained-decoding expectations. The assertor will (1) emit structured telemetry when deviations are detected (token-level mismatch, truncated objects, unexpected terminals), (2) apply configurable remediation policies (retry with permissive decoder, invoke truncation-reassembly, fall back to synchronous full-response decoding, or route to a compatibility model), and (3) log minimal repro artifacts (prompt + stream prefix + model metadata) to a guarded bucket. This ticket covers the implementation of the assertor hook in the streaming pipeline, the telemetry schema and dashboards, a small policy engine for fallback decisions, and the accompanying e2e smoke and chaos tests that simulate partial streams and interleaved tool-calls.
1) Assertor emits telemetry (stream_assertor.event) on mismatch with fields: error_type, token_index, model, route, and schema_id. 2) Fallback policy executes and returns a valid JSON payload or a documented failure path for >95% of injected pa
…[truncated]
```

#### #9 `dsid_bfd2d47aab5449e3b43866cf38aa5cf5`

```
Streaming fragment reassembler and typed-event surface for Python SDK

Problem: In long-running streaming chat sessions we frequently observe tokens and structured events arriving split across transport boundaries (SSE/frame/chunk). This makes it hard for application code to consume atomic semantic events (e.g., function_call start/arg fragments, structured JSON patches, tool call boundaries) and to support idempotent resume after retries or reconnects.

Goal: Implement a resilient fragment reassembly layer and a typed streaming-event surface in the Python SDK that: 1) reassembles delimited/fragmented payloads (token fragments, JSON fragments, function_call arg fragments), 2) yields strongly-typed events (Delta, Fragment, Patch, FunctionStart, FunctionArg, FunctionEnd, Done, Error), 3) exposes checkpoint tokens and resume semantics to enable safe retries and reconnects, 4) emits telemetry for fragmentation metrics and reassembly latency, and 5) keeps the developer ergonomics simple (async iterator + optional callbacks).

This ticket covers: design, prototype implementation, unit + integration tests against the streaming test harness, and a small migration guide for existing custome
…[truncated]
```

#### #10 `dsid_b44e9b54ae344067ab33fa45b234026a`

```
SDK/API Bridge: launch roadmap, sample kits, telemetry mapping, and rollback runsheet

Objective: Coordinate a cross-functional launch for the SDK + API surface that covers function-calling, structured output, and streaming. Deliverables: (1) language-specific sample kits (Python/JS/Go) that demonstrate function calling + structured output + streaming fallbacks; (2) consolidated release notes template and public-facing changelog entries; (3) telemetry mapping for SDK metrics to Console dashboards; (4) a rollback runsheet with safe fallback routes and canned comms; (5) an internal launch ritual checklist and post-launch evaluation plan. This ticket covers orchestration and handoffs across Docs, SDK, Runtime, Design, and Growth teams.
Public release notes drafted and approved by Legal & Communications
Sample kits (Python/JS/Go) published in the samples repo with README and runnable demo scripts
Telemetry mapping doc created that maps SDK events to Console charts (latency, token counts, stream drop rates)
Rollback runsheet tested in a dry-run with ENG on-call and Product Ops
SDK/Server compatibility matrix validated by Runtime team and added to release notes
Launch checklist completed
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 14: `qst_0053::metadata` · N=40000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks do not address the specific question about metric label allowlist and caps for shadow traffic metrics, indicating a lexical mismatch. The gold chunk is non-empty but off-topic, while the retrieved chunks are also non-empty but irrelevant to the question, leading to a low relevance score.

### Question

In the late-January 2025 technical deep dive with FinBank about private disaster recovery and backup restore, how long was the call in minutes?

### Gold document(s)

#### GOLD `dsid_c3be99dbca144db488c037dd2f0831ef`

```
FinBank x Redwood — Private DR + backup/restore technical deep dive

FinBank walked through DR requirements for a Redwood Private VPC deployment (plus a smaller, restricted environment with limited egress). Key asks: enterprise RPO/RTO targets, deterministic restore into a clean cluster, encryption with customer-managed keys, and evidence/validation of restores. Redwood described the Day-2 toolkit direction: control-plane backups (manifest + encrypted artifact), optional scheduled backups via Helm CronJob, least-privilege S3+KMS patterns, and post-restore validation/smoke tests. Discussion covered whether Kubernetes resources are included (Redwood will back up Redwood control-plane/state + critical Helm values; Kubernetes/etcd snapshots are separate and only for cluster-level recovery), handling of secrets (references vs secret material), KMS/HSM constraints, and offline/air-gapped-ish restore workflows (signed bundles, no outbound calls, local checksum verification).
FinBank target RPO/RTO and DR scenarios (cluster loss vs region outage)
Backup scope: control plane state, config DB, object store references, routing/tenant config
Kubernetes backup tools (Velero) vs Redwood snapshots; etcd snapshot caveats
Encryption: envelope encryption, KMS key ownership, rotation, and KMS outage behavior
Air-gapped / restricted egress operations: signed artifacts, offline docs, deterministic bundles
Restore validation: smoke tests, health checks, audit log continuity, and evidence artifacts
FinBank (Tom Reyes) - Send current target RPO/RTO and DR runbook constraints (including maintenance windows) - due 2025-02-03
FinBank (Nina Shah) - Confirm KMS/HSM requirements (AWS KMS vs CloudHSM, key policies, allowed cryptographic operations) - due 2025-02-03
Redwood (Colin O'Donnell) - Share reference architecture for S3+KMS backup bucket + least privilege IAM and staging-restore workflow - due 2025-02-05
Redwood (Hanae Suzuki) - Share Redwood encryption approach summary (envelope encryption, key rotation expectations, what happens if KMS is unavailable) - due 2025-02-05
Redwood (Sean Gallagher) - Provide a sample restore validation checklist + what logs/metrics are produced for eviden
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_88ac70470c174934b394dec360f60a62`

```
Orion AI disaster recovery, SSO/KMS & SLA tabletop

Tabletop-style walkthrough of Redwoods incident response and BCDR for a potential Private deployment. Covered SSO and RBAC mapping, KMS/HSM options for customer-managed keys, retention/audit log access, RTO/RPO tradeoffs (warm-standby vs active-active), escalation matrix and SLA credit mechanics. Action items: share redacted SOC2, draft runbook for a cold failover test, propose warm-standby topology + cost estimate.
SOC 2 / ISO artifacts
RBAC and SSO mapping (SAML/SCIM)
Audit logs & retention windows
Encryption & KMS (customer-managed keys vs Redwood-managed)
BCDR: RTO/RPO goals, warm standby vs active-active
Escalation and on-call matrix (PagerDuty/phone)
SLA credits and uptime calculation
Private deployment network requirements
Ethan to send redacted SOC 2 Type II report and ISO 27001 scope - due 2026-02-24
Samira to draft a proposed warm-standby topology and cost delta for Orions expected QPS - due 2026-03-03
Mark to share current SSO/SAML metadata and RBAC matrix - due 2026-02-25
Schedule a 90-minute deep dive runbook session (technical playthrough) - tentatively 2026-03-05
Ethan: send redacted compliance artifacts (SOC2/ISO) 
…[truncated]
```

#### #2 `dsid_aa49078d78d24048a24dc79743033225`

```
Multi-tier fallback and SLA alignment — discovery with Archipelago Ventures

Discovery focused on multi-tier fallback strategy (hosted -> dedicated -> private fallbacks), realistic SLA targets and contractual carve-outs for planned maintenance, and technical validation needs (prefix cache priming, multi-region KV cache consistency). Customer wants clear economic tradeoffs and an ops playbook for graceful degradation.
Hosted vs Dedicated vs Private fallback policies
Multi-region steering and latency tradeoffs
SLA targets and carve-outs (planned maintenance, force majeure)
Cache consistency and prefix/KV cache behavior on failover
Canary and rollback strategies
Security/compliance gating for Private deployments
[00:00] Maya (AE): Hey everyone, thanks for joining, quick intros — I'm Maya from Redwood, Diego and Lena on the line from our solutions team.
[00:07] Ravi (Archipelago/CTO): Thanks, Maya. I'm Ravi, CTO, Nora leads platform, Samir is our SRE, and Elise is here to listen from legal.
[00:15] Maya: Great. Goal for today is to understand your availability needs and how you'd like Redwood to behave in partial failures, multi-region issues, and what SLA commitments you need in contr
…[truncated]
```

#### #3 `dsid_d3e3da235df940bca76d3202bac77ec5`

```
Security governance, uptime SLA & escalation workshop with Bluecliff Capital

Meeting Start: 2026-09-28 16:00 PDT
Duration (recorded): 62 minutes
Attendees: Maya (Redwood AE), Connor (Redwood SE), Diego (Redwood SE), Anya (Bluecliff CISO), Marcus (Head of Platform), Priya (Legal), Evan (SRE)

Summary: Quick sync to validate Redwood's SOC 2 posture, KMS/encryption options for private deployments, and to walk through incident escalation and BCDR runbook expectations. Bluecliff wants clear RTO/RPO numbers and an SLA exhibit for Dedicated deployment; also needs assurance on audit log retention and SSO onboarding timeline.

00:00:06 - Maya: hey everyone, thanks for joining. quick agenda, we'll do a short overview of our compliance artifacts, run through SSO/RBAC options, then Connor will take you through the planned RTO/RPO and failover model. save time at end for priya's procurement questions.
00:00:22 - Anya: thanks maya, yeah high level we're prepping for internal audit in q1 and procurement wants the SLA and key security docs by mid-october.
00:00:35 - Marcus: also want to understand impact on our latency profiles if we route to dedicated vs hosted fallback. cost vs availability tra
…[truncated]
```

#### #4 `dsid_4175fd65c25a4c79b9cf3090a11eb870`

```
Incident Response, BCDR & Escalation Review - Acme Retail Systems

Meeting header: 2025-04-10 15:00 PDT / Duration: ~63 minutes
Attendees: Sophia Park (Redwood AE), Daniel Kim (Redwood SE), Rhea Patel (Redwood CRE); Priya Shah (CISO - Acme), Miguel Torres (Head Infra), Liam O'Connor (Compliance), Dana Liu (Platform Ops), Ethan Brooks (SRE)

[00:00] Sophia Park: Hi everyone, thanks for joining. Quick roll call -- Sophia here, AE at Redwood. Dan and Rhea from the infra/ops side.
[00:15] Priya Shah: Hey all, Priya here. We have our infra and compliance folks on the call, want to make sure we cover incident response, BCDR expectations, and escalation.
[00:25] Daniel Kim: Great, thanks Priya. Today we want to walk through how Redwood handles incident detection, triage, escalation, RTO/RPO targets for both hosted and dedicated deployments, and what audit artifacts we can provide for your compliance team.
[00:40] Miguel Torres: Good. We run a hybrid stack; most of our workloads are in us-west on AWS but we have some EU data residency requirements for checkout data. We'll want to understand how Redwood's private deployment and network isolation options work with our VPC and KMS.
[00:55] Rh
…[truncated]
```

#### #5 `dsid_9ff022b2877240ff86f5fb3efc98ac29`

```
Strategic Health & Burn Council - Northpoint Health Q1

Quarterly health check focused on usage trajectory, burn rate concerns, and capacity planning for Q2. Northpoint noted a 48% month-over-month increase in inference volume driven by new clinical summarization feature. Finance flagged higher-than-expected variable spend. Redwood proposed a Dedicated sizing recommendation, batching/kv-cache suggestions, and a pilot for quantized model variants to control token cost while meeting p95 latency. Action items assigned and follow-up technical deep dive agreed.
usage growth and projection
cost / burn rate and finance guardrails
latency SLOs and p95 targets
Dedicated vs Hosted tradeoffs
VPC/private deployment considerations
model rollout and quantization pilot
observability and runbooks
Maya Chen: Send forecast spreadsheet and pricing band breakdown (due: 2026-03-11)
Diego Alvarez: Produce lightweight test harness and latency spreadsheet for 512/2048 token profiles (due: 2026-03-12)
Lena Park: Share recent traffic patterns and p95 latency targets (due: 2026-03-09)
Priya Menon: Approve finance review cadence and set spend ceiling for Q2 pilot (due: 2026-03-15)
Maya to share month-by-month
…[truncated]
```

#### #6 `dsid_cc8d0c4da15b494badd135e32a27fa03`

```
Resilience, SSO/KMS Orchestration & SLA Tabletop — Northbridge Systems

Meeting header:
Date: 2027-03-28 16:00 UTC — Duration: 58m
Attendees: Jordan Park (Redwood AE), Maya Chen (Redwood SE), Liam O'Connor (Redwood SE) — Evan Riley (CISO), Priya Malhotra (Head Cloud Eng), Samir Patel (SRE), Olivia Zhang (Compliance)

Summary:
Quick tabletop focused on SSO/SAML, KMS/HSM orchestration, audit log retention, and the BCDR escalation ladder (RTO/RPO specifics). Walkthrough of a simulated region outage and how Redwood fallbacks (model variants, dedicated vs hosted) and private KMS behave.

Topics covered:
- SSO/SAML + RBAC mapping to Redwood Console roles
- KMS integration patterns (bring-your-own keys, HSM-backed rotation)
- Audit logs, retention, and export for auditors
- RTO/RPO expectations and multi-region failover sequence
- SLA escalation chain and oncall handoffs

Transcript:
[00:00] Jordan: hey everyone thanks for joining, quick roll call, and we'll kick off — we planned a tabletop — i think priya you were going to outline current rto targets?
[00:22] Priya: yeah um hi, thanks. so currently our app teams are at RTO 2 hours and RPO 15 minutes for core services, but for ai inferenc
…[truncated]
```

#### #7 `dsid_c5c7dddf71a444fda03fa312accb9e2f`

```
Rapid rollback rehearsal and chaos simulation handoff

Redwood-led rehearsal to validate rollback procedures after last week's edge cache eviction wave. Agreed on a short rollback playbook, telemetry checks, and a customer-exec chaos sim scheduled. Security wanted KMS audit and SSO caveats clarified. Next step: SE to run a dry-run and share runbook updates and benchmark script.
Meeting header: 2026-02-19 15:00 PST — duration ~52 minutes. Attendees: Marta, Samir, Rae (Redwood) — Lina, Marcus, Priya, Diego (BlueFork).\n\n[00:00] Marta: Hey everyone, thanks for jumping on, we wanted to use this call to run through the rapid rollback rehearsal after that eviction wave last week, and hand off the chaos sim plan. \n[00:18] Lina: thanks Marta, yeah last week was rough, we saw big token backpressure and KV cache thrash — some of our endpoints started timing out. \n[00:30] Samir: quick correction, I think some of the transcripts flagged it as \"KV cash\" last time, it's KV cache, sorry, but yes we saw eviction wave on the edge caches. \n[00:45] Marcus: the important bit for us is minimizing blast radius. We want an automated rollback that restores stable model variant and ramps requests dow
…[truncated]
```

#### #8 `dsid_f03e9c26da514f7fa2e33fccbb9fda9d`

```
Fallback policy stress test intake - discovery with Equinox Labs

Meeting header:
Date: 2026-08-27 14:00 UTC
Duration: ~47 minutes
Attendees: Maya Chen (Redwood AE), Diego Alvarez (Redwood SE), Samira Khan (Equinox Head of Platform), Jonas Reed (Equinox SRE), Priya Patel (Equinox Security), Alex Moreno (Product)

Summary:
Quick intake to map Equinox's reliability targets and design a staged fault-injection stress test for fallback policies across hosted/dedicated/private deployments. Main concerns: cascade failures during region outage, cold-start latency for fallback variants, KV cache consistency during steering, and compliance constraints for private deployment.

00:00 - Maya (Redwood): hey everyone, thanks for joining. can you hear me ok?
00:05 - Samira (Equinox): yep, loud and clear. thanks for setting this up. we've got about 45 minutes.
00:12 - Maya: great, we wanted to walk through your goals for a stress test — like what you mean by "fallback" and what success looks like. diego and i will take notes and propose next steps.
00:25 - Jonas: our context — we run chat assistants for clinical intake, high p99 SLA expectation. real time-ish. when a region gets noisy we need autom
…[truncated]
```

#### #9 `dsid_0400240ded8b4d1e8a5ecff2b3bffa11`

```
Regional fallback strategy discovery with Helios Analytics

Meeting header: 2025-11-19 15:00 UTC | Duration: 46m | Auto-recorded by Fireflies
Attendees: Maya Chen (Redwood AE), Diego Alvarez (Redwood SE), Sarah Patel (Helios, Head of ML), Liam O'Connor (Helios, Platform Eng), Olivia Grant (Helios, Security).

Summary: Quick discovery focused on reliability, multi-region failover, and incident-tolerance expectations. Customer wants clarification on Hosted vs Dedicated tradeoffs for graceful degradation, cross-region replication, and SLA commitments plus auditability requirements. Agreed to run benchmarks and share SLA artifacts and pricing.

Topics: reliability goals, fallback topologies, regional routing, SLA definitions, security/audit needs, pilot next steps.

[00:00] Maya Chen: Hi everyone, thanks for joining, I think we have about 45 minutes. Quick intros?
[00:08] Sarah Patel: Sure, Sarah here, Head of ML at Helios, we build forecasting models for energy markets, main concern is inference availability and data residency when models are used in EU.
[00:16] Liam O'Connor: Liam, platform eng, I'll be owning rollout, orchestration, network stuff.
[00:19] Olivia Grant: Olivia, secur
…[truncated]
```

#### #10 `dsid_909c474ff72047428ba5dcf0f03844a3`

```
ForestFall degradation fallback & resilience sprint planning

Meeting header:
- Date/Time: 2026-05-20 14:30 UTC
- Duration: ~60 minutes
- Attendees: Maya (Redwood AE), Arjun (Redwood SE), Sofia (Redwood CSM), Lena (ForestFall SRE), Daniel (VP Eng), Aisha (CTO), Tom (oncall), Priya (Product)

Summary:
- Follow-up on the 2026-05-12 long tail latency surge impacting interactive chat sessions. Align on short-term fallbacks, runbook updates and scope a 2-week resilience sprint to harden KV cache, autoscaling, and circuit breakers. Plan a bench test that mirrors ForestFall's mixed small-chat + embedding workload.

Topics:
- Root-cause hypotheses (KV cache miss storms, cold KV partitions, priority routing imbalance)
- Short-term mitigations: prefix caching, emergency fallback model, throttling at edge, autoscale policy adjustments
- Long-term hardenings: pinning critical endpoints to dedicated capacity, improved observability (token-level traces), and runbook automation for fallback rollouts

Transcript:
[00:00] Maya (Redwood): ok hey everyone thanks for joining, uh quick check - is this still a good time?
[00:05] Lena (ForestFall): yeah good here, we're a bit stretched but we pushed folk
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 15: `qst_0054::metadata` · N=100000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant but do not directly address the specific question about the lattice scheduler rollout. The gold chunk is on-topic and non-empty, but the retrieved chunks lack direct relevance to the question, indicating an embedding near miss.

### Question

Who is listed as the owner of the draft internal notes document about an onramp for a claims connector involving a private deployment in an AWS VPC?

### Gold document(s)

#### GOLD `dsid_f8b3bf0c730f44f4a24981a3d4cd9c49`

```
Mistral Claims — connector onramp notes

Call date: 2025-02-13 - intake call (30m)
Attendees: Marta Lopez (Mistral product), Tyrell Vaughn (Mistral infra), Priya Soni (Redwood SE), Daniel Kim (Redwood SE), Ethan Moore (Redwood SRE)

Purpose: quick technical intake to capture integration constraints for Mistral Claims' plan to route incoming claim intake (documents + short text forms) through a Redwood Private deployment in their AWS VPC. They want model-assisted triage, PHI redaction, simple QA checks, and embedding indexing for retrieval.

High-level ask from customer:
- Replace current rules+human triage with model-first triage for ~30k claims/month initially, 1500 concurrent daily users across geos.
- Keep all PII/PHI inside their VPC; no token or verbatim data to leave their account.
- Provide configurable redaction step (automated, with human-in-loop exception queue).
- Low-latency critical for frontline agents (95th pct < 350ms for short prompts).
- Batch/async pipeline for bulk document ingestion (PDFs/Images via OCR).

Notes / raw capture from conversation:
- Infra: Mistral has an AWS-only footprint in us-east-1 and uses private subnets with strict egress rules. They run Kinesis streams + a legacy SFTP ingest. Tyrell emphasized that any egress to a public Redwood control plane is a regulatory blocker unless we run Private entirely in their VPC.
- Security: Must integrate with their KMS (customer-managed CMK) for envelope encryption. HSM not immediately required but flagged for later SOC discussion.
- Audit: 2 year retention for audit logs, redaction metadata must be exportable to their SIEM.
- Throughput: Peak ingestion bursts ~120 r/s for small prompts during shift changes. Average token length for triage prompts ~80 tokens but full-document OCR outputs can be 6–8k tokens.
- Attachments: PDFs up to 25MB. They expect us to recommend a pattern to chunk OCRed text and keep a pointer to original S3 object.
- Latency SLO nuance: agent UI needs interactive responses for short prompts; longer summarization jobs can be async w/notification.
- Cost sensitivity: They want an initial PoC to run for 6 weeks with cost reporting and a rollout plan to Dedicated reserv
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_10daee01b2fc4bf98c5a75569af7aabd`

```
CedarGate VPC Solutions

Account lead: Maya. CTO (E. Holloway) is focused on a fully private VPC deployment — model traffic must not traverse public internet. Primary ask: PrivateLink endpoints or VPC peering with static egress IPs for allowlisting. Must integrate with their KMS (AWS KMS with CMKs) and optionally HSM for key custody. Retention: audit logs shipped to their S3 with 7+ year retention and immutable WORM policy. Compliance: SOC2 in progress, pursuing ISO27001; require SAML SSO via Okta and SCIM provisioning. Data residency: US-East only for production. Performance targets: p50 latency <150ms for embeddings, steady-state throughput 40-60 req/s for chat-heavy assistant. Cost sensitivity: medium — willing to pay premium for strict isolation and SLAs. Quote from CTO: "No cross-tenant network egress; we need predictable IPs and private endpoints." Notes on network: prefer AWS PrivateLink to avoid route table changes, but open to VPC peering if Transit Gateway simplifies routing. Firewall rules: deny all egress except Redwood endpoints; egress controls must include DNS policies and NAT restriction. IP allowlists: require static egress IPs or NAT with Elastic IPs for outbound 
…[truncated]
```

#### #2 `dsid_a20051645422436ea586508a46255fd0`

```
StrataGuard Analytics

2025-11-12 - Lead created from AWS re:Invent contact; initial interest flagged for private deployment due to customer data regs.
2025-12-04 - Intro call (Jordan Lee) — business use: agent summarization + sensitive doc search for wealth management clients. Priority: no raw customer text allowed to leave their VPC.
2026-01-15 - Security questionnaire submitted; legal flagged KMS BYOK + audit retention as must-haves.
2026-01-26 - PoC scope agreed: sandbox in their dev VPC, routing via PrivateLink preferred; evaluate latency impact and egress cost delta vs dedicated peering.
2026-02-03 - SE deep-dive (Priya) — discussed network choices: AWS PrivateLink (preferred), Transit Gateway peering (fallback), and on-prem connectivity via Direct Connect. Documented firewall rule set and requirement for restrictive egress (only to Redwood endpoints/IPs).
2026-02-10 - Call with infra (ff_20260210_4762) — infra wants explicit /28 IP ranges for allowlist, TLS + mTLS for control plane, and assurance that KV cache won't persist PII outside customer KMS envelope.
2026-02-12 - Legal asked for written KMS integration flow (BYOK), key lifecycle controls, and sample audit logs for re
…[truncated]
```

#### #3 `dsid_cd9f545c273e4883be9f8d52d267466d`

```
Third-Party Integration Readiness and Compatibility Guidelines for Private Deployments

Summary:
This document defines the integration readiness requirements and compatibility guidelines for third-party systems (connectors, proxies, IAM, observability vendors, and storage backends) used with Redwood Private deployments (VPC and on-prem). It focuses on the recommended integration sequence, minimal technical constraints, acceptance tests, and rollback hooks to reduce field failures during installation and Day-2 operations.

Scope and target audience:
- Scope: Tenant-facing connectors and external systems that Redwood operators or customer operators integrate with Redwood Private control plane and runtime. This includes: identity providers, KMS/HSMs, object stores, proxies/load balancers, SIEM/obs vendors, and cloud-native service integrations.
- Audience: Field engineers, SREs, customer platform engineers, solutions architects, and professional services.

Key principles:
1) Integration order matters: verify identity and network connectivity before enabling data plane flows.
2) Fail fast with safe defaults: connectors must support non-destructive mode for initial validation.
3) Observ
…[truncated]
```

#### #4 `dsid_4bba2fec619f42a9bf29b58be2cded25`

```
Pallisade Guardian Cloud

CRM notes:
- 2026-01-10 inbound: CTO (L. Moreno) initial outreach re: private VPC for claims automation. Wants strict residency controls for PII.
- 2026-02-03 AE intro call (Morgan) + SE (Devon). Discussed architecture options: VPC peering vs. PrivateLink. Customer preference: VPC peering with strict egress rules.
- 2026-02-18 security deep-dive w/ CISO (quote paraphrase): "We need an auditable chain for every inference – keys, logs, and retention policy are blockers." Fireflies ff_2026-02-18_1302 attached.
- Submitted initial SIG/CAIQ v1 on 2026-02-22. Security team returned with 34 follow-ups (encryption, subprocessor mapping, pen-test cadence).
- 2026-03-02 workshop: reviewed shared-responsibility matrix draft. Action: Redwood to provide canonical matrix mapping (network, disk, app logs, caching). Fireflies ff_2026-03-02_0915.
- 2026-03-05 legal requested full subprocessor list + SOC2 Type II report and ISO cert copies. Drive links shared.
- POC plan: 2-week Private VPC sandbox -> KMS cross-account key integration -> audit log ingestion into customer's SIEM -> performance runbook for 99th percentile latency.
- Customer comment: "If we can show encryptio
…[truncated]
```

#### #5 `dsid_85593be116884060a4505b103ff3e897`

```
Archipelago Enterprise Solutions

POC for private VPC deployment. Must integrate with customer KMS, deliver audit logs to Splunk, enforce SSO via SAML, meet US-only data residency for PHI-adjacent datasets. Low tolerance for fallbacks to public endpoints. Prefer quantized open models for cost control. Need canary rollback and A/B routing during rollout.
Deploy Redwood Private control plane in customer VPC (GKE) using provided Terraform + Helm. Validate: model serving (gpt-like open model), prefix/KV cache functionality, KMS-integrated envelope encryption, audit log delivery to customer's SIEM, e2e load test at 100rps with <200ms p99. Deliver runbook and handoff docs.
Kick off POC in customer VPC: deliver Terraform modules + Helm charts, run integration tests, get sign-off from security by 2025-02-21.
legal review of data residency clause
customer network ACLs require adjustment
KMS policy cross-account role pending
billing code for Dedicated/Private not approved
2025-01-10 - Lead (Ethan) opened opportunity after intro call
2025-01-15 - Security intake form submitted (Anita)
2025-01-22 - Technical deep-dive (Fireflies ff_2025-01-22_Archipelago_POC)
2025-01-30 - Legal & compliance ca
…[truncated]
```

#### #6 `dsid_573ca1fc195e450e85e3f10d1a068cf6`

```
HelmBridge Healthcare

Account background:
- Enterprise healthcare SaaS provider, strong on PHI workflows. Interested in on-prem/VPC option early (HIPAA concerns).
- Initial intro 2025-09-12 (AE: Priya). Demo delivered 2025-10-05 (SE: Marcus) — focus on low-latency clinical assistant and secure embeddings for document search.
- 2025-11-20 security kickoff w/ InfoSec (paperwork: NDA + data flow diagram). Requested SOC2 + HIPAA articulation and KMS/HSM details.
- POC (2025-12-18 -> 2026-01-08): small clinical assistant POC using hosted variant; we demonstrated latency and cost estimates. POC passed functional tests but security team required VPC endpoints + SIEM integration.
- Procurement review 2026-01-25: finance ran TCO vs hyperscaler-managed endpoints. Their pricing model (with committed AWS discounts) made AWS Bedrock managed endpoints ~25-30% cheaper operationally given no additional ops headcount.
- Final decision 2026-02-10: chose AWS native managed endpoints + PrivateLink for data in transit; quote from CTO: "We can't add a new ops surface right now — exec mandate is to consolidate on existing cloud services."
- Post-mortem notes: timeline slipped on private deployment timel
…[truncated]
```

#### #7 `dsid_01fbf5f87c9242aca7b31e4f0d0c10a7`

```
Pinnacle Vaultworks

CRM notes (shorthand, partials):
- Enterprise FS customer, heavy compliance requirements.
- Primary ask: private VPC deploy with strict encryption posture + key management integrated into their existing AWS KMS/HSM cluster.
- In-transit: require mTLS between customer app -> Redwood private control plane -> inference nodes; mutual certs and cert rotation policy.
- At-rest: AES-256 disk encryption + envelope encryption required. Customer insists on CMKs they control; Redwood must support customer-managed keys with HSM-backed KMS.
- Key rotation: legal/security want rotation cadence 90 days for ephemeral keys, annual rotation for master CMK; must support scheduled rotation and zero-downtime rewrap.
- Secrets mgmt: prefer HashiCorp Vault integration for node join secrets and short-lived tokens. Need vault auth flow documented.
- Audit logging: immutable audit trail for all model invocations containing metadata (no PII). Logs must be forwardable to customer's logging endpoint (S3 + Kinesis) and retain for 7 years for compliance team.
- Data residency: all inference nodes must be in us-east-1, no cross-region replication.
- Quote from CISO: "We can't accept provider-
…[truncated]
```

#### #8 `dsid_c6fec429e5104024a0c749fa14664ab1`

```
Harborline Insurance Tech

- Initial discovery 2025-11-12: scope = claims automation + internal policy drafting. Highly regulated, must keep PII in-region.
- Quote: "we need strong audit logs and residency — cannot ship PII to hosted multitenant without contractual guarantees."
- Submitted security questionnaire 2025-12-02; CR team pinged for clarifications 2026-01-05.
- Architecture review w/ infra (Lisa Moreno, Head of Infra) 2026-01-14: asked about VPC/private control plane and KMS integration. Team requested on-prem option for sensitive workloads.
- Shared dedicated pricing and POC scope 2026-01-20 (pricing deck link above).
- Procurement flagged Q1 budget freeze internally 2026-01-28 — asked to hold formal purchase until April.
- AE followed up 2026-02-15; initial reply then silence. Multiple pings; no calendar replies, email opens but no replies.
- Likely outcomes: 1) budget deferral to next quarter; 2) choosing competitor (BigCloudAI) who offered temporary hosted-only pilot; 3) internal headcount churn — reported that Mark Reynolds (project champion) moved org 2026-02.
- Current status: stalled. Security team still has 2 outstanding items: HSM-backed KMS design + SOC2 eviden
…[truncated]
```

#### #9 `dsid_d98cd5211d01496bbf4d6f650a6f1316`

```
Seacliff Private Inference

Confirm VPC topology doc + KMS cross-account key policy; security team to sign NDA; schedule network peering test
legal: data residency clause for EU + APAC
network: restricted egress policy (no internet from worker subnets)
procurement: budget approval for Dedicated nodes
2026-02-25 Lead created from inbound form (requested private deployment)
2026-02-26 Intro call (AE Jordan) — infra + infosec on call. Customer: 'need everything in eu-west-1 and ap-southeast-1; cannot route traffic over public internet',
2026-03-02 Security questionnaire v0.1 returned (attached) — asked about audit log retention, KMS BYOK, and separation of control plane
2026-03-05 Architecture workshop — proposed model: private control plane with cross-account IAM role, worker ENIs in customer subnets, VPC endpoints for S3 and ECR, NAT only for control-plane egress through approved firewall
2026-03-08 Fireflies meeting — demo of routing/fallback rules; discussed canary rollout inside private VPC; action: produce network diagram and KMS policy draft
2026-03-10 POC scoping call — agreed to 2-week POC limited to eu-west-1, 2x A10G workers, KV cache disabled initially to simplify network

…[truncated]
```

#### #10 `dsid_3c58c6154d1e40ceb3927a04d14f51ed`

```
Veridian RegTech Labs

Enterprise EU Private VPC deal; high security bar. Next: network workshop + finalize SOW.
EU-only data residency for all inference and logs
Customer-managed KMS with HSM-backed keys and clear cross-account role to Redwood infra
Audit logs exported to customer SIEM (Splunk) with guaranteed retention controls and ACLs
Network: PrivateLink or VPC peering option, recommended PrivateLink for cross-account, explicit firewall rules for egress, NAT with fixed egress IPs
IP allowlist for corporate CIDR and fixed NAT egress IPs; strategy for autoscaling worker nodes
No direct internet egress from GPUs; only approved telemetry endpoints allowed
Pen-test and compliance artifacts required before go-live
Network workshop w/ infra team (PrivateLink/peering design) + final SOW draft
clarify customer-managed KMS cross-account access pattern
legal requires EU-only data residency proof
dynamic EKS node IPs for allowlist - need strategy
pending pen-test report from Redwood staging
Initial sales intro 2026-02-25: high-level fit for compliance use-cases; strong interest in Private VPC
CTO (Lars Nyberg): 'All inference traffic and logs must remain in EU and under our KMS'
Security 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 16: `qst_0056::metadata` · N=25000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant but do not directly address the specific GPU incident and load balancer network setting change mentioned in the question. The failure mode is likely an embedding near miss due to the related but not directly matching content. Both gold and retrieved chunks are non-empty and on-topic, but the retrieved chunks lack specific details about the GPU inciden

### Question

In the users drive area, which draft engineering SRE doc owned by Aisha Patel was last modified in early March 2026 about replaying a multi-region fallback incident?

### Gold document(s)

#### GOLD `dsid_81323a96121047cf98e958463e33d80a`

```
Fallback replay — command log and breadcrumbs

Notes to self: quick replay checklist and command history for the multi-region fallback incident on 2026-02-11. Intended as a reproducible scratchpad to run later in staging and to hand off to oncall for follow-up.\n\nSummary / what happened\n- Around 2026-02-11T21:06Z we saw a spike of route_ejections + regional fallbacks originating from EU-west (az-eu-3).\n- Clients observed elevated latency and ~2.7% 5xxs for about 18 minutes; smart-routing triggered fallback to compatible model variant in us-central for some traffic.\n- Automatic rollback to primary region was slow; suspect policy hysteresis + bad kvcache priming.\n\nObservations gathered (metrics + quick reads)\n- Route ejection metric: route_policy.eject_count[route=chat-text,region=eu-west] increased from 0 to 106 over 6m.\n- Error class in traces: \"handshake_timeout\" + \"kv_cache_miss\" mixed with failed tcp handshakes.\n- Token lat p50 jumped 30ms -> 220ms for routed requests to fallback target.\n- Tracing showed request ids that crossed regional boundary had missing kv_cache headers (x-kv-prefix absent).\n\nImmediate commands I ran (copy/paste friendly)\n# grab recent traces for region slice (3x sources)\nkubectl -n prod logs deploy/route-proxy --since=25m | rg \"region=eu-west\" -B3 -A4 | sed -n '1,500p' > /tmp/eu-west-traces-20260211.log\n\n# sample telemetry query (metrics backend)\ncurl -s \"https://metrics.internal/api/query?metric=route_policy.eject_count&from=2026-02-11T20:50Z&to=2026-02-11T21:30Z&tag=route:chat-text\" | jq . > /tmp/eject-count.json\n\n# fetch routing table at time of incident (config-db)\nredis-cli -h conf-db.prod.internal HGETALL \"routes:chat-text:2026-02-11T21:00Z\" > /tmp/route-config-snapshot.txt\n\n# check last rollout for model variant used as fallback\ngh pr view 842 --json title,body,commits > /tmp/pr-842-summary.txt\n\n# repro request to emulate region failure by forcing route header (staging)\ncurl -v -H \"X-Client-Region: eu-west\" -H \"X-Force-Route: chat-text\" -H \"Authorization: Bearer $STAGING_KEY\" \\\n  \"https://staging.api.redwood.ai/v1/generate\" -d '{"prompt":"hi","max_tokens":10}' --write-out \"\\\\nHTTP_
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_eafe4383765542a183b7ff9f171ee222`

```
Consolidate routing drain detection and harden fallback resilience after multi-region misroutings

Postmortem and follow-ups for a Feb 12th incident where automated region drains + routing cache TTL mismatch caused large-scale misroutes and cascading fallback to underprovisioned model variants. This ticket captures the incident timeline, root cause analysis, immediate mitigations, and long-term remediation work we completed/triaged.
On 2026-02-12 03:14 UTC, customers in EU-West began seeing elevated latencies and 5xx errors. The control plane initiated an automated drain for a GPU cluster due to underlying hardware ECC warnings. A combination of stale routing cache entries and a mis-ordered drain handshake caused large swaths of traffic to be redirected to a low-cost fallback variant (quantized-8) which exceeded its capacity and triggered cascading fallbacks to smaller variants and rate-limit enforcement. The outage lasted ~42 minutes for impacted tenants and caused reduced throughput and higher tail latency for a subset of PLG customers.
2026-02-12 03:12 UTC: Hardware ECC alert on eu-west-a pool.
2026-02-12 03:13 UTC: Control plane issues drain: drain-job(v=4392) created and broad
…[truncated]
```

#### #2 `dsid_5c2f8d2ea0f24dbb9fb0b5e342d669e6`

```
Surgical traffic remediation and staged rollback playbook for mixed-hosted/dedicated cross-region routing incidents

Summary: Create a prescriptive, low-risk runbook and playbook for repairing misrouted traffic and KV-cache divergence that can occur during cross-region traffic shifts involving mixed Hosted + Dedicated customers. This ticket focuses on: tenant-aware surgical remediation, staged rollback commands, validation checks, safe fallbacks to compatible model variants, and coordinated customer communication. Scope includes Hosted API, Dedicated pools, and coordination instructions for Private/VPC customers when operator action is needed. Excludes lower-severity non-tenant-isolating issues.
1) Runbook tested end-to-end in staging with simulated tenant traffic and at least two fault modes (regional network partition, autoscaler misplacement). 2) Clear command snippets for tenant pinning, partial region drain, and staged rollback validated by SRE run. 3) Communication templates approved by support & AMs. 4) Telemetry queries for correctness and SLA impact added to dashboards. 5) Postmortem checklist ready and linked.
Step 0 - Triage: Confirm incident type with oncall: Is this a 
…[truncated]
```

#### #3 `dsid_e28c2b76f9ae43bdb6e809f2acf37930`

```
Region failover sequencing bug and priority shed policy consolidation

Summary: On 2026-03-01 at ~08:03 UTC a multi-region failover sequence caused a correlated set of circuit-breaker (CB) openings and priority queue shedding across EU and US regions, resulting in a 28-minute continuous SLO violation for the generation latency P99 for several high-throughput customers. The orchestrator replayed an out-of-order failover sequence after a partial control-plane partition which briefly allowed dual warmup eviction and simultaneous CB signals. This ticket captures the incident analysis, immediate mitigations, and cross-team corrective plan to prevent recurrence.
SLO: generation P99 latency exceeded target (1.2s -> observed 3.8s) for 28 minutes
Affected regions: EU-west-1 primary, US-east-1 secondary (sticky affinity misrouted to secondary under failover)
Customers: 7 high-throughput tenants experienced increased 429/503 errors and tail latency spikes
Operational: automated rollback to lower model concurrency triggered but did not fully alleviate due to inter-region backpressure
2026-03-01 08:02:38 UTC - Control plane observed degraded heartbeat from EU controller (brief partition).
2026-
…[truncated]
```

#### #4 `dsid_aca62fe6a1c84870a36208b32749ea76`

```
Shadow failback timing exposed circuit-breaker coordination gap causing SLO misses

Summary: On 2026-03-01 we observed a multi-region SLO regression affecting API latency p99 for hosted text-generation. A staggered failback from the DR region to primary region coincided with a shadow (non-primary) region reintroduction: overlapping routing changes plus asynchronous circuit-breaker state caused a brief amplification of requests to a small subset of hot shards. That amplification pushed token processing beyond our graceful-degradation thresholds and triggered aggressive load-shedding, producing SLO misses and client errors for ~18 minutes. This document captures timeline, root cause, immediate mitigations, and follow-up action items.
User-facing latency p99 rose from 240ms baseline to 1.8s for affected customers in NA-east and EU-west for ~18 minutes. ~2.3% of requests returned 503/504 or truncated responses during window. Business impact: a handful of enterprise customers reported degraded UX and one observed an automated retry loop increasing downstream costs. SLO category: latency p99 and availability; customer_impact: high.
2026-03-01T01:12:00Z - Primary region reported elevated 
…[truncated]
```

#### #5 `dsid_3fc55e5263f14129af120e912bb79e0b`

```
Coordinated cross-region traffic drain with tenant-priority and emergency hotpatch

Summary: This ticket captures the runbook and emergency fix path for coordinated cross-region traffic drains when a regional service regression affects latency or correctness. Scope covers Hosted API routing, Dedicated tenant pools, and Private (VPC) deployments when partner-managed control planes request guidance. The focus is to: 1) safely evacuate traffic from a degraded region with tenant-prioritization (SLA customers first), 2) preserve KV-cache/LLM context warmup to reduce error/regression risk, and 3) ship an emergency kernel-scheduling hotpatch for a race we observed that amplifies cross-region desynchronization under heavy tail latency.
Runbook tested in staging with simulated region outage and verified tenant-priority ordering works (SLA-marked tenants drained first)
Automated traffic-shift automation triggers with expected fallback model variants and verifies per-tenant tokenization compatibility
Emergency hotpatch (kernel scheduler tweak) passes canary in two regions with no regression for p99 latency over 72h
Post-incident checklist completed and communicated to affected customers withi
…[truncated]
```

#### #6 `dsid_4b52a93a47474cb292df6a79917f97ff`

```
Regional ejection from delayed telemetry leading to fallback amplification — incident retrospective

Summary: On 2025-10-28 at ~09:12 UTC, a telemetry ingestion lag in the regional aggregator caused stale health signals to be propagated to the control plane. The control plane interpreted the stale metrics as a sustained regional failure and ejected an EU region pool from routing. The ejection caused a sudden reroute of persistent sessions and long-running KV-cache-backed token streams to other regions. Those regions then began hitting per-tier capacity limits and automatic fallback policies activated, cascading into an amplified fallback surge to lower-capacity model variants and increased end-to-end latency for customers across multiple accounts.

This ticket is the incident retrospective describing what happened, the immediate mitigations we executed, root cause analysis, and the remediation plan to prevent recurrence.
2025-10-28T09:12Z - Alerts: control-plane emitted 'region-unhealthy' for eu-west-2. Initial alert volume increased due to route error spikes seen in API gateways.
2025-10-28T09:16Z - Ops: on-call investigated dashboards; regional health metrics (heartbeat_rate, avg
…[truncated]
```

#### #7 `dsid_90d9b4c489fe4f689324379fd42d5190`

```
Tiered-region-eviction-and-rollback-protocol + customer-bridge for cross-region KV desync

Summary: A reproducible class of incidents has emerged where asymmetric leader leases during incremental region resynchronization lead to KV cache desynchronization and amplified tail latency for a subset of tenants. This ticket captures a new, tiered eviction-and-rollback protocol designed to: 1) stop customer-facing errors quickly with minimal traffic loss, 2) provide a safe surgical rollback path for affected region state, and 3) create a short customer bridge communication pattern for Hosted and Dedicated customers while the state patch is deployed.
Step 0: Activate emergency incident bridge (SRE + PM + ENG + CSM) and pin public comms template.
Step 1: Reduce region ALB weights to 0.2 and enable tenant-priority routing so only P0/P1 tenants keep sessions on the degraded region.
Step 2: Enable read-through KV fallback (cold read from cross-region authoritative snapshot) for affected shards to avoid stale in-memory responses.
Step 3: Temporarily disable continuous prefix caching for write-heavy tenants to prevent amplification of desync windows.
Step 4: Run cross-region KV quick-reconcile t
…[truncated]
```

#### #8 `dsid_97a1326a4ecb49afa2fdb7edd3e985d6`

```
Stabilize observability fanout after event gap recovery (customer escalations)

Multiple customers reported missing time-series and truncated traces following a cross-region control-plane failover. Investigation shows an event fanout mismatch between the telemetry ingesters and the dashboard aggregation tier, resulting in opaque gaps (partial metric shards) and broken live-panel renderings. This ticket scopes the immediate repair, stabilization changes to fanout/ingest coordination, and communication/remediation runbook for affected customers.
Simulate control-plane failover in staging by toggling region-primary flag and shepherding ingestion through the secondary region
Load replay of high-cardinality tenant traffic for 30 minutes using telemetry-replay-v2 (link in artifacts)
Observe metric shard registration events and verify fanout acknowledgements across ingestion replicas
Trigger a dashboard live-panel refresh and inspect metric tiles for empty or partially-populated series
2026-03-02: Emergency hotpatch applied to resume probe-level re-ingest for critical SLO metrics (partial success)
2026-03-04: Circuit-breaker introduced on the aggregation service to prevent tombstoning of 
…[truncated]
```

#### #9 `dsid_8f050e5e55374b72a2265597eb6fdb1e`

```
Regional traffic surge, partial SLO degradation: incident analysis and corrective roadmap

On 2026-02-18 we observed a sudden traffic surge originating in EU-WEST that caused increased tail-latency and an SLO miss for text generation endpoints. Traffic was partially failed over to US regions which reduced availability for EU customers and exposed weaknesses in circuit breaker and load-shedding policies. This ticket documents the event timeline, root causes, immediate mitigations, and a prioritized corrective roadmap.
2026-02-18 09:12 UTC — First alert: 95th percentile latency for /v1/generate (eu-west cluster) crossed 800ms (SLO target 300ms).
2026-02-18 09:14 UTC — Autoscaling triggered but observed slow VM provisioning due to burst cold-starts in dedicated pools.
2026-02-18 09:20 UTC — Circuit breaker for eu-west marked the region as unhealthy and routed ~40% of traffic to us-east as configured by smart routing.
2026-02-18 09:23 UTC — US region experienced increased load; KV cache miss rate spiked because cache keys were highly cardinal due to user-supplied prefixes, causing CPU contention and higher token cost.
2026-02-18 09:28 UTC — Load-shedding policy prioritized embedding wo
…[truncated]
```

#### #10 `dsid_595af30d9c194f8ea1a068a39dd9cedd`

```
Proactive congestion-island detection and sticky-region guardrails

Summary: During a progressive traffic surge on 2026-03-09 we observed cross-region failover amplification that caused an SLO miss for request p99 latency and error rate for hosted inference customers. Secondary regions entered a congestion mode that persisted despite circuit-breaker trips; routing replays and probe jitter amplified load to warm caches and overloaded GPUS. This ticket captures the postmortem analysis and prescribes mitigations and follow-ups to prevent recurrence.
2026-03-09 09:12 UTC - Automated health checks detected increased tail latency in region-eu-west-1.
2026-03-09 09:18 UTC - Smart routing triggered failover policy to reroute ~18% of traffic to region-us-west-2 (secondary).
2026-03-09 09:21 UTC - Circuit breakers in us-west-2 tripped and then rapidly reset due to short hysteresis config; controllers replayed queued requests.
2026-03-09 09:26 UTC - Observed progressive KV cache cold misses and repeated replays; GPU utilization saturated and request queues began to grow.
2026-03-09 09:40 UTC - On-call rotated, emergency mitigation (partial traffic pause to a warm standby) executed at 09:47 UT
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 17: `qst_0063::metadata` · N=100000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are generally on-topic but do not address the specific latency target for NorthPoint Signalworks. The failure mode is a lexical mismatch, as the retrieved documents discuss similar topics but do not match the specific query requirements.

### Question

For the SMB edtech account in North America that wants a hosted API for K-12 copilots, who is the sales owner listed in the record?

### Gold document(s)

#### GOLD `dsid_15dd15bfbd0f42c485a9b5b9ace6a3d1`

```
Cobalt Campus Innovations

Inbound signup via hosted API free tier (referral from teacher meetup).
Founder: Ben Morales (product lead for classroom experiences).
Initial impression: wants lightweight copilots embedded in teacher dashboard, not full LLM ops. Budget-conscious — experimenting on free credits first.
Requirements summary: chat-style copilots for K-12 teachers; inline content moderation for student inputs; short-term conversation memory (per session), exportable summaries for lesson notes; light embeddings for quick rubric lookup. Latency target: median <300ms for single-turn chat in US-West. Throughput: low (dozens of sessions concurrently), bursty around 8-11am local class times.
Model preference: open-model compatibility, but happy to start with Redwood-hosted curated model that keeps costs low. Wants quantified per-student monthly cost estimate.
Security: district will ask about COPPA and data retention. They want audit logs and an easy-to-explain retention policy (30/90/365 options). SSO/SAML likely later.
POC ask: create a 2-week sandbox for 3 pilot teachers to run the copilot in their existing LMS; provide content-moderation presets + webhook for flagged events.
Quote from call: "We need something teachers can trust — fast, cheap, and with minimal admin overhead."
Notes on integration: front-end team will call Redwood SDK via server-side proxy to hide keys; IT wants clear IP ranges to allow outbound.
Cost sensitivity: target $200-400/mo during pilot; long-term goal to scale to $1k-2k/mo if unit economics are clear.
Follow-ups: send pricing + simple token budget example for a class of 25 students; attach code snippet for streaming chat; provide moderation rule doc stub.

district procurement review
COPPA compliance clarifications
tight token budget (target $200-400/mo)
IT firewall rules for outbound API calls
Send hosted API pricing sheet and sample token budget; issue sandbox keys; schedule 30m POC kickoff week of 2026-03-22.
2026-02-24: inbound signup via hosted API trial (self-serve, form includes 'education' tag)
2026-03-02: 45m discovery call — Maya + Aaron with Ben Morales; demo of hosted API and streaming chat (ff_20260302_aurora_demo)
20
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_e555234794034e218991ca49a2ffb3ea`

```
Cascade Copilot Solutions

Inbound SMB lead via blog post signup. Small NYC-based edtech building in-class copilots and teacher-assist tooling. Interested in hosted API for fast self-serve integration; cannot justify dedicated or private yet.

Highlights from discovery call (2026-03-03):
- Attendees: Maya Chen (AE), Liam Ortiz (SE), Priya Rao (Founder/CTO), Ben Li (Product).
- "We need something that just works out of the box and doesn't blow our budget" — Priya.
- Primary workload: classroom copilot for live Q&A and teacher assistance + automated homework feedback. Secondary: content moderation for student submissions (esp. image captions & short answers).
- Latency/throughput: target <400ms token latency for short-turn chat (1–2 student exchanges), bursty usage during class hours (25–60 concurrent sessions).
- Cost sensitivity: high. Wants estimation for token costs at 10k monthly active students pilot (target ARR < $5k first-year).
- Model preferences: open to small/efficient open models (quantized) or Redwood-curated models; wants fallback routing if the hosted SKU is rate-limited.
- Security: needs SSO (SAML), audit logs for teacher actions, and basic KMS support; FERPA concer
…[truncated]
```

#### #2 `dsid_562d40ac95ef4410919e6103788b9b6b`

```
ZenithClass Education

Inbound SMB lead from teacher-founder (K-8 focus). Signed up via docs — looking for a lightweight hosted API to integrate a classroom copilot and content moderation into their web app.
Pilot target: 20 teachers, ~3k students (district charter partners) — mainly formative feedback and question summarization during class.
Primary constraints: budget under $1k/mo, must avoid high false positives for moderation (student language/context important). Wants transparent per-token costs and clear batching guidance.
Technical preferences: public cloud only, no VPC or on-prem. Retention target: 30 days; needs audit logs for teachers/admins. No immediate SSO requirement but may add SAML next school year.
Requested deliverables: sample moderation rule set and expected FP/FN behavior, quickstart code sample for streaming copilot responses, estimated monthly cost for 25k tokens/mo and 100k embed units.
Quote from demo: 'If our filters flag too much student chatter we lose teacher trust — need a tunable, explainable moderation model.'
Wants to run a 30-day POC on hosted API with promo credits and lightweight usage analytics to validate latency and cost against classroom work
…[truncated]
```

#### #3 `dsid_cf4056237f4747cab4a5bde4728ce77a`

```
Papertrail Learning Hub

SMB edtech, classroom copilot + moderation POC. Budget sensitive; prefers hosted API. Needs SAML + US-only processing confirmation. Next: trial creds + SE demo for moderation tuning.
Inbound via community webinar (classroom copilots) — founder demo sign-up
Founder: 'we need cheap, reliable completions for inline teacher assistants'
Primary flows: teacher+student chat, answer generation from district docs, real-time moderation of student input
Budget constrained: looking for usage-based hosted API, prefer predictable per-seat budgeting
Prefers open model variants if quality/cost tradeoff is clear — asks about quantized models and latency tradeoffs
Wants SDK examples for React + Firebase login flow
Security: SSO for teacher admin (SAML) is a must-have for pilot; SOC2 would be nice but not blocking for initial test
Data residency: pilot with one US school district — needs confirmation of US-only processing
Asked about streaming responses for live chat and content-moderation latency SLOs
Wants a short POC (4 weeks) with 10 teacher accounts + up to 5k messages/month
Quote from call: 'If we can keep costs under $X/month per teacher, we can scale to 2k teachers ne
…[truncated]
```

#### #4 `dsid_715ad99c826a4e1fb5002c553f4b16d7`

```
Academic Ally AI

SMB edtech, wants hosted-api for classroom copilot + moderation. Budget-constrained; needs SSO and audit logs. SE eval of moderation required.
Lead profile: small NYC-based edtech building a teacher-facing copilot + student safety layer. Self-serve signup, used credits for initial testing.

What they said: "We need something cheap and reliable — teachers use it live in class, so latency matters." Wants hosted API; no capacity for Dedicated.

Primary pain: moderating student-submitted content (teen slang, abbreviations, code-switching) and giving teachers quick drafts/feedback. Budget sensitive — prefers open/quantized models or Redwood cost-saving suggestions.

Technical requirements / asks:
- Target median 400-600ms for short prompts (classroom micro-interactions).
- Throughput small: ~30-50 qps peak per classroom cluster; initial deploy single-region NA.
- Retention 30 days; audit logs required for teacher actions.
- SSO via Google (G-Suite) mandatory for teacher accounts.

Security notes: SOC2 desired but not blocking (will accept SOC2 roadmap). KMS not required initially; wants an easy audit log export.

Routing/model preferences: open to small Llama-variant o
…[truncated]
```

#### #5 `dsid_8ad05e98218845e9b5e4fc4275eba6c4`

```
PencilCore Education

SMB edtech inbound — early discovery. Looking for hosted API, strong moderation support for K-12, SSO/SAML, and low-cost profile. AE to provide pricing worksheet and SE to run a technical walkthrough. Budget ~ $1k-$5k ARR initial.
Founder: 'We need something lightweight to help teachers build personalized study plans — cost is the blocker.'
Primary workload: classroom co-pilot embedded in teacher dashboard; short chat turns, inline Q&A, auto-quiz generation
Moderation reqs: K-12 safety is critical — need examples of false-positive handling and appeals flow
Latency target: sub-350ms for single-turn chat on RN latency-sensitive flows; most traffic off-hours (evenings)
Throughput: initially modest (50-200 requests/day), expected to grow with pilot schools
Model preference: open to small/medium open models with quantized options; wants hosted API to avoid infra ops
Cost sensitivity: very price conscious — likely to stay on hosted tier if per-token math works
Quote from lead eng: 'If we can get predictable pricing and a simple SSO path, we can onboard two districts this summer.'
2026-03-01 - Inbound: self-serve signup, used free credits to test text-gen and moderat
…[truncated]
```

#### #6 `dsid_9a679ab76b7e425dbbd31fa1c7dda1c3`

```
Lodestar Classroom Tools

Inbound SMB edtech — product-led signup, wants hosted API only. Founder Aneela is hands-on: 'need something we can turn on this week and not own infra.' Primary workloads: classroom copilot for teachers (assist with lesson plan generation, inline feedback), student Q&A bot, and automated content moderation for student-submitted text and file metadata. Cost-sensitive: target spend <$6k/year initially; expects spikes at 10-11am local class times (daily). "Moderation must catch profanity and PII patterns; false-positives tolerable but must be configurable." Prefers small/efficient open models or Redwood-curated lower-cost variants. Latency target: <=250ms p95 for short-turn Q&A; throughput modest (~50 req/min burst). Wants token-level cost breakdown and batching recommendations. Wants SAML SSO for teacher admin portal (can postpone, but needs confirmation of support). Current blockers: finance approval for first-year spend, need short security note for procurement mentioning SOC2/HIPAA posture (they saw Redwood logos in marketplace but want doc). Next steps: share hosted pricing link, security FAQ, quick prompt templates for classroom copilot + moderation, se
…[truncated]
```

#### #7 `dsid_c1c9c05711914698b1c6e97a985af9da`

```
Snowberry ScholarWorks

Inbound via docs/edu newsletter sign-up. Self-serve account created 2026-02-12, used free credits to prototype chat copilot for middle-school teachers. Wants hosted API; does not want dedicated or on-prem now. Priorities: low per-student cost, simple integration with existing LMS (Canvas), and built-in moderation for student-generated content. Quote from founder on discovery call: "We need something that handles classroom tone and flags risky replies — but our budget is tiny." Technical contact is CTO (Lenora Kim) — leaning open models if cost-effective. Interested in streaming for real-time typing feel and function-calling for gradebook actions. Open to using smaller quantized models to save cost. Requests sample latency numbers at 128-token responses and a pro-forma monthly cost for 5k active students.
SMB edtech focused on classroom copilots + moderation. Expected workload: conversational assistants embedded in LMS, light embeddings for FAQ, periodic batch reranking for homework submissions. Latency target: conversational replies under 700ms p50 for typical 64-128 token responses. Throughput: expected concurrency 30-70 active students during peak class ho
…[truncated]
```

#### #8 `dsid_2416d1a0ff034d0586046642daffd0eb`

```
Cerulean Campus AI

2026-02-24: inbound via docs.google signup form - requested low-cost copilot for K-8 classrooms
2026-02-25: AE outreach (Avery) - intro email, sent quickstart link and sandbox key instructions
2026-02-28: discovery call (ff-2026-02-28-cerulean-intro) - demo of intent: assistant for teachers + realtime moderation
2026-03-02: dev tried hosted API sample, reported prompt latency ~400ms for 256-token test (note: repro on their side), asked about batching
2026-03-05: follow-up email with cost estimates for 5000 MAUs; asked for student data retention options
2026-03-09: SE sync with Luis - technical fit looks fine; trial keys expiring in 10 days; waiting on budget ok from founder
Inbound SMB edtech. Founder (Maya R.) cares about teacher-facing copilot and built-in moderation for student messages. Very price sensitive — "cheap per-student" is repeated twice on calls. Wants hosted API (self-serve) to avoid infra ops. Key snippets from call: "We need something that doesn't explode the monthly bill when usage spikes during assignments" and "can you show us cost-per-1000-students with a 2x safety buffer?". Prefers US data residency but not strict — early-stage. Security as
…[truncated]
```

#### #9 `dsid_de9ed80a929e4794854467cf5afd6d63`

```
Sage Scholar Labs

SMB edtech, tight budget; building an assistant for K-12 tutors + classroom copilots. Wants hosted API (self-serve) ideally — lower ops. Key ask: content moderation and profanity/PG filters built-in or guidance for policies.

Quotes from call: 'We need something affordable for a lean team — if token costs spike we can't scale.' — Head of Product.

Tech constraints: avg response length ~250 tokens, peak concurrency ~30 concurrent students per session, latency target 150-300ms p50 for short prompts, can accept higher p95.

Security: requires SSO (SAML), audit logs for admin actions, SOC2 proof for procurement. Data residency: prefers NA but OK with multi-region public cloud.

POC ask: 2-week pilot using hosted API (sandbox) with 200k tokens monthly cap, run moderation pipeline + classroom assistant flows. Wants example policy templates and cost simulation.

AE notes: candidate for self-serve expansion; low ARR but good reference case in education vertical. Follow-up: provide pricing tier comparison + sample moderation rules + sample prompt templates.

Attachments: pricing deck stub, security evidence request in Drive.
2026-01-27: inbound sign-up from product page, 
…[truncated]
```

#### #10 `dsid_917abe74a753481baf00f0bc5f4588a9`

```
PebblePath Education

Inbound via self-serve (signup form) from founder. Primary product: lightweight classroom copilot that sits in teacher dashboard and student chat. Workload mix: multi-turn chat for tutoring + real-time content moderation on student submissions + end-of-session summarization. Latency target: median p95 generation <350ms for 256-token responses (real-time feel for chat). Throughput: pilot ~1k requests/day (spiky during class hours), long-term hope 50k+/month as adoption grows. Cost sensitivity: 'we need predictable costs under ~$0.03 per active student per month during pilot' — founder is very budget conscious.

Model preferences: open to smaller open models if quality & latency acceptable; interested in Redwood's verified model profiles and any quantized variants for cost savings. Important: automated fallback to cheaper variant when low-priority routes (summaries) to save cost. Also need simple rate-limits and per-route token accounting for teachers.

Security/compliance: SMB but schools require audit logs, SSO/SAML integration planned for next term, data residency in US preferred. SOC2 not mandatory immediately but they want answers for retention and access l
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 18: `qst_0068::metadata` · N=50000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved document IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to latency and streaming topics but do not address the specific question about the default wait time and differences between hosted and dedicated tiers. The failure mode is lexical mismatch as the retrieved documents do not match the expected content. Both gold and retrieved chunks are non-empty and on-topic, but not specific to the question asked.

### Question

For the SMB B2B SaaS account in discovery that needs audit logging and is evaluating a hosted API for an in-app chat assistant with streaming latency concerns, who is the assigned solutions engineer?

### Gold document(s)

#### GOLD `dsid_d9a7de9e7cfc4fe0b7b57765b6d25ad9`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_3c69e5d0b7a6462d9c7d54f40dbb914d`

```
SpruceTop AssistKit

Building an in-app streaming chat assistant for SMB B2B SaaS. Expected traffic: 100-300 concurrent active users in month 1, scaling up. Target latency: p95 <= 100ms for user-visible first-token and smooth streaming. Priorities: streaming SDK, low overhead integration, predictable per-route cost.
Inbound self-serve signup from sprucetop.ai -> used free credits and hit streaming sample. CTO (Marco Reyes) on call 3/15. Wants very low latency for in-app assistant: "sub-100ms p95 is ideal for chat experience". Team is small (engineering 12, product 4). Primary ask: streaming SDK + example on React Native, per-route token cost clarity, and quickstart for prefix caching. Security: SOC2 required, SSO via SAML, audit log retention 12 months. Pricing sensitivity: startup budget; prefers pay-as-you-go initially but may convert to reserved if predictable. Notes from call: "If p95 jumps >200ms users complain instantly". AE notes: fast follow, send benchmark pack and invite engs to POC. Keep messaging simple — emphasize hosted API + streaming, minimal infra setup.
```

#### #2 `dsid_1c2a8f0a58244503800e031d4e1980a8`

```
Humble Harbor AIWorks

Inbound SMB lead from small CX SaaS. CEO/CTO duo (Lena Ortiz, Carlos Mejia) are focused on rapid cost controls after 2 months of trial. Primary ask: 'Can you show us quick wins to cut token spend without hurting quality?' Preference for hosted_api, want self-serve POC. Key items: batching suggestions, prefix caching for KB lookups, prompt compression + stop token trimming. Wants a lightweight token audit for last 50k requests. Cost sensitivity: high — target to reduce prod token spend by 30% within first month. Latency: p95 target ~200-300ms; throughput spikes up to 10 reqs/sec during peak. Quote from CTO: "If we can get a 25-30% cost improvement with minimal infra changes, we can commit to paid tier."
Deliver token-usage audit + batching/caching recommendations; schedule POC kickoff (week of 2026-03-15).
budget sign-off from finance
clarify SSO timeline with IT
legal questions on data retention policy
2026-02-15 — Inbound sign-up via hosted API free credits, self-serve trial started
2026-02-16 — Intro discovery call (owner: Ava Chen); high-level product fit
2026-02-19 — Shared pricing deck (drive: /decks/humbleharbor-pricing-v1); asked for cost optimization 
…[truncated]
```

#### #3 `dsid_3f6b75da6a0745c197dd3ee4f6207e0d`

```
Mosswood EchoAI LLC

Lead: Mosswood EchoAI (SMB support SaaS). Primary contact: Elena Morales (CTO).
Context: signed up self-serve, experimenting w/ hosted API for in-app chat + FAQ assistant. Main pain: latency for EU customers — reports of slow UX causing drop in trial engagement.
Direct quote from Elena on 2026-03-02 call: 'We see spikes where a single response takes 2-3s to start streaming; makes chat feel sluggish compared to competitors.'
Customer environment: mostly public cloud; no private/VPC plan right now. Wants guidance rather than infra changes.
Requested: 1) quick perf tuning checklist (region selection, SDK timeouts, prompt-length guidance), 2) sample config to enable streaming + prefix caching, 3) cost vs latency tradeoffs for routing to US region vs EU region.
SE observations (Priya): short prompts (<120 tokens) have relatively higher overhead — recommend batching user messages server-side? Not feasible for chat real-time; recommend streaming + reduce model context to 1024 when possible. Also tried switching to na region with immediate improvement.
Action items captured in notes: "Share short perf checklist", "Provide sample timeout settings and example SDK snippet
…[truncated]
```

#### #4 `dsid_554b411fbaed4e908d7a5f425a109000`

```
Crownbrook ConverseHub

Inbound via self-serve signup -> quick start. Product: in-app assistant embedded in B2B SaaS UI (customer success + contextual help). Team: 6 engs (backend + infra), 2 ML/AI engineers. Wants streaming + token-level partial responses for perceived latency improvements. Quote from demo: "Users abandon if response > 200ms perceived. Streaming is a hard requirement."

Key asks: low median latency (<150ms ideal), drop-in hosted API with streaming websockets, predictable per-token cost for budgeting, and simple SAML/Google SSO for internal admin console. Prefers open/quantized models to control cost but wants Redwood to handle kernel/quantization recommendations.

Notes on traffic: expected pilot 500-1500 MAU, peak concurrency target 30-80 concurrent chat clients, burst tolerance required (end-of-month billing support chats). Budget band for pilot ~$800-$1.5k/month; ARR target if rollout succeeds $10k-$20k/year.

Security: SMB but cares about audit logs and SSO; will escalate SOC2 if enterprise sales route triggered. Data residency preference: US primary, EU for select customers later.

Internal stakeholders: Head of Product (Lena K.), CTO (Marco Ruiz), Dev lead (
…[truncated]
```

#### #5 `dsid_451062cb78a04e08adb918f8c77a3748`

```
SableBeam Assist

Inbound via self-serve signup (trial credit used). Small B2B SaaS (in-app assistants for SMB customers). Primary ask: low-latency streaming for conversational UI embedded in their web app. Engineering notes from intro call: target p50 ~100ms, p95 <400ms for short-turn messages (most responses are 8-40 tokens). Expect ~200 active concurrent sessions initially; burst to 600 during peak. Cost sensitivity high — wants guidance on token/unit cost tradeoffs and batching. Preferred region: AWS us-west-2. Security: Okta SSO, need audit logs and optional KMS integration; retention default 30d. They tried prod PoC with another provider and reported intermittent streaming stalls and dropped frames: "we saw 200-800ms spikes and users felt it lagged". Redwood value props that resonated: streaming + predictable latency, per-route cost breakdown, easy SDK for websocket streaming.

POC ask: 2-week hosted API trial to validate steady p95 under 400ms w/ streaming enabled, sample SDK + latency harness, and clear contract on token caps for concurrent streaming.

Sales shorthand / recent note snippets:
- "AE intro: verified use-case + budget band, engineer (CTO) wants hands-on latency
…[truncated]
```

#### #6 `dsid_c73df6b8cc0645439edeabed43cce6d2`

```
BentoAssist Cloud

SMB support automation vendor. Primary goal: hosted API for fast self-serve POC to auto-summarize inbound tickets, extract structured fields (issue_type, priority, customer_tier), and perform function/tool calls to their ticket system to set status/assign. Expect to start on public cloud; low initial security friction but SOC2 and SAML planned. If POC shows performance/cost benefits, move to higher commit or Dedicated plan.
- Lead source: docs signup + chat widget. Wants a self-serve path first.\n- Use case: automatic ticket summarization and structured extraction for downstream routing + tool-calling to update status in their system.\n- Latency/throughput: avg ticket body length ~300-600 tokens; peak 6 reqs/sec during business hours; target median latency <200ms for summary-only path, <450ms for tool-calling flow.\n- Cost sensitivity: SMB margins, looking for predictable per-token pricing; interested in suggestions on batching and prefix caching to cut costs.\n- Model preferences: open to smaller open models for summarization; wants ability to route to higher-quality model for high-priority tickets.\n- Security: SOC2 required within 6 months; currently use Okta 
…[truncated]
```

#### #7 `dsid_ea23b1139d4141c483f46443089031e0`

```
Sable Counsel LLC

Inbound SMB lead from legaltech vertical. Small team (20 ppl), building a contract review assistant and internal knowledge search. Priority: keep all audit logs for 12 months, must store logs in US region only — "must not leave US" (quote from CTO).

Security checklist: interested in SSO/SAML, KMS for key wrapping, and per-request audit entries (requestor, route, model, prompt hash, token counts). Concerned about PII in prompts and want guidance on redaction or client-side hashing.

Cost sensitivity: price matters, will start with low-volume self-serve but expects bursts during monthly review cycles.

Current status: discovery — signed up for trial but hasn't started heavy testing. Asking for: sample audit-log schema, retention options + costs, confirmation of US region hosting, and a short doc on how Redwood handles prompt retention vs. ephemeral KV cache.

Notes from call (shorthand):
- CTO Samir: 'we cannot send raw SSNs or client identifiers to non-US servers'
- Legal ops lead wants example SOC2 language for procurement package
- AE action: send hosted-api security FAQ + sample logs schema; loop in SE for technical call

Next step: schedule technical deep-div
…[truncated]
```

#### #8 `dsid_a3ff6f6eec4b44f69c0e88303c264c65`

```
Elmbridge AssistCo

Inbound SMB lead building an in-app chat assistant. Qualified: wants hosted API self-serve POC with streaming and low perceived latency. Cost-sensitive; SOC2 on roadmap. Next: provide streaming test key and JS sample, confirm billing and retention FAQ.
Prospect profile: early-stage B2B SaaS (In-app assistant for user onboarding + contextual help). Very latency-sensitive; primary KPI is perceived RTT in UI. Target: initial 80-150ms per-turn feel (they acknowledge token-level latency will be higher, but want streaming chunking so first tokens appear <200ms).
CRM notes (shorthand):
- Product: embedded chat widget + contextual tips (SDK in TS/React).
- Traffic pattern: many short sessions, avg session 40-80 tokens, bursts at product launches (concurrent ~20-40 sessions).
- Cost sensitivity: SMB budget, looking for predictable per-session billing; want to avoid large cold-start costs.
- Model preference: prefer smaller open models with good streaming characteristics; asked about Redwood model catalog and quantized variants.
- Integration asks: websocket streaming example, token-chunked responses, reconnect behavior, client-side socket keepalive.
- Security: SSO (Okta
…[truncated]
```

#### #9 `dsid_0d53c29e820a4a9bad06c8b5e00cd889`

```
Luminaris Chatdesk

Discovery call 2026-02-28 with CTO (Alex Marquez) + two mobile engineers. Inbound via blog post on streaming + latency. Team is building an in-app assistant for B2B SaaS product support and feature discovery. They signed up for self-serve, used free credits to test simple prompt completions. Main asks: 
- Streaming API (progressive message rendering) is a hard requirement — they want tokens as they come for better UX on mobile.
- Latency target: sub-300ms for first token on warm routes, bursty peaks 50–80 rps across customers, avg session length ~120 tokens.
- Cost sensitivity: moderate — startup runway conscious but willing to pay for latency improvements. Looking for clear unit economics.
- Model choices: prefer small/medium open models for cost, but need a fallback path to higher-quality models for ambiguous queries. Interested in automatic routing/fallback by policy.
- Security: SOC2 is a checkbox for their procurement team; SSO/SAML for admin console; basic audit logs and retention controls required. No hard residency requirement (US customers primarily).
- Implementation notes: mobile front-end (React Native) hits their backend; backend will call Redwood h
…[truncated]
```

#### #10 `dsid_51183030e764419caca09cfe647048e7`

```
Banyan Loop AI

SMB inbound — self-serve signup, early discovery. Focused on hosted API streaming for in-app assistant; latency sensitive, moderate cost concern.
Inbound from YC-backed B2B SaaS (product analytics assistant embedded in their app).
Primary ask: in-app chat assistant with streaming responses — product guidance + contextual suggestions pulled from app telemetry.
Latency focus: product team expects first token latency <200ms in US regions; OK with slight increase for long context fetches.
Cost sensitivity: SMB budget, wants predictable per-month hosted spend; likely start small (pilot) then expand if metrics ok.
Deployment: prefer hosted API (self-serve). No plans for Dedicated/Private in near term — ops bandwidth low.
Security: SSO via Okta, needs audit logs and basic retention controls; compliance ask is light (SOC2 preferred but not blocking).
Quote from CTO: "Need streaming to feel native — partial answers while we fetch context. If streaming is choppy, UX suffers."
Engineering note: currently queries include in-app session context + 2–3 KB of recent events; want guidance on prefix/KV caching and batching strategy.
Tried competitor sandbox (large provider) — liked l
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 19: `qst_0069::metadata` · N=10000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to SaaS and API topics but do not directly address the specific question about GPU rebalancing and slot capacity. The failure mode is a lexical mismatch, as the retrieved documents do not match the expected content. The hit flag inconsistency indicates a pipeline issue.

### Question

Who is the solutions engineer assigned to the mid-market product analytics SaaS account running a two-week parity POC before moving from a hosted LLM API to dedicated nodes?

### Gold document(s)

#### GOLD `dsid_b9eb7e39bc2e4f65814c42358089d49b`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_de9c1d389e964346a5d863550ba817a2`

```
Hightide ProductWorks

Evaluating Hosted API -> Dedicated. Run POC, then cost optimization workshop to determine batching/caching/quantization levers and Dedicated sizing/pricing.
Mid-market product analytics company evaluating hosted API as fast path, then Dedicated for predictable throughput and data isolation. Very cost-sensitive: primary driver is unit economics — wants to understand per-query cost at production scale. QPS profile: baseline 3-5 QPS, peak bursts to ~35 QPS for nightly rerank jobs. Latency targets: chat P50 ~150-250ms, embedding batch jobs acceptable up to 2s per batch (parallelized). Prefers open model variants but flexible if Redwood quant/profiles drop cost significantly. Security: SSO + SAML, SOC2 required, KMS for key control, retention rules for PII. Stated quote from CTO: "We need a predictable $/MAU hit model and a clear path to cut inference spend 3x before committing dedicated pool." POC plan: 2-week hosted POC with sample corpus and test harness -> measure latency/cost with batching/caching -> 1-month Dedicated trial if numbers hit threshold.
2026-01-18 - lead sourced from webinar ("Optimizing LLM unit economics")
2026-01-25 - intro call (AE Jordan Par
…[truncated]
```

#### #2 `dsid_8ca703d991844bd195b4b8fdc16040fd`

```
Copperfield Nimbus Solutions

2025-11-12 - Initial inbound via community trial sign-up (self-serve).
2025-12-02 - Discovery call (Maya + Diego) - product: collaborative knowledge + chat; initial KPIs discussed.
2026-01-05 - Hosted API trial started (3-week trial, dev + staging integration).
2026-01-20 - Trial metrics snapshot: average QPS 42, peak QPS 160 during batch sync, average tokens/request 185.
2026-02-07 - Demo: Dedicated intro + cost model (Diego) — customer asked about reserved GPU sizing and canary rollout.
2026-02-18 - Capacity sizing workshop (Diego, Maya, infra lead Tom) — sketched out concurrency and token mix assumptions.
2026-02-26 - Security & compliance kick-off (Priya) — requested SOC2 evidence and KMS integration pattern.
2026-03-01 - Pricing follow-up email with committed throughput tiers and discount math sent (thread-1782345).
Mid-market collaboration SaaS building an in-app assistant + enterprise doc search. Started on Hosted API to validate UX and quality. After positive hosted trial metrics, moving toward Dedicated for predictable latency and data isolation. Core asks: predictable p50/p95 latency for chat (target p50 <150ms, p95 <400ms), embeddings throug
…[truncated]
```

#### #3 `dsid_2a640cd6a0f44f07bd772d630f650e34`

```
PillarWave Analytics

Company: mid-market customer, B2B analytics platform (embedded ML features in product)
Primary contact: VP Product (Caroline Huang) — wants predictable latency for in-app assistants
Initial preference: start with Hosted API for speed/experiment, then move to Dedicated VPC once latency/cost profile validated
POC ask: 2-week Dedicated VPC with isolated GPU pool, preset throughput target ~200 qps, target p95 <200ms for 512-token context
Security: "SOC2 Type II" is required in procurement; must support SAML SSO, audit logs export, KMS-backed key management; one-year retention of audit logs
Data residency: US and EU for customer data partitioning; legal insists on DPA changes for egress; no PHI allowed in test dataset — "can't risk PHI in POC"
Model preferences: open model variants acceptable; interested in Redwood-recommended quantized variants to reduce cost; want routing fallback to smaller hosted model for burst traffic
Integration notes: need service account pattern for CI, static egress IPs for allowlists, list of CIDR ranges requested from infra (provided 2026-03-02 call)
Quote from VP Eng: "If we can hit the latency SLO without 10x the cost of hosted, we ca
…[truncated]
```

#### #4 `dsid_75fff671684246fc80766d44866bf248`

```
Sparrowtail Insights

Complete 2-week hosted POC reranking run; compare NDCG/latency vs current pipeline; provide Dedicated pricing/commit options
legal wants explicit data residency clause
99th-percentile latency SLA to meet product SLOs
budget approval for Dedicated reserve
2025-01-10 - inbound from G2 form (search/rerank use case)
2025-01-13 - discovery call (Aisha P). Product team: head of search (Maya Lopez), ML eng (Ravi Shah)
2025-01-20 - hosted API demo: live rerank endpoint, live streaming, evals overview (notes in drive)
2025-01-22 - POC scope agreed: run offline eval set (10k queries), integrate rerank endpoint for A/B lift test
2025-01-24 - security questionnaire submitted (SOC2 required), linked in drive
2025-02-01 - POC kickoff: ingest eval set, baseline scoring using current Elastic pipeline
2025-02-07 - Fireflies transcript: call_4512abc (POC check-in)
2025-02-12 - first offline scoring results: +9% NDCG (internal), latency median 35ms on hosted
2025-02-14 - pricing conversation: interested in commit for Dedicated if 99th% latency < 120ms and 20% cost savings
2025-02-20 - Dedicated demo scheduled (Carlos M to present)
- Mid-market e-commerce personalization vendor. 
…[truncated]
```

#### #5 `dsid_f43c071c3ace43cca4170bdece263a69`

```
Southbank Sentry Solutions

Mid-market product analytics SaaS focused on in-app help + intelligent search. Team: Head of Product (Eva Lund), Platform Eng (Tomás Iglesias), SecOps (Rashid O'Connor). They want quick time-to-value using Hosted API for chat+search, then move to Dedicated if latency/cost justify. Key asks: EU-only residency for PII-derived embeddings, multi-region routing policy to keep EU traffic local but failover to us-west for burst, p95 chat <200ms target inside EU, embeddings throughput 30–50 qps, reranking latency budget 50–100ms. Pricing sensitivity: prefer staged approach (hosted POC -> committed Dedicated pool). Security: sent security questionnaire (SaaS vendor form), asked for SOC2 + ISO27001 evidence; asked about KMS integrations and audit log retention. Notes from 2025-03-12 call: "We need a plan where we can start on hosted and not re-architect when moving to Dedicated — minimal code changes." They prefer model catalog visibility and ability to pin models during rollout. 
Run 2-week POC on Redwood Hosted (EU region) with production-like traffic; collect latency/cost metrics; follow-up pricing for Dedicated pool
SOC2 evidence requested by security team
pro
…[truncated]
```

#### #6 `dsid_d2d62518de7849f8b62097aa09be7701`

```
VerityLane Product Labs

Mid-market SaaS evaluating Hosted -> Dedicated. POC done. Needs Dedicated sizing for ~35 sustained QPS, 120 daily peak, avg 320 tokens/request. Security: SSO, SOC2, KMS, EU residency. Next: finalize sizing + pricing + legal SOW.
Lead: VerityLane builds an embedded product assistant inside their core B2B app (mid-market customers). Evaluating Redwood: started with Hosted API trial (2 weeks), moved to a short POC using production-like traffic replay.

Key takeaways from POC:
- Traffic characteristics: weekday peak 120 QPS at 14:00, sustained daytime 28-35 QPS, overnight <5 QPS. Observed burst spikes up to 180 QPS during feature launches.
- Concurrency: UI shows ~40 concurrent sessions typical, peak concurrency observed 60 during replay.
- Token mix: avg tokens/request ~320. Breakdown: ~68% short chat exchanges (prompt+100-400 tokens), ~22% long-form generation (500-1,200 tokens), ~10% embeddings/rerank calls (avg 1,024 dims).
- Latency targets: p95 <250ms for chat; p99 <500ms preferred. Currently hitting p95 ~280ms on hosted trial for generation flows.
- Cost sensitivity: mid-market margin constraints; wants to keep hosted per-token spend under $0.0009 equiva
…[truncated]
```

#### #7 `dsid_f9f5ba9463e148568f19b479f835147b`

```
PraxisLoop CX Systems

Schedule Dedicated sizing workshop (internal infra + product), deliver 6/12 month cost model, sign Dedicated LOI
uncertain QPS peaks during sale events
legal wants data residency clause for EU customers
budget sign-off for Dedicated capacity
4-week hosted API proof: chat support assistant + semantic search reranking; onboarded 3 product teams (support, product, trust)
Hosted API trial successful. 2.1M tokens consumed over 4 weeks. Average 1.9s latency for tail-50 on hosted models. Quality: FRT answer precision at 87% vs baseline 73%. Reranking reduced irrelevant top-3 results by 42%.
Primary traffic: customer support chat (70% of requests), doc search + reranking (20%), internal summarization/triage (10%). Weekly diurnal pattern with Monday/Tuesday 1.6x baseline. Two monthly sale spikes observed reaching 3.5x baseline during trials.
Recommended baseline: 5 x A10G-equivalent workers distributed across 2 AZs -> supports sustained 30 QPS and 95th-pctl latency <600ms for average 520-token calls. For headroom to cover 3.5x sale spikes, add 3x burst GPUs or autoscale policy to 8 workers.
medium-high; wants predictable monthly commit with clear unit economics. Inter
…[truncated]
```

#### #8 `dsid_df25e31bc79b4764ad3945872ee1f87d`

```
SummitGrove Product Labs

Top-line: mid-market product analytics startup building in-app assistant (support + docs search). Interested in hosted first to move fast, then evaluate Dedicated for predictable latency and data isolation. Key pain: token spend with heavy search rerank workloads. Talks started Feb 18 demo; POC scoped Feb 25. AE said: 'need clear unit economics vs current vector db + lambda pipeline'.
- 2026-02-18: Intro demo (hosted API) w/ AE Jordan + SE Maya. product team + infra lead attended.
- 2026-02-22: Security questionnaire submitted (SOC2 + SSO questions).
- 2026-02-25: POC kickoff call. Scope: chat assistant + reranker for 2M monthly queries, 95th pctile latency target 350ms.
- 2026-03-02: Pricing deep-dive w/ revenue ops; requested dedicated commit scenarios (3yr/12mo).
- 2026-03-03: Cost-optimization workshop scheduled; internal stakeholders: PM, infra, finance.
- 2026-03-05: Security follow-up: request for KMS integration diagram.
Workload: mixed chat + embeddings + reranking. Targets: 95th pctile <= 350ms for chat, sustained throughput ~60 QPS for rerank during peak, average cost sensitivity: high (target <$0.02 per active user/month). Model prefs: prefer s
…[truncated]
```

#### #9 `dsid_4b0f5e573e5e4ce8bbbcf370c3ea7eaa`

```
NorthPoint Signalworks

Mid-market B2B SaaS product team evaluating Redwood for chat-first workflows plus semantic search. Started on hosted API; moving to Dedicated POC to validate latency, cost, and secure deployment (VPC + KMS). POC will exercise canary rollouts and fallback routing between model variants and regions, and must demonstrate automated rollback rules tied to eval/regression checks.
2024-08-05 - inbound trial signup (hosted API). Product team ran smoke tests.
2024-09-10 - hosted API demo with Maya. Primary ask: p95 latency <200ms for chat flows.
2024-10-22 - cost/throughput workshop. Customer requested Dedicated options for predictable SLA.
2024-11-12 - security review kickoff with SecOps; requested SOC2 evidence + KMS diagram (see Drive)
2024-11-15 - SE Jamal performed throughput sim (concurrent chat workload). Proposed canary + fallback blueprint.
2024-11-18 - verbal approval to run 4-week Dedicated POC. Signed NDA; awaiting SOW/pricing doc.
POC objective: validate Dedicated pool for interactive chat + embeddings at mid-market scale (200-400 daily concurrent users).
Latency targets: p95 <180ms for short chat (<=512 tokens); p50 <80ms. Product lead: "We can't accept
…[truncated]
```

#### #10 `dsid_947baa655c154bf7a8a853e8c70f9fda`

```
Lotus Helm Analytics

- Company background: mid-market B2B SaaS (product analytics for mobile apps). SLA-driven product teams, heavy real-time support channels.
- Primary ask: lower per-token cost on embedding + reranking pipeline, predictable latency for support assistant (99th pctl < 350ms for short queries).
- Phased approach requested: 1) start on Hosted API to validate quality and prompts (done), 2) move to Dedicated for throughput and predictable unit economics (POC).
- POC scope (agreed): 2-week Dedicated run with a canary route (~10% traffic) then gradual ramp to 100% if metrics hit SLOs. Canary focus: latency, tail-latency, token cost, and model output stability.
- Routing/fallback plan discussed in tech deep-dive:
  * Primary model: open LLM v2-q8 (quantized variant) on Dedicated GPUs for cost/throughput.
  * Canary model: same architecture but a fresh pinned version to validate rollout.
  * Fallbacks: auto-fallback to Hosted-compatible model variant (smaller footprint) when Dedicated pool capacity saturated.
  * Region failover: start in us-west-2; if health checks fail, route to us-east-1 with reduced batch sizes.
  * Rollback: automatic traffic cutback to Hosted API if
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 20: `qst_0069::metadata` · N=50000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The retrieved chunks are on-topic regarding SaaS and API evaluations but do not address the specific question about GPU rebalancing and slot capacity. The failure is due to lexical mismatch, as the retrieved documents do not match the specific context of the question.

### Question

Who is the solutions engineer assigned to the mid-market product analytics SaaS account running a two-week parity POC before moving from a hosted LLM API to dedicated nodes?

### Gold document(s)

#### GOLD `dsid_b9eb7e39bc2e4f65814c42358089d49b`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_5f0f36543c1a4dc3b83c4dab1995c021`

```
Summit Lake Insightworks

Mid-market analytics SaaS evaluating Redwood. Started with Hosted API for quick integration; now moving to a 4-week Dedicated POC to validate latency, cost and routing controls. Primary goals: predictable p95 latency, cost per 1M tokens, and robust rollback/fallback behavior for regional outages.
Finalize Dedicated POC access + sign NDA; schedule canary config workshop
SLA/latency targets need validation under burst load
security review pending for KMS integration
legal reviewing data residency wording
2025-11-18 - Lead created from website demo request
2025-12-02 - Intro call (Jordan) - product fit for personalization + search
2026-01-08 - Hosted API spike trial (2 weeks) - basic integration done
2026-02-14 - Security questionnaire submitted (Priya) - SOC2 & KMS asked
2026-02-20 - Pricing deck v2 shared (drive link)
2026-02-28 - Decision to run Dedicated POC; AE + SE kickoff
2026-03-02 - POC onboarding meeting (Fireflies ff_2026-03-02_101b)
2026-03-08 - POC baseline load test scheduled
Customer: product + infra leads (CTO + platform lead)
They liked hosted API latency but want isolation and predictable throughput for peak events
Asked for canary strategy,
…[truncated]
```

#### #2 `dsid_facae219b4374259b471a45e3ee85c57`

```
Zenith Helix Software

Product analytics SaaS looking to replace batch inference pipeline with low-latency model serving for user-facing features: contextual help (support-agent), in-product summarization of session logs, and runtime personalization. Started on Hosted API for fast proof; moving to Dedicated for predictable throughput and data isolation.
Key contacts: CTO - Anya Ramesh (security lead), Head of ML - Ben Ortiz. Customer started with hosted_api pilot (Jan-Feb) to validate model quality; positive on quality but cost and p95 variance are concerns. Decision criteria: 1) p95 latency target ~<120ms for 32-token responses for support-agent flows, 2) stable throughput 60-100 QPS during business hours, 3) ability to failover between regions with <30s degraded window, 4) audit logs + KMS + SSO. They explicitly said: 'We can't have noisy neighbor spikes during peak hours' and asked about dedicated GPU pools and autoscaling. POC asks: Dedicated reserved pool with canary traffic at 5-10% for 48-72h, validate canary metrics (latency, error rate, token cost), then ramp to 50% with automatic fallback to an L2 model variant or hosted fallback if performance drops. Rollback plan must i
…[truncated]
```

#### #3 `dsid_a01626c8e33e45a0a876df2f9b499789`

```
Copper Summit Solutions

Top-line: mid-market product analytics vendor. Started with Hosted API POC in Q4; impressed with latency and easy SDKs. Now moving to Dedicated for isolation and predictability. Legal/procurement heavily engaged. Notes below are a mix of call snippets, internal handoffs, and open items.
2026-02-18: Kickoff Hosted API POC — demo + initial traffic; SE present (Priya). Fireflies transcript ff_2026-02-18_8492.
2026-03-03: POC review w/ product + infra. Discussed Dedicated sizing and autoscale options. Fireflies ff_2026-03-03_9021.
2026-03-05: Pricing follow-up — sent committed throughput tiers and illustrative ARR math (drive link).
2026-03-09: Legal call to review MSA/DPA redlines — Copper Summit provided annotated MSA (LEGAL-78).
2026-03-10: Internal Redwood meeting with Solutions + Sales to prepare redline responses, assign owners.
Primary workload: in-app assistant (chat) + document search + reranking for suggestion UX.
Latency target: P50 < 200ms, P95 < 600ms for chat messages (end-to-end).
Throughput: sustained ~40-60 rps at peak burst (30min windows) across US region.
Cost sensitivity: moderate — willing to commit to reserved capacity if unit economics a
…[truncated]
```

#### #4 `dsid_cefd9d05ba684ca98e6be1172ec8cbb9`

```
Sapphire Helm Solutions

Account summary: mid-market product analytics vendor building an AI assistant inside their product and improving semantic search. Evaluating Redwood Hosted API first to prove integration and latency in EU region, then moving to Dedicated if cost/perf tradeoffs make sense.\n\nKey asks / requirements: \n- EU data residency: all customer data stored in EU regions for PII indices.\n- Multi-region routing: want EU primary + failover to NA only for short outage windows; concerned about latency jumps.\n- Latency/throughput: p95 generation latency target <150ms for short responses; sustained throughput ~50 rps during peak.\n- Cost sensitivity: tight unit economics; need conservative estimate for token cost and percent savings for dedicated reserved capacity.\n- Security: SSO (SAML), audit logging, KMS integration for key material, retention controls for logs and embeddings.\n\nPOC plan discussed: 2-week hosted-region POC in eu-west with representative traffic replay, measure p95 and token cost; parallel RPS load test to validate batching behavior and KV cache hit assumptions. SE to prepare simple routing tests showing failover latency to NA and expected degradation
…[truncated]
```

#### #5 `dsid_6d1056e675d442a1a0a2bcd19fe25964`

```
Marlin Crest Analytics

Mid-market analytics SaaS evaluating Hosted API POC then Dedicated/VPC — SOC2 and SSO are gating items for procurement.
Start: hosted_api for rapid prototype (chat + embeddings). Move to: dedicated (reserved GPU pool) behind VPC with KMS for keys and audit logs. Consider Redwood Optimize recommendations post-POC.
- Decision makers: CTO (technical), VP Product (budget), Head Infra (security).
- Desired latency: 95th <= 120ms for short chat; batch reranking throughput target 200 qps with autoscale.
- Data residency: selected EU clients need data stored and processed in eu-west-1.
- Desired contract: 12-24 month reserved capacity with burst credits.
- Preferred billing: monthly with token-level visibility for cost ops.
Qualification notes:
- Mid-market B2B SaaS (analytics + customer insights). Heavy multitenant ingestion, anonymized PII layers.
- Primary ask: start on Hosted API (fast MVP), prove latency/cost, then migrate to Dedicated (VPC) for steady traffic and isolation.
- Quote from CTO on 2026-02-28 call: "Need predictable tail latency under 120ms for 95th pct on short-chat flows. SOC2 artifacts non-negotiable."
- They ran a small Hosted POC (Feb) for emb
…[truncated]
```

#### #6 `dsid_9a9b059554874f379b2adbe8be7db281`

```
Silvershore ProductWorks

Mid-market product analytics vendor building embedded AI features for in-app search and help. Team: CTO Anya Patel, Product Lead Jonah Ramirez. Wants to trial hosted API to move fast; will evaluate Dedicated if unit economics + latency predictable. Primary asks: 1) <200ms median latency for chat/search at 95th pct under typical load; 2) throughput ~200 rps for embeddings pipeline during daily batch jobs; 3) clear per-token unit economics and guidance for batching/caching; 4) ability to pin model versions and a clean rollback story. Cost sensitivity: high — BAU run will be thousands of daily queries, want to avoid 3-4x overrun. SE meeting noted: "If we can show 30-40% token cost reduction w/ batching+KV cache + INT8 quant profiles, they'll consider Dedicated commit." Legal flagged data residency for EU customers; product requires VPC and KMS integration. Workshop goals: run a cost model with their token distribution, advise batching window and cache TTLs, recommend quant profiles for accuracy tradeoffs, produce expected $/1000-query matrix. POC scope: 2-week hosted API proof (ingest sample customer data, run embeddings, evaluate latency & output quality), t
…[truncated]
```

#### #7 `dsid_1673cbb4976a4394ab74862d44128eb9`

```
Stratus Grid Works

Mid-market product analytics platform focused on in-app assistance and contextual search. Team: CTO (Anika Patel), Head of Product (Marco Velez), Eng Lead (Priya Rao). Evaluating Hosted API first for dev speed; want to run pilot in Q1 then move to Dedicated/VPC for production. Key quote from CTO: "Need predictable latency under 120ms p95 for chat and sub-50ms for vector lookups." Cost-sensitive but willing to commit to reserved capacity if SLA and security meet reqs.

Recent security asks: SOC2 report (in last 12m), SSO/SAML integration pattern, audit log retention (7+ years), KMS/HSM key control, option for data residency in us-east-1. Also need network diagram for VPC peering + proxy requirements.

POC plan: 6-week pilot. Week 1-2: Hosted API integration + synthetic traffic. Week 3-5: Dedicated sizing test with 2 model variants (open Llama2-70B quantized & rw-medium). Week 6: performance/cost report + exec demo. 

AE notes (Maya): initial demo 2026-01-22 went well; SE ran loadbench; Marco wants hands-on pricing models (unit economics). Security team asked for Redwood's data retention controls and ability to disable logging for sensitive endpoints.

Open items:
…[truncated]
```

#### #8 `dsid_de9c1d389e964346a5d863550ba817a2`

```
Hightide ProductWorks

Evaluating Hosted API -> Dedicated. Run POC, then cost optimization workshop to determine batching/caching/quantization levers and Dedicated sizing/pricing.
Mid-market product analytics company evaluating hosted API as fast path, then Dedicated for predictable throughput and data isolation. Very cost-sensitive: primary driver is unit economics — wants to understand per-query cost at production scale. QPS profile: baseline 3-5 QPS, peak bursts to ~35 QPS for nightly rerank jobs. Latency targets: chat P50 ~150-250ms, embedding batch jobs acceptable up to 2s per batch (parallelized). Prefers open model variants but flexible if Redwood quant/profiles drop cost significantly. Security: SSO + SAML, SOC2 required, KMS for key control, retention rules for PII. Stated quote from CTO: "We need a predictable $/MAU hit model and a clear path to cut inference spend 3x before committing dedicated pool." POC plan: 2-week hosted POC with sample corpus and test harness -> measure latency/cost with batching/caching -> 1-month Dedicated trial if numbers hit threshold.
2026-01-18 - lead sourced from webinar ("Optimizing LLM unit economics")
2026-01-25 - intro call (AE Jordan Par
…[truncated]
```

#### #9 `dsid_4ccec796173f458889b2801084f777e7`

```
Ambervale DigitalWorks

Customer uses LLMs for product search augmentation + support assistant. Need embeddings + chat for contextual answers and reranking. Production requires predictable throughput (120 qps steady), <120ms p95 latency, and strong data controls (VPC, KMS, audit logs). Will begin with Hosted to validate prompts, then move to Dedicated/VPC for GA.
Status: warm. Mid-market product analytics vendor building a customer-facing search and AI assistant. Started POC on Hosted API around Jan — quick results but concerned about per-token volatility and data residency. After demo, they requested Dedicated (VPC) for predictable throughput + isolation. Security team (Lead: Marcus Chen) is strict: wants SOC2 Type II or equivalent, SSO/SAML integration, audit log retention >= 12 months, and KMS/HSM compatibility. SE Priya ran a live runbook walkthrough on 2/24. Notes from call: 'We need predictable 99th p95 latency at <120ms for search flows' and 'Can you guarantee no egress to non-approved regions?'.

Key POC facts:
- POC: hosted_api -> 3 endpoints (search, chat-helper, doc-qa)
- Observed avg latency (hosted): 80–110ms token generation under typical load
- Peak QPS target for pr
…[truncated]
```

#### #10 `dsid_79c12603b0d146dc92f30c8a56847276`

```
Harrow Cove Solutions

Quick summary: mid-market product analytics SaaS. primary goal: add LLM-driven support assistant + embed search across knowledge base.
Started with Hosted API to move fast; POC for chat + embeddings completed. Good dev velocity; low friction onboarding.
Now evaluating Dedicated for predictable latency and data isolation. main ask: VPC peering + KMS for key control.
Security team requires SOC2 evidence, DPA with EU/NA residency clauses, and ability to set token retention to 30 days max.
Legal returned MSA with multiple redlines on IP, liability cap, and audit rights — want vendor to accept mutual indemnity. Jordan: "we can be flexible but need standard carveouts."
SE (Aisha) ran Dedicated demo 2026-02-05: showed autoscaling pools, latency profiles at 4k seq, and prefix caching. CTO liked batching controls.
POC notes: Hosted API 2-week POC showed p95 latency ~120ms for chat; embeddings pipeline stable but costy at full sync. Optimize recommendations reduced cost by ~18% in sim.
Procurement wants line-item pricing: baseline reserved GPUs + burst credits + data egress assumptions. asked for 3-year vs 1-year pricing.
Finalize MSA/DPA redlines + confirm Dedicated c
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 21: `qst_0079::basic` · N=75000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The retrieved chunks are on-topic regarding inference timeouts but do not address the specific mitigation proposed in the gold chunk. The failure mode is a lexical mismatch, as the retrieved documents discuss similar issues but not the exact mitigation strategy. The chunk quality is high, but relevance to the specific question is low.

### Question

In a morning account blitz note from May 2026, what was the proposed mitigation to address repeated inference timeouts for a healthcare customer with a mid-June renewal?

### Gold document(s)

#### GOLD `dsid_9776bd75ffbb4ca7b10669be1512daa3`

```
Account Blitz Log — AM rounds

Morning blitz (short log + action list) — May 10 2026

08:10 — quick pass through high-risk accounts (15 min radio round):
- Fortis Health (A): renewal 2026-06-15 (60d). Usage trending down 12% MoM, timeout errors in last week.
  - Immediate: open support escalation for recurring timeouts (TKT-2189) — assigned to Diego, ETA EOD.
  - Prep for QBR: collect 30/60/90 day token usage chart, latency P50/P95, recent error traces (include example payloads).
  - Risk mitigation suggestion: propose 10% reserved burst for their peak windows and enable KV prefix caching on main inference route.
  - Owner note: call scheduled 2026-05-22 10:00 PT (pre-brief 05-21). Align playbook with Aisha for canary fallback.

08:28 — Ionata (B): renewal in 9 months, churning signal: support queue volume + decreased embeddings quality complaints.
- Action: confirm evaluation dataset used for embeddings baseline (linked to CS-5098). Ask research for quick re-eval (does quantization profile 4 degrade their similarity?).
- Short script for outreach: "Quick check-in — we noticed changes in similarity scores, can we sync on a small eval set?"

08:40 — Nimbus Labs (C): high-volume, no immediate renewal risk but alerted on cost spike.
- Investigate batching settings: current batch window = 40ms. Suggest moving to 20ms for steady traffic; recommend caching high-frequency prompts.
- Ticket to infra: request cost breakdown per model variant for last 30 days (include quantized vs fp32).

08:52 — Support follow-ups to clear before noon:
- TKT-2189 (Fortis) — reproduce logs + root cause hypothesis (diego)
- TKT-2205 (custom tokenizer bug, queued) — triage with Eng-DX, ask for patch ETA
- TKT-2211 (private deploy networking flake) — SRE loop in, escalate if not stabilized by 12:30

09:10 — QBR checklist items to attach to deck (for all top-10 accounts):
- One-slide health summary (usage, latency, cost delta, top incidents)
- Proposed optimization (batch/caching/quant) with estimated cost delta per month
- Open risks + mitigation plan (dates, owners)
- Ask / decision for customer (e.g., enable dedicated pool, approval for extra commit)

Micro TODOs (quick hits):
- [ ] Pull F
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_872dd780a37c4e9791115a2f73f54d3d`

```
Intermittent region-affinity flip causing bursty cross-region inference and timeouts for Chronos Health

Issue summary: Chronos Health reported sudden elevated p95/p99 latency and a spike in streaming request timeouts beginning at 2026-03-10 09:40 UTC. The customer's traffic, normally pinned to us-west for low-latency inference, experienced intermittent routing to eu-west for a subset of requests, producing cold KV-cache misses and high tail latency. Impact: Several production endpoints used by Chronos' clinician-facing workflow saw ~15% request failures (stream disconnects / 504s) and 3x p99 for generation calls over a ~40 minute window.
Customer-facing production inference degraded for Chronos Health: increased 504s and stream disconnects, user-visible timeouts in the care app during 09:40-10:20 UTC. Estimated 12k requests impacted, some time-sensitive workflows delayed.
prod | us-west (customer region affinity expected)
smart-routing
serving-runtime
api-gateway
cache
1) Send sustained generation requests from a Chronos Health customer account with region affinity set to us-west (via account-routing tag).
2) Observe p50/p95/p99 for streaming and non-streaming endpoints over 5-10 
…[truncated]
```

#### #2 `dsid_06a6ac5f75494a8db16663ef957f6e94`

```
Healthcheck throttle + runaway backoff causing elevated 5xx and runtime restarts during tenant fairness reshard

Issue summary:
Customer (NimbleHealth, dedicated tenant) reported an abrupt increase in 5xx responses and elevated latency starting ~2026-03-13T09:10Z. Errors are predominantly 502/504 from the API gateway and a subset of upstream serving runtime processes reporting OOM/kernel-fallback restarts. Impact: multiple production endpoints degraded (chat generation and embeddings).

Impact:
- Customer reports ~15% request failure rate for the affected routes over a 30m window.
- Real-time product features degraded for end users; increased retry traffic observed.

Environment:
- Prod cluster: us-east, tenant: nimblehealth-dedicated-pool-7
- Affected routes: /v1/chat/completions, /v1/embeddings/batch
- Autoscaler: horizontal with warm pools; healthcheck policy: aggressive (3s interval, 2 failures to mark unhealthy)

Steps to reproduce / observed pattern:
1) Send steady traffic for chat route at 120 rps with sporadic embedding spikes.
2) After a spike, API gateway returns 502/504 for ~1-3 minutes, then partial recovery followed by repeated micro-waves.
3) Runtime logs show repeate
…[truncated]
```

#### #3 `dsid_17e77b6582ae4c27b73e3ca4bf81f4a9`

```
Edge priority fanout amplification causing intermittent 5xx and streaming drops during tenant concurrency ramp

Issue summary: During a tenant concurrency ramp for customer NimbusHealth (dedicated), we observed sustained, intermittent 5xx responses and streaming session drops starting at ~2026-03-13T22:05UTC. The pattern correlated with an edge priority change combined with an automated keystore rotation window. Impact: Multiple production clients reported degraded streaming sessions (short responses, aborted streams) and increased 5xx rate (~8% error-rate for affected tenant traffic) for ~55 minutes. Environment: prod - us-east; affected tenant on Dedicated pool A; traffic spike originated from a scheduled data migration at the customer's side that produced bursty concurrent short requests. Observed behavior: API-Gateway accept queue grew rapidly; hedged/mirrored requests amplified fanout to multiple runtime pools; a transient TLS handshake slowdown during keystore rotation increased handshake latency and caused upstream connection stalls; runtime threadpool utilization went to 95% and a subset of runtime proxies returned 502/503 on request hedged paths. There were frequent short-
…[truncated]
```

#### #4 `dsid_15407e001bb34739b1116698c4a9a397`

```
Elevated 502/503 error floor on streaming chat route during priority-handshake stampede for NexaHealth (dedicated)

Issue summary: Starting 2026-03-12 08:14 UTC we observed a sustained elevation in 502/503 responses on the /v1/chat/streaming endpoint for NexaHealth's dedicated tenancy. Impact: customer-facing failed requests for streaming chat sessions (intermittent 5xx, ~12-18% error-rate for the tenant), degraded latency for successful sessions, and visible client reconnect churn. Environment: prod - dedicated fleet in us-west-2, tenant pinned to redwood-open-7b-quant-v2. Steps to reproduce: 1) Initiate ~300 concurrent streaming connections that immediately start an auth/handshake then send a short transcript; 2) Observe connection establishment / TLS handshake wave; 3) Watch 502/503s and streaming session resets escalate after ~30s. Observed around tenant priority routing changes and a burst of hedged retries from the edge. Logs & dashboards: refer to apigw/error_rate (2026-03-12 08:10-09:00), runtime-proxy/handshake_metrics, and kvcache/lock_counts. Customer report: NexaHealth observed client SDK reconnect loop and requested immediate mitigation.
08:18 UTC - Alert from SLO that
…[truncated]
```

#### #5 `dsid_045196dc3e594c099b1877ba0cac18c1`

```
Adaptive batching config swap caused tail-latency cascade; request for safe unwind and verification

Issue summary: Customer observed increased 95th/99th token latency and sporadic streaming disconnects immediately after we enabled an adaptive batching experiment for their tenant (coalesce_small_reqs=true, adaptive_grouping=aggressive) and a matched experimental quant profile (q8_dyn_prefetch). They requested guidance for a safe unwind: minimal customer disruption, no model-quality regressions, and a reproducible verification checklist.
Several production routes for BrightHealth AI show 95p latency up from ~180ms to 750-1200ms and periodic client stream resets. Traffic is on Dedicated pool assigned to the customer; estimated 12% of user-facing requests affected. Business impact: user timeouts and degraded UX for conversational flows; P1 SLA breach risk.
1) Tenant uses dedicated pool with tenant_id bhai-prod-42.
2) Apply optimizer profile: {coalesce_small_reqs: true, max_batch_wait_ms: 15, adaptive_grouping: aggressive, quant_profile: q8_dyn_prefetch}.
3) Replay synthetic production load (mix of short prompts and streaming long generations).
4) Observe that small concurrent requests
…[truncated]
```

#### #6 `dsid_4412fbd468c64de7baf04f9064b80911`

```
AegisPharm private deployment: multipath failover amplified requests, ordered-stream reassembly failures, and billing exposure

Issue summary:
During a scheduled nightly batch from AegisPharm (private deployment, eu-west), the Redwood private control plane entered a multipath failover loop causing amplified request fanout, repeated retries, and ordered-stream reassembly failures for streaming completions. Symptoms started at ~2026-03-10T01:12Z and lasted for ~90 minutes.

Impact:
- Customer observed duplicate completions and truncated streaming transcripts across ~18% of requests for the 90-minute window.
- Significant token accounting discrepancies led to a billing exposure (estimated 2.4x token inflation for affected requests).
- Several model variants in the customer's pinned rollout experienced high tail latency and intermittent 5xx errors.
- Business impact: AegisPharm paused nightly ingestion jobs and opened an escalation call.

Environment:
- Deployment: Redwood Private (customer-managed control plane)
- Region: eu-west-1
- Cluster: aegispharm-prod-cluster-3 (dedicated GPU pool)
- Canary config: pinned redwood-quant-4bit behind routing policy with multipath failover enabled

…[truncated]
```

#### #7 `dsid_fb91791924d245218e2b99799d7787bc`

```
Repeating 429s for tenant caused by delegated service-account refresh loop consuming burst credits

Issue summary:
Customer DataHarbor reports periodic waves of 429 throttles across multiple endpoints during daytime ingest windows. They see server-side rate-limit rejections for a sustained 30–90 minute window even though aggregate token usage reported in their console remains under their committed burst and sustained quotas.

Impact:
- Multiple background jobs and webhooks failing with 429s (non-idempotent retries cause downstream duplicates).
- Customer reports increased error rates in their SLA dashboards and two supportable customer incidents.
- Revenue-impacting: delayed batch commits and retry storms.

Environment:
- Dedicated tenant on prod-us-east, dedicated GPU pool.
- Jobs originate from a delegated service account (service-account-managed by DataHarbor) that rotates short-lived credentials every ~2 minutes.

Steps to reproduce (provided by customer):
1) Deploy connector that rotates delegated SA keys and launches 8 parallel upload workers.
2) Each worker uses temporary credentials to start streaming SSE connections + periodic background flush jobs.
3) Observe console & cl
…[truncated]
```

#### #8 `dsid_971ebeb1c4304a27a0d417c37f085a14`

```
Intermittent 429 bursts for multiplexed websocket chat causing degraded UX

Issue summary: NimbusHealth is seeing intermittent bursts of HTTP 429 responses returned to multiplexed websocket clients on the hosted API during peak business hours. Impact: Users in their clinical triage chat are experiencing message failures and UI retries, increasing perceived latency and leading to dropped conversations. Scope: Affects ~10 client connection pools from NimbusHealth (enterprise account) in us-east region; seen across redwood-chat-small and medium models. Expected: Multiplexed websocket connections should see smoothing by token-level and connection-level rate limits with transparent backpressure, not sudden 429 bursts. Observed: Spikes of 429s lasting 20-40s every ~15 minutes, correlating with bursty fan-out from a single internal service. Steps to reproduce: 1) Establish multiplexed websocket session using shared API key for multiple browser clients (as customer implemented). 2) Simulate parallel message bursts (20 simultaneous requests over the same websocket multiplex) with messages that produce ~80-200 tokens. 3) Observe intermittent 429 responses returned with X-RateLimit-Remaining:
…[truncated]
```

#### #9 `dsid_8fffd704ff4c4744a7ac815e117abda3`

```
Aggregate latency spike caused by client SDK retry amplification against silent quota enforcement

Issue summary:
Customer BrightHealthAI reported intermittent but sustained inference slowdowns and request timeouts for live traffic hitting rw-llm-large-v1 in us-east. Initial symptom: spikes in p95/p99 latency and a rise in perceived client-side timeouts.

Impact:
- Multiple production endpoints for BrightHealthAI experienced higher tail latency starting 2026-03-11 21:00 UTC, with cascading 5xx/timeout observations from their frontend.
- Customer reports degraded user experience and several aborted sessions. Estimated ~12% request failure for the last 12 hours for the tenant.

Environment:
- Dedicated tenant on prod (us-east), running rw-llm-large-v1 pinned to model:v2026-02-28.
- Customer using internal SDK (v0.9.2) with default retry settings (immediate retry ramp, no jitter).

Steps to reproduce (customer):
1. Send a burst of concurrent streaming generation requests (20-50/sec) from their service using SDK v0.9.2.
2. Observe initial 429 responses followed by client-side timeouts and long-tail latency.
3. When retry storms occur, end-to-end p95 jumps >3x and many requests fail wit
…[truncated]
```

#### #10 `dsid_461588786f8544a899f5e632f040bcd3`

```
Clarify rate-limit accounting for internal proxy with per-user signed-keys triggering intermittent throttles

Issue summary: Customer reports intermittent 429 throttles originating after they introduced an internal forwarding proxy that reuses persistent HTTP/2 connections and issues per-user signed keys for downstream requests. Impact: Production traffic for NimbleHealth's inference feature sporadically receives 429 responses during normal load peaks, causing degraded user experience for some customers and automated ingestion backfill failures. Environment: prod:us-east (primary), eu-west (replicated). Affected endpoints: /v1/chat/stream, /v1/embeddings/batch.

Observed behavior: NimbleHealth sees short bursts (tens of seconds) of 429 responses across many users, with throttle headers reporting a near-empty token bucket for the tenant. When the proxy is bypassed and clients call Redwood directly using same signed keys, the issue disappears. Customer believes token accounting should follow API key only and not be affected by connection multiplexing or signed key re-issuance frequency.

Customer-provided context: NimbleHealth uses an internal gateway that mints short-lived signed ke
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 22: `qst_0084::metadata` · N=5000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant to enterprise requests and security concerns but do not directly address the specific question about reducing triage time using an intake checklist. The failure mode is lexical mismatch due to the lack of direct relevance to the question's specific context. The chunks are generally on-topic but not directly answering the question, leading to a low rele

### Question

For the SMB legaltech prospect owned by Alex Martinez that needs SAML SSO and US-only data residency, what month is the close forecasted for?

### Gold document(s)

#### GOLD `dsid_1d13149e585f4be398015d748e24e449`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_3bc3170ead63470eaef9a53ca835cec0`

```
Trialbridge Legal Solutions

Inbound via website contact form 2026-01-18. SMB lawtech focused on small litigation firms — indexing confidential case docs and client communications. Wants quickstarter: self-serve hosted API, US-only region, strong audit logs. Quote from founder: 'We cannot have PHI/PII leave US borders; audit trail is table stakes.'

Discovery call 2026-02-22 with Evan (AE) + Priya (SE). Asked about: token retention, audit log retention windows, SSO/SAML support, and whether Redwood can guarantee US region routing for hosted. Very cost conscious — early-stage paying customers currently on Mixpanel/Stripe integrations; expects modest monthly usage initially (embedding heavy, bursts during litigation prep).

Technical notes from SE: prefer smaller base model with embeddings + reranking for search; latency targets: p50 < 300ms for embedding lookups, generation latency not critical but prefer streaming for long summaries. Wants ability to pin model version, view token-level cost in console.

Follow-ups done: sent security FAQ + SOC2 summary (drive link) 2026-02-24, emailed step-by-step quickstart for Python/Node 2026-02-25. Provided sample IaC snippet to ensure traffic 
…[truncated]
```

#### #2 `dsid_99da2cf6cc6547e985b1dcb199819ba8`

```
Pineglen Capital Tech

Inbound SMB lead via self-serve signup (trial credits used). CTO (A. Lopez) flagged SOC2/SSO early — security team will not allow shipment of user-identifiable transaction data to vendors without SOC2 evidence. Initial ask: can we start on Hosted API in public cloud while we evaluate Dedicated/VPC for next quarter.

Recent timeline (short bullets):
- 2025-11-03: Signup with test keys; simple embed experiment (doc search) ran fine.
- 2026-02-25: AE intro call (Maya) — high-level requirements, product fit, cost sensitivity.
- 2026-02-26: Sent baseline pricing deck (drive link) + SOC2 one-pager.
- 2026-03-01: SE discovery call (Ravi) — walked through typical latency/throughput, discussed batching and cost tradeoffs. Fireflies: ff-20260301-3421.
- 2026-03-05: Security kickoff; Pineglen sent vendor questionnaire (SLA, incident response, retention).

Requirements summary (as paraphrased):
- Workloads: customer support chat widget (low-latency chat), embeddings for internal agent search, reranking of transaction alerts for fraud triage.
- Latency targets: 150-300ms token latency for chat (~95th pct target), end-to-end 300-600ms per response acceptable for first pass
…[truncated]
```

#### #3 `dsid_39bcc08d966442039e8a9afce31c3aff`

```
Sable Orbit AI

Inbound: came from webinar (scaling inference for product teams), AE outreach 2025-11-06
Discovery call 2025-11-12 w/ Head of Product (Maya Chen) + Eng lead (Carlos Rios). Primary driver: replace internal embeddings pipeline that is costly and brittle.
Initial POC (hosted API) 2026-01-10 -> 2026-02-07: built search prototype against 12M doc corpus. Results: relevance good, embeddings ~2.4ms per doc on avg, cost within expected range for dev but projected TCO too high for production traffic.
Tech note: hosted p95 generation latency observed ~150ms from us-west; target for customer product is p95 <= 120ms for chat and <= 100ms for reranking. Dedicated expected to hit p95 ~80-110ms based on our perf guidance.
POC ask: reserved burst capacity for quarterly releases, prefix/KV caching to reduce token cost on conversational flows, ability to pin model versions for A/B rollouts.
Optimize feedback: Redwood Optimize suggestion to quantize embedding model to int8 for their workload; estimated embedding cost reduction ~35-45% without measurable quality loss on eval set.
Pricing conversation: prefer a tiered committed capacity deal (monthly) rather than pure on-demand; finance 
…[truncated]
```

#### #4 `dsid_48e13d429774409db3aaa152d19407b6`

```
RiverMark Assist

Inbound SMB lead. Signed up self-serve trial on hosted API. CTO (A. Patel) is the primary security contact. Immediate asks: SOC2 Type II evidence or concise SOC2 summary, full sub-processor CSV, DPA for legal review, data residency options (US/EU), and default retention for embeddings. Wants legal sign-off before trial end (two weeks).

Call snippets: 
- 2026-03-07 intro (Maya/Carlos): good product fit for KB + triage bots; latency ok (P95 150-250ms in test).
- 2026-03-09 security sync: "We can't push to paid until we see SOC2 or equivalent and a sub-processor list."
- 2026-03-11 email: attached logs; asked "where do embeddings live and how long".

Sales note: Low-touch onboarding. Focus follow-ups on security artifacts, not feature deep-dives.
Hosted API will power a helpdesk assistant: real-time chat, semantic search over internal KB, and reranking recommended articles. Traffic small (10-30 qps), p95 latency target ~300ms. Cost sensitivity moderate; must avoid storing PII without controls.
Is Redwood SOC2 Type II in-scope for hosted API?
Who are the sub-processors for compute, logging, monitoring?
Can we get a DPA and choose EU/US residency?
What is default embe
…[truncated]
```

#### #5 `dsid_1e0fc5d675ce479dbb6fe082402a49c5`

```
Bayleaf Cartmatic

Inbound SMB lead from paid ad. Key ask: "Do you persist prompts and logs?" — quote from legal. Wants explicit opt-out + purge for user-submitted PII. Sandbox POC: 2 weeks, estimate ~100k tokens/month. Use-case: customer support chatbot + product recs; embeddings for search. Prefers hosted API (self-serve) but needs clear retention guarantees before procurement. Cost sensitivity noted: prefers usage-based pricing; will reconsider Dedicated only if steady 500k+ tokens/month. Security asks: SSO, audit logs, ability to disable prompt retention and an API to purge per-customer data. Quoted: "We can't have customer support transcripts stored indefinitely — need 30 day max unless we opt in." AE suggested default 30-day ephemeral logs for hosted tier; legal wants written policy and an option to opt-out of non-essential logging. SE to confirm whether admin-level purge is available and how long KV/prefix caching persists. References: procurement deck (drive link), legal thread (gmail), Fireflies transcript attached. Next: provide formal retention matrix and sample privacy FAQ, then legal sync. Short-term blocker: internal legal sign-off and product confirmation on purge AP
…[truncated]
```

#### #6 `dsid_d79518c427654533a01173792f51f986`

```
Onyx Cloud Labs

Mid-sized fintech platform building personalization and compliance-sensitive customer support workflows. Heavy on PII and transaction history, requires strict controls and auditability.
Workload: real-time support chat + reranking over transaction histories. Latency targets: p95 < 120ms for chat, throughput 200 qps. Data residency in US, strict retention rules. Must support SSO (SAML), audit logs, KMS-managed keys, and external SOC2/ISO evidence. Preferred on-prem or VPC private deployment for initial rollout.
Status: Closed-lost (security)
- Opportunity progressed quickly after demo (Dec 2025) — CTO enthusiastic about latency and routing features.
- Security review started Jan 2026. They asked for SOC2/ISO evidence and completed our security questionnaire.
- Legal asked for attestations (SOC2 report or ISO certificate) + controls mapping to our KMS/HSM recommendations.
- On 2026-02-18 security said: 'We cannot accept self-attestation; need audited reports. If vendor refuses to provide, corp legal will not sign.'
- Customer unwilling to share internal compliance audit extracts and expected vendor to provide public SOC2/ISO docs. Our hosted roadmap for SOC2 in H2 20
…[truncated]
```

#### #7 `dsid_de174c9811834eff9929fd6d4efb3d30`

```
HelixBridge Healthtech

Overview: enterprise healthtech company building clinician-facing search and summarization across EHR notes. Heavy emphasis on PHI handling, audit trail and data residency.

Timeline / recent activity:
- 2025-11-18: Intro call (AE Maya + SE Jared) — interest in embeddings-based clinical search; target: 200ms median latency, 10 qps sustained for search. Fireflies id ff_2025-11-18_helixbridge_intro.
- 2025-12-03: POC kickoff — ingest pipeline for 50k patient documents, testing Redwood hosted private VPC. Fireflies id ff_2025-12-03_poc_kickoff.
- 2026-01-22: Security deep-dive with InfoSec (requested SOC2 Type II, ISO artifacts, pen test summary). Fireflies id ff_2026-01-22_security_review.
- 2026-01-25: Shared Redwood security pack + DPA template (Gmail thread thread-CA+security-qna-20260125).
- 2026-02-03: HelixBridge legal returned heavily redlined MSA + DPA: unlimited liability clause, data residency clause requiring EU-only for specific flows, 90-day breach notification tightened to 24 hours. Procurement asks for vendor audit and supplier attestation.
- 2026-02-12: Redwood SE provided technical responses and proposed mitigation (encryption at rest with KMS
…[truncated]
```

#### #8 `dsid_178f5ada27f64226843c83f032cf3481`

```
Larkspur KnowledgeWorks

Mid-market legal-tech customer. POC started (doc-search + summarization). Integration progressed but stalled mid-POC due to no engineering cycles and security/budget blockers. Outreach unanswered since Jan; at-risk for closed-lost by mid-March.
Summary: POC kicked off Nov 2025 for confidential contract search + summarization. Initial integration went well (S3 peering + VPC established) but we lost momentum after week 3. POC milestones missed: embedding job + reranker validation not completed. Eng team pulled off to higher priority project (mobile app rewrite).

Key quotes: "we love the perf but can't commit cycles until Q2 hiring lands" — Head of Search (K. Morales). Legal wants full KMS + residency proof before moving to prod. CISO opened formal security questionnaire 2026-01-05, still awaiting answers.

Decision context: internal pilot vs building in-house. CTO mentioned interest in an internal lightweight reranker; procurement flagged budget freeze for external infra through Feb. Sales comp: account at-risk; competitor (InHouseModelTeam) pushing custom infra as cheaper long-term.

Recent outreach: Maya sent trimmed POC proposal 2026-01-14 (drive link abo
…[truncated]
```

#### #9 `dsid_47063f6493b143959a76a68f294b1b67`

```
StellarForge SaaSworks

Legal review redlines: finalize MSA/DPA responses + confirm SLA uptime targets
MSA indemnity and liability cap negotiation
DPA retention & deletion language for EU customers
SLA: target uptime and credit formula vs our internal requirement
Pricing model for Dedicated reserved GPUs vs burst usage
2025-08-12 - Intro call (AE Alyssa) — high level use-cases: support agent + code assistant; interested in fast ramp
2025-09-05 - Hosted API POC started — 2-week eval, sample dataset for help center ingestion
2025-09-18 - POC results: embeddings quality ok, average latency 120ms token-stream (hosted), cost higher than expected
2025-10-02 - Demo of Dedicated offering (SE Marco) — capacity planning discussion, autoscale options
2025-10-15 - Pricing deep-dive with finance — request for 12-month reserved commit discount and overage rules
2025-11-04 - Security questionnaire submitted; SOC2 cert attached; asked about KMS + audit logs
2025-12-01 - Internal procurement: legal routed MSA/DPA to vendor (Redwood); initial redlines returned
2026-01-10 - Follow-up call on redlines (AE/SE/Legal) — highlighted indemnity, liability cap, data residency
2026-01-25 - SLA draft received 
…[truncated]
```

#### #10 `dsid_74f7199105d04593a891d0f2ccdd794d`

```
Obelisk Dataworks

Mid-market B2B SaaS: analytics + knowledge product. Started on Hosted API (POC) -> strong perf for embeddings & doc-search. Asking to move to Dedicated for predictable throughput and data isolation. Legal pushing for MSA + DPA changes. Finance needs clearer unit economics before committing. SEs flagged KV cache behavior for long-context retrieval.

Key quotes: 'We need deterministic cost at 95th pctl, can't have surprise token bills' — Head of Product.

Tone: pragmatic, technical buyer (Head of Product + Platform Eng), legal-heavy procurement. Shortened items below.
2026-01-15: Intro call (AE Maya) — basic use case capture, demo scheduled
2026-02-03: Hosted API POC kickoff — integrated embedding pipeline, ingest 200k docs
2026-02-18: Technical deep-dive (SE Diego) — KV cache, batching, observed 35ms median gen on hosted for short chat flows
2026-02-26: Pricing review (AE + Finance) — Redwood provided committed capacity estimate + pricing deck (v2)
2026-02-28: Legal introducer call — exchanged initial MSA/DPA markups (Obelisk redlines sent)
2026-03-01: Onsite + workshop (remote) — SLA expectations clarified; Redwood asked for expected QPS and latency SLOs
Workload
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 23: `qst_0085::basic` · N=10000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The retrieved chunks are unrelated to the question about interaction tiering models, indicating a lexical mismatch. The gold chunk is relevant and non-empty, while the retrieved chunks are off-topic but non-empty. The hit flag is incorrectly set to true, indicating a pipeline issue.

### Question

What are the three request quality and cost tiers proposed in the lightweight interaction tiering model for user facing features?

### Gold document(s)

#### GOLD `dsid_2271ae6c393d409093b11b5a6d5b96ed`

```
Interaction tiering: personal idea scrapbook

Topline: brain-dump on a lightweight interaction-tiering model for user-facing features. Goal is a small, composable way to classify/route requests into quality/cost tiers with clear developer ergonomics and ops signals. This is rough — notes to self + things to show KD for feedback.

Why: teams keep asking for predictable unit costs and simpler fallbacks they can reason about. Full-blown QoS systems are heavy. We can give product teams a set of interaction tiers (micro, standard, deep) tied to routing policies, response shapes, and model variants so they can opt-in per route.

Problem statements:
- Product teams: need predictable per-interaction cost buckets without lifting infra complexity.
- Platform: wants transparent SLOs + simple rollout knobs to degrade gracefully under load.
- UX: different flows have different tolerance for latency/verbosity. No single "one-size" model fits all.

Design principles (rough):
- Primitive, composable: tiers are small metadata tags attached to a request.
- Declarative routing: config-driven mapping from tier -> model variant, cache behavior, batching policy.
- Observable: pronounced telemetry (p50/p95 latency by tier, cost per token by tier, quality regression alerts per tier).
- Safe defaults: "standard" tier matches current default behavior; micro/deep are opt-ins.

Tiers (first pass):
- micro: cheapest. short max tokens, high quantization profile, aggressive prefix cache, fallback to canned snippet when generation fails. Use for UI hints, autosuggest, quick facts.
- standard: baseline. balanced latency/cost. default model family and mid quantization. good for general chat, assistant replies.
- deep: quality-first. higher token budgets, less quantization, larger model family, enable structured-tool-calls and longer context. Use for long-form writing, code gen, final answers.

User stories:
- As a product engineer, I want to mark route /search/hint as "micro" so my feature stays within the free tier budget and I can cap per-session spend.
- As platform SRE, I want an emergency policy that turns existing "deep" requests to "standard" when GPU queues exceed 80% for 2m.
- As a grow
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_09eaf3ba24444871ad5ad1347c0cf22c`

```
Thunderberry CloudWorks LLC

2026-03-05: inbound self-serve signup via website; applied trial credits
2026-03-06: automated welcome email + docs link (sent by platform)
2026-03-08: intro call (AE + SE). Fireflies: ff_2026-03-08_4567; discussed chat/support pilot
2026-03-09: SE follow-up with sample prompt-set request and token estimate template
2026-03-12: customer submitted traffic profile and target latencies; asked for model cost/quality guidance
2026-03-13: internal pricing + recommended model draft prepared by AE
Lead profile: small SaaS (support-focused) building in-app assistant for customer-facing help. Early product market fit; looking to replace bulky keyword search with embeddings + LLM answers.
Primary constraints: fast time-to-value (self-serve), keep infra costs low, prefer hosted API rather than Dedicated. No strict residency requirement.
Use-case detail: chat-first UX with context windows up to ~3k tokens; embedding-based doc search for KB (~200k docs). Expect 20-40 concurrent active users initially.
Latency/throughput targets: p95 chat < 300ms preferred, p50 < 120ms; embeddings requests can be async/batched (throughput ~200 reqs/min during peak).
Cost sensitivity: 
…[truncated]
```

#### #2 `dsid_a883c3a9f23d4da98c657a76f9870740`

```
Driftglade Commerce

conversational_customer_support
product_recommendation_reranking
semantic_search_embeddings
hosted_api
Inbound signup via self-serve trial (Feb 24) — signed up with credit card, created two API keys.
Initial discovery call 2026-03-02 w/ Maya + Daniel. Attendees: CTO Lina Park, Head of Support Marco Ruiz.
Primary ask: reduce support response time and automate common returns questions. Secondary: improve product recommendations via reranking embeddings.
They repeatedly ask: 'Which open models give near-gpt quality for a fraction of the cost? Can we A/B cheaply?'
Security: SMB but they require SSO (Okta) and basic audit logs; SOC2 not required today but might be asked by key retail partners.
Quote from Lina: 'We want something that feels like a hosted API — no infra fuss. Open weights preferred so we can manage costs.'
Spin up 7-day eval comparing Mistral-7B-instruct, Llama-2-13B-quant, Qwen-7B-chat; send hosted API billing link and cost projection spreadsheet
uncertain latency targets
need clear quality vs cost baseline
internal budget approval by finance
How does Llama-2-13B (quantized) compare to Mistral-7B-instruct on instruction-following for returns FAQs?
Wh
…[truncated]
```

#### #3 `dsid_92bb1f050a6640dd9d5d7abbfc1a0760`

```
LumenFold Technologies

SMB SaaS product embedding a chat-like support agent and automated email drafting. Primary workload = chat/support + KB search fallback. Latency target: p95 in 400ms region (prefers sub-300ms for single-turn). Throughput modest (2–10 QPS typical). Cost sensitivity: high — wants guidance on 7B vs 13B tradeoffs, and when cheaper quantized variants make sense. Needs hosted API (no infra), streaming + function-calls, simple SSO (SAML) and audit logs. Would like automatic fallback to a cheaper model when budget/throughput spikes. Trial tokens used to validate prompt templates and reranking.
- Lead came from blog CTA (Model Selection Guide). signed up self-serve; early-stage POC.
- Key ask: 'give us a short, practical rule-of-thumb: when should we use Mistral-7B vs Llama-13B vs Qwen-14R for support chat?'
- Cost sensitivity: "high" — CFO wants predictable $/month, not surprises. Prefer price-per-1000-tokens examples.
- SE comments: recommend start on Mistral-7B-instruct (good quality/cost) for intent/classification + chat, then A/B to Llama-13B for longest-context/nuanced responses. Consider Qwen variants if multilanguage (they have a small EU+CN userbase).
- Cust
…[truncated]
```

#### #4 `dsid_14f8395107244d9fbe00572db0e5aa72`

```
GroveFuse Chatworks

Inbound lead via self-serve signup — sandbox account created 2026-02-25.

Initial contact: Jordan Kim (AE) intro call 2026-03-03 — short discovery (FF id FF-20260303-84A-GF). CTO (Maya Lin) + Lead ML Eng (Rico Santos) on call.

Key pain: need a small-footprint chat assistant for SMB customers (in-app help/search) that stays cost-effective at scale. Also running hybrid semantic search for FAQ/KB (embeddings).

Model questions / asks (explicit):
- "Can you compare Llama-2 13B, Mistral-7B, Qwen-7B in hosted offering?" — wants realistic quality vs token-cost tradeoffs.
- Interested in quantized variants: 4-bit options, impact on latency and hallucination risk.
- Multi-model routing: prefer cheaper model for straightforward queries, higher-quality for fallbacks. How to set up routing/fallback in Hosted API?
- Latency target: 150-300ms tail for single-turn chat (typical message length ~30-80 tokens). Throughput: bursts to ~30 QPS during peak.
- Embeddings: batch up to 10k docs/day, need per-embedding cost estimate and suggestions (model choice vs recall).

Security/compliance: SOC2 required, SSO/SAML integration with Okta (engineering already using Okta), audit logs 
…[truncated]
```

#### #5 `dsid_080da3e2a82e41158a49f62d4739dc46`

```
NimbleClasp AIWorks

NimbleClasp builds an in-app support assistant + knowledge search. Primary workloads: real-time chat snippets (low-latency), nightly document embeddings for search, and reranking for suggestion feed. Current hosted API usage from quickstart shows heavy token counts due to long system prompts and full conversation history being sent. Targets: p95 chat latency < 250ms, support flows <= 200ms median; cost sensitivity high — target 30%+ reduction in monthly token spend. Wants guidance on batching for high-throughput embedding pipelines, prefix/KV caching for chat, and automated prompt compression/token audits for templated messages.
Inbound demo signup via quickstart (converted from free credits) — high product engagement: 4 teams active.
Primary ask on first call: how to cut monthly token spend — mentions high cost from long system prompts and chat history. Wants concrete levers: batching, caching, prompt compression.
AE notes: they're comfortable with hosted API (public cloud) but cost sensitivity is high — CFO flagged potential cancel if unit economics don't improve.
Quote from CTO (Mar 02): 'Our retention engine will blow the budget if we keep calling the big m
…[truncated]
```

#### #6 `dsid_d029cb3c0961442282cdbd91013c2857`

```
SmallCurrent Solutions

SMB inbound; evaluating hosted API; model selection & cost tradeoffs (Llama/Mistral/Qwen); high cost sensitivity; SE deep-dive scheduled.
Lead type: inbound SMB (self-serve). Primary contact: CTO (Maya Rao) -- hands-on with evaluation. Wants Hosted API to avoid infra. Key ask: which model family to pick for customer-facing chat + product recommendations given tight monthly budget.

Customer details and requirements (copied from call):
- Traffic: seasonal spikes; baseline ~50 QPS across multiple endpoints, peak ~400 QPS for flash sales (expects to use autoscaling on hosted tier).
- Latency goal: p95 < 350ms for chat simple Qs; can accept up to 800ms for long-form retrieval-augmented answers.
- Cost sensitivity: high. Wants to understand quality delta between Mistral/Mistral-instruct variants, Llama 2 13B, and Qwen 7B / 14B; wants per-token cost projections for 100M tokens/month.
- Model preferences: open to open-weight models, no need for proprietary closed models. Interested in cheaper quantized variants if quality holds.
- Routing/fallback: wants simple cost-based fallback (cheap variant when latency not critical), and single-API surface if possible.
- Secu
…[truncated]
```

#### #7 `dsid_5dbca2a3ac844546b9a4c6aad5af7730`

```
HarborPoint LLMWorks

Inbound trial signup via marketing landing page on 2026-03-04; used free credits to test text-gen endpoint.
Discovery call 2026-03-09 w/ AE Jordan + SE Priya (30m). high-level ask: small engineering team, embed chat + code assistant into support portal.
Customer quotes: 'We need reasonable quality for intent + summarization, but cost is the gating factor.'
Model selection concerns: wants recommendations between Llama 2 (13B/70B), Mistral Large variants, and Qwen-medium — tradeoffs for latency & token cost discussed.
Latency / throughput targets: target p95 latency <= 200ms for short chat turns (<= 256 tokens), concurrent users ~50, burst to 200.
Cost sensitivity: POC budget ~ $1k/month; willing to scale if clear ROI. Ask: which model variants give best perf/$ for chat + completions.
Tech notes from SE: suggest starting with quantized Llama-2-13B or Mistral-7B-v0 as low-cost baseline; try higher-quality Llama-2-70B or Mistral-1.2 for A/B if quality gap large.
Want quick A/B harness: run ~200 prompt pairs (support FAQs + code snippets) across 3 model configs; measure latency, #tokens, and subjective quality.
Security: SOC2 compliance important for procurement; S
…[truncated]
```

#### #8 `dsid_8fe621e97b814937b9b07fb58e38d3d9`

```
Ironwood Atelier AI

SMB ecommerce tooling company — building a merchant-facing chat assistant and internal search over product docs
Primary ask: guidance on model selection (Llama vs Mistral vs Qwen variants) balancing quality vs cost. Quote: 'We need near-LLM-2 quality for product answers but can't triple our inference bill',
Prefer hosted API for speed of iteration, self-serve. Not ready for Dedicated/Private. Public cloud only.
Token budget concern: target ~10-15k tokens/day for pilot; latency objective: <300ms for short chat replies, embeddings batch overnight, realtime for small queries
Model preferences discussed: Llama 2 13B for higher quality, Mistral 7B Instruct for cost-sensitive chat, Qwen 14B for multilingual product content — ask for sample cost per 1k tokens and perf profile
Security: needs SOC2 evidence + ability to use their IdP (SAML/OKTA). Interested in KMS for key management but ok to start without for pilot
Requested deliverables: 1) short Llama vs Mistral vs Qwen comparison sheet with cost estimates, 2) hosted API quickstart example repo, 3) sample embedding memory architecture for merchant search
2026-02-12 - inbound signup via quickstart; activated free cred
…[truncated]
```

#### #9 `dsid_41f7a51a3feb41a88a3f3c314f070773`

```
StitchForge AI

SMB ecommerce plugin embedding conversational shop assistant + product recommendation embeddings. Short-turn chat with emphasis on factual accuracy and low per-token cost.
Inbound trial signup via landing page (Feb 28). Small ecommerce plugin vendor building conversational shop assistant + quick product recommendations. Self-serve tests running against hosted API; devs making sample calls. Main thread: lightweight, pragmatic. Primary questions on model selection: Llama 2 7/13B vs Mistral 7B vs Qwen 6B variants — tradeoffs between output quality on short conversational turns and per-token cost. Quote from call: "We want something as cheap as possible that doesn't hallucinate product attributes — accuracy > fancy language." Typical request shape: very short user prompts (avg 20–40 tokens) and 80–160 token responses for support flows. They also care about embeddings for similarity-based recommendations (dense vectors, 1536-4096 dims). Testing results so far: Mistral-7B-v1 feels snappier, Llama-13B gives slightly better factual recall but slower / more expensive; Qwen 6B cheaper but mixed on product attribute recall. Dev notes: pref cold-start latency under 350ms p50, s
…[truncated]
```

#### #10 `dsid_fccd01322b1047fe8b987b3824adcd1e`

```
Cobalt Clew Analytics

Inbound SMB e-comm discovery: model selection (Llama/Mistral/Qwen) tradeoffs, cost-sensitive POC, routing for FAQ vs complex, SOC2 + SSO. Next: send cost matrix + offer 2-week hosted POC credits.
Lead source: inbound self-serve signup, converted to discovery after initial auto-email. Short background: mid-market e-comm with ~120 employees. Building a customer support+search experience for product pages and refunds. Primary ask: how to pick a model for hosted API that balances token cost and answer quality for both quick FAQ-style queries and longer context-aware responses.

Key snippets from calls / internal quotes:
- 'We want chat answers in ~200-400ms tail p95 for simple queries, and can tolerate ~1s for complex prompt+context.'
- 'Cost matters — we're a lean SMB, want to keep monthly inference spend < $3k during POC.'
- 'If we can route cheap QnA to a lighter model and escalate to a higher-quality model for complex sessions, that would be ideal.'

Model selection conversation (very specific):
- Evaluating Mistral-7B variants (good quality/cost balance), Llama 2/3 family (better fine-tune ecosystem for us), and Qwen-lite options (promising latency). Asked a
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 24: `qst_0091::metadata` · N=20000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not match the expected document ID, indicating a lexical mismatch. The retrieved chunks are unrelated to the question about key rotation intervals, focusing instead on account management and renewal strategies. The gold chunk is also off-topic, discussing trading operations rather than key rotation. This suggests a potential issue with the retrieval process or document labeling.

### Question

Which enterprise capital-markets account in North America was last updated in mid March 2026 and has a forecast close month of May 2026?

### Gold document(s)

#### GOLD `dsid_c669e9bde8764a1a9636674fce02ff52`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_0f991287334d40fbb4d597b305447fd2`

```
Subscription Flagship Tracker - Q4 2026 (working)

Working tracker for high-touch subscription accounts for Q4 2026. Focus: prioritize accounts with >50% ARR exposure and mid/high risk scores. Action items: 1) finalize price decks for Dedicated/Private options for Atlas Health and CoreBank; 2) run Optimize cost analyses for NovaSearch and Sable Analytics; 3) schedule executive QBRs where renewal probability >70% to capture early commitments; 4) low-ARR churn candidates (Zephyr Media) to be moved into playbook 'low-touch save' and FYI to scaled success team.
Account,ARR,Contract End,Renewal Window,Renewal Probability (%),CS Owner,Last Contacted,Next Step,Action Owner,Risk Score (1-5),Notes
Sable Analytics,$240,000,2026-12-15,90 days,70,Maya Thompson,2026-09-28,Schedule executive QBR + pricing review,Maya Thompson,3,Customer evaluating Dedicated vs Hosted; needs cost/perf comparison and canary SLA
Horizon Retail,$85,000,2027-01-10,60 days,45,Liam O'Neil,2026-10-02,Send usage delta + success stories; plan kickoff,Liam O'Neil,4,Usage dip in July; primary champion changed roles
CoreBank Systems,$1,200,000,2027-02-01,120 days,85,Priya Desai,2026-10-05,Propose 12-month reserved capacity d
…[truncated]
```

#### #2 `dsid_4ee96635eb8e4dda8b644d0403b6b229`

```
Customer Lifecycle Convoy — Compact Pipeline Tracker (May 2026)

Compact tracker for upcoming contract milestones, ARR exposures, renewal probabilities and immediate next actions. Purpose: lightweight QBR input + weekly ops standup reference (abbreviated columns for sprint-driven follow ups).
Contract ID
Account
ARR (USD)
Contract End
GTM Owner
Renewal Probability
Primary Risk
Next Step / Owner
QBR Notes
CL-2026-001, CartaLabs Inc, $120,000, 2026-07-15, Rafael Gomez, 75%, product-fit concerns -> exec demo scheduled, Demo + pricing review / Rafael, Needs expanded usage report before QBR; compute spike noted
CL-2026-002, Neptune Health, $420,000, 2026-08-01, Priya Shah, 55%, budget cycle (pending approval), Finance kickoff + champion alignment / Priya, CFO intro on 2026-06-10 (prep: usage delta slides)
CL-2026-003, BrightBuild, $48,000, 2026-06-30, Jordan Lee, 90%, low risk (expansion opp), Auto-renew likely; send renewal contract + minor discount / Jordan, Short-term upsell: additional embeddings POC
CL-2026-004, Atlas Retail, $300,000, 2026-09-12, Elena Park, 40%, performance SLO vs cost, Propose Dedicated pool + pilot quantization profile / Elena, SRE call scheduled 2026-05-25; ri
…[truncated]
```

#### #3 `dsid_2016c4fb92394c21af9f481e0fb4b3ee`

```
Client Contract Momentum Sheet — Q4 2026

Purpose: lightweight, action-first spreadsheet to track contract expiries, expected ARR impact, and the immediate playbook steps per account. This is intended as an ops-first sheet used during weekly renewal huddles and the customer QBR prep flow.

Columns (tab-delimited):
Account	Account Owner	Contract Start	Contract End	ARR (USD)	Renewal Probability (%)	Expected ARR (ARR * Prob)	Next 3 Actions	Last Contact	Risk Flags	Playbook Variant	Notes

Rows:
Acme Robotics	Marcus Lin	2023-11-01	2026-11-30	420,000	65	273,000	1) In-person exec QBR by 2026-10-18; 2) Technical deep-dive on latency SLOs; 3) Commercial propose 12% discount for 24m commit	2026-10-27	delivery-issues, exec-change	enterprise-retention	Client requested real-world latency numbers; procurement lead changing in Nov.

BrightMart (Commerce)	Evelyn Ortega	2024-04-15	2026-12-15	180,000	40	72,000	1) Confirm usage baseline & optimize batching; 2) Offer Optimize credits; 3) Book renewal call 2026-11-10	2026-10-22	mid-size-price-sensitivity	midmarket-expand	Has prototype using dedicated; concerned about cost per session spikes.

DatumAI Labs	Priya Khanna	2022-12-01	2026-12-31	1,200,000	85	
…[truncated]
```

#### #4 `dsid_5fc60be2347646f283ce3d63a2925deb`

```
Churn risk heatlist + renewal actions (Q1 tracker)

Working tracker intended for weekly CS standups. Combines quantitative signals (ARR, usage trend, contract date) with qualitative notes (risk factor, next step) so AMs/CSMs can prioritize churn prevention and targeted plays. Draft stage: seeking alignment on scoring weights and escalation thresholds.
How to use this sheet: 1) CS owner updates Last Customer Touch and Next Step after each cadence. 2) 'Renewal Probability' should be revisited after legal/PO activity. 3) Use filter: Risk Score > 70 to generate weekly focus list. 4) Attach customer-specific evidence to linked_artifacts (Confluence pages, Jira tickets). 5) For accounts with 'Billing / Legal Flag' mark owner as urgent and notify Sales Ops.
Renewal Probability is a blended heuristic: baseline = historical renewal rate by cohort (0.7 for enterprise, 0.45 for midmarket, 0.25 for SMB) adjusted +/- for recent NPS touches, usage trend (3-6 month delta), open legal/billing flags (-0.3 if present), and presence of active upsell discussions (+0.15). Risk Score is 0-100 where higher means higher risk; generated by weighting (Contract proximity 30%, Usage delta 25%, Billing/Legal 2
…[truncated]
```

#### #5 `dsid_6b3bf537e0b54d76948f36c106333492`

```
Renewal Portfolio Snapshot — Brief

Total ARR: $1,910,000 | Total Weighted ARR: $1,333,950 | Accounts Tracked: 12 | High-risk accounts (Probability < 0.6): 3 | Immediate escalations flagged: Atlas Retail, CopperOps, Verta AI
Account,Contract End,ARR,Probability,Weighted ARR,CSM,Next Step,Next Step Date,Last Touch,Status,Notes,Escalation
Nimbus Health,2028-02-14,$120000,0.85,$102000,Katherine Nguyen,Schedule pricing + ROI QBR,2028-01-12,2027-12-20,On Track,Strong product adoption,No
Atlas Retail,2028-01-31,$450000,0.72,$324000,Ravi Patel,Legal review of renewal T&Cs,2028-01-05,2027-12-22,At Risk,Requests multi-year discount,Yes
Helix Analytics,2028-03-08,$200000,0.95,$190000,Maya Fernandez,Technical healthcheck + roadmap sync,2028-02-20,2027-12-28,On Track,Expanding to 3 more teams,No
CopperOps,2028-02-02,$85,000,0.40,$34000,Ethan Zhao,Executive alignment call,2028-01-10,2027-12-10,High Risk,Procurement concerns,Yes
Meridian Auto,2028-04-15,$310000,0.65,$201500,Katherine Nguyen,Proposal for committed capacity,2028-02-28,2028-01-02,Watch,Considering dedicated vs hosted,No
Orion Fintech,2028-01-20,$95,000,0.55,$52250,Ravi Patel,Security & compliance sign-off,2028-01-08,2027-12-18,At R
…[truncated]
```

#### #6 `dsid_33fe9208812c4384a9ae90c9d84dcf13`

```
Northern Arc Fintech

Hold (company-wide hiring freeze). AE to re-engage Jan 2026 if budget/hiring reopens.
2025-03-15: Initial inbound via docs team; AE assigned (Maya)
2025-04-02: Discovery call w/ ML infra + payments PMs. Identified reranking use-case for fraud scoring.
2025-06-10: NDA signed; security questionnaire sent. Security requested KMS + residency info.
2025-08-12: PoC kickoff (subset of transactions, latency target 50ms p95). SE Diego leading integration.
2025-09-25: PoC results: model latency 40-55ms p95 on dedicated nodes; accuracy lift ~12% vs baseline.
2025-10-15: Pricing proposal v3 shared. Finance wanted 12-month committed pricing; legal flagged data residency.
2025-10-29: Final call w/ Head of Payments — positive, but asked for a detailed security addendum.
2025-11-01: Company announced hiring freeze and broad budget constraints (email from CFO). Project paused.
2025-11-08: AE updated CRM: account marked stalled, hold for at least one quarter.
Summary: strong technical fit (dedicated/dedicated+VPC) for reranking; PoC validated latency & quality.
Key quote (Head of Payments): 'Love the numbers — main blocker is headcount and budget right now.'
Security: asked for
…[truncated]
```

#### #7 `dsid_cafcb9b9916a420b9c743beb093794b7`

```
CS Contract Coverage Inventory — Q2 2026

Working tracker to inventory expiring contracts, ARR at risk, playbook steps per cohort, and an action log for QBR prep. Meant to feed into the QBR slide deck and renewals sprint.
Pipeline Summary
Columns: Account | Customer Tier | Product Footprint | ARR (USD) | Contract End | Auto-Renew | Renewal Probability | Owner | Next Step | Risk Notes | Last Touch

Acme Labs | Strategic | Hosted API + Optimize | 420,000 | 2026-05-14 | No | 85% | Priya Nair | Schedule exec QBR + send usage/ROI pack | Exec sponsor engaged, finance reviewing committed spend | 2026-03-10
BrightLeaf Health | Mid-Market | Dedicated | 120,000 | 2026-06-02 | No | 60% | Evan Rogers | Share Tiered Pricing + propose 12mo commit | Support ticket SUP-2341 open (latency regressions) | 2026-03-09
Nimbus Retail | Growth | Hosted API (embeddings) | 48,000 | 2026-04-22 | Yes | 92% | Marta Lopez | Confirm auto-renewal terms, no action unless scope change | Renewal auto-renews; low risk | 2026-03-11
Orbit Analytics | Strategic | Private (VPC) | 1,200,000 | 2026-07-30 | No | 40% | Noah Kim | Schedule technical migration review + commercial proposal | Security SOW outstanding; procuremen
…[truncated]
```

#### #8 `dsid_85bc31ebe5de4cf7bd0fc36f5d3e5ad8`

```
Northstar Provenance AI

Re-engage VP Product (exec sponsor) for signoff; schedule CFO budget sync; propose phased roll-in to reduce initial ARR.
2025-11-02 - Created account (inbound via webinar). Named AE: Jordan Park.
2025-12-10 - Intro call (Jordan/Maria). Customer: building metadata provenance and document audit trails. Primary ask: low-latency doc search + traceability.
2026-01-05 - Discovery call, SE Mariela joined. Agreed POC scope: 2-week POC (search+reranking + provenance tags) against 10M doc index. Success metrics: median latency < 100ms for 128 tokens, rerank NDCG lift >= 12%, cost target <$0.006/token equivalent.
2026-01-19 - POC kickoff. Fireflies id ff-2026-01-19-northstar-poc-demo. Notes: will test hosted first, then dedicated for throughput comparison. VP Product (exec sponsor) committed to review POC results.
2026-02-03 - POC mid-point sync. Observed caching benefits on repeated prefixes, KV cache reduced tokens by ~18% for common queries.
2026-02-20 - POC completed. Results: median latency 65ms (128 tokens) on dedicated config, throughput ~120 rps with burst. Rerank NDCG +14%. Cost model estimates aligned after quantization suggestions from Redwood Optimize.
202
…[truncated]
```

#### #9 `dsid_e1baae564a6346abade621d30c819226`

```
Cedar Harbor AI Systems

Account snapshot: Cedar Harbor is a mid-market maritime logistics firm exploring LLMs to power an internal support assistant for operations + a telemetry summarization pipeline for captains. Team liked Redwood's dedicated latency and cost controls but the initiative is paused due to a company-wide hiring and spend freeze (announced 2026-02 by CFO).

Primary contacts:
- VP Product: Aisha Reynolds (evaluation lead)
- Head of Infrastructure: Tom Kwan (security gating)
- Procurement/CFO liaison: Ben Morales (holds budget)

Recent timeline (bullets):
- 2025-10-01: Intro call (Jordan P.) — high-level use cases, roadmap alignment.
- 2025-11-12: Technical kickoff with SE (Marisol) — agreed on POC scope: 2-week dedicated cluster trial, SSO + KMS demo. Action: security questionnaire handed off.
- 2025-11-30: POC deployed (dedicated small pool) — demo data loaded (anonymized). Initial perf: median gen latency ~85ms for 512-token prompts; batching + prefix cache reduced cost ~28% vs baseline.
- 2025-12-08: Security meeting — Tom requested SOC2 + penetration test summary; Redwood provided security FAQ & KMS integration doc (drive link). Ticket SEC-2218 opened.
- 2026-01
…[truncated]
```

#### #10 `dsid_0df6e984d47c465ca31f0c9e2beb6142`

```
Crestfield Payments Inc.

- Account profile: core payments processor for mid-size/enterprise merchants. Heavy compliance/regulatory needs.
- Use-case prioritized by product: conversational support bot (tiered routing), doc summarization for compliance reviews, model-based reranking for fraud signals.
- Jan 15: initial inbound via solutions form — assigned Maya. quick discovery call scheduled.
- Jan 23: discovery call (30m) w/ PM, SecOps. Key ask: SSO + audit logs, residency in us-east, ability to pin model versions.
- Jan 30: sent pricing + architecture deck (drive link). SecOps requested SOC2 + whitepaper.
- Feb 10: demo w/ Diego (ff_20250210_crestfield_demo). Showed hosted API + dedicated sizing. Questions on caching and KV persistence.
- Feb 14: security review — asked for KMS/HSM integration details; protracted review with legal.
- Feb 20: internal stakeholder shift — procurement put on hold pending budget reforecast (Q2).
- Feb 24: product emailed — they are running a 2-week spike using OpenAI direct API for rapid prototyping (ease-of-use cited).
- Feb 28: final sync — customer prefers OpenAI/Anthropic due to brand familiarity and lower initial setup friction. No champion to p
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 25: `qst_0096::metadata` · N=75000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`other`
- **LLM note:** The retrieved document IDs do not include the expected document ID, making the Hit@10 label incorrect. The retrieved chunks are non-empty and on-topic for technical issues related to model deployment and tenant management, but they do not address the specific question about SaaS billing and user deactivation. The failure mode is categorized as 'other' due to the lack of direct relevance to the question, rather than a near miss or lexical mismatch.

### Question

In the customer-support incident about tenant pinning breaking during deferred prewarm and causing mixed model replies in a dedicated prod us-east environment, what is the SLA due date?

### Gold document(s)

#### GOLD `dsid_ca09c9594d0f4293b971c96fa9ed647c`

```
Tenant stickiness erosion during deferred prewarm leads to cross-variant responses

Issue summary:
BrightForms reported intermittent mixed-model responses for a tenant shortly after a staged model promotion where the system deferred prewarm jobs to prioritize candidate canary capacity. Impact: some requests returned outputs from the legacy model variant instead of the promoted v1 despite the tenant being explicitly pinned to v1.

Impact:
- Customer-facing inference returned inconsistent outputs (~4% of requests across a 20-minute window).
- Increased error budgets for the customer's dedicated pool due to retries and fallbacks.
- Customer paused a subset of traffic and escalated to enterprise support.

Environment:
- Dedicated pool in prod-us-east served via edge-proxy cluster ep-12.
- Tenant: brightforms-tenant-03 pinned to redwood/caesar-7b-v1.
- Rolling promote executed 2026-03-10T02:15Z with deferred prewarm queue enabled to avoid capacity spike.

Steps to reproduce (from customer repro):
1) Pin tenant to a newly promoted model variant (v1) in dedicated.
2) Trigger staged rollout with deferred prewarm enabled (prewarm tasks scheduled after canary threshold).
3) Send 10k short-chat requests (~15 token prompt) across 10 client connections.
4) Observe ~300 responses that match the legacy model signature (different tokenization/stop sequences).

Observed behavior:
- A subset of requests were routed to the legacy variant within a 12–25s window after promotion.
- Orchestrator logs show tenant affinity assigned to v1, but edge-proxy trace shows a redirect to a node still serving the legacy container.
- KV cache hit metrics for v1 are initially low; legacy variant reports KV hits from cold-requests, implying session routing crossed variants.

Expected behavior:
- Tenant pin should remain honored for all in-flight and new requests after promote commit; deferred prewarm should not allow any routing to legacy once pin committed.

Preliminary investigation notes:
- Hypothesis A: Deferred prewarm leaves a short window where edge-proxy fallbacks to warm nodes still advertising legacy variant; edge routing uses last-known healthy node when prewarm queue incomplete.
- Hypoth
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_9ef76c1d3d354ade932995b6e2ad581a`

```
Enforced model pin suppressed by fallback-throttle preemption during canary window, causing mixed-model responses

Issue summary: Customer BrightAssist reported intermittent mixed-model outputs despite having an explicit tenant model pin configured. Impact: a subset (~4%) of requests during the canary window returned responses generated by a compat/legacy variant instead of the pinned model, causing degraded answer quality and downstream QA alerts. Environment: Dedicated tenant on prod(us-east), pinned via tenant config to redwood-7b-v1.
1) Tenant has explicit pin: tenant_config.pin_model = 'redwood-7b-v1'
2) Trigger canary rollout for redwood-7b-v1 -> redwood-7b-v2 in same region with 10% weight
3) Simulate load spike with concurrent prefix-heavy streams (50 RPS sustained for 10m)
4) Observe router logs and serving runtime traces for requests that should honor tenant pin
edge-proxy trace: req=1a7c3f7e tenant=brightassist route=chat model_hint=redwood-7b-v1 fallback_reason=throttle_preemptor selected_model=redwood-1.5b-v2
orchestrator log snippet: 2026-03-11T15:42:08Z WARN fallback-controller: preemptive-throttle triggered for slice 10; suppressed explicit_pin=true for cohort 'tena
…[truncated]
```

#### #2 `dsid_d84bdbf7547f4feab122ed2f99e23782`

```
Hosted API: elevated 5xx in us-east; request auto-fallback behavior unclear for pinned customers

Description
- Customer reports intermittent 502/503 on chat completions in us-east starting ~10:10 PT.
- Customer has contract language around model pinning; they are pinned to `rw-llama3-70b` build 2025.01.27.
- Customer asks: "Are you failing over to a different model behind the scenes?"

Impact
- ~3% requests failing for this account during the event window.
- Customer escalated via CSM; asks for written clarification.

Investigation notes
- SRE indicates us-east cluster at ~97% util; scheduler rejects spiking.
- Router currently does NOT automatically switch pinned builds to a different variant; only manual region failover was used.

Comments (abridged)
Vanessa Ortiz (Support): customer wants to know if any variant fallback occurred; they require explicit notice if model changes
Connor O'Brien (Eng): confirmed: no variant fallback for pinned builds. we can do region failover if another us region is allowed, but LexiLoop is US-only so us-east->us-west is OK
Priya Natarajan (SRE): toggled manual degrade flag for primary route; traffic shifted to us-west for 22 mins
Vanessa Ortiz (Sup
…[truncated]
```

#### #3 `dsid_86783f1b3d154ac7b57c6d3d71bb5efc`

```
Unexpected fallback to degraded variant during staged graceful rollout despite model pin and prewarm success

Issue summary: Customer reported that during a scheduled staged rollout (graceful promote) of h-gpt-7b-quantized-v2 the tenant traffic unexpectedly diverted to the degraded fallback variant for ~6 minutes despite the tenant being explicitly pinned to the new version and prewarm checks returning healthy.

Impact: Horizon Analytics (dedicated) observed elevated error rates and lower-quality completions for a subset of sessions affecting two production cohorts. Business impact: several active inference pipelines returned degraded outputs, increasing latency and manual retries. Estimated affected requests: ~4.2k during window.

Environment: production (us-west-2), dedicated capacity pool ID: ded-pool-05, orchestrator release tag: v2026.03.10-canary, edge-proxy version: 1.18.2.

Observed behaviour: explicit model pin for tenant T-98765 was present in control plane; the serving runtime reported KV-cache warmed; prewarm probes returned 200/OK. Despite that, routing logs show a switch to fallback variant serving-degraded-1 for requests that previously had pinned affinity. Edge retr
…[truncated]
```

#### #4 `dsid_4c3b0b28fdb04170860fa7130f328892`

```
Tenant lease jitter causes pinned model demotion during canary wave

Issue summary: During a staged canary wave for gptx-alpha-3.1 we observed a subset of tenant sessions that were explicitly pinned to 3.1 being demoted to a degraded variant (3.0-quant) without an explicit rollback or pin change. Impact: Affected tenant (AtlasSearch) saw inconsistent outputs and higher latency on ~2% of requests; downstream QA flagged semantic drift causing failed assertions in their processing pipeline. Environment: prod-us-east, Dedicated pool: dp-us-east-2 (4x A100), orchestrator v1.8.3, edge-proxy v2.2.1. Observed window: 2026-03-08 18:12 - 18:46 UTC. Expected behavior: Explicitly pinned sessions should continue routing to the pinned model until pin expiry or explicit unpin. Workaround applied: Triggered manual pin-refresh job which reasserted lease tokens for affected tenant and restored routing for most sessions.
Partial degraded routing for pinned sessions affecting AtlasSearch (dedicated). Approximately 2% of their traffic routed to quantized fallback, causing semantic divergence and a 60-120ms median latency increase for those requests.
AtlasSearch reported that their nightly QA jobs flagg
…[truncated]
```

#### #5 `dsid_5c1c408fa554409fac6125db3ce9b387`

```
Tenant pin corruption during deferred prewarm trigger causes silent transparent fallback

Issue summary: After a deferred prewarm event triggered by autoscaler warm-up, a subset of tenant sessions observed a corrupted pin token that led requests to be routed to a fallback (degraded) variant without surface errors. Impact: Customer AuroraDocs reported elevated inference delta and a drop in quality for ~2% of requests starting 2026-03-05 02:12 PDT. No 5xxs were returned; clients saw silent model output divergence and occasional slower tails. Expected: pin handshake during prewarm should preserve tenant-version affinity and not route to fallback unless health checks fail. Observed: when deferred prewarm triggered under bursty queue conditions, the orchestrator prewarm routine updated prewarm state and wrote a pin with an invalid cohort checksum; edge-proxy accepted the pin but orchestrator epoch mismatch caused downstream router to prefer fallback variant.
```

#### #6 `dsid_2369a3a36fb046abb1d8d9355dce86ed`

```
Priority escalation during regional failover overrides explicit tenant model pin causing degraded routing and unexpected billing

Pulse Health reports that during a short region-level failover window an automated priority escalation (capacity-protection) bumped fallback routes and effectively superseded an explicit tenant pin to redwood/v1-chat-6B@2026-02-19. Requests were routed to open/llama-13b-quant and produced truncated answers and missing clinic identifiers. Customer saw a 37% increase in billed tokens for the window and open tickets from end-users. Pins should be authoritative; fallback routing should not revoke an explicit tenant pin.
1) Tenant pins path /v1/generate to redwood/v1-chat-6B@2026-02-19 via tenant config and confirms active sessions
2) Trigger regional control-plane health degrade for us-east (internal test flag) to simulate failover conditions
3) Allow priority-escalation policy (configured for preemptive capacity protection) to run which increases fallback variant weight
4) Observe routing table and request traces: pinned tenant traffic is routed to fallback variant for ~22 minutes
5) Compare generation outputs and billing token counts during the window
Init
…[truncated]
```

#### #7 `dsid_de78c84196854989820c74f81540de1d`

```
Tenant edge header rewrite causes pin to be claimed during canary prewarm, producing mixed model responses

Issue summary: During a staged canary prewarm for model redwood/llama-3b-v1, several tenants observed mixed responses where requests that should have stayed on the pinned variant returned outputs from the canary variant. Impact: Customer reported regression in inference outputs (semantic differences) and elevated token consumption for pinned sessions. This affects a dedicated customer in prod (Acme Health) and is causing customer-facing errors for health-reporting microservices that rely on deterministic outputs. Environment: production (us-east-1) dedicated capacity pool for Acme Health. Canary rollout initiated 2026-03-12 02:00 UTC; prewarm traffic started 02:05 UTC. Steps to reproduce: 1) Customer pins route to redwood/llama-3b-v1 via dashboard or route header. 2) Initiate staged canary promotion to redwood/llama-3b-quantized-v1 with prewarm mirror enabled. 3) Simulate tenant traffic with X-Tenant-ID and X-Prefer-Model headers set; note that customer has a CDN that rewrites headers (X-Tenant-ID -> X-Tenant). 4) Observe that sessions previously pinned to v1 begin receiving 
…[truncated]
```

#### #8 `dsid_175de838f80642e194b706d3418ff35d`

```
Intermittent APAC-egress routing observed for EU-pinned dedicated tenant causing p95 latency jitter

Issue summary:
Customer (DataMill Analytics, dedicated tenant) reports intermittent high p95 latency for inference calls from EU-based traffic. Tenant is pinned to eu-west pool but we are seeing a subset of requests routed via ap-southeast-1 which increases p95 from ~180ms to ~850ms.

Impact:
- Production traffic for DataMill analytics pipelines experiencing periodic p95 spikes (~0.5%–2% of requests during rolling windows).
- Errors are not increased; primary impact is latency and customer SLA concern.

Environment:
- Tenant: datamill-prod (dedicated gpu pool)
- Region: eu-west primary pin configured via tenant routing policy (strict_pin: false by default)
- Time window: first observed 2026-03-09 18:20 UTC, reproducible intermittently through 2026-03-10

Steps to reproduce:
1. Send batched generation requests for model redwood-1-large pinned to tenant datamill-prod from EU IPs.
2. Observe latency distribution in Console -> Per-route latency (p50/p95/p99).
3. Correlate request IDs that show p95 > 500ms with router decision logs.

Observed logs / snippets:
- Example request IDs (obser
…[truncated]
```

#### #9 `dsid_f30e41ac9021447b94eaed3b00f037ec`

```
Tenant routed to secondary variant despite explicit model pin during orchestrator retry surge

Issue summary: One enterprise customer observed tenant traffic being routed to a secondary (fallback) variant even though their project had an explicit model version pin. Impact: customer-facing production traffic experienced degraded model behavior and increased cost due to falling back to a larger, higher-cost variant. This started during a rolling canary of a separate release when orchestrator retry activity spiked.
1) Create a tenant-level model pin to redwood/rlhf-3b-v2 with strict affinity; 2) Initiate a rolling canary that toggles health checks for a different model in the same region to induce orchestrator retries; 3) Observe routing decisions in the control plane and edge traces for a burst window; 4) Repeat with increased orchestrator retry rate and note whether pinned affinity holds.
During a control-plane retry surge the tenant's session affinity was dropped and requests were routed to the secondary variant for ~8 minutes. Edge traces show the pin still present in the tenant metadata but the orchestrator returned a fallback routing decision. Requests received mixed variant out
…[truncated]
```

#### #10 `dsid_942cd438bca54d999095774e62b2cbfd`

```
Edge header stripping evicts tenant model pin during dedicated preemptive rebalancing causing transparent fallback and billing spike

Issue summary:
Customer observed intermittent routing to a compatibility variant (compat/llama-compat-1.0) for specific tenant sessions that had an explicit model pin to redwood/falcon-v2-7b-llm-v2.1.3. The divergence began during a scheduled dedicated pool preemptive rebalance tied to an autoscaler prewarm and regional cutover.

Impact:
- Several tenant sessions returned responses from the compat variant for ~15-30 minutes intermittently across us-east and eu-west.
- Customer reported increased token bill for compatibility variant (estimated +32% token cost) and user-facing quality regressions for high-value workflows.
- Streaming connections remained connected; issue primarily observed on requests that included function-calling metadata and custom headers.

Environment:
- Tier: dedicated
- Dedicated pool: atlas-dedicated-gpupool-3 (us-east primary, eu-west standby)
- Model pinned by tenant via API: redwood/falcon-v2-7b-llm-v2.1.3
- Time window: 2026-03-10 02:12 - 2026-03-10 02:47 UTC

Steps to reproduce (as provided by customer):
1) Create tenant s
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 26: `qst_0144::basic` · N=15000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks discuss technical performance issues but do not address the specific question about median latency improvement from continuous batching. The failure mode is lexical mismatch due to the absence of relevant content in the retrieved documents. The chunk quality is moderate, as the content is on-topic for performance but not directly relevant to the question.

### Question

In the recent Friday all-hands notes, what was the reported median latency improvement attributed to continuous batching?

### Gold document(s)

#### GOLD `dsid_a227a7f316c4452eab4c05567edb9404`

```
all-hands

Maya (People Ops): Hey all — quick heads-up about this Friday's all-hands (10:00 PT). Agenda draft below, please drop any Qs in-thread or add to the doc: https://redwoodinternal/ah/agenda-2028-03-05 :spiral_calendar:
Maya (People Ops): Agenda (30m total): 1) Exec update (Sam) 2) Product highlight + demo (Lina) 3) Runtime & infra health + roadmap (Devon / Tom) 4) Q&A (open mic) 5) Ops & benefits update (Maya) — aim to finish by 10:40 and leave 20m for small-group followups if needed.
Maya (People Ops): Please add 1-line Qs to the doc or paste here by Thu EOD. If you're remote and need captions or ASL, reply and we will arrange.
Sam (CEO): Looking forward to sharing a brief update on our Dedicated and Private momentum — will include a short customer story. :chart_with_upwards_trend:
Lina (Product): I'll demo the new rollout controls and can show a/ b canary flow. If anyone wants a specific route or model included in the demo, ping me.
Devon (Eng): Planning to show the new batching telemetry and a perf chart. We'll avoid running load tests during the call but have a short recorded snippet.
Tom (Infra): Note: we're scheduling a minor kernel/security patch Tue morning; it won't affect Friday's all-hands but FYI for anyone on Dedicated clusters.
Juno (Talent): Quick Q — will there be an update on the parental leave policy that was discussed in HR last month?
Maya (People Ops): Good Q Juno — yes, ops will include a summary of benefits updates and next steps. No policy will change without formal comms.
Olga (SRE): Can we have a 2-min slide on incident retro cadence? smallask: put a link to last quarter's incidents in the agenda doc.
Maya (People Ops): Thanks all — I'll lock agenda Thu 6pm PT and send calendar invite with dial-in + caption link.
--- (post-meeting)
Maya (People Ops): Thanks everyone who joined — posting quick meeting notes and recording link below.
Maya (People Ops): RecordingBot posted: https://redwoodinternal/ah/recordings/1851234567 (will also land in All-hands Resources channel)
Maya (People Ops): Key takeaways: 1) Sam: 2 new Dedicated customers in EMEA; sales motion is showing improved lead-to-commit conversion. 2) Lina: rollout canary fea
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_b4d35e0dc5d944708190a6b25b335c0a`

```
eng-oncall

incident-bot: :rotating_light: ALERT: High enqueue depth on inference-pool-3. 95th latency spiking to ~4s, error_rate=5% over 5m. Affected routes: /v1/generate, /v1/chat. Autoscaler at 90% and queuing growing.

jen_oncall: seeing it live. paging SRE. starting mitigation checklist.

miguel_sre: +1. Immediate suggested mitigations (short):
1) Apply org-level spike throttle (burst=50/s, steady=20/s)
2) Increase continuous batching window from 50ms -> 250ms to pack more requests (expected +20-40% throughput, p99 latency +~200ms)
3) Disable streaming for non-critical orgs to reduce token flush overhead
4) Temporarily reduce max_input_tokens for free-tier to 512
Any concerns?

aar oncall: how do we flip the batch window? need command/snippet.

miguel_sre: using admin-config API — sample:
```
curl -X POST 'https://internal-config.local/api/v1/batching/config' \\n  -H 'Authorization: Bearer REDACTED' \\n  -H 'Content-Type: application/json' \\n  -d '{"query":{"target":"inference-pool-3"},"patch":{"continuous_window_ms":250,"max_batch_tokens":4096}}'
```
Apply streaming toggle per-org:
```
curl -X POST 'https://internal-config.local/api/v1/featureflags' -d '{"org_pattern":"trial
…[truncated]
```

#### #2 `dsid_a7ddd026edfe4398a0de803474cb7bad`

```
eng-runtime

ashley: heads-up — after the runtime change that prefers the FlashAttention path we see an 8-12% throughput drop on small-seq workloads (seq <= 32). opening thread to collect profiling and tweak continuous-batcher heuristics.
omar: can you paste the perf summary? p50/p99 or tokens/sec?
ashley: p50 unaffected, p99 up ~30ms for tiny requests; tokens/sec down ~10% on our chat-heavy trace. quick profile: 
```
PROFILE small-seq workload (avg_seq=18):
- kernel-switch: flash_attn path selected 78%
- tokens/sec: 52k -> 47k (-9.6%)
- p99 latency: 210ms -> 240ms (+14%)
- batch_size distribution: median 6, tail >32 due to long polls
```
morgan: interesting — on my trace paged-KV promotions are happening mid-batch, causing extra memcpy and stalling the batcher. we see spike in CUDA memcpy latency at the same times.
rui: hypothesis: FlashAttention has lower arithmetic for long seqs but worse startup cost for very small sequences; kernel launch + workspace alloc kills tiny-batch efficiency. we should bias batch formation and token_budget targets to avoid too many tiny + flash combos.
omar: agree. propose two quick experiments: (1) per-batch kernel-choice based on avg_seq threshold (
…[truncated]
```

#### #3 `dsid_87c3919424d34ffcbf2638b9157901c8`

```
eng-ml

anya: hey — during the nightly load run the new quantized runner started applying a hard backpressure at ~1.2k tokens/s per shard, even though targets are 2.5k. results show throughput collapse and cost-per-token spikes. anyone seen this pattern?
jun-ho: saw a blip earlier, thought it was infra noise. do you have the runner logs?
anya: pasted main fragment below: 
```
2026-01-29T04:12:07Z runner[pid=8421] INFO  batcher: scheduling 64 reqs, shard=0
2026-01-29T04:12:07Z runner[pid=8421] WARN  backpressure: queue_length=512 threshold=256 apply=true
2026-01-29T04:12:07Z runner[pid=8421] INFO  kernel: selected int8-path quant_profile=fast32
2026-01-29T04:12:07Z runner[pid=8421] ERROR kvcache: prefetch stall detected, inflight=8
2026-01-29T04:12:08Z runner[pid=8421] INFO  backpressure: applied delay=120ms
```
anya: that 120ms delay multiplied across micro-batches killed tail latency and effective throughput.
mike_g: hmm kvcache prefetch stall + backpressure. could be our new prefetch window interacting with continuous batching. what's the repo sha?
anya: sha: a3f4b9c — the change was reducing prefetch concurrency from 16 -> 8 and adding an adaptive-delay in backpressure that scal
…[truncated]
```

#### #4 `dsid_644fae527fe648318b1af179fd2a118d`

```
eng-runtime

maria: FYI saw a perf regression in prefix cache hit-rate after yesterday's continuous-batching tweak. p99 token latency up and hit-rate down. Anyone else?

sam: saw alerts. numbers?

maria: quick snapshot from prod (last 1h):
```
- prefix-cache hit-rate: 62% -> 38% (pre/post change)
- overall token cost: +12%
- p50 token latency: 12ms -> 15ms
- p95 token latency: 38ms -> 62ms
- p99 token latency: 120ms -> 210ms
- fraction of mixed batches (prefix + no-prefix): 18% -> 52%
```

cheng: ugh. that batch mixing stat jumps out — continuous batching is aggressively filling windows and mixing short-prefix requests with cold ones. when we mix, cache hits go down because keying is per-client prefix variant.

kevin: do we have keying collisions or normalizations changed? I remember a change to trim trailing whitespace from the key last week.

maria: we rolled a kernel selection + batching heuristic PR (runtime#4127). keying change was just normalization (strip EOL), not a semantic change. But the batching policy now waits up to 6ms to assemble bigger batches, and it favors filling with anything available which increases heterogeneity.

sam: quick profiler dump from a representati
…[truncated]
```

#### #5 `dsid_fe8c351da7fe4f48a1115e12f4ef5005`

```
eng-runtime

rui: quick heads-up — after the kernel-selection change last night we're seeing ~8–12ms extra host-side on short chat flows.
olivia: ugh. source? ingress or host parse? :eyes:
matt: I can take a look, @rui can you paste the flamegraph or pprof snippet?
rui: gist of pprof: 
```text
pprof -http=:6060 /tmp/host.cpu
Total: 12.8ms
  4.2ms  32.8%  tokenization::tokenize
  3.6ms  28.1%  parse::request_unmarshal
  2.1ms  16.4%  grpc::writev_send
  1.7ms  13.3%  kvcache::lookup_miss
  1.2ms   9.4%  other
```
rui: kvcache miss rate up from 2% -> 17% on sub-16 token requests after minibatch heuristic picks kernel-A for 64 sequences.
anya: that suggests batcher is grouping dissimilar seq-lengths, evicting hot k-v shards. can we tweak minibatch alignment?
matt: kernel-selection change prefers kernel-A when avg-seq>32; but lots of short flows get coalesced into same batch. i'll add a quick guard to avoid kernel-A for avg<24.
olivia: also seeing grpc writev spike — chunking reduced to 512b frames causing more system calls. can we increase streaming chunk to 4k for host->gpu path?
infra-bot: deploy 1739987001 rolled kernel-selector v3 to canary (svc-rt-2), status: healthy
matt: i'll p
…[truncated]
```

#### #6 `dsid_3f82c6b8c22648828bdb30bdbc4d08b3`

```
all-hands

sam: Quick runtime follow-up from today's all-hands Q&A. Capturing owners + short timeline.

nora: Thanks. Main asks were kernel parity, batching defaults, and customer-facing notes.

diego: Kernel parity update: fused-attn + remat-mlp are green on unit tests; integration tests for long sequences scheduled Thu. Expect feature-complete by Friday.

kim: Batching defaults for Dedicated: we'll set `batch_size_target=56` and enable `kv_cache_sharing` on canary pools. Monitoring window 30m.

deploy-bot: canary deploy started (pool: canary-runtime-2) at commit c8d7a3.

sam: Metric thresholds: rollback if `kernel_fallback_rate` > 0.5% sustained for 10m, or p95 increases >10%.

nora: I'll draft the customer note about latency wins + short nondeterminism caveat and post for review.

diego: Adding `kv_miss_ratio` and `kernel_fallback_rate` to the runtime dashboard now.

kim: I'll own the infra roll-out, Diego owns runbook updates, Nora owns comms.

sam: Thanks all. Post any regressions here and tag me. :thumbsup:
```

#### #7 `dsid_1406539b05e245e7899f6441f78e561f`

```
incidents

incidents-bot: ALERT: [P1] increased 95th latency + node flaps on prod-us-east-1 serving cluster. Symptoms: repeated CUDA OOMs, container restarts, sustained queue growth in continuous-batcher. Auto-pager sent to @maria (oncall).

maria: seeing the alert, joining. can someone grab logs from the affected pods?

samir: grabbing logs now. initial grep shows repeated: 
```
RuntimeError: CUDA out of memory. Tried to allocate 1.20 GiB (GPU 0; 14.73 GiB total capacity; 12.34 GiB already allocated; 512.00 MiB free; 13.09 GiB reserved)
  at continuous_batcher.cpp:483 process_batch()
  at executor.cc:218 schedule()
```

raj: also seeing batch queue length climbing on host batch-worker-17: queue_size=1_924_000 and growing, cpu% 98, OOM kills on 3 restarts in last 2m.

elaine: thanks. hypothesis: a regression in batching window/flush logic allowed runaway batch aggregation (batch growth) when a downstream kernel started failing (CUDA OOM), causing backlog + deadlock in scheduler.

maria: immediate mitigation plan? priorities: 1) stop customer-facing latency blowup 2) prevent cascading node flaps 3) collect triage artifacts.

tasha: suggestion: flip the runtime feature-flag that disa
…[truncated]
```

#### #8 `dsid_bdf9d0a3684341c58cebdb98f26464fa`

```
eng-runtime

Kai (eng-runtime): Heads-up — saw a perf regression on FP8 mixed-precision when continuous batching is on + KV cache warmups. Profiling attached below, looks like kernel selector is flipping between fp8 -> int8 for certain shapes and padding waste blows up.

Maria (eng-ml): ugh. repro on main? which model/seq-len distribution?

Kai (eng-runtime): repro on staging with the 2.7B open model. Sequence length mix: 8/32/512 (mostly 8 and 32). Continuous batching policy groups by latency, so small requests get packed with long ones.

Dan (eng-runtime): can you paste the selector logs? curious if it's just fallback heuristics or something in kernel-shape matcher.

Kai (eng-runtime): selector snippet from trace:
```
[2026-03-15T14:12:22Z] model=rw-2.7b quant=fp8 batch_shapes=[8,32,512] chosen_kernel=fp8_matmul_compat
[2026-03-15T14:12:22Z] shape=8x4096 -> kernel=fp8_small_col_major
[2026-03-15T14:12:22Z] shape=512x4096 -> kernel=int8_large_row_major (fallback)
[2026-03-15T14:12:22Z] observed_padding=0.24 kv_cache_hits=0.43
```
Kai (eng-runtime): note the fallback on the 512 chunk — CPU fallback for quant conv path increased latency.

Priya (eng-sre): perf-bot shows a 2.3x p95 i
…[truncated]
```

#### #9 `dsid_ba3b8c9ea5004dab9b332c9ba9cfc8f9`

```
eng-platform

maya: Heads up — p99 jumped ~180ms on the model latency dashboard after the quantized-batched rollout this morning. Appears concentrated on /v1/generate in EU-prod. https://dash.internal/redwood/xyz :thinking:
liam: I’m seeing p50 flat, p95 +40ms, p99 +180ms. Small payloads only (tokens < 40). Could be batching behavior + new kernel scheduling.
maya: query i ran: ```SELECT percentile(lat_ms, 50), percentile(lat_ms, 95), percentile(lat_ms, 99), count(*) FROM latency
WHERE route='/v1/generate' AND env='eu-prod' AND model_variant='rdw-gpt-q4_batched'
GROUP BY endpoint, routing_policy```
anika: did we change routing policy weights for EU earlier? Canary weight bumped from 10% -> 35% at 09:50.
ops-bot: deploy-bot: Canary rollout rdw-gpt-q4_batched id=canary-2026-03-23T09:48 completed.
samir: if tdigest rollups are merged across variants with different sequence-length distributions, pctl values can skew. We should check raw sample counts vs tdigest merge metadata.
liam: good call — i’ll pull raw samples for the affected hour, also check KV cache hit rates.
maya: saved query to pin: ```curl -s -H 'Authorization: Bearer $TOKEN' 
  'https://telemetry.internal/api/query?from=61
…[truncated]
```

#### #10 `dsid_5a8604739f9b42b199a09d5e42eb241c`

```
eng-ml

Mira: quick heads-up — during quill9b-int8 bring-up I saw a p99 latency spike when context >8k with adaptive KV cache + dynamic batching enabled.
Jon: can you paste the perf summary / logs?
Mira: pasted below — results from a 1k req sweep (varying ctx len). tl;dr: throughput OK, but p99 jumps ~3x at 12k-16k ctx.

bench-bot: automated-run: https://benchboard.internal/runs/sha/01f3a — summary: p50 98ms, p95 170ms, p99 420ms at ctx=16k; int8, batch=auto, kvcache=adaptive

Mira: logs snippet:
```
[2026-03-18T14:02:10Z] request id=abc123 ctx=16384 tokens=1024 batch_size=8 latency_ms=421 p50=96 p95=168
[2026-03-18T14:02:11Z] runtime: selected_kernel=fast_attn_v2 mode=int8 kv_cache=adaptive batcher=dynamic
[2026-03-18T14:02:12Z] perf: kvhit=0.12 padding_frac=0.47
```
Kai: padding_frac 0.47 is huge — looks like dynamic batching is grouping lots of shorter prefixes with long ctx ones, causing extra pad work on GPU.
Sofia: could also be KV cache thrashing — adaptive policy may be evicting hot keys for long sequences, forcing recompute.
Arman: can we repro with `batch=static` and `kvcache=fixed`? that should isolate batching vs kv eviction.
Mira: yes running that next. command I'm usi
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 27: `qst_0144::basic` · N=40000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved document IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to latency and batching but do not specifically address the question about the median latency improvement from continuous batching. The failure mode is a lexical mismatch, as the retrieved documents do not match the specific content of the expected document. Both gold and retrieved chunks are non-empty and on-topic, but the retrieved chunks lack speci

### Question

In the recent Friday all-hands notes, what was the reported median latency improvement attributed to continuous batching?

### Gold document(s)

#### GOLD `dsid_a227a7f316c4452eab4c05567edb9404`

```
all-hands

Maya (People Ops): Hey all — quick heads-up about this Friday's all-hands (10:00 PT). Agenda draft below, please drop any Qs in-thread or add to the doc: https://redwoodinternal/ah/agenda-2028-03-05 :spiral_calendar:
Maya (People Ops): Agenda (30m total): 1) Exec update (Sam) 2) Product highlight + demo (Lina) 3) Runtime & infra health + roadmap (Devon / Tom) 4) Q&A (open mic) 5) Ops & benefits update (Maya) — aim to finish by 10:40 and leave 20m for small-group followups if needed.
Maya (People Ops): Please add 1-line Qs to the doc or paste here by Thu EOD. If you're remote and need captions or ASL, reply and we will arrange.
Sam (CEO): Looking forward to sharing a brief update on our Dedicated and Private momentum — will include a short customer story. :chart_with_upwards_trend:
Lina (Product): I'll demo the new rollout controls and can show a/ b canary flow. If anyone wants a specific route or model included in the demo, ping me.
Devon (Eng): Planning to show the new batching telemetry and a perf chart. We'll avoid running load tests during the call but have a short recorded snippet.
Tom (Infra): Note: we're scheduling a minor kernel/security patch Tue morning; it won't affect Friday's all-hands but FYI for anyone on Dedicated clusters.
Juno (Talent): Quick Q — will there be an update on the parental leave policy that was discussed in HR last month?
Maya (People Ops): Good Q Juno — yes, ops will include a summary of benefits updates and next steps. No policy will change without formal comms.
Olga (SRE): Can we have a 2-min slide on incident retro cadence? smallask: put a link to last quarter's incidents in the agenda doc.
Maya (People Ops): Thanks all — I'll lock agenda Thu 6pm PT and send calendar invite with dial-in + caption link.
--- (post-meeting)
Maya (People Ops): Thanks everyone who joined — posting quick meeting notes and recording link below.
Maya (People Ops): RecordingBot posted: https://redwoodinternal/ah/recordings/1851234567 (will also land in All-hands Resources channel)
Maya (People Ops): Key takeaways: 1) Sam: 2 new Dedicated customers in EMEA; sales motion is showing improved lead-to-commit conversion. 2) Lina: rollout canary fea
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_a883ceba9c4244bc9297a97a96f5b35e`

```
support

Sam K: Hey — after a marketing promo we saw embedding 99th pct latency jump to ~6s for a specific client. They send lots of tiny texts (2–8 tokens). No errors, just tail spike. Anyone seen this with dynamic batching?
Priya R: Which model/endpoint and any recent deploys? Also what are your dynbatch settings (max_batch_size, coalesce_window_ms)?
Sam K: Endpoint: /v1/embeddings (model: redwood-embed-1024). No deploys. Dynbatch config from tenant: max_batch_size=128, coalesce_window_ms=5, per_client_priority=false. 95th ~2s, 99th ~6s, median ~40ms.
Matt G: That pattern (many tiny requests) can create lots of tiny batches which increases scheduling overhead + queue jitter. Can you paste a short runtime trace / batch_size histogram?
Sam K: Sure — pasted metrics from the last 5m: 
```
batch_size_histogram: {1: 42%, 2-4: 33%, 5-16: 20%, >16: 5%}
avg_coalesce_wait_ms: 2.1ms
p50_queue_depth: 1
p99_queue_depth: 18
cpu_sched_time_ms (per-batch): median 0.6ms, p99 4.8ms
```
Logs show a ton of batches with size 1-2.
Priya R: Yep — those tiny batches push up tail. Two levers: increase coalesce_window_ms (let more requests join a batch) OR lower max_batch_size and enable per-client batchi
…[truncated]
```

#### #2 `dsid_b4d35e0dc5d944708190a6b25b335c0a`

```
eng-oncall

incident-bot: :rotating_light: ALERT: High enqueue depth on inference-pool-3. 95th latency spiking to ~4s, error_rate=5% over 5m. Affected routes: /v1/generate, /v1/chat. Autoscaler at 90% and queuing growing.

jen_oncall: seeing it live. paging SRE. starting mitigation checklist.

miguel_sre: +1. Immediate suggested mitigations (short):
1) Apply org-level spike throttle (burst=50/s, steady=20/s)
2) Increase continuous batching window from 50ms -> 250ms to pack more requests (expected +20-40% throughput, p99 latency +~200ms)
3) Disable streaming for non-critical orgs to reduce token flush overhead
4) Temporarily reduce max_input_tokens for free-tier to 512
Any concerns?

aar oncall: how do we flip the batch window? need command/snippet.

miguel_sre: using admin-config API — sample:
```
curl -X POST 'https://internal-config.local/api/v1/batching/config' \\n  -H 'Authorization: Bearer REDACTED' \\n  -H 'Content-Type: application/json' \\n  -d '{"query":{"target":"inference-pool-3"},"patch":{"continuous_window_ms":250,"max_batch_tokens":4096}}'
```
Apply streaming toggle per-org:
```
curl -X POST 'https://internal-config.local/api/v1/featureflags' -d '{"org_pattern":"trial
…[truncated]
```

#### #3 `dsid_a7ddd026edfe4398a0de803474cb7bad`

```
eng-runtime

ashley: heads-up — after the runtime change that prefers the FlashAttention path we see an 8-12% throughput drop on small-seq workloads (seq <= 32). opening thread to collect profiling and tweak continuous-batcher heuristics.
omar: can you paste the perf summary? p50/p99 or tokens/sec?
ashley: p50 unaffected, p99 up ~30ms for tiny requests; tokens/sec down ~10% on our chat-heavy trace. quick profile: 
```
PROFILE small-seq workload (avg_seq=18):
- kernel-switch: flash_attn path selected 78%
- tokens/sec: 52k -> 47k (-9.6%)
- p99 latency: 210ms -> 240ms (+14%)
- batch_size distribution: median 6, tail >32 due to long polls
```
morgan: interesting — on my trace paged-KV promotions are happening mid-batch, causing extra memcpy and stalling the batcher. we see spike in CUDA memcpy latency at the same times.
rui: hypothesis: FlashAttention has lower arithmetic for long seqs but worse startup cost for very small sequences; kernel launch + workspace alloc kills tiny-batch efficiency. we should bias batch formation and token_budget targets to avoid too many tiny + flash combos.
omar: agree. propose two quick experiments: (1) per-batch kernel-choice based on avg_seq threshold (
…[truncated]
```

#### #4 `dsid_77ea2b1d92d94269ad5c55cb9dfdd792`

```
eng-runtime

julie_support: quick heads-up / support just routed two escalations — customers report sudden p95/p99 increases after last night's runtime rollout (v1.4.2). No error traces, just much higher tails. Can runtime / infra triage? :interrobang:

mike_runtime: which customers and which endpoints? any request IDs?

julie_support: Customer-Atlas and Customer-Beta, mostly the /generate route (text gen) and a couple embedding requests. They saw p95 jump from ~100ms to ~300-450ms and p99 up near 1.1s. First reports around 2023-11-13T03:50Z (post-deploy).

deploy-bot: deployed runtime v1.4.2 -> pool:prod at 2023-11-13T03:30Z by @mike_runtime

emma_sre: quick PromQL checks coming up:
```
histogram_quantile(0.95, sum(rate(request_duration_seconds_bucket{route="/generate"}[5m])) by (le))
histogram_quantile(0.99, sum(rate(request_duration_seconds_bucket{route="/generate"}[5m])) by (le))
```

mike_runtime: running those now 1030Z metrics show cluster p95 increased to ~340ms right after 03:30. Canary nodes 410ms p95; legacy nodes ~110ms.

sanjay_prod: what changed in 1.4.2? I recall a kernel dispatch change and a batching tweak.

mike_runtime: correct 1: kernel-dispatch v2 (prefers fuse
…[truncated]
```

#### #5 `dsid_84dd557786524607b1f32119d44f9c97`

```
eng-ml

maya: kicked off a regional continuous-batcher sweep comparing H100 vs A100 across APAC/EU. focusing on window jitter, max_batch_tokens, and kernel selection. baseline is q4_0 quantized mosaic-13b.
jin: great — which metrics did you capture? latency p50/p95, tokens/sec, and quality delta?
maya: yup. p50/p95, tokens/s, kernel time breakdowns, and offline evals (perplexity + a small prompt set). attached short logs below.
bench-bot: RUN 2412345678 STARTED: cont-batch-sweep --model mosaic-13b-q4_0 --regions apac,eu --gpus h100,a100 --windows 10,20,40 --max_tokens 512,1024 --kernels fused,split
oscar: quick note — we saw earlier that increasing max_batch_tokens reduces p50 but hurts tail due to microburst queueing. watch the >95th percentile.
maya: exactly. raw highlights:
- H100 APAC window=20 max_tokens=512 fused kernel: p50 28ms, p95 190ms, tokens/s 7200
- A100 EU window=20 max_tokens=512 fused kernel: p50 42ms, p95 240ms, tokens/s 4500
- H100 APAC window=40 max_tokens=1024 split kernel: p50 34ms, p95 305ms, tokens/s 9200 (but p95 spikes)
- A100 EU window=10 max_tokens=512 fused kernel: p50 46ms, p95 210ms, tokens/s 3900
jin: interesting that split kernel pushes tokens/s hig
…[truncated]
```

#### #6 `dsid_87c3919424d34ffcbf2638b9157901c8`

```
eng-ml

anya: hey — during the nightly load run the new quantized runner started applying a hard backpressure at ~1.2k tokens/s per shard, even though targets are 2.5k. results show throughput collapse and cost-per-token spikes. anyone seen this pattern?
jun-ho: saw a blip earlier, thought it was infra noise. do you have the runner logs?
anya: pasted main fragment below: 
```
2026-01-29T04:12:07Z runner[pid=8421] INFO  batcher: scheduling 64 reqs, shard=0
2026-01-29T04:12:07Z runner[pid=8421] WARN  backpressure: queue_length=512 threshold=256 apply=true
2026-01-29T04:12:07Z runner[pid=8421] INFO  kernel: selected int8-path quant_profile=fast32
2026-01-29T04:12:07Z runner[pid=8421] ERROR kvcache: prefetch stall detected, inflight=8
2026-01-29T04:12:08Z runner[pid=8421] INFO  backpressure: applied delay=120ms
```
anya: that 120ms delay multiplied across micro-batches killed tail latency and effective throughput.
mike_g: hmm kvcache prefetch stall + backpressure. could be our new prefetch window interacting with continuous batching. what's the repo sha?
anya: sha: a3f4b9c — the change was reducing prefetch concurrency from 16 -> 8 and adding an adaptive-delay in backpressure that scal
…[truncated]
```

#### #7 `dsid_644fae527fe648318b1af179fd2a118d`

```
eng-runtime

maria: FYI saw a perf regression in prefix cache hit-rate after yesterday's continuous-batching tweak. p99 token latency up and hit-rate down. Anyone else?

sam: saw alerts. numbers?

maria: quick snapshot from prod (last 1h):
```
- prefix-cache hit-rate: 62% -> 38% (pre/post change)
- overall token cost: +12%
- p50 token latency: 12ms -> 15ms
- p95 token latency: 38ms -> 62ms
- p99 token latency: 120ms -> 210ms
- fraction of mixed batches (prefix + no-prefix): 18% -> 52%
```

cheng: ugh. that batch mixing stat jumps out — continuous batching is aggressively filling windows and mixing short-prefix requests with cold ones. when we mix, cache hits go down because keying is per-client prefix variant.

kevin: do we have keying collisions or normalizations changed? I remember a change to trim trailing whitespace from the key last week.

maria: we rolled a kernel selection + batching heuristic PR (runtime#4127). keying change was just normalization (strip EOL), not a semantic change. But the batching policy now waits up to 6ms to assemble bigger batches, and it favors filling with anything available which increases heterogeneity.

sam: quick profiler dump from a representati
…[truncated]
```

#### #8 `dsid_3d2f2b3332f047e3b9e74165001fd24a`

```
incidents

IncidentBot: [PAGER] kv-cache memory cliff detected in prod-west-1: sustained GPU mem usage spike + OOMs across multiple pods — severity: P1. Auto-escalation to oncall.
Maya (oncall): seeing it, joining. agree this looks like the continuous-batching path. metrics: eviction_rate x10, avg-batch-size spiked.
Maya (oncall): @Jun can you confirm if the new batching cap rollout touched prod-west yesterday?
Jun (eng-runtime): we rolled a config bump to continuous_batch.max_tokens=4096 -> 8192 at 03:12 UTC for canary -> gradually to prod. Canary looked fine.
Oliver (eng-ml): perf test showed compaction regressions with long prefixes and quantized cache entries; might exacerbate fragmentation.
Rachel (sre): customer impact: several webhooks reporting +500 latencies, a few 503s. CS says two enterprise tenants reported errors. tagging CustomerOps.
CustomerOps: confirmed two customers got increased error rates, ticket opened INC-4729. Need ETA on mitigation.
Jun (eng-runtime): grabbing logs. initial error in pod gpu-23: "cudaMalloc failed: out of memory" followed by multiple retries and then eviction thrash. snippet:
```
E 2026-03-15T03:45:12Z runtime.cpp:624 cudaMalloc(ptr=0x7f3a..
…[truncated]
```

#### #9 `dsid_84d5400bfd0d4d7781a16c6456c1ca16`

```
incidents

alex: FYI — customer `Brightline` reporting bursts of 5xx / 504s to the hosted inference endpoint starting ~08:15 UTC. Multiple tenants affected. :rotating_light:
sofia: hitting us too, seeing p95 jump to 9s and a tsunami of queued requests in the batcher.
sofia: stack: hosted-gateway -> ingress-batcher -> continuous-batcher pool -> model-worker
ingress-sre: can you paste the gateway logs and batcher depths?
sofia: gateway logs (snip):
```
[2026-03-18T08:14:53Z] INFO incoming_requests=1248 in_flight=512 dropped=0
[2026-03-18T08:15:02Z] WARN enqueue_time_ms_p95=4800 queue_depth=10240
[2026-03-18T08:15:07Z] ERROR 504 gateway_timeout request_id=rid_8c12
```
```
batcher metrics (prom): continuous_batch_queue_depth{pool="cbatch-eu"} 10240
continuous_batch_dequeued_rate 120/s
continuous_batch_pending_batches 420
continuous_batch_process_time_p95 6500
```
devon: that queue_depth is > configured max (8192). Looks like backlog growth due to slow dequeues from model-worker. Are workers seeing OOM/GC?
mira: model-worker logs show frequent long KV cache misses and repeated long steals:
```
WARN kvcache_miss=1.0 seq_len=2048 decode_ms=1200 -> fallback slow-path
WARN gpu_util=98% mem_
…[truncated]
```

#### #10 `dsid_cf1e3fbe20b74484971e94f8d7f4fed6`

```
eng-runtime

aditya singh: Heads-up: we enabled microstrand scheduling on canary GPUs at 07:45 PT and wanted to share an ultra-brief snapshot. Early telemetry: p50 latency -12%, p95 -18%, memory working set down ~16% for typical 2k-3k seq loads. Token cost estimate improvement ~-28% for mixed gen workloads (gpt-medium family).

leah kim: wow those numbers look great. did you run the stress-suite across bursty traffic?

aditya singh: yes, ran the burst and PLG replay sets. Throughput improved ~9% when packing small concurrent streams. Observed one anomaly: increased jitter for long streaming sessions (~0.8% sessions had >200ms spikes) during kernel handover window.

omar gomez: any errors surfaced? timeouts / 5xx?

aditya singh: transient 504s rose by 0.15% in the first 8m as a result of a race between the eviction thread and the microstrand allocator. We pushed a quick mitigation (serialize the eviction for >8k contexts) and the rate returned to baseline within 4m. No customer tickets.

perf-bot: Canary dashboard (08:10 PT): p50=62ms -> 55ms, p95=220ms -> 180ms. TokenCost/1M: $0.82 -> $0.59. Events: microstrand_toggle=enabled @2012345678, mitigation_patch=@2012345686. https://redwo
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 28: `qst_0150::basic` · N=50000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, indicating a lexical mismatch. The retrieved chunks discuss API key issues but do not directly address permission scopes, which is the focus of the question. The hit_at_10_auto flag is incorrectly set to False, as no expected document ID is retrieved. The gold chunk is relevant but not directly answering the question, while retrieved chunks are somewhat related but not specific to permission scopes.

### Question

What are the required permission scopes for an API key when SDK examples fail with a 401 unauthorized error during developer onboarding?

### Gold document(s)

#### GOLD `dsid_5af1ed23fd2a4bb3984ec368d0e3b23e`

```
Developer Onramp: Localization, Docs-site Ops, and Canonical Fixes Playbook

Overview

This playbook bundles three tightly related areas that frequently cause onboarding friction for new integrations: SDK localization (i18n) readiness, docs-site operational procedures (staging/canary/translation pipelines), and a compact set of canonical fixes for the top support issues we see from developer onramps. The goal is a one-page operational reference that engineering, Docs, and Support can use during new SDK ship weeks and customer trials.

Goals
- Reduce mean-time-to-first-success (MTTFS) for new SDK adopters by 30% through localized examples and a repeatable docs deploy pipeline.
- Provide concise canonical fixes for the top 8 devx support issues so Support can resolve 60% of triageable tickets without engineering intervention.
- Maintain a low-friction docs release process (canary -> staged -> prod) with clear rollback semantics and telemetry hooks.

Audience
- Developer Experience engineers and tech writers shipping SDK examples and docs.
- Support engineers handling integration issues and reproductions.
- Product engineers owning SDKs or client libraries.

Scope and non-goals
- Included: JavaScript/TypeScript, Python, and Go SDK snippets; docs-site content lifecycle; translation handoff and CI checks; canonical fixes for common API/SDK errors.
- Excluded: full localization of legal or marketing copy; mobile SDKs beyond sample snippets.

Prerequisites
1) Repo layout: all SDK examples live under repo: redwood/devx-examples (branch: main).
2) Docs-site: hosted via docs.redwood-inference.internal, uses static site generator with i18n plugin (locales in /i18n/*.json).
3) CI: GitHub Actions with workflows: docs-canary.yml, docs-staged.yml, docs-prod.yml.
4) Telemetry: snippet telemetry.events.example_load, telemetry.tags.locale, and telemetry.context.sdk_version must be emitted by sample harness.

Quickstart: Localized SDK Example Bundle (developer flow)
1. Clone examples: git clone git@github.com:redwood/devx-examples.git && cd devx-examples
2. Install toolchain (node/pip/go): ./scripts/bootstrap-dev.sh
3. Generate locale-specific examples: ./scripts/generate-localize
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_6f37b2b4341947028019bd41748eaff9`

```
Python SDK sends 'Bearer Bearer' in Authorization header for some configs

Issue summary: Customer upgraded to redwood-sdk-python v0.9.4 and began receiving 401 Unauthorized. Their proxy logs show Authorization header is 'Bearer Bearer <key>' (double prefix). They previously passed api_key='Bearer <key>' (historical pattern from other vendors). Impact: auth failures in one service until rollback. Steps: (1) Initialize client with api_key that already includes 'Bearer ' (2) SDK adds Bearer prefix again (3) API rejects. Expected: SDK should accept raw key only OR detect and avoid double prefix and warn.
Ava Chen (Support): Customer insists they have always stored the value with the prefix; they missed this requirement in docs.
Ethan Park (DevEx): This is technically misconfiguration, but we should add a guardrail: if api_key starts with 'Bearer ' then strip the prefix and log a warning.
Ava Chen: Provided workaround: store raw key only (no prefix).
Ethan Park: Marking as closed with docs + validation improvement tracked separately (INT-771).
```

#### #2 `dsid_a75a4d9aa7d940009b7966188753d520`

```
New user quickstart fails with 401 "invalid_api_key" (wrong API key or env var name)

Issue summary:
Customer is following the Hosted API quickstart and consistently receives HTTP 401 with error "invalid_api_key". Root cause appears to be using the wrong API key value (copied from the wrong Console context) and/or setting an incorrect environment variable name, resulting in the SDK sending an empty/incorrect Authorization header.

Impact:
Blocks time-to-first-success (TTFS). Customer cannot complete the first request step and is at risk of churn.

Customer report (verbatim-ish):
"We’re using the Python quickstart, but every request returns 401 invalid_api_key. We copied the key from the console and set it as an env var. Not sure what we’re missing."

Environment:
- Hosted API (prod)
- Region: us-east
- Python SDK quickstart (customer did not specify exact version initially)
- Running locally (MacOS)

Steps to reproduce (from customer + internal repro):
1) Create API key in Console
2) Export env var
3) Run the Python quickstart snippet
4) Observe 401 invalid_api_key

Observed error:
- HTTP status: 401
- Body: {"error":{"type":"invalid_request_error","code":"invalid_api_key","message
…[truncated]
```

#### #3 `dsid_a8af533a3f89402ca739bfdc5322b42e`

```
Python SDK returns 401 after API key rotation (works via curl)

Issue summary: Customer rotated their Redwood API key and started receiving 401 Unauthorized when using redwood-sdk-python v0.9.3. Same key works via curl and via the Hosted API playground. Impact: production traffic blocked for one service. Environment: Python 3.11, requests transport, running on AWS ECS. Steps: (1) set REDWOOD_API_KEY env var to the new key (2) run their existing integration (chat.completions) (3) observe 401. Notes: customer suspects the SDK is trimming or transforming the key. Request ID provided in attachment.
Aisha Rahman (Support): Confirmed 401s in logs. Ingestion shows Authorization header present but value differs from expected length; looks like trailing whitespace/newline?
Ethan Park (DevEx): Could be env var parsing; some CI systems inject a newline. We should strip only "
" and surrounding whitespace carefully, but not touch internal chars.
Customer (Kiteframe): We store the key in AWS Secrets Manager and inject as env var. We noticed the secret value ends with a newline in their console export.
Ethan Park: Repro with key ending in "
"; current SDK uses .strip() which removes more than ne
…[truncated]
```

#### #4 `dsid_65b12644ea52428b9c032d2cd9b75d8a`

```
Add SDK guardrail: detect 'Bearer ' prefix in api_key and warn across SDKs

Background: Support saw multiple customer-reported auth issues due to key/header formatting across SDKs (SUP-4821, SUP-4884, SUP-4902, SUP-4933). Proposal: add a shared validation behavior across SDKs: (1) if api_key value begins with 'Bearer ' strip prefix and log warning (2) if trailing CR/LF exists, trim and warn (3) if other whitespace exists, error with actionable message. Also update docs and support playbook.
Logan Wright: Align behavior w/ TS and Go changes already merged; need python follow-up PR for Bearer prefix detection.
Ava Chen: Please prioritize docs update; support keeps seeing this.
Logan Wright: Will draft minimal spec and open PRs per SDK.
```

#### #5 `dsid_1a160e1c00934f108e17183f44e3ca77`

```
Go SDK reports 'invalid API key' when key loaded from file includes trailing newline

Issue summary: Customer running Redwood Private deployment reports Go SDK errors 'invalid API key' after moving from env var injection to reading key from a mounted file. They confirmed the key works via curl when manually copied. Impact: app cannot authenticate to private control plane. Steps: (1) read file contents (2) pass string to redwood.NewClient(apiKey) (3) API returns 401 with message invalid_api_key. Hypothesis: key string contains trailing newline or spaces.
Jordan Blake (Support): Customer logs show key length one char longer than expected; likely 
.
Elliot Price (DevEx): Go SDK currently validates key with a regex and fails if it contains whitespace; we should probably trim only trailing 
 and provide a clearer error.
Customer (Northwind Health): Confirmed file ends with newline. Removing newline fixes.
Elliot Price: Added patch to tolerate trailing newline when key is loaded via helper; added docs note.
```

#### #6 `dsid_f940e7c95688406cb497b0b1dab44e99`

```
Known issues: API key rotation/revocation edge cases

# Summary
This page documents recurring customer issues encountered during Hosted API key rotation/revocation.

# Issue 1: intermittent 401s after rotation
**Symptoms**
- Some requests succeed, some fail with 401.

**Likely cause**
- Customer updated one service but not all workloads (cron jobs, background workers, edge functions).

**Recommended fix**
- Search customer repos/infra for the old key name/secret reference.
- Deploy new secret everywhere.
- After validating all components, revoke the old key.

# Issue 2: propagation delays (rare)
**Symptoms**
- Immediately after disabling a key, a small number of requests still authenticate for a short window.

**Notes**
- The system is designed for immediate revocation, but a limited edge-cache inconsistency has been observed in rare cases.

**Workaround**
- Advise customer to allow up to 60 seconds.
- If it persists > 5 minutes, open a support ticket and capture request ids.

# Issue 3: customer pasted key id, not key value
**Symptoms**
- All requests fail with 401 immediately after update.

**Fix**
- Clarify difference between the key record identifier vs the secret key value sho
…[truncated]
```

#### #7 `dsid_26db0d269ce04474afdae8bf7265e1ca`

```
Northwind Analytics: rotate/revoke Hosted API key after suspected CI exposure

Issue summary:
Customer believes a Hosted API key may have been exposed in CI logs. They want to revoke/rotate quickly and understand expected behavior (401s, propagation).

Impact:
Potential unauthorized access if key compromised. Customer proactively disabling key; risk of self-inflicted outage if rotation not coordinated across services.

Environment:
Hosted API, prod, us-east.

Requested outcome:
Provide canonical steps and confirm revocation behavior.
2025-02-12 Vanessa Ortiz (CS): Advised customer to disable/revoke first given suspected exposure, then create/regenerate a new key and deploy via secrets manager. Reminded them not to paste secret values in ticket/email.

2025-02-12 Dev Patel (Eng): Confirmed revocation is immediate by design; in rare cases edge-cache propagation may take up to ~60 seconds. If longer, collect request IDs and timestamps.

2025-02-12 Camila Reyes (Support): Sent customer link to internal customer guide page and copied the relevant Console steps (Settings > API Keys > Disable/Regenerate).

2025-02-13 Vanessa Ortiz (CS): Customer confirmed key disabled and new key deployed
…[truncated]
```

#### #8 `dsid_c6efd46ecc6449ac8be1e53ed3803e92`

```
Tolerate trailing newline in API key and improve auth error messaging

Context: SUP-4902. Customers reading API keys from mounted files often include a trailing newline. The Go SDK previously validated the API key string strictly and returned a generic 'invalid api key' error, causing confusion. Changes: if key ends with CR/LF, trim only those characters; if other whitespace exists, return a clearer error message pointing to the whitespace; add unit tests; update README guidance for Kubernetes secret mounts. Release: v0.6.2.
Hiro Tanaka: Any risk of accepting invalid keys?
Elliot Price: Only CR/LF at end; API still validates key server-side; this just prevents obvious footguns.
Jordan Blake: Please reference private deployment troubleshooting page.
Elliot Price: Added link in README.
```

#### #9 `dsid_f0b14f9b0cf2409baf9ee85b61b507c7`

```
API key lifecycle (Hosted): creation, rotation, and revocation

# Purpose
This policy defines Redwood Inference requirements for **Hosted API key** lifecycle management, including creation, storage, rotation, and revocation.

# Scope
- Applies to: Hosted API customers and internal staff with access to customer orgs/projects.
- Does not cover: Dedicated/Private customer-managed identity providers (SSO/IAM) beyond the Hosted API key surface.

# Requirements
## 1. Creation
- Keys must be created per environment (prod vs non-prod) and per application/service when feasible.
- Keys must be named using the convention: `{env}-{service}-{owner}-{YYYYMM}` (example: `prod-billing-worker-cs-202504`).

## 2. Storage
- Keys are secrets and must not be shared over Slack or pasted in Jira tickets.
- Keys must be stored in a secrets manager (1Password, AWS Secrets Manager, GCP Secret Manager, Vault) and injected via CI/CD.

## 3. Rotation
- Recommended rotation frequency: every 90 days for enterprise customers; every 180 days otherwise.
- Rotation must follow a **two-key overlap** approach when possible:
  1) Create new key
  2) Deploy new key
  3) Confirm success
  4) Revoke old key

## 4. Revocat
…[truncated]
```

#### #10 `dsid_89c64051f03340b584e438dceebcc4ad`

```
support

samira.k: Hey team, customer 'AcmeCloud' says they suddenly get 403 when opening Audit Log -> Exports > Retention settings. They used to be able to view. Screenshot attached in thread (link).
jorge.m: Can you paste the exact error? 403 could be entitlement or token scopes.
samira.k: Console shows a modal: "You do not have permission to view audit exports. (error: audit.view_denied)". API calls to /v1/audit/exports return: 
```
HTTP/1.1 403 Forbidden
{
  "error": "insufficient_scope",
  "detail": "missing scope: audit.read"
}
```
jorge.m: Ok that looks like token scope. Is this user signing in via SSO? Or using API key?
samira.k: It's SSO (Okta OIDC). User logs into the console; everything else works. Only audit exports/retention pages blocked.
tina-support: Quick checklist — 1) confirm user role in SCIM/IdP mapping 2) check OIDC token scopes and 'aud' 3) ensure org has retention entitlements (billing)
maya-secc: I ran token introspection for the user's session token (redacted) — token claims: 
```
{
  "sub": "00u123...",
  "scp": ["openid","profile","email","console.read"],
  "aud": "redwood-web",
  "roles": ["engineering"]
}
```
maya-secc: Not seeing audit.read in scp. Al
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 29: `qst_0156::basic` · N=50000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the topic of deployment and fallback strategies but do not directly address the specific question about composite health score thresholds. The gold chunk is on-topic and non-empty, providing detailed context about deployment policies and fallback strategies. The failure mode is likely an embedding near miss, as the retrieved documents are related but not sp

### Question

In the planning meeting about a strict deployment change freeze and automatic fallback during a model rollout, what composite health score thresholds defined green, amber, and red states?

### Gold document(s)

#### GOLD `dsid_9c63777c789c4f7db9e391024dd887ae`

```
Deployment sterile window and fallback choreography

Planning session to finalize deployment sterile-window policy, coordinated fallback choreography across regions, and align on runbook triggers + telemetry gating for launch. Focus on minimizing blast radius during model rollout and ensuring fast automatic fallback to edge model variants. Discussed A/B gating, canary thresholds, and required dashboards and runbook edits.
Header: 2027-01-19 10:00 PST / Duration 62 minutes / Attendees: Avery Chen, Sofia Ramos, Jonah Park, Priya Nair, Marco Li, Ellen Graves, Tomás Rivera

00:00 Avery Chen: ok let's kick off, thanks for carving the time, I want to get to one clear sterile deployment window policy and the fallback choreography so we can ship the optimizer bits this sprint
00:12 Marco Li: yep morning, we've got exec eyes on this, timeline hasn't changed, go-no-go is end of next week
00:18 Sofia Ramos: quick note, the runtime team pushed the KV cache optimization which reduces cold-starts but it flips some timings, so we need to adjust canary thresholds
00:30 Jonah Park: (murmur) uh and the dedicated pools behave differently under prefix caching
00:34 Priya Nair: agreed, we've seen the metric skew on P50 vs P95 when prefix hits rise
00:40 Ellen Graves: just so we're aligned, sterile window means no schema or infra changes during the seventy-two hour window around rollout? how strict
00:52 Avery Chen: yeah, strict. we want only immediate rollback-safe toggles during the window. No infra merges unless critical. Also, all canary traffic routes must be reproducible and reversible
01:06 Tomas Rivera: question on region routing — if a region is degraded do we fail-over to nearest region or to a cheaper model variant in same region
01:18 Sofia Ramos: we prefer same-region fallback when possible to reduce latency impact; if capacity is exhausted then route to variant-small which is quantized
01:30 Marco Li: is variant-small acceptable for early customers? it changes token quality
01:36 Jonah Park: quick comment — quality drop is measurable but for 60% of edge cases it's fine, we need a customer-facing SLA note
01:48 Priya Nair: and KMS keys for the private deployments — do we
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_83effe9968594d25a5ecb719178034c6`

```
Composite-signal strategy and rollback heuristics for Optimize evals

PRD and acceptance criteria for a composite evaluation signal used by Optimize to decide A/B winners, canary progression, and automated rollback triggers. Focus: prompt set stratification, per-metric regression thresholds, composite scoring, statistical test settings, and severity-tiered rollback heuristics.
Optimize currently emits per-prompt and per-metric deltas for candidate model changes but lacks a standardized composite decision pipeline and actionable rollback rules. PMs and SREs need a repeatable, explainable mechanism so quality regressions are caught early without excessive false positives that block safe rollouts.
Define a composite signal that aggregates semantic quality, safety, latency, and cost into a single actionable score
Specify A/B test parameters (alpha, power, effect sizes) to use across canary sizes
Create tiered rollback triggers (soft alert -> pause -> auto-rollback) with explicit numeric thresholds and aging rules
Produce acceptance criteria and test harness to validate the gating logic before shipping
Model-selection heuristics (e.g., choose quantization level) rather than eval gating

…[truncated]
```

#### #2 `dsid_705b5d2b5ddb4e098964fa67911a0daf`

```
QBR health signal exploration & scoring lab

Purpose / context:
This is a working lab document—notes from QBR signal brainstorming session (11/04/2025) plus a first-pass scoring worksheet and operational playbook mappings. Goal: propose a compact, explainable health score used inside QBRs and renewal prep that highlights top risk drivers (not just a single opaque number). Keep it human-readable for CSMs and compatible with downstream analytics (SQL, dbt).

High-level requirements (what we need from the model):
- Interpretable: each score component maps to a tangible signal and recommended action.
- Lightweight: can be computed from event stream + billing + support tables daily.
- Tunable: weights easy to change per customer segment (SMB / Mid / Enterprise).
- Actionable thresholds: red/yellow/green with recommended playbook steps.
- Handles missing data: fallbacks and imputation notes.

Primary signal groups (candidate list & quick defs):
1) Usage and adoption (45% baseline weight)
   - active-users-weekly: unique users with any API call in last 7 days
   - routes-used: number of distinct Redwood endpoints the customer calls (chat/generate/embeddings)
   - peak-concurrency: 95th pc
…[truncated]
```

#### #3 `dsid_d78b80dce604425ebb87797c5835f01d`

```
Field operational runway and safety windows for private deployments

Summary
-------
This document defines the operational "runway" (how much maintenance/upgrade activity a private deployment can safely absorb) and the safety window model used by Redwood field engineers and customer operators when performing upgrades, scheduled maintenance, or emergency changes in Private/VPC/on-prem deployments. It codifies threshold-based decision logic, a step-by-step maintenance procedure, required telemetry, and an explicit rollback decision matrix.

Scope
-----
- Applies to Redwood Private deployments (VPC and on-prem) that are in steady-state or candidate for minor/major upgrades.
- Focus areas: control plane updates, runtime (serving) upgrades, model swaps, KV cache migrations, host/firmware maintenance, network failover drills.
- Not in scope: initial provisioning, hardware replacement performed by vendor field engineering.

Goals and guarantees
--------------------
- Maintain customer-visible SLOs during maintenance where possible: 99.95% availability, p95 request latency < 250ms for small-sequence (<128 tokens) requests on Dedicated/VPC tiers.
- Define conservative safety windows that mi
…[truncated]
```

#### #4 `dsid_93a93dc4fe054f238d6c09ef8d558bd0`

```
Tenant Urgency Index for Model Deprecation: telemetry, thresholds, and migration playbook

Objective: define and deliver a per-tenant 'Urgency Index' that quantifies how urgently each customer should be migrated off a model that is being deprecated or degraded. The index will drive automated notifications, prioritized migration tickets, and prescriptive runbooks (auto-fallback, dedicated capacity offers, CSM outreach). Scope: hosted + dedicated customers; initial rollout for enterprise tenants (> $10k/month) with phased rollout to mid-market. Excludes on-prem private deployments for now (different upgrade cadence).
We have ad-hoc deprecation and fallback playbooks today. Sales/CS and Solutions teams repeatedly ask: who should we prioritize when a model variant is sunset or an external model has an availability shock? Current triage is manual and reactive; this ticket designs an objective telemetry-driven index so engineering, support, and GTM have a shared, measurable prioritization signal.
Use a signals-weighted score (0-100) rather than simple rule sets so we can rank large customer populations and tune weights per cohort. Prioritize signals that reflect both reliability (SLO bre
…[truncated]
```

#### #5 `dsid_3af6827a6dd54e7dbe9261d9a530aa17`

```
traffic-throttle-and-roll-forward-matrix-for-experiments

Goal: Define a prescriptive traffic throttling schedule and roll-forward decision matrix for A/B tests, canaries, and incremental feature rollouts that balances rapid iteration with customer safety. This ticket captures milestone definitions, metric gating rules, the automation hooks for rollback/roll-forward, and required dashboards and alerts. The output will be a deployable YAML matrix used by the rollout controller plus a short playbook for on-call/PM/Eng action in each gate state.
Current ad-hoc canaries vary across teams, causing inconsistent time-to-detection and uneven customer exposure. We need a standardized template that product teams can reuse for model/API changes and feature flags. The matrix should be compatible with console routing policies (region, tier), include quality and infra gates, and support both time-window and event-driven decisions.
Milestone 1: Define signal taxonomy and owners (quality, infra, business).
Milestone 2: Draft traffic throttling schedule (percent increments + duration windows).
Milestone 3: Implement automation hooks for the rollout controller and feature-flag service.
Milestone 4: 
…[truncated]
```

#### #6 `dsid_0c10879aaadf4314bec81aed9961477a`

```
Holistic Acceptance Matrix for Model Promotion

This page defines a single, reproducible acceptance matrix and workflow used by Redwood Inference to decide whether a candidate model (or model variant) may be promoted to staging and production. The matrix covers automated evals, human checks, performance/latency budgets, quantization acceptance, and regression-triage triggers. It is intended to reduce ambiguity in promotions and standardize cross-team expectations.
Provide a deterministic set of checks, metrics, and decision rules for onboarding new model versions across hosted, dedicated, and private deployments. The matrix balances quality, cost, and operational safety and ties results to rollout constraints and rollback criteria.
Applies to all model artifacts that will be served through Redwood API, Dedicated pools, or Private deployments. Includes open-source base models and any internal fine-tuned variants. Excludes short-lived experimental snapshots that are explicitly labeled "experimental" and not intended for promotion.
The acceptance matrix groups checks into five axes: 1) Functional quality (task-specific metrics & human eval), 2) Safety and policy (toxicity, PII leakage
…[truncated]
```

#### #7 `dsid_03353a3e32ba43c482e0efc6dff87a86`

```
Rollout Stoplight Decision Tree & Economic Sentinel

Purpose:\nThis doc defines a compact, operational stoplight decision tree for staged feature rollouts plus an 'Economic Sentinel' — a thin cost-monitoring layer that gates traffic expansion when unit economics deviate. Intention is to give on-call, product ops, and platform a single rubric (green/amber/red) tied to both SLOs and per-token cost impact.\n\nContext and why this is different:\n- We often gate on latency/errors only. That misses cost regressions (quantization changes, batch policy shifts, model swaps) that can double run costs unnoticed.\n- The stoplight combines reliability + cost + quality signals into a single pass/fail-ish decision tree so non-ML folks can make go/no-go calls during launches.\n\nQuick summary of the decision tree (high level):\n1) Green path: All primary SLOs within thresholds AND Economic sentinel below soft threshold -> expand to next stage.\n2) Amber path: Any single SLO near threshold OR economic sentinel between soft and hard threshold -> hold expansion, start mitigation playbook, notify engineering and product ops.\n3) Red path: Any SLO breach OR economic sentinel above hard threshold -> imm
…[truncated]
```

#### #8 `dsid_a6a4d42e97ce47aa9509e779f67a6463`

```
Adaptive Cohort Guardrails and Decision Flow for Optimize Eval Quality

This PRD defines an adaptive, hypothesis-driven evaluation contract for Redwood Optimize that: 1) assigns traffic-safe signals to cohorted prompt sets, 2) computes multi-signal regression scores with dynamic thresholds, and 3) maps those signals to automated and manual rollback actions. The goal is to reduce false positives that trigger unnecessary rollbacks while ensuring real regressions are caught quickly and acted on with clear playbooks for engineers and SREs. This work is specifically for the Optimize product: the eval harness and production canaries that gate model/quantization rollouts.
Customers using Optimize rely on automated recommendations (quantization, batching, model variants). We currently lack a unified eval contract that ties prompt cohorts, statistical tests, and actionability rules to a deterministic rollback flow. Recent outages (INC-2026-09) highlighted oscillations from over-sensitive single-signal thresholds which rolled back benign changes. This PRD aims to codify a stable multi-signal approach and explicit decision flow to avoid both missed regressions and noisy rollbacks.
Define coho
…[truncated]
```

#### #9 `dsid_3c00e57d05144023b526014bf5a01cb3`

```
Define tiered resilience metrics and automated deployment gates for inference services

Summary: This ticket captures a concrete, testable PRD for tiered SLA/SLOs and automated deployment gating for Redwood inference endpoints. Goal: provide deterministic acceptance criteria for model rollouts (hosted and dedicated) that balance latency, availability, and quality regressions while enabling automated canaries and rollbacks. The output will be a single canonical definition used by Console rollouts, CI pipelines, and runbooks.
In scope: (1) Define SLO targets for three workload tiers (internal dev, standard customer, enterprise isolation) covering p50/p95/p99 latency for text generation and embeddings, 99.9/99.95 uptime windows, and request-level error budgets. (2) Define automated gating rules for canary percentage ramps, rollback thresholds (latency, error rate, quality drift), and mandatory human approval gates. (3) Acceptance tests and observability signals required to mark a rollout as Passed/Failed. (4) Hand-off checklist for Console UI and rollout automation engineers.
Out of scope: per-model benchmarking methodology (handled by model-onboarding), pricing changes, deep infra re
…[truncated]
```

#### #10 `dsid_d208b7227aff40309d40cdadff67b65d`

```
Distribution Stability Eval and Response Playbook

Purpose:
This playbook describes Redwood's standardized process for evaluating distribution stability (inputs, embeddings, outputs) and the operational response for detected deviations. It is intended to connect evaluation harness outputs, production telemetry, and remediation actions so teams can act consistently across model types and deployment modes.

Audience:
- Applied ML engineers maintaining model quality
- SREs and platform engineers managing observability and alerts
- Owner teams performing model rollouts and post-deployment verification

High-level goals:
- Detect meaningful distribution changes with low false-positive rate
- Maintain model calibration within expected bounds for customer-facing metrics
- Provide automated safe mitigations and clear handoffs for human investigation

Core signals we monitor (defaults):
- Token-level PSI: alert if PSI > 0.25 over 24h window
- Embedding median cosine shift: alert if median shift > 0.08 over 1h window
- Token KL divergence: alert if KL > 0.5 on sampled prompts
- Scalar calibration gap: alert if absolute gap > 0.06 on labeled validation tasks
- Feedback-derived error rate: ale
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 30: `qst_0166::basic` · N=20000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`other`
- **LLM note:** The expected document ID is not present in the top-10 retrieved document IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty but do not address the procurement target date question, indicating a relevance issue. The hit flag is inconsistent with the ID membership, suggesting a pipeline discrepancy.

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Gold document(s)

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_573ca1fc195e450e85e3f10d1a068cf6`

```
HelmBridge Healthcare

Account background:
- Enterprise healthcare SaaS provider, strong on PHI workflows. Interested in on-prem/VPC option early (HIPAA concerns).
- Initial intro 2025-09-12 (AE: Priya). Demo delivered 2025-10-05 (SE: Marcus) — focus on low-latency clinical assistant and secure embeddings for document search.
- 2025-11-20 security kickoff w/ InfoSec (paperwork: NDA + data flow diagram). Requested SOC2 + HIPAA articulation and KMS/HSM details.
- POC (2025-12-18 -> 2026-01-08): small clinical assistant POC using hosted variant; we demonstrated latency and cost estimates. POC passed functional tests but security team required VPC endpoints + SIEM integration.
- Procurement review 2026-01-25: finance ran TCO vs hyperscaler-managed endpoints. Their pricing model (with committed AWS discounts) made AWS Bedrock managed endpoints ~25-30% cheaper operationally given no additional ops headcount.
- Final decision 2026-02-10: chose AWS native managed endpoints + PrivateLink for data in transit; quote from CTO: "We can't add a new ops surface right now — exec mandate is to consolidate on existing cloud services."
- Post-mortem notes: timeline slipped on private deployment timel
…[truncated]
```

#### #2 `dsid_7ebcb79ae27b49e2ade629edbf764551`

```
Silverbridge AI Security

Legal to finalize DPA response; schedule triage with procurement week of 12/9
DPA redlines on liability & indemnity
Vendor risk questionnaire overdue
Procurement budget freeze for Q4
No internal champion — legal wants product security writeup
08/15/2024 — Intro call (AE Morgan): discovery, use cases: customer support chatbot + account summarization + post-search reranking
08/22/2024 — Demo + throughput sizing (SE Priya): target p95 latency < 120ms for support chat; expected 120k user messages/mo; prefer model variants with quantized profiles
09/05/2024 — Security questionnaire submitted by Silverbridge (60+ Qs). They flagged data residency and KMS integration as blockers.
09/18/2024 — Legal review kickoff: Silverbridge legal requested our DPA + proposed changes. Primary asks: lower liability cap, tighter deletion SLA, audit rights clarification.
10/01/2024 — AE escalated to Product for a written note on KV cache retention and purge flow (sent 10/02).
10/21/2024 — 30m call (ff-2024-10-21-7890): Legal recapped redlines — indemnity and export control language not acceptable as-is. Procurement requested SOC2 Type II and recent pen test report.
11/08/2024 — Pri
…[truncated]
```

#### #3 `dsid_c7018f1cf17b4677a9368dda646702a8`

```
Galena ProcureWise, Inc.

Legal to confirm counterparty DPA changes and procurement to run final vendor onboarding check; schedule wrap-up call with CFO and Head of Procurement.
DPA redlines - customer insists on strict data residency and deletion clauses
MSA indemnity and liability cap disagreements (legal asking for lower caps)
Vendor onboarding requires independent pen-test report + 3rd-party attestation before PO
Internal champion (Head of ML) left in Jan — no clear replacement driving the project
2026-02-20 - Legal sent counterparty DPA with redlines (see drive link)
2026-01-28 - Procurement questionnaire submitted (security team requested SOC2 + pen-test)
2026-01-12 - POC demo (3-day) completed. Performance met SLA for 95th p50 latency; cost estimate provided
2025-12-10 - Intro call with AE + SE. Use case validated (RFP automation + vendor chat).
AE notes: procurement timeline dragging — buyer busy with budget planning.
SE note: POC ran on dedicated quantized model, latency OK; main objection is legal clauses.
"They want a vendor attestation and a DPA scoped to EU residency — procurement won't sign until verified", paraphrased from Head of Procurement.
Champion update: Head o
…[truncated]
```

#### #4 `dsid_03e8e7561d79413ebb487cb9926a1670`

```
Mantelbridge Support & Governance

2024-10-15 - Lead created via inbound whitepaper download (contact: emma.hale@mantelbridge.com). AE assigned: Ava Collins.
2024-10-23 - Intro call (Ava + Ravi). High-level need: automate 24/7 contact center for payments disputes + sensitive account queries. Emphasis on zero-data-exfil for PHI/PCI fields.
2024-10-23 - Fireflies ff_20241023_8472: 35m call. Quote from Dir. Support Ops: 'We cannot allow PHI to leave our VPC even in transient caches.'
2024-10-30 - Tech deep-dive with infra + security. SE notes: will require private control plane in VPC, KMS/HSM key wrapping, and immutable audit logs for tool-calls. POC scope -> 4-week sandbox in customer VPC using 1 pod, simulated spike test planned.
2024-11-01 - Security questionnaire received. Key asks: retention windows (30/90/365), audit log export formats, SSO SAML flows, and SOC2 scope. Legal asked for model weights handling statement.
2024-11-04 - Pricing deck shared (drive:/decks/mantelbridge-pricing-proposal-v2.pdf). Procurement flagged ARR band and preferred committed throughput discount.
2024-11-05 - Follow-up call (ff_20241105_1291). Agreed POC success criteria: (1) Agent assist latency p50
…[truncated]
```

#### #5 `dsid_26958e32ed0d4b7080c9e42bc34b1e2e`

```
Praxis MedTech Regulatory Solutions

Account summary:
- Multi-hospital MedTech provider: FDA-regulated device telemetry + clinical decision support. They cannot tolerate cloud-hosted PHI processing.
- Primary ask: Private deployment in EU region with on-prem, air-gapped variant for select customer sites. KMS must integrate with on-prem HSMs (Thales/Utimaco) or FIPS 140-2/3 equivalent.
- Security: heavy. ISO27001 + SOC2 required; need sample audit logs and retention policy (minimum 7 years for some records).
- Network: strict egress restrictions. We discussed a pull-only update mechanism for model binaries and signed artifacts; customer asked for signed artifact verification and offline install playbook.
- Performance: inference for imaging pipeline targets 150 concurrent sessions, 50ms token latency not required but per-image end-to-end < 250ms target for lightweight models, some large batch offline jobs ok.
- Cost sensitivity: willing to commit to Dedicated capacity for baseline throughput; air-gapped variant priced as separate on-prem license + support.
- Quote from CISO: "We will only accept a deployment model that can be fully decommissioned and audited; no persistent outbound 
…[truncated]
```

#### #6 `dsid_da8b915c58a74bce8ccb88cd9b05d346`

```
Beacon Health Payments

Account summary:
- Vertical: payments for ambulatory clinics + patient billing reconciliation. Needs both PCI scope (card on file) and HIPAA PHI handling (EOBs, claims notes).
- Primary contact: VP Product Maya Saunders; Procurement lead: Sean Riley (payments ops). CTO (former) left 2026-01-22 -> hiring freeze in infra team.
Timeline / recent activity:
- 2025-11-12: inbound demo request via website; AE assigned (Ethan).
- 2025-11-18: intro call; mapped high-level requirements (throughput: 500 TPS ingest, latency p95 < 200ms for short prompts).
- 2025-12-03: scope call with SE (Priya) — requested POC for anonymized claims summarization + reconciliation embeddings.
- 2026-01-10: POC kickoff (fireflies ff-20260110-83bcd). We proposed private deployment w/ dedicated HSM and VPC endpoints.
- 2026-01-25: Security questionnaire submitted; payment processor (merchant acquirer) elevated PCI requirement to co-scope level.
- 2026-02-14: Security review with payments/QSA present (ff-20260214-91a2f). QSA concluded hosted shared-tenant API cannot be PCI-scoped without third-party attestation; recommended on-prem or fully isolated HSM-backed service.
- 2026-02-20: Legal re
…[truncated]
```

#### #7 `dsid_4dc77de6649d4e0799648a18290d96b5`

```
BlueCrest Secure Support

Account background: BlueCrest runs payments reconciliation + telehealth billing support for a set of regional clinics and a payments gateway. Heavy PCI + PHI scope; central support org handles escalations and chargeback disputes.

Call highlights (2026-01-15):
- CISO (R. Gomez): "cannot leave payment PANs or PHI in external storage; need KMS + HSM, full audit trail to SIEM."
- Head of Support Ops (L. Chen): looking for agent assist to reduce AHT by 20%, live suggestion latency <150ms, and summarization that produces 3-4 sentence TL;DRs with configurable retention windows.
- Platform Lead (M. Patel): asks for VPC deployment, private control plane, and the ability to pin model versions + automatic fallbacks during capacity events.

Technical constraints / must-haves:
- VPC/private deployment mandatory for POC.
- SAML SSO + SCIM provisioning integrated into Okta.
- Audit logging forwarded to Splunk/SIEM with 90-day hot retention, 7-year cold retention for payment dispute records.
- KMS/HSM integration for envelope encryption; customer will not allow Redwood-managed keys without HSM-backed KMS.
- Tokenization or redaction pipeline for PAN/PHI before model expo
…[truncated]
```

#### #8 `dsid_25d5245f41e349f0ba6c5af9519b9d79`

```
Summit Clinical Research Inc

Account snapshot: Summit Clinical Research (clinical CRO focused on oncology trials). Wants secure patient-facing assistant + automated clinical note summarization.

History / context:
- Initial discovery Sep 2025: strong interest in private deployment for PHI handling. AE Jordan + SE Priya demoed dedicated/private options (Nov).
- Security questionnaire submitted 2025-11-20; follow-ups Jan 2026. Security team escalated to compliance board.
- Jan 22 call (ff_2026-01-22_0a9s4): CISO said: "We need formal HIPAA attestation + on-prem option + audit chains; cannot accept hosted API without legal sign-off."
- Procurement timeline slipped due to Q1 budget freeze. Internal champion (Dr. Alonso) moved teams Feb 2026.
- Final decision: internal compliance board declined Redwood private package because engineering wanted Epic-integrated in-house deploy (cost-neutral with existing contracts).

Notes from SE: POC completed (anonymized note pipelines), performance met latency targets (75ms median for short summaries), cost model acceptable within committed ARR but legal required additional contractual clauses re: BAAs and HSM-backed keys.

CRM shorthand / follow-up
…[truncated]
```

#### #9 `dsid_5957ce1d094641c9aea7cf9011ed7ef4`

```
Zephyr Data Systems

Summary: Enterprise procurement for Dedicated capacity. Heavy security & legal gating. Primary contact is CTO (R. Alvarez) + CISO (K. Monroe).\n\nHighlights / asks: \n- Workloads: customer intends to route production chat + reranking + embeddings for fraud scoring (real-time).\n- Latency targets: 99th pctl chat < 150ms for 128-token responses; P50 < 40ms.\n- Throughput: baseline 100 concurrent chat sessions, burst to 250; goal is predictable tail latencies under reserved capacity.\n- Reserved GPU plan being discussed: initial commit 8x A100-80GB equivalent (dedicated pool), optional scale to 16x after Q2. Finance wants step-up pricing and cancellation mechanics.\n- SLA asks: 99.95% uptime, clear service credit table, ability to reserve capacity with guaranteed throughput per-GPU. They want quantifiable throughput guarantees (tokens/sec per GPU) and escalation path if capacity not met.\n- Procurement/legal: redlines on DPA around data residency, indemnity cap requested at 12 months of fees or $5M, whichever lower; they pushed to include security breach notification timelines (72 hrs), and a one-way audit right for SOC2 scope.\n- Insurance: procurement requesting
…[truncated]
```

#### #10 `dsid_de174c9811834eff9929fd6d4efb3d30`

```
HelixBridge Healthtech

Overview: enterprise healthtech company building clinician-facing search and summarization across EHR notes. Heavy emphasis on PHI handling, audit trail and data residency.

Timeline / recent activity:
- 2025-11-18: Intro call (AE Maya + SE Jared) — interest in embeddings-based clinical search; target: 200ms median latency, 10 qps sustained for search. Fireflies id ff_2025-11-18_helixbridge_intro.
- 2025-12-03: POC kickoff — ingest pipeline for 50k patient documents, testing Redwood hosted private VPC. Fireflies id ff_2025-12-03_poc_kickoff.
- 2026-01-22: Security deep-dive with InfoSec (requested SOC2 Type II, ISO artifacts, pen test summary). Fireflies id ff_2026-01-22_security_review.
- 2026-01-25: Shared Redwood security pack + DPA template (Gmail thread thread-CA+security-qna-20260125).
- 2026-02-03: HelixBridge legal returned heavily redlined MSA + DPA: unlimited liability clause, data residency clause requiring EU-only for specific flows, 90-day breach notification tightened to 24 hours. Procurement asks for vendor audit and supplier attestation.
- 2026-02-12: Redwood SE provided technical responses and proposed mitigation (encryption at rest with KMS
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 31: `qst_0166::basic` · N=25000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are generally on-topic regarding procurement and timelines but do not specifically address the procurement target date after the streaming model benchmark and security review. The failure mode is a lexical mismatch as the retrieved documents do not match the specific content of the expected document. The chunk quality is adequate but not directly relevant to the question.

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Gold document(s)

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_a110cebd6e8844afbb800d73e451bf55`

```
Request to pause trial countdown while procurement completes

From: Olivia Grant <olivia.grant@clearpathhealth.com>
To: Hannah Schmitt <hannah_schmitt@redwood.com>
Date: Sat, 15 May 2027 09:02:00 -0700
Subject: Re: Trial access for ClearPath - procurement update

Hi Hannah,

Quick update from our side — procurement is still verifying the vendor onboarding docs and they pushed our PO approval out further than expected. The team is concerned about the trial countdown expiring before we have an approved PO. Can Redwood pause or extend the trial window while procurement finishes the checks?

I can loop in procurement if you need their ETA, but right now we expect resolution by end of next week (target 5/24).

Apologies for the back-and-forth — Olivia
Senior Product Manager
ClearPath Health

Attachment: ClearPath-PO-Note.txt (text)

From: Hannah Schmitt <hannah_schmitt@redwood.com>
To: Olivia Grant <olivia.grant@clearpathhealth.com>
Cc: Ben Carter <ben_carter@redwood.com>, Marissa Cole <marissa_cole@redwood.com>
Date: Sat, 15 May 2027 10:15:00 -07:00
Subject: Re: Trial access for ClearPath - procurement update

Hi Olivia — thanks for the heads up and for the ETA.

We don’t want the demo
…[truncated]
```

#### #2 `dsid_03a70a43e57c4895b63e456c7e836890`

```
MAP: Alder Health — success criteria, exit gates, and procurement checkpoints

From: Rafael Mendes <rafael.mendes@redwood.ai>
To: Claire Zhang <claire.zhang@alderhealth.com>
Cc: laura.bennett@redwood.ai, marcus.lin@redwood.ai
Date: Wed, 14 Jul 2027 09:12:00 -0700
Subject: MAP: Alder Health — success criteria, exit gates, and procurement checkpoints

Claire — great to meet last week. Following up with a draft mutual action plan so we can align on what ‚success’ looks like for Alder’s evaluation and what procurement needs to unblock signature. High level: 6-week technical evaluation (pilot) + 8-week measured production ramp. Key asks below — please confirm/annotate.

Summary of primary acceptance gates (draft):
- Gate 1 (Week 2): Integration & data sanity — live API calls to non-prod dataset, no PII exfiltration, response rate >= 95% for sample set.
- Gate 2 (Week 4): Latency & throughput — 95th percentile latency <= 280ms for 512-token requests under 10rps baseline; sustained handling of 30rps burst for 5 minutes.
- Gate 3 (Week 6): Quality & concordance — accuracy/concordance >= 88% on the clinical extraction prompt set (shared).
- Gate 4 (Onboarding signoff): Operational requireme
…[truncated]
```

#### #3 `dsid_4fb433d5bc984ee4b7f8a0815bb693b2`

```
Mutual action preflight: capacity & lead times — MAP for Dedicated/Private

From: Naomi Feldman <naomi_feldman@redwood.com>
To: Kat Greene <k.greene@helixhealth.com>
Cc: Marissa Cole <marissa_cole@redwood.com>, Ben Carter <ben_carter@redwood.com>
Date: 2027-05-20T10:12:00-07:00
Subject: Mutual action preflight: capacity & lead times — MAP for Dedicated/Private

Kat — following our call this morning, attaching a short preflight so we can lock the MAP items related to capacity reservation and close timeline. High level asks: 

- Confirm target production start date (you mentioned early Q4).
- Procurement / PO cadence and expected sign date from your side.
- Desired GPU pool sizing (p95 tokens/day) and acceptable latency SLOs.
- Whether this will be Dedicated (Redwood-managed GPU pool) or Private (VPC/on-prem) for the initial rollout.

Our constraints to call out up front: Dedicated lead time for H100 tranches is ~8–12 weeks from commitment (depends on region); Private on-prem/VPC installs add an installation window of ~4–6 weeks plus customer infra validation. For MAP planning we usually include a 2-week staging acceptance window and a 3-week buffer for any rework discovered during e
…[truncated]
```

#### #4 `dsid_8bca7188b1ab4065870d0d836f574a44`

```
Re: MAP cost probe — token economics & batching/caching assumptions

From: Vivek Kulkarni <vivek@redwood.com>
To: Jordan Hayes <jordan.hayes@stratoshealth.com>, Neha Kapoor <neha@redwood.com>, Ben Carter <ben@redwood.com>
Cc: procurement@stratoshealth.com
Date: Sun, 22 Aug 2027 09:12:00 -0700
Subject: MAP kickoff — baseline cost assumptions (tokens/$, caching/batching)

Jordan — thanks for the quick sync earlier. As we discussed, attaching a focused draft that isolates the unit economics assumptions we'll need to lock in during the MAP so we can sign off on POC scope and runway. Key asks up front:
- Can you share a short representative sample of typical request length and the percent of calls that hit a short-context path (<128 tokens)? (we've attached token-profile.csv for you to populate)
- Confirm acceptable latency SLO during the POC (our default target is p95 < 400ms for single-turn generation)
- Procurement: any constraints on retention/telemetry we should bake into the POC contract?

High level notes from our side (see MAP-draft-v2.pdf):
- Baseline token price: we model $0.0018 per 1k input+output tokens for the selected open model variant (quantized). This is preliminary an
…[truncated]
```

#### #5 `dsid_6e085f20a0ac448e882e94b0d9dd8d7c`

```
MAP kickoff: draft milestones, who owns what, and target close options

From: Irene Choi <irene.choi@redwood.com>
To: Aisha Thompson <aisha.thompson@helixhealth.com>
Cc: Karthik Iyer <karthik.iyer@redwood.com>, Marissa Cole <marissa.cole@redwood.com>
Date: Sun, 04 Apr 2027 15:12:00 -0700
Subject: MAP draft + timeline options & stakeholder confirmation (post-discovery)

Hi Aisha — great to meet earlier. Thanks for walking us through the Helix Health platform and the key constraints (data residency + low-latency inference in your West region). Per our call, attaching an initial Mutual Action Plan (MAP) draft and two timeline options so we can align on expectations and owners before a kickoff.

Attachment: 2027-04-04_MAP_Draft_v1.xlsx (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

Quick recap from discovery:
- Primary objective: pilot Redwood inference for on-prem patient summary generation (throughput target ~150 req/min, median p95 latency < 350ms).
- Must remain within Helix VPC for PHI; SOC 2 evidence required.
- Decision stakeholders: Security, IT Ops, Procurement, and Product.

Proposed MAP highlights (see attached for full table):
1) Aggressive path (Optio
…[truncated]
```

#### #6 `dsid_b3decda0465142bf8bc4b4cc5bb933ae`

```
Sprint gates & purchase flow: HealthCorps MAP + evaluation plan

From: Maya Singh <maya@healthcorps.com>
To: Evelyn Hart <evelyn_hart@redwood.ai>, Marcus Lin <marcus_lin@redwood.ai>
Cc: Procurement Team <procurement@healthcorps.com>
Date: Tue, 25 Aug 2026 09:12:00 -0700
Subject: Sprint gates & evaluation plan for Redwood POC

Hi Evelyn / Marcus,

Thanks again for the demo last week. Procurement asked me to put together the high-level evaluation plan and the gating checkpoints we need before we can route to legal/finance. I want to make sure we have a clean mutual action plan (MAP) so the internal review doesn't stall. Quick context: HealthCorps is running a 6-week POC with a small cohort of clinicians; primary concerns are data residency, SOC 2 evidence, and a clear acceptance test for model responses on sensitive prompts.

Initial asks from procurement/legal:
- Proposed MSA + DPA timeline (who needs to sign and when)
- SOC 2 / pen-test evidence and KMS approach
- Order form / purchase flow and expected cycle (PO vs corporate card)
- A short evaluation checklist we can attach to our SOW (success = pass X/Y/Z)

Can you share a draft MAP/sequence you recommend and the earliest dates 
…[truncated]
```

#### #7 `dsid_c1a07408bf3c472da41ce5ed8df44c09`

```
Vendor security questionnaire: SIG vs CAIQ — clarifying asks

From: Rachel Kim <rachel.kim@redwoodinference.com>
To: Claire Evans <claire.evans@medisys.health>, Tom Alvarez <tom.alvarez@medisys.health>
Cc: Karthik Iyer <karthik.iyer@redwoodinference.com>, Ben Carter <ben.carter@redwoodinference.com>
Date: Wed, 17 Jun 2026 15:12:00 -0700
Subject: Vendor security questionnaire: SIG vs CAIQ — clarifying asks

Hi Claire / Tom — thanks again for a productive call earlier. Quick recap and a few clarifying questions so we can move the security intake forward: 

Recap (from our side)
- You want Redwood to start the vendor security intake to unblock procurement and security review.
- Primary concerns: HIPAA scope (PHI), SOC 2 evidence, and data residency (US).
- Procurement will need an estimated timeline and a draft BAA.

Clarifying questions / asks
1) SOC 2 status: you mentioned an audit is in flight — can you confirm whether it will be Type II and the expected completion quarter? If you have an interim report / readiness assessment, that helps speed the review.
2) Questionnaire type: would you prefer SIG (full CAIQ-style profile) or a shorter CAIQ-only prefill? We can initiate a SIG and 
…[truncated]
```

#### #8 `dsid_e329f4afaa124f53be372634eb7ab9cb`

```
PHI boundaries & hosting paths — post-call summary + next steps

From: Connor O'Reilly <connor.obrien@redwood.ai>
To: Nina Sethi <nina.sethi@cardiomed.com>, Alex Ruiz <alex.ruiz@cardiomed.com>
Cc: Marissa Cole <marissa.cole@redwood.ai>, Laura Bennett <laura.bennett@redwood.ai>
Date: Mon, 02 Nov 2026 15:12:00 -0800
Subject: PHI boundaries & hosting paths — post-call summary + next steps

Hi Nina / Alex —

Great to meet you both on today’s discovery call. Quick recap of the security/compliance items we covered and the concrete next steps so we stay aligned: 

1) PHI handling boundary we discussed
   - CardioMed confirmed the current use-case will send patient identifiers + clinical notes into inference requests for triage predictions. This is PHI in scope.

2) BAA availability and timing
   - Redwood has a standard BAA template and can sign for hosted (Redwood API), Dedicated (reserved GPU pools), and Private (VPC / on-prem) deployments. We noted you prefer a hosted-first eval but need the BAA before any PHI is processed.

3) Eligible deployment modes for PHI
   - Hosted API (Redwood managed): Supported with BAA + customer consent; limited region availability (US regions fully suppor
…[truncated]
```

#### #9 `dsid_bf0a48f2f2564bc78dbae6b00ce0fcef`

```
Draft MAP — SDK streaming & toolcall integration: owners, milestones, risks

From: Priyom Das <priyom.das@redwood.ai>\nTo: Alyssa Chen <alyssa.chen@healthaxis.ai>, Michael Torres <michael.torres@healthaxis.ai>\nCc: Neha Kapoor <neha.kapoor@redwood.ai>, Ben Carter <ben.carter@redwood.ai>\nDate: Thu, 30 Jul 2026 17:05:00 -0700\nSubject: Draft MAP & integration checklist (post-call recap)\n\nHi Alyssa / Michael — thanks again for the call earlier today. Quick recap and next steps so we have alignment on the MAP milestone that covers the SDK/streaming/tool-calling work: \n\nSummary (what we discussed)\n- Primary integration path: HealthAxis will embed Redwood SDK for request/response generation, and enable streaming for live transcription->assist flows.\n- Tool calling: HealthAxis wants structured outputs and deterministic tool calls for order-of-operations in their clinician assistant.\n- Success criteria: proof-of-concept with streaming + function/tool calls, structured-output schema validation, and an internal perf target of p95 latency < 350ms for single-request streaming fragments.\n\nProposed MAP milestone items (draft) — see attached MAP_draft_v1.xlsx for table view:\n1) SDK int
…[truncated]
```

#### #10 `dsid_9701a2e5d4a54d74acbd973f91ee67f3`

```
Procurement MAP & sequencing for BlueBridge pilot

From: Anika Rao <anika@bluebridgehealth.com>
To: Stephanie Nguyen <stephanie@redwood.com>
Date: 2026-07-08T08:14:00-07:00
Subject: Procurement MAP & contract sequencing for BlueBridge pilot

Hi Stephanie,

Thanks for the demo last week — BlueBridge is excited to move into a timeboxed pilot for the clinical triage assistant. Procurement/legal asked me to pull together the evaluation plan and a mutual action plan so we can map dependencies to signing. High level asks from our side:

- We need a MAP that lays out evaluation milestones, evidence for security/compliance, and the contract sequencing (MSA/DPA/order form).
- Procurement would like clear handoffs and a target signature window; our internal target is pilot start week of Aug 30 but we can be flexible if legal needs more time.
- Please include acceptance criteria for the pilot and what artifacts will constitute signoff.

I attached the RFP their team shared (BlueBridge_RFP.pdf) — it has some specific data residency/retention questions that legal will flag. Can you send a MAP and an initial sequencing proposal by EOB Friday? Also cc procurement@bluebridgehealth.com on any contr
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 32: `qst_0166::basic` · N=50000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty and relevant to procurement and legal processes but do not address the specific question about ClearPath Health's procurement target date. The failure is due to lexical mismatch, as the retrieved documents do not contain the specific information sought. The hit flag inconsistency is a critical issue.

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Gold document(s)

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_8412b7b7ea7d4ba28d0662190d169ff7`

```
Oxbow Health Systems

Late-stage enterprise healthcare opportunity stalled in procurement. Primary blocker is compliance: Oxbow requires an executed HIPAA BAA, SOC2 evidence, and independent penetration testing before approving a private/on-prem deployment. Internal champion has left and procurement has a temporary budget freeze. Competitor SecureServe AI is being evaluated because they presented an existing BAA and healthcare references. Next steps focus on legal (BAA) and security (pen-test) items; low confidence close this quarter unless legal/sales can fast-track compliance materials.
Follow up after security committee decision; get legal on BAA + pen-test schedule
HIPAA BAA not signed
Security team requires additional pen-test and SOC2 evidence
No internal champion after product lead left
Procurement budget freeze for Q1
2025-09-10 - Lead created via webinar sign-up (product team)
2025-10-02 - Intro call with AE (Priya); noted HIPAA workload; interested in on-prem/private model
2025-11-12 - Technical kickoff with SE (Marco) and platform team; reviewed architecture and data flow; Fireflies: ff_2025-11-12_oxbow_kickoff
2025-12-08 - Security questionnaire submitted; security foll
…[truncated]
```

#### #2 `dsid_97997d6c05ea451fb63afba925baf9f1`

```
Procurotics Onboarding

STATUS: Stalled in procurement/legal. Short summary: strong product fit for contract summarization and procurement-assistant workflows; POC technically successful (latency and throughput targets met on dedicated). Primary failure mode: legal/procurement timeline. Details:\n\n- Procurement quote: interested in Dedicated or Private deployment. Cost sensitivity around steady-state token volumes; asked for detailed unit-cost model (see drive deck).\n- Security: completed SIG-lite but Infosec flagged two items: (1) indemnity/limitation of liability in DPA, (2) vendor onboarding asks for SOC2 + ISO evidence and KMS integration. They requested data residency assurances for EU customers.\n- Legal: sent DPA and MSA redlines 2026-02-07. Their GC wants to cap liability and remove some vendor-hosted telemetry clauses. Our Legal provided counters on 2026-03-01. Customer procurement has moved to a multi-vendor procurement window and placed Redwood in vendor onboarding queue (VENDOR-2041).\n- Internal champion: originally VP of Procurement (Elena Voss) was driving; has shifted priorities and is on extended leave; no clear exec sponsor now. Sales contact has been trying to 
…[truncated]
```

#### #3 `dsid_573ca1fc195e450e85e3f10d1a068cf6`

```
HelmBridge Healthcare

Account background:
- Enterprise healthcare SaaS provider, strong on PHI workflows. Interested in on-prem/VPC option early (HIPAA concerns).
- Initial intro 2025-09-12 (AE: Priya). Demo delivered 2025-10-05 (SE: Marcus) — focus on low-latency clinical assistant and secure embeddings for document search.
- 2025-11-20 security kickoff w/ InfoSec (paperwork: NDA + data flow diagram). Requested SOC2 + HIPAA articulation and KMS/HSM details.
- POC (2025-12-18 -> 2026-01-08): small clinical assistant POC using hosted variant; we demonstrated latency and cost estimates. POC passed functional tests but security team required VPC endpoints + SIEM integration.
- Procurement review 2026-01-25: finance ran TCO vs hyperscaler-managed endpoints. Their pricing model (with committed AWS discounts) made AWS Bedrock managed endpoints ~25-30% cheaper operationally given no additional ops headcount.
- Final decision 2026-02-10: chose AWS native managed endpoints + PrivateLink for data in transit; quote from CTO: "We can't add a new ops surface right now — exec mandate is to consolidate on existing cloud services."
- Post-mortem notes: timeline slipped on private deployment timel
…[truncated]
```

#### #4 `dsid_7ebcb79ae27b49e2ade629edbf764551`

```
Silverbridge AI Security

Legal to finalize DPA response; schedule triage with procurement week of 12/9
DPA redlines on liability & indemnity
Vendor risk questionnaire overdue
Procurement budget freeze for Q4
No internal champion — legal wants product security writeup
08/15/2024 — Intro call (AE Morgan): discovery, use cases: customer support chatbot + account summarization + post-search reranking
08/22/2024 — Demo + throughput sizing (SE Priya): target p95 latency < 120ms for support chat; expected 120k user messages/mo; prefer model variants with quantized profiles
09/05/2024 — Security questionnaire submitted by Silverbridge (60+ Qs). They flagged data residency and KMS integration as blockers.
09/18/2024 — Legal review kickoff: Silverbridge legal requested our DPA + proposed changes. Primary asks: lower liability cap, tighter deletion SLA, audit rights clarification.
10/01/2024 — AE escalated to Product for a written note on KV cache retention and purge flow (sent 10/02).
10/21/2024 — 30m call (ff-2024-10-21-7890): Legal recapped redlines — indemnity and export control language not acceptable as-is. Procurement requested SOC2 Type II and recent pen test report.
11/08/2024 — Pri
…[truncated]
```

#### #5 `dsid_653df4a231424a6bb4e6b55e03df7dd1`

```
Granite Harbor Logistics

Legal to confirm DPA redlines; procurement to open vendor portal ticket
DPA redlines around indemnity and data residency
Vendor onboarding form stalled in procurement portal
No signed MSA; legal insists on HSM/KMS clause and 24h breach-notification
Finance has procurement spend on hold pending Q2 budget review
2025-10-02 inbound SDR demo request; focus on cost predictability for peak season.
2025-10-20 initial AE intro (Arielle) — demo of Dedicated and routing; asked about Canadian data residency and private control plane.
2025-11-14 discovery call w/ CTO + Legal: CTO wants KV caching + reranking for TAT; Legal flagged indemnity and breach-notification SLA.
2025-12-05 POC kick-off: 2-week pilot on Dedicated cluster; SE Diego configured model routing, observed ~85ms p95 on sample queries.
2025-12-22 security questionnaire submitted (vendor portal ID VEND-559). Legal returned DPA with heavy redlines (indemnity cap request, remove subprocessor clause).
2026-01-18 follow-up (Fireflies ff_2026-01-18_poc-handoff); procurement asked for vendor onboarding checklist; portal still shows 'pending' in status.
2026-01-29 AE escalated to Solutions; customer legal will n
…[truncated]
```

#### #6 `dsid_70a3499794194af0a1a68476f01a4ea6`

```
MedPay Bridge LLC

Account summary: med-pay fintech that routes payments for clinics + patient billing; stores limited PHI and card tokens. Primary ask: private VPC deployment w/ KMS integration, robust audit logging, and residency in us-east. Compliance mapping request received — wants explicit controls and gaps for SOC 2, ISO 27001, HIPAA (BAA), and PCI SAQ scope.

Meeting notes (shorthand):
- CISO (M. Alvarez): 'cannot accept multi-tenant token storage unless we have HSM-backed keys and clear audit trail.'
- CTO (R. Chen): heavy cost sensitivity; prefers dedicated reserved capacity for 99th percentile p95 latency <150ms for chat assistants and <50ms per-embedding request for batch jobs.
- Legal: BAA required; clarify data flows for cardholder PANs (they currently tokenize upstream but want confirmation no PANs persist in our logs).

Compliance mapping highlights (SE provided mapping - condensed):
- SOC 2: Redwood Private + Dedicated: infrastructure segregation, SSO/SAML, role-based access, audit logging retention (configurable). Need formal SOC 2 report copy + control mappings for CC6/CC7 (encryption & change management).
- ISO 27001: suggest documentation packet: ISMS overview,
…[truncated]
```

#### #7 `dsid_d8ca6f03b07342d2b58f37aa3e7a8ae7`

```
Mariner Regulatory HealthData

Summary: Clinical-research data platform for multi-site trials. Want LLM features for investigator portal (chat), de-identification helpers, and embedding-based chart search.
Kicker: Legal & compliance require a signed BAA + evidence of audit logging and US data residency before any PII/PHI is processed. Current timeline from legal: must have BAA in place by 2026-01-31 — missed.
Timeline (high level):
- 2025-08-12: Inbound from webinar signup (whitepaper on secure inference). AE Sofia assigned.
- 2025-09-01: Discovery call w/ CTO (Anika Rao) and Head of Compliance (Mark Feld). Confirmed need for HIPAA + residency + KMS integration.
- 2025-09-15: Product demo focused on hosted_api streaming chat + embeddings. Recorded (ff_2025-09-15_9834).
- 2025-09-30: Security questionnaire submitted (50+ items). SE Marcus responded with SOC2 docs and network diagrams.
- 2025-11-03: Deep-dive with Security (Fireflies ff_2025-11-03_10422). Legal reiterated requirement: BAA mandatory; hosted offering acceptable only if BAA executed and data residency controls demonstrated.
- 2025-12-10: Customer requested private/VPC timeline and ballpark on-prem costs. Engineering est
…[truncated]
```

#### #8 `dsid_c7018f1cf17b4677a9368dda646702a8`

```
Galena ProcureWise, Inc.

Legal to confirm counterparty DPA changes and procurement to run final vendor onboarding check; schedule wrap-up call with CFO and Head of Procurement.
DPA redlines - customer insists on strict data residency and deletion clauses
MSA indemnity and liability cap disagreements (legal asking for lower caps)
Vendor onboarding requires independent pen-test report + 3rd-party attestation before PO
Internal champion (Head of ML) left in Jan — no clear replacement driving the project
2026-02-20 - Legal sent counterparty DPA with redlines (see drive link)
2026-01-28 - Procurement questionnaire submitted (security team requested SOC2 + pen-test)
2026-01-12 - POC demo (3-day) completed. Performance met SLA for 95th p50 latency; cost estimate provided
2025-12-10 - Intro call with AE + SE. Use case validated (RFP automation + vendor chat).
AE notes: procurement timeline dragging — buyer busy with budget planning.
SE note: POC ran on dedicated quantized model, latency OK; main objection is legal clauses.
"They want a vendor attestation and a DPA scoped to EU residency — procurement won't sign until verified", paraphrased from Head of Procurement.
Champion update: Head o
…[truncated]
```

#### #9 `dsid_03e8e7561d79413ebb487cb9926a1670`

```
Mantelbridge Support & Governance

2024-10-15 - Lead created via inbound whitepaper download (contact: emma.hale@mantelbridge.com). AE assigned: Ava Collins.
2024-10-23 - Intro call (Ava + Ravi). High-level need: automate 24/7 contact center for payments disputes + sensitive account queries. Emphasis on zero-data-exfil for PHI/PCI fields.
2024-10-23 - Fireflies ff_20241023_8472: 35m call. Quote from Dir. Support Ops: 'We cannot allow PHI to leave our VPC even in transient caches.'
2024-10-30 - Tech deep-dive with infra + security. SE notes: will require private control plane in VPC, KMS/HSM key wrapping, and immutable audit logs for tool-calls. POC scope -> 4-week sandbox in customer VPC using 1 pod, simulated spike test planned.
2024-11-01 - Security questionnaire received. Key asks: retention windows (30/90/365), audit log export formats, SSO SAML flows, and SOC2 scope. Legal asked for model weights handling statement.
2024-11-04 - Pricing deck shared (drive:/decks/mantelbridge-pricing-proposal-v2.pdf). Procurement flagged ARR band and preferred committed throughput discount.
2024-11-05 - Follow-up call (ff_20241105_1291). Agreed POC success criteria: (1) Agent assist latency p50
…[truncated]
```

#### #10 `dsid_a26be99609ac4721b7fe14ef477a27f7`

```
Cedarbridge Health Systems

2026-02-20: Initial inbound via partner referral (security champion: A. Martinez)
2026-02-25: Intro demo (hosted API) — PI team interested in private due to PHI
2026-02-28: Tech deep-dive with infra and InfoSec (Fireflies ff_20260228_991)
2026-03-02: Compliance mapping workshop (SOC2/ISO/HIPAA) — action items captured (ff_20260302_784)
2026-03-08: Submitted draft network diagram and onboarding checklist; legal requested BAA template
Planned 2026-03-17: Security review meeting with InfoSec + procurement to discuss KMS HSM options
Deliver technical appendix for KMS/HSM integration and updated network diagram; schedule security review with InfoSec on 2026-03-17
Legal: BAA sign-off pending
Network: VPC peering window limited (change freeze week of 3/22)
Proof-of-concept: KMS HSM E2E test required
Decision driver: must avoid any vendor-managed multi-tenant storage of PHI; VPC private plane preferred.
Primary requirement: VPC private deployment with customer-managed KMS (HSM) or KMS BRIDGE to meet encryption-key separation.
InfoSec quote: 'Need explicit proof of audit logging to S3 for 365 days and immutable retention for security-relevant events.'
Compliance 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 33: `qst_0166::basic` · N=75000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, indicating a lexical mismatch. The retrieved chunks are relevant to procurement and agreements but do not directly address the specific procurement target date for ClearPath Health. The gold chunk is on-topic but lacks specific date information. The hit flag is consistent with the ID membership check.

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Gold document(s)

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_d36ef5e873bc4b719948073663178630`

```
Procurement sequencing + condensed MAP & evaluation milestones

From: Patrick O'Neill <patrick.oneill@clearviewhealth.com>
To: Priya Natarajan <priya.natarajan@redwood.ai>
Date: Sun, 18 Apr 2027 09:12:00 -0700
Subject: Procurement kickoff — sequencing & evaluation window

Hi Priya,

Thanks for taking this on. Our procurement team asked me to capture what they need so we can lock a firm close date. High level:

- We need a clear sequencing plan: who signs what and in what order (MSA, DPA, Order Form).
- Evaluation period: 10 business days with an agreed-off test plan and SLA checks.
- Security artifacts: current SOC 2 report, encryption-in-transit confirmation, subprocessors list for the DPA.
- PO timing: procurement prefers an executed MSA + DPA before issuing PO; order form can be routed after.

Target close window: early May (aiming for week of May 3). If Redwood can provide SOC2 evidence and the DPA template by EOD Tue 4/19, we can accelerate.

Attached is our procurement checklist (procurement_requirements_ClearView.pdf) — it includes the legal contact and the template they use for vendor onboarding.

Can you circulate a mutual action plan with milestones and owners? Also, who 
…[truncated]
```

#### #2 `dsid_5a7a71032ce149e1b9979bf18bacd6f3`

```
Post-demo: commercial onramp & security gating — procurement options

From: Vivek Kulkarni <vivek.kulkarni@redwood.ai>
To: Alice Nguyen <alice@goodhealth.com>
Cc: marissa_cole@redwood.ai, karthik_iyer@redwood.ai
Date: Thu, 22 Apr 2027 17:12:00 -0700
Subject: Post-demo: commercial onramp & security gating — procurement options

Thanks again for the demo earlier today, Alice — appreciate the time. Quick recap and proposed next steps so we can get you to a fast pilot without surprises.

Key notes from call:
- GoodHealth interested in Redwood for patient-facing summarization and triage (initial pilot: 2-4 models, ~500k tokens/month).
- Procurement preference: typically PO for contracts >$10k/mo; however team is open to marketplace if that speeds onboarding.
- Security asks: SOC 2 Type II report, DPA signed, and a short security questionnaire from your InfoSec team.

Asks / proposed path:
1) Which procurement route would you prefer if both are an option: Marketplace enrollment (fast) OR PO/invoice (standard)?
2) Can procurement share a target procurement date / cutover window? You mentioned end-of-month would be ideal.
3) Security: we can share our most recent SOC 2 Type II and a pre-fi
…[truncated]
```

#### #3 `dsid_62d0211fd9334dfb85f8ba2194e17a12`

```
VPC commercial: rebate & support bundling inquiry

From: Sanjay Rao <sanjay.rao@healthbridge.ai>\nTo: Tessa Morgan <tessa_morgan@redwoodinference.com>\nCc: procurement@healthbridge.ai\nDate: 2027-06-14T09:12:00Z\nSubject: VPC commercial - rebate & support bundling question\n\nHi Tessa,\n\nThanks again for the demo last week. We ran the pilot on two sites and the execs asked me to follow up on pricing: specifically whether Redwood can offer a rebate on the platform fee if we commit to a 3-site rollout (pilot -> staging -> prod) and whether that rebate can be tied to a higher support tier (SLA 99.9 + 4hr P1 response).\n\nTwo quick constraints from our side:\n- procurement requires a single contract and an attached SOW (we've attached an internal draft to this mail).\n- we'd like a consolidated invoice monthly, not separate invoices per site.\n\nCan you outline options (standard vs. committed rebate) and any limits on burst capacity / node allocation for private deployments? We're preparing a procurement packet for next Wed.\n\nBest,\nSanjay\nDirector of IT \nHealthBridge Labs\n\nAttachment: HealthBridge_internal_SOW_draft.docx (stub)
From: Tessa Morgan <tessa_morgan@redwoodinference.
…[truncated]
```

#### #4 `dsid_03a70a43e57c4895b63e456c7e836890`

```
MAP: Alder Health — success criteria, exit gates, and procurement checkpoints

From: Rafael Mendes <rafael.mendes@redwood.ai>
To: Claire Zhang <claire.zhang@alderhealth.com>
Cc: laura.bennett@redwood.ai, marcus.lin@redwood.ai
Date: Wed, 14 Jul 2027 09:12:00 -0700
Subject: MAP: Alder Health — success criteria, exit gates, and procurement checkpoints

Claire — great to meet last week. Following up with a draft mutual action plan so we can align on what ‚success’ looks like for Alder’s evaluation and what procurement needs to unblock signature. High level: 6-week technical evaluation (pilot) + 8-week measured production ramp. Key asks below — please confirm/annotate.

Summary of primary acceptance gates (draft):
- Gate 1 (Week 2): Integration & data sanity — live API calls to non-prod dataset, no PII exfiltration, response rate >= 95% for sample set.
- Gate 2 (Week 4): Latency & throughput — 95th percentile latency <= 280ms for 512-token requests under 10rps baseline; sustained handling of 30rps burst for 5 minutes.
- Gate 3 (Week 6): Quality & concordance — accuracy/concordance >= 88% on the clinical extraction prompt set (shared).
- Gate 4 (Onboarding signoff): Operational requireme
…[truncated]
```

#### #5 `dsid_becda14d664a40bebfc240c766e6c5c2`

```
Post-call: technical pathway & scope checklist for HealthPath POC

Hi Jamie + Tom,

Thanks for the time today — quick recap and proposed technical pathway so we can move to a scoped POC. I captured the pain, the success criteria you shared, and suggested next steps below. Please flag anything I missed.

Pain points you described:
- Current triage assistant returns inconsistent prioritization for urgent referrals (precision at top-k is low).
- Latency spikes on peak hours when running models in-house; cost of overprovisioned GPUs is a concern.
- Difficulty adding structured outputs into downstream EHR fields (need deterministic JSON schemas).

Goals for the POC (agreed):
1) Demonstrate 95%+ top-1 relevance on a 500-case test set for triage labels (embeddings + rerank).
2) End-to-end latency below 450ms p95 for classification/structured extraction in production-like load.
3) Delivery of a function-calling + streaming pipeline that emits a validated JSON payload for EHR ingestion.

Technical pathway we propose:
- Phase A (week 1): Connector + sample dataset ingest (you provide 500 de-identified cases).
- Phase B (week 2–3): SDK integration for embeddings + rerank; run offline evals an
…[truncated]
```

#### #6 `dsid_4fb433d5bc984ee4b7f8a0815bb693b2`

```
Mutual action preflight: capacity & lead times — MAP for Dedicated/Private

From: Naomi Feldman <naomi_feldman@redwood.com>
To: Kat Greene <k.greene@helixhealth.com>
Cc: Marissa Cole <marissa_cole@redwood.com>, Ben Carter <ben_carter@redwood.com>
Date: 2027-05-20T10:12:00-07:00
Subject: Mutual action preflight: capacity & lead times — MAP for Dedicated/Private

Kat — following our call this morning, attaching a short preflight so we can lock the MAP items related to capacity reservation and close timeline. High level asks: 

- Confirm target production start date (you mentioned early Q4).
- Procurement / PO cadence and expected sign date from your side.
- Desired GPU pool sizing (p95 tokens/day) and acceptable latency SLOs.
- Whether this will be Dedicated (Redwood-managed GPU pool) or Private (VPC/on-prem) for the initial rollout.

Our constraints to call out up front: Dedicated lead time for H100 tranches is ~8–12 weeks from commitment (depends on region); Private on-prem/VPC installs add an installation window of ~4–6 weeks plus customer infra validation. For MAP planning we usually include a 2-week staging acceptance window and a 3-week buffer for any rework discovered during e
…[truncated]
```

#### #7 `dsid_3ebb269f9c3841fdbdd14c376311e299`

```
MAP: anchoring the close date — proposed bridge and procurement checkpoints

From: Markus Klein <markus_klein@redwood.com>
To: Sara Velasquez <sara.velasquez@medicore.com>
Cc: Camila Reyes <camila_reyes@redwood.com>
Date: Fri, 27 Aug 2026 09:08:00 -0700
Subject: MAP: anchoring the close date — proposed bridge and procurement checkpoints

Sara —

Following our sync this morning, attaching a focused MAP and a procurement checklist that target the items MediCore called out. High level proposal:

- Re-baseline close to 2026-09-24 (three-week buffer) to allow procurement PO, SOC evidence dispatch, and a one-week acceptance canary.
- Bridge items (must-have): signed PO, SOC 2 evidence package (we can provide the redacted bundle by EOD Mon), Docusign for the addendum, and a scoped canary acceptance plan.
- Risk delta: procurement lag and internal security review — mitigations below.

Immediate asks:
1) Please confirm whether MediCore can commit to a PO by 2026-09-10.
2) Confirm acceptance criteria owner (who signs off on canary) and a functional contact for the week of 9/20.

Attachments: MAP-draft-v3.pdf (application/pdf, 96 KB); procurement-checklist.xlsx (application/vnd.openxmlformats
…[truncated]
```

#### #8 `dsid_fb73513f33204883b0130d2bf88a88b2`

```
Packaging optimization & tier tradeoffs — ClarityMed

From: Samantha Ortiz <samantha.ortiz@claritymed.com>
To: Karthik Iyer <karthik.iyer@redwoodinference.com>
Date: Wed, 22 Mar 2028 09:14:00 -0700
Subject: Packaging questions — tier posture & burst needs

Hi Karthik,

Thanks again for the demo last week — the team liked the latency profile, but procurement and architecture have a few open questions before we move forward:

- We currently use a mix of reserved capacity and on-demand for inference. Curious which Redwood packaging you’d recommend for predictable throughput with occasional burst month-over-month.
- Can we mix a smaller dedicated pool for our critical pipelines and a metered host plan for lower-priority traffic without losing the same API interface?
- Pricing ask: what discounts are typical for a 12–18 month commitment? Any levers (credits, seat bundling, feature gates) we should consider to hit our 20% unit-cost target?

We’re aiming for procurement sign-off by the end of April. Can you share a quick note of options (upgrade/downgrade paths + tradeoffs) and attach any SOW-ish template you’d use? I can loop in procurement (procurement@claritymed.com) if helpful.

Best,
…[truncated]
```

#### #9 `dsid_43a97ef31b374195a66e116b8aa52d68`

```
MAP cadence lag — forensics and traction plan

From: Sanjay Patel <sanjay.patel@novumhealth.com>
To: camila_reyes@redwood.com, Asha Narayan <asha.n@novumhealth.com>
Date: 2026-08-25T09:15:00-07:00
Subject: Re: Mutual Action Plan — procurement timing

Camila / Cam team,

Quick status from my side — procurement just surfaced a legal review + third-party security questionnaire. The vendor-security slot they gave is next Tuesday, which pushes our internal procurement sign-off at least two weeks. Practically that means our target go-live around 2026-09-01 is unlikely unless we compress other MAP items.

We want to avoid losing the September cadence. Two asks: 1) can Redwood support a compressed MAP (parallel acceptance + early access) and 2) any temporary concessions you can make on onboarding or credits if we need an extra week?

I can circulate the full questionnaire this afternoon. Appreciate quick guidance — procurement will escalate internally if we can't show a compact remediation path.

Thanks,
Sanjay
Sanjay Patel
VP, Platform Ops
Novum Health

[Attachment: vendor-questionnaire.docx (docx) — referenced but not included in this export]
From: camila_reyes@redwood.com
To: Sanjay Pat
…[truncated]
```

#### #10 `dsid_c7110f395ad042769bab6231ca56989c`

```
Pipeline buffer assessment & mitigation plan — Q2

From: Aditya Rao <aditya.rao@redwood.com>\nTo: Ben Carter <ben_carter@redwood.com>, Neha Kapoor <neha.kapoor@redwood.com>\nCc: Marissa Cole <marissa.cole@redwood.com>\nDate: 2028-04-05T08:12:00-07:00\nSubject: Pipeline buffer assessment & mitigation plan — Q2\n\nTeam —\n\nQuick heads-up as Finance locked the preliminary Q2 forecast this morning: our pipe-to-quota buffer in US mid-market shows a 18% shortfall versus the coverage target we agreed in the planning cadence. I ran a quick pass on the top-20 deals that can move in the next 30 days and attached a one-page summary plus a MAP (NIM-MAP-v2.xlsx).\n\nGoal: get to a defensible commit for Forecast A by Friday EOD (2028-04-07).\n\nPrimary asks (please action by EOD Wed):\n- Ben: flag any deals you can reasonably push to Commit this week (stage move + clear next-step) — update HubSpot deal stage + expected close date.\n- Marissa: run a quick health check on the five deals we discussed last week (contacts, demo dates, procurement status) and call out any that need leadership touch.\n- Neha: confirm whether we should tighten the buffer target from 1.4x to 1.6x for mid-market given cu
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 34: `qst_0200::semantic` · N=25000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are generally on-topic regarding latency and system performance but do not specifically address the end-to-end response time target for the hospital system's chatbot. The failure mode is likely an embedding near miss, as the retrieved documents are related but not specific to the question's context. The chunk quality is decent, but relevance to the specific question is low

### Question

For the hospital system that wants to run an interactive intake chatbot and auto-generate discharge writeups entirely inside its own locked-down data center with no patient data leaving the network, what end-to-end response time target did they set for producing about 200 tokens under peak load?

### Gold document(s)

#### GOLD `dsid_eab7ef95052c4016aff7a3df422131f0`

```
ValeHealth on-prem implementation capture

Call notes (2024-09-17) — discovery with ValeHealth (CTO: Aaron Li, SecOps: Maya Singh, Arch: Dan Ochoa)\n\n- Context: ValeHealth is a mid-sized digital health provider planning to run conversational triage + discharge-summary generation inside their data center (air-gapped option discussed). They must not send PHI outside their network. Primary asks: private control plane with VPC peering to their corp network, KMS/HSM integration for key material, audit logs for every inference, and 12 month retention for audit records.\n\n- Key constraints called out by customer:\n  - PHI: full PHI scope, must meet SOC2 + HIPAA controls.\n  - Network: strict egress rules; anything that talks to hosted control plane needs explicit allow list.\n  - Hardware: they will provision 2x A100 80GB per zone initially, plan to add 4x after pilot.\n  - Throughput target: 12 concurrent triage sessions, average 40 tokens/response, target p95 token latency per token <= 90ms (end-to-end p95 for a 200-token response <= 18s) — customer expects interactive feel.\n  - Burst behavior: expect spikes morning 8–10AM and post-op 3–5PM.\n\n- Functional reqs (high level):\n  1) On-prem Redwood Private with local model hosting and local KV/prefix caching.\n  2) VPC-only control plane connectivity (can run in their VPC or peered) — no public IPs on inference nodes.\n  3) KMS or HSM integration: must support AWS CloudHSM or on-prem Thales via KMIP.\n  4) Audit logs: immutable tamper-evident logs for each request (user id, route, token counts, prompt hash).\n  5) Structured outputs: discharge summary templates + JSON schema enforcement + function-calling hooks.\n  6) Streaming WebSocket support for triage chat UI.\n  7) Canary deploys and fast rollback; cannot have model drift affecting PHI fidelity.\n\n- Non-functional / ops notes:\n  - Warmup: with A100s expect ~20–40s cold start for large Llama-family models to reach peak throughput. Need pre-warm policy for scheduled windows.\n  - Batch sizing: small batch sizes to preserve latency SLO; recommend continuous batching with low-latency cutoff (15ms).\n  - KV cache: prefix caching will significantly cut token gene
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_ae34b1a3cb6a47c8aeeaf6eb4cd9fa4c`

```
Vermillion Hall Platforms

CRM notes: 
- Product team (Lead PM: A. Rivers) wants dedicated so they can guarantee latency for paid tier. 
- Quote from PM: "We care more about latency consistency than absolute lowest cost — business UX depends on predictability." 
- Procurement timeline: internal finance review scheduled Mar 2026, legal will need SOC2 + data residency clauses. 
- POC ask: Redwood to provide capacity runbook + recommended cluster config (GPU type, pool sizing, autoscale thresholds) and an initial pricing term sheet. 
- SE notes: can leverage prefix caching for doc-search to reduce token spend; need to run a small canary on Dedicated with 10% traffic. 
- Action items assigned: Evan to circulate draft SOW by 2026-03-05; Priya to produce sizing calc and cost per QPS estimate; Jordan to prepare onboarding checklist. 
- Risks: EU customers expect data residency; ops team currently blocks any cloud-only solution without VPC+HSM options.
Dedicated sizing call with infra + pricing proposal; send draft SOW and capacity forecast
Procurement review
Need EU data residency option
Budget committee sign-off
2025-11-10: Intro demo (AE Evan + SE Priya) — showed hosted quickstart + emb
…[truncated]
```

#### #2 `dsid_78643c4ae9f24e7ab7543da3e8c40266`

```
LatticeBeam QueryCraft

Inbound SMB lead - bought credits, spinning up candidate-facing chat widget. Primary pain: perceived slow response times for EU users (frontline recruiters).
CTO (A. Morales) quote: "Users in London report 1.6s -> 4s variance, sometimes timeouts."
Integration: JS SDK -> app server -> Redwood hosted_api. No Dedicated.
Traffic pattern: peaks 11:00-15:00 UTC. Observations: spikes correlate with model selection (larger base model in EU) and long system + history prompts.
Customer constraints: cost-sensitive; prefers EU data residency for EU candidates but fine with public cloud.
Common asks: region switch test, timeout guidance, prompt length heuristics.
SE quick wins recommended: pin region to nearest endpoint, set client/server request_timeout 8-12s, enable streaming responses to improve perceived latency, trim system prompt to 300-400 tokens, aggressive history truncation (last 3 messages + summary from vector search), enable prefix/KV caching for canned replies, consider lower-latency model variant if acceptable quality tradeoff.
References: Fireflies ff_97531eac (call 2026-03-01); gmail thread-APH9k3Lq; drive links provided.
2026-02-20: Inbound signup via s
…[truncated]
```

#### #3 `dsid_4df2ca01cc9b427d985c51a63b595a87`

```
CoveHaven QuickAssist

High tail latency (p95) for NA East users when calling hosted API from us-west default region; worsens with long system prompts and bursty traffic.
perceived high latency for NA users
unclear client timeout settings
token cost concerns for long prompts
Send short perf lab checklist + 30m region A/B session; follow-up email with prompt-length guidelines
2/20 - inbound signup via self-serve credits. quick setup, first API keys provisioned.
2/22 - initial test: default region us-west chosen by UI; devs report slow chat replies for east coast users.
2/24 - 15m call w/ Jordan (AE) + dev lead (Aisha). customer: 'responses feel snappy in dev but 400-700ms extra RTT in production'.
2/24 - dev notes: single-turn support replies (~120-200 tokens) hitting p95 latency spikes during traffic bursts.
2/27 - SE (Priya) requested traces and example request ids; customer provided sample trace (ff-20260224-01).
3/03 - AE suggested region A/B test: try us-east-1 vs us-west-2 and enable streaming to reduce perceived latency.
3/05 - customer ran quick smoke: us-east-1 median latency improved ~80-120ms vs us-west, but p95 still elevated when messages include long system prompt.
3/0
…[truncated]
```

#### #4 `dsid_43b87c65f81b4e2ca03ef919c456effd`

```
Moonbeam Sprint AI

Lead background: small ecommerce SaaS (checkout messaging + merchant help chat). Self-serve signup, early discovery. Primary pain: perceived slowness on customer-facing chat widget.
- "Can we make replies feel instant?" — product lead quoted on call.
- Reported metrics: median latency ~380ms but p95/p99 up to 900ms on EU users. Most traffic originates EU; account defaulting to us-west endpoints.
- Current setup: using SDK default region (us-west-2), timeout_ms left at SDK default (10s), no streaming enabled, long system prompt (~1.2k tokens) appended client-side.
- SE observations: network RTT + cold model initialization + long prompt length are primary contributors. Also small batch sizes (1) causing limited throughput but better latency — need balance.
- Quick wins suggested to customer: switch to eu-west-1 region for EU traffic, enable streaming for perceived latency, move heavy static system prompts to server-side cached context (prefix cache) or use short system + retrieval for long content, set client timeout to 30s only for long-running ops, instrument SDK to capture request_id and region in logs.
- Longer-term: evaluate model variants with faster inferen
…[truncated]
```

#### #5 `dsid_caa8922c528b4bad8c5391ec1e5ad409`

```
Pyxis Transit Systems

Customer context: national transit operator; high-availability for rider-facing chat and ETA reranking; outages directly impact operations
Scale: peak concurrent requests estimated 12k QPS at regional level during rush windows, baseline 2-3k QPS off-peak
Primary ask: Dedicated GPU pools across 3 regions (na-east, na-west, eu-west) with active failover and 20-30% headroom for spikes
Latency targets: p50 <30ms, p95 <80-100ms for chat generation (end-to-end); embeddings p95 <60ms
Throughput guarantee: 10k tokens/sec sustained per region (reserved), burst to 40k tokens/sec (shared burst) during incident windows
Customer prefers pinning model families (llama-variant and a faster distilled model) and automatic fallback to smaller model on overload
Security notes: must support SAML SSO, KMS key ownership, audit logs retention 1 year, and optional on-prem enclave for PII flows
Quoted: 'We need deterministic throughput in rush hour — can't have noisy neighbor impact' (VP Infra)
Cost sensitivity: moderate-high; interested in Redwood Optimize recommendations for batching/quantization to reduce reserved GPU count
POC asks: 4-week pilot with reserved pool in na-east and n
…[truncated]
```

#### #6 `dsid_080da3e2a82e41158a49f62d4739dc46`

```
NimbleClasp AIWorks

NimbleClasp builds an in-app support assistant + knowledge search. Primary workloads: real-time chat snippets (low-latency), nightly document embeddings for search, and reranking for suggestion feed. Current hosted API usage from quickstart shows heavy token counts due to long system prompts and full conversation history being sent. Targets: p95 chat latency < 250ms, support flows <= 200ms median; cost sensitivity high — target 30%+ reduction in monthly token spend. Wants guidance on batching for high-throughput embedding pipelines, prefix/KV caching for chat, and automated prompt compression/token audits for templated messages.
Inbound demo signup via quickstart (converted from free credits) — high product engagement: 4 teams active.
Primary ask on first call: how to cut monthly token spend — mentions high cost from long system prompts and chat history. Wants concrete levers: batching, caching, prompt compression.
AE notes: they're comfortable with hosted API (public cloud) but cost sensitivity is high — CFO flagged potential cancel if unit economics don't improve.
Quote from CTO (Mar 02): 'Our retention engine will blow the budget if we keep calling the big m
…[truncated]
```

#### #7 `dsid_b558dd44aa6141228f8cafc23dcbfe89`

```
BrightSail Answers

2026-02-10: self-serve signup, trial API key issued (free credits)
2026-02-18: inbound email complaining about perceived slowness in EU region (Gmail thread)
2026-02-25: short exploratory call (15m) with AE Maya to get context; customer reported p95 ~800-1200ms on chat flows
2026-03-02: 45m technical sync with SE Diego (Fireflies ID ff_6729); agreed to run perf trace, try region switch and shorter prompts
2026-03-04: SE uploaded tracing ticket RDW-1421; provided suggested timeout and prompt templates
Lead background: BrightSail Answers operates a small ecommerce chat/support widget used on their storefront. Came in via free signup; heavy focus on fast reply times for checkout-touch flows. They are price conscious and want to keep everything on hosted API (public cloud).

Customer-reported symptoms (from email & call):
- "Perceived slowness" when customers ask shipping/checkout questions; internal timing shows p95 ~800-1,200ms for single-turn chat requests.
- Timeouts in their frontend at 1.0s cause degraded UX; they sometimes hit client-side 504s.
- Variance by region: EU users saw worse median latency vs NA.

What we verified / recommended so far:
- Region choi
…[truncated]
```

#### #8 `dsid_627192b1db54474386f0be4d1905f678`

```
Elm Harbor Assistants

Inbound SMB lead via self-serve (free credits). Small engineering team (2 backend, 1 frontend). Primary product: chat-based support assistant + doc search across help center. Key pain: perceived slowness on user-facing chat — several customer complaints this week.

Observed behavior (customer reports / internal testing):
- Users in US experiencing ~600-900ms extra RTT vs EU users; account originally created with default region eu-west-1.
- Frontend shows request timeouts at ~12s (client-side) when prompts include long context + history (~1.5-3k tokens).
- Team tried increasing client timeout but worried about cost and UX.

What they've asked/said: 
- "We signed up fast, but users are saying the bot feels slow — is this something we can fix without moving infrastructure?" 
- Very cost-sensitive; prefer hosted API but may upgrade if clear perf wins.

Redwood quick wins suggested on call: 
- Region: suggest creating API key in us-west-2 region for US traffic; ran quick curl test (we provided sample) showed ~250ms median improvement in staging.
- Timeouts: recommend bumping client timeout to 30s temporarily for troubleshooting and using streaming to cut perceived
…[truncated]
```

#### #9 `dsid_9a685924a565498f98e609151249d57f`

```
Fractile CX Economics

Platform must enable low-latency automated replies for high-volume chat deflection while minimizing cost per conversation. Key levers requested: continuous batching, prefix/KV caching, 4-bit quantization profiles, smart routing to smaller fallbacks, and dedicated capacity option for predictable burst handling.
avg_latency_target:<200ms_for_ui_responses
95th_latency_target:<300ms
target_throughput:1200_qps_peak
target_cost:<0.003_per_deflected_conversation
open_quantized_13B_4bit
7B_int8_fallback
tiny_fallback_for_routing
Must support policy-based routing: route by latency SLO, cost tier, and session stickiness. Automated fallback to lower-cost model variants during sustained load.
Zendesk app + server-to-server tool-calls (create/update ticket) with idempotency. Webhook backpressure handling. Export usage and cost metrics to Snowflake and BI dashboards.
Procurement requires modeled unit economics (tokens -> $) for three scenarios: baseline hosted, dedicated reserved (monthly commit), and private VPC. Break-even within 9 months preferred.
Show 30-50% cost reduction vs their current in-house LLM routing, hit 95th pct latency <300ms, demonstrate quantization wit
…[truncated]
```

#### #10 `dsid_9fad67220fcc4e6596b8f2cc292872d1`

```
Crimson Lark Assist

Inbound SMB — self-serve signups, small engineering team.

Summary: Customer signed up via hosted API trial (credit used). Primary ask: improve perceived latency for their chat widget (live support). They are metric-driven — want p95 under ~250ms. Currently seeing p95 ~300-450ms from EU users; NA looks OK.

Call notes (2026-02-14, Fireflies ffl-20260214-CL-01):
- AE Aisha intro + quick product pitch.
- CTO Mara Hsu: 'Users complain the chat feels sluggish; conversion drops on slow interactions.'
- They tested region eu-west-1 and saw median ~120ms but p95 spikes to ~420ms on longer prompts + context.
- Want recommendations that are actionable for their small infra team — prefer hosted API tuning (no private).

Technical pain points observed / reported:
- Long system prompts + verbose context (avg prompt tokens 1500) causing kernel overhead and tokenization latency.
- No client-side timeout standardization; UI times out at 10s which sometimes cancels before streamed tokens arrive.
- Using default model variant; interested in lower-latency variants but worried about quality regressions.

Perf tuning guidance given (short bullets):
- Region: suggest NA for majorit
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 35: `qst_0204::semantic` · N=5000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are generally on-topic, discussing SaaS trials and technical requirements, but they do not specifically address the question's focus on mid-market product analytics SaaS and its specific needs. This suggests a lexical mismatch in retrieval. The gold chunk is relevant and non-empty, while retrieved chunks are also non-empty but less relevant.

### Question

What are the immediate follow up actions for the mid market product analytics SaaS that wants cheaper and more consistent in app assistant responses and is planning a short trial on the shared service before moving to a private network isolated deployment?

### Gold document(s)

#### GOLD `dsid_a45c07f3daaf47c18b7bc75d3cbf2112`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_48e13d429774409db3aaa152d19407b6`

```
RiverMark Assist

Inbound SMB lead. Signed up self-serve trial on hosted API. CTO (A. Patel) is the primary security contact. Immediate asks: SOC2 Type II evidence or concise SOC2 summary, full sub-processor CSV, DPA for legal review, data residency options (US/EU), and default retention for embeddings. Wants legal sign-off before trial end (two weeks).

Call snippets: 
- 2026-03-07 intro (Maya/Carlos): good product fit for KB + triage bots; latency ok (P95 150-250ms in test).
- 2026-03-09 security sync: "We can't push to paid until we see SOC2 or equivalent and a sub-processor list."
- 2026-03-11 email: attached logs; asked "where do embeddings live and how long".

Sales note: Low-touch onboarding. Focus follow-ups on security artifacts, not feature deep-dives.
Hosted API will power a helpdesk assistant: real-time chat, semantic search over internal KB, and reranking recommended articles. Traffic small (10-30 qps), p95 latency target ~300ms. Cost sensitivity moderate; must avoid storing PII without controls.
Is Redwood SOC2 Type II in-scope for hosted API?
Who are the sub-processors for compute, logging, monitoring?
Can we get a DPA and choose EU/US residency?
What is default embe
…[truncated]
```

#### #2 `dsid_799a1bb8e7234cdf89834a0a17e04ba4`

```
Elmbridge Apps

SMB SaaS (customer support bot + KB search). Typical session length 6-10 turns, target p99 latency <600ms for chat, throughput modest (~3-5 rps peak), monthly token volume currently estimated 1.2M tokens (growing). Primary asks: concrete batching/caching recommendations, prompt compression best practices, token usage audit for current prompts, quick ROI estimates for quantization/batching. Preference for hosted API (self-serve) but want to understand Dedicated only if spend scales. Low compliance needs but require SSO and request-level audit logs.
- Lead came from organic docs/article on cost optimization
- Customer quote: "We love the response quality but the bill surprised our CTO"
- Wants a short, actionable token audit report (CSV of high-cost prompts)
- Interested in prefix caching for KB lookups and suggestion around prompt templating
- AE/SE recommended: 1) run token audit, 2) try batching 4-8 requests in dev, 3) evaluate caching 10-30s for repeated KB queries
- POC constraints: single AWS region, no VPC needed for now
- Files shared: example prompts.txt, sample logs (redacted), quick perf CSV
- Drive links above include sample token breakdown and suggested p
…[truncated]
```

#### #3 `dsid_451062cb78a04e08adb918f8c77a3748`

```
SableBeam Assist

Inbound via self-serve signup (trial credit used). Small B2B SaaS (in-app assistants for SMB customers). Primary ask: low-latency streaming for conversational UI embedded in their web app. Engineering notes from intro call: target p50 ~100ms, p95 <400ms for short-turn messages (most responses are 8-40 tokens). Expect ~200 active concurrent sessions initially; burst to 600 during peak. Cost sensitivity high — wants guidance on token/unit cost tradeoffs and batching. Preferred region: AWS us-west-2. Security: Okta SSO, need audit logs and optional KMS integration; retention default 30d. They tried prod PoC with another provider and reported intermittent streaming stalls and dropped frames: "we saw 200-800ms spikes and users felt it lagged". Redwood value props that resonated: streaming + predictable latency, per-route cost breakdown, easy SDK for websocket streaming.

POC ask: 2-week hosted API trial to validate steady p95 under 400ms w/ streaming enabled, sample SDK + latency harness, and clear contract on token caps for concurrent streaming.

Sales shorthand / recent note snippets:
- "AE intro: verified use-case + budget band, engineer (CTO) wants hands-on latency
…[truncated]
```

#### #4 `dsid_622d015ee083494eaefdb80d70b7638a`

```
Sundrop Hollow Analytics

Inbound SMB trial (signup from website). Short summary:\n- 2026-02-16: self-serve signup, generated first API key, very small initial test (few embedding calls).\n- 2026-02-18: onboarding call (Priya + Marco). Customer: small e-comm analytics startup, building product recommendation and search layers.\n- POC scope: embeddings for product search, chat for internal agent helpers, lightweight reranking for suggestions. Target throughput 5-10 rps, tail latency target ~200-400ms, cost-sensitive.\n- 2026-02-21: initial POC results: embedding quality OK, but observed higher-than-expected latency on longer queries; caching interest noted. Very low volume overall (30 API calls across first week).\n- 2026-02-25: asked for pricing example and best-practice on batching & caching; provided Optimize guide + suggested batching config.\n- 2026-03-05: follow-up email — no activity. Customer mentioned they were testing other vendors after being offered credits by a competitor.\n- 2026-03-12: churn signal: account inactive for 14 days post-key. No billing set up.\nNotes from calls/quotes: "We like the simplicity of the API, but we need predictable unit cost — credits from th
…[truncated]
```

#### #5 `dsid_85d1214a19b44f779a5c844647712756`

```
Saffron Lane Systems

30m tech deep-dive; trial region switch to eu-west; collect request_ids for diag
latency concerns hurting trial conversion
unclear best practices for client timeouts
no clear routing config in their SDK
2026-02-25: inbound signup via quickstart, connected API key, made first test calls
2026-02-28: AE intro email (Samira) — asked for traffic profile and latency targets
2026-03-03: discovery call (30m) — user reports intermittent 700-1200ms tail latency for chat; Fireflies transcript linked
2026-03-05: SE (Ethan) requested sample request_ids and region setting; customer shared SDK config (default region: us-west1)
2026-03-08: Ran perf tests with Redwood sample harness; observed 180-220ms median in us-west1, 600-900ms p95 for EU-origin traffic via us-west endpoint
2026-03-10: Follow-up call — customer to try eu-west1 endpoint and increase client-side timeout; AE scheduled tech deep-dive
Lead profile: small SaaS—helpdesk automation. majority of users in EU, HQ in NA (Toronto).
Key pain: trial users seeing slow responses ("feels laggy" from support testers). UX drop-off during sign-up funnel.
They self-served onboarding, used hosted_api; low integration effort but 
…[truncated]
```

#### #6 `dsid_5b7ebd1666de42f68602a7663ab34b63`

```
SummitRidge Cognify

Profile: mid-market SaaS (customer engagement platform) embedding a conversational assistant into product UI; priority is latency + deterministic behavior for tool calls.
Workload specifics: interactive chat agent with streaming responses + function/tool-calling to call internal product APIs (lookup, create-ticket, suggestion). Typical session: 4-8 turns, many short prompts (20-120 tokens).
Latency targets: customer quoted target: first-token 99th percentile < 400ms in-region; end-to-end including tool call < 800-1000ms if possible. Conservative SLOs for initial rollouts.
POC approach: start on Hosted API to validate correctness, streaming UX, and tool-calling reliability. If throughput/cost delta warrants, move to Dedicated with VPC for data separation.
Prompt/evals: they want automatic regression gating — every model/rollout must pass a set of prompt-based evals (agent-level behavior + hallucination checks). Require A/B comparisons and canary percentage with automatic rollback on metric regressions.
Cost sensitivity: product team cares about cost per DAU; engineering wants quantization + caching suggestions. Finance asked for modeled spend at 2M monthly token
…[truncated]
```

#### #7 `dsid_feb8da8346204b55a30da34d84e24073`

```
FoxDen FastAI

Inbound SMB lead from product signup. Primary contact: CTO (Aaron Patel) + Eng lead (Sophia). Early discovery — trying hosted API first; want self-serve trial to validate user-facing chat.

Recent activity:
- 2026-03-05: Fireflies call (ff-20260305-xyz123) with CTO. Demo of hosted API; Aaron reports "p95 ~1.1-1.3s from EU" on prototype flow.
- 2026-03-06: Support ticket RDW-4782 created (high latency observed for EU users). Attached sample request/response headers.
- 2026-03-08: AE (Maya) quick sync with Eng lead — they sent logs showing long tokenization time in client prep.
- 2026-03-09: Sent initial region recommendations + sample timeout settings (drive link). CTO replied: "We need clear, low-effort tuning steps; can't refactor retrieval pipeline right now."

Use-case / asks (from calls):
- Primary use: in-app chat for SMB dashboard (support + context-aware assistant).
- Latency priority: UX sensitive; want <500ms typical, accept occasional spikes but need improvements vs current 1.1s p95.
- Cost sensitivity: SMB budget; wants minimal lift (hosted API) before thinking Dedicated.
- Model preference: open to small/medium open models; curious about quantized variant
…[truncated]
```

#### #8 `dsid_3c69e5d0b7a6462d9c7d54f40dbb914d`

```
SpruceTop AssistKit

Building an in-app streaming chat assistant for SMB B2B SaaS. Expected traffic: 100-300 concurrent active users in month 1, scaling up. Target latency: p95 <= 100ms for user-visible first-token and smooth streaming. Priorities: streaming SDK, low overhead integration, predictable per-route cost.
Inbound self-serve signup from sprucetop.ai -> used free credits and hit streaming sample. CTO (Marco Reyes) on call 3/15. Wants very low latency for in-app assistant: "sub-100ms p95 is ideal for chat experience". Team is small (engineering 12, product 4). Primary ask: streaming SDK + example on React Native, per-route token cost clarity, and quickstart for prefix caching. Security: SOC2 required, SSO via SAML, audit log retention 12 months. Pricing sensitivity: startup budget; prefers pay-as-you-go initially but may convert to reserved if predictable. Notes from call: "If p95 jumps >200ms users complain instantly". AE notes: fast follow, send benchmark pack and invite engs to POC. Keep messaging simple — emphasize hosted API + streaming, minimal infra setup.
```

#### #9 `dsid_58a34b025e1c4ccf8c97dbc9e042548b`

```
Indigo Trail Assist

Inbound SMB from B2B SaaS company building embedded chat assistant for their product. Wants streaming-first UX (token-by-token) with end-to-end perceived latency <= 300ms on typical US calls. Team is engineering-first (CTO + 3 engs), self-serve oriented. Quoted: "we need near-instant typing experience; users drop off if assistant lags". Currently prototyping with small LLaMA-style model on hosted trial. Main asks: 1) examples of streaming API and SDK snippets, 2) per-route latency & token-cost dashboard, 3) auto-fallback to cheaper model on high load. Important: public cloud only, no VPC at this stage. Security: they require SOC2, SSO for later stage, and audit logs. Budget: pre-seed/seed metrics, expect ARR small first year. Next: send tailored quickstart (streaming example), published latency benchmarks for comparable workloads, and invite to 30m POC review. Notes are shorthand; contact prefers Slack for fast responses. 
Customer values low-touch onboarding. Would like a 14-day trial with streaming enabled and token usage meter. They may convert to paid hosted plan if latency SLOs and cost per session look reasonable. No enterprise contract expected now.
Send
…[truncated]
```

#### #10 `dsid_8ca703d991844bd195b4b8fdc16040fd`

```
Copperfield Nimbus Solutions

2025-11-12 - Initial inbound via community trial sign-up (self-serve).
2025-12-02 - Discovery call (Maya + Diego) - product: collaborative knowledge + chat; initial KPIs discussed.
2026-01-05 - Hosted API trial started (3-week trial, dev + staging integration).
2026-01-20 - Trial metrics snapshot: average QPS 42, peak QPS 160 during batch sync, average tokens/request 185.
2026-02-07 - Demo: Dedicated intro + cost model (Diego) — customer asked about reserved GPU sizing and canary rollout.
2026-02-18 - Capacity sizing workshop (Diego, Maya, infra lead Tom) — sketched out concurrency and token mix assumptions.
2026-02-26 - Security & compliance kick-off (Priya) — requested SOC2 evidence and KMS integration pattern.
2026-03-01 - Pricing follow-up email with committed throughput tiers and discount math sent (thread-1782345).
Mid-market collaboration SaaS building an in-app assistant + enterprise doc search. Started on Hosted API to validate UX and quality. After positive hosted trial metrics, moving toward Dedicated for predictable latency and data isolation. Core asks: predictable p50/p95 latency for chat (target p50 <150ms, p95 <400ms), embeddings throug
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 36: `qst_0208::semantic` · N=15000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The retrieved document IDs do not include the expected document ID, making the Hit@10 label incorrect. The retrieved chunks are relevant to contact center performance and burst handling but do not specifically address the Fortune 500 customer's burst traffic requirements. The failure mode is likely an embedding near miss due to the general similarity in topic but lack of specific match. The chunk quality is decent, but the relevance to the specific question is low.

### Question

For the Fortune 500 oriented customer evaluating a dedicated inference setup for an agent assist contact center, what burst traffic level and duration did they ask the vendor to guarantee beyond their steady state request rate?

### Gold document(s)

#### GOLD `dsid_c336dcdf965d44b0bcf4c8e3930af440`

```
Ironclad Support Reserve

Account synopsis: Ironclad builds a multi-tenant contact center SaaS used by several Fortune 500 CX teams. They are evaluating Redwood Dedicated to guarantee 24/7 SLA-backed inference for agent-facing features (low tail latency + reserved throughput).

Recent timeline and touchpoints:
- 2026-02-20: Intro call (AE Maya Chen) — high-level requirements captured. Customer: 'we cannot have model cold starts during peak hours; latency spikes kill CSAT.'
- 2026-02-25: Technical deep-dive with SE (Liam) — provided preliminary perf numbers, discussed batching, KV cache. Fireflies: ff_2026-02-25_ironclad_poc_call.
- 2026-03-03: Security questionnaire walkthrough with Security/Compliance; requested SOC2 + encryption details. Fireflies: ff_2026-03-03_security_review.
- 2026-03-08: Demo of route/fallback policies and canary rollout options; showed cost vs latency tradeoffs.
- 2026-03-10: Submitted POC plan and test harness (load script + prompt sets).

Requirements / success criteria (from customer):
- Reserved throughput to handle baseline + 3x burst for peak (target baseline 600 reqs/sec, burst to 1800 reqs/sec for 60s windows).
- 95th percentile token latency < 200ms for assistant replies; p99 < 500ms under normal load.
- Deterministic fallbacks: automatically route to quantized model variant when capacity constrained, with no more than 10% degradation in answer quality.
- Tool-calling / function-calling integration to their internal ticketing API (REST + OAuth). Must support idempotent retries and strict audit logs.
- Context window: maintain 8k tokens of conversation history with efficient KV caching; ability to pin last 5 system messages.
- Data controls: customer-managed KMS, audit logging retention 1 year, option for on-prem model hosting for regulated enterprise customers.

POC scope and plan:
- Week 1: Deploy dedicated pool in customer's VPC (staging), validate TLS + KMS integration, run security checklist. Drive doc: drive:/decks/ironclad-redwood-dedicated-pricing-v1.pdf.
- Week 2: Run synthetic load test to 2k reqs/sec with traffic shape that mimics morning/evening spikes; measure p95/p99 token latency and cold-start times.
- Week 3: Int
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_4f28f2c0e594459f9bda0cedbce6dda7`

```
Aurora SpikeGuard CX

Customer: mid-size cloud contact center provider focused on enterprise customers in retail and telco
Primary pain: system slowdowns and failures during incident bursts and seasonal spikes (Black Friday, product launches)
Current stack: hybrid — cloud-hosted routing + some on-prem ticketing connectors (Zendesk + internal KB); they run their own NLU for intent detection
Seeking: predictable, SLO-backed inference that can handle burst multipliers (10x baseline) without cascading failures
POC ask: demonstrate graceful degradation strategy (fallback to quantized model + routing to warmed dedicated nodes) — show 95th p95 and p99 during synthetic 6x and 12x spikes
Latency targets: <500ms end-to-end for short agent-assist completions (95th), tail tolerance to 1.2s for complex multi-call tool actions
Throughput targets: sustained 2k reqs/min, expected peaks to 12k reqs/min for seasonal events; average token length 80-120
Cost sensitivity: medium-high — will accept higher baseline cost for guaranteed reliability and predictable billing; looking for batching / cache suggestions
Tool-calling needs: function calling to ticketing system (create/update tickets), KB lookup pl
…[truncated]
```

#### #2 `dsid_f64d70ed51db4c7c94ae26be93157bb8`

```
Sequoia Reserve Workshop Co

2025-01-14: Intro call (Avery/Jordan) – high-level requirements, asked for baseline QPS and latency targets
2025-01-22: Technical deep-dive with infra + SRE (Jordan, Sequoia infra team) – traffic shape, caching constraints
2025-01-30: Workshop scheduled; pre-read sent (workload slide deck)
2025-02-07: Sizing workshop — ran traffic profiles, token distributions, peak simulation (recording: ff_5442)
2025-02-11: Follow-up with benchmark numbers; draft reserved GPU estimate shared
2025-02-18: Legal kickoff to discuss SLA windows and data residency (Drive: /Sales/Sequoia/legal/SLA-draft)
2025-02-20: Pricing revision after procurement questions
Workshop takeaway: workload is bursty — long tails during market open (09:30–10:15 ET)
Baseline steady-state: ~120 QPS for short chat flows (avg ~60 tokens output). Customer wants baseline guarantees + headroom for 3x burst capacity.
Peak observed in simulation: 380–420 QPS for ~8–12 minutes during market bursts; planning should allow 450 QPS headroom for safety.
Tokens/day estimate from workshop: ~25M–35M tokens/day depending on personalization fan-out.
Customer quote: "We need predictable unit economics — no surprise
…[truncated]
```

#### #3 `dsid_0378cb48015d438fac7668e261750bd7`

```
StratusPeak Surge Systems

Context: StratusPeak runs a global contact center provider that outfits mid-size retailers with chat + voice channels. Primary ask = keep agent-assist and auto-triage reliable during incident bursts and seasonal peaks.

Key quotes:
- "We hit 6x baseline on Black Friday last year and the modal model fell over — agents had empty suggestions and latencies spiked to 4s+." — VP Support
- "Need graceful degradation: low-priority summarization can fall back to a cheaper quantized model while high-priority agent assist uses pinned weights." — Head of Platform

Requirements summary (shorthand):
- Workloads: real-time agent assist (token-by-token streaming), post-call ticket summarization, automated tool-calls into Zendesk macros + internal orchestration, burst detection/alarm.
- SLOs: median latency < 120ms for autocomplete tokens in agent context; P95 end-to-end suggestion latency < 350ms during normal load; during bursts target bounded degradation and documented fallback.
- Throughput: avg concurrent agents 400, expected seasonal peaks 1600+ (target 4x baseline).
- Cost sensitivity: willing to pay reserve capacity for predictability but need transparent unit eco
…[truncated]
```

#### #4 `dsid_a2e4352770864f679741fd902a51ee87`

```
Cobalt Finance

Regulated finance prospect evaluating Redwood Dedicated with controlled burst capacity for predictable peaks (month-end close / batch risk runs). Interest is high but gated on security/compliance: audit logging coverage for burst config + admin overrides, strict RBAC (including Support/debug tooling), and contract/SLA language that clearly defines burst semantics + guardrails. Security review in progress; legal drafting language; technical evaluation focused on denial behavior, determinism, and observability.
Send (1) burst capacity contract/SLA addendum draft and (2) audit logging + RBAC evidence pack; schedule 60-min technical deep dive on burst guardrails + denial behavior; confirm data residency (us-east only) and retention settings for logs.
Security sign-off contingent on burst audit logging events, RBAC scoping for Support tooling, and log retention controls
Legal wants explicit SLA language: burst is optional/guardrailed, not part of baseline Dedicated throughput commitment; define denial/429 semantics
Procurement requires DPAs + subprocessor list alignment for Private/VPC deployment
HQ: New York, NY. Operates in US + limited EU footprint. Compliance posture
…[truncated]
```

#### #5 `dsid_1c22110ff4394bbea631b330f48bdc0f`

```
Crestline Realtime Assist

Real-time agent assist: streaming token-level suggestions and canned reply generation, ticket summarization post-call, model-invoked tool-calls to create/update tickets and lookup customer context. Must maintain low latency and robust behaviour during spikes; guardrails to block PII leaks and policy violations required.
Summary: Crestline builds a cloud contact center platform used by several mid-size telcos and OTTs. Looking to add low-latency streaming agent assist (token-level suggestions + canned reply tool-calls) to reduce AHT and ramp time.
Customer quote (VP Eng): "We need sub-100ms suggestion latency for 90% of typing interactions — anything above that the agents don’t use."
Primary constraints: strict EU data residency for a subset of customers, SSO via SAML, must demonstrate audit logs and KMS integration.
Current stack: Genesys/Avaya front-end via CTI bridge + homegrown orchestration; willing to run Redwood Dedicated or Private in their VPC.
POC ask: streaming suggestions with guardrails (intent detection + blocklist), live tool-calls to CRM and ticketing (create/update ticket), and graceful degradation under sudden spikes (Black Friday test sc
…[truncated]
```

#### #6 `dsid_3b8a6d554a994a739449fd95719f32ae`

```
Obsidian Harbor Inference Labs

Enterprise logistics partner evaluating Redwood Dedicated for low-latency dispatch and document retrieval. Primary goals: sustained throughput for 500 concurrent agents during peak (approx 300–600 qps depending on prompt length), P95 latency <= 120ms for short-turn prompts (<=128 tokens), P99 latency budget <= 400ms with fallback routing to smaller quantized model; predictable reserved GPU footprint (initially 8x A100-class equiv) and clear per-token costing for committed capacity. Must support VPC deployment, SSO/SAML, audit logs, and EU data residency for certain customers.
Finalize soak-test plan + confirm GPU SKU and rack assignment (due 2026-03-17)
capacity sizing approval from infra budget
legal needs SLA addendum for latency SLOs
data residency paperwork for EU customers
Phase 1 - Baseline: run single-node single-model perf tests with 1:1 client emulation, collect token-level latency histogram
Phase 2 - Load test: step up to target qps (300 -> 600) over 8 hours, validate autoscaling/burst behavior and KV cache hit rates
Phase 3 - Soak test: 72-hour sustained load at 80% of peak with simulated KV cache churn and model version roll
Phase 4 - Fai
…[truncated]
```

#### #7 `dsid_40c1008e9c4c44e1ab69666e14031887`

```
Mariner Benchmarking Labs

Run 2-day dedicated sizing workshop (baseline QPS + peak sim) and deliver GPU reserve proposal
internal finance needs final pricing for committed capacity
security wants HSM/KMS diagram for private deployment
2025-11-10: intro call (AE) — sketched use-case: low-latency chat + reranking for recommendations
2025-12-02: architecture review with infra (SE) — request for VPC-only control plane
2026-01-12: provided sample prompt traces and token histograms (MBL data) — avg tokens/req ~180
2026-01-20: SRE call — expressed need for 99.95% availability, 95th pct latency SLOs
2026-02-08: internal procurement check-in — interested in 12–24 month reserved commit
2026-02-22: pre-workshop call — agreed on metrics to capture: qps, tokens/sec, p95 token latency
Key ask: dedicated capacity for interactive personalization flows + reranking during live streams.
- Baseline traffic: weekday steady-state ~100 QPS across 12 services (chat + rerank).
- Peak: concurrent live events spike to 1,200 QPS for 3-6 minute windows (bursty, regional).
- Token profile: median 120 tokens/req, 95th ~450 tokens/req — impacts batching and KV-cache sizing.
- Latency targets: p50 < 60ms, p95 < 2
…[truncated]
```

#### #8 `dsid_9b7c033ca2d741b380c38e3edd38273d`

```
Lumen Reserve Platforms

Context: Lumen Reserve Platforms is an enterprise ecommerce platform embedding conversational search and product personalization into the storefront. Primary ask is a predictable Dedicated pool with throughput guarantees and clear latency SLOs for customer-facing chat. They will likely start with a 6–12 month reserved commitment and evaluate private on-prem pilot for compliance teams.

Key quote: "We need predictable tail latencies — if a promo goes live we can't have customers waiting or falling back to degraded models."

Requirements summary (high level): steady-state chat, high peak bursts (sales events), embedding generation for indexing, reranking for product results. Strict residency requirements for EU PII subsets; corporate legal requires SOC2 + KMS + audit logs before procurement. Very cost-conscious about steady-state unit cost but will pay premium for SLA-backed tail guarantees.

Sizing workshop focused items below (workshop run 2026-03-02): baseline QPS math, tokens/sec baseline and peak multipliers, GPU sizing options (A100/H100), warm pool vs. instant burst planning, fallback routing and auto-fallback policies, and SLA credit language draft. N
…[truncated]
```

#### #9 `dsid_79518960a5e94ef099f030986d818a53`

```
Pegasus Flow Assist

Account: core product is a cloud contact-center SaaS; 800 agents globally; heavy EU user base (finance clients)
Primary ask: realtime agent assist — streaming, sub-200ms p95 suggestion latency under normal load; graceful degradation to text-only 50ms slower during spikes
Use-case details: assistant shows suggested reply snippets, next-best-actions, and one-click tool calls (create ticket, escalate, send survey)
POC success metrics: p95 latency <= 200ms at 2k concurrent agents; no more than 5% error rate for tool-calls; summary quality NPS >= 4/5 vs human baseline
Model preference: open-models allowed but must support local quantized variants; prefer ability to pin model version + automatic fallback to a cheaper quantized model
Routing/fallback: need multi-tier routing (region -> dedicated pool -> hosted fallback). Must support explicit fallback policies for elevated latency
Guardrails & safety: redaction for PII, hallucination detection, response allowlist/blocklist, strict tool-calling whitelists; audit trail for every suggestion and action
Data controls: log-level toggles (no transcripts in hosted logs by default), retention policy configurable per-tenant, ke
…[truncated]
```

#### #10 `dsid_5ef618fee40741bb9fac512e2448e560`

```
Ferncrest Inbound AI

Lead source: self-serve signup -> product trial. Small ecommerce-focused conversational bot vendor. Primary ask: how Hosted API handles bursty traffic and quotas; wants minimal engineering work.

Recent timeline:
- 2024-10-05: Signup via docs quickstart, trial credits auto-provisioned.
- 2024-10-08: Initial discovery email from owner (Maya) confirming use-case: chat + order-assist + embedding-based FAQ.
- 2024-10-12: Quick 20-min intro call (Fireflies id ff_8231b2a-call-2024-10-18 scheduled follow-up). Discussed traffic patterns: regular 10-20 RPS, marketing-driven spikes up to 400-600 RPS for ~5-10 minutes during promotions.
- 2024-10-18: Demo + technical Q&A with SE (Liam). Covered token pricing, concurrency limits, and candidate mitigation strategies (client-side backoff, retry-after header, sidecar queue).
- 2024-10-22: Customer ran local spike test -> observed intermittent 429s at ~150 concurrent reqs; unsure whether due to per-key concurrency or org rate limit.
- 2024-10-25: Sent security questionnaire; customer expects audit logs and basic retention control (provided drive doc link). They are not asking for VPC/private right now.
- 2024-10-30: Pricing d
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 37: `qst_0209::semantic` · N=100000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the question but do not match the expected document ID, indicating an embedding near miss. Both gold and retrieved chunks are non-empty and on-topic, with good quality content. No pipeline issues or severity flags were identified.

### Question

For a small B2B SaaS embedding a live chat helper inside their product that needs partial replies immediately while it fetches recent user-event context, what first-response-time target and concurrent-load threshold were set as the pass criteria for their short trial?

### Gold document(s)

#### GOLD `dsid_51183030e764419caca09cfe647048e7`

```
Banyan Loop AI

SMB inbound — self-serve signup, early discovery. Focused on hosted API streaming for in-app assistant; latency sensitive, moderate cost concern.
Inbound from YC-backed B2B SaaS (product analytics assistant embedded in their app).
Primary ask: in-app chat assistant with streaming responses — product guidance + contextual suggestions pulled from app telemetry.
Latency focus: product team expects first token latency <200ms in US regions; OK with slight increase for long context fetches.
Cost sensitivity: SMB budget, wants predictable per-month hosted spend; likely start small (pilot) then expand if metrics ok.
Deployment: prefer hosted API (self-serve). No plans for Dedicated/Private in near term — ops bandwidth low.
Security: SSO via Okta, needs audit logs and basic retention controls; compliance ask is light (SOC2 preferred but not blocking).
Quote from CTO: "Need streaming to feel native — partial answers while we fetch context. If streaming is choppy, UX suffers."
Engineering note: currently queries include in-app session context + 2–3 KB of recent events; want guidance on prefix/KV caching and batching strategy.
Tried competitor sandbox (large provider) — liked latency but cost was opaque; wants transparent token pricing and per-route cost breakdowns.
POC success criteria: consistent first-token latency <250ms at 50 concurrent small sessions; error rate <1%; cost estimate for 10k messages/month.
Suggested Redwood value props called out: streaming SDK, per-route dashboards, cost breakdown, quick self-serve onboarding.
2026-01-24 - Web signup: used free credits, created first org; initial chat test (node/react demo) — low friction
2026-01-28 - Intro call w/ Taylor (AE) — product overview, mainly hosted API interest; mentioned target latency <200ms for first token streaming
2026-02-02 - Engineering sync w/ Priya (SE) — shared stack (React frontend, Node backend on AWS), asked about streaming SDK and token accounting
2026-02-11 - Demo of basic chat flow using vanilla streaming example; ran sample under dev load ~30 concurrent users; observed variable tail latency
2026-02-15 - Sent ask list: Okta SAML, audit logging SLA, cost per 1k tokens on hoste
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_a7de4ed8e20d4fd784748c38d66c1ee8`

```
RazorLeaf Chatly

Inbound self-serve signup from product site. CTO (Jordan Hale) and Sr. Eng (Mei Lin) on call. Primary ask: embedded in-app chat with streaming tokens — want near-instant replies and smooth typing UX. Latency target: p50 < 150-200ms for short replies, p95 < 400ms. Throughput: expected 30-60 concurrent active sessions during business peaks; optimistic growth to 200 concurrent over 6-9 months. Cost sensitive; primary metric = $/active-session-minute. Prefer hosted API for now (fast time-to-market). Quote from call: "We need something that feels instant inside the app — streaming + small chunk latencies matter more than slightly better model quality." Interested in prefix caching and request-level KV cache ideas. Mentioned they benchmarked OpenAI streaming but hit variability around region routing and token stalls. Security: SOC2 important for upcoming investor diligence; will need SSO (SAML) and audit logs in Q2. Data residency: NA-only preferred but not mandatory. POC: 2-week engineering spike -> integrate streaming endpoint, run load test, evaluate cost & UX. Owner notes: keep messaging light on Dedicated until clear scale signals — SMB, budget conscious. Short, ch
…[truncated]
```

#### #2 `dsid_70b7129b5b5940d8a17b1322f649957a`

```
QuickReply Stack

Small SaaS embedding a chat assistant into their product UI. Need streaming-first API with end-to-end perceived latency <200ms for p50, p95 target <600ms. Throughput modest initially (100–300 concurrent sessions), bursty at peak. Prefers public-cloud hosted offering; wants easy SDK for web streaming (SSE/WebSocket). High cost sensitivity; requests guidance on batching, KV/prefix caching and discount thresholds. Security: SSO for admin, audit logs, SOC2 proof for procurement. Wants model fallback policy (cheaper variant) when expensive model latency/cost increases.
Lead profile: small B2B SaaS building an embeddable chat widget for customer apps
Primary ask: streaming responses with UI-perceived latency <200ms for most tokens
Quoted from product lead: 'UI must feel instant; any multi-second pauses kill conversion.'
Prefer hosted API for speed to market — will revisit Dedicated if usage spikes or data residency asks arise
Model preference: open/compatible models that allow cheap sampling and local KV cache; willing to test Redwood-verified smaller variants
Cost sensitivity: high — target < $0.02 per active user/month for chat features at MVP scale
Onboarding notes: 
…[truncated]
```

#### #3 `dsid_d6ffa7c2fade456ea0e9628164c50e3b`

```
MicroGlint Assistly

In-app assistant for customer workflows: short queries (1-3 turns), context window ~2k tokens, must stream partial replies to UX. Primary model preference: cost-balanced 7B/13B open models (quantized) with fallback to slightly larger model when answer quality drops. Strong interest in built-in streaming + token-level cost breakdowns.
Early-stage B2B SaaS building an in-app chat assistant embedded in their product. Very latency sensitive — wants streaming token-by-token playback with median client-visible first-byte <300ms for short queries. Founder = ex-mobile product manager, cares about bandwidth and cost. Requested: "can we get streaming live in 1 day?". Currently prototyping on public cloud — prefers self-serve hosted API. Trial usage small but spikes in simulated demos (15-25 concurrent chat sessions).
Target median client-visible first-byte <300ms for 1-2s responses; peak concurrency 20 sessions; context cache useful for repeated prompts; prefer JSON streaming with function/tool-calling later.
Week 1: give trial tokens + quickstart; run 15-min streaming demo (SE-led)
Week 2: small integration (React SDK) — measure median first-byte latency and tail
Week 3
…[truncated]
```

#### #4 `dsid_5607a534089044e99d2422ffe483df27`

```
TidePointe Assistive AI

Need hosted API with predictable latency for in-app chat. Primary constraints: low-latency for EU & NA regions, minimal setup (self-serve), SOC2 attestation required for procurement, low cost per conversation. Workload: realtime chat (short to medium sessions), occasional embeddings for doc-search. Willing to accept model fallback to smaller/faster variants during peak if transparent to UX.
Inbound trial signup via self-serve. Product-led SMB using hosted API for chat-based in-app support widget. Early discovery: they hit latency spikes during peak (9am-11am CST) and seeing 500ms -> 1.2s for streaming first-token in na-east-1. Very cost-sensitive — wants to keep per-conversation token cost down; currently using ~1.2k tokens per convo (lots of context).

Call 2026-03-03 with AE + SE + PM: customer demo'd their flow, shared Fireflies recording ff_20260303_8721. Quoted: "experience feels sluggish for users in Europe" — they are routing EU traffic to na-east-1 due to initial signup. Asking for guidance: region choice, timeout best practices, prompt trimming, and streaming config.

Observed: client default http timeout on frontend is 1.5s; they are not using str
…[truncated]
```

#### #5 `dsid_bef1504f9179415bb2ebc5e2be12a7c3`

```
OrbitLoop Support

Lead came from self-serve signup; initial product fit looks good for hosted_api. Primary pain: perceived latency for live chat — agents complain answers are 'snappy sometimes, laggy other times'. Customer metrics: session A (5 concurrent users) sees reply times 300ms->2s range; peak hours 8am-10am PST worst. They are running a single-region integration pointing at default endpoint. Quotes: "We see the app freeze while waiting for completions — users leave the chat."

Key facts captured in call: fragments + bullets ok. Customer added full ticket history into prompt to improve context retrieval — length now ~1500 tokens in some cases. They have high cost sensitivity; want to keep hosted API (no Dedicated) for now. No legal/regulatory residency needs, SOC2 and audit logging are nice-to-have. Current implementation uses 5s request timeout in frontend; backend retries on 502 with immediate retry. They used streaming in one test but not consistently.

Customer asked directly for quick wins: region selection advice, timeout/retry defaults, prompt-length best practices, and whether enabling streaming or smaller context windows would reduce perceived latency. SE recommend
…[truncated]
```

#### #6 `dsid_872c0e6b001e4719bcb860b908f9d29a`

```
NibbleLoop Assistantry

Inbound via docs + quickstart — founder demoed live chat with 40ms perceived latency (local).
Product: white-label in-app assistants for B2B SaaS (help centers, onboarding flows).
Current infra: Node.js frontend + Go backend; using websockets for streaming UI.
Primary ask: turnkey hosted API that supports streaming responses (server-sent events / websocket) and predictable p95 latency under 150ms for 1-3 turn interactions.
Traffic profile: starting small — 200–1,000 monthly active users; peak concurrency expected 20–60 concurrent streams during demo events.
POC plan discussed: 1) self-serve signup + API key; 2) integrate streaming SDK (frontend) and measure browser->response TT partial tokens; 3) run 1k synthetic messages to validate p95 under 200ms; 4) iterate caching/batching guidance.
Quote from CTO: 'We need the assistant to feel instant — anything >200ms feels sluggish to customers.'
Model preferences: open weights ok; prefer cost-conscious smaller context models for chat; interested in Redwood-curated candidates and quantized variants.
Routing/fallback: would like simple fallback to a smaller low-cost model when load spikes; asked about auto-fallback p
…[truncated]
```

#### #7 `dsid_b558dd44aa6141228f8cafc23dcbfe89`

```
BrightSail Answers

2026-02-10: self-serve signup, trial API key issued (free credits)
2026-02-18: inbound email complaining about perceived slowness in EU region (Gmail thread)
2026-02-25: short exploratory call (15m) with AE Maya to get context; customer reported p95 ~800-1200ms on chat flows
2026-03-02: 45m technical sync with SE Diego (Fireflies ID ff_6729); agreed to run perf trace, try region switch and shorter prompts
2026-03-04: SE uploaded tracing ticket RDW-1421; provided suggested timeout and prompt templates
Lead background: BrightSail Answers operates a small ecommerce chat/support widget used on their storefront. Came in via free signup; heavy focus on fast reply times for checkout-touch flows. They are price conscious and want to keep everything on hosted API (public cloud).

Customer-reported symptoms (from email & call):
- "Perceived slowness" when customers ask shipping/checkout questions; internal timing shows p95 ~800-1,200ms for single-turn chat requests.
- Timeouts in their frontend at 1.0s cause degraded UX; they sometimes hit client-side 504s.
- Variance by region: EU users saw worse median latency vs NA.

What we verified / recommended so far:
- Region choi
…[truncated]
```

#### #8 `dsid_6eb7309b85b24fc38090e56f568f6d89`

```
Driftline Assistly

Embedding an assistant in their web app for B2B customers: quick Q&A, triage tickets, and short contextual followups. Priority: perceived latency and smooth streaming incremental replies. Secondary: embeddings for semantic search across product docs.
Inbound via self-serve signup. Product-led onboarding: created account, used free credits to prototype streaming chat. Lightweight engineering team (CTO + 2 fullstack). Focus: in-app assistant embedded in their SaaS product (B2B sales ops). Emphasis on sub-100ms token generation for short-turn dialogues, streaming for progressive responses. Cost sensitivity high — want predictability and quick tips on batching/kv-cache. Asked about token retention and audit logs. Legal asked for DPA and SOC2 proof. Sales comment: likely $3-8k ARR first year if latency + costs hit targets.
run 48h throughput/latency POC on hosted API using streaming; send quickstart guide + sample SDK snippet
want 50ms p50 for short chats - need benchmark evidence
concerns about token cost for streaming long sessions
legal wants SOC2 + data processing addendum
streaming websocket support
p50 latency <=100ms for <64-token responses
per-route cost esti
…[truncated]
```

#### #9 `dsid_d030f33813764880947db98061d277cf`

```
VelociChat Solutions

B2B SaaS in-app chat assistant for customer support and triage. UX sensitive to token-level latency (streaming). Wants React Native SDK and easy webhook integration. Low tolerance for >200ms token latency on happy-path streams. Prefers hosted API initially; may evaluate Dedicated later if usage ramps.
Inbound from YC alum founders (SaaS helpdesk/chat). Self-serve sign-up last week, used free credits, ran a toy integration.
Key quote from PM on call: "We need streaming responses that hit ~50-150ms token latency for good UX."
Customer priorities: low-latency streaming, easy SDK for React Native, predictable per-token cost, minimal infra ops.
Metrics shared: expected 20k monthly active users in 12 months, peak concurrent chat streams estimate 50-200.
Security: SSO required for web console; audit logs nice-to-have. No air-gapped/on-prem need today.
Budget: early-stage, expect to start on pay-as-you-go then move to small committed tier if SLOs met.
SE notes: wants example batching config, recommended token-cost estimator, and sample streaming demo with lightweight prefix caching.
Follow-ups: send integration guide + sample app, schedule POC for week of 2026-03-15.

…[truncated]
```

#### #10 `dsid_5a28962c1cb44e5699fce877df71bf35`

```
Slatefold Insights

Mid-stage SaaS that provides an AI-first support desk layer for e-commerce merchants. B2B2C focus; product-led growth. Primarily US customers. Self-serve sign-up landed 2026-01-10.
Primary pilot: AI triage + quick reply templates for support agents (chat flows) + embedding-based KB lookup. Requirements: low-latency short responses, modest throughput (peak ~30 req/s), strong token-cost sensitivity.
key issued + sample script provided; instrumented logs show single embedding batch call; no further SDK usage
2026-01-10: self-serve signup; trial API key issued automatically
2026-01-12: inbound email from CTO asking about latency for short chat flows
2026-01-15: AE Maya opened discovery thread; suggested sample prompts + cost estimates
2026-01-18: first API call seen (healthcheck + small embedding batch), then silence
2026-02-08: automated churn alert — 12 days no traffic after initial usage
2026-02-15: 30m call with SE Arjun — demoed hosted API, discussed prefix caching and batching; CTO mentions competitor credits
2026-02-22: price/credit follow-up sent; no reply
2026-02-28: check-in hit — reply: "trying competitor free credits first"
Trial looked promising: used e
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 38: `qst_0213::semantic` · N=40000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the question but do not match the specific details of the expected document. This suggests an embedding near miss, where similar content was retrieved but not the exact match. Both gold and retrieved chunks are non-empty and on-topic, indicating good chunk quality.

### Question

For a content templating company planning tens of millions of very short generations during a Q3 ramp, what was the requested plan for a time limited evaluation that included a large free usage allowance?

### Gold document(s)

#### GOLD `dsid_ad14c3cb06c4494093dfcfff5098d89d`

```
BrambleBox Content Labs

Lead source: inbound marketing signup (content marketing template generator).
Point of contact: Eliza Moreno (Head of Product) - eliza@bramblebox.co — technical but cost-constrained.
Why Redwood: fast time-to-market for hosted API, transparent per-token billing, suggestion for caching/batching to reduce unit costs.
Summary of need:
- High-volume short-copy workloads: email subject lines, 10-variant landing headers, social posts (mostly <120 tokens).
- Expected monthly volume: rough estimate 30M-60M generation tokens during Q3 ramp.
- Latency target: 100-300ms p50 for single-shot prompts (interactive UI).
- Cost target: want to keep average per-output cost under $0.0016 across variants.
- Model preference: open-weights or Redwood-curated small/medium models; willing to test quantized variants.
Deployment intent: Hosted API self-serve initially; may evaluate Dedicated only if unit economics require reserved capacity.
Security/compliance: basic SOC2 and audit logging required for vendor selection; SSO not blocking for now.
Conversation highlights (bullets, shorthand):
- 2026-02-11: Intro demo w/ Jordan + Eliza (FF id ff-20260211-bramblebox-demo). Product fit confirmed for short-copy templating.
- 2026-02-14: Email follow-up sent with pricing ranges + quickstart (Gmail thread/Gm-20260214-01).
- 2026-02-18: Eliza asked for concrete batching examples and expected savings for 10-variant outputs. "If batching saves 30% on token cost, that's a game-changer"
- 2026-02-20: Internal cost-model note from SE: run sample using hosted_api with 2 model variants (small, medium quantized) to compare latency/cost.
- 2026-02-22: Sync call to agree on benchmark data points; client to provide representative prompt set (sent).
Technical notes and asks:
- Primarily short outputs; prefix caching might help for template scaffolds. KV cache less relevant (no long conversations).
- Want to understand streaming vs non-streaming trade-offs for UX and cost.
- Interested in automatic batching configuration: want recommendations for batch size and timeout given 50 RPS bursty traffic.
- Question on model fallback: can Redwood route to cheaper variant automatically when qu
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_4b07ee432d54461e8e41640a184a47ef`

```
PhraseForge Labs

SMB marketing/content generation platform that churns high-volume short-form copy. Wants hosted API for quick onboarding, strong cost controls (caching/batching), and lightweight security (SOC2 + SSO).
Inbound from content-marketing demo; marketing team (50 writers) wants to reduce time-to-first-draft across campaign templates. Interested in Hosted API (self-serve) — wants predictable per-template costs.

Call notes (2026-03-02):
- Elena: 'We generate ~1.2M tokens/week across templates, peak spikes during promos'
- Ben: cost is primary blocker; also want caching so repeated templates are cheap.
- Prefer public cloud, no private VPC for now.
- No hard regulatory constraints but need SOC2 + SSO.

Technical requirements / wishlist:
- Low-latency single-request generation for short ad copy (target 200-400ms p95)
- Bulk batch rendering for nightly campaign generation (throughput target ~1000 requests/min)
- Token-level cost estimates and tooling to simulate monthly spend by template
- Support for prefix/KV caching; interest in server-side caching suggestions from Redwood Optimize

Sales snippets / shorthand:
- "high-volume, cost-first"
- wants self-serve sign-up + cred
…[truncated]
```

#### #2 `dsid_b65f12db881f41dc9239fe044f4754dd`

```
FluentForge Mediaworks

Inbound from content marketing vertical — demo requested after whitepaper CTA. Primary ask: scale templates and batch generate large sets of SEO articles (daily jobs ~10k+ completions).
- Source: inbound MQL via webinar 'Scaling Content Ops' (2026-02-20).
- Quote from CTO: "We need predictable cost per article and low tail latency for short templates."
- Prefers open/quantized models to control cost; willing to test Redwood hosted if unit economics beat current provider.
- Interested in batching and prefix/KV caching to amortize prompt overhead across thousands of similar templates.
- No immediate enterprise compliance requirement beyond SOC2; will accept public-cloud SaaS.
- Wants a short POC: 72h run, measure tokens per article, avg latency, cost per 1k completions, cache hit rate.
- Pricing deck sent (drive link). Security questionnaire partially answered; SOC2 attestation requested.
- AE notes: good fit for Hosted API self-serve -> convert by showing 30-40% cost saving with batching+cache.
- Typical content length: 200-800 tokens; many repeated prefixes (title, brand boilerplate).
- Rate expectations: sustained bursts, ~800-1200 reqs/sec for 5-10 minute 
…[truncated]
```

#### #3 `dsid_b22b28a8614b4aaf9e0b7a94b1b4e461`

```
Verblyx Content Suite

Inbound from content marketing ad; trial-focused SMB with large monthly volume patterns.\nTopline: builds multi-tenant SaaS for agencies + small brands to generate localized landing pages and micro-copy.\nVolume estimate: 5-15M tokens/month now, potential to double in Q3 — very cost sensitive.\nWants hosted API (self-serve) to avoid infra ops. Prefer predictable public cloud pricing and easy SDKs for Node/Python.\nKey asks: can we provide batching/caching guidance for SEO batching jobs? How does prefix/KV cache work with fine-tuned prompt templates?\nLatency target: 200-500ms p50 for short-copy generation (50-150 tokens) — can accept streamed responses.\nModel preferences: open-family Llama-derived variants or Redwood-curated small gen models to control cost. Will accept quantized variants if quality holds.\nSecurity: basic SSO/SAML for admin, audit logs retention 90 days. No on-prem requirement today.\nQuote from CPO on call: "We need to validate unit economics before committing — show us predictable per-1k-token breakdown with caching savings."\nAE notes: good fit for Hosted API trial; close depends on cost math and simple onboarding templates for batching 
…[truncated]
```

#### #4 `dsid_8d95e02dfe9241b78cf697c0b4921c9b`

```
SparkPlume Marketing Lab

SparkPlume runs a multi-tenant content-generation platform for niche publishers. Workload = high-volume short-form generation (500–1,200 tokens per completion typical), heavy template reuse (good candidate for prefix/KV caching), bursts around newsletter hours. Primary ask: hosted API that can scale with predictable cost and easy self-serve onboarding.
Performance: interactive UI latency ~200-500ms for short completions; batch throughput for bulk jobs. Cost: strict per-campaign budget caps and projection tools. Security: SOC2 evidence, SSO/SAML, audit logs. Features: prefix caching, auto-batching, model variant routing (cheaper fallback), usage analytics per API key.
Lead source: webinar + downloadable prompt templates (marketing kit). Early-stage SMB building a content generation SaaS for small publishers. Key snippets from calls:
- 'We need to generate 10-20 short articles per minute across many templates'
- 'Cost is make-or-break; if tokens blow up we won't convert'
- Interested in automatic prefix caching and batching to reduce per-token spend.
CRM fragments: trial account created, API key provisioned, tried gpt-style and open-model endpoints. Wants mo
…[truncated]
```

#### #5 `dsid_1f2249d75d8c4f9fb387f2d5a9b599e5`

```
SierraFold ProductWorks

Finalize pricing schedule & SOW; align execs (CFO + Head of Product) wk of 2026-03-22; legal to review Dedicated T&C by 2026-03-18.
Legal review of Dedicated T&C (data residency clause)
Budget ramp approval from finance
Clarify burst & overage math vs expected QPS
Validation of model quality regression metrics on 2.7B quantized variant
2026-01-15 — Intro demo (hosted API). AE demo'd streaming + embeddings; product team liked latency.
2026-02-01 — POC kick-off (hosted API). 4-week test: support flows + search reranking.
2026-02-20 — Perf bench results. Avg latency 120ms for chat v.s. SLA target 100ms; embeddings within target.
2026-02-25 — Discussed Dedicated. Customer asked about reserved GPU equivalent, burst windows, and ramp schedule.
2026-03-05 — Pricing discussion (call). AE presented two commit tiers: 6-month ramp vs 12-month lock. Customer prefers 12-month with 3-month ramp.
2026-03-08 — Legal & Security questionnaire submitted (SAML, SOC2, KMS, retention windows).
2026-03-10 — Exec alignment call with Head of Product; requested formal pricing matrix and SOW.
Lead: Head of Product = Maya Chen (strong technical PM, formerly at Datadog). CTO = Aaron Li
…[truncated]
```

#### #6 `dsid_4ab355f5e3fa460688f3f24f7ad27d60`

```
Runway Inferwise

Origin: inbound from pricing page -> signed up for hosted API free trial.
Primary contact: Priya Desai (CTO) - internal platform owner for support chat.
Workload: user-facing chat + vector-based doc search. Expect steady background embedding traffic + chat bursts during marketing emails.
Traffic profile and targets: steady 10-15 QPS baseline across regions; expected normal peak 60-80 QPS; planned seasonal/campaign spikes up to 350-450 QPS for ~20-30 minutes.
Latency SLO: 95th <= 200ms for short replies (client-side acceptable up to 300ms if burst queued).
Cost sensitivity: moderate. Want to avoid overprovisioning; prefer smart batching and short KV cache TTLs to reduce token usage.
Rate-limiting concerns (from call): CTO quote - "We can tolerate a few throttled admin calls, but customer-facing chat hitting 429s during flash sales is a showstopper."
Requested features/examples: per-route quotas, per-key concurrency limits, burst allowance (token-bucket style) for short spikes, clear rate-limit headers, documented retry/backoff best practices and idempotency guidance.
Specific asks for SE: sample quota config for 0-60 QPS baseline + 5m burst to 400 QPS; expected beh
…[truncated]
```

#### #7 `dsid_d65ee44630bc41e690542da2d87fcf89`

```
SparrowBurst Systems

Inbound SMB lead via docs widget. Self-serve trial started 2026-02-20. Key ask: how does Redwood handle traffic spikes, 429s, and temporary concurrency increases for flash sales. They run a merchant chat widget that sees sharp traffic during promotions (10x baseline). Concerned about conversion loss if users hit 429s. Cost-sensitive: wants predictable burst billing and a simple fallback story.

Call 2026-02-25 w/ CTO + Eng lead: discussed default quotas, per-key concurrency, and soft vs hard 429s. We demoed exponential backoff advice and suggested route-level rate limiting. CTO: "If our chat starts returning 429s during promo peaks we lose trust — need safe fallback to degraded flow, not outage."

Technical asks: transient quota lift API, real-time quota monitoring, per-route SLOs, token-based cost forecast for 48-72 hour spike. Prefer public cloud hosted API for speed to market. Willing to start on free tier then convert to paid if burst handling works.

AE notes: shipping quickstart for spike-testing; propose temporary burst increase for trial window and provide a sample load script. Legal asked for DPA and minimal retention controls. Scheduling follow-up we
…[truncated]
```

#### #8 `dsid_8072db5171ba4c0eb05debefe16d5262`

```
Verbatimly Marketing Platform

Inbound from content marketing webinar (Nov 4). Signed up for self-serve trial on site; filling initial usage during onboarding. Quick summary:
- 2025-11-04: MQL via webinar signup (requested pricing + latency info).
- 2025-11-06: Automated welcome email + quickstart link.
- 2025-11-12: 30m intro call (Jordan H) — product fit looks promising. Interested in hosted API only for now.
- 2025-11-20: Started trial, running batch generation jobs (templates -> multi-variant outputs).
- 2025-11-25: Submitted short security questionnaire; SOC2 required but not strict SSO right now.
- 2025-11-28: Follow-up call to clarify batching/caching behaviour, cost math.
POC / Requirements notes (from AE convo):
- Primary workload: high-volume template-based generation for customers (multi-variant outputs per template). Expect bursts up to ~1M tokens/day, steady 200-300k tokens/day.
- Latency: not ultra-low — ~400-800ms acceptable for editor flows, but shorter is nice for batch throughput.
- Cost sensitivity: critical. Need per-token cost comparison and recommendations (quantization, batching, cache TTLs). Keeping unit cost < $0.0006/token is target (customer calc).
- Cach
…[truncated]
```

#### #9 `dsid_73c78b2ba4f94c8ca693978422ad296a`

```
Larksong Systems

Summary: Larksong (consumer ecommerce platform) evaluating Redwood Dedicated for real-time personalization and search reranking. Primary drivers: consistent p95 latency <120ms, predictable per-month spend, and ability to pin model versions. Asked us to model 12-month reserved commitments with 3 ramp profiles (conservative/moderate/aggressive).

From CTO: "We need deterministic tail latency during sales peaks — cannot have >200ms p95 for recommendation endpoints."

SE notes: current infra uses GPU instances but suffers from cold-starts and uneven batching. They like Redwood's KV caching + routing. Security requires SSO + audit logs + customer-managed KMS.

Procurement: focused on commit levels and break/fallback clauses. Wants pricing per-GPU and example unit economics per 1M tokens for their workload.

Action items: send revised TCO with utilization sensitivity, include quota/fallback language for SLA, provide SOC2 evidence and KMS architecture diagram.
Primary: online personalization (recommendation rerank) + search rerank. Typical request: 2-4 candidate passages (avg 64 tokens generated). Peak traffic: 25k reqs/min (steady: 6-8k reqs/min). Latency SLO: p95 <120m
…[truncated]
```

#### #10 `dsid_e7afaaeaeb2f46619c64a33dd14200c1`

```
Strandly Marketing Systems

AE notes: customer is a mid-size marketing automation vendor building content-generation features for SMB customers. Primary ask: a frictionless self-serve flow so their product teams can prototype. Quote from founder: 'If the trial shows 30-40% savings on token spend via caching and batching, we'll convert.' SE notes: wants a short example config for prefix caching and a cost comparison (hosted_api, single-region). They are open to using open models only. Security team requested SOC2 + SSO doc; provided Security-FAQ link. Pricing sensitivity repeatedly emphasized. Quick wins: trial credits, sample batching config, short benchmark showing tokens/sec and $/1000tokens. Next AE action: send sandbox creds + templated caching guide and invite for a 30-min POC session.
workload: high-volume content generation (campaign variants, blog batches, ad copy)
latency_target: batch jobs tolerant (1-3s), personalization endpoints target <200ms
throughput_target: peaks of 50-200 rps for personalization; 10k+ tokens/min for nightly batches
cost_sensitivity: high — primary decision driver; exploring caching, batching, and lower-precision model profiles
model_preferences: p
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 39: `qst_0224::semantic` · N=75000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are on-topic for data handling and privacy but do not address the specific question about replacing email addresses with identifiers in documentation. The gold chunk is relevant and non-empty, discussing the use of 'actor_id' instead of 'user_email'.

### Question

In the public documentation for searching system activity records, what identifier should examples use instead of showing a persons email address to avoid exposing sensitive personal data?

### Gold document(s)

#### GOLD `dsid_96088536cbcc449eb676e94bf800486a`

```
docs

jess-docs: FYI I opened a docs PR updating the audit-log query examples and the SDK snippets. PR: https://github.com/redwood-inference/docs/pull/4199. Found a broken anchor in the 'audit event fields' section that the old link points to. Can legal + security skim the query examples for bad phrasing or accidental PII exposure?

elaine: looking now. The Python query example looks fine but we should provide a Go snippet for customers using our Go SDK. Also re: examples that reference "user_email" we should switch to "actor_id" to avoid showing emails in docs.

compliance_rob: quick note from compliance: avoid enumerating concrete PII examples like SSN/credit card in the public docs. Use placeholders: {PERSONAL_ID}, {FINANCIAL_TOKEN}. Also change the word "PII" to "sensitive_personal_data" in the readability guide.

sec_ari: security: good catch on actor_id. Also add a short paragraph explaining that query results may contain tenant identifiers and that customers should limit query permissions (RBAC) to audit:search. We should call out tokenization: prefer tokenized_actor_id in examples.

jess-docs: noted. I'll convert examples to use tokenized_actor_id and add an RBAC snippet. Also will add a Go SDK example showing streaming query results.

ops-rita: small ops nit: the CLI export sample in the PR uses --kms-key placeholder but no example ARN. Please use an example like arn:aws:kms:us-west-2:123456789012:key/abcd-ef01 and show how to copy the exported bundle to a customer bucket with aws s3 cp and a presigned URL.

jess-docs: added the ARN example and an aws s3 cp line. Also noticed the link that was failing: the docs anchor changed from #audit-event-fields to #audit-event-attributes which caused the broken link in the migration guide. Fixed the link and added a redirect anchor note.

docs-bot: PR #4199 7 checks: failing  broken-link-checker 

jess-docs: right, the broken-link-checker flagged one internal reference. I pushed a tiny patch to align the anchor text and updated the TOC.

compliance_rob: wording pass from compliance with one change: in the retention table replace "indefinite" with "customer-managed (no default)" for Private deployments. Hosted defa
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_34fdaca05c5a4b9e993acc4d874410f2`

```
Temporary restricted query access to raw inference traces for security investigation

Issue summary: Security team requests time-limited, read-only access to raw inference traces (logs + input/output tokens) in prod to investigate a suspected information disclosure reported by a customer incident.

Impact: Investigation required to determine scope of potential data exposure. Access must be tightly scoped to a small set of traces, instrumented with full audit logs, and approved by Legal and Privacy before any retrieval. Incorrect handling could cause non-compliance with our data handling policies or contractual obligations for enterprise customers.

Request details: Provide a temporary IAM role or short-lived signed URL that allows Security engineers to run restricted queries against the logging store for trace IDs matching: trace_id in ["tr-20260312-8f4c3","tr-20260313-a1b2c"] and customer_id = "cust-9482". Time window: 2026-03-11T00:00:00Z through 2026-03-13T23:59:59Z. Output must be redacted for any full PII tokens and must not be exported outside the approved investigation VM.

Compliance constraints: Must retain an immutable audit trail (who, when, query), record the exact data
…[truncated]
```

#### #2 `dsid_b107a80048a3416399f3035a2a212897`

```
Stage-gated anonymized session extract for regulatory data correction request (Acme Health)

Issue summary:
Customer (Acme Health, enterprise) requests a timebound extract of inference session records to support a regulatory data-correction request. They provided a list of session IDs and example timestamps and need a small, anonymized snapshot to validate corrected patient identifiers in their records.

Impact:
- Customer cannot complete regulatory filing without sample outputs.
- High-priority: regulatory timeline driven (HIPAA-equivalent process in customer region).
- Access must be tightly scoped and auditable.

Environment:
- Production inference traces for requests routed through the hosted Redwood API in us-east-1.
- Affected models: redwood-base-7B and redwood-internal-13B-v2.

Request details:
- Provide anonymized session-level extracts for 28 session IDs (provided in secure spreadsheet).
- Include request metadata (timestamp, model, route, latency buckets) and redacted request/response text.
- Redaction rules: remove or tokenize any 1) direct identifiers (names, SSNs, MRNs), 2) free-text patient notes; preserve structural markers (e.g., [PATIENT_NAME]) to allow Acme to ve
…[truncated]
```

#### #3 `dsid_f8188e8b6fea41d6b75280a3448e4a7c`

```
Time-boxed access to de-identified inference snippets for privacy validation of new redaction rules

Issue summary:
Request from Applied ML (privacy team) for a short, auditable access window to a small, de-identified set of inference input/output pairs to validate a new automatic redaction transform.

Impact:
- Low production risk if handled per controls below, but the validation must use live workload distributions to catch edge-cases.
- Customer data sensitivity: potential PII in free-text prompts; must ensure strong redaction and minimal exposure.

Environment:
- Production inference traces (us-east) sampled during business hours for the past 72 hours.

Request details / Scope:
- Provide up to 250 inference records (input + output) containing examples where the new redaction logic triggered or was expected to trigger.
- Records must be de-identified using the approved pipeline: token-level masking, email/SSN regex scrub, and hash-only user/session IDs.
- Timebox: access for 48 hours from provisioning. After that, copies must be destroyed and S3 artifacts permanently deleted.
- Consumers: Applied ML (aisha.patel@redwood.com), Privacy Review (tbd), and one engineer from serving-r
…[truncated]
```

#### #4 `dsid_9720935431c34e4b8ec4bbf19058ac10`

```
Temporary re-identification proof for regression analysis

Issue summary: Request a minimal, verifiable re-identification proof to validate a regression flagged by fraud-detection models. Background: On 2026-03-10 our anomaly detector surfaced a spike in false-negative fraud signals tied to a small subset of customer sessions. The investigation team needs to confirm whether two sampled hashed identifiers correspond to the same internal account to rule out model-label drift before rolling back a recent change. Purpose: provide cryptographically-limited re-identification confirmation (yes/no match) for 2 hashed keys without exposing plaintext customer data. This is strictly timeboxed and must follow data minimization controls.
Investigation is blocked; risk of incorrect rollback affecting ~0.2% of live inference traffic. Without the proof, an emergency rollback may be requested leading to increased latency for Dedicated customers and potential billing reconciliation work.
Prod inference logs (sharded), us-east serving cluster; affected time window 2026-03-09T23:00 to 2026-03-10T04:00 UTC. Keys in question: hk_3f7a2e and hk_9c1b4d (hashed identifiers).
1) Run the fraud-detector job fo
…[truncated]
```

#### #5 `dsid_54f31ab02427447a9920f9c6004c00a9`

```
eng-security

maria: Quick sanity check needed — MercuryBank sent a security questionnaire asking for details on our logging/redaction + who can access logs. Draft answer below, want to make sure I'm not overstating anything before I return to them.

maria: Draft excerpt for SQ: "We do not retain raw user prompts or PII in logs. Our ingestion pipeline redacts email addresses, payment tokens, SSNs, and full prompt_text fields before persistence. Logs are encrypted at rest and access-controlled; only authorized SRE and security roles have time-limited access. Subprocessors that receive aggregated metrics or masked logs are listed in our subprocessor inventory."

maria: Example log we were asked to justify redaction on:
```
INFO user=12345 action=completion prompt_text="Transfer $500 to john@example.com confirm?" model=gpt-4x
```

tim: That draft is okay but be explicit that `prompt_text` is redacted at ingest. We hash `user` IDs for debugging traces, we never store cleartext emails or financial tokens. Also mention that debug dumps require an access approval and are audited.

ashley: +1. For the SQ I'd write: we perform field-level redaction (email, phone, ssn, payment_token, prompt_
…[truncated]
```

#### #6 `dsid_5ae902af66af4638b1f7599937e6ae5a`

```
Timebound credentialed replay sampler access for data subpoena response

Issue summary: Legal has received a civil subpoena requesting a narrow set of customer transcripts tied to a specific account for calendar year 2025. Legal requests a timeboxed credentialed access path so we can produce pseudonymized replay traces required for evidence.

Impact: Controlled internal access only. Data contains potentially sensitive PII in user prompts; exposure risk if full raw payloads are shared. Request must satisfy legal chain-of-custody and minimize re-identification risk.

Requestor: Legal (N. Chen), Case ID: SUBP-2026-014; Customer account hash: acct_0x9bfc (lawyer provided full account identifier internally).

Data needed: Selective replayable traces for matching session IDs between 2025-01-01 and 2025-12-31. Each trace should include timestamps, request/response token counts, model version, and redacted/pseudonymized request text where identifiers are replaced with consistent tokens (e.g., <PERSON_1>, <EMAIL_1>). The legal team specifically requests the request/response sequence in a format suitable for evidence review (CSV + gzipped JSONL) and a short provenance report describing how p
…[truncated]
```

#### #7 `dsid_8227309d1f954048b6690aef8454daa3`

```
Request: canonical access journal reconciliation & export packaging for SIG

From: Compliance Team <compliance@healthgrid.com>\nTo: Ben Carter <ben.carter@redwood.ai>\nCc: audits@thirdparty.com\nDate: Fri, 28 Aug 2026 09:12:00 -0700\nSubject: Request: canonical access journal + examples for SIG questionnaire\n\nBen —\n\nAs part of our SIG review we need to validate how Redwood affords an \"access journal\" for privileged operations and admin activity. Specifically HealthGrid's audit team would like:\n\n- A concise definition of which admin actions are captured (console, API, operator runbooks).\n- A 24‑hour sample extract (CSV) that shows schema, timezone normalization, and any hashed PII fields.\n- The routing and export options (S3 signed upload, HTTPS delivery, or secure Drive share).\n- The retention/TTL policy and a canonical checksum-based manifest for delivered bundles.\n\nCan you confirm feasibility and an ETA for a signed sample bundle? If useful please include a short README describing redaction and deterministic sampling.\n\nThanks,\nMarta Alvarez\nHead of Compliance, HealthGrid\n---\nAttachment (requested): sample schema / expected column list\n
From: Ben Carter <ben.ca
…[truncated]
```

#### #8 `dsid_79de123d71494a34b5e924d4252aba7d`

```
Approval request: timeboxed obfuscated session handoff to Privacy triage for customer incident

Issue summary: Request for short-lived, obfuscated session handoff from Support to Privacy Triage to investigate a suspected customer PII exposure during a streaming session in prod.

Impact: Low-volume event affecting 2 customer sessions across us-west; customer has reported redacted snippet that may include a token-like string. No confirmed exfiltration; request is precautionary to validate redaction patterns and confirm no downstream storage.

Justification: Privacy team needs targeted session context (only first 200 tokens of each session plus metadata) to validate redaction rules and confirm whether post-processing stored any sensitive fragments. Support already attempted local redaction and sampling but requires Privacy engineers to run pattern checks and replay in a sandbox.

Access requested: Two obfuscated session snapshots (session IDs provided), each reduced to first 200 tokens, all user-provided free-text replaced with salted hash except token-like strings left for pattern analysis. No API keys, no full raw traces. Access window: 6 hours.

Duration and scope: 2026-03-14 09:00
…[truncated]
```

#### #9 `dsid_ee4bbadb32f14a57a022161e7a3183eb`

```
Tenant-aware SIEM entity crosswalk, deterministic pseudonymization, CSV deliverable and security evidence bundle

Issue summary: Customer requests a nightly CSV deliverable that contains a tenant-scoped SIEM event crosswalk mapping original user identifiers to deterministic pseudonyms. Impact: Compliance deadline for financial regulator in 7 days; customer cannot proceed with audit without deliverable. Environment: Redwood Private VPC deployment in us-east with dedicated audit-export pipeline.

They need: 1) per-event CSV with columns (event_timestamp, tenant_id, original_id_hash, pseudo_id, event_type, payload_reference) 2) deterministic pseudonymization algorithm (HMAC-SHA256 with tenant-specific salt) with rotatable KEK, 3) signed delivery manifest with RFC3161 timestamps and SHA256 checksums, 4) SFTP drop with presigned object-lock and retention metadata, 5) a short security evidence bundle describing cryptographic controls, KMS key lifecycle, and sample pseudonymization code snippet.
Customer ran on-demand export job via Console -> Exports -> New Export using 'tenant=maplebank' and 'window=2026-03-09T00:00:00Z/2026-03-09T23:59:59Z'
Export job completed but CSV contained unhash
…[truncated]
```

#### #10 `dsid_da17037e340a474b947c88433b6eeb28`

```
Scoped approval: audit-gated snapshot of pseudonymized request traces for replay investigation (enterprise customer)

Issue summary:
Requesting time-limited, strictly-scoped access to a small snapshot of request metadata and pseudonymized payloads to perform a deterministic replay for an enterprise customer (AcmeHealth). The replay is needed to reproduce a sequence of model completions that diverge from expected behavior in production.

Impact:
- Customer is reporting incorrect or malformed SOAP-like responses from the model for a paid integration.
- Investigation cannot progress without a minimal set of request traces that include request IDs, pinned model version, tokenized length, and anonymized input text.

Data requested (minimal scope):
1) 100 request trace records from 2026-03-09 00:00 to 2026-03-11 23:59 UTC selected by request_id prefix filter supplied by customer.
2) For each record: request_id, model_version, route, timestamp, sequence_length, pseudonymized_input (named-entity masked), and response hash.
3) Associated gateway TLS metadata (only headers necessary to correlate routing) for the same request_ids.

Justification:
- Deterministic replay is required to root-cau
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 40: `qst_0234::semantic` · N=40000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the topic of rollout and traffic ramp schedules, but they do not match the specific expected document ID. The failure mode is likely an embedding near miss due to the semantic similarity but lack of exact ID match.

### Question

During the rollout of the new version of our inference cost optimizer, what is the suggested traffic ramp schedule for moving from a small canary to full production, including the minimum stabilization wait between increases?

### Gold document(s)

#### GOLD `dsid_ad58457891774bd7ba480e0bcd13df3a`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_0084c60e481b426d9810bd95581e7cd7`

```
introduce-adaptive-warmup-probe-and-traffic-rampup-sentinel-for-canary-orchestrator

Context: We observed sporadic canary regressions that correlate with cold-start and rapid traffic shifts during cutovers. Existing canary probes assume a stationary request distribution and immediate eligibility to evaluate new revisions, which increases false positives and noisy rollbacks for stateful or large-model deployments. Goal: Reduce spurious canary failures by delaying evaluation until the candidate pool is warmed and by ramping traffic in a traffic-aware, variance-sensitive schedule. Design: 1) Adaptive Warmup Probe: new probe that watches tail latency and token-per-request variance during an initial warmup window. The probe computes a dynamic warmup duration based on observed variance and historical warmup profiles for the model family. Warmup probe outputs: "ready" | "warming" | "failed-warmup" and exposes confidence score. 2) Traffic Rampup Sentinel: integrates with the canary traffic scheduler to enforce a configurable ramp sequence (percentiles -> steady-state) that is shaped by live throughput and latency signals. If warmup remains "warming" beyond a threshold, the sentinel will pa
…[truncated]
```

#### #2 `dsid_af5a00d697a84f3db1d3503eef66b055`

```
Microphase release conductor: slate, observability notes, and quick rollback

Working notes and compact checklist for a microphase (small-cohort) rollout of the model-routing update + deployment of the request-batching tweak. Includes an hourly watchlist, signal thresholds, smoke test scripts, and a skeletal release notes draft for product comms.
Deploy model-routing v2.3 with updated fallback policy (region-first then cost-tier) to 5% of traffic for 4 hours
Roll out continuous batching tweak to serving runtime on canary pool to reduce p99 token latency by ~7%
Validate telemetry and automatic fallback paths; ensure no regression to customer-facing latency SLOs
Produce short release note for product and customer success summarizing change and known caveats
Merge approval: runtime PR #2187 has 2 approvals and green CI
Integration smoke: local end-to-end test run passing (e2e-smoke-v2)
Canary pool health: baseline CPU/GPU utilization and KV-cache hit rates recorded at t-24h
Config pin: model-routing config saved as routing/v2.3 pinned for canary tenants
Backout artifacts prepared: previous model-routing config and runtime image tagged: runtime:v2.2-rollback-ready
Pager and on-call: re
…[truncated]
```

#### #3 `dsid_162a23cfbbe64f50abb0e8cd5e34c023`

```
traffic-conditional throughput confidence fence and hysteresis rollback policy

Adds a traffic-conditioned throughput confidence fence for canaries; introduces hysteresis-driven rollback budget and dashboarding for throughput SLOs.
Context and motivation: We observed false-positive throughput regressions during short-lived traffic bursts and cross-tenant traffic spikes when running canaries. This PR introduces a traffic-conditional throughput confidence fence: a statistical estimator that normalizes throughput delta signals by recent traffic modality and owns a hysteresis rollback budget so transient spikes do not immediately trigger rollbacks. The feature is intended to reduce noisy canary failures while keeping the fail-fast property for sustained regressions. Implementation summary: 1) Introduced a lightweight traffic-modality classifier that tags windows as steady, bursty, or ramping based on rate derivatives and per-cohort heatmaps. 2) Added a Bayesian throughput delta estimator that conditions on modality and produces a calibrated confidence interval for observed throughput change. 3) Implemented a hysteresis-backed rollback budget: the fence exposes a budget that decays with
…[truncated]
```

#### #4 `dsid_9f02944542c24e8ca28be216bc0e5665`

```
Canary Playtest & KPI Lighthouse — Go/No-Go Workbook

Working workbook for a phased canary + playtest approach to validate rollout KPIs (latency, cost per request, error rate, quality regression) across host/dedicated/private deployments. Includes simulated traffic profiles, lightweight analysis heuristics for go/no-go, and a condensed checklist for on-call and product owners.
Simulate production traffic with 3 load profiles (low, baseline, spike)
Measure per-route latency P50/P95/P99 and cost/token across model variants
Detect quality regressions using canary eval prompt set
Provide deterministic go/no-go rules for phased rollouts
Latency_ms: observed median and tail latencies for 90s windows
Cost_per_1k_requests: estimate including GPU vs fallback routing
Error_rate_pct: client-facing 4xx/5xx and internal inference failures
Quality_regression_score: percent of prompts with degraded rating >= threshold
P50_latency_ms <= 150 (green), 150-250 (amber), >250 (red)
P95_latency_ms <= 350 (green), 350-600 (amber), >600 (red)
Error_rate_pct <= 0.5% (green), 0.5%-1.5% (amber), >1.5% (red)
Quality_regression_score <= 2% failures (green), 2%-5% (amber), >5% (red)
low: 10 rps sustained, 10% b
…[truncated]
```

#### #5 `dsid_d7d4834102c44a4a8c154cd192757da9`

```
Model serving rollout readiness + KPI escalation ladder

Operational checklist and KPI ladder for rolling out new model-serving configurations (quantization + batching changes) to hosted and dedicated customers. Focuses on launch readiness gates, measurable KPIs (latency, token burn rate, cache hit, fallback ratio), and a three-step escalation ladder tied to SLA & cost impact.
Applies to any rollout that changes the inference execution path: kernel changes, quantization profile swaps, batching policy adjustments, or model variant replacements. Excludes purely client-side SDK updates or Console UI-only changes.
1) Safety and correctness: unit/integration tests, regen prompt set pass rate >= 98%
2) Performance baseline: canary latency and throughput validated against baseline traffic shape (90th P95 latency delta <= +15% for P50 and P95)
3) Cost & capacity: simulated token burn and GPU slot occupancy modeled for expected peak; < 12% buffer required for autoscale policies
4) Observability: dashboards, alerts, trace sampling, and postmortem templates created
5) Rollback playbook: verified rollback build, DB/metadata compatibility confirmed, canary revert time measured < 15 minutes
Late
…[truncated]
```

#### #6 `dsid_a66baf012dc248a49ccdd0e9ff14d6e5`

```
Introduce traffic-conditioned stability sieve for rollout guards

Motivation: Reduce noisy rollback triggers caused by transient traffic composition shifts during canaries. We observed multiple false-positive canary failures when a small cohort of high-latency traffic (e.g., long-context batched requests or heavy re-ranking paths) temporarily increased the metric variance. This PR implements a traffic-conditioned stability sieve that (1) segments traffic by configurable attributes (route, request shape, sequence length bucket, customer tier), (2) computes per-cohort stability scores using an adaptive quantile ensemble, and (3) fuses cohort signals with global detectors to produce a conservative rollout gate.
Design: - Traffic partitioner: lightweight sampling-based partitioning upstream of the canary evaluator.
- Cohort detectors: run percentile- and bootstrap-based checks per cohort to detect sustained degradation.
- Sieve fusion: weights cohort alerts by statistical significance and traffic volume; small noisy cohorts are downweighted to avoid overreaction.
- Backfill & warmup: the sieve warms with a short sampling window (configurable) and supports backfill from historical telem
…[truncated]
```

#### #7 `dsid_ef0efd89151944dc91bbd43d90d094ce`

```
Progressive-traffic experiment playbook with quality-score gates and automated rollback

Purpose: Provide a repeatable playbook for running progressive-traffic experiments for new inference-serving changes (model variants, kernel schedulers, batching strategies) that prioritizes user-facing quality while controlling cost and latency. This ticket captures milestones for canary windows, evaluation criteria, automated gating, and the incident rollback path. The playbook is intended for PM + Eng + Design collaborative execution and should be used as the default for any A/B or canary rollout touching production traffic.
Primary quality metric defined with baseline and target delta (e.g., end-to-end task success rate or BLEU/ROUGE proxy for structured outputs)
Canary and ramp windows specified with sample sizes and minimum traffic per window
Automated metric checks implemented in the CI/ops pipeline that can pause or rollback the rollout if thresholds are breached
Dashboards and alerting (Slack + Pager) configured for primary, latency, and cost signals
Post-launch evaluation doc and retrospective template created and scheduled
Use sampled prod traffic with deterministic sampling key to e
…[truncated]
```

#### #8 `dsid_b16eb801dbc741558b841c7c3047e98d`

```
Rollout economics prioritization checklist and calendar — 2026 WIP

Purpose
---
This is a working note for the release engineering + product + infra conversation about how we prioritize rollout lanes based on economics (cost-per-token, tail latency exposure, reserved vs burst capacity), not just feature rollouts. Goal is a compact checklist and 4-week rollout calendar to make decisions predictable and measurable.

Status/context
---
- Branch: release/2026-q4-economics-tuning.
- This doc is intentionally opinionated: it treats cost and latency trade-offs as first-class gating signals for canary progression.
- Intended audience: release-engineering, infra-capacity, product-hosted-api, SRE, solutions-eng.

High-level heuristic (one-liner)
---
Advance a lane only when: observed correctness and latency SLOs are green in canary AND the measured marginal unit-cost delta is within the agreed threshold (<= +12% for experimental quantizations, <= +5% for model swaps). If either fails, hold and run targeted mitigations.

Key definitions (for this doc)
---
- Marginal unit-cost: additional cost per 1k tokens attributable to the change (measured against a 7-day baseline).
- Latency SLO: 95th per
…[truncated]
```

#### #9 `dsid_d860b38467164897a12689e77a689d5b`

```
Roll-forward/Haltable Canary for Optimize Recommendation Enactment

Background: The Optimize pipeline generates batching and KV-cache configuration recommendations to lower per-token cost. We need a safe enactment mechanism that can apply these recommendations automatically while giving operators an immediate halt/rollback control and ensuring detectable regressions trigger an automated pause. This ticket implements a 'roll-forward/haltable' canary that applies changes to a small traffic slice, monitors key health metrics and cost, and expands or halts based on thresholds.

Goals and scope: Implement a controllable canary controller and operator UI hooks that allow:
- staged application: traffic slices (1%, 5%, 20%) with time windows
- programmable success criteria: latency P95, error rate, quality regression signal (eval set pass rate), unit cost delta
- automatic pause and rollback on threshold breaches with human-in-the-loop resumption
- audit logging for every automated apply/rollback and operator action
- safe defaults and opt-out per-customer

Architecture notes: Introduce a Canary Controller in the rollout service that coordinates:
- dry-run simulation (cost estimate) and va
…[truncated]
```

#### #10 `dsid_a2fce6c2cdea4418952592e91372fd6b`

```
eng-releases

deploy-bot: Post-deploy smoke started for release v2.14.3 (canary=3/5) in eu-west-1. Checks: /health, kv-cache-probe, synthetic-embed. Summary: /health 200 (42ms). kv-cache-probe FAIL (p90=4.2s). synthetic-embed latency elevated (2.3s vs baseline 150ms).

cheng: seeing same in grafana — KV fanout spikes coincide with canary traffic at 19:12 UTC. looks like a cache miss storm after instance rotation.

sam: copying logs from inference-api-42: `grep "kv_fetch" /var/log/inference/requests.log | tail -n 50` shows a lot of `cache_miss=true` entries and backlog growing.

ana: @cheng can you pull the canary routing %? I want to see traffic ramp.

cheng: canary routing is at 20% to v2.14.3 for eu-west shards (was scheduled ramp). we moved to 20% at 19:10.

sam: small excerpt of logs:
```
2026-03-19T19:12:31Z inference-api-42 kv_fetch id=abc123 miss=true backend_latency=210ms
2026-03-19T19:12:31Z inference-api-43 kv_fetch id=abc456 miss=true backend_latency=4.1s
2026-03-19T19:12:32Z inference-api-42 synth_embed id=abc123 latency=2370ms
```

riyad: hypothesis: new model variant v2.14.3 changed tokenization prefetch pattern -> larger KV footprint -> cold cache -> fanout latency. 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 41: `qst_0234::semantic` · N=100000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to deployment and rollout strategies but do not specifically address the question about the traffic ramp schedule and stabilization wait times. The failure mode is lexical mismatch due to the absence of the expected document in the retrieved set. The chunk quality is decent but not directly on-topic for the specific question asked.

### Question

During the rollout of the new version of our inference cost optimizer, what is the suggested traffic ramp schedule for moving from a small canary to full production, including the minimum stabilization wait between increases?

### Gold document(s)

#### GOLD `dsid_ad58457891774bd7ba480e0bcd13df3a`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_0f05d12854974e1e8ab599b93cf46efe`

```
Canary Scheduler: Cost-Aware Deployment & Rollback Design Spec

Design for a Canary Scheduler that balances deployment safety with runtime economics by dynamically adjusting canary traffic, model variants, and rollback thresholds based on real-time cost and SLO signals.
Overview

This design spec defines the Canary Scheduler: a control-plane component of Redwood that manages staged rollouts of model variants and runtime configuration with explicit cost-awareness. The scheduler’s goal is to maximize safe throughput delivered to customers while minimizing per-token runtime cost and reducing unnecessary full-rollbacks. It tightly integrates with observability, Optimize recommendations, and the routing layer.

Key objectives

- Make canary rollouts safer by incorporating cost signals alongside latency/error SLOs.
- Reduce unnecessary escalation to full rollback by enabling traffic diversion to cheaper compatible variants when quality is acceptable.
- Provide transparent, auditable decision logs and guardrails for commercial and compliance review.
- Enable rapid automated rollback or safe ramp-up when signals meet defined policies.

Scope and non-goals

- In scope: hosted and dedicated 
…[truncated]
```

#### #2 `dsid_39628c72e38a452689606754ee5616de`

```
Model Promotion: Canary, Chaos and Load Validation Protocol

This document defines the canonical protocol for promoting a candidate model from staging to production in Redwood inference environments. The protocol combines canary traffic validation, targeted chaos experiments, and load-scaling verification to ensure models meet functional, performance, cost, and robustness requirements before full promotion.
Provide a repeatable, auditable process that reduces risk when rolling out new model versions across Hosted, Dedicated, and Private deployments. Ensure compatibility with quantized artifacts, KV-cache behavior, and downstream prompt sets and metrics used by product features.
Applies to all model promotions handled by the Model Onboarding and Serving teams: text generation and chat models, embedding variants, and quantized model builds. Does NOT replace safety evaluations or legal/compliance checks (those must be completed separately).
Candidate model: the specific model artifact/weight bundle being promoted. Canary cohort: a small percentage of production traffic routed to the candidate. Chaos test: deliberate fault injection into dependencies or resources (network latency, GPU 
…[truncated]
```

#### #3 `dsid_40eb3865fec54d00acf0d86f192151a5`

```
Mixed-workload scheduler prototype — rollout runbook

## Purpose
This runbook describes how to safely enable and ramp the mixed-workload scheduler prototype (short/long prompt-aware scheduling) in production pools.

Primary goal: reduce user-visible p95 tail latency (TTFT and end-to-end) under mixed prompt-length distributions without materially regressing throughput or fairness.

This runbook covers:
- Preconditions and required sign-offs
- Feature flag enablement and safe parameter ramps
- Monitoring checklist and known-bad signals
- Rollback procedure
- Owner rotation and escalation

---

## Scope
Applies to runtime version(s) that include the prototype scheduler (currently: runtime-1.18+ candidate builds where the feature flag is present).

In-scope deployment targets:
- Hosted API: a single canary region/pool first (typically us-east)
- Dedicated: a small, opt-in subset of Dedicated GPU pools with mixed-workload symptoms

Out of scope:
- Multi-tenant QoS tier productization
- Broad admission-control redesign (only minimal coupling to existing backpressure)

---

## Definitions (quick)
- **Short vs long class**: request classification based on prompt/context length and/or predi
…[truncated]
```

#### #4 `dsid_2ce26a1937a3405d9d041a48bddf3a61`

```
Canary kernel deployment patterns and health matrix

Overview:

This document defines recommended patterns for deploying new GPU/kernel changes into the runtime using canary and staged rollout strategies, and provides a concise health matrix used to decide promotion, hold, or rollback. It consolidates deployment intents, metric definitions, sampling guidance, alert thresholds, and operational checklists so kernel engineers and SREs have a shared playbook for safe kernel rollouts.

Scope and assumptions:
- Applies to kernel-level changes that affect scheduling, memory management, attention kernels, quantized code paths, and dispatcher logic.
- Targeted at deployments to both hosted and dedicated fleets where traffic is mixed-tenant.
- Assumes pre-built artifacts are versioned (kernel-version, driver-bundle, runtime-image) and feature flags exist for runtime toggles.

Goals and success criteria:
- Detect regressions early with small blast radius.
- Promote backwards-compatible kernels with measurable latency, throughput, and stability improvements or neutral impact.
- Provide deterministic rollback criteria to minimize incident MTTR.

Deployment patterns (with tradeoffs):

1) Small c
…[truncated]
```

#### #5 `dsid_5267cd82c772437fa0f9dd9e9568388b`

```
Hosted rollouts: SLO metrics and alerts (cohort-specific)

## Purpose
This page defines the SLO signals, cohort-specific metrics, and alerting guidance for **Hosted canary rollouts** (percentage-based traffic splitting on Hosted routes).

The goal is to:
- Detect real customer impact quickly (error/latency/timeouts) **per cohort** (baseline vs canary).
- Provide safe defaults for **auto-stop/auto-rollback** wiring without creating alert storms.
- Standardize dashboard panels and queries used during beta and GA.

This page is SRE-owned, but it is intended for product engineers, on-call responders, and support.

## Scope
Applies to:
- **Hosted routes** using the canary rollout workflow.
- Cohort tagging emitted by the data plane and aggregated by telemetry.

Does not cover:
- Dedicated/Private rollouts (separate SLO policy; signals may be similar but dimensions differ).
- Deep quality-eval gates (optional/manual in GA; future automated gates will be a separate doc).

## Definitions
- **Rollout**: A controlled change for a Hosted route that shifts traffic from a baseline config/model version to a canary config/model version.
- **Cohort**: The request classification for metric attribut
…[truncated]
```

#### #6 `dsid_037af0f9e58844e78a524f4a0fe969a9`

```
Canary GPU workload federation and IaC promotion pipeline

Overview:\n\nThis runbook documents the end-to-end process for performing canary federations of GPU inference workloads across regions and for promoting the supporting Terraform/IaC modules and CI/CD artifacts. It ties together three areas that commonly surface flakiness during scale-ups: placement and affinity, egress capacity, and IaC promotion safety checks. Use this playbook for planned canaries and for emergency canary rollbacks when a rollout impacts latency, throughput, or tenant isolation.\n\nGoals:\n- Safely validate that a new runtime/driver/kernel release or a Terraform module change works for multi-region GPU workloads.\n- Limit blast radius by starting with 1–5% production traffic and automated rollback triggers.\n- Ensure IaC artifacts (terraform-module and promote jobs) can be promoted with automated checks and human approvals.\n\nApplicability and scope:\n- Applies to hosted inference clusters (redwood-infer-*) across us-west1, us-east4, eu-west1.\n- Targets changes to: runtime kernel binary, gpu-node image, nvlink/networking config, and placement IaC modules (module/gpu-placement and module/egress-pool).\n-
…[truncated]
```

#### #7 `dsid_53c73fdd8e1c4156af355c91f69f1cc6`

```
Quality Gates and Observability Contract for Feature Rollouts

Overview:\n\nThis design spec defines a product-level \"observability contract\" and set of automated quality gates that must be satisfied before, during, and after feature rollouts in Redwood Inference. The intent is to make rollouts predictable, measurable, and reversible by defining the telemetry, thresholds, dashboards, and automated actions owned by product and platform teams.\n\nGoals:\n- Create a minimal, standardized telemetry contract for any new routing/serving/optimizer feature that impacts production inference (latency, cost, correctness).\n- Define pass/fail quality gates that can be evaluated continuously and used by CI/Release orchestrations and canary controllers.\n- Specify required dashboards, alert rules, and remediation playbooks for failed gates.\n- Provide a clear owner matrix for who implements telemetry, who validates signals, and who executes rollbacks.\n\nNon‑goals:\n- This spec does not mandate implementation detail for instrumentation libraries; it requires observability outputs (metric names, tags, dimensions) and example collectors.\n- It is not a replacement for model quality evals or huma
…[truncated]
```

#### #8 `dsid_e757a2d8d46340cd8805e1f6a04247a6`

```
Runtime Operational Tuning and Triage Playbook

A practical playbook that brings together runtime architecture patterns, kernel-scheduler knobs, profiling procedures, and benchmark guidance to support tuning and regression triage for the inference runtime (v2.8+). Intended for SREs, runtime engineers, and applied ML owners.
Applies to hosted and dedicated clusters using the main runtime image. Excludes driver-level debugging (NVDriver/ROCm internals) and customer-specific VPC networking changes.
- Small models (<512 tokens) p99 <= 50 ms
- Medium models (512-2048) p99 <= 200 ms
- Long sequences (>2048) p99 <= 600 ms
- Cost target: <= 1.5x per-token cost vs baseline quantized profile
- Regression sensitivity: detect +10% p99 or +20% per-token cost change within 3 hours
rt-agent (diagnostics & snapshotting), kernel-scheduler (priority-driven executor v3), perfbench (bench & replay), kvcache-coop (KV cache service), observability (Prometheus, OTLP->Jaeger, Loki)
Workload | Model | Seq len dist | Concurrency | Expected p50 | Expected p99 | Notes
small-chat | llama-7b-q4 | 16/64/128 | 100 qps | ~18ms | ~48ms | baseline small mix
summarization | llama-13b-fp16 | 256/512 | 40 qps | ~120ms 
…[truncated]
```

#### #9 `dsid_5d54ce4fb8dd4774be03775516f1c8bb`

```
SLO deployment gates and capacity safety net

Purpose
This page defines the deployment gating rules and capacity safety-net controls that SRE uses to approve SLO-impacting changes (model swaps, runtime updates, autoscaler changes, quantization/weights changes) for inference services. The intent is to reduce regression risk by combining small, verifiable canary windows with capacity hedges and automated telemetry acceptance criteria.

Scope
- Applies to all production inference clusters: hosted api, dedicated pools, and private clusters managed through Redwood Private control plane.
- Applies to changes that affect request-path latency, availability, or per-token cost (model changes, runtime releases, autoscaler/policy changes, packaging/quantization).

High-level policy
1) Any change that could affect SLOs requires an explicit deployment gate evaluation.
2) Gates are a mix of automated checks (synthetic canaries, telemetry assertions) and human review for high-risk changes.
3) Capacity safety-net must be established before canary start: pre-warmed model replicas, headroom reservation, and burst absorber configured.
4) Automatic rollback triggers are enforced for the canary window; 
…[truncated]
```

#### #10 `dsid_5fc7774b86ff4d6f92c40a2bb5ac8b89`

```
Change-Immune Deploy Patterns for LLM Inference Runtime

Overview

This document describes a set of practical, testable deployment patterns we call "change-immune" for the Redwood LLM inference stack. The goal is to allow safe upgrades (models, kernels, batching logic, routing rules, and adapters) with minimal user-facing regression risk while keeping operator toil low.

We cover patterns that combine contract adapters, shadow validation, staged traffic slices, and automated rollback criteria. These patterns are intended for use by platform engineers, runtime owners, and on-call operators during medium-to-large rollouts (hosted API, Dedicated, and Private).

Why this matters

- LLM serving changes can silently degrade output quality or cost characteristics without traditional error spikes.
- A single model/kernel change can influence prefix-cache behavior, request latency distributions, and multi-tenant fairness.
- Existing canary flows (pure percent-based traffic) are necessary but insufficient for semantic regressions or subtle token-cost regressions.

Patterns summary (high-level)

1) Contracted API Adapters
   - Provide a lightweight, versioned adapter layer between our public 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 42: `qst_0238::semantic` · N=15000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant but do not directly address the specific experimental setup described in the question. The failure mode is likely an embedding near miss, as the retrieved documents discuss related concepts but do not match the specific contrapositive exemplar strategy. The chunk quality is decent, with coherent and on-topic content, but not directly aligned with the

### Question

How should I structure a small prompt experiment to reduce overconfident mistakes by mixing a couple of correct examples with one intentionally wrong example plus an immediate fix, while keeping the total examples very short and tracking things like made-up details and format compliance over a few hundred test prompts?

### Gold document(s)

#### GOLD `dsid_e528bed025b44f71bc37a54f5a9aefcd`

```
Template Contrapositives Workbench

Goal:
Experiment with "contrapositive" training examples and template variants to surface brittle instruction-following behavior and produce guarded templates that reduce silent failures. The idea: instead of only providing positive few-shots (how to do X), explicitly include inverted or wrong examples (how NOT to do X) and add scaffolding prompts that steer the model away from high-risk misinterpretations.

Background / motivation:
- Observed classes of failure in downstream apps where a short instruction is ambiguous and the model confidently returns undesired content (hallucinated facts, policy violations, misformatting).
- Regular few-shot sets improve style/format but do not consistently reduce semantic misinterpretation.
- Hypothesis: providing 1–2 contrapositive exemplars (deliberate bad outputs + short rationale why they are bad) will increase model calibration around the instruction boundaries and reduce brittle generalization.

Quick glossary (informal):
- Contrapositive exemplar: an example pair (instruction -> intentionally bad/incorrect output) annotated with a one-line critique and a corrected output.
- Template smoothing: small natural language scaffolds inserted pre/post-instruction to reduce abrupt generalization leaps.
- Failure probe: a short test input designed to reveal overconfident incorrect behavior.

Design constraints / rules for examples:
- Keep contrapositive exemplars obviously wrong but plausible-sounding (so the model can't treat them as noise).
- Keep critique brief: 6–12 tokens, explicit ("Incorrect because...").
- Follow with a corrected exemplar immediately after to anchor the desired behavior.
- Limit few-shot context to 4 examples total to preserve tokens; try 2 normal + 1 contrapositive + 1 correction ordering.

Micro-experiment matrix (to run on hosted API):
1) Baseline: 0-shot instruction only
2) Std few-shot: 2 positive exemplars
3) Contrapositive: 2 positive + 1 contrapositive + 1 correction (ordering varied)
4) Smoothing: contrapositive set + short scaffold preface ("Do not repeat the mistake in the examples below.")
5) Negative-control: 2 positive + 1 contrapositive but no correction
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_92f56ed27b75455f82f43528f6644f3c`

```
Shot Blending Heuristics — personal scratchpad

Purpose:
This is a lightweight, messy lab notebook for experimenting with 'shot blending' — mixing few-shot exemplars of varying fidelity/length to improve robustness on multi-turn summarization and instruction-following tasks. Goal is to find small, repeatable heuristics that are cheap (<= ~200 tokens per prompt) and that avoid common failure modes (hallucination, instruction drift, token budget blowouts).

Notes / guiding hypotheses:
- Short canonical exemplars (2–3 sentences) often help for clarity but hurt for edge-case coverage. Blending 1 long exemplar + 2 short anchors might combine precision + recall.
- Example ordering matters less than exemplar diversity; but anchored exemplars (explicit "DO" vs "DON'T") reduce polarity errors.
- Weighting via phrasing ("Important: use this format") seems more reliable than positional weighting across models.
- Repetition of the instruction across exemplars reduces stochastic drift over long contexts.

Experimental setups tried (model, temp, window):
- model: open-model-1.3b (quantized) | temp 0.2 | max_ctx 1024 | continuous batching on Redwood dev host
- model: open-model-7b | temp 0.0 | ma
…[truncated]
```

#### #2 `dsid_58396d0a09aa421bbab72f67e955ad23`

```
Latent Prompt Variables Scratchbook

Purpose:
This scratchbook is for exploring the idea that short, consistent 'latent' tokens embedded in prompts can act as compact controllers for style, output length, factual conservatism, and hallucination bias. I want cheap knobs that transfer across models and few-shot sets so product prompts can be shorter and more stable.

Hypotheses (quick):
- H1: A small set of invented tokens (e.g., <L-FRM> for formal, <L-CAS> for casual) will reliably change tone across model families if used in a canonical position early in the prompt.
- H2: Chaining a numeric token (e.g., <L-0>.. <L-5>) can serve as a coarse temperature proxy for generation creativity without touching model params.
- H3: Embedding a short 'fact-check instruction' token <L-FC> before the task will reduce unsupported assertions in long-form answers.

Design notes / primes: (these are intentionally messy)
- Keep tokens 6-8 chars so they don't collide with common words but are short for copy/paste.
- Always place latent tokens at the top with a brief natural-language anchor: "Latent control: <TOKEN>" then a blank line, then instruction. This canonical anchoring reduces variability across
…[truncated]
```

#### #3 `dsid_032a9f67deb945a0a432e9b75785f422`

```
Leftover Prompt Curio Cabinet — hunches & micro-experiments

Context / purpose:\nA running scratchpad for odd prompt variants I keep finding in the wild — small, messy experiments to capture failure modes and promising micro-templates. Not a polished playbook; more a museum of curios and hunch fragments.\n\nTopline observations (quick):\n- Short, high-contrast exemplars often help for style transfer but break on factual consistency (expected).\n- Adding a 1-sentence ‘constraint reminder’ after the few-shot set reduces hallucination in ~30% of tiny samples, but can introduce omission (model over-censors).\n- Templates that use explicit tokens (<<<EX>>) occasionally get the model to repeat those tokens in output — useful for routing but noisy for final text.\n\nNotes-to-self:\n- Keep examples tiny (3–5 tokens in each exemplar) when testing token-budget-sensitive flows.\n- Track prompt length distribution; some bugs only show up at >512 tokens.\n- Save RNG seeds? For now, note timestamp + model + temp + seed when interesting.\n\nExperiment 1 — microtemplate: \"role + goal + constraint\"\nTemplate: [Role instruction]\nGoal: [single-sentence desired outcome]\nConstraint: [one line: what
…[truncated]
```

#### #4 `dsid_455031f4831d48feb5d44d543223101f`

```
Ensemble Prompt Templates Bank

Goal: collect candidate prompt templates and few-shot sets for ensemble experiments. Quick scratchpad rather than formal PRD — keep raw failure notes, weird edge cases, and compact examples to rerun in eval harness.

Context notes:
- Using the hosted API (small latency budget) and Dedicated for heavy evals. Want ensembles that trade token cost for reduced output variance.
- Hypothesis: small targeted diversity (2–5 variants) + reranker reduces hallucination rate on knowledge queries but will increase tokens ~+15–30%.

Experiment buckets (id tags for harness):
E1: Surface-level template variations (instruction phrasing, explicit constraints)
E2: Few-shot exemplar swap (different reasoning chains, more abstract vs concrete examples)
E3: Output-format ensembling (json schema vs bullet list) + post-rerank
E4: Temperature/beam mix ensembles (low-temp consensus + high-temp explorer)

Representative templates (compact):
- Templ-A (concise): "You are a concise technical assistant. Answer in <=3 sentences, include code if helpful."
- Templ-B (step): "You are a helpful analyst. Show step-by-step reasoning and then a final concise answer. Use numbered steps."
-
…[truncated]
```

#### #5 `dsid_bf8681ce9427455299245cb2ee67b4a0`

```
Prompt chaining — error catalog & quick experiments

Purpose:
- Scratchpad: collect concrete failure modes that show up when we chain multiple prompts (planner -> executor -> verifier).
- Surface quick mitigations, small templates, and unit tests to convert into prompt-library entries later.

Context / hypothesis:
- Chaining increases context complexity: mismatch in assumptions between stages leads to drift, hallucination, and truncated state.
- Common patterns: instruction loss, role-drift, token overflow, inconsistent grounding, verifier false-negatives.

Quick experiment notes (local runs, gpt-style open model):
- Setup: 3-step chain: (1) Decompose user intent into steps, (2) Execute step producing structured output, (3) Verify/normalize output.
- Prompt config: 0.2 temperature, stop tokens on END_STEP; batch size 1, 2048 context.
- Observations: many failures occurred at step boundaries — executor assumed implicit defaults from planner.

Concrete failure types + examples
1) Instruction loss / truncation - Symptoms: last steps missing, executor returns partial JSON.
- Example planner output (truncated):
  "STEPS: [1) collect links, 2) summarize, 3) make bullets "
  executor outp
…[truncated]
```

#### #6 `dsid_7a25e9b6949b4b7da4f050661f626990`

```
Shot sentinel sneeze test notes

Quick brain-dump and running log for a small, oddball experiment: 'shot sentinel sneeze' — a lightweight probe to surface brittle few-shot templates across role and exemplar permutations. Purpose is to capture reproducible failure patterns and quick heuristics for building a compact prompt library that degrades gracefully under token pressure.

Background / motivation:
- We keep seeing specific few-shot layouts that pass internal tests but catastrophically fail on short paraphrases or when a cue word is slightly moved. Want a rapid way to generate 'sneeze' perturbations (tiny, cheap changes) to detect brittle exemplar dependencies.
- Goal: build a small corpus of prompt variants + annotated failure cases we can iterate on and eventually feed into Optimize for template ranking.

Experiment setup (notes to self):
- Model: internal dev hosted endpoint (v-hosted-alpha), using 8k context profile, temp=0.6 for fuzz; also run deterministic pass temp=0.0 for binary checks.
- Query types: classification (label extraction), summarization distillation, instruction-following transformation.
- Few-shot bank size: 3 exemplars baseline, alternate runs with 1 and 5
…[truncated]
```

#### #7 `dsid_3d49b09649b941e5998967200b834bea`

```
Microinstruction Misalignment — fieldnotes and quick experiments

Purpose:\nQuick personal notes about a recurring failure mode I keep hitting while assembling few-shot microinstructions into larger prompt templates. Trying to capture patterns, minimal repros, and some tiny countermeasures to test later. This is messy — intended as an ideation + repro log.\n\nBackground / motivation:\n- We frequently stitch tiny directive snippets (microinstructions) into a single prompt in order to get compositional behavior (tone + format + constraints).\n- Observed: when prompts exceed ~220 tokens or contain many short directives, model starts to ignore specific microinstructions (esp. qualifiers like \"only list\" or \"do not\"), or flips ordering.\n- Hypothesis: token budget + attention dilution + incompatible framing (imperative vs. descriptive) cause misalignment. Also occasional stochastic anchoring to last few-shot example instead of instruction header.\n\nKey failure patterns (examples):\n1) Instruction drop: model omits a required field when multiple short instructions are combined.\n   - Prompt snippet: \"Write a 3-line product blurb. Use bullet points. Do not include pricing. Keep lang
…[truncated]
```

#### #8 `dsid_0f3b9705709c4c949ec53ae2f3d27190`

```
Macroshot template garden — few-shot and failure probes (scratchpad)

Quick intent: build a compact set of macro-shot templates (macroshots) that generalize across tabular QA, short-summarization, and roleplay tasks. The idea is to have 3–5 canonical few-shot skeletons + a lightweight failure probe suite to catch brittle edgecases.

Notes to self:
- Macroshot = small, labeled scenario + 2–3 distilled exemplars + explicit output constraints. Keep token budget <= 220 for hosted tests.
- Prioritize: deterministic instruction framing, then example diversity, then negative exemplars.

Working templates (sketches):
1) Instruction-first macroshot (IFM)
- Prompt header: goal + format + constraints (1 line each)
- Examples: 2 positive, 1 counterexample (contrast)
- Final instruction: single-sentence task request

2) Context-anchored macroshot (CAM)
- Header with user persona/context (1–2 lines)
- 3 short exemplars that vary persona tone
- Output schema enforced with JSON tags

3) Chain-of-evidence macroshot (CEM)
- Ask for intermediate reasoning steps (short) then final answer
- Use explicit step headers: [EVIDENCE], [SYNTHESIS], [ANSWER]

Representative few-shot set (for tabular QA):
- Exe
…[truncated]
```

#### #9 `dsid_302e42b1c5be42519f7933c3dd8b9e8f`

```
Counterfactual prompt probe notes

Purpose:
Quick personal scratchpad for probing model sensitivity to counterfactual seeds and minimal-context perturbations. Want small, repeatable experiments to surface brittle behaviors and candidate mitigation templates for prompt library. Keep this messy — ideas I can try in the RETRO session or local eval harness.

High-level hypotheses:
- H1: Short counterfactual anchors (1-2 sentences that assert unlikely facts) change output distribution more than paraphrased innocuous anchors of same length.
- H2: Placing the counterfactual as a system-level preface vs. as an in-context example yields different failure modes (hallucination vs. refusal).
- H3: A single robust instruction template with explicit refusal + example-based negative examples reduces unsafe counterfactual adoption.

Quick experiment matrix (fast runs):
- Models: rwd-13B-v2-opt (int8), rwd-70B-slim, open-70b-quant (for baseline).
- Modes: single-turn generation (stream off), 3-shot fewshot, system-preface + 1-shot.
- Metrics: semantic drift (BLEU-ish to gold), hallucination-rate (manual label on small sample), instruction-adherence score (0-1), top-token entropy shift.

Template ca
…[truncated]
```

#### #10 `dsid_f702ebb6e5cd4a8aa92d9b030723b2eb`

```
Anchorless exemplar curation log

Personal scratchpad for experiments with "anchorless" exemplar sets (no system role header, no explicit instruction anchor). Purpose: see whether curated exemplars alone can reliably steer task framing with fewer tokens and more robustness to instruction perturbation.

Background notes:
- Problem: prompts with large system instructions are verbose and brittle between models/quantized weights.
- Hypothesis: a compact, well-structured exemplar set (3–5 shots) + minimal single-line task tag can achieve comparable behavior while being cheaper and easier to roll out.

Experiment matrix (quick):
- V1: 3 exemplars, varied phrasing, each labeled only by example_output. No system message. Task tag: "summary-v1" on first line.
- V2: 5 exemplars, include adversarial negative example (bad output) to bias away from common failure mode (hallucination).
- V3: dynamic pruning: compute similarity of new input to each exemplar (embedding dot) and drop least similar shot to keep token budget <= 256.

Prompts / templates to try (copyable):
- Template A (anchorless minimal):
  "Task: summary-v1

  Example:
  Input: A long news paragraph about city budget shortfall.
  O
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 43: `qst_0239::semantic` · N=20000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks discuss compliance and security topics relevant to fintech but do not specifically address the compliance items for merchant reconciliation and dispute handling as required by the question. The failure mode is likely an embedding near miss due to thematic overlap but lack of specific content match. The chunk quality is decent but not directly relevant to the question.

### Question

For the fintech prospect doing merchant reconciliation and dispute handling, what are the specific compliance items their ops and security teams said must be in place before moving past the pilot phase?

### Gold document(s)

#### GOLD `dsid_ef492479c7dc4a3c9dd55d6771e5df54`

```
SaltBloom Payments

Lead: SaltBloom is a payments fintech focused on SMB merchant reconciliation and dispute triage. Inbound self-serve signup, ~2 weeks of trial activity. Wants hosted API to start (ease of onboarding) but asked early about VPC for production later.

Key asks / quotes:
- 'We need SOC2 evidence before expanding beyond POC.' — CTO Maya Lin
- 'SSO + audit logs are blockers for our compliance team.' — Head of Ops

Technical: tested embeddings for transaction clustering; reranking for fraud signals; chat assistant for merchant support. Observed: p95 chat latency acceptable on hosted but wants SLA language. Cost is sensitive — projected monthly token spend after scale ~ $12k-18k.

POC plan (proposed): 1) Short technical demo + SSO review (week of 3/15), 2) 2-week POC (embedding + rerank) using hosted API, sample dataset provided by SaltBloom, 3) Security questionnaire + SOC2 pack delivered, 4) Decision on Dedicated/VPC after successful POC and contract review.

Sales notes (fragmented):
- AE touched base 2/20; sent pricing overview + churned example calculators.
- Lina (SE) ran cost opt session 3/9 — suggested batching & quantized model for rerank pipeline.
- Security requested: SOC2 Type II report, SAML SSO flow diagram, KMS integration notes.

Next actions: Upload SOC2 pack to Drive, send SSO setup doc + example SAML metadata, schedule 30m tech demo with Lina. Keep pressure on pricing cap ask; offer Optimize onboarding to reduce unit cost.

Stated blockers: SOC2 evidence, final budget sign-off, VPC validation for enterprise plan (not immediate).
2026-02-15 - inbound signup via pricing page; claimed early credits; experimented with chat + embeddings
2026-02-20 - AE intro email (Jordan); customer asked for SOC2 status and SSO options
2026-03-02 - Discovery call (CTO Maya Lin, Prod lead Tomas) — high-level infra, data flows; wants audit log and KMS integration details
2026-03-04 - Fireflies transcript (ff-2026-03-02-83ef) attached; customer reproduced embedding use-case with sample dataset
2026-03-09 - SE pairing session (Lina) — demoed batching, prefix caching; measured p95 ~320ms for chat on hosted; cost projection created
Send SOC2 + SSO FAQ and hos
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_c87bda7c87f4438596851c844134e017`

```
Northbridge Banking

Workload: chat + RAG (internal), plus summarization (agent assist).

Performance targets (pilot): p95 TTFT <= 350ms (streaming), p95 end-to-end <= 2.5s for ~400-800 output tokens; steady-state 30-60 concurrent users initially, scaling to 300+.

Reliability: needs explicit fallback behavior (model variant/region) disabled by default in regulated mode; change control + rollout policy required.

Security/Compliance: SOC2 report under NDA; encryption in transit + at rest; customer-managed KMS keys; detailed audit logs (who/what/when), export to Splunk; SSO via SAML; configurable retention / log retention guidance; US-only data residency; no training on customer data.

Deployment: Private (VPC) with tight network boundaries; security team requests architecture diagram and ports/egress documentation for approval packet.
vpc (private deployment required). Customer preference: AWS us-east-1 in a dedicated VPC w/ customer-managed KMS; no public internet egress from inference plane.
soc2
audit_logging
kms
sso_saml
retention_controls
data_residency
internal-knowledge-assistant (RAG)
contact-center-agent-assist
policy-and-procedure-summarization
kyc-aml-casework-triage (pi
…[truncated]
```

#### #2 `dsid_4dc77de6649d4e0799648a18290d96b5`

```
BlueCrest Secure Support

Account background: BlueCrest runs payments reconciliation + telehealth billing support for a set of regional clinics and a payments gateway. Heavy PCI + PHI scope; central support org handles escalations and chargeback disputes.

Call highlights (2026-01-15):
- CISO (R. Gomez): "cannot leave payment PANs or PHI in external storage; need KMS + HSM, full audit trail to SIEM."
- Head of Support Ops (L. Chen): looking for agent assist to reduce AHT by 20%, live suggestion latency <150ms, and summarization that produces 3-4 sentence TL;DRs with configurable retention windows.
- Platform Lead (M. Patel): asks for VPC deployment, private control plane, and the ability to pin model versions + automatic fallbacks during capacity events.

Technical constraints / must-haves:
- VPC/private deployment mandatory for POC.
- SAML SSO + SCIM provisioning integrated into Okta.
- Audit logging forwarded to Splunk/SIEM with 90-day hot retention, 7-year cold retention for payment dispute records.
- KMS/HSM integration for envelope encryption; customer will not allow Redwood-managed keys without HSM-backed KMS.
- Tokenization or redaction pipeline for PAN/PHI before model expo
…[truncated]
```

#### #3 `dsid_6db818ee43a94ad88882c91a3fe40491`

```
Axion Guard

Quick summary: Axion Guard is a payment+health fintech (card processing + claims billing) with strict PCI + PHI needs. Wants agent-assist integrated into Salesforce and internal desk ops, automatic ticket summarization, and safe tool-calling (CRM writebacks, refunds). Primary constraint = VPC deployment + customer-managed KMS + immutable audit trail for 7 years. Performance: p50 token latency target <= 120ms, p95 under 300ms during normal load; must sustain bursty spikes up to ~10k concurrent agent events with graceful degradation (fallthrough to cached responses). Pricing sensitivity: moderate — will trade some cost for strong compliance and predictable latency. SE notes: prefer model routing + fallback to smaller quantized variant during spikes; interested in Redwood Optimize suggestions for batching and KV caching. On calls the Head of Ops said: "We cannot expose PHI or full card PANs to hosted multi-tenant services; need VPC/private with audit proof". Current blockers: legal language for retention + KMS attestation, partner data residency proof. Next actions: supply KMS integration guide, run short on-prem smoke test, finish security questionnaire, provide draft SO
…[truncated]
```

#### #4 `dsid_9019af805aa04f7394fb350b6eb679ae`

```
Silverbloom Contact Ops

Summary:
- Mid-size payments platform with embedded customer support for merchant disputes and cardholder inquiries. Heavily regulated: PCI scope + some PHI in billing notes. Must run in VPC with private link to Zendesk and internal data stores.
- Primary goals: real-time agent assist (suggest replies, next-best-action), automated ticket summarization for QA, safe tool-calling (create/close tickets, escalate), and robust behavior during episodic traffic spikes.
Technical / SLOs:
- Target: agent-suggestion latency p95 < 250ms (streaming suggestions preferred), end-to-end reply generation under 800ms.
- Peak concurrency: up to 3k agents during Black Friday-style spikes; average concurrent 600.
- Throughput requirement: sustained 120 requests/sec, bursts to 3k req/sec for short periods.
Model & routing preferences:
- Prefer open models (LLM family) with quantized variants for cost. Want model catalog visibility and verified perf profiles.
- Must support automatic fallback to smaller model variants and routing by cost/latency during saturation.
Security/compliance:
- SSO via SAML, enterprise SCIM, audit logs with 7+ year retention for PCI evidence, KMS/HSM for 
…[truncated]
```

#### #5 `dsid_64470f7c6b15433c9f67cc78b51b16fc`

```
Lakeview Credit Union

Early ABM target. Hypothesis: GLBA/FFIEC-aligned controls will drive preference for VPC/private deployment and strong audit logging + retention controls. No confirmed workload details yet; likely customer support assistant + knowledge search across internal policy/docs; potential fraud/risk summarization workflow. Need to validate: data residency expectations (US-only?), PII handling boundaries, and whether they require customer-managed keys (KMS) and SSO via Okta/SAML.
Continue outbound to identify security + platform owner; propose 20-min security overview + reference architecture for VPC deployment.
No confirmed champion yet
Unable to identify owning team (IT Security vs Digital Banking vs Data/AI)
No response to initial outbound; phone tree routes to general IT helpdesk
Multiple visits to /regulated-workloads landing page from org IP range (unconfirmed attribution)
Downloaded 'security FAQ' link from marketing email (tracked click, no form fill)
Job posting observed: 'ML Engineer - Fraud & Risk Analytics' (signals internal build vs buy)
Tech stack hint (BuiltWith): AWS + Okta (needs validation)
VP Information Security / CISO (name unknown) - target for co
…[truncated]
```

#### #6 `dsid_60903cb34ddb4fae9b5ea1830dae1437`

```
FuseWave Payments

Quick-growing payments startup building merchant-facing dispute assistant and daily settlement reconciler. Primary contact: CTO (Rhea Patel). Wants to start with hosted API (self-serve) — low lift for engineering. Early security asks: "Do you have SOC2 Type II?" and SAML/SSO for admin console. VPC is 'nice to have' down the road if we sign Dedicated or Private; for now they want predictable per-token cost. Latency targets: 150-250ms p50 for short chat flows; batch embeddings for nightly reconciliation jobs (throughput ~100k embeddings/day). Cost sensitivity: high for embeddings; asked about quantized model recommendations and batching. Models: prefers open models (Llama2-like) but open to Redwood-curated variants if cost/lateny tradeoff is good. Quote from CTO: "We need something that just works with minimal infra friction — security is a blocker but we can work with hosted if SOC2 docs + SSO path look good." POC goals: integrate chat assistant into merchant dashboard + run nightly reconciler with embeddings within 2 weeks.\nNotes/clips: uses AWS us-east-1, data residency not strict yet. Mentioned potential pilot with 5 merchants.
Send SOC2 pack + SAML integratio
…[truncated]
```

#### #7 `dsid_780679d5c13d42e5938af847beed38bf`

```
CloverStripe Fintech

Primary: customer support chat (low-latency dialog) + embeddings-based doc search for KYC & billing docs. Secondary: reranking transaction alerts for fraud triage. Expected initial throughput small (100-500 reqs/day) during POC; aiming to scale to 2-3k/day within 6 months. Needs simple integration (JS SDK), token audit logs, and SSO for admin access.
Inbound from seed-stage fintech focused on SMBs. Signed up for self-serve hosted API trial (trial token: trial-cs-03). Early discovery call 2026-03-05 (CTO: Priya Raman). Wants hosted first; asking about VPC later once scale picks up. Key asks: SOC2 evidence, SSO/SAML for admin console, audit logs, and a short note on data residency. POC scope: support chatbot for billing and basic KYC doc lookup + embeddings for internal knowledgebase. Latency sensitivity: conversational latency target ~200-400ms p50 for short responses; cost-sensitive but willing to start with small paid POC. Quote from CTO: "We need something that just works out of the box — security checks are blocker 0." SE call 2026-03-09 covered rate limits, token pricing, batching suggestions. Sent Optimize suggestions doc and quick quantization notes. Act
…[truncated]
```

#### #8 `dsid_1df44244f57144619f742ec2e7dfd87d`

```
Peregrine DataWorks

Summary:
- Peregrine DataWorks = mid-stage fintech analytics provider. Very security conscious (PCI-adjacent data flows).
- Primary interest: accelerate fraud detection model enrichment (embeddings + reranker) and ingesting customer docs for dispute resolution.
- Preferred: Dedicated pool (predictable throughput) but will consider hosted if VPC-like isolation available.
- Security asks: SSO/SAML, SOC2 evidence, audit logs, KMS, possibility for EU data residency for specific customers.

Demo takeaways (02/04):
- Demo went well; live latency demo for 4k token sequences looked OK. Sec Eng asked good infra questions about KV cache persistence and HSM/KMS flow.
- Product liked: automatic prefix caching, rollout policies, canary fallbacks.
- They asked about model quantization and effect on fraud-detection recall — flagged as a concern.

Conversation snippets / quotes:
- Head of ML: "We need to be sure recall doesn't dip — false negatives are ... business-critical."
- Sec Eng: "Can you provide integration docs for SAML and KMS + SOC2 artifacts?"
- Procurement (via AE): "Budget is tight for Q2; will need to re-evaluate in next fiscal cycle."

Current status / signals:
…[truncated]
```

#### #9 `dsid_f4fbc3f2bcc24bb29f9da2c81e43661f`

```
Nimbus Compliance Labs

Account summary: large US regional bank spinout (platform+retail) evaluating enterprise code assistant for regulated engineering org.
Primary asks: VPC/private deployment, SSO (SAML), full audit logs with token-level traceability, retention controls down to 7/30/365 day buckets, KMS integration for model keys.
Latency/throughput targets: interactive IDE edits <80ms median token latency, streaming token delivery <50ms for editor integration; batch code-search/rerank throughput 2000 qps internal routing for repo scale.
Model preferences: pinned model for production (LLM-1.3-quant), fallback to smaller quantized variant during load. Must support deterministic seedability for code generation evals.
Cost sensitivity: high for developer seat scale (~3k devs) — looking at hybrid pricing: reserved capacity for steady state + hosted burst.
Security/compliance notes: SOC2 already required; iso27001 desirable; must support EU data residency for certain teams; legal flagged vendor subprocessors.
SE feedback from demo (2026-01-18): "Editor integrations looked good; prefix/KV caching reduced repeated completion calls by ~60% in demo"
Customer quote: 'We need predictable l
…[truncated]
```

#### #10 `dsid_da8b915c58a74bce8ccb88cd9b05d346`

```
Beacon Health Payments

Account summary:
- Vertical: payments for ambulatory clinics + patient billing reconciliation. Needs both PCI scope (card on file) and HIPAA PHI handling (EOBs, claims notes).
- Primary contact: VP Product Maya Saunders; Procurement lead: Sean Riley (payments ops). CTO (former) left 2026-01-22 -> hiring freeze in infra team.
Timeline / recent activity:
- 2025-11-12: inbound demo request via website; AE assigned (Ethan).
- 2025-11-18: intro call; mapped high-level requirements (throughput: 500 TPS ingest, latency p95 < 200ms for short prompts).
- 2025-12-03: scope call with SE (Priya) — requested POC for anonymized claims summarization + reconciliation embeddings.
- 2026-01-10: POC kickoff (fireflies ff-20260110-83bcd). We proposed private deployment w/ dedicated HSM and VPC endpoints.
- 2026-01-25: Security questionnaire submitted; payment processor (merchant acquirer) elevated PCI requirement to co-scope level.
- 2026-02-14: Security review with payments/QSA present (ff-20260214-91a2f). QSA concluded hosted shared-tenant API cannot be PCI-scoped without third-party attestation; recommended on-prem or fully isolated HSM-backed service.
- 2026-02-20: Legal re
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 44: `qst_0240::semantic` · N=40000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to rate limiting and quota issues but do not directly address the specific problem of epoch anchor disagreement during multi-region failovers. The gold chunk is detailed and on-topic, while the retrieved chunks are generally relevant but not specific enough, indicating an embedding near miss. The hit flag inconsistency is a critical issue.

### Question

During a multi region switchover, what is causing some customers to get bursty too many requests and occasional service unavailable responses because different parts of the traffic gatekeeper disagree briefly on the time boundary used for quota calculations?

### Gold document(s)

#### GOLD `dsid_5402831508734a51adf649603be4b075`

```
Investigate & fix rate-policy jitter that starves tenant capacity during regional failovers

Several customers (hosted + dedicated + private) escalated sustained 429/503 errors during a regional failover window. Initial triage shows that the rate-limiter's burst evaluation enters a transient jitter state when epoch anchors between proxy, orchestrator, and host-level rate controllers disagree. This leads to aggressive admission drops for a subset of tenants (capacity starvation) rather than graceful fallback. The goal of this ticket is to identify the root cause, implement a safe reconciliation path, and ship mitigations + tests to prevent recurrence.
Multiple enterprise customers observed multi-minute spikes of 429 and some downstream 503s during scheduled failover and autoscaler activity. Customer requests were effectively throttled beyond configured quota; billing and SLAs were impacted for two Dedicated customers and one Private deployment. Pager escalations and CS tickets received during outage window.
1) Simulate region failover by toggling route priorities in staging multi-region env
2) Run sustained high-concurrency generator at 60% above target per-tenant sustained rate
3) Force orchestrator restart and proxy rolling restart to create misaligned epoch anchors
4) Observe per-tenant admission drops and token-pool drain events in orchestrator logs
5) Check metrics: tenant_admission_rejected, burst_claim_mismatch, quota_epoch_skew
2026-03-02: On-call (Luis) validated customer traces and correlated spike with a control-plane failover that overlapped proxy rolling restart.
2026-03-03: Reproduced in staging. Found a 200-800ms window where orchestrator computed burst credits using previous-epoch metadata while proxy used a freshly persisted marker; mismatch caused double-counting and premature eviction of tenant tickets.
2026-03-04: Heap of evidence shows race in policy evaluator: policy cache refresh is async and not versioned atomically with token epoch transitions.
2026-03-06: Confirmed that Private deployments using slower KMS and commit-confirmation had longer window of misalignment.
2026-03-08: Small hotfix deployed on hosted to introduce 250ms guard windo
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_cc4c5c2310714fd99962514beac82e74`

```
Burst reservation failover triggers degraded P99 throughput and imbalanced batching for dedicated tenant

Issue summary:
Customer (NimbleDocs) reports a sudden spike in P99 token latency and a ~35% drop in measured throughput for their dedicated pool after an automated burst-reservation failover event. Impact: multiple application endpoints experienced increased tail latency leading to user-facing timeouts.

Impact:
- ~35% drop in throughput for tenant-specific routes starting 2026-03-12T17:12:00Z.
- P99 token latency increased from ~180ms to ~820ms for short chat requests (<= 128 tokens).
- Errors increased: transient 504s and client-observed timeouts.

Environment:
- Dedicated cluster: pool-id dp-45-nimble
- Region: us-west-2 (customer dedicated nodes)
- Runtime: 1.8.3 (serving runtime)
- Autoscaler: predictive-autoscale v2.1

Observed behavior:
- Autoscaler triggered a burst capacity failover at 17:11:42Z when reserved node set hit soft-capacity and a scheduled burst was rejected by quota check.
- Scheduler started evacuations of several tenant slots; eviction logs show KV cache drop and checkpoint flushes.
- Following evictions, request batching became imbalanced: many small ba
…[truncated]
```

#### #2 `dsid_ad148b222d31473f8a3d279d679935eb`

```
INC-2025-0303 Postmortem: Dedicated autoscaler lag + quota ceiling caused sustained throttling

# Summary
On 2025-03-03, a set of Dedicated customers saw elevated 429 throttling and increased queueing latency for ~62 minutes. The dedicated autoscaler attempted to add GPU nodes but hit a cloud quota ceiling, while the fallback routing policy was configured to prefer in-region capacity.

**Incident ID:** INC-2025-0303
**Customer impact:** Dedicated tier (subset), primarily eu-west
**Owning engineering team:** Eng SRE

# What happened
A scheduled load test by a customer coincided with a new prompt pattern increasing average output length. The autoscaler hit scale limits and then failed to provision due to quota. The system kept retrying, causing prolonged throttling.

# Timeline (UTC)
- 2025-03-03 09:12: Alert: dedicated-throttle-rate > 2%
- 09:17: Eng SRE on-call engaged
- 09:24: Identified provisioning failures due to quota ceiling
- 09:29: Mitigation: temporarily enabled cross-region burst for dedicated pool
- 10:14: Quota increased; scale-out succeeds

# Root cause
**Primary:** Provisioning blocked by GPU quota ceiling; autoscaler did not fast-fail to fallback behavior.
**Contribu
…[truncated]
```

#### #3 `dsid_4507a4e9254b4dd8b5a6d122ab69266d`

```
Misleading console quota reset after subaccount merge leading to opaque 429s

Issue summary:
Customer reported a sudden surge of 429 responses for interactive traffic after performing a subaccount merge via the Console UI. Console showed the merged subaccount's quota as '0 / 0' (reset) for ~20 minutes while requests were being rejected with 429. This is confusing for the customer because the billing/usage dashboard later reported quota available and there was an apparent mismatch between control-plane display and data-plane enforcement.

Impact:
- PulseMetrics experienced ~18 minutes of elevated 429 errors affecting webhooks and real-time SSE clients (~30% of production traffic).
- Customer-facing dashboards showed quota reset to zero leading to an incident escalation to their SREs.

Observed behavior:
- Console shows quota as 0 immediately after merge.
- API returns 429 with X-RateLimit-Remaining: 0 and X-RateLimit-Reset headers that appear inconsistent across edge nodes.
- Backend token-bucket snapshots indicate tokens still present on origin, but edge caches returned a local 'exhausted' decision.

Expected behavior:
- Console should reflect an accurate post-merge quota state qui
…[truncated]
```

#### #4 `dsid_141107a294da437e8c6d0ae9aa25bd03`

```
DST rollover induced quota-refill drift causing soft 429s across geo-edge pools

Issue summary: Starting 2026-03-08 02:00 UTC we observed increased soft 429s (rate-limit responses) for BrightCart's dedicated pool across eu-west and us-east. Impact: customer reports degraded throughput for order-processing chat assistants during peak morning traffic, 5-15% request failure rate for short-lived streams. Observed behavior: token refill counters on edge nodes drifted by up to 65 seconds relative to origin refill windows after a scheduled BGP failover that coincided with a DST clock adjustment in eu-west. This led to temporary double-accounting and then under-refilling on some edge pools, producing tenant-level soft 429s. Timeline: 02:00 UTC scheduled BGP rotation -> 02:05 first 429 spikes -> 02:12 engineered mitigation (edge token smoothing) applied -> 02:40 error rates returned to baseline but drift persisted until manual smoothing rollout.
1) Customer with dedicated pool and multi-region edge enabled uses many short-lived streaming sessions (avg duration 8s) around the local DST rollover window.
2) Trigger a BGP-driven edge failover or proxy swap during the clock change (simulated by 
…[truncated]
```

#### #5 `dsid_f5e17784eba547afad5f09a3287ced08`

```
Automatic model-fallback causes duplicated quota accounting and transient 429s

Issue summary:
Customer reports spikes of 429 responses (quota exhausted) when their traffic triggers automatic fallback between primary and smaller model variants. The 429s appear for a subset of requests during normal traffic patterns and immediately after a model variant rollout.

Impact:
- Intermittent request failures for production search ranking calls (degraded UX for customers).
- Affects ~3% of requests during fallbacks; sustained for seconds to a few minutes.

Environment:
- Tenant: NimbleSearch Inc. (enterprise)
- Region: us-east-1
- Route config: primary pinned to redwood/gpt-medium-v2 with automatic fallback to redwood/gpt-small-v2 when latency or capacity constraints occur

Steps to reproduce (as provided by customer):
1) Send steady stream of ranking requests (concurrency ~120) pinned to the primary route.
2) Force a minor model rollout on the primary (or simulate short degradation). The platform triggers automatic fallback to smaller variant for some requests.
3) Observe a burst of 429s in client logs during fallback window, not present when fallback disabled.

Observed behavior:
- Gatew
…[truncated]
```

#### #6 `dsid_e20aa4d066d14bcdbc90be241cbf8d04`

```
Tenant overspill causes synchronous fallback and throttled bursts during regional surge

During a multi-region traffic spike for three large customers, several tenants experienced elevated 5xxs and throttled burst allocations. The autoscaler and admission controller allowed an overspill pattern where tenant burst tokens were synchronously routed to a fallback path (slower warm coldpool) causing headroom exhaustion and queue amplification. Customers reported degraded latency and denied bursts for sustained short windows, triggering escalations. This ticket tracks investigation, hotfix, and follow-ups to prevent recurrence.
Spike correlated with 02:17 UTC regional surge. Headroom gauge dropped from 18% to 3% within 90s. AdmissionController.sync_fallback_count rose by 6x. Tenant burst_denied_rate spiked for top customers from 0.2% to 18%. Latency p95 for fallback path jumped from 120ms to 820ms. Autoscaler scale_up events lagged by median 70s due to sensor smoothing and lease-table stamp skew.
2025-02-14 02:12 UTC: First customer alert - elevated latencies in EU region
2025-02-14 02:16 UTC: SRE paged, preliminary mitigation applied: increased temporary burst_limit for affected tenants
…[truncated]
```

#### #7 `dsid_287214114f8c44778b323430e70eef90`

```
Intermittent p95/p99 latency spikes when region-pinned traffic falls back to out-of-region egress

Issue summary: Customer reports intermittent high latency (~200-800ms increase at p95/p99) for in-region requests when their routing falls back off the primary us-west pool into an out-of-region egress path. Impact: user-facing timeouts for inference calls in production, elevated token cost due to retrying. Timeline: 2026-03-09 17:40 UTC - customer began seeing spikes; 2026-03-09 18:05 UTC - first support contact; 2026-03-10 - triage opened and routed to SRE and Routing owners. This ticket covers investigation of whether egress policy, TLS session reuse, or cross-region routing orchestration is the root cause.
Production inference calls for NimbusHealth show transient p95/p99 latency increases causing degraded UX during morning traffic peak. Estimated 8% of requests experienced >=200ms extra latency during incident windows.
1) Configure account with region-pin=us-west and low-tier fallback routing enabled
2) Send steady generation traffic (approx 30 requests/s) targeting rw-7b-instruct with short contexts
3) Simulate reduced capacity in us-west pool to trigger fallback routing
4) Obse
…[truncated]
```

#### #8 `dsid_e9e9646d70df41e1813bf84634906671`

```
Regional affinity routing behavior during capacity surge and pin-unavailable fallthrough

Issue summary: Customer reports higher p95 latency for requests originating from EU users after they pinned to eu-west. When eu-west pool reported transient capacity pressure the routing behavior appeared to route some traffic to us-east resulting in increased latency and customer concern about data egress.

Impact: Intermittent increase in p95 latency from ~140ms to ~420ms for inference calls; some requests show cross-region egress. Customer is dedicated tier with reserved capacity, expecting strict region affinity unless strictly unavailable.

Observed window: 2026-03-01T09:10Z to 2026-03-01T09:44Z.

Expected: When a customer pins region to eu-west with dedicated capacity, traffic should preferentially remain in eu-west. Only when strict affinity policy is not possible (e.g., no compatible capacity and strict failover disabled) should traffic fall back, and this behavior should be clearly documented and surfaced in console/alerts.

Customer quote: "We pinned to eu-west to meet residency commitments. During the surge we saw many requests served from us-east — this breaks our data residency as
…[truncated]
```

#### #9 `dsid_595af30d9c194f8ea1a068a39dd9cedd`

```
Proactive congestion-island detection and sticky-region guardrails

Summary: During a progressive traffic surge on 2026-03-09 we observed cross-region failover amplification that caused an SLO miss for request p99 latency and error rate for hosted inference customers. Secondary regions entered a congestion mode that persisted despite circuit-breaker trips; routing replays and probe jitter amplified load to warm caches and overloaded GPUS. This ticket captures the postmortem analysis and prescribes mitigations and follow-ups to prevent recurrence.
2026-03-09 09:12 UTC - Automated health checks detected increased tail latency in region-eu-west-1.
2026-03-09 09:18 UTC - Smart routing triggered failover policy to reroute ~18% of traffic to region-us-west-2 (secondary).
2026-03-09 09:21 UTC - Circuit breakers in us-west-2 tripped and then rapidly reset due to short hysteresis config; controllers replayed queued requests.
2026-03-09 09:26 UTC - Observed progressive KV cache cold misses and repeated replays; GPU utilization saturated and request queues began to grow.
2026-03-09 09:40 UTC - On-call rotated, emergency mitigation (partial traffic pause to a warm standby) executed at 09:47 UT
…[truncated]
```

#### #10 `dsid_f3bfa55dffa442ef834731b7596981c1`

```
Clarify burst-window vs sustained-rate delta policy causing intermittent 429s for many short parallel requests

Issue summary:\nCustomer reports intermittent 429 responses during sustained parallel short requests (50-200ms requests) even though average tokens/sec is well below tenant quota. They suspect a 'burst window' or delta-rate policy interaction that punishes short-lived concurrency spikes.\n\nImpact:\n- Affects DocuFlow's background indexing workers and webhooks; ~10% of calls are 429-ing intermittently during peak sync windows.\n- Customer-facing failures (failed webhook retries) and delayed indexing jobs. No billing anomalies reported.\n\nEnvironment:\n- Prod us-east, self-serve account\n- API: /v1/generate (non-streaming)\n- Model: redwood-v1-large pinned to v1.3\n\nSteps to reproduce (as provided by customer):\n1) Launch 40 short-lived workers (each sends 15 concurrent requests in bursts for 30s)\n2) Observe steady average throughput ~300 requests/minute but many 429s in bursts\n3) Backoff and retry results in sustained job delays; sometimes 429s appear even when individual request rate per API key looks low in customer's telemetry.\n\nObserved behavior:\n- 429 response
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 45: `qst_0240::semantic` · N=75000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the topic of traffic management and rate limiting but do not directly address the specific issue of epoch anchor disagreement causing bursty errors during regional failovers. The gold chunk is detailed and on-topic, while the retrieved chunks are generally relevant but not specific enough to the question's context.

### Question

During a multi region switchover, what is causing some customers to get bursty too many requests and occasional service unavailable responses because different parts of the traffic gatekeeper disagree briefly on the time boundary used for quota calculations?

### Gold document(s)

#### GOLD `dsid_5402831508734a51adf649603be4b075`

```
Investigate & fix rate-policy jitter that starves tenant capacity during regional failovers

Several customers (hosted + dedicated + private) escalated sustained 429/503 errors during a regional failover window. Initial triage shows that the rate-limiter's burst evaluation enters a transient jitter state when epoch anchors between proxy, orchestrator, and host-level rate controllers disagree. This leads to aggressive admission drops for a subset of tenants (capacity starvation) rather than graceful fallback. The goal of this ticket is to identify the root cause, implement a safe reconciliation path, and ship mitigations + tests to prevent recurrence.
Multiple enterprise customers observed multi-minute spikes of 429 and some downstream 503s during scheduled failover and autoscaler activity. Customer requests were effectively throttled beyond configured quota; billing and SLAs were impacted for two Dedicated customers and one Private deployment. Pager escalations and CS tickets received during outage window.
1) Simulate region failover by toggling route priorities in staging multi-region env
2) Run sustained high-concurrency generator at 60% above target per-tenant sustained rate
3) Force orchestrator restart and proxy rolling restart to create misaligned epoch anchors
4) Observe per-tenant admission drops and token-pool drain events in orchestrator logs
5) Check metrics: tenant_admission_rejected, burst_claim_mismatch, quota_epoch_skew
2026-03-02: On-call (Luis) validated customer traces and correlated spike with a control-plane failover that overlapped proxy rolling restart.
2026-03-03: Reproduced in staging. Found a 200-800ms window where orchestrator computed burst credits using previous-epoch metadata while proxy used a freshly persisted marker; mismatch caused double-counting and premature eviction of tenant tickets.
2026-03-04: Heap of evidence shows race in policy evaluator: policy cache refresh is async and not versioned atomically with token epoch transitions.
2026-03-06: Confirmed that Private deployments using slower KMS and commit-confirmation had longer window of misalignment.
2026-03-08: Small hotfix deployed on hosted to introduce 250ms guard windo
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_31059f73d2d2409488178447167534e6`

```
Burst allocation timebase drift during Private->Dedicated switchover causing opaque throttles

During an automated switchover from Private to Dedicated routing for a large tenant, a drift between two allocation timebases caused burst credits to be misapplied. The orchestrator and admission proxies used different epoch anchors for burst ledger reconciliation, which resulted in immediate silent 429 rejections and opaque errors for customer traffic for ~14 minutes. This ticket captures the investigation, mitigation, and long-term fix plan.
1) Configure tenant in Private mode with reserved burst budget.
2) Trigger a controlled switchover to Dedicated routing (simulated in staging).
3) Force orchestrator snapshot + fast follower restart where system clocks are slightly skewed (simulate NTP jitter).
4) Replay high QPS traffic spikes for 2 minutes using the tenant's traffic profile.
Expected: smooth handoff of burst ledger. Observed: admission proxies reject requests with 429 and 'quota_unavailable' until manual resync.
2026-03-10T18:03:42Z orchestrator INFO: snapshot(epoch=1289, anchor=2026-03-10T18:03:40Z)
2026-03-10T18:03:43Z proxy WARN: allocation-mismatch tenant=acme-co expected-epoc
…[truncated]
```

#### #2 `dsid_e20aa4d066d14bcdbc90be241cbf8d04`

```
Tenant overspill causes synchronous fallback and throttled bursts during regional surge

During a multi-region traffic spike for three large customers, several tenants experienced elevated 5xxs and throttled burst allocations. The autoscaler and admission controller allowed an overspill pattern where tenant burst tokens were synchronously routed to a fallback path (slower warm coldpool) causing headroom exhaustion and queue amplification. Customers reported degraded latency and denied bursts for sustained short windows, triggering escalations. This ticket tracks investigation, hotfix, and follow-ups to prevent recurrence.
Spike correlated with 02:17 UTC regional surge. Headroom gauge dropped from 18% to 3% within 90s. AdmissionController.sync_fallback_count rose by 6x. Tenant burst_denied_rate spiked for top customers from 0.2% to 18%. Latency p95 for fallback path jumped from 120ms to 820ms. Autoscaler scale_up events lagged by median 70s due to sensor smoothing and lease-table stamp skew.
2025-02-14 02:12 UTC: First customer alert - elevated latencies in EU region
2025-02-14 02:16 UTC: SRE paged, preliminary mitigation applied: increased temporary burst_limit for affected tenants
…[truncated]
```

#### #3 `dsid_595af30d9c194f8ea1a068a39dd9cedd`

```
Proactive congestion-island detection and sticky-region guardrails

Summary: During a progressive traffic surge on 2026-03-09 we observed cross-region failover amplification that caused an SLO miss for request p99 latency and error rate for hosted inference customers. Secondary regions entered a congestion mode that persisted despite circuit-breaker trips; routing replays and probe jitter amplified load to warm caches and overloaded GPUS. This ticket captures the postmortem analysis and prescribes mitigations and follow-ups to prevent recurrence.
2026-03-09 09:12 UTC - Automated health checks detected increased tail latency in region-eu-west-1.
2026-03-09 09:18 UTC - Smart routing triggered failover policy to reroute ~18% of traffic to region-us-west-2 (secondary).
2026-03-09 09:21 UTC - Circuit breakers in us-west-2 tripped and then rapidly reset due to short hysteresis config; controllers replayed queued requests.
2026-03-09 09:26 UTC - Observed progressive KV cache cold misses and repeated replays; GPU utilization saturated and request queues began to grow.
2026-03-09 09:40 UTC - On-call rotated, emergency mitigation (partial traffic pause to a warm standby) executed at 09:47 UT
…[truncated]
```

#### #4 `dsid_2cc1acdfe064404eaa81e75adeeb4a7d`

```
Autoscaler threshold sensitivity causing small-tenant preemption and reserved-pool shortfalls

Summary: A sequence of production incidents over the past week where small tenants experienced sudden latency spikes and 503s. Root cause traced to an aggressive threshold sensitivity change in the dedicated autoscaler that caused premature preemption of warm slots for low-cardinality tenants and incorrect replenishment of reserved pool headroom. Symptoms: customer-facing timeouts, elevated token queuing, and rapid depletion of burst credit for affected tenants. Impact: multiple customers reported degraded performance during peak bursts; three enterprise customers opened escalations and one threatened to convert to Dedicated burst guarantees.
2025-02-18 09:23 - Ava Chen: Triage call summary: observed correlated jump in preempt_count for small tenants starting 2025-02-17 22:00 UTC. Autoscaler metric preempt_sensitivity was increased in runtime-1.18 to reduce queue latency for high-cardinality traffic; unintended side effect for small tenants.
2025-02-18 11:10 - Diego Morales: Reproduced locally with synthetic workload: lowering tenant qps to mimic low-cardinality ramps shows preemptive evi
…[truncated]
```

#### #5 `dsid_b78b3f805e5744408c1b64e9cfc0c395`

```
Unexpected region cycling triggered a fallback wave leading to high-latency and model variant overload — postmortem

This ticket documents the incident that occurred on 2026-03-03 where our routing subsystem began rapidly cycling regional weights for a subset of customer clusters, which triggered a chained fallback to cheaper model variants. The immediate effect was a region flapping pattern that increased cross-region tail latency and overloaded variant-serving pools, causing elevated 5xxs and timeouts for multiple tenants. This postmortem covers detection, impact, root cause, mitigations, permanent fixes, and action items.
At ~2026-03-03T06:17:00Z, routing weight adjustments for eu-west-1 started oscillating for traffic from the EU control plane. The control-plane signal interpreted temporary telemetry gaps as sustained capacity loss, aggressively draining region weight. Traffic was re-routed to fallback tiers and model variants; fallback pools (variant-v2-quant) reached saturation. Overloaded fallback pools experienced increased inference latency and queueing, causing a cascade where other regions also drained to pick up load, amplifying the problem into a routing wave. Total cu
…[truncated]
```

#### #6 `dsid_e5a1cfad51b14cc39727fd1ca235b9cd`

```
Investigate burst policy fan-out mismatch causing cross-tenant throttles

Summary: Multiple customers (hosted + dedicated + private) reported sustained 429 spikes between 2026-03-09 22:00 UTC and 2026-03-10 03:40 UTC. Symptoms: opaque 429s at edge, long tail latency on admission, and token exhaustion metrics on the orchestrator. Scope: cross-environment (hosted API, a Dedicated pool in eu-west, and one Private VPC install). Hypothesis: a mismatch in burst-window semantics and the fan-out logic in the admission controller caused transient credit over-allocation to a single tenant, which then triggered global reconciliation that starved other tenants. The mismatch appears when policy objects are serialized by older private deploys and interpreted by the orchestrator with a different epoch granularity (milliseconds vs seconds) and a per-tenant fanout multiplier incorrectly applied during rehydration.

Repro steps observed:
1) Create tenant with aggressive burst policy (burst_tokens: 5000, window: 120)
2) Launch rapid warmup traffic from 20 distributed clients over 30s
3) Observe admission logs: admission/allocate:burst=5000 accepted, but orchestrator ledger shows epoch window 120000 i
…[truncated]
```

#### #7 `dsid_eb500d00dfb34dbc80c551f107f59b33`

```
Adaptive burst smoothing and quota-enforcement failover

Problem: The current quota/rate-limiter struggles with short-duration bursts and has a single-path dependency on the centralized token refill service. Recent incidents showed both unfairness across customers during bursts and a catastrophic failure mode when the refill pipeline experienced backpressure. Goal: Implement an adaptive burst-smoothing layer, hierarchical fairness at customer+route granularity, and a robust degraded-mode failover that preserves SLOs and reduces cascading outages. Deliverables include algorithm design, Redis-backed state with local fallback, circuit-breaker thresholds, tests, dashboards, and a staged rollout plan.
Burst smoothing reduces 95th and 99th percentile request rejections during short bursts by >= 40% for synthetic burst tests
Quota enforcement latency (limiter decision path) stays under 100ms P99 in normal mode and under 250ms P99 in degraded mode
Fairness rules prevent any single customer from consuming > 60% of aggregate burst tokens within a 10s window
Limiter primary path availability >= 99.95% and degraded-mode availability >= 99.99% during simulated central-refill outages
Automated r
…[truncated]
```

#### #8 `dsid_fc34f401b1724cac87b02b53c49b14e9`

```
hybrid-routing-quota-drift-silent-rejections

Summary: Multiple customers across Hosted, Dedicated, and Private deployments reported sudden unexplained request rejections over the past 72 hours. Symptoms included elevated 429/opaque-denial rates from edge proxies, console quota UIs showing rapid consumption without corresponding traffic spikes, and degraded tail-latency for routed requests. This ticket tracks investigation, mitigation, and a permanent fix for a token-bucket state-drift issue exposed by our hybrid routing logic between Hosted and Dedicated routing layers.
2026-02-27: First alert from monitoring (unexpected quota depletion for 3 Hosted tenants). 2026-02-28: Dedicated customer support ticket and escalations from two large customers experiencing intermittent rejections. 2026-02-29: On-call identified desynced rate-limiter state during cross-region failover; temporary mitigations applied. 2026-03-01: Ticket created to track permanent fixes and rollout plan.
Affected: ~6 customers (mix of Hosted and Dedicated), several internal prod routes. User-visible: 10-30% request rejection spikes for impacted tenants, increased latencies due to retry storms. Business: one customer 
…[truncated]
```

#### #9 `dsid_e28c2b76f9ae43bdb6e809f2acf37930`

```
Region failover sequencing bug and priority shed policy consolidation

Summary: On 2026-03-01 at ~08:03 UTC a multi-region failover sequence caused a correlated set of circuit-breaker (CB) openings and priority queue shedding across EU and US regions, resulting in a 28-minute continuous SLO violation for the generation latency P99 for several high-throughput customers. The orchestrator replayed an out-of-order failover sequence after a partial control-plane partition which briefly allowed dual warmup eviction and simultaneous CB signals. This ticket captures the incident analysis, immediate mitigations, and cross-team corrective plan to prevent recurrence.
SLO: generation P99 latency exceeded target (1.2s -> observed 3.8s) for 28 minutes
Affected regions: EU-west-1 primary, US-east-1 secondary (sticky affinity misrouted to secondary under failover)
Customers: 7 high-throughput tenants experienced increased 429/503 errors and tail latency spikes
Operational: automated rollback to lower model concurrency triggered but did not fully alleviate due to inter-region backpressure
2026-03-01 08:02:38 UTC - Control plane observed degraded heartbeat from EU controller (brief partition).
2026-
…[truncated]
```

#### #10 `dsid_3b4b3f6a33fa42beb71c55e6550fd2cd`

```
Backpressure amplification from sticky auth lease retries caused regional 429 wave

Summary: On 2025-02-14 a regional 429 storm lasted ~42 minutes for a subset of production tokens. Traffic analysis showed a dramatic amplification where aggressive retry loops from edge auth clients (gateway edge agents) caused concentrated load on the central lease/token service and the quota enforcer. Sticky lease retries (clients re-requesting short-lived auth leases without exponential backoff/jitter) caused a feedback loop: auth service latency increased -> gateway retries synchronously -> quota enforcer perceived many simultaneous token bursts and applied hard quotas resulting in regional starvation. Impact: some customers experienced elevated 429s and request tail latency; headroom for Dedicated pools in the affected region dropped 60% for 20 minutes. This ticket captures the postmortem, mitigations applied, and the action plan to prevent recurrence.
2025-02-14T09:12Z - First pager alert: gateway 429 rate > 5x baseline in us-west-2
2025-02-14T09:15Z - Triage: partial mitigation toggled (increase short-term token allowance) to reduce immediate 429s
2025-02-14T09:22Z - Observed auth lease call 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 46: `qst_0242::semantic` · N=10000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant to the topic of partnerships and security but do not directly address the specific question about the security lead's target date for a smoke test. The failure mode is likely an embedding near miss, as the retrieved documents are related but not specific enough. Both gold and retrieved chunks are non-empty and on-topic, but the retrieval did not captu

### Question

In the partner integration call about getting a third party AI service into another companys cloud catalog, what date did the security lead target for completing the pre publication image security smoke test?

### Gold document(s)

#### GOLD `dsid_3fc14ed9048e4e1f861e0632b06fc39b`

```
HaloTech x Redwood: Marketplace listing + ref-arch integration sync

Kickoff technical integration sync between Redwood and HaloTech focused on listing Redwood in HaloTech Marketplace, producing a joint reference architecture for a managed VPC deployment, and clarifying billing/metering and security artifacts required for marketplace publishing. Agreed deliverables and dates; follow-up calls planned for billing and QA of AMI/terraform artifacts.
Header:
- Date/Time: 2025-03-11 15:30 PT
- Duration: ~62 minutes
- Location: Zoom
- Attendees: Ava (Redwood AE), Marcus (Redwood SE), Sophie (Redwood Product), Daniel (HaloTech Partnerships), Priya (HaloTech Platform), Liam (HaloTech Security), Rosa (HaloTech Marketplace PM)

Auto-summary (auto-gen, may be noisy):
- Discussed marketplace listing requirements (AMI vs SaaS), metering hooks, ref-arch for private VPC+peering, and SOC2/KMS documentation. Identified next steps and owners.

[00:00] Ava (Redwood AE): Hey everybody, thanks for joining. Quick roll call — I'll kick us off. Marcus and Sophie from our side, and from HaloTech is Daniel, Priya, Liam, Rosa?
[00:08] Daniel (HaloTech): Yep, all here. Thanks Ava. Quick note, we have about an hour, we want to make sure we get the AWS marketplace and the reference arch checklist covered.
[00:15] Marcus (Redwood SE): Cool. I'll start with a high-level on the integration options we see: 1) Hosted Redwood API listing in HaloTech marketplace (SaaS consumption), 2) AMI / appliance style listing for private customers (bring-your-own infra), 3) Terraform module + module registry approach that customers can use to deploy Redwood private inside HaloTech accounts.
[00:33] Priya (HaloTech): For our marketplace we prefer SaaS listings for first-class billing, but we also support AMIs for private customers. We need to pin down how metering will work — will Redwood emit usage events we can consume, or do we need to integrate with AWS SaaS metering API?
[00:48] Marcus (Redwood SE): Good question. We support both patterns. For hosted SaaS we can emit metering events to the marketplace platform; we also can provide a SaaS connector that calls the marketplace metering API. For AMI/private dep
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_544c8acb021e44179a154dc218df4d0d`

```
partnerships

alex.partnerships: Ok looping in the team — we got a request from TitanEdge (hardware partner) for the marketplace listing. They need our SOC2 artifacts, pen-test summary, and an upload we can hand to their SI. TL;DR: they want an evidence bundle by next Wed.

maya.security: Thanks. We have a redacted SOC2 Type II PDF and pen-test exec summary. Full pen-test report is sensitive — legal needs to review before sharing.

sam.partner-eng: For the SI integration they want firmware hashes + attestations for the appliance images. Also asking for a sample config and the API endpoint cert chain.

priya.ops: Logistics: do we want to generate presigned S3 links or place everything into a partner S3 bucket with cross-account access? Pref: presigned links with 7-day TTL and one-time download.

jordan.legal: We need a data sharing addendum signed before we hand over any raw reports. Redacted SOC2 ok to share now, full pen-test only after AAD is signed and we confirm scope.

maya.security: Agreed. Also want to ensure artifacts are encrypted at rest and that presigned URLs are scoped to specific files. I'll prepare a checklist of items to include.

alex.partnerships: Action items: 1)
…[truncated]
```

#### #2 `dsid_521ceaa63b844d85940cd637e799da97`

```
partnerships

maria-partnerships: Quick sync — got vendor notes from call. Need to align H200/B200/MI300 availability with cloud marketplace onboarding and joint-ann dates. Can we list concrete dates + blockers? @leah-marketplace @ajay-hw
ajay-hw: From infra side: H200 driver+firmware test pass targeted 2026-04-15. B200 early access nodes arriving 2026-05-01; internal perf runs start week of 5/4. Key blocker: firmware rollback path still TBD.
leah-marketplace: Marketplace listing windows: AWS marketplace staging slot 2026-04-20, GCP marketplace review 2026-05-10, Azure needs security attestation — ETA 2026-05-25. Need final SKUs and pricing by 2026-04-10.
oliver-solutions: Customer-visible docs and quickstarts need model artifacts + container images. Can ops get a stable image tag by 4/18? Also want a sample throughput report for sales.
maria-partnerships: Action items: Ajay confirm image tag & rollback plan. Leah confirm marketplace form fields (I can fill). Kayla to draft joint-ann comms once dates lock. Let's avoid a hard public date until we have vendor GA.
ajay-hw: I'll push image tag 2026-04-16 if all tests green. Rollback plan: we can finalize by 4/12 after one more firmware
…[truncated]
```

#### #3 `dsid_73f4e1dea88c4fc1a39af9720187bfc3`

```
partnerships

jen_partnerships: quick check-in 15m: VaultStream (SI) wants a joint MSSP listing bundling Redwood Private + VaultStream secrets. asks: SAML SSO example, SCIM provisioning sample, and KMS/HSM key-wrap demo. Partner marketing needs a short runbook + smoke script by EOW. @samir_eng @lee_security can we commit?

samir_eng: I can run the smoke. need to clarify KMS scope  is it symmetric key-wrap for rotation or HSM signing?

jen_partnerships: they called it key-wrap for rotating secrets-at-rest (wrap/unwrap). also want sample SAML assertion and SCIM group sync. deadline is tight  webinar next week.

lee_security: treat as BYOK for Private. confirm VaultStream's KMS vendor (KeyWave?) and whether they support KMIP. add short threat-model about cross-tenant key access. no real certs in docs.

olivia_sales: VaultStream will provide a dev tenant and a non-prod KMIP endpoint with test certs. they'll also want an integration checklist to prep service accounts and roles.

samir_eng: plan: 1) exchange SAML metadata, 2) SCIM token + incremental group sync, 3) KMIP key-wrap handshake, 4) call Redwood rotate API to verify rotation. I'll post minimal examples.

samir_eng: SCIM token e
…[truncated]
```

#### #4 `dsid_5aff2c70fbb447a6bd58dfc7e7f72688`

```
Galena Archive Solutions

Top-line: regional archive authority evaluating an air-gapped Private deployment for long-term records search + automated incident summarization. Very risk-averse; must be fully on-prem, no egress, signed offline model bundles, HSM for key management.

Key points from calls: 
- 'We cannot allow any outbound connections from the inference cluster' — CISO (paraphrase).
- Preference for physical media/model transfer and image signing.
- Will require STIG/NIST 800-53 mapping; Fed controls applied internally (CUI).
- LDAP/AD integration only; SSO via SAML must be mapped to existing IDP but remote OIDC not allowed in SCIF.
- Retention controls: legal hold + immutable retention for outputs for 7 years.

Procurement context: prime integrator will manage datacenter procurement. Decision influenced by ability to: provide signed SBOM, offline update process, FIPS/HSM integrations, and support for SCIF install procedures. Price vs. risk: cost is secondary to compliance in this account.

Quotes/Notes from AE/SE: 
- SE: 'We can package model artifacts as signed tarballs + verification tooling for their security team.'
- AE: 'Need clear escalation path and a runbook for 
…[truncated]
```

#### #5 `dsid_f23926802cf44ae4b85c4410682eab90`

```
partnerships

sara.partnerships: quick sync — marketplace partner lab connector certification planning. goal: provide a GA-ready helm + terraform module path, multi-arch images, and an SI smoke harness for partner onboarding. who owns what?

alex.eng: I'll own infra CI. plan is GH Actions matrix for arm64/amd64 + gpu variants. will gate on helm lint + kube smoke. sample matrix snippet:```matrix:
  arch: [amd64, arm64]
  gpu: [none, ampere]```

miguel.se: +1. I'll build the terraform module for partner onboarding (vars: region, instance_profile, ami, node_pool). will include examples for VPC peering to partner env and simple ansible for post-provision.

devon-sre: can we reuse the existing refarch network overlay? i can supply a terraform overlay module (overlay-refnet) and CI job that applies it to test clusters.

janet.product: timeline question — marketing needs assets and copy 2 weeks before any joint announcement. is MVP realistic in ~3 weeks?

alex.eng: MVP target = 3 weeks. CI gates: terraform fmt + validate, helm lint, smoke deploy (5-minute), basic e2e (latency/cold-start quick check).

sara.partnerships: who will coordinate SI validation sessions? we should block a partner
…[truncated]
```

#### #6 `dsid_b7f8adc1e56749938ac0fe666319bd33`

```
Briarwood Network Dynamics

Complete SIG/CAIQ responses, schedule KMS integration PoC with infra team; finalize SOW for private VPC
security completing vendor risk intake (SIG) - awaiting legal sign-off
network firewall rules and peering details from infra
central KMS/HSM validation and access policy
procurement budget approval, final T&Cs
30k+ meters across US regions; strict data residency for customer billing data
Security team requested full SIG and CAIQ matrix — want vendor risk intake completed before infra kickoff
Primary ask: Private VPC deployment with KMS integration (customer-managed keys), audit logging forwarded to central SIEM
Latency target for conversational agent: 150-200ms p95 for short flows (chat frontend); high throughput for nightly embedding jobs
Cost sensitivity moderate — willing to commit reserved capacity if unit economics shown (prefers predictable ARR over all-in usage spikes)
SE notes from 2026-02-18 call: "We need a tight shared responsibility doc — security wants explicit lines on log retention and token handling"
Procurement: legal wants indemnity language changes; data residency clause needs region-specific residency in NA-west and NA-east
Asked fo
…[truncated]
```

#### #7 `dsid_157aeecf95f543329978debd0f4164e8`

```
Pegasus VPC Solutions

Schedule architecture deep-dive with network/security (2026-03-10). Share SOC2/ISO mapping doc and BAA draft.
Legal requires signed BAA
Data residency decision for EU/US split pending
Network diagram and VPC peering acceptance
Cost analysis for dedicated GPU pools not finalized
Key contact: CTO Maria Lopez (focus: PHI handling, residency).
PoC scope: private VPC deployment w/ customer-managed KMS, audit log forwarding to Splunk, optional on-prem inference for batch PHI workloads.
From 2/18 call: 'We cannot send raw PHI to third-party shared GPUs' — legal emphasized need for BAA + VPC isolation.
Security wants explicit mapping: SOC2 CC6 (access controls) -> SSO/SAML + RBAC integrations; audit logging must retain 1 year for clinical audits.
ISO 27001: require evidence for A.10 cryptographic controls — Redwood KMS integration + HSM option discussed.
PCI consideration: only tokenized card data will be allowed through Redwood; full PANs must be redacted before sending. Compliance team to validate.
Data residency: plan to route EU PHI to EU-dedicated private deployment; ask for proof of residency (regions list, certs).
Performance targets: p95 latency < 350ms for c
…[truncated]
```

#### #8 `dsid_4aa62974759543e8b27eaa9d940e2ae3`

```
BlueHarbor Compliance AI

POC scope: deploy Redwood Private into customer-managed EU VPC (Frankfurt). Deliverables: Terraform modules + Helm chart, KMS cross-account integration, audit log delivery to in-region S3 and Splunk, retention controls (7y), and runbook for ops. Security: completed questionnaire v2; outstanding items: HSM/KMS attestation, pen test schedule, and requirement for audit logs to never leave EU. Tech contacts: Elena Novak (CTO), Marco Ruiz (Lead Infra). Quote: "We can't leave logs outside EU — need strict residency and audit trail." POC status: terraform repo shared 2026-01-10, helm deployed to staging 2026-02-15. Integration tests: smoke OK, load tests show p95 latency spikes >150ms intermittently; root-cause likely Helm init race with EFS mount and KV cache warmup. KMS: customer requires CMK rotated on their schedule and customer-managed keys (AWS KMS) with cross-account grants — IAM policy draft under review. Compliance/legal: redline requested on data residency and retention clauses; they want legal to sign SOW only after KMS and audit logging controls verified. Commercial: medium cost sensitivity; prefers dedicated/reserved with SLAs (99.9% uptime, <150ms p
…[truncated]
```

#### #9 `dsid_03a61b2b31094c4d909de520ac49e75f`

```
Grenadier Regulated EdgeWorks

Snapshot notes (shorthand)
- Organization: regional defense research consortium, multiple classified enclaves across 3 sites. Primary contact: Dir. of AI Ops (M. Hargreaves).
- Motivation: replace brittle rule pipelines for analyst chat + unify embeddings for threat intel similarity across enclaves.
- Must run in air-gapped on-prem with HSM-backed key store. No egress allowed; updates via signed image bundles only.
- Latency/throughput: soft SLO 100ms p95 for short-turn chat queries; high-throughput bulk embedding job overnight (100M tokens/day acceptable if batched). Cost sensitivity moderate, reliability and compliance trump unit cost.
- Models: prefer audited open models (FP16/INT8 quantization), ability to pin model versions and roll back. Interested in Redwood's quantization recommendations and kernel/compilation controls.
- Integrations: SIEM (Splunk), internal secrets manager (HSM by Thales), SSO via SAML + SCIM for automation, audit log shipping to internal retention lake (7 years).
- Security asks: SOC2 equivalent audit evidence, FISMA-moderate mapping, signed SBOM for runtime images, vulnerability CVE triage SLA, on-site pentest approval.
- 
…[truncated]
```

#### #10 `dsid_3c18e45fbc064bdeb056d94d621846f2`

```
partnerships

maria: Kicking off a Partner Runway thread — want to align SI enablement milestones for the Q2 SI onboarding pilot. Quick sync?
aj: +1. Goal: cert + lab access + playbooks before pilot. Timeline?
kyle: Thinking a 6-week runway: W1 KT, W2 lab infra & creds, W3 train-the-trainer, W4 cert exam, W5 pilot prep, W6 joint announce / handoff.
sanjay: We need dedicated sandbox creds + a small HW testbed spec for integrator validation. Can infra/partners spin this up? Any IP/network constraints?
maria: Onboarding checklist draft I sketched: access reqs, sample apps, platform tenant, test datasets (PII-scrubbed), eval harness, pass criteria. I'll upload DOC and link in #drive.
alexa: Product marketing: Heads up — avoid conflicting with marketplace launch on May 12. We prefer joint announcement week of May 20. Is that feasible?
aj: May 20 feasible only if certs finished by May 10 and we have recording and cert badge assets ready. Also need partner logos signed off.
kyle: Proposed training format: 2hr live session + 3 hands-on on-demand labs (deploy sample webhook, Dedicated capacity flow, model rollback test). Slide + demo repo + self-cert quiz.

kyle: Quick draft checklist (past
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 47: `qst_0251::semantic` · N=15000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the topic of vector retrieval and performance targets but do not match the specific details in the gold chunk. The gold chunk is detailed and on-topic, while the retrieved chunks are also relevant but lack the specific performance targets mentioned in the question. This suggests an embedding near miss rather than a complete mismatch.

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Gold document(s)

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_9e5e6325ff084b08898293033de2d391`

```
Retina SearchWorks

Primary: customer support agent + ticket deflection. Use dense embeddings for recall, then fast cross-encoder rerank to ensure top-5 quality for agent suggestions and self-serve KB answers.
Complete perf POC + finalize pricing for 18M doc index; procurement demo 2026-03-18
Clarify high-QPS pricing
Internal security questionnaire (INF-Sec)
Legal approval for data residency clause
Indexing DAG for daily updates
Index target: ~18,000,000 historical tickets (10 yrs), ~1.6B tokens; snapshot size 2-4 TB; ~150k new vectors/day expected during ramp
RAG (semantic search + rerank) QPS target 150-250; reranker top-5 latency budget p95 < 120ms; end-to-end P95 (query->answer) < 400ms for most flows; throughput spike handling to 500 qps with graceful fallback
Will stream ticket updates via Kafka -> incremental embedding pipeline
Need guidance on warm KV cache strategy for bursty chat sessions
Expect connector to internal Confluence + S3 artifact store; must support incremental deletes
2026-02-05 - Initial intro call (AE Liam) - described goals: deflect 35% of tickets, reduce AHT by 20%
2026-02-18 - sent security questionnaire + pricing template (AE)
2026-02-20 - POC kickoff: 
…[truncated]
```

#### #2 `dsid_a6123856d857425bb7419ea99b49e265`

```
Pegatrix MassIndexers

Company background: Pegatrix builds an enterprise search layer for regulated legal and financial corpora. Customers include law firms and compliance teams.
Primary ask: scalable embeddings + reranking pipeline capable of 100M-1B vectors; predictable P95 latency <50ms for retrieve phase, <200ms end-to-end with reranker for top-10.
Workload profile: heavy fanout on retrieval (topK=1k in initial candidate generation), then cross-encoder rerank on top-30. Expect bursts around e-discovery jobs (spikes x5).
Cost sensitivity: unit-cost per query is a key purchasing metric. "Low-per-query" target: <$0.002 per query at 250M vectors baseline, with aggressive batching/caching to hit goals.
Model preferences: prefer open embedding models (ada/variant-style) for CPU/quantize, and a compact cross-encoder (T5-small-ish) for reranker but open to offloading to GPU for latency-critical flows.
Indexing requirements: incremental ingestion, shingling (sliding window embedding), live deletes/PII redaction, and reindex windows every 24-48h for source connectors.
Operational needs: per-route cost & latency dashboards, token-level cost breakdown, automatic fallback to cheaper model v
…[truncated]
```

#### #3 `dsid_c663f74bce354012a30c0b95849b090a`

```
Lithic Code Archives

Account: internal-first search for proprietary codebase + customer-facing devdocs. High priority: replace several brittle grep/Elasticsearch layers with vector-based retrieval + token-aware reranker. Team is infra-heavy (SRE + search engineers). Primary ask: support 40M vectors now, growth to 120M within 12 months; daily full reindex unacceptable -> need delta + streaming reindex. Quote from CTO: 'We need search that scales like storage, not like ML experiments.' Wants end-to-end SSO (SAML) + audit logs and per-namespace residency. Cost sensitivity: will evaluate unit cost at 1M queries/day baseline. Interested in dedicated pools for predictable latency and private deployment for code residency. Short bulleted notes: - heavy emphasis on reranking for precision at top-K - LLM candidate models: open-code-tuned and custodial fine-tunes - caching hot prefixes for frequently accessed repos - compliance: must meet SOC2 plus audit retention 1 year
Scaling: current corpus ~40M embeddings (768-d). Target growth 3x in 12 months. Re-indexing cadence: daily delta + weekly snapshot; ingestion peak 200k vectors/hour. Performance: tail latency P95 < 150ms for top-5 retrieval
…[truncated]
```

#### #4 `dsid_4f571bb8e6574a93a4a65ca03f9ec89c`

```
Valorium Enterprise Retrieval

Top line: large DoD contractor; searching >200M docs (mixed structured/unstructured) across classified/unclassified enclaves. Primary ask: on-prem, air-gapped RAG platform supporting dense embeddings + cross-encoder reranking; strict retention/residency and audit requirements.\n\nRecent activity: \n- 2026-02-09 kickoff call (ff link above). Intro w/ procurement + security + search team. Quick wins: baseline perf numbers and SOW outline agreed.\n- 2026-02-16 SE deep-dive: Diego walked architecture options (dedicated private runtime vs full on-prem). Customer: \"need determinism — can't have bursty cloud fallbacks.\"\n- 2026-02-24 security review w/ CISOs (ff transcript). They requested KMS/HSM proof-of-concept, detailed logging pipeline, and compartmentalized tenant model.\n- 2026-02-28 POC scope agreed: 3-node air-gapped cluster, 100M-doc index (subset), vector index stored on encrypted NVMe, include reranker (cross-encoder) for top-10 re-rank. Metrics: P90 query latency target 250ms (ideally <200ms for short queries), throughput 120 qps sustained, cost per query target (internal) <$0.015.\n\nRequirements summary / customer language: \n- Indexing scal
…[truncated]
```

#### #5 `dsid_a935e7827ac34cb49ba446eb24dcd055`

```
LucidGrove Answersphere

Finalize POC perf run + receive security checklist answers
SOC2 audit pending
data residency details for EU customers
cost per q unknown
2025-02-10 — initial intro call, AE Jordan Hale; product fit looks good
2025-02-18 — SE workshop (Priya) demoed embeddings + reranker flow; focused on latency
2025-02-27 — security intro; asked for SOC2 + KMS details; sent security FAQ
2025-03-01 — provided sample token-cost calc; requested POC SLA
2025-03-03 — scheduled POC perf run for 2025-03-10; need dataset and query profile
Indexing scale: ~300k canonical KB articles + 200k historical support tickets (total ~500k docs)
Peak QPS: 500-1,200 queries/sec; steady 300 qps
Latency SLO: embed lookup <=50ms, reranker + top-k re-rank <=120ms p95
Cost target: <$0.02 per query (avg) across lookup+rerank
Model preference: quantized open models for embeddings; small/medium reranker (7B-13B)
Routing: simple cost-based fallback to smaller reranker on spike; regional routing to eu-west for EU traffic
Security: SSO (SAML), audit logs, KMS for keying, retention controls, EU data residency for some customers
Deliver sample eval harness by 2025-03-07 (redwood SDK + query simulator)
POC p
…[truncated]
```

#### #6 `dsid_e611d79c110248d9853fb40b4be0e216`

```
Pegasus Compass

Shorthand from calls / internal: customer is running a SaaS help center and in-app support chat. Primary goal: accurate doc search + answer generation for agents and automated chat. Wants embeddings + cross-encoder rerank to keep top-k precise. CTO quote: "Need <150ms p99 at 1k qps or it's a non-starter." Pricing sensitivity: target unit cost <$0.004 per full query (embedding + rerank). Current dataset: ~2.5M docs expected at scale (mix of long articles and short FAQs). Ingest pattern: nightly full + delta; support ticket stream requires near-real-time (<5m) updates. Preference for hosted API for time to value; open weights preferred for model transparency (Llama2/Mistral families called out). Customer asked about automatic prefix caching and fallback model routing during spikes. SE notes: focus on batching config, KV cache hit rate, and rerank cross-encoder latency budget. Action items: run P99 bench with Redwood's batching and quantized kernels, deliver cost estimate for steady 1k qps, and confirm SSO test window.
Performance POC (read+rerank) demo 2026-03-20; finalize SOW
SSO integration timeline
budget committee sign-off
PII data handling questions
clarify SLA 
…[truncated]
```

#### #7 `dsid_6bdbaca3a8d84301a2a4b920fdeca63b`

```
Cypress Bay Financial Knowledge Mesh

Summary: enterprise research portal (equities + fixed income research) needs RAG-style search with embeddings + reranking; very sensitive to latency and data residency. Prefer dedicated capacity (predictable throughput) with VPC and KMS integration.\n\nRecent timeline:\n- 2026-02-18: Intro call (Anika / Marco). High-level requirements capture. Fireflies ff_20260218_9b3a.\n- 2026-02-25: Deep-dive with infra + security. Confirmed need for EU residency for subset of datasets. Fireflies ff_20260225_1d7f.\n- 2026-03-03: Sent SAML diagram + initial security questionnaire (drive link).\n- 2026-03-08: Demo of hosted embeddings + basic rerank; internal infra team requested dedicated POC.\n\nRequirements (explicit):\n- Index scale: target 300M-700M embedding vectors initially; plan to shard by product line.\n- Query load: 800-1,200 qps peak expected (intra-day spikes around earnings).\n- Latency SLO: 95th < 120ms, 99th < 250ms for rerank pipeline (embedding search + transformer reranker).\n- Cost sensitivity: looking for <$0.015 per complex query (search + rerank) at scale.\n- Model prefs: open model family preferred; willing to test quantized 8-bit vari
…[truncated]
```

#### #8 `dsid_065ec47b5af54db594c352e0e1dcaf1f`

```
Northwind Embark

SMB ecommerce search team — small ML infra team (1 ML eng, 2 backend engs)
Primary ask: replace current keyword search with semantic doc search + reranking of product pages and support articles
Technical questions: embedding dimensionality (768 vs 1536), best practice for hybrid ranking (BM25 + embeddings), how to do server-side reranking w/ hosted API
Performance targets: 95th percentile latency < 200ms for rerank step; overall search flow < 350ms desirable
Cost sensitivity: ~200k monthly queries across site search and help center — tight budget, wants conservative cost estimate
Integration note: using managed vector DB (VectorPoint) today, wants sample code for bulk upsert, incremental refresh of embeddings
Security: requires SSO for admin UI, audit logging for API keys; preference for US-only data residency
Quote: "We want something that just plugs into our index; zero infra ops. If hosted API gives predictable economics, we can roll out site-wide."
AE/SE tactical: propose 1536 embedding for quality critical rerank, fallback to 768 for cost-sensitive routes; show unit-cost comparisons
Requested artifacts: quickstart repo, example curl + python SDK snippet for e
…[truncated]
```

#### #9 `dsid_dfb4ae719e5643248dad81b2de5baa47`

```
Moonlit Concourse

Embeddings-based retrieval for 10M->50M vectors; two-stage retrieval (ANN recall) + cross-encoder reranker for top-5 quality; 95p E2E <=150ms; VPC with KMS; cost target ~$0.002/query.
Summary: Moonlit Concourse builds a helpdesk + knowledge base for mid-market SaaS; primary objective is aggressive ticket deflection using RAG + reranking.
Go-to-prod ask: replace current sparse keyword search + static FAQ with embeddings-based retrieval + cross-encoder reranker for top-5 precision.
Indexing scale: initial scope 10M tickets + KB articles, target steady-state 50M vectors (logs + attachments), expect 3–4 updates per day per doc (delta indexing).
Latency SLOs: 95th pctile end-to-end (retrieve + rerank) <= 150ms for user-facing agent suggestions; SLA for bot fallback 200ms.
Cost goals: under $0.003/query average at 50k qps peak for deferred batch; POC target $0.0015–0.0025 per served query depending on routing tier.
Model preference: embedding model (768–1536 dim) for vector store; reranker: cross-encoder candidate (BERT-ish) or distilled cross-encoder to hit latency budget.
Routing/fallback: want staged routing — primary dedicated pool in us-east, fallback hosted small
…[truncated]
```

#### #10 `dsid_7c0f737b0560484796c1a9b012160af1`

```
Whitewater Vector Integrations

Summary: enterprise search vendor building knowledge layer for customer support + internal docs. Primary interest: embeddings + reranking pipeline to improve top-k precision at scale.

Requirements / priorities:
- Scale: target production dataset 50M vectors (eventual 150M), initial POC with 2–12M vectors.
- Vector dimensionality: 1536 (OpenAI/Redwood standard embeddings), likely multiple embedding models over time.
- Latency SLO: p50 < 60ms, p95 < 200ms for single-query retrieve+rerank (top-20 retrieval then cross-encoder rerank).
- Cost sensitivity: target $0.0005–$0.003 per query (retrieve + rerank); looking for unit economics analysis for each connector.
- Reranking pipeline: prefer hybrid approach — ANN retrieve on vector DB (GPU optional) + CPU cross-encoder for top-20. Need guidance on where to run cross-encoder (dedicated GPU or CPU pool) to manage cost.
- Connector requirements:
  * Bulk upsert throughput >= 100k vectors/min for initial ingest; incremental upserts with <2s visibility target.
  * Support for hybrid search (BM25 + ANN) or ability to rely on Elastic for sparse + vector DB for dense.
  * Vector index lifecycle APIs: snapshot/exp
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 48: `qst_0251::semantic` · N=25000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to vector retrieval but do not specifically address the performance targets for the overnight vectorization run and interactive response time. The gold chunk is detailed and on-topic, while the retrieved chunks are generally relevant but not specific to the question. The failure mode is likely an embedding near miss due to semantic similarity but not exact mat

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Gold document(s)

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_3388f6da93134707a1fb443e775eabc7`

```
Storied Searchworks

Summary: Storied Searchworks manages ~14M archived media assets (text transcripts, long-form articles, OCRed image text). Primary need: fast, accurate enterprise search + RAG for editorial teams and legal discovery. They are very price-sensitive at scale and need predictable latency for interactive tools.

Data & scale: average document length ~12k words; 95th percentile up to 120k words (OCR-heavy). Prefer to avoid indexing raw long-docs as single vectors. Expect ~60M chunks after current planned chunking strategy; growth ~25%/yr.

Tech priorities discussed:
- Two-stage retrieval: cheap ANN pass (512-d) -> lightweight scorer -> transformer-based reranker for top-K (K=20)
- Chunking: prefer variable-length semantic chunks (200-800 tokens) with 20-30% overlap for passage continuity. Want metadata-preserving chunk ids and original offsets for reunification at display time.
- Reranker tuning: tune on editorial judgments; heavy emphasis on precision@5 and MRR. Discussed training pairwise reranker on company-specific labeled pairs vs using open-source monoBERT/rerank models.
- Embeddings model: evaluation of open LLaMA-derived embedding vs higher-cost proprietary; t
…[truncated]
```

#### #2 `dsid_751af885e0d8442a9b4e167b33ff7841`

```
Inkwell Answers

Moderate index scale (~3-5M documents, mixed short FAQs + long KB articles). Primary flow: query -> sparse+vector hybrid retrieval -> ANN (HNSW) top-50 -> cross-encoder rerank top-5 -> answer generation. Target sustained QPS 700-900, spikes to 2k. End-to-end query latency target 80-120ms (search+rerank budget ~<100ms). Vector dims 1536; prefer hosted embeddings but evaluating open-source 1536-d models. Cost sensitivity: target < $0.02 per user query at scale. Must support per-tenant index isolation and per-customer quotas. SSO (SAML) and audit logs required. US data residency only.
Run 72-hour throughput POC against hosted API (500-2k QPS profile) then review cost telemetry; finalize SOW for 3-month pilot.
SOC2 report requested by security team (in progress)
data residency confirmation for US-only legal review
clarify SLA for sustained >1k QPS
2025-11-20 - lead created from webinar (knowledge-base scaling)
2025-12-02 - discovery call (AE Maya + SE Liam) - confirmed primary use case: SaaS KB RAG for customer support
2026-01-12 - demo of hosted API (chat + embeddings + rerank) - showed live rerank of top-50 -> final top-5
2026-02-10 - security kick-off: requested SOC
…[truncated]
```

#### #3 `dsid_9e5e6325ff084b08898293033de2d391`

```
Retina SearchWorks

Primary: customer support agent + ticket deflection. Use dense embeddings for recall, then fast cross-encoder rerank to ensure top-5 quality for agent suggestions and self-serve KB answers.
Complete perf POC + finalize pricing for 18M doc index; procurement demo 2026-03-18
Clarify high-QPS pricing
Internal security questionnaire (INF-Sec)
Legal approval for data residency clause
Indexing DAG for daily updates
Index target: ~18,000,000 historical tickets (10 yrs), ~1.6B tokens; snapshot size 2-4 TB; ~150k new vectors/day expected during ramp
RAG (semantic search + rerank) QPS target 150-250; reranker top-5 latency budget p95 < 120ms; end-to-end P95 (query->answer) < 400ms for most flows; throughput spike handling to 500 qps with graceful fallback
Will stream ticket updates via Kafka -> incremental embedding pipeline
Need guidance on warm KV cache strategy for bursty chat sessions
Expect connector to internal Confluence + S3 artifact store; must support incremental deletes
2026-02-05 - Initial intro call (AE Liam) - described goals: deflect 35% of tickets, reduce AHT by 20%
2026-02-18 - sent security questionnaire + pricing template (AE)
2026-02-20 - POC kickoff: 
…[truncated]
```

#### #4 `dsid_a6123856d857425bb7419ea99b49e265`

```
Pegatrix MassIndexers

Company background: Pegatrix builds an enterprise search layer for regulated legal and financial corpora. Customers include law firms and compliance teams.
Primary ask: scalable embeddings + reranking pipeline capable of 100M-1B vectors; predictable P95 latency <50ms for retrieve phase, <200ms end-to-end with reranker for top-10.
Workload profile: heavy fanout on retrieval (topK=1k in initial candidate generation), then cross-encoder rerank on top-30. Expect bursts around e-discovery jobs (spikes x5).
Cost sensitivity: unit-cost per query is a key purchasing metric. "Low-per-query" target: <$0.002 per query at 250M vectors baseline, with aggressive batching/caching to hit goals.
Model preferences: prefer open embedding models (ada/variant-style) for CPU/quantize, and a compact cross-encoder (T5-small-ish) for reranker but open to offloading to GPU for latency-critical flows.
Indexing requirements: incremental ingestion, shingling (sliding window embedding), live deletes/PII redaction, and reindex windows every 24-48h for source connectors.
Operational needs: per-route cost & latency dashboards, token-level cost breakdown, automatic fallback to cheaper model v
…[truncated]
```

#### #5 `dsid_c663f74bce354012a30c0b95849b090a`

```
Lithic Code Archives

Account: internal-first search for proprietary codebase + customer-facing devdocs. High priority: replace several brittle grep/Elasticsearch layers with vector-based retrieval + token-aware reranker. Team is infra-heavy (SRE + search engineers). Primary ask: support 40M vectors now, growth to 120M within 12 months; daily full reindex unacceptable -> need delta + streaming reindex. Quote from CTO: 'We need search that scales like storage, not like ML experiments.' Wants end-to-end SSO (SAML) + audit logs and per-namespace residency. Cost sensitivity: will evaluate unit cost at 1M queries/day baseline. Interested in dedicated pools for predictable latency and private deployment for code residency. Short bulleted notes: - heavy emphasis on reranking for precision at top-K - LLM candidate models: open-code-tuned and custodial fine-tunes - caching hot prefixes for frequently accessed repos - compliance: must meet SOC2 plus audit retention 1 year
Scaling: current corpus ~40M embeddings (768-d). Target growth 3x in 12 months. Re-indexing cadence: daily delta + weekly snapshot; ingestion peak 200k vectors/hour. Performance: tail latency P95 < 150ms for top-5 retrieval
…[truncated]
```

#### #6 `dsid_4f571bb8e6574a93a4a65ca03f9ec89c`

```
Valorium Enterprise Retrieval

Top line: large DoD contractor; searching >200M docs (mixed structured/unstructured) across classified/unclassified enclaves. Primary ask: on-prem, air-gapped RAG platform supporting dense embeddings + cross-encoder reranking; strict retention/residency and audit requirements.\n\nRecent activity: \n- 2026-02-09 kickoff call (ff link above). Intro w/ procurement + security + search team. Quick wins: baseline perf numbers and SOW outline agreed.\n- 2026-02-16 SE deep-dive: Diego walked architecture options (dedicated private runtime vs full on-prem). Customer: \"need determinism — can't have bursty cloud fallbacks.\"\n- 2026-02-24 security review w/ CISOs (ff transcript). They requested KMS/HSM proof-of-concept, detailed logging pipeline, and compartmentalized tenant model.\n- 2026-02-28 POC scope agreed: 3-node air-gapped cluster, 100M-doc index (subset), vector index stored on encrypted NVMe, include reranker (cross-encoder) for top-10 re-rank. Metrics: P90 query latency target 250ms (ideally <200ms for short queries), throughput 120 qps sustained, cost per query target (internal) <$0.015.\n\nRequirements summary / customer language: \n- Indexing scal
…[truncated]
```

#### #7 `dsid_c29508f784174459926dcfcf31a58b50`

```
Reverie Botsight

In progress — baseline ingest done (50k), perf run shows viability but cost above target. Next: full ingest to 300k + batching enabled.
Run full-load perf test with batching + reranker pipeline; finalize legal/data residency Qs
legal_data_residency_questions
budget_ceiling
SLA_clarification
2026-01-14: Intro call (AE Jordan) — product fit for KB RAG, emphasized hosted API + high QPS
2026-01-28: Tech deep-dive (SE Maya) — ingestion pipeline, current vector db = self-hosted Postgres+pgvector
2026-02-09: POC kickoff — ingest first 50k docs, baseline embeddings (1536-dim), naive reranker eval
2026-02-22: Mid-POC checkpoint — ran 10k QPS stress window (spike), observed queuing; asked for batching suggestions
2026-03-02: Security questionnaire submitted (legal) — request for SOC2 report + KMS integration details
2026-03-05: Perf run (SE) — simulated 1k QPS steady for 10m, p95 end-to-end retrieval+rerank ~180ms, cost higher than target
Contact: CTO = Lina Morales (wants low TCO for 500k doc KB)
Primary product team building in-app support assistant (SaaS desk) + internal knowledge search
Workload notes: moderate indexing scale (~300k-600k docs), high peak QPS (500-1,200)
…[truncated]
```

#### #8 `dsid_a935e7827ac34cb49ba446eb24dcd055`

```
LucidGrove Answersphere

Finalize POC perf run + receive security checklist answers
SOC2 audit pending
data residency details for EU customers
cost per q unknown
2025-02-10 — initial intro call, AE Jordan Hale; product fit looks good
2025-02-18 — SE workshop (Priya) demoed embeddings + reranker flow; focused on latency
2025-02-27 — security intro; asked for SOC2 + KMS details; sent security FAQ
2025-03-01 — provided sample token-cost calc; requested POC SLA
2025-03-03 — scheduled POC perf run for 2025-03-10; need dataset and query profile
Indexing scale: ~300k canonical KB articles + 200k historical support tickets (total ~500k docs)
Peak QPS: 500-1,200 queries/sec; steady 300 qps
Latency SLO: embed lookup <=50ms, reranker + top-k re-rank <=120ms p95
Cost target: <$0.02 per query (avg) across lookup+rerank
Model preference: quantized open models for embeddings; small/medium reranker (7B-13B)
Routing: simple cost-based fallback to smaller reranker on spike; regional routing to eu-west for EU traffic
Security: SSO (SAML), audit logs, KMS for keying, retention controls, EU data residency for some customers
Deliver sample eval harness by 2025-03-07 (redwood SDK + query simulator)
POC p
…[truncated]
```

#### #9 `dsid_5be817654250421db53ca7552b9a3d00`

```
FathomLine Support Intelligence

2024-11-05 - Inbound lead via webinar (low-latency RAG talk). Jordan (AE) assigned.
2024-11-12 - Discovery call w/ CTO (Maya Chen) + Head of AI Ops (Ravi Kapoor). Key ask: "replace current embedding tier with a single platform that guarantees p95 <200ms for top-5 retrieval + rerank."
2024-12-03 - Sent Redwood capabilities deck and dedicated pricing sketch (drive link). Asked for estimated ARR band prerequisites for Dedicated vs Private.
2025-01-10 - Security questionnaire submitted. They flagged need for KMS integration + audit logs retention 1 year.
2025-01-22 - Architecture deep-dive (Fireflies ff_20250122_9103). Discussed hybrid approach: ANN index for recall, cross-encoder reranker for top-5 quality. They want cross-encoder only on narrowed candidates (5-20) to hit cost/latency targets.
2025-02-05 - Pricing follow-up (Fireflies ff_20250205_0048). Customer: "we need hard numbers: cost/query at 100k/mo, 1M/mo, 5M/mo. Also want model fallback chain for capacity outages."
POC scope notes: index size target 8-12M ticket vectors (1-3TB storage depending on vector dim and compression). Expect average query fanout 128 -> ANN candidate set ~100 -> rerank
…[truncated]
```

#### #10 `dsid_e611d79c110248d9853fb40b4be0e216`

```
Pegasus Compass

Shorthand from calls / internal: customer is running a SaaS help center and in-app support chat. Primary goal: accurate doc search + answer generation for agents and automated chat. Wants embeddings + cross-encoder rerank to keep top-k precise. CTO quote: "Need <150ms p99 at 1k qps or it's a non-starter." Pricing sensitivity: target unit cost <$0.004 per full query (embedding + rerank). Current dataset: ~2.5M docs expected at scale (mix of long articles and short FAQs). Ingest pattern: nightly full + delta; support ticket stream requires near-real-time (<5m) updates. Preference for hosted API for time to value; open weights preferred for model transparency (Llama2/Mistral families called out). Customer asked about automatic prefix caching and fallback model routing during spikes. SE notes: focus on batching config, KV cache hit rate, and rerank cross-encoder latency budget. Action items: run P99 bench with Redwood's batching and quantized kernels, deliver cost estimate for steady 1k qps, and confirm SSO test window.
Performance POC (read+rerank) demo 2026-03-20; finalize SOW
SSO integration timeline
budget committee sign-off
PII data handling questions
clarify SLA 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 49: `qst_0251::semantic` · N=100000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`unsure` mode=`other`
- **LLM note:** llm_error: OpenAI HTTP 429: {
    "error": {
        "message": "Rate limit reached for gpt-4o in organization org-XSSQmWIx80t1tvfOCV1hxO4V on tokens per min (TPM): Limit 30000, Used 27876, Requested 2568. Please try again in 888ms. Visit https://platform.openai.com/account/rate-limits to learn more.",
        "type": "tokens",
        "param": null,
        "code": "rate_limit_exceeded"
    }
}

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Gold document(s)

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_3388f6da93134707a1fb443e775eabc7`

```
Storied Searchworks

Summary: Storied Searchworks manages ~14M archived media assets (text transcripts, long-form articles, OCRed image text). Primary need: fast, accurate enterprise search + RAG for editorial teams and legal discovery. They are very price-sensitive at scale and need predictable latency for interactive tools.

Data & scale: average document length ~12k words; 95th percentile up to 120k words (OCR-heavy). Prefer to avoid indexing raw long-docs as single vectors. Expect ~60M chunks after current planned chunking strategy; growth ~25%/yr.

Tech priorities discussed:
- Two-stage retrieval: cheap ANN pass (512-d) -> lightweight scorer -> transformer-based reranker for top-K (K=20)
- Chunking: prefer variable-length semantic chunks (200-800 tokens) with 20-30% overlap for passage continuity. Want metadata-preserving chunk ids and original offsets for reunification at display time.
- Reranker tuning: tune on editorial judgments; heavy emphasis on precision@5 and MRR. Discussed training pairwise reranker on company-specific labeled pairs vs using open-source monoBERT/rerank models.
- Embeddings model: evaluation of open LLaMA-derived embedding vs higher-cost proprietary; t
…[truncated]
```

#### #2 `dsid_447b145145ac475da57a16ae41af5f0b`

```
AnchorBright Search

2026-03-10 - Inbound form: signed up for free tier, product interest = doc search / RAG
2026-03-12 - Auto-welcome email + quickstart sent (link to docs + embed example)
2026-03-15 - AE outreach (Priya) — short intro, asked for architecture diagram
2026-03-18 - Intro call (Fireflies id ff_20260318_anchbri_call_01): demo of their current vector pipeline; asked about reranking
2026-03-20 - SE sync (Sam Chen): technical Qs on embedding dims, batch endpoints, vector DB connectors
2026-03-25 - Follow-up email with sample cost estimates and suggested POC scope
Inbound lead from blog post about 'building a smarter doc search' — signed up for self-serve. Fast-moving SMB, 20 engineers + PMs.

Problem: customers (SMBs) need accurate answers from multi-pdf repos. Current flow: extract text -> create embeddings -> store in Supabase vector extension -> nearest-neighbor -> return top-k, then simple prompt to LLM for answer. Results are noisy: need reranking stage and tuned prompts.

What they asked on call:
- Can Redwood hosted API handle async batch embedding ingestion (50k docs initial import) and provide throughput estimates?
- Reranking patterns: prefer to run embedding-b
…[truncated]
```

#### #3 `dsid_7032728f84204589803d0ee2cc72ac84`

```
EchoQuarry SupportSearch

Scale: target index 8-12M doc chunks. Throughput: 80 qps sustained for peak customers, burst to 250 qps. Latency: tight tail SLOs for end-to-end RAG (see notes). Quality: top-5 reranking precision target >= 85%. Security: VPC, SAML SSO, KMS, audit logs. Compliance: SOC2 required; interest in ISO later.
Context: enterprise support SaaS (B2B) that powers live chat + ticketing for ~150 enterprise customers. Current search stack: Elastic cluster + custom TF-IDF + light re-ranker (on CPU). Looking to move to dense embeddings + neural reranker for top-5 precision to reduce escalations and deflect tickets. Key asks: index scale ~8-12M docs (KB articles + historical tickets), tail-latency guarantee for retrieval+rerank, predictable cost per query for pricing to customers.

Conversation highlights: 
- "We need top-5 answers to match agent quality 85% of the time, otherwise escalations spike." (VP Eng)
- Customer strongly prefers VPC deployment initially, may consider Dedicated pools if latency/cost tradeoffs look good.
- Security: must support SSO (SAML), KMS-managed keys, and audit logging + 7-year retention policy for some enterprise customers.
- Cost target: int
…[truncated]
```

#### #4 `dsid_c9afc162f3b04610a5edc3f68287972d`

```
Aquifer Lookup

Customer will power support article search and an in-app Q&A assistant. Plan: nightly full reindex + streaming upserts for recent docs; query flow is: (1) user query -> embed via hosted API -> kNN search in vector DB -> optional dense rerank via hosted API. Want to minimize rerank calls to top 10 results.
Early-stage SMB focused on integrating RAG into their support search product.
- Primary ask: hosted API for embeddings + dense reranking into existing vector DB.
- Tech constraints: current vector DB is a managed Redis+vector plugin (trial); want guidance on recommended vector dimensions, indexing strategy, and upsert throughput.
- Latency goal: p95 lookup <200ms; end-to-end query (embed lookup + rerank) <500ms.
- Cost sensitivity: team is price-conscious (startup budget), wants guidance on token vs embedding cost tradeoffs.
- Security: require SSO (SAML) and audit logging for production; data residency not required today.
- Quote from CTO: "Need near-realtime index updates from our ingestion pipeline (~1-2s)", wants to confirm host API supports that pattern.
- SE notes: potential quick win using hosted API embeddings + client-side hybrid search (BM25 + dense) to r
…[truncated]
```

#### #5 `dsid_751af885e0d8442a9b4e167b33ff7841`

```
Inkwell Answers

Moderate index scale (~3-5M documents, mixed short FAQs + long KB articles). Primary flow: query -> sparse+vector hybrid retrieval -> ANN (HNSW) top-50 -> cross-encoder rerank top-5 -> answer generation. Target sustained QPS 700-900, spikes to 2k. End-to-end query latency target 80-120ms (search+rerank budget ~<100ms). Vector dims 1536; prefer hosted embeddings but evaluating open-source 1536-d models. Cost sensitivity: target < $0.02 per user query at scale. Must support per-tenant index isolation and per-customer quotas. SSO (SAML) and audit logs required. US data residency only.
Run 72-hour throughput POC against hosted API (500-2k QPS profile) then review cost telemetry; finalize SOW for 3-month pilot.
SOC2 report requested by security team (in progress)
data residency confirmation for US-only legal review
clarify SLA for sustained >1k QPS
2025-11-20 - lead created from webinar (knowledge-base scaling)
2025-12-02 - discovery call (AE Maya + SE Liam) - confirmed primary use case: SaaS KB RAG for customer support
2026-01-12 - demo of hosted API (chat + embeddings + rerank) - showed live rerank of top-50 -> final top-5
2026-02-10 - security kick-off: requested SOC
…[truncated]
```

#### #6 `dsid_af63752ecdc44ba3a8ec5f8082ac3d89`

```
Midtown Retrieval Works

Run 72-hour high-QPS POC on hosted API + finalize security questionnaire
clarify cost_per_query model at 300+ QPS
security questionnaire responses (DPA, KMS)
indexing throughput & warm-up plan
contract terms re: data residency
2025-11-05: Intro call (Avery) — high level use case: KB RAG for multi-tenant SaaS support portal; likes hosted API simplicity
2025-12-02: Demo — showed two-stage retrieval (ann + reranker) and cost model; client asked for concrete QPS costing
2026-01-18: Security intake submitted — requested SOC2 report, DPA, KMS integration details
2026-02-05: Deep technical call (Diego + infra) — discussed indexing cadence, update latency, and shard sizing for ~3M docs
2026-02-12: Proposal v2 shared; asked for 72-hour soak test at 300 QPS; legal asked for data residency clarifications
2026-02-14: Pricing follow-up, client confirmed budget band and pushed for reranker latency numbers
Workload: SaaS customer KB retrieval; multi-tenant per-customer indices; average corpus per tenant 500k-1.5M docs; aggregate index ~3M docs
QPS: baseline 100-200 qps, peak 300-400 qps during support hours, burst tolerance to 600 qps
Latency SLO: 95th percentile retrieva
…[truncated]
```

#### #7 `dsid_dde0b07ea5fe4658b918743a264291ce`

```
Praxis Echelon

2025-01-15 - Intro call (Maya/Julián) - customer describes 'aggressive latency requirements; cannot exceed 350ms for top-5 results'
2025-01-29 - Sent security questionnaire; customer flagged HSM/KMS + audit logging as must-haves
2025-02-12 - Deep dive w/SE (Julian) - walked through caching, prefix-KV, and reranker architecture (ff_20250212_07k9c)
2025-02-18 - Customer shared eval dataset (45k tickets + KB). Wants embeddings dimension 1536 and deterministic reranker reproducibility
2025-02-28 - Pricing deck delivered (drive:/PraxisEchelon/Redwood_POC_Pricing_v2.pdf). Customer asked for committed capacity quote for 100M q/mo
2025-03-05 - Live perf call; observed p95 retrieval ~120ms in hosted trial but p99 spikes on large queries (ff_20250305_1b2xv)
Quote from Liam: 'We need to be able to surface the right KB article top-3 in under 200ms — anything slower is a dealbreaker for deflection.'
Security/Legal: require EU data residency for EU customer subset; want SOC2 + ISO evidence and KMS key control flow docs
Ops note: interested in automatic batching suggestions from Redwood Optimize and model quantization recommendations for reranker
POC completion + perf review; fina
…[truncated]
```

#### #8 `dsid_5b4d475cf8ea46dba627b40368b1ac00`

```
LumenBridge CodexSearch

Account snapshot: mid-stage engineering org building enterprise code search for internal devs + mkt product. Heavy emphasis on embeddings + reranker pipeline.

Recent call notes (paraphrased):
- 2026-02-25 onsite sync: SE demo of hybrid embeddings + LightGBM reranker; product team asked about latency tradeoffs.
- 2026-02-18 security deep-dive: SSO/SAML mapping and encryption-at-rest confirmed; legal asked about data residency for EU customers.
- 2026-02-04 kickoff POC: Blake (CTO) "we need sub-75ms median, p99 under 450ms for developer queries"; wants cost projection per query at 1M vectors.

Shorthand:
- primary workload: code search across monorepos (700k->5M files projected), frequent re-index (daily delta, weekly full), embeddings updated with new commits.
- reranking: lightweight neural reranker + features from commit history, repo metadata.
- cost sensitivity: wants clear cost per query and break-even vs self-hosting.
- infra preference: VPC private control plane, potential air-gapped for certain customers later.

Customer quote snippets:
- "We can't tolerate confusing false positives — precision > recall tradeoff acceptable but must be tunable."
- "S
…[truncated]
```

#### #9 `dsid_9e5e6325ff084b08898293033de2d391`

```
Retina SearchWorks

Primary: customer support agent + ticket deflection. Use dense embeddings for recall, then fast cross-encoder rerank to ensure top-5 quality for agent suggestions and self-serve KB answers.
Complete perf POC + finalize pricing for 18M doc index; procurement demo 2026-03-18
Clarify high-QPS pricing
Internal security questionnaire (INF-Sec)
Legal approval for data residency clause
Indexing DAG for daily updates
Index target: ~18,000,000 historical tickets (10 yrs), ~1.6B tokens; snapshot size 2-4 TB; ~150k new vectors/day expected during ramp
RAG (semantic search + rerank) QPS target 150-250; reranker top-5 latency budget p95 < 120ms; end-to-end P95 (query->answer) < 400ms for most flows; throughput spike handling to 500 qps with graceful fallback
Will stream ticket updates via Kafka -> incremental embedding pipeline
Need guidance on warm KV cache strategy for bursty chat sessions
Expect connector to internal Confluence + S3 artifact store; must support incremental deletes
2026-02-05 - Initial intro call (AE Liam) - described goals: deflect 35% of tickets, reduce AHT by 20%
2026-02-18 - sent security questionnaire + pricing template (AE)
2026-02-20 - POC kickoff: 
…[truncated]
```

#### #10 `dsid_d350205a78c0485cafc26c52837a95b4`

```
Sentinel VectorWorks

Key ask: scalable embeddings + reranking pipeline for enterprise search across legal corpora (contracts, briefs, memos).
Customer wants to index ~10-50M unique docs initially; expects growth to 200M in 18 months.
Quote from CTO: 'Latency under 200ms for 95th pctl is make-or-break for internal tools'
POC currently comparing Weaviate (vector + filters), pgvector (cost control, local), and Elastic (hybrid BM25+ANN).
Priority: hybrid search (BM25 metadata + ANN embeddings), plus lightweight reranker stage to push quality for top-K results.
Explicit connector requirements called out by infra: streaming upserts via CDC, idempotent bulk ingestion, per-vector metadata tags, conditional deletes, per-tenant namespaces.
Security: must be able to bring keys (KMS/HSM) and export audit logs to their SIEM; retention controls required for legal holds.
Cost sensitivity: >10M queries/month puts cost/per-query as first-class decision variable; they want price modeling for both hosted and dedicated setups.
They have an internal pgvector PoC but are concerned about shard management and query latency at scale.
Drive deck includes baseline cost model (see linked_drive_docs).
SE note
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 50: `qst_0252::semantic` · N=15000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are somewhat relevant to incident response but do not specifically address the criteria for a quick after-action review based on impact duration and customer impact. The failure mode is likely an embedding near miss due to semantic similarities but not exact matches. The chunk quality is moderate, with relevant but not directly applicable content.

### Question

In our incident response process, what is the rule for when a quick time-boxed after-action review is acceptable instead of writing the full formal analysis, based on impact duration and whether the issue hit one customer versus many?

### Gold document(s)

#### GOLD `dsid_01eaeaf6045941beaeaf74e6170aceea`

```
Responder rotation synthesis and deferred postmortem protocol

Overview:\n\nThis playbook describes Redwood's responder rotation synthesis process and a lightweight Deferred Postmortem (DPM) protocol for incidents that meet defined criteria. It combines on-call scheduling practices, a structured bridge handoff procedure, and customer-facing messaging templates designed for speed and clarity. The goal is to reduce cognitive load during high-impact events and to ensure timely learning when full postmortems are not immediately practical.\n\nScope:\n- Applies to: SRE, Serving Runtime, Platform, and Incident Response stakeholders.\n- Excludes: low-priority alerts that resolve without human intervention (see 'Auto-resolved alerts' below).\n\nDefinitions:\n- Responder rotation synthesis: periodic review and rebalancing of on-call shifts, handoffs, and escalation ladders to maintain equitable load and coverage.\n- Deferred Postmortem (DPM): a time-boxed post-incident review that defers non-critical analysis until stakeholders are available, while still capturing root evidence and action items immediately.\n\nKey principles:\n1) Fast stabilization first: prioritize containment and customer impact minimization.\n2) Minimal friction handoffs: standardized bridge transfer reduces repeated context overhead.\n3) Continuous learning: short DPMs for low-severity incidents; full postmortems for Sev1/Sev2.\n4) Equity in rotations: no responder assigned >36 hours continuous duty without relief.\n\nOn-call rotation design (synthesis process):\n1. Quarterly synthesis review (owner: SRE lead):\n   - Pull the last quarter's on-call logs and pager counts.\n   - Calculate median and 95th percentile pager counts per responder.\n   - Identify top-10% busiest windows and common root causes.\n2. Rebalance rules:\n   - Move noisy services to a dedicated micro-rotation if they account for >25% of pages.\n   - Limit night-weekend primary duty to volunteers in the rotation unless emergency staffing required.\n3. Local fairness check (monthly):\n   - Team leads run a 15-minute review in the first week of each month to confirm schedule fairness and swap if needed.\n\nRotation constraints (config)
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_d0f651d038ca44868cc31facb0331d84`

```
External outage chronicle and technical safeguards brief

Purpose and audience:\nThis is a customer-facing draft that combines a concise status-page update format with a longer post-incident chronicle and technical safeguards summary. Intended recipients: account owners, SRE contacts, and technical product leads at impacted customers.\n\nDocument goals:\n- Provide a short, clear status page blurb customers can post to their teams immediately.\n- Offer a longer chronological timeline and technical explanation suitable for customers who require forensic detail.\n- Describe mitigations we applied in real time and durable safeguards we will implement to reduce recurrence risk.\n- Template section for customer-facing follow-up (compensation/credit language, SLA implications).\n\nQuick status (1-2 sentence status-page blurb) — short form for 1st update:\n- Incident started: 2026-08-08 14:22 UTC. Impact: multi-region elevated latency and transient request failures for text-generation endpoints.\n- Current status: degradation mitigations in place; partial recovery observed in US-east and EU-west; APAC region traffic is routed to fallback pools. Investigations ongoing; no data loss.\n\nExpa
…[truncated]
```

#### #2 `dsid_4f82a120ef1442fa9bd7189c9833e3ae`

```
emergency-comms-runbook-and-status-templates

Practical runbook draft for SRE incident communications focused on fast, clear external status updates, customer-facing emails, and an internal war-room checklist. Designed to reduce cognitive load during high-severity incidents and provide copy+paste-ready templates for status.page, email, and Slack. Meant to complement the incident response checklist (see linked Confluence).
sev0: service down / API returns 500s or >50% request error rate / major data loss; require immediate war-room.
sev1: degraded performance or partial feature outage impacting a subset of customers; war-room if impact widens.
sev2: intermittent errors or increased latency with mitigation available; handle via on-call + async comms.
sev3: informational (scheduled maintenance, low-impact bugs).
Trigger external comms when any of: sustained error rate >5% across production for 5+ minutes, latency p50 increases >2x baseline and p95 >4x baseline, customer-facing feature completely unavailable for >2 customers in a 10-minute window, or when Postmortem Owner deems customer notification appropriate. If in doubt, err on the side of transparency and post an initial holding m
…[truncated]
```

#### #3 `dsid_4c9c686c513a4946b335f17a8da911f1`

```
Oncall Hackbook: Fast Repair Patterns for API Stalls and Rate Surges

Purpose:
This is a compact, operator-focused hackbook for rapid triage and temporary remediation of common API failure classes we repeatedly see in production: hard timeouts, client 429s (rate-limited behaviour), degraded streaming (stalling or truncated/choppy chunks), and elevated error rates (5xx bursts).

Scope and intent:
- Not an exhaustive incident timeline; this is a fast-reference for first responders to reduce blast radius and buy time for deeper fixes.
- Prefer safe, reversible actions. Prioritize keeping downstream product UX alive (graceful degradation, cached responses, feature flags).
- Capture whatever you do in the incident channel (timestamps + why).

Signals that should trigger this playbook:
- Sudden spike in p50/p95 latency or tail latencies crossing SLOs for a route
- Surge of 429 responses in metrics or customer reports of throttled calls
- Streaming sessions showing appended partial tokens or long pauses (>2s chunk gap)
- Spike in 5xx (5xx-rate > 3x baseline for >5m)

Quick triage checklist (first 12 minutes):
1) Scope: which route(s) and region(s)? (logs + dashboards)
   - Query traces pe
…[truncated]
```

#### #4 `dsid_b360d00be3f84b08b1a879d102835d2f`

```
Post-incident summary template (publishable)

## Purpose
This template is used to produce **customer-publishable** post-incident summaries for Redwood’s public status page and linked surfaces (e.g., Console). The goal is to provide a timely, accurate account of:
- **Customer impact** (what customers experienced)
- **Timeline** (when it started, when it was mitigated, when it was fully resolved)
- **Root cause class** (what kind of failure occurred, without leaking sensitive details)
- **Mitigations and prevention** (what we did immediately and what we are changing)

This template is designed to be:
- Clear to a non-Redwood audience
- Consistent across Hosted, Dedicated, and Private messaging
- Safe to publish (see confidentiality rules below)

---

## When to publish
Use this summary when an incident is customer-visible and any of the following are true:
- Severity is **Sev0–Sev2** (or equivalent) OR
- The incident resulted in a public status page incident OR
- Support/CS requests a publishable follow-up due to customer escalation

### Timing targets (guidance, not a commitment)
- **Sev0/Sev1:** publish within **2 business days** of resolution
- **Sev2:** publish within **5 busines
…[truncated]
```

#### #5 `dsid_3b7139962b28486aaa3a498cb375b2a9`

```
Incident Orchestration Decision Canvas and Runbook

Overview\n\nThis page documents a combined decision canvas and runnable playbook for on-call responders at Redwood Inference. The intent is to give a clear, SLO-driven decision process that: 1) shortens time-to-containment, 2) reduces noisy escalations, and 3) improves evidence collection for post-incident analysis. Use this page as the primary guide when an active incident affects customer-facing inference services (hosted API, Dedicated, or Private control plane).\n\nScope\n\n- Applies to incidents that impact latency, availability, correctness (quality regressions), or billing/quotas for inference endpoints.\n- Does NOT replace service-specific runbooks for deployment, onboarding, or infra reconfiguration; it is the orchestration layer to choose which runbook and communications path to use.\n\nQuick facts and SLO thresholds (production)\n\n- Availability SLO: 99.95% (per-region, 30d rolling).\n- Latency SLO: p99 < 350ms for short-form generate endpoints; p99 < 700ms for long-sequence pipelines.\n- Error budget alert: Trigger when 7-day rolling availability drops below 99.9% or error-rate increase > 2x baseline for 30 minutes.\n
…[truncated]
```

#### #6 `dsid_aaf549b678034217953d420252250815`

```
Urgent service degradation — spokes notes and Q&A (standby)

Purpose: quick-reference spokes notes and Q&A for managers on standby while we triage degraded serving in us-west-2. This is a personal scratchpad — short, blunt, editable.

Key principles to keep in all comms:
- Acknowledge quickly, be factual, avoid speculation.
- Reassure with observable actions (teams, mitigation steps, ETA windows).
- Surface customer impact clearly (who, how many requests, which APIs/routes).
- Commit to follow-up: timeline for next update and postmortem cadence.

Suggested Slack announcement (short, sent by @ravi or @oncall):
"Heads up — we're seeing degraded latency and increased errors for text-generation routes in us-west-2 (hosted API). Engineering is investigating. If you're experiencing failed requests, please retry after ~30s. We'll post updates every 15–30 minutes and share a postmortem. Incident key: JIRA-INC-4312."

Longer note for internal channel or email to CS/GTM leads: (copyable)
- What happened: starting ~09:12 PDT we observed 5xx spikes and P95 token latency > 3s for /v1/generate and chat endpoints in us-west-2. Traffic reduction measures were auto-triggered but errors continued fo
…[truncated]
```

#### #7 `dsid_51877a563b0d4f42a63e33d7735913ff`

```
Responder Guidance and Simulation Labs with Templates

Summary:\nThis document is a compact, operational reference for responders, rotation leads, and incident controllers. It combines: severity definitions and triage ladders, a quick-run containment checklist, standardized status page and customer communication templates, a blameless postmortem timeline, and a small library of hands-on simulation (game-day) scenarios and lab steps. Designed to be printed on a single page for pager responders and expanded in linked runbooks for each service.\n\nGoals and intended audience:\n- Goals: reduce time-to-stable, standardize communications, ensure actionable post-incident follow-up, and improve responder readiness through repeatable simulations.\n- Audience: primary on-call responders (SRE/Platform, Serving Runtime, Infra), incident commanders, product-support liaisons, and on-call rotation managers.\n\nDefinitions and severity matrix (quick reference):\n| Severity | Impact description | Target initial response | Example triggers |\n|---|---|---:|---|\n| Sev0 | System-wide outage affecting >95% of traffic / external customer blocking | 5 minutes | API unavailable, entire region down |\n| S
…[truncated]
```

#### #8 `dsid_c24658680cc94dcfb0a25ff8103ac916`

```
Incident brief and customer action plan — May 5 impact on inference latency

From: Ben Carter <ben.carter@redwood.com>
To: BlueHarbor IT Ops <it-ops@blueharbor.com>, Carlos Mendez <carlos.mendez@blueharbor.com>
Cc: Lauren Bishop <lauren_bishop@redwood.com>, Markus Klein <markus_klein@redwood.com>
Date: Wed, 5 May 2027 09:15:00 -0700
Subject: Incident brief and customer action plan — May 5 impact on inference latency

Hi Carlos / BlueHarbor team,

Thank you for your patience while we investigated the increased latency some of your inference requests experienced this morning. We take these incidents seriously and want to share an interim customer-facing summary plus our immediate remediation actions. A final post-incident report with a full timeline and long-term mitigations is attached (customer-facing-postmortem-draft.pdf).

Quick summary
- What happened: A surge of short-lived bursts caused the autoscaler to under-provision GPUs for a subset of generation workloads in the us-west-2 cluster, resulting in queued requests and elevated p95/p99 latency.
- Impact window: 03:12:10 UTC — 03:49:22 UTC on 2027-05-05 (approx 37 minutes).
- Customer impact: ~0.9% of total inference requests f
…[truncated]
```

#### #9 `dsid_8cc9488676c647e2a22ee8b8bc7e890a`

```
Critical Latency Fast-Recovery Playbook and On‑Call Toolkit

Overview:\n\nPurpose: This playbook provides a single, opinionated response flow for critical latency incidents (service-level latency regression impacting customer-visible requests). It combines immediate triage steps, runbook playbooks for common latency root causes, escalation rules, status page and customer communications templates, and a lightweight postmortem checklist to ensure timely recovery and measurable improvements.\n\nScope: Applies to API services and inference routing layers that are part of the hosted Redwood API and Dedicated frontends. This doc does NOT replace component-specific runbooks for non-latency failures (eg. data-plane corruption) but should be used when P99/P95 latency spikes or sustained degradation are observed.\n\nOwner and contacts:\n- Primary on-call: API Platform SRE (team: eng-sre) — person who owns the paging channel\n- Secondary on-call: Serving Runtime on-call (team: eng-serving-runtime)\n- Incident lead: rotating Senior SRE/PM technical lead (assigned at incident start)\n\nKey contacts (phone/Slack):\n| Role | Team | Pager / Slack channel | Typical response time expectation |\n|---
…[truncated]
```

#### #10 `dsid_9b4db0cb7a42489a91686818c91882a1`

```
Incident tactical brief & customer-facing templates

Purpose
This is a tactical working brief for customer-facing comms during infrastructure or inference incidents. Includes short status-page-ready text blocks, staggered update templates, a customer postmortem summary scaffold, and suggested SLA/credit language for commercial customers. Use these as starting text — keep edits minimal during an incident to avoid confusion.

Audience
Primary: customer-success managers, account managers, solutions engineers who need to post or escalate status updates. Secondary: SRE/ops for timeline facts and engineering-led postmortems.

How to use
- Pick the block that matches impact level (degraded, partial outage, full outage).
- Fill in the placeholders in ALL CAPS (e.g., {AFFECTED_REGION}, {ESTIMATED_RESTORE}).
- Keep the first public status update short (<= 3 sentences) and mark ‘investigating’.
- For targeted email to Enterprise customers, include timelines and a named escalation contact.

QUICK STATUS PAGE SNIPPETS (copy/paste)
1) Investigating — short (public status page)
Title: Degraded inference throughput for hosted-api in {REGION}
Summary: We are investigating increased request latency 
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 51: `qst_0252::semantic` · N=50000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to incident response but do not specifically address the criteria for a quick after-action review based on impact duration and customer scope. The failure mode is lexical mismatch as the retrieval did not capture the specific criteria outlined in the question.

### Question

In our incident response process, what is the rule for when a quick time-boxed after-action review is acceptable instead of writing the full formal analysis, based on impact duration and whether the issue hit one customer versus many?

### Gold document(s)

#### GOLD `dsid_01eaeaf6045941beaeaf74e6170aceea`

```
Responder rotation synthesis and deferred postmortem protocol

Overview:\n\nThis playbook describes Redwood's responder rotation synthesis process and a lightweight Deferred Postmortem (DPM) protocol for incidents that meet defined criteria. It combines on-call scheduling practices, a structured bridge handoff procedure, and customer-facing messaging templates designed for speed and clarity. The goal is to reduce cognitive load during high-impact events and to ensure timely learning when full postmortems are not immediately practical.\n\nScope:\n- Applies to: SRE, Serving Runtime, Platform, and Incident Response stakeholders.\n- Excludes: low-priority alerts that resolve without human intervention (see 'Auto-resolved alerts' below).\n\nDefinitions:\n- Responder rotation synthesis: periodic review and rebalancing of on-call shifts, handoffs, and escalation ladders to maintain equitable load and coverage.\n- Deferred Postmortem (DPM): a time-boxed post-incident review that defers non-critical analysis until stakeholders are available, while still capturing root evidence and action items immediately.\n\nKey principles:\n1) Fast stabilization first: prioritize containment and customer impact minimization.\n2) Minimal friction handoffs: standardized bridge transfer reduces repeated context overhead.\n3) Continuous learning: short DPMs for low-severity incidents; full postmortems for Sev1/Sev2.\n4) Equity in rotations: no responder assigned >36 hours continuous duty without relief.\n\nOn-call rotation design (synthesis process):\n1. Quarterly synthesis review (owner: SRE lead):\n   - Pull the last quarter's on-call logs and pager counts.\n   - Calculate median and 95th percentile pager counts per responder.\n   - Identify top-10% busiest windows and common root causes.\n2. Rebalance rules:\n   - Move noisy services to a dedicated micro-rotation if they account for >25% of pages.\n   - Limit night-weekend primary duty to volunteers in the rotation unless emergency staffing required.\n3. Local fairness check (monthly):\n   - Team leads run a 15-minute review in the first week of each month to confirm schedule fairness and swap if needed.\n\nRotation constraints (config)
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_15e23a53f5124b67ac74eec12a9c59a0`

```
Postmortem-to-QBR Translation and Customer Readout Playbook

Purpose:\nThis playbook defines a repeatable process for turning internal incident postmortem findings into a concise, customer-facing QBR (Quarterly Business Review) narrative and readout. The goal is to:\n- Surface root causes and mitigations in a way that maps to customer SLAs/SLOs and business impact.\n- Provide a clear, action-oriented plan customers can review and sign off on.\n- Standardize the rhythm and artifacts for CS-led incident readouts so engineering, SRE, and account teams stay aligned.\n\nWhen to use this playbook:\n1) Any incident that triggered a postmortem with customer-visible impact (latency SLO breach, model-quality regression, outage affecting >1% of tenant traffic, billing anomalies tied to runaway token usage).\n2) Major configuration or migration failures that change expected behaviour for a customer.\n3) Recurring or high-severity issues flagged by the Customer Success or Enterprise Support teams.\n\nScope and audience:\n- Primary audience: Customer Success Manager (CSM), Account Executive (AE), Engineering Lead on the incident, and the affected customer’s technical stakeholders.\n- Secondary a
…[truncated]
```

#### #2 `dsid_bb8ff87e19ec43afa947c80233d3dbaf`

```
Containment Checklists and Post-Incident Learning Path

Actionable containment checklists for common Redwood incident classes plus a structured post-incident learning path and governance checklist. This page is the single-source reference for first-responder actions, communications cadence, and how to convert incidents into prioritized engineering work and measurable improvements.
On-call engineers, SREs, incident commanders, product and CS leads responsible for customer communications, and owners of production services.
This document provides concise, role-oriented containment checklists (what to do in the first 30/60/120 minutes), a severity classification table tied to SLO impact, a template cadence for internal and external communications, and the Post-Incident Learning Path that turns incidents into tracked improvements. Use these checklists immediately when an incident is suspected; escalate to the Incident Commander (IC) when a checklist does not restore service within the first containment window.
Severity | Customer Impact | Typical SLO Signal | Target Response Window
--------|----------------|-------------------|------------------------
P0 (Sev-0) | Complete service outag
…[truncated]
```

#### #3 `dsid_f1f8c246c42d4b9e8030b6320d6fb0ad`

```
Ten-Minute Stabilization Checklist and Customer Briefs

Overview

Purpose: This document is a compact, prescriptive playbook for the first 10 minutes after an operational signal that materially affects customer experience. It combines a rapid-stabilization checklist, service-specific mitigations for common failure modes, a clear escalation ladder, and customer-facing status templates suitable for status.redwood.ai and enterprise communication. Use this when SLOs are at risk (see SLO section) or when an incident is declared.

Scope: Production services that impact hosted inference, Dedicated pools (redwood-dedicated-*), and Private control plane components. Not intended for minor developer-facing issues or backlog tasks.

Audience: On-call engineers, incident commanders, customer success, and on-call rotation leads.

Service ownership and SLOs

- Example services in scope:
  - redwood-serve-api (external REST/streaming gateway)
  - runtime-inference (GPU serving runtime pool)
  - kv-cache (Redis cluster used for prefix caching)
  - routing-proxy (smart-request-router)
- Key SLOs to watch (example thresholds):
  - Availability (p99 request success) target: 99.95% per region
  - Laten
…[truncated]
```

#### #4 `dsid_16af07ca08904644989072866aab7b6d`

```
QBR action plan template for model quality regression

Overview

This document is a repeatable QBR action-plan template to triage, contain, and communicate model quality regressions observed for enterprise customers. It is intended for Customer Success, Solutions Engineering, and the Model Ops/Applied ML teams to prepare a concise, technical-to-executive handoff that can be reviewed during a QBR or an ad-hoc postmortem review.

When to use this template

- Any sustained customer-facing degradation in automated evaluation metrics (examples: eval score drop >= 5% relative, BLEU/ROUGE delta, semantic-similarity regression, or embedding downstream accuracy drop).
- Significant rise in customer complaints tied to model outputs (false positives/negatives, hallucinations, policy violations).
- Persistent customer-side error-rate or latency increase that correlates with model changes.

Quick summary structure (one-slide / one-paragraph target)

1. Summary: what changed, when observed, customers impacted (count & priority).
2. Impact: short list of user-facing symptoms and metric deltas.
3. Immediate containment actions taken (if any).
4. Next steps & owners (72-hour action plan).

Stakehol
…[truncated]
```

#### #5 `dsid_eea56bf657db4ee59d2f2e7f234ae077`

```
Swift Response Taskforce Playbook and CSR Briefing Protocol

Summary:\nThis playbook describes the activation, composition, and operating procedures for Redwood’s Swift Response Taskforce (SRT). It standardizes rapid stabilization steps, evidence collection, CSR (customer success representative) brief scripts, and post-incident handoffs for incidents that risk violating customer-facing SLOs or require immediate customer outreach. Use this document when an incident meets Severity 1 or a high-severity multi-tenant degradation (see \"Severity and Activation Matrix\").\n\nPurpose and scope:\n- Provide a lightweight, reproducible pattern for assembling a cross-functional rapid-response team within the first 15 minutes of detection.\n- Ensure consistent, brand-safe customer messaging from first detection through postmortem.\n- Define measurable stabilization objectives, evidence artifacts, and closure criteria.\n\nWhen to use this playbook (activation criteria):\n1) Any alert that indicates SLO breach for 1+ customer(s) for more than 5 minutes.\n2) Multi-region outage, e.g. >30% increased p99 latency across regions A/B/C.\n3) Persistent KV cache thrash or sustained GPU OOMs affecting ded
…[truncated]
```

#### #6 `dsid_b720475c75e34ca88f256003e5258d63`

```
Fast-Path Escalation and Restoration Index

Overview:\n\nThis page defines the \"Fast-Path\" incident lanes, escalation rules, runbook index, and pre-baked communication templates used by Redwood Inference responders to shorten time-to-containment and accelerate restoration for high-impact customer-facing degradations. It is intended for first responders, on-call SREs, and incident commanders.\n\nScope:\n- Applies to service-impacting incidents that cause user-visible errors or major latency regressions for the Redwood API, Dedicated ingestion, or Console.\n- Not intended for scheduled maintenance, developer-only defects, or low-priority internal alerts.\n\nGoals:\n- Contain customer impact within the first 15 minutes for Fast-Path incidents.\n- Stable mitigation within 60 minutes.\n- Complete restoration or defined workaround within the agreed SLA window.\n\nKey concepts and lanes:\n1) Fast-Path lane (high priority)\n   - Trigger: page is fired for SEV-1 or aggregated SEV-2 (see severity table).\n   - Objective: immediate triage, short-lived mitigation (eg. circuit-break, scale-up), notify customers within 20 minutes.\n\n2) Stabilize-Path lane (medium priority)\n   - Trigger: serv
…[truncated]
```

#### #7 `dsid_b360d00be3f84b08b1a879d102835d2f`

```
Post-incident summary template (publishable)

## Purpose
This template is used to produce **customer-publishable** post-incident summaries for Redwood’s public status page and linked surfaces (e.g., Console). The goal is to provide a timely, accurate account of:
- **Customer impact** (what customers experienced)
- **Timeline** (when it started, when it was mitigated, when it was fully resolved)
- **Root cause class** (what kind of failure occurred, without leaking sensitive details)
- **Mitigations and prevention** (what we did immediately and what we are changing)

This template is designed to be:
- Clear to a non-Redwood audience
- Consistent across Hosted, Dedicated, and Private messaging
- Safe to publish (see confidentiality rules below)

---

## When to publish
Use this summary when an incident is customer-visible and any of the following are true:
- Severity is **Sev0–Sev2** (or equivalent) OR
- The incident resulted in a public status page incident OR
- Support/CS requests a publishable follow-up due to customer escalation

### Timing targets (guidance, not a commitment)
- **Sev0/Sev1:** publish within **2 business days** of resolution
- **Sev2:** publish within **5 busines
…[truncated]
```

#### #8 `dsid_3b7139962b28486aaa3a498cb375b2a9`

```
Incident Orchestration Decision Canvas and Runbook

Overview\n\nThis page documents a combined decision canvas and runnable playbook for on-call responders at Redwood Inference. The intent is to give a clear, SLO-driven decision process that: 1) shortens time-to-containment, 2) reduces noisy escalations, and 3) improves evidence collection for post-incident analysis. Use this page as the primary guide when an active incident affects customer-facing inference services (hosted API, Dedicated, or Private control plane).\n\nScope\n\n- Applies to incidents that impact latency, availability, correctness (quality regressions), or billing/quotas for inference endpoints.\n- Does NOT replace service-specific runbooks for deployment, onboarding, or infra reconfiguration; it is the orchestration layer to choose which runbook and communications path to use.\n\nQuick facts and SLO thresholds (production)\n\n- Availability SLO: 99.95% (per-region, 30d rolling).\n- Latency SLO: p99 < 350ms for short-form generate endpoints; p99 < 700ms for long-sequence pipelines.\n- Error budget alert: Trigger when 7-day rolling availability drops below 99.9% or error-rate increase > 2x baseline for 30 minutes.\n
…[truncated]
```

#### #9 `dsid_82c0781b50cb47668b5d37a67a9a157d`

```
Containment and Recovery Runbook — Customer Impact Incidents

Overview

This runbook describes a focused containment-and-recovery workflow for incidents that have measurable customer impact (errors, high latency, failed inference, or data loss risk). It is intentionally concise to support fast decision-making during the first 60–180 minutes of an incident. Use this document for: production API degradations, multi-customer failures, and partial platform outages that require immediate customer communication.

Scope
- Services in scope: Redwood API (hosted inference), Inference Router, Serving Runtime, KV Cache, Auth/Gatekeeper, Billing/Quotas.
- Out of scope: isolated developer environment failures, feature request regressions, or non-production test clusters.

When to invoke this runbook
- Customer reports or monitoring alerts indicate user-visible errors >= 1% of requests or sustained latency increases beyond SLO by 2x for > 5 minutes.
- Multiple customers report similar failures across regions.
- Automated canary checks fail for >= 2 consecutive runs.

Severity classification (quick reference)
| Severity | Customer impact example | Immediate actions |
|---|---|---|
| Sev-1 (Critic
…[truncated]
```

#### #10 `dsid_51877a563b0d4f42a63e33d7735913ff`

```
Responder Guidance and Simulation Labs with Templates

Summary:\nThis document is a compact, operational reference for responders, rotation leads, and incident controllers. It combines: severity definitions and triage ladders, a quick-run containment checklist, standardized status page and customer communication templates, a blameless postmortem timeline, and a small library of hands-on simulation (game-day) scenarios and lab steps. Designed to be printed on a single page for pager responders and expanded in linked runbooks for each service.\n\nGoals and intended audience:\n- Goals: reduce time-to-stable, standardize communications, ensure actionable post-incident follow-up, and improve responder readiness through repeatable simulations.\n- Audience: primary on-call responders (SRE/Platform, Serving Runtime, Infra), incident commanders, product-support liaisons, and on-call rotation managers.\n\nDefinitions and severity matrix (quick reference):\n| Severity | Impact description | Target initial response | Example triggers |\n|---|---|---:|---|\n| Sev0 | System-wide outage affecting >95% of traffic / external customer blocking | 5 minutes | API unavailable, entire region down |\n| S
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 52: `qst_0265::semantic` · N=5000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to analytics and dashboard issues but do not directly address the specific problem of transient zero or outdated values in long-range analytics charts. The gold chunk is highly relevant and non-empty, while the retrieved chunks are on-topic but not directly relevant, indicating an embedding near miss.

### Question

Why do some long range analytics charts in the US East production console briefly show zero or outdated values and the drill through to traces disappears, then fixes itself after about 10 to 30 minutes?

### Gold document(s)

#### GOLD `dsid_876b1a31bcc7409ab560b9ccbe5a0d41`

```
Historical dashboard panels show stale counts and lose trace links after retention compaction warmup

Issue summary: Several customers (notably LumenHealth) report that historical dashboard panels (time ranges > 30 days) intermittently show zeroed or stale metric counts and their trace links are missing. The problem is transient: panels become correct again after ~10-30 minutes without user action. Impact: dashboards with SLA and usage rollups show incorrect historical values; alerting based on those rollups can under- or over-fire. This affects customer trust in console analytics and can mask billing/usage anomalies. Environment: production us-east region. Affected customers reported on enterprise tier; observed across multiple orgs.
1) Open Console -> Dashboards -> choose a dashboard with weekly/monthly rollups (time range > 30 days). 2) Observe counts for a low-cardinality metric (e.g., route_success_rate, total_tokens) and trace-link anchors. 3) Rapidly change time window back and forth (e.g., 90d -> 30d -> 90d) and refresh. 4) Some panels will render with zeroed or very old counts and trace-link buttons show 'No traces' instead of opening the trace view. 5) Wait 10-30 minutes; panels recover without manual cache clear. Repro is intermittent (~1 in 10 attempts during retention compaction windows).
console-frontend: panel-render: query=rollup_v2 start=2025-12-01 end=2026-03-01 shard=warm-compact read_mode=primary; retention-indexer: compaction job id=cmp-2026-03-12-08 warmup=true; indexer-lag: lag=18m; kv-cache: miss-rate spike to 78%. Trace-hook service logs show O(200) missing anchors during query window. No 5xx in api-gateway. No token auth errors. Relevant links: https://grafana.redwood.internal/d/retention/indexer-run-03-12, https://kibana.redwood.internal/app/discover#/logs?q=cmp-2026-03-12-08
Initial hypothesis: retention compaction warmup job is causing a temporary partition state where rollup queries hit compacted partitions that are in 'read-repair' mode; dashboard renderer treats empty result as zero and trace-hook anchor resolution returns empty. Confirmed with SRE that a compaction job ran with warmup=true and indexer lag spiked ~18 minutes. Quer
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_2e39cd2d813b4399b28a20543130d48e`

```
Live trace stream produces duplicate session metrics when Live Trace toggle is enabled in Console

Issue summary: When a customer enables the 'Live Trace' toggle in Console (Tracing view) and starts a live session, the Console usage analytics shows duplicated session-start metrics (session_count and live_sessions). Impact: LexiconAI reports inflated usage numbers and unexpected cost projections for the dedicated pool. This appears to affect streaming traces only and does not always correlate with duplicate websocket connections in the app. Environment: Prod (us-east-1) on Dedicated cluster for LexiconAI. Observed behavior: Every time a trace event is emitted from the SDK during an active live session, Console increments session_count twice or more, creating bursts of duplicate sessions in the usage histogram. Expected behavior: Enabling Live Trace should increment a single session event per user session and update streaming metrics once per session initiation.
1) Customer (LexiconAI) enables Live Trace from Console > Tracing > toggle 'Live Trace' ON. 2) Start a live tracing session from their application using SDK v1.8.3. 3) Emit 3-5 trace events over the websocket in the same sess
…[truncated]
```

#### #2 `dsid_096e4752a7ed47e680ddc1fe7d3488dc`

```
Intermittent egress routing loop during failover causing p99 latency spikes for enterprise customer

Issue summary: Customer reports repeated p99 latency spikes (up to 2.6s) for requests pinned to us-east. Spikes correlate with automatic region failovers observed during a capacity shuffle.

Impact: BrightHealth Analytics (enterprise) observed degraded request-level latency for production models (~5% of traffic) for ~3 hours during a maintenance window; business-critical pipelines delayed.

Environment: prod-us-east, Redwood hosted API, dedicated routing policy with regional affinity enabled.

Steps to reproduce (customer-reported):
1) Send steady request stream to pinned endpoint (customer uses region pin TTL=30m).
2) Trigger a capacity rebalancing event (internal or simulated by failover stub).
3) Observe intermittent responses routed to eu-west and returned via a different egress path.
4) p99 latency increases and some streaming connections reset.

Observed logs / traces:
- Gateway logs show repeated 307-level route handoffs between us-east edge and eu-west serving nodes.
- Tracing spans show multiple DNS lookups for serving pool during a single request lifecycle.
- No applicatio
…[truncated]
```

#### #3 `dsid_4a74904e96de469eb6959ac78443f035`

```
Dashboard time-series shows transient spikes when tracing hook updates trace tags

Issue summary: BrightCart reports recurring, short-lived spikes on several dashboard time-series immediately after their application emits a tracing-hook that updates custom trace tags. Impact: Reports are noisy and alert thresholds (P99 latency and request counts) are tripping; affects three business dashboards used for capacity decisions. Environment: prod (us-east), dedicated org org-874. Observed behavior: When a tracing-hook updates tag "experiment_group" on an active trace, the dashboard line charts show a 5–15 second high-amplitude spike in request counts and client-side latency metrics that is not reflected in raw API logs. The anomaly correlates with the timestamp of the tag-write; spikes are visible in the console UI and in cached hourly rollups but do not appear in the ingestion pipeline raw event stream.
1) Customer reproducer: Attach tracing hook that patches trace.tags.experiment_group after trace is created
2) Generate sustained traffic (~80 RPS) with the tag update happening for ~10% of requests
3) Open customer dashboard (last 30 minutes) and observe sudden short spikes aligned to ta
…[truncated]
```

#### #4 `dsid_bad6bd97d4db46a59cb15721b6537cd8`

```
Console route experiment results appear stale / not updating for active experiment (aggregation + propagation lag suspected)

Customer reports that the new Console "Route Experiments" results dashboard is not updating (appears stuck on the same deltas/graphs) even though traffic is flowing to both variants.

Issue summary:
- Console results view for an active route experiment shows stale charts/metrics (latency/cost/error deltas unchanged for ~45–90 minutes).
- Customer validated traffic is being split (they see variant headers in responses).

Impact:
- Customer cannot make ramp/stop decisions from Console due to stale guardrail readouts.
- Increased risk of running an experiment longer than intended / missing regression.

Customer context:
- Account: Acme AI (beta design partner)
- Experiment: route-level A/B test (A=baseline, B=model swap) on production route.
- Customer expectations: near-real-time results (they assumed <5–10 min lag).

Environment:
- Prod
- Regions observed: us-east and eu-west

What we think is happening (initial hypotheses):
1) Config propagation lag: experiment config updates (start/ramp) not consistently visible to results attribution pipeline, causing mism
…[truncated]
```

#### #5 `dsid_a0f25cffcb264f0ea6eba5e501de0e08`

```
Unexpected egress flip from EU to APAC during high-rate embedding batch causing P99 latency burst

Issue summary: Customer observed a sudden P99 latency spike for small-batch embedding requests. During the window (~2026-03-12 09:15-09:35 UTC) requests that should have egressed in eu-west were routed to ap-southeast, adding ~220ms network RTT and causing downstream timeouts in their ingestion pipeline.

Impact: Production ingestion pipelines for Streamline Analytics degraded (10% request failures, 25% higher token latency). Affects users pinned to eu-west and using batch-embeds endpoint.

Environment: prod | eu-west (tenant: streamline-prod, customer-tier: enterprise)

Steps to reproduce: 
1) Send concurrent small-batch embedding calls (batch size 8, concurrency 40) to /v1/embeddings with tenant API key from EU.
2) Observe egress path in edge logs and p99 latency in Grafana.
3) Repeat during off-peak — issue appears correlated with higher control-plane heartbeat jitter.

Observed behavior: During burst, control-plane reports for tenant showed delayed residency stamp refresh; edge selected nearest healthy edge (ap-southeast) as fallback for some connections. TLS handshakes and auth t
…[truncated]
```

#### #6 `dsid_5b0ffeac1ea64dbda6a6e9db4e98afec`

```
GPU demand bucketed weekly rollup (cluster & pool)

Purpose:\nThis sheet is a weekly exported rollup that buckets incoming GPU demand signals by latency class and maps them to clusters/pools to estimate short-term headroom and recommended burst actions. Intended for on-call infra, capacity planning sync, and the Dedicated sales POV for burst guarantees.\n\nSummary (high level):\n- Week window: 2026-04-20 -> 2026-04-26\n- Primary signal sources: realtime API queue depth, scheduled batch jobs, Dedicated pool prewarm traces\n- New approach: bucket requests into three demand types (latency-critical, interactive, batch) and estimate peak GPU-hours per bucket per cluster to prioritize allocation and preemption policies.\n\nHow this was generated:\n- Dashboard scrape of per-cluster 1h and 5m percentiles (P50, P95) for GPU utilization and active containers.\n- Demand inferred from request arrival *estimated tokens-per-request* for transform workloads; batch jobs counted by job runtime * GPU count.\n- We then map inferred demand onto current pool placement rules and quantize into 1-GPU headroom units for actionable decisions.\n- Export columns below are the minimal set needed for weekly cap
…[truncated]
```

#### #7 `dsid_124b2cc184714cbbbfe3bffb46c1eaf0`

```
Route-level token/cost breakdown omits prefix/KV cache token contributions causing underreported usage

Issue summary: Customer reports that the per-route token and cost breakdown in the Console Usage view is consistently lower than the raw token counts returned by the Usage Export.

Impact: BrightFolio's finance and engineering teams are seeing underreported token usage on route-level dashboards compared to raw exports and the Dedicated billing meter. This is causing inaccurate cost attribution per route and missed alerting thresholds for high-cost routes.

Initial hypothesis: The route-level aggregation is excluding tokens attributed to prefix/KV cache lookups and cached continuation tokens that are consumed by the serving runtime. The raw export (which shows total tokens) includes these cached token events; the Console breakdown appears to sum only direct generation tokens.

Environment: Production, Dedicated pool in us-east-1. Customer uses pinned model redwood-4x-ensemble with KV prefix caching enabled at the route level.

1) Customer runs a steady workload against route /api/v1/summarize with prefix caching enabled and sampling that triggers cache hit patterns.
2) Export raw 
…[truncated]
```

#### #8 `dsid_2cd6d5100fbe4334bd47b237f3f30678`

```
Trace Orchestra Conductor Profiling

Objective:\nQuick, reproducible exploration of the long-tail E2E latency behavior observed on the v2 serving runtime (public fleet). We want: 1) a compact per-stage decomposition for p50/p95/p99, 2) a small set of high-confidence hypotheses for root causes, and 3) actionable experiments to run in the next sprint.\n\nContext / why now:\nOver the last two weeks we've seen intermittent p99 spikes (clients reported 10x slower responses on small chat completions). Dashboard snapshots: overall generation p50=14ms, p95=64ms, p99=320ms. Spike pattern looks correlated with bursty multi-route traffic and a handful of long-seqlen traces. This doc gathers trace excerpts and preliminary attributions.\n\nMethodology (how traces were selected):\n- Sampled traces via the SLO-driven sampler (slo-sample window 100s, weight p99-biased).\n- Focus set: 200 traces in the 250–600ms wall-clock bucket from the last 48h on region-us-west1, model-family: rw-base-13b (quantized).\n- For each trace we stitch stage spans: (http-ingest -> tokenization -> request-queue -> batcher-wait -> kernel-exec(s) -> kv-lookup -> emit -> egress).\n- Derived per-stage percentiles using per
…[truncated]
```

#### #9 `dsid_343773ee53ee474bbf3743a366c113dc`

```
Console quota readout shows refreshed tokens but requests continue 429ing during geo failover

Issue summary:

Customer reports seeing Console quota counter jump back to non-zero (token refill) after a regional failover, but API requests continue to receive 429s for several minutes. This looks like a mismatch between what the Console reports and what edge enforcement is doing.

Impact:
- Large customer ingestion pipelines (TraceScale) experiencing sustained 429s during a geo failover window, causing worker retries to back off and backlog to grow.
- Estimated 30-40% of ingestion workers unable to push data for ~8 minutes during event.

Environment:
- Dedicated pool for TraceScale (customer-dedicated-42)
- Primary region: us-east; failover region: eu-west
- Model in use: redwood/llama2-70b text-generation
- Traffic pattern: mixed short streaming sessions + periodic bulk embedding jobs from 200 parallel workers

Steps to reproduce (as reported by customer):
1) Begin bulk ingest from 200 workers aimed at the dedicated endpoint in us-east (sustained throughput).
2) Trigger simulated regional maintenance/failover (istio NLB drain in test) causing traffic to route to eu-west.
3) Watch Con
…[truncated]
```

#### #10 `dsid_f9292a8538ea407e969b854176e438b7`

```
Drilldown latency percentiles on dashboard show stale per-route values after prefix-cache TTL rollover in eu-west

Issue summary:
When a large prefix-cache TTL rollover completed in eu-west this morning, several LuminaHealth dashboard drilldowns that show per-route latency percentiles (p50/p95/p99) continued to display the pre-rollover (stale) values for up to ~45 minutes. The aggregated dashboard tiles updated but drilldown queries remained anchored to the old prefix-cache shard until a manual cache invalidation.

Impact:
- Customer-visible: LuminaHealth reported alert noise and missed escalation because the drilldown didn't reflect the post-rollover latency regression for a small set of routes.
- Scope: Affects console drilldowns that rely on route-scoped percentile rollups where prefix-cache keys were rotated during TTL rollover. Observed in prod:eu-west only.

Environment:
- Prod (eu-west)
- Customer: LuminaHealth (enterprise) using pinned routes and per-route alerting
- Console version: 2026.02.8
- Ingest pipeline: kafka->ingest-service v3.4.1

Steps to reproduce (observed):
1) Triggered scheduled prefix-cache TTL rollover (automated job) at ~2026-03-10T05:00:00Z.
2) Dashboard
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 53: `qst_0265::semantic` · N=20000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to the question but do not match the specific issue described in the gold chunk. This suggests an embedding near miss, where semantically similar but not identical issues were retrieved. Both gold and retrieved chunks are non-empty and on-topic.

### Question

Why do some long range analytics charts in the US East production console briefly show zero or outdated values and the drill through to traces disappears, then fixes itself after about 10 to 30 minutes?

### Gold document(s)

#### GOLD `dsid_876b1a31bcc7409ab560b9ccbe5a0d41`

```
Historical dashboard panels show stale counts and lose trace links after retention compaction warmup

Issue summary: Several customers (notably LumenHealth) report that historical dashboard panels (time ranges > 30 days) intermittently show zeroed or stale metric counts and their trace links are missing. The problem is transient: panels become correct again after ~10-30 minutes without user action. Impact: dashboards with SLA and usage rollups show incorrect historical values; alerting based on those rollups can under- or over-fire. This affects customer trust in console analytics and can mask billing/usage anomalies. Environment: production us-east region. Affected customers reported on enterprise tier; observed across multiple orgs.
1) Open Console -> Dashboards -> choose a dashboard with weekly/monthly rollups (time range > 30 days). 2) Observe counts for a low-cardinality metric (e.g., route_success_rate, total_tokens) and trace-link anchors. 3) Rapidly change time window back and forth (e.g., 90d -> 30d -> 90d) and refresh. 4) Some panels will render with zeroed or very old counts and trace-link buttons show 'No traces' instead of opening the trace view. 5) Wait 10-30 minutes; panels recover without manual cache clear. Repro is intermittent (~1 in 10 attempts during retention compaction windows).
console-frontend: panel-render: query=rollup_v2 start=2025-12-01 end=2026-03-01 shard=warm-compact read_mode=primary; retention-indexer: compaction job id=cmp-2026-03-12-08 warmup=true; indexer-lag: lag=18m; kv-cache: miss-rate spike to 78%. Trace-hook service logs show O(200) missing anchors during query window. No 5xx in api-gateway. No token auth errors. Relevant links: https://grafana.redwood.internal/d/retention/indexer-run-03-12, https://kibana.redwood.internal/app/discover#/logs?q=cmp-2026-03-12-08
Initial hypothesis: retention compaction warmup job is causing a temporary partition state where rollup queries hit compacted partitions that are in 'read-repair' mode; dashboard renderer treats empty result as zero and trace-hook anchor resolution returns empty. Confirmed with SRE that a compaction job ran with warmup=true and indexer lag spiked ~18 minutes. Quer
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_b127efa7f884490fb4704c90cc8f0592`

```
Saved dashboard query times out for >24h ranges and associated tracing links return 404

Issue summary: Saved dashboard query for 'usage_per_model' consistently times out when run over windows larger than 24 hours. When the query is re-run, the console shows result rows but the 'view trace' links on individual rows return a 404. Impact: Customer cannot investigate usage spikes or link traces from console; blocking incident investigation and delaying billing reconciliations for their dedicated tenant. Environment: prod (us-west), dedicated tenant soma-prod-01, console v2.8.2.

Steps to reproduce:
1) Login as customer user on SomaHealth dedicated tenant.
2) Open Console -> Dashboards -> Saved Queries -> 'usage_per_model'.
3) Set time range to last 7 days and Run.
4) Observe spinner; query returns after ~60s with partial results.
5) Click 'View Trace' on any row -> 404 from tracing endpoint.

Expected behavior: Query completes within SLO (<30s) for 7d with aggregated rollups; 'View Trace' opens full trace in tracing UI. Actual behavior: Long-running query (~60-90s) or times out depending on occasional backend throttling; trace links point to tracing URL with missing trace id or return
…[truncated]
```

#### #2 `dsid_02ae04b078dd456e825c2d2d5a87175c`

```
Trace span anchor misalignment in console causing dashboard 'open logs' to jump to wrong time window

Issue summary: Customers using console trace links (Dashboard -> "open logs" / "view trace") are being taken to a time window that does not match the selected trace span. The link opens the logs 30–90 seconds earlier than the selected span, which breaks direct investigation workflows and correlating trace->log events.

Impact: Multiple enterprise customers (reported by NebulaPayments) are unable to correlate low-latency 5xx spikes with trace spans during cross-region fallbacks. This increases MTTI and requires manual time adjustments in Kibana. Not a full outage but blocks timely RCA for P1 incidents.

Environment: Production console, traces collected via obs-ingest and forwarded to the tracing indexer; customers on dedicated routing with cross-region fallback enabled. Problem reproducible most frequently when the original request is routed from eu-west to us-east and the console trace span includes multiple 'fallback' child spans.

Observed behavior: Clicking the dashboard trace tile opens the trace viewer and then the "Open Logs" link directs to the logging console with a start t
…[truncated]
```

#### #3 `dsid_c1f90c472e1946e88bda0de64a95ff70`

```
Console dashboard panel goes blank when timeframe crosses retention cutoff

Issue summary:
When a dashboard time range spans the ingestion retention boundary (e.g., 'now-90d to now'), large panels that fan out multiple series return a completely blank panel in the Console UI. Traces and raw events for the same timeframe are still queryable via the Trace view and raw exports. The blank panel occurs intermittently and appears correlated with panels that run queries hitting older hourly/rollup tables plus the recent hot partition.

Impact:
- Customer-facing dashboards appear empty for large time ranges crossing retention cutoffs.
- Users at Zypher Analytics (enterprise, heavy historical analytics) report inability to reconcile metrics with exported CSVs.
- Affects dashboards with >10 series across combined storage layers; can impact downstream alerts that depend on panel series.

Environment:
- prod | us-east (primary reports), also observed in eu-west during repro.
- Console version: web-2026.03.01
- Query-service: q-2.8.4, retention-worker: r-1.5.2

Steps to reproduce:
1) Login to Console as org admin for Zypher Analytics (org-id: zypher-001).
2) Open Dashboard 'Customer Latency — 9
…[truncated]
```

#### #4 `dsid_a8302bc5f129440a880dc1ddaced54e9`

```
Dashboard series facet ordering appears randomized after live refresh, breaking drilldowns

Issue summary:
When viewing a dashboard with a high-cardinality 'series' facet, users report that the ordering of the series list becomes effectively randomized each time the live panel refreshes. This causes the drilldown links for popular series to change position and, in some cases, the exported drilldown link points to the wrong series.

Impact:
- OrbitAnalytics (dedicated customer) reports recurring user-facing confusion and incorrect drilldowns on three production dashboards used by their analysts.
- Analysts rely on stable facet ordering to validate alerts and run ad-hoc investigations; incorrect drilldowns lead to wasted time and occasional incorrect conclusions.
- Reproducible for the customer on multiple browsers and appears to affect dashboards with >500 unique series in the time window.

Environment:
- Redwood Console (hosted) serving OrbitAnalytics dedicated org
- Region: us-east
- Dashboards: traffic-anomalies-weekly, model-inference-attribution
- Time window: last 7 days, auto-refresh enabled (30s)

Steps to reproduce:
1) Login as OrbitAnalytics user and open 'traffic-anomalie
…[truncated]
```

#### #5 `dsid_4866ef84859a43b89d77178c28d9513c`

```
Console dynamic filter debounce causes trace-link disappearance on dashboard update

Issue summary: When a user applies or edits dashboard filters with quick successive changes (typing + selecting time ranges), the console's client-side debounce and query cancellation logic sometimes removes the "Open trace" links on several heatmap and trace-linked widgets. Impact: Customers lose the ability to jump from a dashboard series to the full trace; some users report missing links on >30% of affected rows for a 90-minute window. Environment: prod, us-east region, console v2.10.3, dashboard-renderer service behind api-gateway. Steps to reproduce:
1) Open Performance dashboard for org/org-122 (NovaAnalytics)
2) Apply global filter: trace.duration > 50ms and start typing a new "service" filter rapidly (type >3 characters, then immediately pick a value)
3) Change time range from Last 1h to Last 6h within 2s of applying the filter
4) Observe heatmap rows and series; hover and open the trace detail.
Observed behavior: Several series display the trace id but the "Open trace" link is missing or the link's href is blank. Clicking sometimes triggers a client console error (see logs). Expected behav
…[truncated]
```

#### #6 `dsid_5f4aa0a4548647ae8553a0929723e4cd`

```
Console usage heatmap bucketization produces missing hourly spikes when zooming/adjusting timescale

Issue summary: Customers (BetaForms) report that the Console usage heatmap shows clear hourly spikes in a broad 7-day view, but when zooming into the hourly range the spikes disappear or are redistributed across non-intuitive buckets. Impact: Customers cannot reconcile observed token usage against billing exports for specific hours. This causes billing confusion for enterprise customers and blocks audits. Environment: Production console, us-east region. Observed since ~2026-03-09 22:00 UTC after a console release. Frequency: Intermittent on some orgs; reproducible for BetaForms datasets. Observed vs Expected: Observed: spikes visible at 1d aggregation but vanish when switching to 1h-aggregations. Expected: spike amplitude should be preserved across aggregation scales (just redistributed to smaller buckets).
1) Login to Console as an org admin (BetaForms-like dataset). 2) Open Usage -> Heatmap -> select last 7 days (bucket size auto). 3) Note a pronounced spike on Day 3 around 14:00 UTC. 4) Zoom to Day 3 and change timescale to hourly or click into the heatmap to view that day. 5) Ob
…[truncated]
```

#### #7 `dsid_5ef9f435fc9d40be94e4d8ba2ab7c34c`

```
Realtime Console 'Usage Snapshot' shows inflated tokens after editing query filters

Issue summary:
Customer reports that the Console "Usage Snapshot" card for a workspace displays a token count that is consistently ~2x the token count shown by the raw usage export after they edit a saved query's filters (timespan and org filter).

Impact:
- Customer cannot reconcile near-real-time usage with raw exports — blocks weekly reconciliation and alerts.
- Affects billing visibility and trust for dedicated customers using committed capacity.
- Reported by ScaleWave (dedicated) for us-east-1 workspace; they see the discrepancy within 1–3 minutes after editing queries.

Environment:
- Console (web) in prod: us-east-1
- Workspace: scalewave-prod (dedicated cluster)
1) Login to Console as an owner of a dedicated workspace (ScaleWave account).
2) Open Usage -> Realtime -> Usage Snapshot (top-right card).
3) Click 'Edit query' and change timespan from '1h' to '24h' and toggle Organization filter (e.g., include/exclude a sub-org).
4) Save query. Observe Usage Snapshot token value (updates within 1–3 minutes).
5) Export raw usage CSV for the same timespan and filters. Compare token totals — snapsh
…[truncated]
```

#### #8 `dsid_2e39cd2d813b4399b28a20543130d48e`

```
Live trace stream produces duplicate session metrics when Live Trace toggle is enabled in Console

Issue summary: When a customer enables the 'Live Trace' toggle in Console (Tracing view) and starts a live session, the Console usage analytics shows duplicated session-start metrics (session_count and live_sessions). Impact: LexiconAI reports inflated usage numbers and unexpected cost projections for the dedicated pool. This appears to affect streaming traces only and does not always correlate with duplicate websocket connections in the app. Environment: Prod (us-east-1) on Dedicated cluster for LexiconAI. Observed behavior: Every time a trace event is emitted from the SDK during an active live session, Console increments session_count twice or more, creating bursts of duplicate sessions in the usage histogram. Expected behavior: Enabling Live Trace should increment a single session event per user session and update streaming metrics once per session initiation.
1) Customer (LexiconAI) enables Live Trace from Console > Tracing > toggle 'Live Trace' ON. 2) Start a live tracing session from their application using SDK v1.8.3. 3) Emit 3-5 trace events over the websocket in the same sess
…[truncated]
```

#### #9 `dsid_0eba0717ee044630af6afd0d633a8261`

```
Anomaly detection alerts link to stale model-version traces after nightly compaction

Issue summary:\nAnomaly-detection alerts for Glyph Health’s production routes fired between 2026-03-10T02:00Z and 2026-03-10T03:15Z. When support engineers or customers click the 'View root cause traces' link in the Console alert card, the trace list contains spans referencing a stale model version tag (model_version: v2025-11-02) instead of the expected v2026-02-28. This made it appear that the anomaly was caused by an older model, delaying triage.\n\nImpact:\n- Glyph Health saw 12 anomaly alerts for sudden latency/embedding drift on several production routes.\n- Console root-cause links pointed to traces whose metadata indicated older model versions and older client ids, hindering investigation.\n- No inference correctness/regression at model serving layer was identified; this is an observability/indexing mismatch causing confusion and wasted triage time.\n\nEnvironment:\nprod / us-east (Glyph Health dedicated pool). Tracing and alerting pipelines: trace-indexer v2.4.1, metadata-enricher v1.7. Nightly compaction: events-compact-v2 job.\n\nSteps to reproduce (customer-provided + reproduced by Sup
…[truncated]
```

#### #10 `dsid_096e4752a7ed47e680ddc1fe7d3488dc`

```
Intermittent egress routing loop during failover causing p99 latency spikes for enterprise customer

Issue summary: Customer reports repeated p99 latency spikes (up to 2.6s) for requests pinned to us-east. Spikes correlate with automatic region failovers observed during a capacity shuffle.

Impact: BrightHealth Analytics (enterprise) observed degraded request-level latency for production models (~5% of traffic) for ~3 hours during a maintenance window; business-critical pipelines delayed.

Environment: prod-us-east, Redwood hosted API, dedicated routing policy with regional affinity enabled.

Steps to reproduce (customer-reported):
1) Send steady request stream to pinned endpoint (customer uses region pin TTL=30m).
2) Trigger a capacity rebalancing event (internal or simulated by failover stub).
3) Observe intermittent responses routed to eu-west and returned via a different egress path.
4) p99 latency increases and some streaming connections reset.

Observed logs / traces:
- Gateway logs show repeated 307-level route handoffs between us-east edge and eu-west serving nodes.
- Tracing spans show multiple DNS lookups for serving pool during a single request lifecycle.
- No applicatio
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 54: `qst_0268::semantic` · N=10000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are non-empty and generally on-topic, discussing issues related to streaming and API errors, but they do not specifically address the March 2026 incident described in the question. This suggests a lexical mismatch where the retrieval system failed to capture the specific context or keywords needed to find the correct document.

### Question

In the March 2026 production incident where long streamed chat replies started arriving chopped up and in the wrong order and the customers usage charges jumped because their client kept reissuing the same request, what was identified as the underlying platform cause?

### Gold document(s)

#### GOLD `dsid_a990e708840f481795741cfd3fb55691`

```
Cinder Labs — session tear causing token reordering, retry amplification, streaming truncations and billing spike

Issue summary:

During a peak traffic window on 2026-03-09 17:22 UTC, Cinder Labs began seeing partial/stale streaming responses, token reordering for long chat sessions (>4096 tokens), and a surge in client retries that amplified upstream throughput. This led to increased 5xx rates from serving nodes, transient throttles from the API gateway, and an unexpected billing delta for the customer.

Impact:
- Multiple customer endpoints experienced truncated streams and out-of-order token sequences (~1200 user sessions affected).
- Observed 5xx rate peaked at 6.3% for the customer’s traffic window.
- Billing spike estimated at +42% for the affected 2-hour window due to retry amplification.
- Customer escalated to enterprise support and requested immediate mitigation, crediting and a post-incident review.

Environment:
- Production (us-east-1) serving cl-13b-v1-quant behind api-gateway v2.13.
- Dedicated routing policy: enterprise-reserved-us-east.

Steps to reproduce (internal):
1. Create a multi-turn chat session pinned to cl-13b-v1-quant with >4096 token context and stream responses.
2. Induce a partial runtime eviction (simulate KV cache evictions / kernel reselect) while continuing to stream.
3. Observe token gaps and client-side automatic retries causing multiple inflight requests for the same session.

Observed behavior:
- When a serving shard dropped the KV prefix during a background compaction, subsequent token continuation resumed from an earlier cache state and produced overlapping token sequences.
- Client SDKs retried idempotently but without session-affinity checks, creating duplicate in-flight completions.
- API gateway detected elevated error rates and began conservative throttling; some requests received 429s while others returned 5xx from the runtime.

Initial mitigation and timeline:
- 17:28 UTC: Support opened escalation and notified SRE and Serving Runtime teams.
- 17:35 UTC: Temporary routing policy change to route Cinder Labs traffic to a healthy pre-warmed pool (bypassed recently-updated autoscaler rules).
- 17:42 UTC: Disabled aggr
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_576496e2926e4747980636f3ee519243`

```
Axiom Payments - duplicate streaming replies and sudden throttling causing transaction failures

Issue summary: Between 2026-03-10T02:05 and 2026-03-10T03:30 UTC Axiom Payments reported duplicated streaming responses and a surge of 5xx errors plus client-observed throttling that caused ~18% of payment API calls to fail or be delayed beyond customer SLOs.
Impact: Transaction creation requests experienced duplicate model outputs (duplicate intents leading to double-charges in downstream processing) and elevated latency/timeouts across the us-east region. Customer reported immediate business impact (failed settlements).
Environment: Production (us-east) serving via Hosted API for enterprise tenant using model redwood-ggml-13B pinned version v2026-02-25. Customer on enterprise plan with dedicated routing policy.
Steps to reproduce: 1) Send a stream-based chat request with small initial prompt and repeated 'confirm' function call; 2) Observe two or more streamed final responses within 1s window for same request id; 3) Repeat under sustained concurrent load (~120 rps) and observe API gateway returning 429s or 502s.
Observed behavior: Streaming connection returned duplicate final chunks f
…[truncated]
```

#### #2 `dsid_5f884c5669194d698c0be56a1df92b33`

```
Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling

Issue summary: Starting ~2026-03-13 11:20 UTC, ChatMetrics reported a rising error floor of 5xx responses for streaming requests. The API Gateway returned 502/503 intermittently and a subset of streaming sessions observed immediate fallback to short-polling which then triggered additional gateway throttling and elevated error rates. Impact: Customer-facing degradation for ChatMetrics (dedicated tier) — streaming API errors for ~40% of active sessions, visible increase in token cost due to retries. Environment: prod-us-east, dedicated tenant cluster. Observed with model redwood/text-xt-3b. Steps to reproduce: 1) Initiate ~600 concurrent streaming sessions from a single ChatMetrics vCPU-based client to the /v1/streams endpoint; 2) Hold long-lived streams with occasional small writes (~1-2 tokens every 2s); 3) Observe on the client: intermittent 502/503 during handshake period followed by server-initiated fallback and then 429s after gateway backoff. Recent changes: nightly keystore rotation completed at 11:05 UTC and an autoscaler policy sweep was applied at 11:10 UTC. Logs/metr
…[truncated]
```

#### #3 `dsid_97992c0043184c7b9c10ed2106482ae1`

```
Hosted API: client-side context deadline exceeded on streaming chat (us-west)

Issue summary:
- Customer reports frequent failures in their Go client: `context deadline exceeded` while using streaming chat.

Impact:
- 1-3% of requests fail; retried requests succeed.
- Most failures occur after ~45-55s of streaming.

Primary symptom: Request timeouts
Deployment offering: Hosted API

Notes:
- Customer is behind a corporate proxy; may be closing idle connections.
- However, we also see periodic pauses in token emission on our side during the failures.

Requested:
- Confirm whether gateway idle-timeout or upstream flush buffering changed in recent deploy.
Aisha Rahman (2026-03-11): Escalating because this is impacting production rollout this week.
Dev Patel (2026-03-11): Found a gateway config change enabling response buffering for a subset of streaming routes in us-west.
Dev Patel (2026-03-11): Rolled back buffering config for chat streaming; timeout errors in logs dropped.
Aisha Rahman (2026-03-12): Customer confirms success rate back to normal.
```

#### #4 `dsid_04e4f59077354c05986cd31b1986c6ac`

```
Intermittent multiplexed SSE session stall when mobile app is backgrounded, partial final output on reconnect

Issue summary: Customer reports that when their iOS app (WKWebView-backed) is backgrounded and later resumed, SSE streams that were multiplexed over a single connection frequently stall and deliver only a partial final token/metadata bundle on reconnect. Impact: end users see truncated assistant replies or replies missing the final choice metadata (finish_reason, token_offsets). This affects conversational flows and causes retries in their client that double-bill tokens in some cases. Environment: prod us-east, multiplexed sessions enabled, client SDK v1.8.2.
Roughly 7-12% of streaming sessions from this customer across us-east show truncated final output after background/resume. Several paid users reported missing final paragraphs; affects live chat UX and billing correctness.
1) Start a streaming chat request using multiplexed SSE (client creates a single SSE connection with multiple client-id headers).
2) Allow the assistant to stream a multi-paragraph response (~350-800 tokens).
3) Background the iOS app (home button / swipe up) before the stream completes and leave fo
…[truncated]
```

#### #5 `dsid_c7bcf2745c8f44228768c7650ed1358f`

```
Streaming sometimes stops mid-generation (no final chunk) on Hosted API

Customer reports that streaming responses occasionally stop without sending a final chunk / [DONE]. They do not always see a network error, but their SDK callback stops firing and they end up with a truncated completion. Happens sporadically, more noticeable during peak hours.

Customer wording (from CSM): "stream just ends halfway through a sentence".

Initial hypothesis: client-side read timeout OR server-side stream closed due to upstream cancellation/backpressure.
Connor O'Brien (Support) 2026-03-14: Creating ticket after CS call. Fireflies transcript in CS workspace references this ("streaming is flaky"; see 2026-03-14).
Maya Srinivasan (Applied ML) 2026-03-15: Are they using OpenAI-compat endpoint or native? If OpenAI-compat, confirm they parse SSE correctly and handle reconnect.
Connor O'Brien 2026-03-16: They use OpenAI-compat + Node fetch streaming; confirmed they expect [DONE] but sometimes get socket hang up.
Aisha Rahman (SRE) 2026-03-18: Noted incident thread in #incidents about increased streaming disconnect ratio in eu-west earlier today. Might be same cluster event.
Maya Srinivasan 2026-03-19: 
…[truncated]
```

#### #6 `dsid_0eb30895fb1a4009bc8c443055718882`

```
SapphireLine multi-region routing race caused streaming truncation during end-of-day batches — customer escalation and action plan

Issue summary:
During SapphireLine's nightly end-of-day batch (scheduled 02:00-03:30 UTC), a subset of inference requests experienced streaming truncation and intermittent 5xx spikes across us-east and eu-west. Customers reported partial transcripts and missing trailing tokens for streaming completions, plus repeated client reconnects. Impact: multiple business-critical batch jobs failed to reconcile logs and generated duplicate downstream processing attempts.

Impact:
- Affected ~7% of batch traffic for SapphireLine between 2026-03-11 02:07 and 2026-03-11 02:41 UTC.
- Streaming responses truncated mid-completion; clients saw final chunk missing.
- Several retries caused billing/usage anomalies and duplicate downstream webhooks.

Environment:
- Hosted Redwood API (enterprise tenant), dedicated routing for SapphireLine in us-east and eu-west.
- Smart-router service v2.3.1 deployed across both regions.

Steps to reproduce (internal):
1) Run high-concurrency streaming job against redwood/gptx-13b-v2 with session affinity enabled and target traffic split a
…[truncated]
```

#### #7 `dsid_a7baddf163ef4946a97b4765bf1cf08b`

```
Invoice shows unexpected token usage and model charges

Issue summary: Customer reports that their March invoice contains an unexpectedly large charge attributed to text-generation tokens. They claim most of their workload is embeddings and a small streaming chat integration.

Impact: Potential billing dispute, customer is evaluating whether to pause Dedicated capacity. Financial impact reported ~$9k over expected month-to-date.

Environment: Dedicated tenant in us-east running pinned model gpt-4o-redwood-13b for chat routes; embeddings routed to embedding-ada-2 via a separate endpoint.

Steps to reproduce / observed behavior:
1) Customer runs batched embedding jobs (low token usage) and intermittent chat streams (small convo).
2) Billing report shows large generation token counts starting 2026-03-02.
3) Customer supplied request ids and sample request timestamps (included in comments).

Investigation notes / logs:
- Initial billing export attached by customer shows line-level usage matching request ids: request-20260302-7a2, request-20260305-1f9, request-20260312-cc3.
- Internal query of request logs shows multiple replayed requests from the routing proxy between 03-02 and 03-05 (
…[truncated]
```

#### #8 `dsid_3042eea9b36942ae8084eab2f28c3012`

```
Rate-shedding policy misfire during tenant surge leading to 5xx retry cascade

Issue summary: During an unanticipated tenant traffic surge for NovaChat, the API gateway applied an adaptive rate-shedding policy that mis-evaluated backend capacity, triggering widespread 5xx responses and a client-side retry cascade. Impact: multiple tenant requests returned 502/503 over a 22 minute window; customers reported stream disconnects and elevated latency. Environment: production us-east cluster serving Dedicated pools with mixed prefetch and streaming workloads.
1) Simulate sustained connection burst with many long-lived streaming sessions against tenant NovaChat on prod us-east
2) Force a mixed prompt workload where many requests trigger prefetch and cold KV cache misses
3) Observe API gateway rate-shedding decisions and how upstream runtimes are selected for fallback
4) Watch for client retry behavior and whether retries are amplified by gateway responses (502/503).
2026-03-13T12:07:12Z apigw[edge-12] WARN shed_decision=adaptive action=drop tenant=novachat sessions=842 backlog=3700
2026-03-13T12:07:13Z runtime[pool-7] ERROR upstream=worker-77 status=exit reason=oom_estimated kernel_swap=f
…[truncated]
```

#### #9 `dsid_fd4ca30984c8455a9e77b5a324cc1b80`

```
Intercontinental multipath crossover causing chunked response delays for streaming inference

Issue summary: Customer Lumenly reports elevated streaming latency and chunked responses when sending long-form chat prompts.
Impact: Multiple production customers using the dedicated pool (account LUM-42) see increased P50->P99 tail on streamed tokens; some sessions experience repeated TCP-level stalls and client perceived stalls for 2-10s.
Timeline: 2026-03-13 08:12 UTC - first alert from Lumenly (support chat); 2026-03-13 08:25 UTC - automated p99 latency alert for us-west serving group; 2026-03-13 08:40 UTC - support ticket created; 2026-03-13 09:10 UTC - SRE and Serving triaged.
Environment: Dedicated capacity (pool dcap-lum-01) in us-west-2 region that routes synthetic traffic to eu-west-1 compute for certain models.
Steps to reproduce: 1) Send a streaming chat request via API key for account LUM-42 with a 2k token prompt. 2) Observe initial tokens stream, then a 1-8s stall before the next chunk. 3) Repeated attempts sometimes succeed without stall (non-deterministic).
Observed behavior: Streaming connection remains open, but token emission is chunked with long inter-chunk gaps rathe
…[truncated]
```

#### #10 `dsid_891626ad3966452c8afa7297f4f27485`

```
Sustained TTFB drift on long-running HTTP/2 sessions caused by proxy flush delay and stream multiplexing

Issue summary: Customer reporting gradual increase in first-byte latency (TTFB) over the lifetime of long streaming sessions. Problem does not manifest as immediate 5xx, but responsiveness for subsequent tokens drifts from ~120ms to 1.2s after ~90s of continuous streaming.

Impact: Enterprise customer (NovaChat) reports degraded UX for multi-turn assistant sessions where responses slow down mid-completion. Affects production traffic in us-east region. Customer is on enterprise plan and has SLA expectations.

Environment: Production, us-east, traffic via HTTP/2 multiplexed connections through our API Gateway -> ALB -> serving runtime. Observed with both rwd-gpt-7b-v1 and open-gpt-3.5-like model endpoints.

Observed behavior: TTFB slowly increases during a single, long streaming request; streaming session remains open (no connection reset) but data arrives in sparser chunks. Not a hard timeout or 5xx, more of a degradation that correlates with header/meta growth and number of concurrent streams on the client connection.

Expected behavior: Stable TTFB across the duration of a str
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 55: `qst_0268::semantic` · N=75000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to streaming and API issues but do not specifically address the March 2026 incident described in the question. The failure mode is likely an embedding near miss, as the retrieved documents discuss similar technical issues but not the exact incident. Both gold and retrieved chunks are non-empty and on-topic, scoring high in chunk quality.

### Question

In the March 2026 production incident where long streamed chat replies started arriving chopped up and in the wrong order and the customers usage charges jumped because their client kept reissuing the same request, what was identified as the underlying platform cause?

### Gold document(s)

#### GOLD `dsid_a990e708840f481795741cfd3fb55691`

```
Cinder Labs — session tear causing token reordering, retry amplification, streaming truncations and billing spike

Issue summary:

During a peak traffic window on 2026-03-09 17:22 UTC, Cinder Labs began seeing partial/stale streaming responses, token reordering for long chat sessions (>4096 tokens), and a surge in client retries that amplified upstream throughput. This led to increased 5xx rates from serving nodes, transient throttles from the API gateway, and an unexpected billing delta for the customer.

Impact:
- Multiple customer endpoints experienced truncated streams and out-of-order token sequences (~1200 user sessions affected).
- Observed 5xx rate peaked at 6.3% for the customer’s traffic window.
- Billing spike estimated at +42% for the affected 2-hour window due to retry amplification.
- Customer escalated to enterprise support and requested immediate mitigation, crediting and a post-incident review.

Environment:
- Production (us-east-1) serving cl-13b-v1-quant behind api-gateway v2.13.
- Dedicated routing policy: enterprise-reserved-us-east.

Steps to reproduce (internal):
1. Create a multi-turn chat session pinned to cl-13b-v1-quant with >4096 token context and stream responses.
2. Induce a partial runtime eviction (simulate KV cache evictions / kernel reselect) while continuing to stream.
3. Observe token gaps and client-side automatic retries causing multiple inflight requests for the same session.

Observed behavior:
- When a serving shard dropped the KV prefix during a background compaction, subsequent token continuation resumed from an earlier cache state and produced overlapping token sequences.
- Client SDKs retried idempotently but without session-affinity checks, creating duplicate in-flight completions.
- API gateway detected elevated error rates and began conservative throttling; some requests received 429s while others returned 5xx from the runtime.

Initial mitigation and timeline:
- 17:28 UTC: Support opened escalation and notified SRE and Serving Runtime teams.
- 17:35 UTC: Temporary routing policy change to route Cinder Labs traffic to a healthy pre-warmed pool (bypassed recently-updated autoscaler rules).
- 17:42 UTC: Disabled aggr
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_576496e2926e4747980636f3ee519243`

```
Axiom Payments - duplicate streaming replies and sudden throttling causing transaction failures

Issue summary: Between 2026-03-10T02:05 and 2026-03-10T03:30 UTC Axiom Payments reported duplicated streaming responses and a surge of 5xx errors plus client-observed throttling that caused ~18% of payment API calls to fail or be delayed beyond customer SLOs.
Impact: Transaction creation requests experienced duplicate model outputs (duplicate intents leading to double-charges in downstream processing) and elevated latency/timeouts across the us-east region. Customer reported immediate business impact (failed settlements).
Environment: Production (us-east) serving via Hosted API for enterprise tenant using model redwood-ggml-13B pinned version v2026-02-25. Customer on enterprise plan with dedicated routing policy.
Steps to reproduce: 1) Send a stream-based chat request with small initial prompt and repeated 'confirm' function call; 2) Observe two or more streamed final responses within 1s window for same request id; 3) Repeat under sustained concurrent load (~120 rps) and observe API gateway returning 429s or 502s.
Observed behavior: Streaming connection returned duplicate final chunks f
…[truncated]
```

#### #2 `dsid_46673c0aed2445bba9152d27087585e1`

```
Starlane Chat: out-of-order completions across multiplexed shards causing inconsistent conversation state and urgent customer escalation

Issue summary: Between 2026-03-10 01:15 UTC and 2026-03-10 03:10 UTC Starlane observed a sequence of chat completions delivered out-of-order for multi-turn conversations. The customer first reported cases where assistant replies for later user messages appeared before earlier replies, causing application state divergence and automated downstream actions triggering on incorrect prompts. Immediate impact: service interruptions for live chat flows, customer escalated to enterprise support and threatened failover to alternative provider.
Multiple customer production chat sessions returned out-of-order transcript chunks. Approx. 8% of requests from Starlane routed through their dedicated shard pool experienced ordering inversion. Several automated downstream actions (message routing, billing triggers) were executed incorrectly. Business impact included degraded UX and potential downstream transaction mismatches.
1) Use Starlane's multi-turn chat client configured with streaming=true and multiplexing across 4 shards.
2) Send sequences of short-turn use
…[truncated]
```

#### #3 `dsid_5f884c5669194d698c0be56a1df92b33`

```
Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling

Issue summary: Starting ~2026-03-13 11:20 UTC, ChatMetrics reported a rising error floor of 5xx responses for streaming requests. The API Gateway returned 502/503 intermittently and a subset of streaming sessions observed immediate fallback to short-polling which then triggered additional gateway throttling and elevated error rates. Impact: Customer-facing degradation for ChatMetrics (dedicated tier) — streaming API errors for ~40% of active sessions, visible increase in token cost due to retries. Environment: prod-us-east, dedicated tenant cluster. Observed with model redwood/text-xt-3b. Steps to reproduce: 1) Initiate ~600 concurrent streaming sessions from a single ChatMetrics vCPU-based client to the /v1/streams endpoint; 2) Hold long-lived streams with occasional small writes (~1-2 tokens every 2s); 3) Observe on the client: intermittent 502/503 during handshake period followed by server-initiated fallback and then 429s after gateway backoff. Recent changes: nightly keystore rotation completed at 11:05 UTC and an autoscaler policy sweep was applied at 11:10 UTC. Logs/metr
…[truncated]
```

#### #4 `dsid_0be5b3eafb744671a8f21b6e4d01c814`

```
Elevated initial response latency for chat completions after inference compiler swap and model handoff

Customer reports increased delay before first token on streaming chat responses after a scheduled compiler/runtime swap and model variant handoff. Impact: user-facing chat features intermittently stall ~0.6-1.2s before the first chunk appears, and some requests surface 504 timeouts when streaming is enabled.
Start an interactive chat session using the completions streaming API with model pinned to gptx-13b-v2.
Send an initial prompt of ~30 tokens (e.g., 'Draft a two-paragraph product summary').
Observe time from request to first stream chunk; compare against baseline (expected ~<150ms).
Repeat across multiple sessions on us-west-2 and track percentiles.
Run curl with stream=true and request timeout 10s to reproduce 504s on some requests.
req_id=rr-6d9f2e49 start=2026-03-10T02:12:33Z model=gptx-13b-v2 source=api-gateway route=/v1/chat/stream status=200 first_chunk_ms=820
req_id=rr-6d9f2e49 runtime=compiler-v2.9.0 kernel=auto batch_id=987 queue_wait_ms=610 serve_ms=120
error: stream_disconnect code=504 upstream_timeout after=10000ms
trace: scheduler:blocking_wait=560ms batching_ada
…[truncated]
```

#### #5 `dsid_cb214acea1614a5989b59174093df168`

```
Intermittent 5xx spike during priority rebalancing and IO slab fragmentation

Issue summary: Starting ~2026-03-12 02:10 UTC we observed repeated 5xx spikes for a subset of NovaChat requests. Errors are concentrated on conversational chat routes for their dedicated cluster and correlate with bursts of priority rebalances triggered by tenant scaling.
Customer-facing: NovaChat reports elevated error rates (~8-12% 5xx) and increased tail latency. Affected endpoints are producing aborted streaming sessions and failed shorter synchronous requests. Business impact: degraded experience for end users and potential SLA breach for dedicated plan.
Dedicated capacity pool for NovaChat (dedicated-prod-us-west), pinned model redwood/gemini-13b-v1, autoscaler configured with aggressive warmup. Observed on both us-west and us-east mirror clusters during tenant-reshard event.
1) Simulate tenant scale-up: push 300 concurrent short-chat requests with mixed priority headers (high/normal)
2) Trigger autoscaler to rebalance shards (force scale-up of ephemeral workers)
3) Observe api-gateway logs and runtime accept-queue metrics for 5-10 minutes
apigw ERROR 2026-03-12T02:11:05Z upstream_timeout id=abcd-12
…[truncated]
```

#### #6 `dsid_97992c0043184c7b9c10ed2106482ae1`

```
Hosted API: client-side context deadline exceeded on streaming chat (us-west)

Issue summary:
- Customer reports frequent failures in their Go client: `context deadline exceeded` while using streaming chat.

Impact:
- 1-3% of requests fail; retried requests succeed.
- Most failures occur after ~45-55s of streaming.

Primary symptom: Request timeouts
Deployment offering: Hosted API

Notes:
- Customer is behind a corporate proxy; may be closing idle connections.
- However, we also see periodic pauses in token emission on our side during the failures.

Requested:
- Confirm whether gateway idle-timeout or upstream flush buffering changed in recent deploy.
Aisha Rahman (2026-03-11): Escalating because this is impacting production rollout this week.
Dev Patel (2026-03-11): Found a gateway config change enabling response buffering for a subset of streaming routes in us-west.
Dev Patel (2026-03-11): Rolled back buffering config for chat streaming; timeout errors in logs dropped.
Aisha Rahman (2026-03-12): Customer confirms success rate back to normal.
```

#### #7 `dsid_75a5de7f48ae4b65a0ef4384f7ae97d4`

```
Rivermark: streamed completions stop delivering chunks (chunked transfer stalls)

Customer reports that streaming responses intermittently stop sending chunks mid-generation. They see partial output and then no more bytes; client times out at ~75s.

They describe it as: "chunked transfer stalls" / "stream stops sending".

Notes:
- Dedicated cluster in eu-west
- Happens more often during peak hours

Repro (customer):
- /v1/chat/completions stream=true
- Long prompts (>12k tokens) + high concurrency

Cross-refs:
- Slack thread in #support about 'streaming freeze' (timestamp 1770582660)

Aisha Rahman (2026-02-28): Customer call follow-up. They have evidence at the load balancer showing the upstream connection remains open but no more body bytes.
Ethan Park (2026-03-01): Looking for correlation with gateway backpressure and flush intervals. Might be hitting per-conn write buffer limits when token rate drops.
Connor O'Brien (2026-03-02): We should confirm whether keepalive comments are enabled on this dedicated environment; fix from SUP-1842 may not be deployed there.
Ethan Park (2026-03-04): Found dedicated gateway is one minor release behind. Planning patch rollout + add metric for 's
…[truncated]
```

#### #8 `dsid_347eff5fb54c4409ad954708536363ad`

```
Midday throughput lull in dedicated pool during short-stream bursts causing autoscaler lag and per-tenant GPU scarcity

Issue summary:
Customer NovusChat reports repeated mid-day throughput lulls in their Dedicated pool (prod-us-west) that coincide with a high volume of short-lived streaming requests. The symptom is a sudden P99 and P95 throughput drop for routes pinned to dedicated capacity, lasting 3–8 minutes before partial recovery.

Impact:
- Intermittent user-facing latency increases for NovusChat users (p99 latency up 4x).
- Background request queueing observed; some requests hit client-side timeouts.
- Business impact: degraded chat responsiveness during peak local hours.

Environment:
- Dedicated cluster: prod-us-west (reserved capacity for NovusChat).
- Customer tier: Dedicated/enterprise.
- Models: redwood/open-compat-13b and openlm/turbo-8k.
- Autoscaler config: min_replicas=4, max_replicas=24, scale_window=120s, short_stream_heuristic_enabled=true.

Steps to reproduce (customer-provided):
1) Send 300-600 concurrent short streaming sessions (1–3s per stream, frequent restarts) distributed across 20 tenants on the same dedicated pool.
2) Observe scheduler allocations and
…[truncated]
```

#### #9 `dsid_211bee1cefa643279441e2a59eea9965`

```
Chat streaming truncated after transient pipeline reset for dedicated customer

Issue summary: Customer reports that SSE/WebSocket streaming responses abruptly truncate mid-sentence following short transient errors in the serving pipeline (worker restart / routing flip). Impact: customer chat sessions for multiple users end with partial output (last token(s) missing), leading to degraded UX and automated retry loops on their side. Environment: LexiVoice dedicated cluster in us-west-2, running dedicated pool rp-lexivoice-usw2 on redwood-rlhf-13b pinned version v2026-02-28. Observed intermittently starting 2026-03-10 18:12 UTC and reproducible for customer under bursty input patterns (20-30 concurrent long-form chats).
1) Use LexiVoice account credentials to send a streaming chat request to /v1/chat with stream=true and model=redwood-rlhf-13b (pinned).
2) Send a long prompt that triggers ~800-1200 token response (typical LexiVoice assistant reply),
3) Simulate burst concurrency: 20 simultaneous streaming requests from distinct client sockets,
4) While streams are in-flight, trigger a light worker restart or cause a routing update (in test: toggle an autoscaler event or redeploy a ser
…[truncated]
```

#### #10 `dsid_ab2164509b734a2c8e1a33bb5182ea33`

```
CumulusMart — intermittent streaming fragment interleaving due to routing oscillation (post-incident escalation)

Issue summary:
Customer CumulusMart reported intermittent streaming responses that showed interleaved fragments and partial duplicate transcripts for multi-part chat completions. Symptoms began 2026-03-10 01:20 UTC and recurred on subsequent traffic spikes. Impact: several customer-facing sessions returned mixed transcripts (segments from two separate handler instances), resulting in corrupted messages and increased token billing for duplicate partial outputs.

Impact:
- Affected ~12% of CumulusMart's streamed completions during the incident window (peak 01:20–03:50 UTC).
- Some sessions exhibited fragment interleaving (parts from two different responses merged out-of-order).
- Elevated token usage contributed to a billing delta (temporary credit issued — see Resolution).

Environment:
- Dedicated pool: cumulus-dedicated-us-east (reserved capacity).
- Models used: redwood-8k-v1 primary, redwood-quant-4bit-v1 as fallback.
- Traffic routed through api-gateway cluster rgw-3 and routing control-plane region us-east-ctrl.

Steps to reproduce (observed in customer traffic):
1
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 56: `qst_0310::intra_document_reasoning` · N=100000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`other`
- **LLM note:** The retrieved document IDs do not include the expected document ID, resulting in a Hit@10=False. The retrieved chunks are somewhat relevant but do not directly address the specific details of the question. The gold chunk is on-topic and non-empty, but the retrieval misses the target document entirely, indicating a potential issue with the retrieval process or embeddings used.

### Question

In the on-prem cutover readiness weekly sync meeting, who attended, and what two checkpoint meetings (with dates) were scheduled around the staging soak test?

### Gold document(s)

#### GOLD `dsid_b9025f196ac14b2cb7a2905654dd42d7`

```
On-prem Cutover Readiness: Egress & Capacity Playbook - weekly sync

Meeting header:\nDate/Time: 2026-09-30 15:00 UTC\nDuration: 48 minutes\nAttendees: Samir Patel (Redwood AE), Lila Novak (Redwood SE), Diego Ramos (Redwood), Marco Rivera (Aurelia CTO), Priya Singh (Aurelia NetOps), Ethan Cole (Aurelia SRE)\n\nAuto-summary (auto-gen, may be rough):\n- Week 5 of on-prem pilot; focus on cutover readiness, egress routing, kernel upgrade and capacity shaping.\n- Identified two main blockers: egress firewall rules & kernel compatibility test failures in one host.\n- Agreed next steps: run soak test, share runbook, provide firewall rules, finalize rollback steps.\n\nTopics: cutover readiness, egress NAT/allowlist, kernel upgrade 6.x, capacity/traffic shaping, fallback policies, soak tests\n\nAction items (captured in metadata too)\n\nTranscript body:\n[00:00] Samir (AE): okay, hi everyone, thanks for joining. good to see you. this is our weekly sync for the on-prem pilot, focused on cutover readiness. we have samir, lila, diego on redwood side. aurelia: marco, priya, ethan, thanks for making time.\n\n[00:22] Marco (CTO): yeah thanks, morning for us. short timezone note, we're on a hard deadline for a staged cutover in two weeks so want to make sure blockers are surfaced.\n\n[00:35] Lila (SE): quick agenda I have — egress readiness, kernel upgrade status, capacity shaping + soak plan, and then open issues. if that works for you we can dive in.\n\n[00:48] Priya (NetOps): works. first item, priya here, egress. we tried to lock down the firewall allowlist but there are some internal groups that route via a proxy and we saw some TLS handshake fails when we hit the redwood private endpoints from our test lab. not sure if it's our proxy or the egress ip set.\n\n[01:12] Samir: got it. can you paste the exact error / log snippet? sometimes the handshake looks like a cert chain timing out vs ip-level block.\n\n[01:24] Priya: (typing sound) i've pasted a snippet in the chat — "tcp reset after 3s handshake timeout, peer cert not found" — and the source ip is from our transit proxy 10.88.4.23, which I believe isn't in your allowlist.\n\n[01:40] Diego: hmm, our NAT egress pool for 
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_8463a5db671f40318362748fc9e9edb4`

```
Deployment safety checks and A/B cutover sync

Weekly POC sync focused on go-live safety: agreed on an A/B cutover with a canary ramp, defined metrics and rollback criteria, planned a staging dry-run, and assigned runbook and telemetry deliverables.
Meeting header:
Date: 2025-09-03
Start time: 14:00 PDT
Duration: ~54 minutes
Location: Zoom
Attendees: Sofia (Redwood AE), Daniel (Redwood SE), Lena (Redwood CSM), Priya (KiteWave), Ethan (KiteWave SRE), Marisol (KiteWave Product), Tom (KiteWave Infra)

[00:00:00] Sofia: Hey everyone, thanks for joining. Quick check — agenda is safety checks for deployment, confirm A/B cutover plan, monitoring knobs, and next steps. Sound good?
[00:00:12] Priya: Yep, that's what we want. We have the exec alignment for next week so this is the last POC sync before staging dry-run.
[00:00:25] Daniel: Cool. I'll run through current telemetry, recent perf numbers, and the proposed canary ramp with thresholds.
[00:00:33] Ethan: Before you start, real quick — we saw a spike in tail latency on Friday when prefix cache was cold, wanted to see if that's reproduced on Redwood dedicated or if it's our end.
[00:00:45] Daniel: Right, that was the KV cache warm-up is
…[truncated]
```

#### #2 `dsid_eb3969b49ce444c092e6ef7aa1d10f55`

```
Weekly POC Sync — heuristic tuning and emergency routes

Reviewed week-over-week POC metrics (latency / failure modes), discussed heuristic tuning for token cutoff and KV cache behavior, compared two catalog candidates for version pinning, and agreed emergency fallback routes and owners. Agreed next steps: run 24h degraded-path soak, share quantization benchmark sheet, and update runbook for cutover criteria.
latency vs cost tradeoffs
model catalog comparison (v1.3a vs v1.2-q4)
KV cache / prefix caching oddities
soft fallback / emergency cutover routes
audit & compliance notes (KMS, audit logs)
Owner: Jonah Li; Item: Run 24-hour degraded-path soak with v1.3a pinned and capture p99 latency + token-cost; Due: 2026-01-23
Owner: Sarah Nguyen; Item: Provide 3 representative prompt sets (support/clinical-summary, intake-parsing, guidance-gen) for regression checks; Due: 2026-01-22
Owner: Carlos Herrera; Item: Confirm network egress rules for VPC peering and share firewall policy snippet; Due: 2026-01-21
Owner: Maya Patel; Item: Share quantization benchmark spreadsheet and recommended quant profiles for BrightHealth workload; Due: 2026-01-22
Start 24h soak on staging-routing -> runbook to
…[truncated]
```

#### #3 `dsid_00b1aa8661ca40c6bee153cfbc57e18d`

```
Helios pilot readiness & cutover rehearsal

Meeting header:
Date: 2026-02-11
Start: 15:00 UTC
Duration: 52 minutes (scheduled)
Attendees: Sophie Martinez (Redwood AE), Daniel Cho (Redwood SE), Priya Kapoor (Helios Head of ML), Aaron Blake (Helios Platform), Mei Lin (Helios Security)

Brief summary:
Quick pilot sync focused on go-live/cutover runbook, canary strategy, monitoring thresholds, and outstanding compliance sign-offs. Agreed to a dry-run rehearsal and a small set of action items. Some clarifications needed around KMS access and rollback timing.

Topics: runbook walkthrough, canary % and A/B gating, telemetry and dashboards, security approvals (SOC2 / KMS / SSO), perf soak tests, rollback and fallback policies.

Transcript body:
[00:00:00] Sophie: hey everyone thanks for joining, we'll keep this tight, 50 minutes ish. quick roll call, daniel you on?
[00:00:08] Daniel: yea here, ready.
[00:00:10] Priya: hi, priya here.
[00:00:12] Aaron: aaron in.
[00:00:14] Mei: mei here.
[00:00:16] Sophie: awesome, goal for today is to walk the cutover runbook and agree on canary gates and monitoring thresholds, also clear any open security blockers.
[00:00:30] Priya: sounds good. we got th
…[truncated]
```

#### #4 `dsid_e4f5c5e330fb4acba12b78927d0bb632`

```
Governance Handoff and Cutover Ops Walkthrough

Mid-poc weekly sync focused on handoff to ops for production cutover. Reviewed canary gating, rollback triggers, monitoring dashboards (latency p95/p99, token cost, error rate), and compliance checkpoints. Agreed on dry-run date and owners for runbook, telemetry export, and security checklist.
Meeting header: 2026-05-20 09:30 UTC | Duration 52m | Attendees: Maya, Samir, Jules (Redwood); Olivia, Marcus, Priya, Diego, Nina, Legal rep (LumenGrid)

[00:00] Maya Chen: Alright folks, thanks for joining. purpose of today is to go through the cutover runbook handoff, confirm canary thresholds, and make sure security signoffs are on track. uh please shout if i talk too fast.
[00:22] Olivia Grant: yeah thanks Maya. high level we want minimal blast radius. timeline hasn't moved — still aiming end of month for pilot->prod, but we need ops to own the gates.
[00:34] Samir Patel: quick intro from my side, i'll walk the telemetry and the gating matrix. note, some of the names in the dashboards are from the staging cluster so you'll see 'redwood-deploy-4' which is fine.
[00:46] Marcus Lee: one ask up front — we need a clear P95 and error-rate threshol
…[truncated]
```

#### #5 `dsid_eb9ab34e2572447095904775e6269dbc`

```
Silverpine Pilot - Gov Ops Tuning Sync

Meeting header:
Date: 2026-11-29
Start: 15:00 UTC
Duration: ~52 minutes
Attendees: Alex Chen (Redwood AE), Priya Rao (Redwood SE), Diego Morales (Redwood CSM); Mark Linton (Silverpine CTO), Rosa Vega (Security Lead), Imran Shah (SRE), Tanya Brooks (PM)

Summary (auto): quick results review from week 3 of pilot, focused on governance / ops items: SSO end-to-end, audit log fidelity, data retention requests, SOC2 artifacts. Agreed next steps for longer dedicated soak and SOC2 docs link.

Transcript:
[00:00:00] Alex Chen: hey everyone, thanks for joining. i think we have a full house — quick roll call?
[00:00:06] Mark Linton: Mark here.
[00:00:08] Rosa Vega: Rosa.
[00:00:10] Imran Shah: Imran, SRE.
[00:00:12] Tanya Brooks: Tanya, product.
[00:00:15] Priya Rao: Priya from Redwood. Diego's on but he had a calendar overlap so he may drop in.
[00:00:20] Alex Chen: cool. agenda — quick perf results, then security ops: SSO, audit logs, retention, SOC two ask, and then next steps. anything to add?
[00:00:30] Mark Linton: nope that's perfect.
[00:00:33] Priya Rao: i'll start with the results slide — last run we did a mix of low-latency hosted traffic and
…[truncated]
```

#### #6 `dsid_25034eed301f4aaf8ef8f45d5313dd9d`

```
Pilot: canary rollforward readiness & nested routing check

Weekly POC sync focused on readiness for canary rollforward, routing priorities for nested VPC paths, and one-off kernel upgrade plan. Discussed fallbacks, KMS audit requirement and timing for cutover. Agreed to a short soak with controlled traffic profile and three clear rollback triggers.
Meeting header: 2027-09-28 15:00 UTC | Duration: 45m | Recording: Auto\nAttendees: Alex Monroe (Redwood AE), Priya Singh (Redwood SE), Jordan Price (Halcyon NetOps), Taylor Reed (Halcyon CTO), Samira Khan (Halcyon Security), Diego (Halcyon SRE), Rita (App Owner)\n\n[00:00] Alex (AE): Hey everyone, thanks for joining. Quick agenda - canary rollforward readiness, nested routing check, kernel/quant upgrade status, and security gating. We'll try to keep it tight.\n[00:18] Jordan: Yeah, thanks Alex, quick heads up, we're a little behind on the cloud egress ACLs but planning to finish tomorrow, so want to make sure that doesn't block the canary.\n[00:30] Priya (SE): Okay noted, if the ACLs miss the window we can still run a private canary within the VPC, but latency profile will be a bit different because of the nat egress.\n[00:45] Taylor (C
…[truncated]
```

#### #7 `dsid_026159f20b7d493ca45e7a3d924b5220`

```
POC weekly sync — signal calibration, on-call rotations, and cutover scripting

Meeting header: 2026-08-26 16:00 UTC, duration ~49m. Attendees: Maya Chen (Redwood AE), Ethan Park (Redwood SE), Sofia Ruiz (Redwood CSM), Jonah Bell (Redwood Infra), Priya Shah (Lumenary Platform Lead), Carlos Mendes (Lumenary SRE), Alicia Grant (Lumenary Security), Tom Wu (PM), Rachel O'Neil (Data).\n\nSummary (auto-gen, may be incomplete): quick run through of this week's pilot telemetry, discuss SLO thresholds and false-positive alerts, align on canary time window and on-call handoffs, action items for cutover scripting and KV cache warmup.\n\nTopics: SLO burn-in numbers; latency p50/p95 drift during business hours; error class split; on-call routing & escalation; cutover script responsibilities; canary gating thresholds; synthetic test plans; security audit checklist follow-up.\n\n[00:00] Maya Chen: hey everyone, thanks for joining. we'll kick off — we have about 50 minutes. quick roll call?\n[00:12] Priya Shah: priya here.\n[00:14] Carlos Mendes: carlos.\n[00:16] Alicia Grant: alicia.\n[00:18] Tom Wu: tom.\n[00:20] Rachel O'Neil: rachel.\n[00:21] Maya Chen: and from redwood: ethan?\n[00:23] Ethan 
…[truncated]
```

#### #8 `dsid_85ca1944512a40418dd9c8fc5b0dae0d`

```
POC Weekly - Incident triage + telemetry gaps

Meeting Header:
Date: 2025-11-04 14:30 PST
Duration: 43 minutes
Attendees: Maya Patel (Redwood AE); Jamal Rivers (Redwood SE); Laura Chen (SentraHealth, CTO); Omar Ruiz (SentraHealth, Platform Eng); Priya Shah (SentraHealth, Data Security)

Summary:
Quick sync on last week's production-like run that surfaced intermittent 5xxs and long tail latencies. Root-cause hypotheses narrowed to a combination of a KV-cache eviction pattern + upstream bursty retries causing queue saturation; telemetry gaps made it hard to correlate client retry timing to server-side load. Agreed next steps include a coordinated soak test, log bundle export, and instrumentation additions.

Topics: telemetry gaps, rate limit headers, retry backoff, KV cache hit ratio, SOC2 / data residency questions, staging soak plan.

Transcript:
[00:00] Maya: hey everyone, thanks for joining, we're gonna run 45 minutes ish, recap of the weekend run and triage the 5xx spike, jamal will jump into traces in a bit
[00:18] Laura: thanks, yeah we saw a couple of customer-facing 502s yesterday during the morning batch jobs, about 1.2% of requests in a 10 minute window spiked, most were s
…[truncated]
```

#### #9 `dsid_44e5f0ab26224c7787364fadac519579`

```
POC Network Rehearsal & Routing Acceptance — AstraVault

Weekly POC sync focused on a dry-run cutover (rehearsal) of Redwood Private into AstraVault VPC, validation of routing acceptance criteria, and review of kernel and quantization upgrade impact. Agreed on go/no-go checklist items, some outstanding MTU/egress shaping tweaks, and follow-ups for security artifacts.
Rehearsal plan and cutover checklist
Routing acceptance criteria and rollback triggers
Kernel/quantization upgrade schedule
VPC egress shaping and MTU mismatch troubleshooting
Security audit docs and KMS integration sign-off
Next steps for final acceptance test
[00:00] Lena Park: All right folks thanks for joining on time. Quick roll call — me, Diego from infra, Sara on CSM side.
[00:08] Maya Singh: Maya here, Jon, Priya and Ethan also on.
[00:12] Lena Park: Great. Agenda today: run the rehearsal checklist, validate routing acceptance, and confirm kernel/quant schedule. We'll try and keep to 45 minutes.
[00:25] Diego Marin: I'll start with the routing diff — we ran the staging sweep this morning, most flows hit the private gateway, fallback path to hosted tier exercised twice. There was a ~20ms spike on the long tail w
…[truncated]
```

#### #10 `dsid_484f118b24dd4bd3b290e59dce06e8f8`

```
Pilot safety matrix, runbook rehearsal, and A/B traffic concord

Weekly POC sync focusing on go/no-go gating: rehearsed runbook steps, refined safety matrix and rollback criteria, validated A/B traffic slices and monitoring dashboards. Agreed warmup plan and synthetic smoke tests; Redwood to deliver updated runbook and telemetry checklist.
Meeting header: 2026-11-03 15:00 PST | Duration: 62m | Recording: yes
Attendees: Sara Patel (Redwood AE), Miguel Ramos (Redwood SE), Aisha Khan (Vantis Platform), Derek Lin (Vantis ML), Maya Ortiz (Vantis Prod Ops)

00:00 Speaker 1 - Sara: okay good afternoon everyone, thanks for joining, we wanted to run the safety matrix and do a full runbook rehearsal for the pilot cutover, especially the A slash B traffic slices and the circuit breaker thresholds. is that still the right scope for today?
00:22 Speaker 2 - Aisha: yes that works, we have ops standing by and we carved out 2 hours tomorrow for the dry-run but wanted to sync first on the exact gating. quick note, we had one more ingest spike in staging overnight, not sure if that affects the warmup plan.
01:12 Speaker 3 - Miguel: yep saw the spike, likely related to our synthetic generator. for wa
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 57: `qst_0349::project_related` · N=75000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The Hit@10 is incorrectly labeled as false; none of the expected_doc_ids are in the top-10 retrieved IDs. The retrieved chunks are relevant to EU-West issues but do not address the specific onboarding email problems. The failure mode is an embedding near miss due to the general relevance but lack of specific overlap. Gold and retrieved chunks are non-empty and on-topic, but the retrieval did not capture the expected documents.

### Question

What caused the EU-West activation funnel and onboarding email issues in late January, and which code/config changes fixed them?

### Gold document(s)

#### GOLD `dsid_21d6b99dc771418287d61444f373852e`

```
New self-serve user not receiving onboarding email sequence (no sends observed for eu-west signups)

Issue summary:
Customer reports they signed up for Redwood Hosted API and did not receive any onboarding emails (welcome / API key / first request). They expected the sequence because a teammate in the US received it the same day.

Impact:
- Customer unable to find quickstart links and activation guidance from lifecycle emails.
- Risk to activation metrics during Lifecycle Growth Experiments sprint.
- Potential broader impact if this is region-based (eu-west signups).

Customer details:
- Company: Lumen Support
- Tier: self_serve
- Signup email domain: customer provided in Support portal (internal note: corporate domain, not a consumer mailbox)
- Approx signup time: 2026-01-30 17:10–17:20 UTC

Environment:
- Console region observed: eu-west
- Product: Hosted API signup + lifecycle onboarding v2

Expected result:
- Email #1 (Welcome / Create API key) within ~5 minutes of signup.

Actual result:
- No onboarding emails received after 24+ hours.
- Customer checked spam/promotions and confirmed nothing.

Troubleshooting performed (Support / MktOps):
1) Confirmed customer is not unsubscribed in email preferences (no opt-out record found).
2) Checked suppression list / bounce logs: no prior bounces or blocks for this address.
3) Checked lifecycle send audit events for the user_id: no "lifecycle_email_send_requested" event present.
4) Checked experiment cohort/flag assignment: user appears eligible for onboarding email v2.

Initial hypothesis:
Trigger worker not processing signup events for eu-west (no send attempted), vs deliverability problem.

Escalation:
- Paging/looping in Growth Eng owner for trigger logic + regional event consumption.
- Related internal threads: #support (reports of similar complaints) and #marketing deliverability ramp plan.

Customer-facing note (to send once confirmed):
Apologize; confirm we identified a system-side issue and can provide links to the quickstart + resend the first message manually while we fix the underlying trigger.
2026-01-31 09:12 UTC — Tyler Benson (Reporter)
Created after 3 similar HelpScout pings escalated to Growth Ops. T
…[truncated]
```

#### GOLD `dsid_44cf2d75d70d4365914aa46947a94b1d`

```
Fix duplicate signup event emission (skewing activation funnel)

## Context
We’ve been seeing inflated counts at the top of the activation funnel (signup stage) since the lifecycle growth sprint instrumentation landed. This has been most visible in regions with higher auth callback latency and for users who refresh the console during the post-signup redirect.

Root cause: `signup_completed` was emitted from *two* places:
1) Auth callback handler (server) when we exchange the OAuth/session token
2) Console bootstrap (client) when `currentUser.isNew == true`

In the happy path these happen once each (still bad), but in the presence of retries/refresh, the client-side emission could occur multiple times, leading to 2–4 events per new user. This skewed the funnel conversion rate, especially when computing “% of signups completing first request within 7 days” with naive event counting.

## What changed
- Make the server-side emission the single source of truth for `signup_completed`.
- Remove client-side fallback emission and replace it with a debug-only log (behind an internal flag) to preserve troubleshooting signal without polluting analytics.
- Add idempotency guard on the server event publisher:
  - Dedupes `signup_completed` per `user_id` for a short window (30 minutes) using an event-key in Redis.
  - Also dedupes `activation_signup` alias to avoid re-introducing duplicates via legacy event name.
- Add a regression test for the callback handler to ensure repeated callbacks do not emit additional signup events.

## Why this is safe
- The event is informational/analytics-only (no product logic is gated on it).
- Server is already the canonical place where we know the signup is complete.
- Dedup window is short and keyed by user, so it won’t suppress legitimate re-signups (new user id) or later lifecycle events.

## Validation
### Before
- Sample (2026-01-27 UTC): ~1.82 `signup_completed` events per distinct `user_id` (p50=2, p95=3)
- Funnel dashboard showed occasional >100% “signup → api_key_created” conversion for small cohorts (clear sign of duplication)

### After (staging + prod canary)
- Staging load test (forced refresh + retry): 1.00 `signup_completed` ev
…[truncated]
```

#### GOLD `dsid_fe7a496e795b4baca997e655f9316fc5`

```
Activation funnel dashboard discrepancy (EU-West drop + mismatch vs warehouse) after lifecycle growth instrumentation changes

Issue summary
- Growth/Marketing and Product flagged a sudden drop and cross-source mismatch in the activation funnel metrics (signup → API key created → first request) used for the Lifecycle Growth Experiments sprint.
- Primary symptom: EU-West conversion from signup → api_key_created appeared ~12–18% lower than US-East starting 2026-01-21 18:00 UTC, and overall “new signups” appeared higher than expected vs auth/user tables.
- Impact: Week 1–2 experiment readouts risked being invalid/noisy; we paused one planned expansion of the email A/B until numbers were reconciled.

Impact
- Affected dashboards: Activation Funnel (Observability Pack) + internal Looker view used by Growth.
- Impacted decisions: stop/go thresholds and lift calculations for onboarding email v2 and console nudge experiments.
- Customer impact: none direct (reporting/measurement issue only), but could cause us to make incorrect product/GT-M decisions.

Detection
- Reported via Slack #help thread ("events missing in one region") and follow-up in #eng-platform on 2026-01-22.
- Observability Pack funnel panel showed EU-West drop; Mei Lin noted mismatch vs daily new users in warehouse.

What changed recently
- PR-28431: added/standardized activation events for signup → api key → first request → first 100k tokens.
- PR-241: new dashboard panels + funnel query definitions.
- Console nudge framework shipped behind flags; additional event properties and cohort assignment introduced during the week.

Initial hypotheses
1) Ingestion lag or partial pipeline outage in EU-West.
2) Region routing misconfiguration (EU events landing in US dataset or vice versa).
3) Event validation rejecting records due to missing required properties (user_id, event_id) for EU only.
4) Duplicate event emission inflating baseline in one region, making EU look like it dropped.

Investigation notes (high level)
- Confirmed ingestion health: Kafka consumer lag normal; no sustained drop in raw event volume by region at the edge collectors.
- Cross-checked three sources for the same window (2026-01-21 00:00
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_140d90d0c1af492a89a8f6e52230ae5d`

```
Postmortem: EU API latency and elevated 5xx (edge routing cache)

h1. Summary
On 2026-01-19 we experienced elevated p95 latency and intermittent HTTP 5xx for a subset of EU-hosted API traffic. The incident lasted 47 minutes end-to-end. Customer impact was concentrated in the eu-west region and primarily affected chat completions with streaming enabled.

*Customer impact:* Yes (degraded performance + partial errors)
*Severity:* SEV-2
*Owning engineering team:* Platform Engineering (Traffic & Edge)
*Primary services:* edge-router, request-gateway, redis-edge-cache

h1. Impact
* ~12% of EU requests exceeded the latency SLO (p95 > 3.5s)
* ~1.8% request failure rate (HTTP 502/503) for EU traffic
* No data loss; retries succeeded after mitigation

h1. Timeline (UTC)
* 10:12 - Alert fired: eu-west request-gateway 5xx > 1%
* 10:15 - On-call acknowledged; triage indicates edge-router cache churn
* 10:21 - Mitigation 1: disabled new cache key format via feature flag
* 10:28 - 5xx decreases but latency still elevated
* 10:35 - Mitigation 2: increased redis-edge-cache memory limit + restarted one shard
* 10:45 - Latency returns to baseline
* 10:59 - Incident resolved; monitoring for recurrence
…[truncated]
```

#### #2 `dsid_0f4afe0e4f4c467bb33500c021f2f394`

```
Storm Harbor AI

Inbound self-serve signup on 2026-02-20; started with free tier credits; quickly hit latency friction when testing chat flows.
Customer profile: midsize support tool, routes live chat + triage summaries, ~10k monthly active conversations. Cost-sensitive but wants responsive UX.
Symptoms: EU users see slower responses vs NA; occasional long tail timeouts. Dev quote: 'EU feels 2x slower, users are noticing.'
Initial repro: long system + user message (~1200 tokens combined) -> request sometimes completes after client timeout (60s). We saw p99 spikes during history replay.
Engineering notes from initial debug: most requests served from us-east-1; customer defaulted to region-agnostic calls (no explicit region header).
Recommendation given in call: set explicit region to nearest infra (e.g., eu-west-1) for EU traffic; enable streaming to reduce perceived latency; raise client timeout to 120s for long-context workflows.
Tried quick test on 2026-03-01: switched a sample user to eu-west-1 -> median latency improved ~45% (customer observed). Still saw p99 spikes for requests that replay large conversation history.
Suggested prompt fixes: trim assistant history (last 6 messa
…[truncated]
```

#### #3 `dsid_d3edd63b9ec54523ad12bd9be3d7e996`

```
Postmortem: EU-West capacity shortage and region fallback (2025-03-03)

h2. Summary
On 2025-03-03, a GPU capacity shortfall in eu-west-1 impacted a subset of Hosted and Dedicated traffic pinned to that region. Mitigation required activating *automatic region fallback* (eu-west-1 -> us-east-1) for eligible routes until additional capacity was brought online.

h2. Impact
* Elevated p95 latency and increased 429/503 responses for region-pinned routes in eu-west-1.
* Customers: 7 Hosted orgs and 1 Dedicated tenant with optional cross-region allowance enabled.
* Duration: ~41 minutes of degraded performance; ~18 minutes of hard errors for the most constrained pool.

h2. Timeline (UTC)
* 09:42: Capacity alert: available_gpu_count < 5 in eu-west-1 pool rw-a100-eu-01.
* 09:48: Saturation exceeded 95% and queue wait climbed > 400ms.
* 09:51: Mitigation: enabled *region fallback* for "chat-default" and "embeddings-default" where customer policy allows cross-region.
* 09:54: Router began directing overflow to us-east-1 for eligible traffic.
* 10:03: Error rate dropped; latency partially recovered.
* 10:23: Added 8 GPUs to eu-west-1 pool; disabled region fallback after stabilization.

h2. Miti
…[truncated]
```

#### #4 `dsid_87fcd4642ef645919bb04b48e043a0c7`

```
Copper Harbor Assistants

Inbound SMB lead from product signup (self-serve). Started with Hosted API last month; onboarding notes below. Customer complaints: slow chat responses for EU users, client timeouts, occasional 504s in peak. Behavior summary from call: 'responses are fine in dev but degrade unpredictably at peak hours' — quoting Head of Product. They are cost-sensitive and on a usage billing model; prefer to avoid Dedicated for now. They want quick actionable changes they can make without infra changes. SE call 2026-03-04 captured latency traces and sample prompts. They are using default region (us-east-1) for calls from an EU-heavy user base — probable routing mismatch. Current config: single API key in app, default timeout 30s in client library, max_tokens often set to 1200 (long summarization), streaming disabled. No KV/prefix caching implemented. Security: require SSO later, currently using basic API keys; need audit log capability for compliance.
perceived high latency; need clear perf steps
unclear timeout/retry defaults
billing questions from finance
Target: sub-500ms median for short chat turns, P95 <1200ms for support flows; Current: median ~420ms but P95 spikes 1
…[truncated]
```

#### #5 `dsid_c9728b8229b84c9a9a1c61f51a31c930`

```
Sparkwell Lumenify

Inbound SMB lead from form sign-up; experimenting with self-serve hosted API. Main pain: latency complaints from EU customers after they switched region to eu-west-1. CTA: want quick wins they can implement without moving to Dedicated.

Quick summary (from kickoff call 2026-03-02):
- CTO Ravi: 'Some customers think responses are slow — we get complaints during peak support hours.'
- Primary flow: chat-first support widget + on-demand doc search (embeddings) for KB.
- Tested models: gpt-open-7b-like (opt variant), default region eu-west-1, fallback to us-east-1 currently disabled.
- Cost sensitivity: medium — SMB budget but needs predictable token costs.
- Security: SOC2 in next quarter; requires SSO and audit logs.

AE notes (Aisha): brief, pragmatic. They prefer short prescriptive docs. Will not move infra, wants Hosted API tuning. POC target: reduce median latency by ~30% and p95 under 600ms for chat flows.

Ticket history: brief reproduced by INF-4129 (support identified slow cold starts on first prompt in a session).
Support chat with KB-augmented retrieval + light embeddings for reranking. Typical prompts short (10-50 tokens), but some long context messages
…[truncated]
```

#### #6 `dsid_5262d75d9e954e94b2cb2f73387196b5`

```
CopperClasp Onboarding

2026-02-20: Inbound signup via quickstart; automated welcome + API key issued
2026-02-24: AE intro (Ava) — discovery questionnaire completed; primary use: chat widget on product pages
2026-03-03: Exploratory call (ff:call_2026-03-03_01) — customer reports EU latency spikes and occasional timeouts
2026-03-05: SE Jordan ran baseline perf in us-east-1; observed p50 ~220ms, p95 ~820ms for 512-token prompts
2026-03-08: Shared tuning checklist and basic timeout recommendations; customer to run smoke tests
2026-03-10: Customer uploaded sample prompts and asked for region guidance, streaming timeouts, prompt-length best practices
Inbound SMB lead — self-serve signup, wants hosted API only. Peak traffic small: ~10 rps, typical 2-5 rps.
Primary problem: 'EU storefront users see timeouts during checkout chat' — spike window 17:00-20:00 CET.
Observed routing issue: many EU requests were hitting us-east-1; recommend final production region in eu-west-1 or eu-central-1.
SE recommendations (initial):
- Use eu-west-1 for EU traffic via region-aware routing in client; set fallback to us-east-1 for overflow.
- Streaming: enable response streaming and set client-side idle time
…[truncated]
```

#### #7 `dsid_b48d3d3042e846059fcde82a3ae771ab`

```
Amberwell Assistify

2026-02-20: Self-serve signup, free credits activated
2026-02-24: First inbound support ticket — "responses feel slow in EU users"
2026-02-26: AE outreach: confirmed majority of traffic from eu-west-1 region; provided initial perf checklist
2026-03-01: Fireflies meeting with engineering (ff-20260301-amberwell) — collected request IDs and p95s
2026-03-03: SE performed quick triage: identified calls hitting us-east-1 default endpoint via CDN fallback
2026-03-05: Offered canary change to region param + streaming advice; awaiting product team approval
Inbound SMB lead — small support SaaS (chat + doc summarization) mainly self-serve onboarding.
Primary complaint: "latency spikes for EU customers, p95 ~ 1100-1400ms, median ~600-800ms"
They are on hosted API, default region appears to be us-east-1 in our logs; most users are EU and APAC.
SE note: logs show roundtrip + model-tokenization overhead. Quick wins: switch region to eu-west-1, enable streaming, reduce client timeout to 15s to surface errors faster.
Prompt guidance given: keep system + retrieval context <= 1,200 tokens; prefer concise instruction templates; limit max_tokens for generation to 200 when showing 
…[truncated]
```

#### #8 `dsid_f1c8b96a990145038be9e21d4275af61`

```
Aftershock: failover oscillation and aggressive shedding during cross-region surge

Summary: A high-traffic event on 2026-02-27 triggered a partial regional failover that exposed a configuration mismatch between circuit-breaker hysteresis and load-shedding thresholds across regions. Traffic oscillated between primary and secondary regions, causing p99 latency and success-rate SLO misses for a 22-minute window. The incident required an emergency rollback of a circuit-breaker hysteresis change, temporary relaxation of shedding policies, and a coordinated cache-warmup campaign to stabilise tail latency.
2026-02-27T14:03Z - First elevated error rates detected on primary region (us-west-2) for model /v1/generate routes.
2026-02-27T14:05Z - Automated regional failover policy started redirecting 30% of new sessions to eu-west-1 as latency crossed the soft-SLO threshold.
2026-02-27T14:07Z - eu-west-1 circuit breakers, configured with more aggressive open thresholds in the recent rollout, began tripping and shedding according to the new profile.
2026-02-27T14:10Z - Observed traffic oscillation: as eu-west-1 shed, traffic remapped back to us-west-2, pushing us-west-2 over higher tail latenci
…[truncated]
```

#### #9 `dsid_1736ae85d6ca46deab8d7b192f551c18`

```
Little Owl AI Tools

Inbound SMB lead via organic signup - small, engineering-led startup building smart help center
Primary ask: lower latency for EU customers; currently defaulting to US region from SDK -> want guidance on region selection
User quote on 3/2 call: 'EU customers complain responses take too long — feels intermittent.'
Observed: staging traces show higher p99 in eu-west; p50 acceptable but p95/p99 spikes during batching windows
Client uses dynamic prompt templates (customer history + long doc snippets) -> prompt length varies 150-1200 tokens
AE notes: cost-sensitive, will likely stick with hosted API if we can get consistent sub-300ms median for short chat prompts
SE recommended actions: region pinning in request, set client-side timeout to 2s for UI calls, compress/trim customer history, enable streaming where feasible
Suggested quick wins: - test model redwood-small-quantized for short chat (lower latency) - enable prefix KV caching for repeated context - set retry/backoff for timeouts
Testing ask: run 10k calls across us-east and eu-west with identical prompts, include streaming vs non-streaming comparison
Docs links shared: /docs/region-selection, /docs/streaming
…[truncated]
```

#### #10 `dsid_5165a7e247c4402598a0005b092aa4b6`

```
Velvetloom Digital

Lead source: inbound signup (self-serve). Reported problem: production chat bot (customer support) experiencing jittery responses and occasional timeouts for customers in EU. Key quotes: "Responses either come fast or hang for 10s+, inconsistent across regions." Early discovery call (03/03): - Ran through integration: using JS SDK, default timeout 60s (client), not pinning region. - Observed traffic pattern: many short messages (avg prompt 120 tokens) but spike on long context windows (history + 1-2 attachments). - Cost sensitivity: SMB budget, wants to keep per-session token cost low; open to small Dedicated later but prefers Hosted API now. Performance hypotheses: - Likely region routing to us-east when model pinned to global endpoint causing cross-region latency for EU users. - Some prompts include long system messages and full conversation context (can trim/prefix-summarize). - Default retry/backoff not configured; SDK timeouts currently 60s leading to UX issues when model falls back or queuing occurs. Agreed next steps: - AE (Sophia) to set up 45m tuning session with Diego (SE) for 03/10 to run live traces and adjust region override. - Customer to share sam
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 58: `qst_0391::constrained` · N=25000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks discuss similar issues like 5xx errors and latency spikes but do not match the specific incident described in the gold chunk. The failure mode is likely an embedding near miss due to similar but not identical content. The chunk quality is decent, but relevance to the specific question is low.

### Question

In the hosted API incident in late April 2026 where streaming requests started returning 502/504 and non-streaming requests also saw a sharp tail-latency increase, what was the underlying trigger (involving an edge keepalive/connection-TTL change) and what immediate mitigations were used to restore service?

### Gold document(s)

#### GOLD `dsid_0b0595a6d39247ada6238d8311b587f8`

```
Streaming write-stall + TTL regression — hosted API outage postmortem (2026-04-25)

Summary:\n\nOn 2026-04-25 at ~02:12 UTC the hosted streaming API experienced a high-severity outage that manifested as 5xx errors for streaming sessions and extreme tail latency for non-streaming requests. Impact lasted ~43 minutes for customers on affected regions and degraded for another 90 minutes during mitigation rollouts. Root cause: an unintended change to a per-connection TTL/keepalive config combined with an edge buffer write-stall bug in the streaming proxy, which caused head-of-line stalls and backlog amplification under normal traffic spikes.\n\nImpact:\n- Scope: ~11% of streaming sessions experienced repeated 5xx (502/504) immediately; additional ~7% of non-streaming requests saw 95th+ latency spikes from 600ms -> 3.2s.\n- Customers: 23 enterprise tenants saw visible error rates; a handful of PLG customers reported degraded developer experience. No data loss or model correctness issues were observed.\n- Business: Incidents triggered PagerDuty P0 and on-call SREs initiated incident response. External status page was updated.\n\nHow it was detected:\n- First alert: custom anomaly detector on streaming session error-rate crossed threshold at 02:13 UTC (SRE paging).\n- Secondary signals: edge response-time dashboards and increased connection resets observed in edge logs.\n- Pager: 02:14 UTC, SRE lead ack at 02:15 UTC.\n\nTimeline (UTC):\n- 02:12 — initial spike in streaming session errors; error rate rose from baseline 0.3% to 18% in 2 minutes.\n- 02:13 — anomaly alert fires; on-call SRE starts investigation.\n- 02:14 — correlating logs show write stall metrics on streaming proxy (high write queue depth).\n- 02:18 — quick mitigation: rolling restart of streaming-proxy fleet in affected region, partial drop in errors but tail latency persisted.\n- 02:25 — rollback of a recent edge-config change that adjusted connection TTL made at 01:55 UTC. Edge config rollback began.\n- 02:35 — error rates fall to ~2%; tail latency trending down but not fully recovered.\n- 02:55 — full rollback complete and additional throttling rules temporarily applied; streaming success rates returne
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_5f884c5669194d698c0be56a1df92b33`

```
Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling

Issue summary: Starting ~2026-03-13 11:20 UTC, ChatMetrics reported a rising error floor of 5xx responses for streaming requests. The API Gateway returned 502/503 intermittently and a subset of streaming sessions observed immediate fallback to short-polling which then triggered additional gateway throttling and elevated error rates. Impact: Customer-facing degradation for ChatMetrics (dedicated tier) — streaming API errors for ~40% of active sessions, visible increase in token cost due to retries. Environment: prod-us-east, dedicated tenant cluster. Observed with model redwood/text-xt-3b. Steps to reproduce: 1) Initiate ~600 concurrent streaming sessions from a single ChatMetrics vCPU-based client to the /v1/streams endpoint; 2) Hold long-lived streams with occasional small writes (~1-2 tokens every 2s); 3) Observe on the client: intermittent 502/503 during handshake period followed by server-initiated fallback and then 429s after gateway backoff. Recent changes: nightly keystore rotation completed at 11:05 UTC and an autoscaler policy sweep was applied at 11:10 UTC. Logs/metr
…[truncated]
```

#### #2 `dsid_966a7c4df170438c8ce53f99d9f5a12d`

```
In-flight header growth + edge proxy slow-flush causing delayed TTFB and intermittent 502/504 for streaming completions

Issue summary: Customer Langtail Labs reports a sharp rise in streaming request failures and delayed first-byte times starting 2026-03-11 late afternoon. Symptoms include delayed TTFB (10-30s), intermittent 502/504 responses, and client-side timeouts on long completion streams. Impact: production traffic for several endpoints sees ~15% of streaming sessions fail or time out during peak; customer reported user-visible degradation in chat product. Environment: Dedicated tenancy (reserved capacity) fronted by Redwood API gateway -> edge-proxy (nginx-based) -> serving runtime pool in us-east-1.

Observed behavior aligns with header growth (rotating trace/cookie headers and sidecar metadata) increasing request header sizes mid-stream while edge proxy is coalescing small upstream writes, causing proxy buffering and a long pause before the first flush to client. When pause exceeds ALB/edge idle_timeouts, upstream connections are reset and clients receive 502/504.

1) Create a long-running streaming completion request (simulate >20s tokens) using a client that rotates a 
…[truncated]
```

#### #3 `dsid_9cfb4812f31542038a01ee9329290d01`

```
Edge connection-hold flood from long-lived keepalive clients causing 5xx spike and runtime CPU pressure for dedicated tenant

Issue summary:\nDuring the customer tenant's steady-state traffic window (03/12 07:15–08:45 UTC) we observed an abrupt rise in 5xx rates originating at the API gateway layer for BeaconHealth Analytics (dedicated tenant). Error rate climbed from baseline ~0.2% to a peak of 6.3% for their routes and correlated with elevated CPU utilization on several serving-runtime pods pinned to the tenant.\n\nImpact:\n- Multiple customer API routes returned 5xx (predominantly 502/503) for ~90 minutes, affecting live clinical scoring and chat features.\n- Observed increased tail latency and client-visible stream disconnects.\n- Customer reported degraded SLA and raised a high-priority support case.\n\nEnvironment:\n- Dedicated tenant: BeaconHealth Analytics, prod-us-east, routing through edge-proxy cluster ep-us-1\n- API Gateway version: apigw-3.7.1\n- Edge proxy: envoy-1.26-custom\n- Serving runtime image: redwood-runtime:2026-03-05-prod\n\nObserved symptoms / logs:\n- Edge accept-queue length increased prior to error wave: accept_queue_depth ep-us-1 peaked at 11k connectio
…[truncated]
```

#### #4 `dsid_b9e867d7f1614b118214334b9ae82405`

```
Gateway buffer pressure from long-polling sessions causing intermittent 5xx pulses

Issue summary: Starting 2026-03-13 02:10 UTC, AcmeDocs observed intermittent 5xx spikes on several streaming endpoints. Errors manifest as HTTP 502/503 returned by the API Gateway and correlated runtime exits on a subset of ephemeral pods. Impact: Multiple customer processes experienced elevated error rates (~6-12% 5xx) for ~45 minutes; some streaming sessions were dropped mid-conversation. Environment: prod (us-east) - dedicated capacity pool allocated to AcmeDocs. Steps to reproduce: 1) Open >100 concurrent long-polling streaming sessions with keepalive interval ~30s. 2) Send periodic short messages (~20-50 chars) that keep sessions active for >20m. 3) Observe gateway and runtime metrics between 02:05-03:00 UTC. Observed behavior: - API Gateway accept queue and buffer growth (queue length metric spiking) - ingress-sidecar memory buffers increase and file descriptor counts approach soft limits - serving runtime threadpool saturation followed by worker exits (OOM-like memory pressure and SIGABRT on a few nodes) - elevated 502/503 rate at gateway, partial zero-byte responses on some streams Expected 
…[truncated]
```

#### #5 `dsid_08ad719d23bb43e4a66b6e52fa079c0b`

```
Intermittent high TTFB and 504s caused by proxy write stalls when request-metadata headers grow during streaming

Issue summary: Over the last 24 hours Nimbus Analytics is seeing intermittent elevated Time-To-First-Byte (TTFB) spikes and occasional 504 Gateway Timeouts on long streaming completions. Impact: customer-facing endpoints for large chat sessions experience degraded latency and occasional request failures, affecting multiple product customers using the same dedicated tenant. Environment: prod (us-east-1), dedicated capacity, requests traverse the external edge gateway (Envoy-based) -> internal ingress -> serving-runtime. Steps to reproduce: 1) Start a long-running chat completion with multi-turn context and tracing baggage headers enabled. 2) Stream responses back to client for ~60-120s. 3) Observe intermittent periods where bytes stop flowing for ~30-90s and then connection resets with 504 or timeout. Observed behavior: interleaved TTFB spikes, streaming stalls with zero bytes for tens of seconds, followed by 504s. Logs/metrics: edge-proxy write buffer growth correlates with increasing per-request header sizes (baggage/trace metadata), envoy stats show upstream_bytes_buf
…[truncated]
```

#### #6 `dsid_20da692d9b2e4db98d4c410dd70c85b4`

```
Intermittent TTFB regressions for streaming completions when API gateway connection reuse interacts with proxy buffering

Issue summary: Customer reports intermittent increases in time-to-first-byte (TTFB) for streaming completions. The symptom is that some streaming requests return initial tokens after a 2-6s delay even though request enters the serving runtime quickly. Impact: customers see perceived latency spikes for interactive flows and partial timeouts when clients have strict idle time windows. Observed at scale across multiple backends in us-west and reproduceable in limited cases from internal synthetic tests.

Observed behavior:
- Requests accepted by API gateway and routed to serving cluster immediately (backend request logs show sub-200ms queuing).
- First chunk from serving runtime often delayed by multiple seconds before being flushed to client. Subsequent chunks stream normally after first flush.
- When we disable proxy buffering on edge (apigw/nginx) the TTFB returns to expected ~120-300ms range.

Why this is likely: preliminary triage indicates a protocol/conn-reuse mismatch between API gateway (proxy) keepalive behaviour and the serving runtime's chunking strateg
…[truncated]
```

#### #7 `dsid_5dfe1a03b30b4e728de8fa999bdf88dd`

```
Intermittent 5xx spike from delayed HTTP/2 ACKs causing streaming sessions to half-close and upstream restarts

Issue summary: Beginning ~2026-03-13 09:10 UTC GreenLeaf AI observed a sustained elevation in 5xx responses on streaming routes. Error pattern shows many short-lived streaming sessions ending with upstream connection resets or 502/503 responses. Impact: customer is seeing ~18% failed requests on high-concurrency streaming workloads (conversational chat) leading to degraded UX and increased retry traffic. Environment: prod us-east tenant on Dedicated pool (pool-id d-12).
1) Send concurrent streaming chat requests (50 concurrent streams) against /v1/stream with model=gptx-13b using their websocket-based SDK
2) Maintain each stream with small intermittent client-side pings (keepalive every 10s) for ~30s
3) Observe occasional immediate 502 response from API gateway, or stream resets with HTTP/2 RST_STREAM codes
4) Reproduce more reliably during tenant burst (~>80% of provisioned concurrency)
[apigw-2026-03-13T09:12:21Z] route=/v1/stream tenant=d-12 upstream=10.2.5.83:8443 status=502 msg=upstream_reset reason=half_closed_ack_delay
[runtime-2026-03-13T09:12:21Z] pid=23914 SIGCH
…[truncated]
```

#### #8 `dsid_73bbb963f3f04ef09e110be84f50d1e1`

```
HPACK header-table mismatch in edge proxy causing intermittent 5xx for long-lived streaming sessions

Issue summary: Since the edge-proxy (Envoy) config bump deployed 2026-03-09 03:12 UTC, BrightChat is reporting intermittent 5xx errors for long-lived streaming sessions. Impact: customer streaming sessions receive 502/503 spikes and some requests terminate mid-stream. Scope: affects a subset of long-poll/streaming traffic for the BrightChat tenant in us-west; other tenants show lower symptoms but heavier streaming load correlates with error rate. Expected: streaming sessions should remain stable under normal concurrency. Observed: sudden uptick in 5xx (502/503) during long sessions; runtime containers show watchdog restarts in the same window. Initial hypothesis: header decoding errors between edge-proxy and backend are causing upstream request terminations and cascading retries.
1) Use BrightChat tenant config and open >150 concurrent streaming sessions to redwood-1-large in us-west
2) Send long prompts (~20k chars total across streaming tokens) and keep connections open >60s
3) Observe that a fraction (~3-8%) of streams fail with 502/503 within 10-40s
4) Check edge-proxy logs for
…[truncated]
```

#### #9 `dsid_6e0a74dab08c4a1ab3d31ae2752e668b`

```
Edge proxy connection stall from slow chunked uploads and header growth causing delayed TTFB for long completions

Issue summary: Starting 2026-03-10 08:10 UTC, Acme Payments reported intermittent large increases in TTFB (time-to-first-byte) for streaming completions >60s. The pattern is correlated with clients that upload request bodies slowly (chunked transfer) while also sending periodic trace/authorization header updates. Impact: Customer-facing inference calls return with long stalls before streaming begins; some requests trigger ALB/edge connection resets and 504s. Environment: prod-us-east-1, traffic through our public API Gateway -> edge proxy layer -> internal ALB -> serving runtime. Observed behavior: When the client uploads body slowly (multi-second pauses between chunks) and repeatedly sends header updates, the edge proxy's HPACK table grows and proxy buffering increases, triggering idle-send-timeouts or partial flush behavior. Expected behavior: Streaming should begin when the server has the initial request payload and upstream should not stall due to header accumulation or slow chunked uploads. Additional notes: This looks related to previous header-growth/idle-timeou
…[truncated]
```

#### #10 `dsid_1e20852dbc9d4a9192a7b8a393f65133`

```
502/503 surge at edge during short-lived streaming bursts causing elevated error rate for dedicated customer

Issue summary: Between 2026-03-10 11:10-11:45 UTC KiteBank reported a spike of 502/503 responses from the Redwood API for short-lived streaming sessions. Impact: ~12% of requests (per their telemetry) returned 5xx; request volume for the customer returned to normal but error rate persisted during short streaming bursts. Customer impact: user-facing failures in KiteBank's chat flows during a scheduled load test; revenue-impacting for production flows.

Timeline:
- 2026-03-10 11:08 UTC: KiteBank begins automated short-lived streaming burst (hundreds of concurrent connections, each streaming ~3-10s then close).
- 2026-03-10 11:12 UTC: Alerts triggered for elevated 5xx rate from apigw routing to us-east.
- 2026-03-10 11:25 UTC: Support ingested customer logs and asked for correlation IDs; SRE observed proxy connection churn and runtime proxy logs showing TLS session errors.
- 2026-03-10 11:40 UTC: Temporary mitigation applied (connection_limit increase and short keepalive tuning). Client-side retry backoff recommended.
- 2026-03-12 10:00 UTC: Root cause patch rolled to edge-pro
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 59: `qst_0423::conflicting_info` · N=100000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not match any of the expected document IDs, indicating a lexical mismatch. The retrieved chunks are relevant to audit and log export topics but do not specifically address the question about the office keycard audit. The hit@10 flag is incorrectly set to false, as no expected document IDs are present in the top 10 retrieved IDs. The gold chunks are relevant and non-empty, while the retrieved chunks are on-topic but not directly relevant to the specific question.

### Question

For the office keycard audit, how many months of access logs should we export?

### Gold document(s)

#### GOLD `dsid_03b2db544a6d4cf886fb9869058a05f2`

```
Office inventory + keycard audit + disposal request (storage shelves + access system cleanup)

Request type: Internal support / facilities + security coordination

Background
Office moved desks last quarter; storage now contains untagged peripherals, old keycards, and leftover badge holders. This ticket consolidates the remaining cleanup work so we can reconcile inventory, tidy shared spaces, and reduce risk from stray credentials.

Scope / Goals
- Produce a concise inventory of unassigned equipment (monitors, keyboards, spare GPU boxes, dongles)
- Audit and deactivate lost/old keycards in the access system and return/re-enroll active ones
- Clean and label community storage shelves and identify disposal candidates for Facilities pickup

Updates vs earlier plan
- Security requested we export access logs for the last 12 months (not 18) for the initial cross-check; they will expand the window only if anomalies are found.
- Anything that could contain data-bearing media (NVMe/SSDs/USBs) must be separated into a "Security review" bin and cannot go directly to e-waste.
- Facilities asked that disposal candidates be grouped into: e-waste, donation, recycle, landfill, and "needs approval".

Acceptance criteria
- CSV inventory uploaded to Drive with columns: item_id, type, location, status, owner_hint, notes
- Keycards deactivated or reassigned; list of card IDs with current status documented (include reason: lost, terminated, replaced, active)
- Disposal list handed to Facilities with approval note and the category breakdown

Planned steps
1) Quick sweep team (1-2 eng volunteers + Facilities) to inventory storage (target: 1 day on-site)
2) Collate CSV + apply physical tags/labels to boxes/shelves (target: 0.5-1 day)
3) Keycard audit with Security (Omar to coordinate) (target: 1-2 days, mostly admin work)
4) Disposal / reallocation decisions + update asset tracker (target: 0.5-1 day)

Notes / investigation log (messy)
- Found box labeled "quantization-experiments-2019" that may contain an older NVMe; moved to Security review bin (do not e-waste yet).
- Some badge IDs show up in access logs in 2024 despite being physically in lost-and-found; need cross-check against HR t
…[truncated]
```

#### GOLD `dsid_c5288dd4874345adb80f4a71c9a18773`

```
misc-chores-office-inventory-and-keycard-cleanup

Background: Office moved desks last quarter; several untagged peripherals, old keycards, and leftover badge holders in storage. This ticket collects misc chores to reconcile inventory and tidy shared spaces.

Goals:
- Produce a concise inventory of unassigned equipment (monitors, keyboards, spare GPUs boxes, dongles)
- Audit and deactivate lost/old keycards in the access system and return/reenroll active ones
- Clean and label community storage shelves and mark disposal candidates

Acceptance criteria:
- CSV inventory uploaded to Drive with columns: item_id, type, location, status, owner_hint
- Keycards deactivated or reassigned; list of card IDs with status documented
- Disposal list handed to Facilities with approval note

Notes / messy log:
- Found box labeled "quantization-experiments-2019" that might contain ancient NVMe; hold for review before E-waste.
- Some badge IDs appear in the access logs for 2024 despite being in the lost-and-found — need cross-check (security notified).
- Short timeline requested by Facilities: prefer completion before holiday break.

Planned steps:
1) Quick sweep team (1-2 engs + facilities) to inventory storage (2 days)
2) Collate CSV, tag physically (labels on boxes) (1 day)
3) Keycard audit with security (Omar to coordinate) (2 days)
4) Disposal / reallocation decisions and update asset tracker (1 day)

This ticket is intentionally lightweight and is a catch-all for small physical tasks that don't merit a formal facilities request. If any item is sensitive (hard drives, HSM parts, private compute media) escalate to security and open a separate INT ticket.
2025-11-10 - Maya Chen: Created initial ticket after impromptu storage sweep. I'll coordinate volunteers.
2025-11-11 - Omar Singh: Reached out to Security about keycard audit; they suggested exporting access logs for the last 18 months.
2025-11-12 - Facilities Bot: Tentative sweep scheduled 2025-11-18 10:00 in 3A storage room. RSVP required.
```

### Retrieved top-10

#### #1 `dsid_a7e036d237404f23991aaef36997406f`

```
eng-security

Maya Chen: Quick Q — compliance needs an ad-hoc dump of admin actions for last quarter. Can someone confirm what fields are in the audit export (CSV/Parquet)? Need actor identifier, email, action, resource, and IP if available. Also what's the retention window and who can run these exports? :eyes:
Cory Patel: We have exports in Parquet and CSV. Default schema includes actor_id, actor_email (if not redacted), action, resource_type, resource_id, ts, request_id, region, and a freeform meta JSON. IP addresses are considered PII and are stripped by default unless approved.
Alex P: To add: exports land in s3://redwood-audit-exports/<org>/<date>/ and we produce a single .zip per request. Parquet is preferred for large datasets; CSV is available for tiny slices or quick eyeballs.
Maya Chen: Good — who needs to sign off on including IPs? Compliance is asking for IPs to support a legal review.
Cory Patel: Inclusion of IPs requires Security + Legal approval (two-person sign-off). Process: open the "Audit Export Approval" Jira template, attach justification and timeframe. See internal docs: <https://redwood.internal/docs/audit-exports> :lock:
Sara Li: FWIW support used the ad-hoc
…[truncated]
```

#### #2 `dsid_dea9de3e5e904e4aa4e173e254e785c7`

```
Audit & access log TTLs, export formats, and customer-driven deletion walkthrough

From: Raj Patel <raj.patel@medicorps.com>\nTo: Monica Patel <monica.patel@redwood.ai>\nCc: MediCorps Legal <legal@medicorps.com>\nDate: Wed, 21 Jun 2028 09:12:00 -0700\nSubject: Log retention/export questions for upcoming audit\n\nHi Monica,\n\nWe have an external audit starting next month and the auditors have asked for a slice of access and audit logs for specific user activity windows (two 30-day windows spread across the past 12 months). We need:\n- Exact retention windows for audit vs access logs (where \"access\" is auth and token events and \"audit\" is admin/role changes + tenant-level actions)\n- Export formats you can provide (CSV, JSON, syslog stream?) and whether exports contain full raw events or are filtered/sanitized by default\n- A short walk-through on how MediCorps can trigger exports and request deletions for specific customer data (GDPR/e-Discovery style) — auditors want an outline we can include in evidence.\n\nCan you also tell us whether exports include IP addresses and whether those are redacted depending on region?\n\nThanks,\nRaj\nHead of Infrastructure, MediCorps\n
From: Mo
…[truncated]
```

#### #3 `dsid_33b8ef3fa0134aec892debb7dcaae434`

```
Bulk audit log delivery and security assertions for upcoming vendor audit (SIEM ingestion + AUP attestation)

Issue summary:
Customer BrightLedger is undergoing a third-party vendor security audit in two weeks and requested: (1) a full export of account-level audit events for calendar year 2025, (2) SIEM-compatible delivery (Splunk CEF or NDJSON with timestamp + sig fields), and (3) signed evidence for control assertions (AUP acceptance confirmation, KMS usage for log encryption, and log retention/immutability statements). Impact: audit deadline is 2026-03-24. Customer requires chain-of-custody metadata and statement of retention policy.

Environment / scope:
- Customer account: brightledger-prod-001
- Region: us-east-1
- Time range: 2025-01-01 to 2025-12-31 UTC
- Record types requested: API request/response events, token usage metadata (anonymized IDs), auth events (login, token create/revoke), model-inference start/stop events, audit config changes, and SIEM-relevant metadata (user_agent, src_ip when available).

Requested output/format options (customer preference):
1) NDJSON, one event per line, ISO8601 timestamp in top-level field "@timestamp", fields: event_type, user_id (has
…[truncated]
```

#### #4 `dsid_a7cdd5969e4043c68b02f1b8ed6a4487`

```
eng-security

auditor_lee: Hi team - need SOC2/ISO evidence for private inference enclave (VPC + KMS) over last 12 months: RBAC change history, KMS Decrypt/GenerateDataKey logs, key rotation proof, and incident correlations. ETA?

carla(sec): We can supply: (1) RBAC change CSV from k8s + IAM snapshots, (2) CloudTrail extracts filtered for KMS Decrypt/GenerateDataKey, (3) KMS DescribeKey rotation statuses and rotation logs, (4) incident correlation table linking RBAC changes to IR tickets.

marta(devops): Auditor: full 12 months preferred? Sampling with exact criteria + full incident windows ok.

auditor_lee: Full 12 months preferred. If sampling, must include methodology and full windows for incidents.

rahul(dev): k8s audit example query: 
```
index=k8s_audit "RoleBinding" OR "ClusterRoleBinding" | fields user, verb, objectRef.name, @timestamp
```
I'll produce CSV with before/after state where available.

ops_tess: KMS pipeline: CloudTrail -> S3. Athena snippet to pull Decrypts: 
```sql
SELECT eventTime, userIdentity.arn, eventName, requestParameters.keyId FROM cloudtrail_logs WHERE eventName IN ('Decrypt','GenerateDataKey') AND eventTime >= '2025-03-01';
```
We will export gzippe
…[truncated]
```

#### #5 `dsid_abef073a060547cc9d242425f89be3e2`

```
Access authority request: timeboxed prod log segment for external privacy assessor

Issue summary: External privacy assessment firm (PrivAudit LLC) has requested a scoped sample of production ingestion logs to verify PII minimization and retention profiles. Request includes a 48-hour contiguous segment of API gateway access logs plus associated audit metadata (no raw inference outputs).

Impact: Minimal service impact expected. High compliance risk if access is not authorized correctly or if sensitive customer data is exposed. Customer-facing incidents could result if accidental raw inference output is included.

Request details:
- Requestor: PrivAudit LLC (contract attached to Security ticket SEC-2026-037)
- Data requested: API gateway access logs and associated audit fields (timestamps, request IDs, route, headers summary hash, auth subject) for window 2026-02-10T00:00:00Z to 2026-02-11T00:00:00Z. Explicitly exclude request/response bodies and any unredacted inference outputs.
- Purpose: external verification of anonymization and retention workflows.
- Duration: Access window 72 hours from token issuance. Token must expire automatically and access must be read-only.
- Delivery me
…[truncated]
```

#### #6 `dsid_67677fea63eb416b9f2023f09d329302`

```
Orion Compliance Networks

Customer requires structured, machine-readable audit logs for every inference request and system event. Logs must be exportable to their Splunk instance in near real-time, optionally via syslog/TCP forwarder or batched S3 export. Logs cannot contain unredacted PII; sensitive fields must be hashed or redacted before export. KMS-managed encryption of logs at-rest and envelope encryption on the log forwarding path required. Retention policy is regulatory: 2 years for event-level telemetry, 7 years for auth/access logs. All fallback and routing decisions must be recorded with unique request IDs for traceability.
Enterprise IT + SecOps heavily involved — CFO also looped for retention cost tradeoffs.
Primary ask: VPC private deployment with full audit trail exported to customer SIEM (Splunk).
"They want schema before legal signs off" — security manager (E. Lawson) on 03/12.
Preference: syslog/TCP forwarder or S3 sink (parquet/json) — must support Fluentd/Logstash ingestion.
Retention expectation: 2 years for event logs, 7 years for access/auth events (banking regs), legal will push).
Must not log PII in plaintext — redaction hooks + token-level masking; KMS env
…[truncated]
```

#### #7 `dsid_ae3841f2fcc84484bdcb89dcdb66874e`

```
Customer session export + compliance SOP for third-party audit request

Issue summary:
Customer (Acme Retail, enterprise) has requested a targeted export of session logs and associated request/response payloads for a pending third-party security audit. They specifically asked for sessions touching a set of customer IDs and date range (2026-02-20 through 2026-03-05).

Impact:
Potential exposure of customer-identifying fields if redaction is incomplete. Request requires coordination across SRE (log extraction), Security (KMS & key access), and Legal/Compliance (contract & audit scope). Time-sensitive due to audit window; customer flagged as enterprise SLA.

Requested deliverables:
- Extract full request+response records for session IDs provided by customer or for the specified date range and customer IDs.
- Provide redaction metadata and confirmation of PII removal (or fields retained with justification).
- Delivery method: secure SFTP to customer-managed location OR temporary signed URL with strict expiry; Legal prefers SFTP to their auditor account.
- Audit trail: who accessed, query filters used, and KMS key IDs used to decrypt artifacts.

Why this is tricky:
- Production logs liv
…[truncated]
```

#### #8 `dsid_fafcd864f11843a28182c451fe0e5a61`

```
customer-success

Maya (CSM): Heads up — ACME's security questionnaire (bespoke SIG subset) flagged two items: audit-log retention longer than 90 days and evidence of KMS rotation + HSM usage. They asked for packaged evidence + a short remediation plan by Fri EOD. Can we pull exports and a one-paragraph response?
Jon (Security Eng): Which specific SIG question IDs? CAIQ or bespoke fields?
Maya (CSM): They pasted this in the form: ```Q: Provide evidence that customer-facing audit logs are retained >= 90 days and include KMS rotation history and HSM keywrap attestations. Provide export and description of controls that would remediate any gap.```
Jon (Security Eng): OK. Our default audit log retention is 30 days for infra logs and 365 days for CloudTrail/immutable event logs. Need clarity on what they mean by "customer-facing audit logs" — is this API request logs or infra-level traces?
Maya (CSM): The questionnaire references request-level audit trail for customer data access (API request + auth events). ACME wants an export covering the last 180 days.
Liu (Legal): If they want 180 days and we only retain 30 for that dataset, we need a documented retention exception + approval. Ask A
…[truncated]
```

#### #9 `dsid_2f6f2eb442c9423993d657259b4fcee3`

```
Prod API-key usage trace provisioning request for regulatory billing review

Request summary:
Support has received a request from Finance/Compliance to run a correlated usage trace for one customer billing period (2026-02-01 to 2026-02-28) to validate API-key attribution across service boundaries. The goal is to reconcile billed tokens against ingress events when the customer asserts duplicate key usage from an internal integration.

Justification:
- Customer dispute escalated to Finance and Legal; compliance requires the ability to show the chain of custody for API-key based requests.
- Data needed is limited to metadata (timestamp, route, API key id, account id, request_id, responding model, token_count) and request hashes — not full request/response payloads.

Data scope and exclusions:
- Include: api_key_id, request_id, ingress_timestamp, route, model_served, token_count, response_status, upstream_ip (hashed), load-balancer request id.
- Exclude: full_request_payload, response_body, any free-text user content; do not include KV cache contents or raw output text.

Requested access window and retention:
- One-time extract for timeframe 2026-02-01 through 2026-02-28.
- Retention: 
…[truncated]
```

#### #10 `dsid_325127fefd874655adaeb228f5353682`

```
Forensic playback export, chain-of-custody manifest and HSM key-rotation attestation for eDiscovery

Issue summary: First Meridian Bank legal team requests a timebounded, tamper-evident forensic export and playback package to satisfy an eDiscovery subpoena covering 2026-01-15 to 2026-01-22. They require chain-of-custody proof, HSM key-rotation attestations for the KMS keys used to sign manifests, and a sampling of raw events mapped back to customer user identifiers.

Impact: High — the export is required by the customer's legal hold with a court deadline. Customer cannot proceed without evidence of immutability and key custody.

Environment: Production (us-east tenant scoped).

Requested deliverables: 1) A resumeable forensic export (S3 presigned package) of ordered audit events for the date range, including raw event JSON and the internal redaction/pseudonymization map. 2) A signed chain-of-custody manifest (RFC-style) with per-file SHA256 checksums and an ed25519 signature. 3) HSM-backed KMS key-rotation audit (rotation events, attestations, and certs) that show key versions active during the range. 4) A small sample (100 events) translated to customer identity mapping for valida
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 60: `qst_0444::completeness` · N=10000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`lexical_mismatch`
- **LLM note:** The retrieved document IDs do not match any of the expected document IDs, resulting in a Hit@10=False. The retrieved chunks are off-topic, focusing on sales briefs and technical playbooks rather than the internal process for launching a new LLM. The gold chunks are relevant and detailed, but the retrieval failed to capture any relevant documents, indicating a lexical mismatch. The hit flag is incorrectly set to true, causing a mismatch.

### Question

What is Redwood Inference's end-to-end internal process for launching a new third-party LLM into the Hosted API model catalog-from intake to post-launch monitoring-including every required gate, owner, and artifact?

### Gold document(s)

#### GOLD `dsid_117e5a150aa94adc86295786bd6b7843`

```
Hosted API model intake: third-party LLM onboarding request

# Purpose
This page describes the *intake* process for launching a new third‑party LLM in the Redwood Hosted API model catalog. It defines what the requester must provide, who owns each step, and what artifacts are required before engineering work starts.

# When to use
Use this process for any new entry in the Hosted API model catalog, including:
- New upstream model families (e.g., Llama, Qwen, Mistral)
- New sizes or instruction variants
- New upstream releases that change tokenizer, weights, or license

# Roles
- Requester: typically Product or Solutions Engineering
- Intake owner: Applied ML Onboarding (Applied ML)
- Runtime owner: Serving Runtime
- Release owner: Release Engineering
- Security gate owner: Security & Compliance
- Docs owner: DevEx / Docs

# Intake ticket and required fields
Create a Linear ticket in *ENG* with label `model-onboarding` and include the following fields (copy/paste section):

## 1) Model identity
- Upstream model name and version tag
- Model type: `chat` | `completion` | `embeddings` | `rerank`
- Upstream repo / source URL
- Tokenizer type and expected special tokens

## 2) Intended catalog surface
- Proposed Redwood model ID (e.g., `rw/llama-3.1-70b-instruct`)
- Compatibility target: `redwood` native | OpenAI-compatible endpoint
- Any planned aliases (e.g., `rw/llama-3.1-70b`)

## 3) License and redistribution
- License name + link to full text
- Redistributable weights: yes/no/unclear
- Any use restrictions that must be enforced in ToS / UI (e.g., geo, user class)

## 4) Data and policy
- Safety/policy concerns (e.g., uncensored, adult content)
- Any known PII or training data controversies (link sources)

## 5) Target customers and workload
- Example customer workloads (prompt length distribution, expected max tokens)
- Regions required (US/EU/APAC)
- Any explicit SLO expectations (latency, availability, streaming)

# Intake gates (must all be satisfied to proceed)
1. **License pre-check** (Owner: Finance-Legal liaison + Security)
   - Outcome: `approved`, `approved w/ restrictions`, or `blocked`
   - Artifact: link to Security risk review page entry (see Security
…[truncated]
```

#### GOLD `dsid_2ad75f27c36b492f847d5b9c63492e4b`

```
Hosted model rollout and fallback runbook

# Overview
This runbook describes the standard procedure to roll out a new model to the Hosted API catalog and configure safe fallback/rollback. It is written for Release Engineering, Platform, and on-call responders.

# Preconditions (must be true before rollout)
- Model intake ticket exists and is in `ready-for-rollout` status.
- Applied ML has provided eval gates pass results and a one-paragraph risk assessment.
- Serving Runtime has signed off the performance bar results for the default profile.
- Security has approved the third-party model risk review (or an exception is linked).

# Roles
- Rollout owner: Release Engineering
- Routing change owner: Platform
- On-call: Eng Oncall (runtime + platform)

# Required artifacts
- GitHub PR in `redwood-model-registry` adding the model and quant profiles
- Perf suite run IDs (default profile)
- Eval harness run links (Suites A + any tool-calling suite)
- Security risk review link + any restriction text that must appear in docs

# Step-by-step rollout procedure
## 1) Create the catalog entry (registry PR)
- Ensure the PR includes:
  - Model ID, version, tokenizer identifier
  - Allowed context lengths
  - Supported features (streaming, structured output, tool calling)
  - Quant profiles and default profile
  - Artifact hashes/provenance notes
- Merge only after required approvals are present.

## 2) Deploy behind feature flag (dark launch)
- Add a routing rule in `router-policy` with state `disabled` and scope `internal`.
- Deploy config to staging and run smoke tests:
  - `/v1/chat/completions` streaming
  - basic JSON schema output
  - max-context request (ensure clean error message on overflow)

## 3) Canary to production
- Enable routing for 0.5% of traffic on one region (us-east-1) for 3060 minutes.
- Monitor dashboards:
  - `hosted_inference_latency` (TTFT p95)
  - `hosted_inference_errors` (5xx, timeouts)
  - `gpu_oom_events`
  - `quality_regression_alerts` (if shadowing enabled)
- If error rate > 0.5% or TTFT p95 breaches the SLO for 10 minutes, abort canary and rollback (see section below).

## 4) Expand rollout
- Increase to 5% in us-east-1, then add eu-west-1, the
…[truncated]
```

#### GOLD `dsid_40471ba4cd3b430eab3ac0877eef0972`

```
Third-party model risk review workflow (Hosted API)

# Purpose
This page defines the security and compliance review required before Redwood can ship a third-party model in the Hosted API catalog.

# Scope
Applies to any new upstream weights/tokenizer/artifacts that Redwood will host or make available via the Hosted API.

# Review owner
- Security & Compliance (Risk & Exceptions)

# Inputs required from requester
Provide in the model intake ticket:
- Upstream source (repo URL, commit/tag, download location)
- License and redistribution terms
- Known upstream maintainers and any vendor relationship
- Any customer constraints (data residency, regulated workloads)

# Required checks (all must be completed)
## 1) Artifact provenance and integrity
- Verify checksums for downloaded artifacts
- Record the exact upstream tag/commit and file hashes
- Store hashes in the model registry change description

## 2) Supply chain scanning
- Scan container images and build environment used for conversion/quantization
- Run malware scan on downloaded archives
- If a conversion script is used, it must come from an approved repo or be reviewed

## 3) License and acceptable use
- Confirm redistribution rights for hosted serving
- Document any restrictions we must enforce in docs and/or API terms
- If restrictions exist, Product must confirm how we communicate them

## 4) Privacy and data handling
- Confirm no customer data is embedded in the model artifact pipeline
- Confirm retention and access controls for internal artifacts (weights, logs)

## 5) Abuse and policy alignment
- Ensure model can be placed behind Redwood policy layer
- If model is known to be high-risk, require a Product signoff and a staged rollout

# Outputs (artifacts)
- A risk review entry summarizing: risks, mitigations, restrictions, and decision
- Decision must be one of: `approved`, `approved-with-restrictions`, `blocked`
- If `approved-with-restrictions`, include the exact restriction text to appear in docs

# Exception workflow
- Exceptions (e.g., unclear provenance, incomplete upstream docs) require a Security exception record and VP Engineering approval.
- Link the exception record in the Linear model intak
…[truncated]
```

#### GOLD `dsid_5cde26f232454906879617dab1800fae`

```
Model launch evaluation gates (Hosted API catalog)

# Overview
This page defines the required evaluation gates for launching a new model into the Hosted API model catalog. The goal is to ensure we can safely serve the model, meet product quality expectations, and detect regressions after launch.

# Ownership and signoff
- Gate owner (quality): Applied ML (Onboarding + Evals)
- Required signoff: Applied ML + Product (for model positioning)
- Optional signoff: Customer Success (if a launch is for a named account)

# Required evaluation suites
All Hosted API catalog launches must pass *all* suites below. Each suite must be run on the candidate model build (exact weights + tokenizer + runtime config) and logged in the eval harness.

## Suite A: Internal prompt set regression
- Source: `prompt-sets/hosted-api/core-regression`
- Metrics: win-rate vs current default in family; structured output adherence for required schemas
- Pass criteria:
  - Overall win-rate >= 50% vs baseline (no regression)
  - Any critical prompt tagged `p0` must not regress
- Artifact: eval harness run link + summary paragraph

## Suite B: Public benchmark sanity
- Source: curated public tasks (e.g., MMLU subset, GSM8K subset, HumanEval-lite)
- Purpose: catch obvious misconfigs, broken tokenizer, prompt formatting issues
- Pass criteria:
  - No single task drops > 5% absolute vs upstream reported numbers *after adjusting for our settings*
  - If upstream numbers are unavailable, compare vs adjacent model sizes in family and explain outliers
- Artifact: table of scores + notes

## Suite C: Safety and policy screening (lightweight)
- Source: policy prompts + refusal behavior checks
- Pass criteria:
  - No increase in disallowed content generation on policy set
  - Refusal templates must be compatible with Redwood policy layer
- Artifact: pass/fail summary + any required policy config notes

## Suite D: Tool/function calling compatibility (if applicable)
- Required when the model is marketed for tools/function calling
- Pass criteria:
  - JSON schema conformance >= 99% on tool-calling prompt set
- Artifact: schema validation report link

# Required documentation artifacts
A launch packet must incl
…[truncated]
```

#### GOLD `dsid_92d0d471ddc941288bcb51b3ded6ec36`

```
Hosted model performance bar (catalog launch requirements)

# Summary
This standard defines the minimum performance and reliability bar a model must meet before it can be launched in the Hosted API catalog.

# Scope
Applies to: chat/completions models offered in the Hosted API, including OpenAI-compatible routes.
Does not apply to: one-off customer private builds (see Private Deployments standards).

# Owners
- Standard owner: Serving Runtime
- Enforcement: Release Engineering + SRE

# Benchmark methodology (required)
Run the perf suite using the current `perf-canary` harness with:
- Hardware class: `H100-80GB` (default) and one secondary class (e.g., `L40S`) when we expect meaningful traffic
- Context sizes: 2k, 8k, 16k
- Workload: mix of prompt lengths matching the top-10 Hosted API routes
- Concurrency: 1, 8, 32
- Streaming: on (default)

Required artifacts:
- Benchmark run IDs (perf suite output)
- Raw logs attached to the Confluence page or linked from Drive
- Summary table (p50/p95 TTFT and tokens/sec)

# Minimum bar for launch
A model can launch if all of the following are true for the *candidate default config*:

## Latency
- TTFT p50 <= 1.2s (2k context)
- TTFT p95 <= 2.5s (2k context)
- TTFT p95 <= 4.0s (8k context)

## Throughput
- Sustained output tokens/sec per GPU >= family baseline minus 10%
- Continuous batching must remain enabled; if disabling is required, document why and get Runtime signoff

## Stability
- No crash loops under 32 concurrency soak test (30 minutes)
- Error rate <= 0.2% for 2k and 8k tests
- No memory growth trend over soak (KV cache leak check)

# Launch decision and signoff
Required signoffs (recorded as links/comments on the model intake Linear ticket):
- Serving Runtime: performance/stability signoff
- SRE: capacity + readiness signoff
- Release Engineering: rollout plan present (see Platform runbook)

# If the model fails the bar
- If TTFT is the only failure and a smaller default max_tokens solves it, you may propose adjusted defaults, but must re-run suites.
- If throughput is low, evaluate quantization profiles and kernel flags; do not ship a degraded model without a Product signoff and a documented note in docs.

# Rel
…[truncated]
```

#### GOLD `dsid_d8d194e311b9482cb38c61134b6d26fa`

```
(chunk text not in verification bundle)
```

### Retrieved top-10

#### #1 `dsid_d705b886ca6c4aa9854dc193043a3963`

```
Inference Platform Sales Brief — Developer & Enterprise Messaging

Purpose
Provide a single, sharable sales brief that the field can use for pre-sales conversations with engineering and platform stakeholders. The document bundles messaging, key competitive differentials, sample pricing guidance, a short customer case example, a pilot offer, objection-handling, and a concise security FAQ for prospects.

1) One-line positioning
Redwood Inference: a developer-first inference platform that delivers predictable latency, measurable unit economics, and a single operational surface across hosted, dedicated, and private deployments.

2) Core value pillars (talking points)
- Performance certainty: predictable p50/p95/p99 tail latency profiles and autoscaling that keeps production SLAs intact.
- Cost controls: batching, KV/prefix caching, and quantization profiles tuned for workload tradeoffs to reduce per-token costs.
- Deployment flexibility: same API/ops experience across Hosted API, Dedicated capacity, and Private (VPC/on‑prem) for regulated workloads.
- Reliability & fallbacks: automatic model-variant fallbacks, regional routing, and transparent degraded-mode behaviors.
- Observability: 
…[truncated]
```

#### #2 `dsid_7715a1d6ffa047389f4ea1bf862bb9ff`

```
Lodehaven RerankWorks

Mid-market KB search vendor evaluating Redwood hosted API for embeddings + reranking POC. High QPS target; needs SSO + audit logs; wants pricing to justify migration from current managed vector DB.
Overview:
- Lodehaven builds a SaaS knowledge base for mid-market B2B apps (customer help centers + internal KB).
- POC focused on embeddings + reranking pipeline; they want to reduce misranked responses on edge cases.
Scale & perf targets:
- Indexing scope: ~2.5M docs (help articles, KB pages, attachments) ~12M embedding vectors after chunking.
- Query profile: bursty but sustained high QPS target: 400-600 QPS peak, 250-350 sustained QPS expected.
- Latency goal: p95 end-to-end < 150ms for top-5 rerank path (ANN + reranker). Cost sensitivity: looking to halve current per-query cost.
Current stack / baseline:
- Using vendor X (managed vector DB) + self-hosted reranker; baseline POC: 120 QPS, p95 ~220ms, cost ~$0.045/query.
Why Redwood evaluation:
- Interested in hosted API to remove vector infra ops; like Redwood's unified routing and prefix/KV caching.
- Needs intelligent batching suggestions, quantization guidance to hit cost SLOs.
- Want built-in fallback models
…[truncated]
```

#### #3 `dsid_c7cff0205a3844bb90782190a42a390b`

```
VouchLaw Digital LLC

Inbound self-serve signup from product lead (Maya K.). Early discovery call 2026-03-03.
- Primary: SMB legal platform for small law firms; handles client contracts + discovery.
- They spun up hosted API keys and ran basic embedding tests against a 50k doc corpus. Positive on retrieval relevance.
- Main concerns: confidentiality of client documents, audit logging (who accessed what & when), and explicit statement that Redwood won't use customer data to train models.
- Quote from call: "We need ironclad audit trails and US-only residency — our clients will not accept data leaving US controls."
- Cost sensitivity: pref to start with low-rate embeddings + occasional chat; want predictable per-month spend cap.
- Latency/throughput: target median latency <400ms for chat; embeddings batch throughput ~5-10 reqs/sec; not high throughput initially.
- Model preference: open to small Llama variants for cheaper fallback; want Redwood model catalog guidance.
- Admin needs: SSO for console, admin audit logs, API key rotation guidance.
- Legal asked for DPA + SOC2 reference; they handle regulated client records (non-health).
- Action items: share Hosted API security FAQ, samp
…[truncated]
```

#### #4 `dsid_713b7766c60948e7b9b30bfc3008df4d`

```
Channel Partner Win Playbook: Technical Value, Pricing & Security Matrix

Summary:
This playbook is intended for channel and strategic partners (ISVs, systems integrators, and resellers) who are evaluating or co-selling Redwood Inference with their customers. It provides crisp positioning, a compact competitive comparison, a technical integration checklist, partner-friendly pricing scenarios for pilots and proofs-of-concept (PoCs), and a security & compliance FAQ tailored to partner conversations.

Use cases targeted:
- Embedded chat and summarization inside SaaS products (low-latency interactive path)
- High-throughput batch embeddings for search and recommendation systems
- Regulated verticals (finance, healthcare) using Private/VPC deployments

Top-level positioning (elevator + extended):
- Elevator (30s): Redwood Inference delivers predictable, low-latency LLM serving across hosted, dedicated, and private deployments so your product team can embed AI features without trading off cost or reliability.
- Extended (90s): Unlike single-mode LLM vendors or raw infra providers, Redwood unifies runtime optimizations (KV-caching, continuous batching, quantization profiles) with operatio
…[truncated]
```

#### #5 `dsid_69e0d85cdd4443b8b38f285dd39bf940`

```
Lighthouse Archive Search

Summary: Lighthouse Archive Search indexing legacy legal documents + client contracts (~120M docs). Primary focus: replace current embeddings store and introduce learned reranker to improve precision@k while keeping median retrieval latency <120ms at 95thpct. Cost sensitivity: strict constraint on cost-per-query (target < $0.06/query with batching + cache).

Key technical constraints / asks:
- Index size: ~120M docs; average doc vector 1536 dims, many short docs (clauses) -> expect heavy index IO and storage.
- Latency targets: 50ms median retrieval, 95th pct < 120ms for simple retrieval; rerank step budgeted ~60-120ms depending on model; end-to-end RAG latency target < 300ms for support workflows.
- Migration plan: offline evals comparing current embeddings (in-house SBERT variant) vs candidate open/embed models; reranker A/B between LightRerank v1 (current) and proposed cross-encoder. Evals include automatic metrics (nDCG, MRR, precision@1/5) + human side-by-side relevance judgments (legal SME panel).
- Rollout requirements: canary by customer segment, AB testing with traffic steering, automatic rollback on quality regression (eval-driven). Need Redwood
…[truncated]
```

#### #6 `dsid_58da53c74d2d4dbab0f19661d4f8eda3`

```
QueryHarbor KB Solutions

Customer: QueryHarbor builds a hosted SaaS knowledge base used by ~400 enterprise customers (ticketing + KB + chat).
Primary problem: search quality degrades as index grows; current solution returns noisy results at scale -> heavy manual tuning and high MTTR.
Indexing footprint: ~1.2M docs (help articles + transcripts + policy pages), average doc length ~420 tokens, expect growth 30%/yr.
QPS profile: peak 1,200 qps (query layer), steady-state 400-600 qps — they want hosted API to sustain high QPS with p95 <200ms for retrieval + rerank path.
Target latency/cost: aim for end-to-end median <120ms, p95 <250ms; cost target <$0.002 per query (embeddings+rerank amortized).
Architecture preference: two-stage retrieval — vector search (hosted embeddings index) + generator/reranker for top-10 reordering. Interested in Redwood's routing + caching for hot prefixes.
Model preferences: open embeddings (1536-d) for first stage, re-ranker as smaller decoder or cross-encoder; evaluating Redwood's quantized variants vs their in-house BERT reranker.
Security/compliance: SOC2 required, SSO for admin console, audit logs for queries, retention controls for transcripts. Data res
…[truncated]
```

#### #7 `dsid_b414948508a24e8ca0df504dd7944601`

```
Partner Technical & Commercial Onboarding Guide

Overview:\n\nThis document is a combined technical and commercial onboarding guide for platform partners (ISVs, channel partners, and system integrators). It codifies the minimal requirements, SLOs, integration steps, and commercial checkpoints required to move a partner from initial engagement to production launch on Redwood Inference. The goal is to standardize the experience so partners meet performance/compliance expectations while minimizing engineering hand-hold time.\n\nAudience:\n- Partner engineering managers and integration engineers\n- Redwood partner managers and solutions engineers\n- Sales and legal teams finalizing commercial terms\n\nGoals:\n- Deliver a repeatable 8-week onboarding path for non-enterprise partners and a configurable 12–16 week path for enterprise integrations.\n- Ensure measurable performance: 95th percentile latency <= 250ms for transactional routes in hosted mode (see SLOs).\n- Validate commercial readiness: billing setup, SKU mapping, crediting and contract sign-off.\n\nScope and partner types:\n- ISVs integrating Redwood API directly into a product (primary focus).\n- Channel partners white-labeli
…[truncated]
```

#### #8 `dsid_06464e95b7cc44de8a9677f3260c336e`

```
Platform Brief: SaaS GTM — Inference Value Metrics & Battlecards

Overview

Purpose: This brief consolidates product positioning, high-impact value metrics, competitive battlecards, pricing guidance, a compact case study, and a prospect-facing security FAQ tailored for SaaS platform buyers evaluating LLM inference solutions. Audience: AEs, SEs, solutions engineers, and product marketing running discovery and technical evaluation calls with mid-market and enterprise SaaS buyers.

Executive positioning (one-liner)

Redwood Inference: Predictable, production-grade LLM inference that maximizes performance and minimizes unit cost across hosted, dedicated, and private deployments — giving platform teams a single API and operational surface to ship reliable AI features without rebuilding inference infrastructure.

Top 3 buyer outcomes we lead with

- Reduce per-inference cost while keeping sub-100ms tail latency for common interactive flows.
- Move from prototype to SLA-backed production without re-architecting (same API for hosted, reserved, and private).
- De-risk compliance through private deployment and audit-friendly telemetry.

Key value metrics and how to frame them in discovery

-
…[truncated]
```

#### #9 `dsid_09153a5878ee4614abb9a0522549b508`

```
AspenField Analytics Labs

Snapshot: mid-market analytics SaaS. Product org (Head of Product = Lina Park) evaluating Redwood for multi-modal feature set (chat + embeddings + rerank). Preferred path: start with Hosted API POC (2 weeks) to validate latency & unit economics, then move to Dedicated reserved pool if numbers justify. Cost sensitivity: medium-high — wants predictable per-token cost and clear knobs to tune (batching/caching/quantization).

POC ask: ingest 200k docs, drive semantic search + reranking + short chat assistant. Latency targets: chat p95 <= 200ms (aspirational 150ms), embeddings throughput ~30-60 req/s, reranking 100 qps peak for short windows.

Security: SOC2 baseline required, SSO/SAML for internal users, EU data residency for a subset of customer data; KMS integration requested.

Pricing conversations so far: AE ran hosted pricing demo (Jared) 2026-02-10; SE Nina did architecture deep-dive 2026-02-12. Pricing model discussion: runway for hosted credits then committed Dedicated for predictable unit pricing if quantized LLMs + batching reduce cost by target 40-60%.

Cost optimization workshop: scheduled as next major milestone. Goals: measure unit economics on 
…[truncated]
```

#### #10 `dsid_1fb32aada9624d7c862713bfec09e2a1`

```
Oakridge SlateWorks

Mid-market product org building in-app assistant and enterprise search for SMB+/mid-market customers.
Currently on 'Other LLM API' (custom wrapper over OpenAI) — looking to move to Redwood for cost predictability and multi-region routing.
AE intro (Maya) 2025-11-07: Jared wants parity first — "must not regress on response quality for support flows".
SE deep-dive 2025-11-20: discussed function-calling and streaming differences; they use structured tool calls heavily.
POC scope agreed: 2-week perf run (hosted) replicating 4 typical dialogs, embeddings index rebuild, and reranker A/B vs OpenAI baseline.
Finance sensitivity: target unit cost reduction 20-30% while keeping p95 latency < 300ms for short-turn chat (<=256 tokens).
Security/SaaS sales ask: SOC2 + SSO + audit logs; will require VPC/Dedicated for enterprise customers in Q3 rollout.
Quote from Jared on call: 'If it’s cheaper but our customers see regressions we'll lose trust — need eval harness and gating.'
Legal raised DPA/residency question — EU customers require tenant data residency in eu-west-1 region.
They maintain a regression suite (1000+ prompts) and want Redwood to run the suite and surface diffs
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 61: `qst_0448::completeness` · N=75000 · meta · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The retrieved document IDs do not match any of the expected document IDs, indicating a failure in the retrieval process. The retrieved chunks are relevant to log retention policies but do not specifically address the exceptions granted to customers, which is the focus of the question. The gold chunks are on-topic and non-empty, providing specific examples of exceptions. The failure mode is likely an embedding near miss, as the retrieved documents are generally related to the topic but not specif

### Question

Which customers have been granted an exception to Redwood’s default inference request log retention policy, and what retention period was approved for each?

### Gold document(s)

#### GOLD `dsid_5f0ab47fe8de47a89bb6668f8722becf`

```
Re: QuantaGov security questionnaire  logging & retention

From: Olga Petrov <olga@redwoodinference.com>
To: Samir Khan <samir.khan@quantagov.example>
Cc: Elena Varga <elena.varga@quantagov.example>
Date: Tue, Oct 21, 2025 at 4:40 PM
Subject: Re: QuantaGov security questionnaire  logging & retention

Samir  responding to the logging/retention section. By default we retain inference request payload logs for 30 days and metadata for 90 days.

You asked for extended retention for audit: 180 days payload + 365 days metadata. We can support this for your Private (VPC) deployment provided access controls and audit logging are enabled in your environment.

Attaching our latest questionnaire responses.

 Olga
(Attachment: QuantaGov_Security_Questionnaire_Redwood_Responses_v3.docx)

---
From: Samir Khan <samir.khan@quantagov.example>
To: Olga Petrov <olga@redwoodinference.com>
Date: Tue, Oct 21, 2025 at 5:12 PM
Subject: Re: QuantaGov security questionnaire  logging & retention

Thanks. Can you confirm the 180/365 retention is approved and will be configured in the telemetry exporter?

---
From: Avery Johnson <avery@redwoodinference.com>
To: Olga Petrov <olga@redwoodinference.com>
Date: Wed, Oct 22, 2025 at 9:03 AM
Subject: Re: QuantaGov security questionnaire  logging & retention

Approved on our side (Security ok) for QuantaGov only: payload 180 days, metadata 365 days. Ive opened INT-1974 to track the config change + evidence.

---
From: Priya Natarajan <priya@redwoodinference.com>
To: Avery Johnson <avery@redwoodinference.com>
Cc: Olga Petrov <olga@redwoodinference.com>
Date: Wed, Oct 22, 2025 at 9:18 AM
Subject: Re: QuantaGov security questionnaire  logging & retention

Confirmed approved with conditions: restricted RBAC, access logging enabled, encryption-at-rest in VPC log store.

---
From: Olga Petrov <olga@redwoodinference.com>
To: Samir Khan <samir.khan@quantagov.example>
Cc: Elena Varga <elena.varga@quantagov.example>
Date: Wed, Oct 22, 2025 at 11:05 AM
Subject: Re: QuantaGov security questionnaire  logging & retention

Confirmed: we will configure the telemetry exporter for QuantaGov to retain payload logs 180 days and metadata 365 days (QuantaGov only).

 Olg
…[truncated]
```

#### GOLD `dsid_67a8c3300752435296938175e9a1daf5`

```
Helio Health  Inference Log Retention Addendum (Executed)

Helio Health, Inc.
Addendum to Master Services Agreement  Inference Request Log Retention

Effective Date: 2025-06-05
Parties: Redwood Inference, Inc. (Provider) and Helio Health, Inc. (Customer)

1. Definitions
Inference Request Logs means logs that may include prompt and completion text (payload) and associated request metadata (timestamps, model id, token counts, latency, status code).

2. Retention Term (Exception)
Notwithstanding any default retention settings, Provider agrees to the following for Customers Hosted API usage in the EU region (eu-west):

- Payload (prompt + completion) retention: Seven (7) days
- Metadata-only retention: Ninety (90) days

3. Deletion
Provider will delete payload logs on a rolling basis such that payload logs older than seven (7) days are no longer available in Providers log storage systems for Customer.

4. No other changes
All other terms of the Agreement remain in effect.

Signatures
Redwood Inference, Inc.: /s/ Kimberly Park
Helio Health, Inc.: /s/ Dana Lowell

(Attachment stub: helio-health-log-retention-addendum-executed.pdf)
```

#### GOLD `dsid_6933f9241ef140da9d3bf98be52be867`

```
Log retention exception  QuantaGov (extended retention for audit)

Issue summary:
QuantaGov (Private VPC deployment) requests longer retention for inference request logs for audit purposes.

Requested retention:
- Payload: 180 days
- Metadata: 365 days

Notes:
This is a Private deployment. Customer uses Redwood-managed telemetry exporter into their VPC-managed log store, but Redwood is still responsible for the default TTL config in the exporter.

Acceptance criteria:
1) Exporter config updated to 180d payload and 365d metadata for QuantaGov only.
2) Security approval documented.
3) Customer acceptance recorded (security questionnaire / email).

References:
- Policy: confluence://security-and-compliance/data-residency-and-retention/inference-request-log-retention-policy
- Exception register: confluence://security-and-compliance/risk-and-exceptions/inference-log-retention-exception-register

Avery Johnson (2025-10-17): Customer requires 6 months for payload and 12 months for metadata. They claim federal audit requirement. Need Security review + confirm we can meet access-control constraints.
Priya Natarajan (2025-10-20): From a policy standpoint, longer retention is allowed if access controls and audit logging are enabled. Please ensure: (a) RBAC group is limited, (b) access is logged, (c) encryption at rest in customer VPC is configured.
Avery Johnson (2025-10-22): Approved. Payload=180d, metadata=365d for QuantaGov only. Evidence: completed security questionnaire response sent by Olga (see email thread in her mailbox).
Ethan Park (2025-10-28): Updated `telemetry-exporter` Helm values for quantagov to set `payload_ttl_days=180` and `metadata_ttl_days=365`. Rolled out in us-east.
Ethan Park (2025-11-03): Validation: config applied and retention policies visible in exporter status endpoint. Customer confirmed.
Hannah Schmitt (2025-11-05): Added to exception register. Closing.
```

#### GOLD `dsid_84ec014ad9f14f1481b45484da41181a`

```
Re: Northstar Bank  confirmation on inference log retention

From: Aisha Rahman <aisha@redwoodinference.com>
To: Jordan Ellis <jellis@northstarbank.example>
Cc: Maya Chen <mchen@northstarbank.example>
Date: Wed, Feb 12, 2025 at 9:14 AM
Subject: Re: Northstar Bank  confirmation on inference log retention

Jordan  confirming what we can support for Dedicated in us-east:

- Prompts/completions (payload): not persisted (0 days retention)
- Request metadata (no payload text): 30 days retention

Well keep aggregated metrics (no request identifiers) for longer-term operational reporting.

If this matches your requirement, reply confirmed and well proceed with the config change and document the exception.

 Aisha

---
From: Jordan Ellis <jellis@northstarbank.example>
To: Aisha Rahman <aisha@redwoodinference.com>
Date: Wed, Feb 12, 2025 at 10:01 AM
Subject: Re: Northstar Bank  confirmation on inference log retention

Confirmed. Thanks for being explicit about payload vs metadata.

Jordan

---
From: Priya Natarajan <priya@redwoodinference.com>
To: Aisha Rahman <aisha@redwoodinference.com>
Date: Wed, Feb 12, 2025 at 10:18 AM
Subject: Re: Northstar Bank  confirmation on inference log retention

Please ensure this is reflected in the exception register and the INT ticket links this thread for evidence.

Priya

---
From: Aisha Rahman <aisha@redwoodinference.com>
To: Priya Natarajan <priya@redwoodinference.com>
Date: Wed, Feb 12, 2025 at 2:02 PM
Subject: Re: Northstar Bank  confirmation on inference log retention

Will do. Linked to INT-1842 and updating the register today.
```

#### GOLD `dsid_b72bd7e0c91a4f8c9d9a13daf6ff3d28`

```
eng-security

Aisha Rahman: Need quick approval: Northstar Bank (Dedicated) wants *no prompt/completion logging* + metadata only for 30d. Blocking go-live. Any issues?

Priya Natarajan: Approved. Set payload retention to 0 (dont persist prompts/completions). Metadata retention 30d is fine. Please record in INT ticket + exception register. :thumbsup:

Alex Martinez: Cool. Ill implement via log pipeline drop + TTL override. Will post verification.

Hannah Schmitt: +1. Make sure customer acceptance is captured (email) and link it in INT-1842.
```

#### GOLD `dsid_b793b06789ae4147884e94681c6beae1`

```
Log retention exception  Helio Health (7-day payload retention)

Issue summary:
Helio Health (Enterprise Hosted API, EU) requests shorter retention for request payload logs.

Requested retention:
- Payload (prompt/completion): 7 days (vs default 30 days)
- Metadata: keep default 90 days

Rationale:
Customer DPA addendum requires minimizing storage of personal data in prompts.

Acceptance criteria:
1) Payload log TTL for Helio Health set to 7 days in eu-west.
2) No change to other customers.
3) Customer confirmation captured (contract addendum or email).

References:
- Policy: confluence://security-and-compliance/data-residency-and-retention/inference-request-log-retention-policy

Olga Petrov (2025-05-28): Legal wants a clear exception approval. Customer asked for 0 days initially but agreed to 7 days if we can guarantee deletion.
Hannah Schmitt (2025-06-03): Approved for Helio Health in eu-west. Payload retention = 7 days. Metadata retention remains 90 days. Please ensure deletion SLA communicated.
Connor O'Brien (2025-06-04): Applied retention override in log pipeline config: `customer_id=helio-health` payload_index_ttl=7d. Validated index policy.
Olga Petrov (2025-06-06): Contract addendum executed and stored in Drive (shared_drives/go-to-market/contracts/helio-health-log-retention-addendum). Update the exception register.
Connor O'Brien (2025-06-07): Register updated; closing.
```

#### GOLD `dsid_e91e68b31a6f4935b87d6f74dd07e1f6`

```
Log retention exception  Northstar Bank (disable prompt/completion logging)

Issue summary:
Northstar Bank (Dedicated) requests a retention exception: do not store prompts/completions (payload) in request logs.

Impact:
Contractual blocker for go-live.

Requested behavior:
- Payload retention: 0 days (do not persist prompt/completion text)
- Metadata retention: reduce from 90 days default to 30 days (customer prefers shorter)

Environment:
- Dedicated cluster: `ded-northstar-prod-us-east`
- Traffic via standard API gateway.

Acceptance criteria:
1) Prompt/completion fields are not written to persistent log storage for this customer.
2) Metadata-only logs retained for 30 days.
3) Implementation validated with a test request.

Links:
- Policy: confluence://security-and-compliance/data-residency-and-retention/inference-request-log-retention-policy
- Register: confluence://security-and-compliance/risk-and-exceptions/inference-log-retention-exception-register

Aisha Rahman (2025-02-10): Customer security team requires no payload logging. They are ok with metadata-only for 30 days. Need Security sign-off for exception + guidance for implementation.
Priya Natarajan (2025-02-11): Approved. Payload retention = 0 days (disabled). Metadata retention = 30 days. Scope: Northstar Bank only; Dedicated us-east. Ensure access controls remain least privilege.
Alex Martinez (2025-02-12): Implementation plan: add customer override in `obs-logs-prod` pipeline to drop `prompt`, `completion`, and `messages` fields before sink. Separate TTL for `request_metadata` index = 30d. Will roll out behind config flag `log_payload_enabled=false`.
Alex Martinez (2025-02-14): Rolled out to `ded-northstar-prod-us-east`. Verified via sample request: payload fields absent in persisted record; metadata present.
Hannah Schmitt (2025-02-18): Confirmed customer acceptance recorded via email (Aisha mailbox). Please update exception register row.
Alex Martinez (2025-02-18): Register updated. Closing.
```

### Retrieved top-10

#### #1 `dsid_5a060c16f9e943dfb6556b74d1bee39e`

```
Re: Redwood Inference security review: retention & deletion timelines

From: Ava Chen <ava.chen@redwoodinference.com>
To: Samir Desai <samir.desai@northpeakbank.com>
Cc: Naomi Feldman <naomi.feldman@redwoodinference.com>, Aisha Rahman <aisha.rahman@redwoodinference.com>
Date: Tue, Feb 18, 2025 at 4:12 PM
Subject: Re: Redwood Inference security review: retention & deletion timelines

Samir  answering inline below.

1) Prompts/outputs retention: For Hosted API and Dedicated, we do not persistently store prompts and model outputs by default.
2) Request logs retention: We retain operational request logs (metadata only) for 14 days by default.
3) Debug payload logging: If you explicitly enable it for troubleshooting, retention is 7 days.
4) Audit logs: retained for 12 months.
5) Deletion requests: once validated, we complete deletion within 30 days for data stored in Redwood-managed systems.

Happy to jump on a quick call if helpful.

 Ava

--
Ava Chen
Enterprise Account Executive
Redwood Inference


On Tue, Feb 18, 2025 at 12:55 PM Samir Desai <samir.desai@northpeakbank.com> wrote:
> Thanks  can you confirm specific timeframes (days/months) for request logs, audit logs, and any payload
…[truncated]
```

#### #2 `dsid_f7d5fea86ebc4266abc8a92f79b93565`

```
Clarify: default retention for prompts vs inference outputs

From: Amit Patel <amit.patel@finapp.com>\nTo: Evelyn Hart <evelyn_hart@redwood.com>\nDate: Sun, 5 Apr 2026 09:12:00 -0700\nSubject: Clarify what Redwood stores by default (prompts vs outputs)\n\nEvelyn —\n\nQuick question from our security review: can you confirm exactly what Redwood stores by default for hosted API customers? Specifically:\n- Are the raw prompts (user requests) and the model-generated outputs both retained as part of \"request/response logs\"?\n- Do embeddings generated via your embeddings endpoint count as the same class of log?\n- What are the default retention windows for these artifacts (prompts, outputs, embeddings, request metadata)?\n- Do you ever use stored request/response data for improving models or analytics unless we opt in?\n\nWe're trying to reconcile your standard contract language with our procurement questionnaire — procurement wants a short clear answer and an attestation we can put in the contract.\n\nAlso: if we need a one-time purge or an ongoing shorter TTL, what are the supported options and SLA for confirming deletion?\n\nThanks,\nAmit\nAmit Patel\nLead Security Engineer, FinApp,
…[truncated]
```

#### #3 `dsid_97200e6e3c2b4062a8cb3c13047a464c`

```
Retention granularity & customer-held logs: workflow and attestation

From: Julia Nguyen <julia.nguyen@acmepharm.com>\nTo: marissa.cole@redwood.ai, security@redwood.ai\nDate: Tue, 25 May 2027 09:12:00 -0700\nSubject: Question on log retention granularity and customer-held logs\n\nHi Marissa —\n\nWe're working through the SIG and CAIQ answers for our procurement review and have two related asks about Redwood's log retention model that came up from our legal/compliance team:\n\n1) Retention granularity: can you confirm whether retention is applied at the customer-tenant level only, or if we can request finer-grained rules (per-project or per-model)? Our internal policy sometimes requires different TTLs for production vs. staging environments.\n\n2) Customer-held logs: for certain regulated workflows we need to be able to request a short-term hold (30–90 days) on raw inference logs (request metadata + prompts, not model weights). Is there an established workflow and attestation Redwood provides when a customer requests a hold? Specifically:\n   - what data fields can be preserved on hold (full payload vs. redacted PII)\n   - whether Redwood can provide a signed attestation and a deliv
…[truncated]
```

#### #4 `dsid_615b95b58757481a96975cbe5ea4f65c`

```
Storage horizon primer — concrete examples for requests vs. results

From: Emma Liu <emma.liu@summitcare.com>
To: Olga Petrov <olga_petrov@redwood.com>
Cc: procurement@summitcare.com
Date: Sat, 09 May 2026 10:12:00 -0700
Subject: Pilot question — what exactly do you keep by default?

Hi Olga,

Thanks for the walkthrough yesterday. Legal asked for a short, concrete summary we can give compliance — specifically: for the hosted pilot, please list with examples what Redwood keeps by default and for how long. They're asking for simple categories we can paste into our vendor questionnaire.

Example they want: 
- "User request (raw text) — kept? for how long?"
- "Model-generated answer — kept? for how long?"
- "Intermediate streamed fragments / k/v cache — kept?"

Can you provide a one-page equivalent (examples + timelines) and any pointers on how customers can opt-out or request erasure?

Appreciate it,
Emma Liu
Procurement, SummitCare

From: Olga Petrov <olga_petrov@redwood.com>
To: Emma Liu <emma.liu@summitcare.com>
Cc: Kimberly Park <kimberly_park@redwood.com>
Date: Sun, 10 May 2026 09:03:00 -0700
Subject: Re: Pilot question — what exactly do you keep by default?

Hi Emma — thanks for
…[truncated]
```

#### #5 `dsid_107b32582f064c0481b84fcc630e026c`

```
Clarifying Redwood default log retention, residency, and delete options

From: Alex Reynolds <alex@acme-corp.com>
To: rishi_malhotra <rishi@redwood.ai>
Cc: Lisa Gomez <lisa.gomez@acme-corp.com>
Date: Sun, 21 Jun 2026 13:12:00 +0100
Subject: Quick Q: default retention for requests/outputs and residency

Hi Rishi,

Thanks again for the demo yesterday — excited about Redwood's latency and cost numbers. Before we move to a POC, the security/compliance team asked for a few clarifications around default log retention and residency for request/response data (prompts + model outputs). High level questions:

- By default, how long does Redwood keep request & response logs for hosted API customers? Does that include raw prompts and outputs or just metadata?
- For EU customers, where are those logs stored by default? Is it single-region, multi-region, or configurable?
- If we request deletion of an account's logs, what is the typical SLA (pushed vs background purge)? Are there any retained audit copies?

We'd like concise answers we can share with our InfoSec. Happy to jump on a quick call if needed.

Thanks,
Alex
Alex Reynolds
Head of Platform, Acme Corp

From: rishi_malhotra <rishi@redwood.
…[truncated]
```

#### #6 `dsid_a1f5902940664452bd4113c082397954`

```
Clarification on non-training guarantee and retention edge cases

From: Sofia Ramirez <sofia.ramirez@nimbushealth.com>
To: priya_natarajan@redwoodinference.com
Cc: Nimbus Health Security <security@nimbushealth.com>
Date: Fri, 14 Sep 2028 09:12:00 -0700
Subject: Quick Q: Are customer payloads used to train models? + retention edge cases

Hi Priya,

Hope you are well. We're progressing through our security review for Redwood as a potential inference partner. Two short, but important, items came up from our InfoSec and Privacy teams:

1) Public statement we can include in our vendor inventory: does Redwood train or fine-tune any public or private models using customer request/response payloads? We need a clear yes/no and the precise boundary — including automated telemetry that might be used for model improvements.

2) Retention edge cases: we understand assertions around not training on customer data, but can you describe what happens to short-lived artifacts (e.g., KV cache, prefix caches, temporary logs) and to backups/snapshots? Is there ever a case where those would be persisted beyond the configured retention window or used for model improvement research?

Appreciate a concise a
…[truncated]
```

#### #7 `dsid_b872e1fd54d94b0488655e58d71d814f`

```
Conditional archive escrow and TTL alignment discussion

From: Laura Chen <laura.chen@northwell-analytics.com>
To: stephanie_nguyen@redwoodinference.com, karthik_iyer@redwoodinference.com
Cc: kimberly_park@redwoodinference.com
Date: Mon, 9 Nov 2026 09:12:00 -0800
Subject: Request: temporary retain for upcoming audit + log retention exception

Hi Stephanie / Karthik,

We have an external compliance audit starting 2026-11-20 and the auditors have asked for a 90-day temporary retain on a subset of transaction logs associated with our integration environment (env: northwell-int-1). Specifically they need:

- All request/response logs for the period 2026-08-01 → 2026-11-20 (index + raw logs)
- Backup snapshots that cover the same window (to allow restore testing)
- Short-lived escalation evidence tied to the DPA Annex B (custody & deletion proof)

Can Redwood put a time-limited hold (90 days) on purge for those artifacts and issue a short annex that documents the retention exception and the subprocessors involved? We attached the audit intake summary.

Also: please point us to the DocuSign/annex flow if one is required.

Thanks — happy to jump on a quick call if helpful.

Best,
Laura Ch
…[truncated]
```

#### #8 `dsid_ac17673b4827489cbc0c55136fb48d8b`

```
Data governance: triage for Sigma Health audit log / retention asks

From: Alice Jenkins <alice.jenkins@sigmahealth.com>
To: marissa_cole <marissa.cole@redwood.example>
Cc: Tom Riley <tom.riley@sigmahealth.com>
Date: Thu, 15 Apr 2027 09:12:00 -0700
Subject: Sigma Health security questionnaire and retention asks

Hi Marissa,

Thanks again for the demo yesterday. Security reviewed the flow and we have two high priority asks before we can move to procurement:

1) We need an immutable audit log that records API request metadata (caller id, model id, tokens in/out, timestamps) with exportable retention controls. Our policy requires a way to prove tamper-evidence for 1 year.
2) Data retention: PII-containing prompts must be retained for 90 days in hot storage, and for 3 years in cold storage — and we need a documented process for purge and legal holds.

I've attached our baseline questionnaire (answers in red would be ideal). Can someone from product/security confirm whether Redwood can meet these or if we should plan an exception?

Best,
Alice Jenkins
Security Program Manager
Sigma Health
[Attachment: Sigma_Security_Questionnaire_v2.pdf (PDF, 1.2MB)]
From: marissa_cole <marissa.cole@red
…[truncated]
```

#### #9 `dsid_dffa4ad88a014af1afda8e2835666e85`

```
Preserving logs during incident — data retention & hold request

From: Samir Joshi <samir@chroniclehealth.com>
To: vivek_kulkarni <vivek@redwood.ai>, monica_patel <monica@redwood.ai>
Cc: Legal Team <legal@chroniclehealth.com>
Date: 2026-10-10T09:15:00-07:00
Subject: Preserving logs during incident — data retention & hold request

Hi Vivek / Monica,

We discovered potential data exposure related to a subset of test traffic on our integration and our legal team has opened an investigation. We need Redwood to preserve certain logs while the investigation is open. Specifically:

- Retain admin/audit logs for the Chronicle account (org-level admin actions, key rotations, user role changes) for the last 12 months and continue retention going forward until the hold is lifted.
- Preserve API request metadata (request_id, timestamp, model id, response metadata) for the period 2026-06-01 through 2026-10-01.

Questions:
1) What are Redwood's default retention windows for audit logs and API request logs today?
2) Can you suspend automatic deletion for the specified ranges and grant an account-level retention hold?
3) If we need a longer retention window (24 months), what is the process, approv
…[truncated]
```

#### #10 `dsid_23f5d21106034c2c9c442e8871fa7a4c`

```
SIG: audit log export formats + delivery options

From: Elena Ramos <elena.r@finbank.com>
To: Rishi Malhotra <rishi_malhotra@redwood.com>
Cc: FinBank Security <security@finbank.com>, Tom Lee <tom.lee@finbank.com>
Date: 2026-08-14T09:12:00Z
Subject: SIG: audit log export format and delivery options

Hi Rishi,

Were working through the SIG and have a couple of specific asks around audit logs for Redwoods hosted inference service: 1) what event types are captured (auth, API request, model inference, admin changes), 2) canonical schema (column names / example record), 3) retention windows for hosted vs dedicated/private, and 4) delivery/export options (console download, S3, syslog) and whether customers can get automated daily exports.

Can you point us to a sample export and confirm whether logs contain prompt/request payloads or just metadata? FinBanks compliance team needs this to sign off on the SIG.

Thanks,
Elena Ramos
FinBank - Security Risk

From: Rishi Malhotra <rishi_malhotra@redwood.com>
To: Elena Ramos <elena.r@finbank.com>
Cc: Monica Patel <monica_patel@redwood.com>, Laura Bennett <laura_bennett@redwood.com>
Date: 2026-08-14T11:30:00Z
Subject: Re: SIG: audit log export for
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---

## Row 62: `qst_0470::miscellaneous` · N=100000 · raw · priority=high

- **auto Hit@10:** `False`
- **LLM triage (optional):** label=`n` mode=`embedding_near_miss`
- **LLM note:** The expected document ID is not present in the top-10 retrieved IDs, making the Hit@10 label incorrect. The retrieved chunks are relevant to GPU scheduling and cache management but do not directly address the specific interview strategy question. The failure mode is likely an embedding near miss due to the thematic similarity but lack of direct content match. Both gold and retrieved chunks are non-empty and on-topic, but the retrieval did not capture the specific expected document.

### Question

In a backend inference engineer interview about multi-tenant GPU scheduling, what strategy did the candidate propose to reduce cold misses for growing attention cache in long chat histories?

### Gold document(s)

#### GOLD `dsid_aea4790d4bcc45859208d7d705f682a1`

```
Interview: Backend Inference Engineer - Jordan Lee

Technical onsite-style interview for a Backend Inference Engineer role. Focus areas: serving runtime internals, batching and KV-cache tradeoffs, and a systems design whiteboard on multi-tenant GPU scheduling. Candidate demonstrated strong systems intuition, some ambiguity in quantization details, and practical experience with distributed caching. Agreed next steps: follow-up take-home exercise and reference checks.
Meeting header: 2026-03-21 16:00 UTC, duration ~58m. Attendees: Priya Narayanan (Redwood), Samir Chen (Redwood), Jordan Lee (candidate).

[00:00] Priya: Hi Jordan, thanks for making time. We're going to do a systems-forward interview — about 50 minutes — and then 5–10 minutes for questions. Sound good?
[00:10] Jordan: Yep that works for me. Excited to talk through some of the infra stuff.
[00:18] Samir: Quick note — feel free to use screen share, we can draw. If you prefer whiteboard verbal, that's fine too.
[00:25] Jordan: I can share a quick diagram, let me know when.

[00:30] Priya: Great. Let's start with a scenario: you have a multi-tenant LLM inference service. Customers have mixed latency requirements; some are small chat responses, some are long-form generation. How would you design the request routing and batching strategy to balance latency and throughput?
[00:50] Jordan: Okay, so first cut, separate by SLO tier — fast-path for low-latency customers, batch-path for bulk. Use an upfront router that tags requests with expected token length and priority. For batching you run continuous batching window, but you also have a max-wait timeout, like 5–10ms for the low-latency tier, and larger for throughput.
[01:20] Samir: When you say continuous batching, are you thinking synchronous queues per worker or a global scheduler?
[01:27] Jordan: I'd go with hybrid — local worker-level queues for micro-batching to reduce cross-host coordination, and a global coordinator for balancing load and moving batches if workers are idle. The coordinator can reshuffle by affinity and memory footprint (KV cache locality).
[01:45] Priya: How would you incorporate KV cache behavior? For large chat histories the KV cac
…[truncated]
```

### Retrieved top-10

#### #1 `dsid_8dc419eccd7744939b1ee86da30e078d`

```
Foreground/Background Cache Thaw Investigation — personal scratchpad

Goal:\nQuickly understand how background tenant noise + periodic low QPS windows cause cache thawing (KV cache miss storm) for foreground low-latency requests. Build minimal reproducible workload and capture empirical latency/kv-hit profiles, hypothesize mitigations.\n\nMotivation/context:\n- Product: low-latency chat endpoint serving many multi-tenant apps. Some customers get repeated short bursts with long idle tails (few minutes).\n- Observed: after a ~2–10m idle, a foreground request sees P99 spike ~3–5x for first few tokens; KV cache hit rate drops sharply. Suspect eviction + cold-start of attention key/value caches on GPU memory + kernel trampolining for quantized models.\n\nHypothesis:\n1) Background batch jobs (low-priority tenants) temporarily evict KV cache or cause GPU memory pressure -> foreground requests get no warm cache.\n2) Even without eviction, the runtime defers kernel specialization for long-tail sequence lengths, leading to first-request kernel selection jitter.\n3) Small prefix (1–3 tokens) of foreground requests is dominated by setup/transfer overhead; once warmed, steady-state is fine.\n\
…[truncated]
```

#### #2 `dsid_a408d0c23fe14754a036e2d2f12be9ad`

```
Nanopause context-switch penalty — exploratory logs

Quick personal runbook and raw logs for measuring short-request context-switch overhead on multi-tenant GPU hosts. Goal: quantify per-request latency penalty when the runtime repeatedly preempts and restores KV cache / CUDA contexts for a mix of short (50–150 tokens) and long (800–2048 tokens) requests.
- Observed a consistent extra 6–18 ms p50 penalty per short request when preceded by a long request that caused an eviction of model context on A100 40GB host with two tenants.
- Penalty scales with cold KV cache size and quantization mode: FP16 had ~12–18ms extra, int8->int8-quantized path had ~6–9ms extra (likely because we pre-compile/int8 kernels and warm-up less heavy). 
- Batch size and request coalescing reduced penalty (single-request streams suffer most). Setting a short 5ms batching window eliminated ~60% of penalty in synthetic mix.
- Host: n1-standard-like node with A100 40GB (Prod-sim cluster, isolated test pool)
- CUDA driver: 520.61
- Runtime build: serving-runtime@main (commit 5d3f7a2), with dynamic KV-cache eviction toggles enabled
- Model: llama-2-13b-instruct (fp16 / int8 variants)
- Quantization path: bitsandby
…[truncated]
```

#### #3 `dsid_43dc7bb3227b4897b1ed21a6b838c647`

```
Hot/Cold prefix stratification and GPU page-aware eviction hints for continuous batching

Problem: Under mixed workloads we observe that small conversational prefixes are frequently re-used while large system prompts and rare long contexts pollute GPU slab space. This increases GPU memory pressure, forces premature eviction of useful KV fragments, and hurts batching efficiency (more cold misses and higher tail latency). Goal: introduce a light-weight runtime-level stratification that marks prefix fragments as hot or cold, emit GPU-page-aware eviction hints, and expose affinity signals into the continuous-batcher so that batches preserve reuse locality and reduce redundant KV loads.
1) Runtime telemetry: extend KV fragment metadata with a hot_score (decay-based) and residency_hint (GPU page id estimate) emitted at fragment write and on reuse. 2) Hot/Cold allocator: maintain two slab pools per GPU: hot-resident slabs (short retention but pinned for faster reuse) and cold-evictable slabs (higher eviction priority). 3) Page-aware eviction hints: when eviction candidate chosen, annotate with approximate GPU page ranges to prefer evicting contiguous cold pages and avoid scattering hot fr
…[truncated]
```

#### #4 `dsid_5edb76bdee774249af7a01dacb69b3c6`

```
eng-platform

Alex: Heads-up — hit a sustained saturation event in eu-west shared pool yesterday (~12m). Small tenants saw p50->p99.5 blow up, overall GPU busy but tail latency spikes. I think it's cache-affinity loss + a handful of heavy workflows spinning hot loops. Proposing a hybrid "pacing+affinity" approach: short-term token pacing per-tenant + soft placement hints to keep KV/cache locality. Thoughts?\n\nNina: Can you paste the query profile and top-10 offending tenants?\n\nAlex: quick snippet below, trimmed for privacy. pattern: lots of short sequential chat completions + long embeddings backfills from same tenant.\n```\nTop tenants: tenant-42, tenant-19, tenant-7\nOps: sustained 60k reqs/min on small sequences, spikey inter-arrival, KV miss ratio up 3x\nLogs: gpu0: util=98%, queue_len=240, tail_lat=480ms\n```\n\nSam: SGTM. Two asks: (1) pacing should be queue-aware (trim refill when queue>threshold), (2) add a small randomized jitter to avoid sync bursts.\n\nLeo: Also consider adding a cost-backpressure signal to billing API so tenants get visibility (and optionally throttle themselves). Helps incent good behaviour.\n\nMarta: How would placement affinity work? do you mean s
…[truncated]
```

#### #5 `dsid_aa8906c3e0b34f8697dd3db42c875fa2`

```
Context-cache tiered quantization + routing probe (FP8/INT8/INT4) with continuous-batching interaction

Investigate a tiered quantization and routing strategy for the context (KV) cache that balances GPU memory reduction with generation quality and continuous-batching latency SLOs. Instead of a single global compression profile, evaluate per-cohort and per-age policies that place older/low-utility cache entries into lower-precision storage (INT4/INT8) while keeping hot/recent entries in FP8 or full precision. Measure quality trade-offs (token divergence, perplexity, end-task metrics) and operational effects on batching and memory fragmentation.
A tiered scheme that assigns cache entries to FP8/INT8/INT4 by estimated future utility (recency + token cohort) will reduce peak GPU memory by >=30% with <1% end-to-end task degradation for most workloads, and can be integrated with continuous batching with minimal impact to p95 latency if fallback and warm-up paths are used.
>30% peak KV memory reduction on mixed web-chat workloads
<+1.0% absolute degradation on chat-turn BLEU/ROUGE or task-specific metric
p50 latency impact <5ms, p95 <10ms on 8-GPU worker under target load
no >0.5% increa
…[truncated]
```

#### #6 `dsid_80992442edfa4cdeac127d5e38c93548`

```
Zenara Inference Ops

Enterprise customer running hybrid inference: primary workload is interactive chat + heavy reranking/embeddings. Goal is a dedicated pool that guarantees throughput (800-1,200 req/s for batch pipelines) and tight latency SLOs (p95<120ms chat). Evaluating model-specific tuning: 70B model with nf4/awq profiles for day-to-day, int8 as fallback for cost bursts; context lengths split (8k for chat, 32k for long-form summarization). Plan includes per-session KV cache (12h TTL), micro-batching for chat to meet latency, and routing policies that fallback to smaller variants or hosted instances during capacity pressure.
POC focus: Dedicated capacity sizing for chat + reranking peak windows (09:00-11:00 PT)
Workloads: persistent chat sessions (~4k monthly active users), high-volume embeddings for search, real-time reranking for recommendations
Throughput target: sustained 800-1,200 req/s for embeddings/rerank pipelines; 200 concurrent chat sessions w/ p95 SLO
Latency SLO requested: p95 < 120ms for chat generate (short prompts), p99 < 400ms preferred
Model prefs: Llama-3 style 70B for quality, fallback to 13B/azure-hosted if capacity constrained
Context length: evaluating
…[truncated]
```

#### #7 `dsid_13f943e69e174ec598db02603ddc82c0`

```
memory-fragmentation-lit-scraps-rina-kapoor

Purpose / quick summary:
I sketched a lightweight reading list and experiment skeleton around what I'm calling \"memory fragmentation\" in KV-style caches for autoregressive inference. Goal: practical ideas we can try on Redwood serving runtime to reduce memory footprint and tail latency when many short, interleaved sessions share the same model instance or cache shard.

Context / motivation:
- In our Dedicated/Private deployments we observe many concurrent short chats where each session has tiny prefixes. That leads to lots of small KV entries with low reuse but high metadata overhead.
- Papers on KV compression and memory-efficient attention propose various encodings; the systems-level cost/benefit tradeoffs for production inference (latency + cost) aren't well explored.
- Want to prioritize changes that are low-risk operationally (no model retrain) and that can be toggled per-customer or per-pool.

Key papers / takeaways (very quick, informal):
1) \"Compact KV Encodings for Transformer Caches\" (hypothetical summary of related work) - shows simple PCA / product quantization on keys reduces memory, but lookup noise grows. Important: qu
…[truncated]
```

#### #8 `dsid_b8e8babc72c443b9a0469590ce3fbf62`

```
Stratix Inference Group

Goal: reliable Dedicated inference with deterministic latency SLOs for chat and scoring. Need reserved GPU plan sized for base load + burst, clear autoscaling policy (scale-up latency <60s, scale-down grace to preserve KV cache), warm pools to eliminate cold-start bias, and SLA with credits for missed p95/p99. Regulatory requirements: audit logs, KMS, EU data residency for subset of traffic.
Summary: large fintech (risk + customer support) exploring Redwood Dedicated + Private for production inference. Primary drivers: consistent p95 latency, predictable cost, and auditability for regulators.

Key constraints / quotes: "We cannot have cold-starts impact p99 during market opens; must be predictable between 9-11am ET" - Head of ML. Procurement: needs a firm committed GPU plan and clear overage rules.

Technical concerns raised by infra team: warm-pool memory residency for KV caches, time-to-warm after scale-up, how scale-down affects active streams and token billing. They asked for explicit queueing behavior under burst (what happens at queue saturation: reject vs queue vs fallback).

SE notes: Redwood's suggested approach - reserve baseline pool (8 GPUs) + w
…[truncated]
```

#### #9 `dsid_562322d06ecd48409b91c0f84852b393`

```
memory-pressure-backpressure-arch-deepdive-notes

Notes and decisions from an architecture deep-dive on GPU memory-pressure containment and request-level backpressure. Goal: design a pragmatic, incremental solution that prevents high-memory requests from causing tail-latency spikes while preserving throughput for latency-sensitive traffic.
Background: Over the last 3 weeks we've seen two incidents where a mix of short, low-token chat requests and a small number of long-document summarization calls pushed GPU memory usage above safe thresholds. This caused the runtime to stall while collecting memory and IO, producing ~300–400ms p99 spikes for latency-sensitive routes.

Telemetry gaps: Mei called out missing signals: per-device soft-resident-bytes (inc. pinned KV), per-request peak-resident estimate, cross-GPU aggregate pending-eviction count, and precise KV cache fragmentation metrics. We agreed to add a small telemetry shim to expose 'estimated-request-memory' from the planner + 'kv-frag-score' from the KV store.

Design proposals discussed:
1) Soft vs hard ceilings: Soft ceiling triggers admission control (queuing or gentle backpressure) when device resident > soft_limit (e.g., 8
…[truncated]
```

#### #10 `dsid_ca7dee5f843c4011aed8e515e08dbe47`

```
SummitRidge Logistics AI

Run 48h soak test on 8x GPU reservation + review SLA synopses with legal
ISO27001 evidence requested by infosec
final GPU sizing approval from infra team
budget hold until procurement sign-off
2026-01-12: Intro call (AE/SE) - overview of Redwood Dedicated; customer high-level requirements captured
2026-01-20: Security intake - uploaded SOC2 report to Drive; asked for ISO checklist
2026-02-02: Requirements workshop - mapped workload: peak bursts from route-optimization chat; QPS patterns
2026-02-15: POC plan agreed - 3-stage: baseline perf, load test (48h), soak (7d) with KV cache enabled
2026-02-28: Pre-POC checklist - VPC peering scheduled, KMS key exchange, sample prompts uploaded
2026-03-01: Load test day 1 - pushing sustained 1200 qps of small-chat requests; trace logs captured
POC objective: validate Dedicated can meet 95th pct latency SLO and throughput guarantees for live driver assistant
Targets: 95th <= 150ms for short-turn chat (<=256 tokens); sustained throughput target 1k-1.5k QPS for small queries; batch rerank 200 QPS with <300ms p95
Reserved GPU planning: customer engineering expects to reserve 8 x A100-equivalent or 4 x H100 for peak window
…[truncated]
```

### Your fields (fill in)

```
human_label_correct:   # y | n | unsure
human_failure_mode:    # see list above
human_notes:
```

---
