# L4 Hit@10 fairness — LLM audit (secondary)

L4 is LLM-assisted secondary audit of Hit@10 fairness and gold-text adequacy. Primary paper claims remain L1 labeled IR (unique eval IDs, membership Hit@k) on the integrity-clean scale ladder. Cursor Luna is not used as an API model; this run used gpt-4o via OpenAI-compatible HTTP.

- Model: `gpt-4o` · prompt `l4-hit-fairness-v1`
- Rows: **62** / 62 · spent **$0.7874** / $5.0
- Labels: `{'y': 62}`
- Gold answers question: true=49 false=13
- Failure modes: `{}`

## Per-row

| # | question_id | N | cond | Hit@10 | gold_ans | label | mode | notes |
|---|-------------|---|------|--------|----------|-------|------|-------|
| 1 | `qst_0002::metadata` | 20000 | raw | False | True | **y** | None | The gold document correctly identifies Markus Klein as the internal organizer for the meeting in question. |
| 2 | `qst_0002::metadata` | 100000 | raw | False | True | **y** | None | The gold document correctly identifies Markus Klein as the internal organizer for the meeting in question. |
| 3 | `qst_0003::metadata` | 5000 | raw | True | True | **y** | None | The gold document provides the due date as before the holiday break, which answers the question. |
| 4 | `qst_0010::metadata` | 5000 | meta | True | True | **y** | None | The gold document answers the question by providing the due date for Irene Choi's action item. |
| 5 | `qst_0010::metadata` | 40000 | raw | False | False | **y** | None | The gold document does not mention any due date for Irene Choi's action item. |
| 6 | `qst_0016::basic` | 40000 | meta | False | True | **y** | None | The gold document specifies the default expiration period for contractor access as 30 days, which answers the question. |
| 7 | `qst_0024::metadata` | 15000 | raw | True | True | **y** | None | The gold document directly answers the question by providing verification steps after rotating production credentials. |
| 8 | `qst_0025::metadata` | 75000 | raw | False | True | **y** | None | The gold document specifies the production environment as 'dedicated-prod-us-east-2'. |
| 9 | `qst_0036::basic` | 20000 | raw | False | True | **y** | None | The gold document specifies telemetry events and alert thresholds for monitoring degraded emissions. |
| 10 | `qst_0038::metadata` | 40000 | meta | True | True | **y** | None | The gold document clearly answers the question by detailing the base branch of the merged PR that added GPU queue depth  |
| 11 | `qst_0041::metadata` | 50000 | meta | False | False | **y** | None | The gold document does not specify a forecasted deal closure month, making the MISS fair. |
| 12 | `qst_0044::metadata` | 25000 | meta | False | False | **y** | None | The gold document does not mention the sales owner for the account. |
| 13 | `qst_0048::metadata` | 10000 | meta | True | True | **y** | None | The gold document clearly states the release version target date for the P0 ticket. |
| 14 | `qst_0053::metadata` | 40000 | raw | False | True | **y** | None | The gold document specifies the call duration as 58 minutes, which answers the question. |
| 15 | `qst_0054::metadata` | 100000 | raw | False | False | **y** | None | The gold document does not list an owner for the draft internal notes document. |
| 16 | `qst_0056::metadata` | 25000 | raw | False | False | **y** | None | The auto Hit@10 is consistent with the gold_id_in_top10, and the gold document does not answer the question about a docu |
| 17 | `qst_0063::metadata` | 100000 | meta | False | False | **y** | None | The gold document does not mention a sales owner, making the MISS fair. |
| 18 | `qst_0068::metadata` | 50000 | meta | False | False | **y** | None | The auto Hit@10 is consistent with the gold_id_in_top10, and the gold document does not answer the question about the as |
| 19 | `qst_0069::metadata` | 10000 | meta | False | False | **y** | None | The gold document does not mention a solutions engineer assigned to the account. |
| 20 | `qst_0069::metadata` | 50000 | raw | False | False | **y** | None | The gold document does not mention the solutions engineer assigned to the account. |
| 21 | `qst_0079::basic` | 75000 | raw | False | True | **y** | None | The gold document provides a clear mitigation strategy for the healthcare customer's inference timeouts. |
| 22 | `qst_0084::metadata` | 5000 | raw | False | False | **y** | None | The gold document does not provide a forecasted close month for the prospect owned by Alex Martinez. |
| 23 | `qst_0085::basic` | 10000 | raw | False | True | **y** | None | The gold document clearly outlines the three tiers: micro, standard, and deep. |
| 24 | `qst_0091::metadata` | 20000 | raw | False | False | **y** | None | The gold document does not mention any account updated in mid March 2026 with a forecast close month of May 2026. |
| 25 | `qst_0096::metadata` | 75000 | raw | False | False | **y** | None | The gold document does not provide an SLA due date, making the MISS fair. |
| 26 | `qst_0144::basic` | 15000 | meta | False | True | **y** | None | The gold document confirms the median latency improvement of ~8% due to continuous batching. |
| 27 | `qst_0144::basic` | 40000 | meta | False | True | **y** | None | The gold document confirms an 8% median latency improvement due to continuous batching. |
| 28 | `qst_0150::basic` | 50000 | raw | False | True | **y** | None | The gold document provides the required permission scopes for an API key when facing a 401 error. |
| 29 | `qst_0156::basic` | 50000 | raw | False | True | **y** | None | The gold document provides the composite health score thresholds for green, amber, and red states. |
| 30 | `qst_0166::basic` | 20000 | raw | False | True | **y** | None | The gold document clearly states the procurement target date as the end of Q1 2027. |
| 31 | `qst_0166::basic` | 25000 | meta | False | True | **y** | None | The gold document clearly states the procurement target date as the end of Q1 2027. |
| 32 | `qst_0166::basic` | 50000 | raw | False | True | **y** | None | The gold document clearly states the procurement target date as the end of Q1 2027. |
| 33 | `qst_0166::basic` | 75000 | meta | False | True | **y** | None | The gold document clearly states the procurement target date as the end of Q1 2027, which answers the question. |
| 34 | `qst_0200::semantic` | 25000 | raw | False | True | **y** | None | The gold document specifies the end-to-end response time target for a 200-token response under peak load. |
| 35 | `qst_0204::semantic` | 5000 | meta | False | True | **y** | None | The gold document outlines immediate follow-up actions for the SaaS trial and deployment plan. |
| 36 | `qst_0208::semantic` | 15000 | raw | False | True | **y** | None | The gold document specifies the burst traffic level and duration requested by the customer. |
| 37 | `qst_0209::semantic` | 100000 | raw | False | True | **y** | None | The gold document provides the first-response-time target and concurrent-load threshold for the trial. |
| 38 | `qst_0213::semantic` | 40000 | meta | False | True | **y** | None | The gold document outlines a plan for a time-limited evaluation with a large free usage allowance, matching the question |
| 39 | `qst_0224::semantic` | 75000 | raw | False | True | **y** | None | The gold document specifies using 'actor_id' instead of 'user_email' to avoid exposing emails. |
| 40 | `qst_0234::semantic` | 40000 | raw | False | True | **y** | None | The gold document provides a detailed traffic ramp schedule and stabilization wait time, answering the question. |
| 41 | `qst_0234::semantic` | 100000 | meta | False | True | **y** | None | The gold document provides a detailed traffic ramp schedule including stabilization waits, matching the question require |
| 42 | `qst_0238::semantic` | 15000 | meta | False | True | **y** | None | The gold document outlines a method for structuring prompt experiments with contrapositive examples, which answers the q |
| 43 | `qst_0239::semantic` | 20000 | meta | False | True | **y** | None | The gold document specifies SOC2 evidence and SSO + audit logs as compliance items needed before moving past the pilot p |
| 44 | `qst_0240::semantic` | 40000 | raw | False | True | **y** | None | The gold document explains the cause of bursty requests and service unavailability during multi-region switchovers. |
| 45 | `qst_0240::semantic` | 75000 | meta | False | True | **y** | None | The gold document explains the cause of bursty requests and service unavailability during multi-region failovers. |
| 46 | `qst_0242::semantic` | 10000 | raw | False | True | **y** | None | The gold document specifies the target date for the security smoke test as March 24, 2025. |
| 47 | `qst_0251::semantic` | 15000 | raw | False | True | **y** | None | The gold document provides the performance targets for the overnight vectorization run and interactive response time. |
| 48 | `qst_0251::semantic` | 25000 | raw | False | True | **y** | None | The gold document provides the performance targets for vectorization and response time. |
| 49 | `qst_0251::semantic` | 100000 | meta | False | True | **y** | None | The gold document provides the performance targets for the overnight vectorization run and interactive response time. |
| 50 | `qst_0252::semantic` | 15000 | raw | False | True | **y** | None | The gold document provides the criteria for using a Deferred Postmortem instead of a full analysis. |
| 51 | `qst_0252::semantic` | 50000 | meta | False | True | **y** | None | The gold document provides the criteria for using a Deferred Postmortem instead of a full postmortem. |
| 52 | `qst_0265::semantic` | 5000 | raw | False | True | **y** | None | The gold document explains the issue of stale or zeroed values and missing trace links due to retention compaction warmu |
| 53 | `qst_0265::semantic` | 20000 | meta | False | True | **y** | None | The gold document explains the issue of stale counts and missing trace links due to retention compaction warmup, which a |
| 54 | `qst_0268::semantic` | 10000 | meta | False | True | **y** | None | The gold document clearly identifies the root cause of the incident as a kernel-selection optimization interacting with  |
| 55 | `qst_0268::semantic` | 75000 | meta | False | True | **y** | None | The gold document clearly identifies the root cause of the incident as the interaction between kernel-selection optimiza |
| 56 | `qst_0310::intra_document_reasoning` | 100000 | meta | False | True | **y** | None | The gold document provides the attendees and the scheduled checkpoint meetings with dates. |
| 57 | `qst_0349::project_related` | 75000 | raw | False | True | **y** | None | The gold document explains the cause and fix for the EU-West onboarding email issue. |
| 58 | `qst_0391::constrained` | 25000 | raw | False | True | **y** | None | The gold document provides a detailed explanation of the root cause and immediate mitigations for the API incident. |
| 59 | `qst_0423::conflicting_info` | 100000 | raw | False | True | **y** | None | The gold document specifies exporting 12 months of access logs, which answers the question. |
| 60 | `qst_0444::completeness` | 10000 | raw | False | False | **y** | None | The gold document does not fully answer the question about the end-to-end process, including post-launch monitoring. |
| 61 | `qst_0448::completeness` | 75000 | meta | False | True | **y** | None | The gold document provides specific exceptions for QuantaGov and Helio Health, answering the question. |
| 62 | `qst_0470::miscellaneous` | 100000 | raw | False | True | **y** | None | The gold document discusses strategies to reduce cold misses in KV cache for long chat histories, which answers the ques |
