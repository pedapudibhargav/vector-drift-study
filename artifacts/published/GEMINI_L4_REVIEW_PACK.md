# Gemini L4 Review Pack — High-priority rows (n=62)

## Role

You are assisting a **human auditor** for an IEEE Access paper on **vector retrieval drift**.
Primary paper metrics (L1) use **document-ID Hit@10** only:

> `Hit@10 = true` iff the gold `doc_id` appears in the retrieved top-10 IDs.

Your job (L4) is a **second check**: given the question and the **full gold document text**,
judge whether that gold text is a **reasonable answer source**, and whether the auto Hit@10
label is fair.

## What you are NOT doing

- Do not re-rank the corpus or invent better documents.
- Do not grade the dense retriever’s overall quality beyond this row.
- Do not treat LLM triage notes (if any) as ground truth.

## Important: full gold text

Gold documents below are loaded from the **original EnterpriseRAG-Bench `.txt` files**
(not UI previews). Answers sometimes appear only in the **tail** (e.g. action-item due dates).
Read the **entire** gold document before deciding `label_noise`.

Retrieved top-10 IDs are listed for context; skim titles only unless needed.

## Decision rules

| Situation | `human_label_correct` | `human_failure_mode` |
|-----------|----------------------|----------------------|
| Gold ID ∈ top-10 **and** gold text contains (or clearly supports) the answer | `y` | leave empty or `—` |
| Gold ID ∈ top-10 but text does **not** answer the question | `n` | `label_noise` |
| Gold ID ∉ top-10 (Hit@10 false) and that seems correct | `y` | optional near-miss mode if useful |
| Gold ID ∉ top-10 but gold text clearly answers and should have been retrieved | `n` | `embedding_near_miss` / `semantic_near_miss` / `metadata_needed` |
| Unsure after reading full gold | `unsure` | best-effort mode + note |

### Failure mode definitions

| Mode | Meaning |
|------|---------|
| `label_noise` | Official gold ID, but document does not answer the question |
| `chunk_too_thin` | Answer might exist but this unit is too incomplete (rare here: doc-level files) |
| `embedding_near_miss` | Crowding / near-duplicate; gold missing from top-10 |
| `semantic_near_miss` | Same topic; wrong or incomplete fact |
| `lexical_mismatch` | Shared words; wrong meaning |
| `wrong_source_type` | Wrong document class |
| `stale_gold` | Outdated gold |
| `multi_gold_partial` | Partial multi-doc gold |
| `metadata_needed` | Needs metadata filter to surface gold |
| `other` | Explain in notes |

## REQUIRED output format

Return **one JSON array** (and nothing else outside a single fenced `json` block) with
exactly **62** objects, one per row_id below, in the same order.

```json
[
  {
    "row_id": 1,
    "question_id": "qst_....",
    "corpus_scale_size": 5000,
    "condition": "raw",
    "auto_hit_at_10": true,
    "gold_answers_question": true,
    "human_label_correct": "y",
    "human_failure_mode": null,
    "answer_span": "short quote from gold that supports the answer, or null",
    "human_notes": "one sentence"
  }
]
```

Field rules:

- `human_label_correct`: only `"y"` | `"n"` | `"unsure"`
- `human_failure_mode`: one of `label_noise`, `chunk_too_thin`, `embedding_near_miss`, `semantic_near_miss`, `lexical_mismatch`, `wrong_source_type`, `stale_gold`, `multi_gold_partial`, `metadata_needed`, `other`, or `null` if `y`
- `gold_answers_question`: boolean — does full gold text answer the Q?
- `answer_span`: quote ≤240 chars from gold when `gold_answers_question` is true; else `null`
- Be consistent: if `gold_answers_question` is false and `auto_hit_at_10` is true → usually `n` + `label_noise`

---

## Row 1

- **row_id:** `1`
- **question_id:** `qst_0002::metadata`
- **corpus_scale_size:** `20000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`other`

### Question

Who was the internal organizer listed for the security review call about an on-prem backup and audit log retention discussion with a healthcare customer in February 2025?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_aa97b7293f9f4f3c8180f645e4fe5911`
_source: full_erb_file:dsid_aa97b7293f9f4f3c8180f645e4fe5911__2025-02-11-onprem-backup-restore-and-audit-log-retention-security-review-meddata.txt_

```text
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

[00:18] Markus Klein: Cool. The goal today is to go through the on-prem backup and restore story for Redwood Private and then specifically audit log retention and what evidence you need for, you know, your auditors. We can keep it pretty tactical. Does that match what you want?

[00:33] Dana Wright: Yeah. We’re regulated healthcare. We have a pretty strict view on retention and chain-of-custody. We also have air-gap constraints in some sites.

[00:41] Aisha Rahman: Got it.

[00:42] Nina Gomez: And to be explicit, we don’t want any vendor-managed keys. Keys have to stay in our boundary.

[00:49] Hanae Suzuki: Understood.

[00:51] Markus Klein: Great. Maybe Eli, can you just level set the deployment you’re contemplating? Like, is this full air-gapped, or “restricted egress”?

[01:00] Eli Brooks: It’s a mix. Primary is on-prem in two data centers. One is pretty locked down — like, no outbound. The other can do limited egress through a proxy. Kubernetes on bare metal, we use an enterprise distro. Storage is mainly NFS and we have a… sort of S3-compatible appliance, but it’s not AWS.

[01:20] Markus Klein: Okay. That helps.

[01:22] Priya Shah: And retention-wise, we have to keep audit logs for seven years minimum. Some teams push for ten.

[01:29] Markus Klein: Okay.

[01:30] Aisha Rahman: One quick note before we get into details: Redwood Private is designed so you can run the control plane in your cluster/VPC, and you own the underlying storage and retention policies. We provide tooling to produce encrypted backup artifacts and to export audit logs, but you choose where they live and how long you keep them.

[01:50] Dana Wright: That’s fine, but we need to demonstrate that the process is “supported” and repeatable. Not like, “here’s a script, good luck.”

[01:58] Markus Klein: Totally. That’s actually what we’re building right now as part of Day-2 ops: runbooks, deterministic restore steps, validation checks.

[02:06] Nina Gomez: When you say deterministic, what do you mean? Like exact same cluster comes back?

[02:11] Hanae Suzuki: Deterministic in the sense that the backup has a manifest, versioned format, integrity checks, and the restore follows a defined order and reports what was restored. Not necessarily “byte-identical nodes,” but functionally consistent state: tenant configs, routing policies, auth config, etc.

[02:30] Priya Shah: Can we start with scope? What exactly is in the backup?

[02:34] Markus Klein: Yep. For Redwood Private we focus on the control-plane state and critical configuration. That typically includes our config database, object store metadata for control-plane artifacts, and the config that’s needed to redeploy deterministically — think Helm release values, versions, and Redwood-specific CRDs where applicable.

[02:54] Eli Brooks: Are you backing up Kubernetes itself? Like etcd snapshots?

[02:58] Markus Klein: Good question. We don’t automatically take cluster-wide etcd snapshots as part of Redwood’s backup. That’s generally considered cluster recovery and is handled by your Kubernetes ops process. Our runbooks will call out when etcd restore is the right tool versus application-level restore.

[03:15] Dana Wright: So if the cluster is gone, we rebuild Kubernetes and then restore Redwood state.

[03:19] Markus Klein: Exactly.

[03:20] Nina Gomez: What about secrets?

[03:22] Aisha Rahman: By default, we avoid backing up raw secret material. The philosophy is “backup references, not secrets,” where feasible. For example, we’ll capture references to your KMS key IDs, external secret manager paths, or Kubernetes Secret names, but not dump the secret values into the backup artifact.

[03:41] Nina Gomez: But if we lose the cluster, those Secrets are gone.

[03:44] Hanae Suzuki: Right, which is why we usually recommend secrets originate from your system-of-record: external secrets manager or an HSM-backed store, or at minimum your own Kubernetes secret backup process. For customers that do keep secrets only in cluster, we can document options, but it gets tricky for compliance because then you’re proliferating secret copies.

[04:05] Priya Shah: Our auditors will ask: does the backup contain PHI?

[04:09] Markus Klein: In the standard control plane backup, it should not include request payloads or model prompts. Audit logs can contain identifiers depending on how you configure them, and those are handled separately. The backup artifacts are primarily configuration and control plane state.

[04:23] Dana Wright: Okay. Now encryption. You said encrypted backup artifacts. How?

[04:28] Aisha Rahman: The pattern is envelope encryption. The backup artifact is packaged — typically a tarball plus a manifest — and encrypted with a data encryption key, a DEK. That DEK is then wrapped by a key encryption key, KEK, managed by your KMS or HSM. So the backup at rest is always encrypted, and you control the KEK.

[04:50] Nina Gomez: If the environment is air-gapped, how does KMS work?

[04:54] Hanae Suzuki: We support a provider interface. In cloud deployments it’s like AWS KMS. For on-prem, it depends on what you have — some customers have a local KMS service, some have HSMs with an API gateway. If you have an HSM that can do key wrap/unwrap operations, we can integrate through the provider layer, but we’ll need to validate your specific product.

[05:18] Eli Brooks: We have Thales. But access is… it’s locked down.

[05:22] Hanae Suzuki: That’s common. What we’d need from you is what operations are permitted and whether we can do unwrap during restore. Sometimes security teams allow wrap only in certain subnets.

[05:34] Dana Wright: Key rotation is mandatory annually. What happens to old backups?

[05:40] Aisha Rahman: Rotation is supported. Practically: backups created under an older KEK remain decryptable as long as you retain that KEK version or the ability to decrypt old wrapped DEKs. Many KMS/HSMs support key versioning. If you retire keys, you may need to rewrap. We can provide guidance: either keep key versions for the retention window, or periodically re-encrypt/rewrap backups to the latest key.

[06:05] Priya Shah: We might need a written statement there.

[06:08] Aisha Rahman: Yep, we’ll send it in writing.

[06:10] Nina Gomez: What about KMS downtime? Like, if the HSM is offline.

[06:15] Hanae Suzuki: Good call. If the KMS/HSM is unavailable at backup time, you have two options: fail the backup (safe default) or allow a temporary local key with strong warnings — but our default posture is to fail because otherwise you create a backup you can’t attest is encrypted under your KEK. During restore, if KMS/HSM is down, you can’t unwrap the DEK, so restore will fail until key service is available.

[06:43] Dana Wright: That’s acceptable.

[06:45] Eli Brooks: Is there a way to pre-stage the decrypt? Like, do unwrap ahead of time?

[06:50] Hanae Suzuki: Not recommended, because then you’re handling plaintext DEKs. We try to keep the DEK ephemeral in memory.

[06:58] Markus Klein: Shifting to retention and storage: you mentioned NFS and an S3-compatible appliance. Our tooling can write backup artifacts to S3-like object storage or NFS, depending on the config.

[07:10] Eli Brooks: NFS is easier here. Object storage appliance is slower and sometimes flakey.

[07:15] Markus Klein: That’s a common tradeoff. For compliance though, Priya, are you requiring immutable storage?

[07:21] Priya Shah: For audit logs, yes. For backups, not strictly immutable, but they need access controls and we need to show they weren’t tampered.

[07:30] Aisha Rahman: For tamper evidence, we rely on cryptographic integrity checks: the manifest includes checksums for each component and we can also sign the manifest as part of the offline bundle signing process. If you store artifacts in immutable/WORM storage, that’s even stronger. On NFS you can approximate immutability with permissions and snapshots, but it’s not the same as object lock.

[07:55] Nina Gomez: When you say sign, is that GPG?

[07:58] Markus Klein: For on-prem bundle distribution, yes, we ship signed artifacts with a checksum manifest, and you verify signatures offline. For backup artifacts themselves, we can include checksums and optionally sign the manifest using a key you trust, depending on your policy. We can talk through what fits.

[08:16] Dana Wright: Our auditors will ask “who can modify backups” and “prove restore was tested.”

[08:22] Markus Klein: Right.

[08:23] Aisha Rahman: On “who can modify”: access controls are enforced by your storage backend and Kubernetes RBAC for the job that writes backups. We recommend least privilege: a service account that can read the necessary config/state and write-only to the backup location (append-only if supported). For “prove restore was tested,” we can generate a restore validation report: timestamps, versions, checksums verified, and health checks run.

[08:50] Priya Shah: Would that report be something we can hand to an auditor?

[08:54] Markus Klein: That’s the idea. It’s not a formal attestation, but it’s evidence from the system.

[09:01] Nina Gomez: Health checks meaning what exactly?

[09:04] Hanae Suzuki: Post-restore validations like: control plane API readiness, can you list tenants, can you fetch routing policy config, does auth config load, does it connect to dependencies, and optionally a smoke inference call if the data plane is present.

[09:21] Eli Brooks: Are you restoring data plane too?

[09:23] Markus Klein: Typically the data plane is stateless. You redeploy it from declarative config. The important part is capturing the config that pins model versions, routing policies, and your deployment settings.

[09:38] Dana Wright: Okay. Now audit logs. We need audit logs retained 7 years, and we need them exportable. What do you support?

[09:48] Aisha Rahman: Redwood Private emits audit events for control plane actions — config changes, auth changes, admin actions, etc. Those can be exported via an audit log exporter in batch mode. The export can land in your storage (again, NFS or object storage) and you control retention.

[10:09] Priya Shah: What format?

[10:11] Aisha Rahman: Typically JSON lines (one event per line) with stable fields: timestamp, actor, action, resource, result, and correlation IDs. We can provide a schema doc.

[10:25] Nina Gomez: Does it include request content? Prompts?

[10:28] Aisha Rahman: No prompt bodies by default in audit logs. We focus on administrative and control plane events. For data plane requests, you can enable request logging separately but that’s usually discouraged for PHI.

[10:42] Dana Wright: We will not log prompts, period.

[10:45] Markus Klein: Understood.

[10:46] Eli Brooks: Is there a way to send audit logs to our SIEM instead of file exports?

[10:51] Markus Klein: In many deployments, yes — via syslog/HTTP collectors, depending on your environment. For the backup/retention conversation today we’re focused on the batch export for long-term retention, but we can also integrate with SIEM for near real-time.

[11:10] Priya Shah: For seven years, we usually want WORM. If we store JSONL on NFS, that’s not WORM.

[11:16] Aisha Rahman: Correct. If WORM is a hard requirement, we recommend an immutable object storage mechanism. Some on-prem appliances support object lock semantics, or you can use storage snapshots with governance controls, but again, it depends. We can provide recommended patterns: (1) export to object storage with immutability, or (2) export to NFS and then replicate to your compliance archive system.

[11:39] Dana Wright: Who owns the replication step?

[11:41] Markus Klein: You would, typically. Redwood’s responsibility is to produce the export and document how to automate it; your team controls the archival system.

[11:52] Nina Gomez: Evidence: can you show that the export ran and didn’t skip events? Like pagination bugs.

[11:59] Aisha Rahman: Great point. The exporter uses cursoring/pagination safeguards and emits metrics: last exported timestamp, counts, and error codes. We can also include a “gap detection” check — if there’s a hole in sequence or time windows, it flags.

[12:20] Eli Brooks: Metrics as in Prometheus?

[12:22] Markus Klein: Yes, Prometheus-style metrics, and dashboards/alerts if you deploy the observability pack.

[12:29] Priya Shah: And those dashboards can be used as evidence?

[12:33] Aisha Rahman: Screenshots can be included, but better is exporting the metrics data or logs. We can advise what other customers do: keep a quarterly restore drill report plus metrics exports and change tickets.

[12:50] Dana Wright: You mentioned restore drills. Do you recommend a cadence?

[12:54] Markus Klein: Common is quarterly for regulated environments, sometimes monthly in staging. We also see customers do a “tabletop” monthly and full technical restore quarterly.

[13:08] Eli Brooks: Restoring into the same cluster or a clean cluster?

[13:11] Markus Klein: Clean cluster is preferred for DR validation. That proves you can rebuild from nothing.

[13:17] Nina Gomez: But for us that’s heavy.

[13:19] Markus Klein: Yep, it’s an investment. We can keep the restore target smaller — like a minimal control plane footprint — but still validate the critical path.

[13:32] Priya Shah: Okay. One detail: do your backups include Kubernetes manifests or Helm values?

[13:38] Markus Klein: The toolkit captures the Helm release values and versions for Redwood-managed components, because that’s needed to redeploy. It does not generally sweep the entire cluster.

[13:50] Eli Brooks: What about CRDs? We had a vendor restore fail once because CRDs weren’t installed.

[13:56] Hanae Suzuki: Yep, that’s a known sharp edge. Our restore runbook includes a pre-flight: confirm required CRDs exist at the expected versions before applying restore. And if they don’t, it tells you what to install first.

[14:12] Dana Wright: That’s important.

[14:13] Markus Klein: 100%.

[14:15] Nina Gomez: I want to circle back to “backup doesn’t include secrets.” If secrets are in our vault, fine. If secrets are in Kubernetes Secrets, we need a plan.

[14:25] Hanae Suzuki: Agreed. We can provide two patterns: (1) recommended: external secrets manager so secrets are rehydrated on redeploy, or (2) if you must, use a Kubernetes secret backup solution in your cluster DR plan. Redwood won’t discourage it, but we won’t bundle secret plaintext into our backups by default.

[14:47] Priya Shah: For audit scope, we also need to know where encryption happens and whether anything is ever written unencrypted to disk.

[14:55] Aisha Rahman: For backup artifacts: encryption happens before the artifact is persisted to the target backend. Temp files can exist depending on your configuration, but the intent is to keep plaintext minimal and ephemeral. We can document the exact behavior and recommended settings to avoid plaintext on disk.

[15:16] Eli Brooks: Is there streaming encryption? Or does it write then encrypt?

[15:20] Hanae Suzuki: Implementation is streaming where possible, but some components may stage data in a temp directory. We’ll call that out with a secure default: encrypted temp volume or memory-backed where feasible.

[15:36] Dana Wright: If our auditors ask, we need that spelled out.

[15:39] Aisha Rahman: Understood.

[15:41] Markus Klein: Let’s talk evidence pack. Priya, what do you typically need for an audit?

[15:47] Priya Shah: We need policies and procedures, plus evidence of execution. For example: a ticket that says “restore drill performed,” logs showing it, and sign-off. For backups: proof backups ran, proof they’re encrypted, proof retention is applied.

[16:05] Markus Klein: Makes sense.

[16:07] Aisha Rahman: Redwood can provide: (a) runbooks, (b) output logs from backup jobs including backup IDs and checksum verification, (c) a manifest per backup with format version, component list, and checksums, (d) restore validation report output, and (e) metrics that show backup success/failure and duration.

[16:29] Nina Gomez: Do you have SOC 2?

[16:31] Markus Klein: Redwood the company does, yes, but for Redwood Private on-prem it’s still your environment. We can share the SOC 2 report under NDA, but it doesn’t replace your controls.

[16:43] Dana Wright: Right, we understand.

[16:45] Eli Brooks: On retention controls: can the system automatically delete old backups? Or do we manage it?

[16:51] Markus Klein: There’s a retention policy option in the scheduled backup job — like “keep N days” — but in regulated environments we usually advise that retention is enforced by the storage backend lifecycle policy, because it’s harder to tamper with.

[17:08] Priya Shah: Deletion is sensitive. We might require dual control.

[17:12] Aisha Rahman: Exactly. Storage-side lifecycle with approval is better.

[17:17] Nina Gomez: Can you prevent operators from restoring an old backup to exfiltrate data?

[17:22] Aisha Rahman: Restore should be gated by RBAC and audit logged. Also, since backups are encrypted with your keys, anyone who can restore must also have access to unwrap keys — that’s your HSM policy. We strongly recommend separating duties: operators can run the job but can’t access keys.

[17:46] Dana Wright: Good.

[17:48] Eli Brooks: About the air-gapped bundle — you mentioned signed artifacts. How do updates work? We can’t pull from the internet.

[17:56] Markus Klein: We provide an offline bundle with deterministic layout and signature verification steps. You import it into your environment. Updates are delivered as new signed bundles. No external calls during install.

[18:12] Priya Shah: Do the backup scripts depend on external containers?

[18:16] Markus Klein: In on-prem mode, everything needed is inside the bundle, including container images if required, and the checksums manifest to verify.

[18:25] Nina Gomez: Are you calling out to any hosted endpoints for telemetry?

[18:29] Markus Klein: Not in air-gapped mode. Telemetry is optional and can be disabled. For your environment, we assume disabled.

[18:38] Dana Wright: Okay.

[18:40] Markus Klein: I want to make sure we answer the “etcd restore vs app restore” question. Eli asked earlier. The general guidance is: etcd snapshots are for cluster-level recovery if your Kubernetes control plane is corrupted. But for DR where you lose a cluster, you rebuild Kubernetes clean and then restore Redwood control plane state using our workflow. If you have etcd and Redwood both, you can end up with conflicts if you restore etcd from a snapshot that includes stale resources.

[19:10] Eli Brooks: Yeah, we’ve seen that. CRDs and old finalizers.

[19:13] Hanae Suzuki: Exactly.

[19:14] Priya Shah: So from an evidence perspective, would you recommend we document both procedures?

[19:19] Markus Klein: Yes. Two runbooks: one for cluster recovery (your infra team) and one for Redwood application restore.

[19:27] Dana Wright: And audit logs… if the cluster is gone, do we lose audit logs not yet exported?

[19:33] Aisha Rahman: If audit logs are stored locally before export, yes, there’s a risk window. Best practice is near real-time export to your durable storage/SIEM, plus batch exports for long-term. We can talk about reducing RPO for audit logs by increasing export frequency.

[19:54] Nina Gomez: For us, audit log RPO needs to be like minutes, not days.

[19:58] Markus Klein: Then we’ll design it as streaming to SIEM plus periodic archive.

[20:03] Priya Shah: Okay. One more: do you support time sync requirements? We’ve had issues with clock skew messing with evidence.

[20:10] Hanae Suzuki: We recommend NTP and we can add a pre-flight check for time sync drift. If drift is beyond a threshold, backup/export warns or fails.

[20:23] Eli Brooks: Good.

[20:24] Markus Klein: We’re at about halfway. Dana, anything not covered?

[20:29] Dana Wright: I want to know: can you provide a “statement of support” that these procedures are supported by Redwood, not just community best effort.

[20:38] Markus Klein: Yes, for the Private offering we will have supported runbooks and we’ll define the support boundaries. For example: we support the Redwood backup/restore workflow; we don’t support your NFS vendor. But we can help triage.

[20:53] Dana Wright: That’s acceptable.

[20:56] Priya Shah: I’d also like an explicit answer on whether any secrets are ever included in backups. Even accidentally.

[21:03] Aisha Rahman: The design intent: do not include secret material. The tooling can be configured to exclude Kubernetes Secrets and to only include references. We’ll provide a written configuration and a validation step: backup verification checks the manifest for forbidden resource types.

[21:23] Nina Gomez: That’s good. Also make sure that if someone misconfigures it, it doesn’t silently include secrets.

[21:29] Hanae Suzuki: Agreed. Secure-by-default is “exclude,” with a very explicit opt-in if ever allowed.

[21:39] Eli Brooks: Another practical question: backup size. Are we talking gigabytes?

[21:44] Markus Klein: Control plane backups are typically not huge — depends on config DB size. But audit logs over years can be massive, which is why we separate “backup” from “audit archive.”

[21:56] Priya Shah: We compress logs and encrypt them. Can we do that with your exporter?

[22:02] Aisha Rahman: Yes, export can be compressed and encrypted. For encryption, we recommend using the same envelope pattern with your keys.

[22:12] Dana Wright: Okay.

[22:13] Markus Klein: I think we should move to next steps. But before that, any competitor comparisons you’re weighing? Just so we understand.

[22:21] Dana Wright: We’re looking at a self-hosted vLLM stack and also some cloud options like Azure OpenAI, but cloud is hard for PHI.

[22:30] Markus Klein: Yep.

[22:31] Nina Gomez: Bedrock was discussed too, but again, data residency is tough.

[22:35] Markus Klein: Understood.

[22:37] Aisha Rahman: From a security stance, on-prem gives you full control, but it also means your DR and retention controls are yours to operate. What we’re trying to do is make that operationally realistic.

[22:51] Priya Shah: Okay. Can you send a sample of the restore validation report? Like what fields we’d see.

[22:56] Markus Klein: Yes.

[22:57] Hanae Suzuki: We can include: backup ID, backup format version, components restored, checksum verification status, KMS provider used (not keys), and post-restore checks.

[23:11] Dana Wright: And for audit logs, we’ll need the schema.

[23:14] Aisha Rahman: We’ll send schema and an example export file.

[23:18] Markus Klein: Great. Anything else?

[23:20] Eli Brooks: Just one: If we do NFS for backups, what are the permission requirements? We want least privilege.

[23:26] Markus Klein: We’ll provide recommended NFS export options and an RBAC policy for the backup service account. Also we can flag insecure mount options.

[23:36] Eli Brooks: Perfect.

[23:38] Markus Klein: Alright, recap. We’ll send: written envelope encryption note, sample manifest, sample restore report, audit log schema + exporter behavior, and recommended retention/immutability patterns. You’ll confirm retention (7 vs 10) and storage target details and HSM constraints. We’ll schedule a follow-up technical session on the HSM provider integration.

[23:59] Dana Wright: Sounds good.

[24:01] Priya Shah: Thanks.

[24:02] Nina Gomez: Thank you.

[24:03] Eli Brooks: Thanks.

[24:04] Markus Klein: Thanks everyone.

(Note: transcript truncation - Fireflies sometimes stops labeling timestamps after ~25 minutes; remainder of call contained continued Q&A on HSM constraints, export cadence, and internal MedData audit evidence workflow, with no additional decisions beyond the recap above.)
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_52dc2b5dcfe44149b98a30b4345ee03e` — AxiomCare Guardian Networks
2. `dsid_b896f53a79d44d3e821d793922b445df` — HolisticSpark Care Co
3. `dsid_4dc77de6649d4e0799648a18290d96b5` — BlueCrest Secure Support
4. `dsid_23899e82cf1c443e94b7d2cde199f08f` — Admin telemetry extraction & retention sync - Cascade Financial
5. `dsid_573ca1fc195e450e85e3f10d1a068cf6` — HelmBridge Healthcare
6. `dsid_e312cfbed0c149f39f147813ace0ff09` — Sapphire Harbor Ops
7. `dsid_ea23b1139d4141c483f46443089031e0` — Sable Counsel LLC
8. `dsid_97c88c6d322d4a09b28cbd9b294c8035` — Baycrest Care Coaching
9. `dsid_22938cefdddd421fad44fecd5fddef95` — Sensitive logs intake: prioritization ladder & legal routing for redaction, retention, export
10. `dsid_a89e842138d4471ea632c42f5d8c33b4` — Sunshadow Health Solutions

### Fill for this row (also include in final JSON array)

```
row_id: 1
question_id: qst_0002::metadata
corpus_scale_size: 20000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 2

- **row_id:** `2`
- **question_id:** `qst_0002::metadata`
- **corpus_scale_size:** `100000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

Who was the internal organizer listed for the security review call about an on-prem backup and audit log retention discussion with a healthcare customer in February 2025?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_aa97b7293f9f4f3c8180f645e4fe5911`
_source: full_erb_file:dsid_aa97b7293f9f4f3c8180f645e4fe5911__2025-02-11-onprem-backup-restore-and-audit-log-retention-security-review-meddata.txt_

```text
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

[00:18] Markus Klein: Cool. The goal today is to go through the on-prem backup and restore story for Redwood Private and then specifically audit log retention and what evidence you need for, you know, your auditors. We can keep it pretty tactical. Does that match what you want?

[00:33] Dana Wright: Yeah. We’re regulated healthcare. We have a pretty strict view on retention and chain-of-custody. We also have air-gap constraints in some sites.

[00:41] Aisha Rahman: Got it.

[00:42] Nina Gomez: And to be explicit, we don’t want any vendor-managed keys. Keys have to stay in our boundary.

[00:49] Hanae Suzuki: Understood.

[00:51] Markus Klein: Great. Maybe Eli, can you just level set the deployment you’re contemplating? Like, is this full air-gapped, or “restricted egress”?

[01:00] Eli Brooks: It’s a mix. Primary is on-prem in two data centers. One is pretty locked down — like, no outbound. The other can do limited egress through a proxy. Kubernetes on bare metal, we use an enterprise distro. Storage is mainly NFS and we have a… sort of S3-compatible appliance, but it’s not AWS.

[01:20] Markus Klein: Okay. That helps.

[01:22] Priya Shah: And retention-wise, we have to keep audit logs for seven years minimum. Some teams push for ten.

[01:29] Markus Klein: Okay.

[01:30] Aisha Rahman: One quick note before we get into details: Redwood Private is designed so you can run the control plane in your cluster/VPC, and you own the underlying storage and retention policies. We provide tooling to produce encrypted backup artifacts and to export audit logs, but you choose where they live and how long you keep them.

[01:50] Dana Wright: That’s fine, but we need to demonstrate that the process is “supported” and repeatable. Not like, “here’s a script, good luck.”

[01:58] Markus Klein: Totally. That’s actually what we’re building right now as part of Day-2 ops: runbooks, deterministic restore steps, validation checks.

[02:06] Nina Gomez: When you say deterministic, what do you mean? Like exact same cluster comes back?

[02:11] Hanae Suzuki: Deterministic in the sense that the backup has a manifest, versioned format, integrity checks, and the restore follows a defined order and reports what was restored. Not necessarily “byte-identical nodes,” but functionally consistent state: tenant configs, routing policies, auth config, etc.

[02:30] Priya Shah: Can we start with scope? What exactly is in the backup?

[02:34] Markus Klein: Yep. For Redwood Private we focus on the control-plane state and critical configuration. That typically includes our config database, object store metadata for control-plane artifacts, and the config that’s needed to redeploy deterministically — think Helm release values, versions, and Redwood-specific CRDs where applicable.

[02:54] Eli Brooks: Are you backing up Kubernetes itself? Like etcd snapshots?

[02:58] Markus Klein: Good question. We don’t automatically take cluster-wide etcd snapshots as part of Redwood’s backup. That’s generally considered cluster recovery and is handled by your Kubernetes ops process. Our runbooks will call out when etcd restore is the right tool versus application-level restore.

[03:15] Dana Wright: So if the cluster is gone, we rebuild Kubernetes and then restore Redwood state.

[03:19] Markus Klein: Exactly.

[03:20] Nina Gomez: What about secrets?

[03:22] Aisha Rahman: By default, we avoid backing up raw secret material. The philosophy is “backup references, not secrets,” where feasible. For example, we’ll capture references to your KMS key IDs, external secret manager paths, or Kubernetes Secret names, but not dump the secret values into the backup artifact.

[03:41] Nina Gomez: But if we lose the cluster, those Secrets are gone.

[03:44] Hanae Suzuki: Right, which is why we usually recommend secrets originate from your system-of-record: external secrets manager or an HSM-backed store, or at minimum your own Kubernetes secret backup process. For customers that do keep secrets only in cluster, we can document options, but it gets tricky for compliance because then you’re proliferating secret copies.

[04:05] Priya Shah: Our auditors will ask: does the backup contain PHI?

[04:09] Markus Klein: In the standard control plane backup, it should not include request payloads or model prompts. Audit logs can contain identifiers depending on how you configure them, and those are handled separately. The backup artifacts are primarily configuration and control plane state.

[04:23] Dana Wright: Okay. Now encryption. You said encrypted backup artifacts. How?

[04:28] Aisha Rahman: The pattern is envelope encryption. The backup artifact is packaged — typically a tarball plus a manifest — and encrypted with a data encryption key, a DEK. That DEK is then wrapped by a key encryption key, KEK, managed by your KMS or HSM. So the backup at rest is always encrypted, and you control the KEK.

[04:50] Nina Gomez: If the environment is air-gapped, how does KMS work?

[04:54] Hanae Suzuki: We support a provider interface. In cloud deployments it’s like AWS KMS. For on-prem, it depends on what you have — some customers have a local KMS service, some have HSMs with an API gateway. If you have an HSM that can do key wrap/unwrap operations, we can integrate through the provider layer, but we’ll need to validate your specific product.

[05:18] Eli Brooks: We have Thales. But access is… it’s locked down.

[05:22] Hanae Suzuki: That’s common. What we’d need from you is what operations are permitted and whether we can do unwrap during restore. Sometimes security teams allow wrap only in certain subnets.

[05:34] Dana Wright: Key rotation is mandatory annually. What happens to old backups?

[05:40] Aisha Rahman: Rotation is supported. Practically: backups created under an older KEK remain decryptable as long as you retain that KEK version or the ability to decrypt old wrapped DEKs. Many KMS/HSMs support key versioning. If you retire keys, you may need to rewrap. We can provide guidance: either keep key versions for the retention window, or periodically re-encrypt/rewrap backups to the latest key.

[06:05] Priya Shah: We might need a written statement there.

[06:08] Aisha Rahman: Yep, we’ll send it in writing.

[06:10] Nina Gomez: What about KMS downtime? Like, if the HSM is offline.

[06:15] Hanae Suzuki: Good call. If the KMS/HSM is unavailable at backup time, you have two options: fail the backup (safe default) or allow a temporary local key with strong warnings — but our default posture is to fail because otherwise you create a backup you can’t attest is encrypted under your KEK. During restore, if KMS/HSM is down, you can’t unwrap the DEK, so restore will fail until key service is available.

[06:43] Dana Wright: That’s acceptable.

[06:45] Eli Brooks: Is there a way to pre-stage the decrypt? Like, do unwrap ahead of time?

[06:50] Hanae Suzuki: Not recommended, because then you’re handling plaintext DEKs. We try to keep the DEK ephemeral in memory.

[06:58] Markus Klein: Shifting to retention and storage: you mentioned NFS and an S3-compatible appliance. Our tooling can write backup artifacts to S3-like object storage or NFS, depending on the config.

[07:10] Eli Brooks: NFS is easier here. Object storage appliance is slower and sometimes flakey.

[07:15] Markus Klein: That’s a common tradeoff. For compliance though, Priya, are you requiring immutable storage?

[07:21] Priya Shah: For audit logs, yes. For backups, not strictly immutable, but they need access controls and we need to show they weren’t tampered.

[07:30] Aisha Rahman: For tamper evidence, we rely on cryptographic integrity checks: the manifest includes checksums for each component and we can also sign the manifest as part of the offline bundle signing process. If you store artifacts in immutable/WORM storage, that’s even stronger. On NFS you can approximate immutability with permissions and snapshots, but it’s not the same as object lock.

[07:55] Nina Gomez: When you say sign, is that GPG?

[07:58] Markus Klein: For on-prem bundle distribution, yes, we ship signed artifacts with a checksum manifest, and you verify signatures offline. For backup artifacts themselves, we can include checksums and optionally sign the manifest using a key you trust, depending on your policy. We can talk through what fits.

[08:16] Dana Wright: Our auditors will ask “who can modify backups” and “prove restore was tested.”

[08:22] Markus Klein: Right.

[08:23] Aisha Rahman: On “who can modify”: access controls are enforced by your storage backend and Kubernetes RBAC for the job that writes backups. We recommend least privilege: a service account that can read the necessary config/state and write-only to the backup location (append-only if supported). For “prove restore was tested,” we can generate a restore validation report: timestamps, versions, checksums verified, and health checks run.

[08:50] Priya Shah: Would that report be something we can hand to an auditor?

[08:54] Markus Klein: That’s the idea. It’s not a formal attestation, but it’s evidence from the system.

[09:01] Nina Gomez: Health checks meaning what exactly?

[09:04] Hanae Suzuki: Post-restore validations like: control plane API readiness, can you list tenants, can you fetch routing policy config, does auth config load, does it connect to dependencies, and optionally a smoke inference call if the data plane is present.

[09:21] Eli Brooks: Are you restoring data plane too?

[09:23] Markus Klein: Typically the data plane is stateless. You redeploy it from declarative config. The important part is capturing the config that pins model versions, routing policies, and your deployment settings.

[09:38] Dana Wright: Okay. Now audit logs. We need audit logs retained 7 years, and we need them exportable. What do you support?

[09:48] Aisha Rahman: Redwood Private emits audit events for control plane actions — config changes, auth changes, admin actions, etc. Those can be exported via an audit log exporter in batch mode. The export can land in your storage (again, NFS or object storage) and you control retention.

[10:09] Priya Shah: What format?

[10:11] Aisha Rahman: Typically JSON lines (one event per line) with stable fields: timestamp, actor, action, resource, result, and correlation IDs. We can provide a schema doc.

[10:25] Nina Gomez: Does it include request content? Prompts?

[10:28] Aisha Rahman: No prompt bodies by default in audit logs. We focus on administrative and control plane events. For data plane requests, you can enable request logging separately but that’s usually discouraged for PHI.

[10:42] Dana Wright: We will not log prompts, period.

[10:45] Markus Klein: Understood.

[10:46] Eli Brooks: Is there a way to send audit logs to our SIEM instead of file exports?

[10:51] Markus Klein: In many deployments, yes — via syslog/HTTP collectors, depending on your environment. For the backup/retention conversation today we’re focused on the batch export for long-term retention, but we can also integrate with SIEM for near real-time.

[11:10] Priya Shah: For seven years, we usually want WORM. If we store JSONL on NFS, that’s not WORM.

[11:16] Aisha Rahman: Correct. If WORM is a hard requirement, we recommend an immutable object storage mechanism. Some on-prem appliances support object lock semantics, or you can use storage snapshots with governance controls, but again, it depends. We can provide recommended patterns: (1) export to object storage with immutability, or (2) export to NFS and then replicate to your compliance archive system.

[11:39] Dana Wright: Who owns the replication step?

[11:41] Markus Klein: You would, typically. Redwood’s responsibility is to produce the export and document how to automate it; your team controls the archival system.

[11:52] Nina Gomez: Evidence: can you show that the export ran and didn’t skip events? Like pagination bugs.

[11:59] Aisha Rahman: Great point. The exporter uses cursoring/pagination safeguards and emits metrics: last exported timestamp, counts, and error codes. We can also include a “gap detection” check — if there’s a hole in sequence or time windows, it flags.

[12:20] Eli Brooks: Metrics as in Prometheus?

[12:22] Markus Klein: Yes, Prometheus-style metrics, and dashboards/alerts if you deploy the observability pack.

[12:29] Priya Shah: And those dashboards can be used as evidence?

[12:33] Aisha Rahman: Screenshots can be included, but better is exporting the metrics data or logs. We can advise what other customers do: keep a quarterly restore drill report plus metrics exports and change tickets.

[12:50] Dana Wright: You mentioned restore drills. Do you recommend a cadence?

[12:54] Markus Klein: Common is quarterly for regulated environments, sometimes monthly in staging. We also see customers do a “tabletop” monthly and full technical restore quarterly.

[13:08] Eli Brooks: Restoring into the same cluster or a clean cluster?

[13:11] Markus Klein: Clean cluster is preferred for DR validation. That proves you can rebuild from nothing.

[13:17] Nina Gomez: But for us that’s heavy.

[13:19] Markus Klein: Yep, it’s an investment. We can keep the restore target smaller — like a minimal control plane footprint — but still validate the critical path.

[13:32] Priya Shah: Okay. One detail: do your backups include Kubernetes manifests or Helm values?

[13:38] Markus Klein: The toolkit captures the Helm release values and versions for Redwood-managed components, because that’s needed to redeploy. It does not generally sweep the entire cluster.

[13:50] Eli Brooks: What about CRDs? We had a vendor restore fail once because CRDs weren’t installed.

[13:56] Hanae Suzuki: Yep, that’s a known sharp edge. Our restore runbook includes a pre-flight: confirm required CRDs exist at the expected versions before applying restore. And if they don’t, it tells you what to install first.

[14:12] Dana Wright: That’s important.

[14:13] Markus Klein: 100%.

[14:15] Nina Gomez: I want to circle back to “backup doesn’t include secrets.” If secrets are in our vault, fine. If secrets are in Kubernetes Secrets, we need a plan.

[14:25] Hanae Suzuki: Agreed. We can provide two patterns: (1) recommended: external secrets manager so secrets are rehydrated on redeploy, or (2) if you must, use a Kubernetes secret backup solution in your cluster DR plan. Redwood won’t discourage it, but we won’t bundle secret plaintext into our backups by default.

[14:47] Priya Shah: For audit scope, we also need to know where encryption happens and whether anything is ever written unencrypted to disk.

[14:55] Aisha Rahman: For backup artifacts: encryption happens before the artifact is persisted to the target backend. Temp files can exist depending on your configuration, but the intent is to keep plaintext minimal and ephemeral. We can document the exact behavior and recommended settings to avoid plaintext on disk.

[15:16] Eli Brooks: Is there streaming encryption? Or does it write then encrypt?

[15:20] Hanae Suzuki: Implementation is streaming where possible, but some components may stage data in a temp directory. We’ll call that out with a secure default: encrypted temp volume or memory-backed where feasible.

[15:36] Dana Wright: If our auditors ask, we need that spelled out.

[15:39] Aisha Rahman: Understood.

[15:41] Markus Klein: Let’s talk evidence pack. Priya, what do you typically need for an audit?

[15:47] Priya Shah: We need policies and procedures, plus evidence of execution. For example: a ticket that says “restore drill performed,” logs showing it, and sign-off. For backups: proof backups ran, proof they’re encrypted, proof retention is applied.

[16:05] Markus Klein: Makes sense.

[16:07] Aisha Rahman: Redwood can provide: (a) runbooks, (b) output logs from backup jobs including backup IDs and checksum verification, (c) a manifest per backup with format version, component list, and checksums, (d) restore validation report output, and (e) metrics that show backup success/failure and duration.

[16:29] Nina Gomez: Do you have SOC 2?

[16:31] Markus Klein: Redwood the company does, yes, but for Redwood Private on-prem it’s still your environment. We can share the SOC 2 report under NDA, but it doesn’t replace your controls.

[16:43] Dana Wright: Right, we understand.

[16:45] Eli Brooks: On retention controls: can the system automatically delete old backups? Or do we manage it?

[16:51] Markus Klein: There’s a retention policy option in the scheduled backup job — like “keep N days” — but in regulated environments we usually advise that retention is enforced by the storage backend lifecycle policy, because it’s harder to tamper with.

[17:08] Priya Shah: Deletion is sensitive. We might require dual control.

[17:12] Aisha Rahman: Exactly. Storage-side lifecycle with approval is better.

[17:17] Nina Gomez: Can you prevent operators from restoring an old backup to exfiltrate data?

[17:22] Aisha Rahman: Restore should be gated by RBAC and audit logged. Also, since backups are encrypted with your keys, anyone who can restore must also have access to unwrap keys — that’s your HSM policy. We strongly recommend separating duties: operators can run the job but can’t access keys.

[17:46] Dana Wright: Good.

[17:48] Eli Brooks: About the air-gapped bundle — you mentioned signed artifacts. How do updates work? We can’t pull from the internet.

[17:56] Markus Klein: We provide an offline bundle with deterministic layout and signature verification steps. You import it into your environment. Updates are delivered as new signed bundles. No external calls during install.

[18:12] Priya Shah: Do the backup scripts depend on external containers?

[18:16] Markus Klein: In on-prem mode, everything needed is inside the bundle, including container images if required, and the checksums manifest to verify.

[18:25] Nina Gomez: Are you calling out to any hosted endpoints for telemetry?

[18:29] Markus Klein: Not in air-gapped mode. Telemetry is optional and can be disabled. For your environment, we assume disabled.

[18:38] Dana Wright: Okay.

[18:40] Markus Klein: I want to make sure we answer the “etcd restore vs app restore” question. Eli asked earlier. The general guidance is: etcd snapshots are for cluster-level recovery if your Kubernetes control plane is corrupted. But for DR where you lose a cluster, you rebuild Kubernetes clean and then restore Redwood control plane state using our workflow. If you have etcd and Redwood both, you can end up with conflicts if you restore etcd from a snapshot that includes stale resources.

[19:10] Eli Brooks: Yeah, we’ve seen that. CRDs and old finalizers.

[19:13] Hanae Suzuki: Exactly.

[19:14] Priya Shah: So from an evidence perspective, would you recommend we document both procedures?

[19:19] Markus Klein: Yes. Two runbooks: one for cluster recovery (your infra team) and one for Redwood application restore.

[19:27] Dana Wright: And audit logs… if the cluster is gone, do we lose audit logs not yet exported?

[19:33] Aisha Rahman: If audit logs are stored locally before export, yes, there’s a risk window. Best practice is near real-time export to your durable storage/SIEM, plus batch exports for long-term. We can talk about reducing RPO for audit logs by increasing export frequency.

[19:54] Nina Gomez: For us, audit log RPO needs to be like minutes, not days.

[19:58] Markus Klein: Then we’ll design it as streaming to SIEM plus periodic archive.

[20:03] Priya Shah: Okay. One more: do you support time sync requirements? We’ve had issues with clock skew messing with evidence.

[20:10] Hanae Suzuki: We recommend NTP and we can add a pre-flight check for time sync drift. If drift is beyond a threshold, backup/export warns or fails.

[20:23] Eli Brooks: Good.

[20:24] Markus Klein: We’re at about halfway. Dana, anything not covered?

[20:29] Dana Wright: I want to know: can you provide a “statement of support” that these procedures are supported by Redwood, not just community best effort.

[20:38] Markus Klein: Yes, for the Private offering we will have supported runbooks and we’ll define the support boundaries. For example: we support the Redwood backup/restore workflow; we don’t support your NFS vendor. But we can help triage.

[20:53] Dana Wright: That’s acceptable.

[20:56] Priya Shah: I’d also like an explicit answer on whether any secrets are ever included in backups. Even accidentally.

[21:03] Aisha Rahman: The design intent: do not include secret material. The tooling can be configured to exclude Kubernetes Secrets and to only include references. We’ll provide a written configuration and a validation step: backup verification checks the manifest for forbidden resource types.

[21:23] Nina Gomez: That’s good. Also make sure that if someone misconfigures it, it doesn’t silently include secrets.

[21:29] Hanae Suzuki: Agreed. Secure-by-default is “exclude,” with a very explicit opt-in if ever allowed.

[21:39] Eli Brooks: Another practical question: backup size. Are we talking gigabytes?

[21:44] Markus Klein: Control plane backups are typically not huge — depends on config DB size. But audit logs over years can be massive, which is why we separate “backup” from “audit archive.”

[21:56] Priya Shah: We compress logs and encrypt them. Can we do that with your exporter?

[22:02] Aisha Rahman: Yes, export can be compressed and encrypted. For encryption, we recommend using the same envelope pattern with your keys.

[22:12] Dana Wright: Okay.

[22:13] Markus Klein: I think we should move to next steps. But before that, any competitor comparisons you’re weighing? Just so we understand.

[22:21] Dana Wright: We’re looking at a self-hosted vLLM stack and also some cloud options like Azure OpenAI, but cloud is hard for PHI.

[22:30] Markus Klein: Yep.

[22:31] Nina Gomez: Bedrock was discussed too, but again, data residency is tough.

[22:35] Markus Klein: Understood.

[22:37] Aisha Rahman: From a security stance, on-prem gives you full control, but it also means your DR and retention controls are yours to operate. What we’re trying to do is make that operationally realistic.

[22:51] Priya Shah: Okay. Can you send a sample of the restore validation report? Like what fields we’d see.

[22:56] Markus Klein: Yes.

[22:57] Hanae Suzuki: We can include: backup ID, backup format version, components restored, checksum verification status, KMS provider used (not keys), and post-restore checks.

[23:11] Dana Wright: And for audit logs, we’ll need the schema.

[23:14] Aisha Rahman: We’ll send schema and an example export file.

[23:18] Markus Klein: Great. Anything else?

[23:20] Eli Brooks: Just one: If we do NFS for backups, what are the permission requirements? We want least privilege.

[23:26] Markus Klein: We’ll provide recommended NFS export options and an RBAC policy for the backup service account. Also we can flag insecure mount options.

[23:36] Eli Brooks: Perfect.

[23:38] Markus Klein: Alright, recap. We’ll send: written envelope encryption note, sample manifest, sample restore report, audit log schema + exporter behavior, and recommended retention/immutability patterns. You’ll confirm retention (7 vs 10) and storage target details and HSM constraints. We’ll schedule a follow-up technical session on the HSM provider integration.

[23:59] Dana Wright: Sounds good.

[24:01] Priya Shah: Thanks.

[24:02] Nina Gomez: Thank you.

[24:03] Eli Brooks: Thanks.

[24:04] Markus Klein: Thanks everyone.

(Note: transcript truncation - Fireflies sometimes stops labeling timestamps after ~25 minutes; remainder of call contained continued Q&A on HSM constraints, export cadence, and internal MedData audit evidence workflow, with no additional decisions beyond the recap above.)
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_03bea1fa6f944d479b97f6c30123c252` — MedData Systems
2. `dsid_e5307f0e837d43cbbf8fc9c954e198cf` — Northbridge Health
3. `dsid_ee0c47a803054794ac6aec50a360d537` — Meridian Patient Analytics
4. `dsid_ef4636bb7f1a419f82eed955664238f8` — Obsidian Health Vault
5. `dsid_ffe615af6fe74ea7a98d5b9e365c1972` — Valencia Health Regulatory Partners
6. `dsid_645197711b374a9bbfb1a49013cc2219` — Ironroot ComplianceCare
7. `dsid_26f5cb5024fa4ff68dc6cf0a8caabf61` — Helio Health Systems
8. `dsid_a8e91c51c409404cbd58310e3cb1c860` — Summit Telehealth
9. `dsid_6917f17be3d64f609026f972dc35eb93` — Lumen MedInsights
10. `dsid_9b199ee0d27242749095cda255f8bc3f` — Security Criteria Declaration & Acceptance Framework for Private Deploy

### Fill for this row (also include in final JSON array)

```
row_id: 2
question_id: qst_0002::metadata
corpus_scale_size: 100000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 3

- **row_id:** `3`
- **question_id:** `qst_0003::metadata`
- **corpus_scale_size:** `5000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `HIT` (`True`)
- **gold_id_in_retrieved_top10:** `True`
- **gold_rank_if_hit:** `1`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the engineering ops cleanup ticket about reconciling office equipment and deactivating old access cards, what is the due date?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_c5288dd4874345adb80f4a71c9a18773`
_source: full_erb_file:dsid_c5288dd4874345adb80f4a71c9a18773__ENG-4721-misc-chores-office-inventory-and-keycard-cleanup.txt_

```text
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

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_c5288dd4874345adb80f4a71c9a18773` ★ GOLD — misc-chores-office-inventory-and-keycard-cleanup
2. `dsid_03b2db544a6d4cf886fb9869058a05f2` — Office inventory + keycard audit + disposal request (storage shelves + access system cleanup)
3. `dsid_463573b2edfe492ca27878c2ef9bc640` — Temporary dual-desk setup and outbound equipment shipments for hybrid onboarding in SF North Tower
4. `dsid_3d1b7e13cb98482a98efe6833cf44d85` — Dock-to-desk equipment migration + temporary badge access for contractor onboarding (Bldg A, 3rd floor)
5. `dsid_a49b2f5e6fee49b998b5188b80885c42` — Satellite office desk: mismatched EU/UK adapter, missing ergonomic footrest, and 48-hour temp badge request
6. `dsid_8138b96e181940418cc5067b2630064e` — Clarify provisional license reclaim window and equipment-return grace period for immediate offboarding
7. `dsid_da7e13b65f8a42b4975b44b2db0a36e4` — Post-evacuation badge suspension + temporary workstation redistribution and inbound courier hold
8. `dsid_d9ac03742f2f4c769507c987d6045436` — Cross-site elevator badge not granting floor access after desk relocation; coordinated ergonomic equipment shipment and return
9. `dsid_8692c99abe3d4ccdb158cf1abf37ae17` — Reassign unused SaaS seats + onboard new identity vendor for engineering org
10. `dsid_562213b6a37e4912add20e642b9f9a15` — people-ops

### Fill for this row (also include in final JSON array)

```
row_id: 3
question_id: qst_0003::metadata
corpus_scale_size: 5000
condition: raw
auto_hit_at_10: true
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 4

- **row_id:** `4`
- **question_id:** `qst_0010::metadata`
- **corpus_scale_size:** `5000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `HIT` (`True`)
- **gold_id_in_retrieved_top10:** `True`
- **gold_rank_if_hit:** `1`
- **LLM triage (ignore if conflicting):** label=`n` mode=`label_noise`

### Question

In the weekly internal sync about a hardware tuning profile pack, what was the due date for the action item assigned to Irene Choi about compiling GPU SKU string variants including MIG suffixes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_1415c2463492415693a3d4758847630b`
_source: full_erb_file:dsid_1415c2463492415693a3d4758847630b__2025-12-03-hardware-tuning-profiles-pack-weekly-sync.txt_

```text
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

[01:03] Irene Choi: And we do have both in fleet. The hosted pools are mostly SXM, dedicated varies.

[01:08] Hiro Tanaka: Exactly. So I want to guard on memory bandwidth / device name.

[01:13] Ethan Park: Just to clarify, guardrails here means the profile includes “applies_if” rules, right? Like “sku_family=h100” plus “form_factor=sxm” or “hbm>=80GB”?

[01:25] Hiro Tanaka: Yeah, that’s the idea.

[01:27] Talia Benson: Okay, so for v0.3 we keep it simple: H100 with explicit differentiation if needed. Ethan, that’s compatible with the schema we landed?

[01:35] Ethan Park: Mostly. We can do it without nesting complex expressions. But we need to keep it readable. Also we have to be careful with string variants. Like “NVIDIA H100 PCIe” vs “H100-80GB” and sometimes the cloud provider adds junk.

[01:49] Irene Choi: Yeah. We’ve got a list. I’ll send the updated list after this.

[01:54] Talia Benson: Great. Sofia, scheduling side?

[01:58] Sofia Ivanova: On scheduler: the big change is we picked up Marcus’s fix for prefill/decode fairness. That was the tail regression we saw when continuous batching was set more aggressively. The patch basically prevents decode starvation when we have a few long prefills.

[02:17] Sofia Ivanova: On the benchmark runs from yesterday, p95 improved. It’s not totally gone in the worst-case streaming scenario, but it’s within the guardrail bands we discussed with SRE.

[02:28] Sean Gallagher: Which band? Like, what are we talking.

[02:31] Sofia Ivanova: For the streaming chat workload at concurrency 64, p95 went from +18% to +6% versus baseline, while tokens/sec stayed +11%. So still a trade, but it’s less scary.

[02:45] Sean Gallagher: Okay. +6% might be acceptable if we’re honest about expected behavior and we can rollback quickly.

[02:52] Talia Benson: Rina/Claire, can you anchor this with the matrix summary? Are those numbers representative or cherry picked.

[02:59] Rina Kobayashi: Um, it’s representative for the “streaming mix” bucket. We have three main mixes right now: non-streaming summarization, streaming chat, and long-context Q&A. The streaming one is the noisy one.

[03:12] Claire Dubois: Also, we still don’t have the “tool calling” pattern in the matrix. Applied ML asked for that because the stop-token and structured output changes the decode pacing. I can add it but we won’t have perfect realism for v0.3.

[03:25] Talia Benson: Understood. Let’s add a lightweight version, not derail.

[03:30] Omar El-Sayed: Can I jump in on “long-context Q&A” because that’s where L40S is exploding.

[03:35] Talia Benson: Yep, go ahead.

[03:38] Omar El-Sayed: So L40S OOMs aren’t just “too big KV”. It’s fragmentation plus some caching behavior. When we do long prompts with moderate concurrency, the KV cache budget expands and we don’t reclaim fast enough. I’ve got a guardrail patch that caps KV per request and shifts to a more conservative eviction.

[03:59] Rina Kobayashi: Is that the thing that was called “KV cash” in the logs? Sorry, I keep reading it like money.

[04:04] Omar El-Sayed: Yeah, the logs are… not great.

[04:08] Benji Okafor: Also the config key name is “kv_cache_budget_mb” and someone’s typo’d it in one of the YAML examples. We should fix docs before it becomes a support issue.

[04:17] Talia Benson: Please capture that as an action item; we can fold into docs PR.

[04:22] Omar El-Sayed: For L40S: with the cap, OOMs went away in my local repro, but p50 got slightly worse on short prompts due to more frequent evictions.

[04:33] Sofia Ivanova: That’s expected. The question is: does it hurt p95 a lot.

[04:38] Rina Kobayashi: We didn’t finish the full L40S matrix because the perf-canary runner died mid run. It’s flaky.

[04:45] Kira Volkov: That’s the same flake I’ve been tracking. The job sometimes pins CPU and the driver resets. It’s not strictly a runtime regression.

[04:54] Vanessa Ortiz: That might be the runner node type. Those L40S boxes have weird CPU steal. We can allocate a different host class.

[05:02] Talia Benson: Okay, but for the pack release we need stable validation. Can we prioritize making L40S runner stable this week.

[05:10] Vanessa Ortiz: Yes, I’ll sync with infra CI folks. We can reserve a pool.

[05:15] Talia Benson: Great.

[05:17] Talia Benson: B200 status. Irene?

[05:20] Irene Choi: Limited access. We have, like, two nodes in us-east and one in eu-west. Driver is the big constraint. Some nodes are on a different branch; CUDA minor version mismatch. So we can’t run the same build everywhere.

[05:36] Hiro Tanaka: Also kernel differences. Some of the H100 heuristics don’t port cleanly. We have to keep the B200 profile experimental and strict-check the driver/CUDA. If check fails, fallback to generic.

[05:50] Ethan Park: The loader supports “requires” with min runtime version and min driver. But we need to decide what we log and what we do when it doesn’t match.

[05:59] Benji Okafor: Current behavior is: if incompatible, log warning, select default profile. But in Private deployments, warnings get ignored. We added startup log matrix in the runtime to show runtime version vs profile version. People will still ignore it.

[06:14] Sean Gallagher: From oncall perspective: I want a big obvious metric: selected_profile, source, and whether we fell back due to compatibility.

[06:22] Kira Volkov: That’s in the metrics PR. It emits “profile_selected{profile=..., source=..., reason=...}” basically.

[06:31] Talia Benson: Okay. For B200, we stick to “off by default” and enable in one pool only. We also need a clear rollback toggle.

[06:41] Irene Choi: Already planning to disable by pool config. But we need override precedence: fleet default vs per-pool vs per-customer.

[06:49] Ethan Park: That’s the ADR. In short: default is in runtime, pack overlays, then fleet/pool overrides, then customer overrides, then per-route overrides. Env var remains highest priority for emergency.

[07:03] Sean Gallagher: Env var at highest priority makes me nervous, but I get why. For emergency we want it.

[07:08] Talia Benson: Let’s park ADR debate; we have to ship.

[07:12] Claire Dubois: Can I ask about “expected behavior” language. Last week we had a docs thread: we need to avoid sounding like we guarantee p95 improves.

[07:20] Talia Benson: Correct. We say “expected behavior under this workload envelope”. We explicitly call out tradeoffs and failure modes.

[07:28] Sofia Ivanova: I’ll add a line: throughput-first can increase tail latency, especially streaming and long-prefill mixes. Balanced mode is default for Hosted. Throughput-first maybe for Dedicated batchy workloads.

[07:42] Hiro Tanaka: +1. Also some kernels are better at long seq but worse at short seq. That’s why the bucketization exists.

[07:51] Rina Kobayashi: On H100 matrix: overall tokens/sec improved 8–15% depending on model family. p50 latency improved slightly on non-streaming. p95 on streaming is variable but less bad after fairness fix.

[08:04] Claire Dubois: Which models are in the matrix again? For notes.

[08:08] Rina Kobayashi: Three families: Llama-style 70B-ish, a smaller 8B-ish, and an embedding model. I’m not saying names because we keep swapping the exact ones, but it’s consistent.

[08:20] Talia Benson: Good. Put the exact model pins in the benchmark artifact, not in this call.

[08:25] Kira Volkov: Perf-canary gates: right now thresholds are too tight for p95 on streaming. We’re failing builds due to noise. I propose we run each scenario three times and gate on median. Also widen band for the known noisy buckets.

[08:41] Sean Gallagher: Please run that by SRE. We can’t widen too much and miss regressions.

[08:47] Kira Volkov: Yeah. We can keep strict bands on error rate, OOM, and queue depth. p95 can be median-of-3 with narrower band.

[08:57] Benji Okafor: On queue depth: the new backpressure settings can change queue behavior. It might look “worse” but it’s actually protecting latency. We need to define the metric expectation.

[09:08] Sofia Ivanova: Exactly. A slightly higher queue depth might be fine if tail latency is stable. But if queue grows without bound, that’s bad.

[09:17] Talia Benson: We need a consistent oncall triage list: which dashboards, which metric thresholds mean rollback.

[09:23] Sean Gallagher: For rollback criteria, I want: p95 latency +10% sustained 15 minutes on top routes OR error rate above X OR OOM events > 0 in that pool post-deploy. Plus a “customer ticket spike” clause.

[09:40] Talia Benson: Great. Capture in runbook.

[09:43] (crosstalk)

[09:44] Vanessa Ortiz: Also autoscaling. If we change batching, throughput changes, autoscaling may react weirdly. We should watch utilization and scale oscillations.

[09:54] Irene Choi: Yep. Some pools have different scaling policies. We’ll do staged rollout: one canary pool per region, then 10%, then 50%, then 100.

[10:06] Talia Benson: Okay, let’s get more detailed on H100: balanced vs throughput-first. Sofia, what knobs differ.

[10:13] Sofia Ivanova: Balanced: lower max batch tokens, more strict prefill/decode fairness, smaller queue limits. Throughput-first: higher max batch tokens, more aggressive continuous batching window, less strict fairness.

[10:28] Hiro Tanaka: And kernel side: throughput-first allows selecting kernels that are slightly worse for short sequences but better for long, to maximize aggregate tokens/sec.

[10:40] Claire Dubois: That aligns with workloads: summarization batch jobs vs chat.

[10:45] Talia Benson: So default: Balanced for Hosted. For Dedicated, we can let customers pick. For Private, default Balanced but document override.

[10:56] Benji Okafor: On Private override: Helm values wire in the profile pack and also allow overriding per deployment. We should include safe “known good” examples.

[11:07] Ethan Park: And validation: if someone sets nonsense values, config validation should fail fast.

[11:13] Sean Gallagher: Fail fast is good, but in production it might brick a rollout.

[11:18] Ethan Park: Right. We only fail fast for invalid types/out-of-range. For optional keys, we ignore unknown keys with a warning. That was the compromise.

[11:30] Talia Benson: Okay.

[11:32] Talia Benson: Let’s check blockers. Rina: what’s blocking the next benchmark report.

[11:37] Rina Kobayashi: Two things: L40S runner flake and missing one H100 rerun after the fairness fix merged. The H100 rerun should finish today if the queue cooperates.

[11:49] Kira Volkov: The H100 queue is fine. L40S is the one with, like, random driver resets.

[11:55] Vanessa Ortiz: I’ll get you a reserved node class by tomorrow.

[12:00] Rina Kobayashi: Great.

[12:02] Talia Benson: Irene: any infra blockers.

[12:05] Irene Choi: Only B200 access. We can’t do a full matrix. I can get NVIDIA to lend us more for a week, but not guaranteed.

[12:14] Hiro Tanaka: For v0.3, maybe it’s fine if B200 remains “experimental preview” with limited validation.

[12:22] Talia Benson: That’s consistent with leadership: experimental, gated, clear fallback. No broad enablement.

[12:30] Claire Dubois: Can we ensure docs say “B200 profile requires driver X / CUDA Y” and “not supported in all regions”.

[12:38] Ethan Park: Yes, and runtime logs show compatibility matrix.

[12:42] Benji Okafor: Plus a debug endpoint to dump effective runtime config. Oncall can ask a customer to run it in Private.

[12:50] Sean Gallagher: That’s huge. As long as it’s gated/secured.

[12:54] Benji Okafor: It’s internal-only by default; for Private we require an explicit enable flag and auth.

[13:01] Talia Benson: Cool.

[13:03] (brief pause)

[13:05] Talia Benson: Let’s talk about override precedence edge cases: MIG and multi-GPU nodes. Irene, did we decide per-device vs per-node.

[13:14] Irene Choi: Most of our serving nodes are single GPU, but some Dedicated has multi. MIG is rare but exists.

[13:22] Ethan Park: The current loader selects a profile per process based on detected GPU 0. If you have mixed GPUs, that’s a problem. But we don’t support mixed in one node anyway.

[13:33] Sean Gallagher: What about MIG slices. The device name can include “MIG 1g.10gb” etc.

[13:40] Irene Choi: Yep, that breaks naive string matching. I’ll include the variants we saw.

[13:46] Hiro Tanaka: Kernel presets on MIG are risky. We should treat MIG as “unknown” and choose conservative defaults.

[13:54] Sofia Ivanova: Scheduling also changes; smaller memory means smaller KV budgets. So yes, conservative.

[14:00] Talia Benson: Okay, we’ll add guardrail: if MIG detected, don’t apply tuned profile unless explicitly allowed.

[14:08] Ethan Park: That’s easy.

[14:10] Talia Benson: Now canary rollout plan. Sean, what do you need.

[14:15] Sean Gallagher: I need the runbook to be explicit: which toggle disables profiles for a pool, and where to look. Dashboard should have panels segmented by selected profile. And alert thresholds should be enumerated.

[14:30] Kira Volkov: Observability pack has the new panels. We can link them.

[14:34] Sean Gallagher: Also: who’s on point during rollout windows. I don’t want a Friday night surprise.

[14:40] Talia Benson: We’ll coordinate with release train owner but for now: staged in business hours. Irene, can we commit to that.

[14:47] Irene Choi: Yes.

[14:49] Talia Benson: Great.

[14:51] (transcription note: multiple speakers)

[14:52] Sofia Ivanova: One more thing: the throughput-first preset can cause token latency spikes if the request mix has lots of short prompts. We should keep it opt-in.

[15:02] Hiro Tanaka: Yep.

[15:04] Claire Dubois: That’s also about workload envelope. We should put a table: recommended for “batchy summarization, non-streaming”, not recommended for “interactive streaming chat with tight p95”.

[15:15] Talia Benson: Good, docs will include.

[15:18] Talia Benson: Anything else from Bench.

[15:21] Rina Kobayashi: I want to mention one thing: embedding workloads. The tuned profiles didn’t help much; maybe 1–2% variance. But they didn’t hurt. So we can say “no meaningful change expected.”

[15:33] Talia Benson: Great.

[15:35] Omar El-Sayed: On L40S: we should define safe-by-default memory behavior. Like KV budget is a function of free memory. But we can cap at X. Right now I used 65% of available memory, leaving headroom.

[15:48] Sean Gallagher: Headroom is good. OOMs are the worst.

[15:52] Sofia Ivanova: But if headroom is too big, throughput suffers.

[15:56] Omar El-Sayed: Yep. That’s the trade.

[15:59] Talia Benson: For v0.3: stability > max throughput on L40S.

[16:05] Hiro Tanaka: Agree.

[16:07] Talia Benson: Okay, quick pass on timeline. Today: H100 rerun finishing. Tomorrow: Irene sends SKU variants + reserved L40S runner plan. End of week: v0.3 content freeze pending L40S validation.

[16:23] Benji Okafor: And integration tests for override precedence are in review. I’ll push to merge by Friday.

[16:30] Ethan Park: Schema validation is already merged.

[16:33] Talia Benson: Great.

[16:35] (The transcript continues; mid-section includes detailed Q&A on perf-canary thresholds, startup logging, and B200 gating checks.)

[24:10] Kira Volkov: One thing: gating on p95 as an absolute number is hard because different runs are noisy. That’s why I’m pushing relative change vs baseline on the same runner.

[24:22] Sean Gallagher: Relative change is fine as long as baseline is recent. Otherwise it drifts.

[24:28] Claire Dubois: We can pin baseline artifacts per runtime release. The matrix runner can store last green baseline.

[24:36] Rina Kobayashi: Yeah, the runner emits a summary JSON artifact. We can compare.

[24:44] Talia Benson: Okay.

[31:05] Irene Choi: For the EU-west B200 node: we already saw weird regressions last time. I’d prefer we disable by default there until we know the driver is consistent.

[31:15] Hiro Tanaka: Agreed.

[31:17] Benji Okafor: That can be a pool override that forces profile “generic-safe”.

[31:24] Sean Gallagher: Perfect.

[38:02] Claire Dubois: Quick doc note: please stop saying “guarantee”. Say “expected”. Also we should include “known failure modes”: long prompt distributions, fragmentation, MIG.

[38:16] Talia Benson: Yes.

[42:40] Talia Benson: Recap time. H100: we’re close, one rerun after fairness fix, likely lock balanced preset. L40S: must fix runner flake and validate KV budget guardrail across long-context bucket. B200: experimental flag, strict version checks, disable in EU-west by default. Perf canary: adjust to median-of-3, tighten non-latency metrics. Runbook: concrete rollback thresholds and toggles.

[43:10] Talia Benson: Did I miss anything.

[43:12] (crosstalk)

[43:13] Sofia Ivanova: No, that’s it.

[43:15] Hiro Tanaka: I’ll share the final bucket mapping options in Slack.

[43:18] Rina Kobayashi: I’ll publish the artifact once H100 rerun finishes.

[43:21] Irene Choi: I’ll send SKU strings and MIG variants.

[43:25] Sean Gallagher: Please add rollback criteria draft in the runbook doc by Friday.

[43:32] Talia Benson: Done. Thanks everyone.

End of transcript
H100: lock Balanced preset knobs for v0.3.0 pack and rerun workload matrix with updated prefill/decode fairness fix
L40S: land KV-cache budgeting guardrails and rerun long-context buckets; confirm no OOMs and watch p95 impact
B200: keep experimental flag; add stricter version checks and disable-by-default in EU pools; request more fleet access for a full matrix run
Infra: update GPU SKU string normalization list (PCIe vs SXM variants, provider strings) and feed into detection logic
Perf/Canary: tighten gates to reduce noise; move from single-run thresholds to 3-run median for p95 where possible
Docs/Runbook: draft ‘expected behavior’ curves + explicit non-guarantees; add oncall playbook for quick disable per pool
Hiro Tanaka - Confirm final H100 kernel autoselect seq-len bucket mapping for profile v0.3.0; share diff + rationale in #eng-runtime - Due 2025-12-05
Sofia Ivanova - Re-run streaming-heavy scenarios after fairness fix and report p95 deltas (H100 balanced vs throughput-first) - Due 2025-12-06
Rina Kobayashi - Publish the standardized benchmark artifact for the latest H100 + L40S runs (matrix runner output + notes) - Due 2025-12-05
Claire Dubois - Update workload matrix doc to include tool-calling / stop-token patterns requested by Applied ML (lightweight version for v0.3.0) - Due 2025-12-09
Irene Choi - Provide updated list of GPU SKU strings seen in fleet (incl. MIG suffixes) and confirm detection fallback when ambiguous - Due 2025-12-04
Benji Okafor - Verify override precedence integration test coverage for per-pool disable toggle and per-route override - Due 2025-12-06
Kira Volkov - Propose revised perf-canary gates to reduce flake (median-of-3, widen band on low-QPS buckets) and route for SRE sign-off - Due 2025-12-09
Sean Gallagher - Draft rollback criteria text for runbook (p95, error rate, OOM, queue depth) and confirm alert routing - Due 2025-12-05
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_1415c2463492415693a3d4758847630b` ★ GOLD — Hardware tuning profiles pack - weekly sync
2. `dsid_672bd385942a466798c7764d484e10d8` — GPU Runtime Profiling: kernel selection & TensorRT-LLM vs vLLM deep dive
3. `dsid_c8895fca3f6b48c4abc2c926a6e3d671` — Kernel Scheduler & CUDA Graph Stability Deep Dive - TRT vs vLLM
4. `dsid_0ffeb7f0c944478a86d90f31250abd0d` — Gimbal POC Weekly Latency Standup
5. `dsid_1f590b50d6f94d5793e8a4a09dd6f28a` — Pilot: Latency Tuning Weekly - Redwood & Aureus
6. `dsid_521d3db1645c486ab156092611d16435` — POC FastPath Convergence Check-in
7. `dsid_5a936db99e324072ba9522a7a365edae` — Northforge - Dedicated Reserve Qualification and Surge Strategy
8. `dsid_ef612b48ab244b2ba146e52faf2e4423` — Asteria Labs - post-launch stability and budget retune
9. `dsid_6ea8b40caf094294a1b322486d254818` — POC SDK & tooling alignment — output hardening
10. `dsid_79e25f2ba8ac47ec8cfe436691cb4b64` — Kestrel Dynamics — Capacity heuristics & prewarm scenario review

### Fill for this row (also include in final JSON array)

```
row_id: 4
question_id: qst_0010::metadata
corpus_scale_size: 5000
condition: meta
auto_hit_at_10: true
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 5

- **row_id:** `5`
- **question_id:** `qst_0010::metadata`
- **corpus_scale_size:** `40000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the weekly internal sync about a hardware tuning profile pack, what was the due date for the action item assigned to Irene Choi about compiling GPU SKU string variants including MIG suffixes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_1415c2463492415693a3d4758847630b`
_source: full_erb_file:dsid_1415c2463492415693a3d4758847630b__2025-12-03-hardware-tuning-profiles-pack-weekly-sync.txt_

```text
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

[01:03] Irene Choi: And we do have both in fleet. The hosted pools are mostly SXM, dedicated varies.

[01:08] Hiro Tanaka: Exactly. So I want to guard on memory bandwidth / device name.

[01:13] Ethan Park: Just to clarify, guardrails here means the profile includes “applies_if” rules, right? Like “sku_family=h100” plus “form_factor=sxm” or “hbm>=80GB”?

[01:25] Hiro Tanaka: Yeah, that’s the idea.

[01:27] Talia Benson: Okay, so for v0.3 we keep it simple: H100 with explicit differentiation if needed. Ethan, that’s compatible with the schema we landed?

[01:35] Ethan Park: Mostly. We can do it without nesting complex expressions. But we need to keep it readable. Also we have to be careful with string variants. Like “NVIDIA H100 PCIe” vs “H100-80GB” and sometimes the cloud provider adds junk.

[01:49] Irene Choi: Yeah. We’ve got a list. I’ll send the updated list after this.

[01:54] Talia Benson: Great. Sofia, scheduling side?

[01:58] Sofia Ivanova: On scheduler: the big change is we picked up Marcus’s fix for prefill/decode fairness. That was the tail regression we saw when continuous batching was set more aggressively. The patch basically prevents decode starvation when we have a few long prefills.

[02:17] Sofia Ivanova: On the benchmark runs from yesterday, p95 improved. It’s not totally gone in the worst-case streaming scenario, but it’s within the guardrail bands we discussed with SRE.

[02:28] Sean Gallagher: Which band? Like, what are we talking.

[02:31] Sofia Ivanova: For the streaming chat workload at concurrency 64, p95 went from +18% to +6% versus baseline, while tokens/sec stayed +11%. So still a trade, but it’s less scary.

[02:45] Sean Gallagher: Okay. +6% might be acceptable if we’re honest about expected behavior and we can rollback quickly.

[02:52] Talia Benson: Rina/Claire, can you anchor this with the matrix summary? Are those numbers representative or cherry picked.

[02:59] Rina Kobayashi: Um, it’s representative for the “streaming mix” bucket. We have three main mixes right now: non-streaming summarization, streaming chat, and long-context Q&A. The streaming one is the noisy one.

[03:12] Claire Dubois: Also, we still don’t have the “tool calling” pattern in the matrix. Applied ML asked for that because the stop-token and structured output changes the decode pacing. I can add it but we won’t have perfect realism for v0.3.

[03:25] Talia Benson: Understood. Let’s add a lightweight version, not derail.

[03:30] Omar El-Sayed: Can I jump in on “long-context Q&A” because that’s where L40S is exploding.

[03:35] Talia Benson: Yep, go ahead.

[03:38] Omar El-Sayed: So L40S OOMs aren’t just “too big KV”. It’s fragmentation plus some caching behavior. When we do long prompts with moderate concurrency, the KV cache budget expands and we don’t reclaim fast enough. I’ve got a guardrail patch that caps KV per request and shifts to a more conservative eviction.

[03:59] Rina Kobayashi: Is that the thing that was called “KV cash” in the logs? Sorry, I keep reading it like money.

[04:04] Omar El-Sayed: Yeah, the logs are… not great.

[04:08] Benji Okafor: Also the config key name is “kv_cache_budget_mb” and someone’s typo’d it in one of the YAML examples. We should fix docs before it becomes a support issue.

[04:17] Talia Benson: Please capture that as an action item; we can fold into docs PR.

[04:22] Omar El-Sayed: For L40S: with the cap, OOMs went away in my local repro, but p50 got slightly worse on short prompts due to more frequent evictions.

[04:33] Sofia Ivanova: That’s expected. The question is: does it hurt p95 a lot.

[04:38] Rina Kobayashi: We didn’t finish the full L40S matrix because the perf-canary runner died mid run. It’s flaky.

[04:45] Kira Volkov: That’s the same flake I’ve been tracking. The job sometimes pins CPU and the driver resets. It’s not strictly a runtime regression.

[04:54] Vanessa Ortiz: That might be the runner node type. Those L40S boxes have weird CPU steal. We can allocate a different host class.

[05:02] Talia Benson: Okay, but for the pack release we need stable validation. Can we prioritize making L40S runner stable this week.

[05:10] Vanessa Ortiz: Yes, I’ll sync with infra CI folks. We can reserve a pool.

[05:15] Talia Benson: Great.

[05:17] Talia Benson: B200 status. Irene?

[05:20] Irene Choi: Limited access. We have, like, two nodes in us-east and one in eu-west. Driver is the big constraint. Some nodes are on a different branch; CUDA minor version mismatch. So we can’t run the same build everywhere.

[05:36] Hiro Tanaka: Also kernel differences. Some of the H100 heuristics don’t port cleanly. We have to keep the B200 profile experimental and strict-check the driver/CUDA. If check fails, fallback to generic.

[05:50] Ethan Park: The loader supports “requires” with min runtime version and min driver. But we need to decide what we log and what we do when it doesn’t match.

[05:59] Benji Okafor: Current behavior is: if incompatible, log warning, select default profile. But in Private deployments, warnings get ignored. We added startup log matrix in the runtime to show runtime version vs profile version. People will still ignore it.

[06:14] Sean Gallagher: From oncall perspective: I want a big obvious metric: selected_profile, source, and whether we fell back due to compatibility.

[06:22] Kira Volkov: That’s in the metrics PR. It emits “profile_selected{profile=..., source=..., reason=...}” basically.

[06:31] Talia Benson: Okay. For B200, we stick to “off by default” and enable in one pool only. We also need a clear rollback toggle.

[06:41] Irene Choi: Already planning to disable by pool config. But we need override precedence: fleet default vs per-pool vs per-customer.

[06:49] Ethan Park: That’s the ADR. In short: default is in runtime, pack overlays, then fleet/pool overrides, then customer overrides, then per-route overrides. Env var remains highest priority for emergency.

[07:03] Sean Gallagher: Env var at highest priority makes me nervous, but I get why. For emergency we want it.

[07:08] Talia Benson: Let’s park ADR debate; we have to ship.

[07:12] Claire Dubois: Can I ask about “expected behavior” language. Last week we had a docs thread: we need to avoid sounding like we guarantee p95 improves.

[07:20] Talia Benson: Correct. We say “expected behavior under this workload envelope”. We explicitly call out tradeoffs and failure modes.

[07:28] Sofia Ivanova: I’ll add a line: throughput-first can increase tail latency, especially streaming and long-prefill mixes. Balanced mode is default for Hosted. Throughput-first maybe for Dedicated batchy workloads.

[07:42] Hiro Tanaka: +1. Also some kernels are better at long seq but worse at short seq. That’s why the bucketization exists.

[07:51] Rina Kobayashi: On H100 matrix: overall tokens/sec improved 8–15% depending on model family. p50 latency improved slightly on non-streaming. p95 on streaming is variable but less bad after fairness fix.

[08:04] Claire Dubois: Which models are in the matrix again? For notes.

[08:08] Rina Kobayashi: Three families: Llama-style 70B-ish, a smaller 8B-ish, and an embedding model. I’m not saying names because we keep swapping the exact ones, but it’s consistent.

[08:20] Talia Benson: Good. Put the exact model pins in the benchmark artifact, not in this call.

[08:25] Kira Volkov: Perf-canary gates: right now thresholds are too tight for p95 on streaming. We’re failing builds due to noise. I propose we run each scenario three times and gate on median. Also widen band for the known noisy buckets.

[08:41] Sean Gallagher: Please run that by SRE. We can’t widen too much and miss regressions.

[08:47] Kira Volkov: Yeah. We can keep strict bands on error rate, OOM, and queue depth. p95 can be median-of-3 with narrower band.

[08:57] Benji Okafor: On queue depth: the new backpressure settings can change queue behavior. It might look “worse” but it’s actually protecting latency. We need to define the metric expectation.

[09:08] Sofia Ivanova: Exactly. A slightly higher queue depth might be fine if tail latency is stable. But if queue grows without bound, that’s bad.

[09:17] Talia Benson: We need a consistent oncall triage list: which dashboards, which metric thresholds mean rollback.

[09:23] Sean Gallagher: For rollback criteria, I want: p95 latency +10% sustained 15 minutes on top routes OR error rate above X OR OOM events > 0 in that pool post-deploy. Plus a “customer ticket spike” clause.

[09:40] Talia Benson: Great. Capture in runbook.

[09:43] (crosstalk)

[09:44] Vanessa Ortiz: Also autoscaling. If we change batching, throughput changes, autoscaling may react weirdly. We should watch utilization and scale oscillations.

[09:54] Irene Choi: Yep. Some pools have different scaling policies. We’ll do staged rollout: one canary pool per region, then 10%, then 50%, then 100.

[10:06] Talia Benson: Okay, let’s get more detailed on H100: balanced vs throughput-first. Sofia, what knobs differ.

[10:13] Sofia Ivanova: Balanced: lower max batch tokens, more strict prefill/decode fairness, smaller queue limits. Throughput-first: higher max batch tokens, more aggressive continuous batching window, less strict fairness.

[10:28] Hiro Tanaka: And kernel side: throughput-first allows selecting kernels that are slightly worse for short sequences but better for long, to maximize aggregate tokens/sec.

[10:40] Claire Dubois: That aligns with workloads: summarization batch jobs vs chat.

[10:45] Talia Benson: So default: Balanced for Hosted. For Dedicated, we can let customers pick. For Private, default Balanced but document override.

[10:56] Benji Okafor: On Private override: Helm values wire in the profile pack and also allow overriding per deployment. We should include safe “known good” examples.

[11:07] Ethan Park: And validation: if someone sets nonsense values, config validation should fail fast.

[11:13] Sean Gallagher: Fail fast is good, but in production it might brick a rollout.

[11:18] Ethan Park: Right. We only fail fast for invalid types/out-of-range. For optional keys, we ignore unknown keys with a warning. That was the compromise.

[11:30] Talia Benson: Okay.

[11:32] Talia Benson: Let’s check blockers. Rina: what’s blocking the next benchmark report.

[11:37] Rina Kobayashi: Two things: L40S runner flake and missing one H100 rerun after the fairness fix merged. The H100 rerun should finish today if the queue cooperates.

[11:49] Kira Volkov: The H100 queue is fine. L40S is the one with, like, random driver resets.

[11:55] Vanessa Ortiz: I’ll get you a reserved node class by tomorrow.

[12:00] Rina Kobayashi: Great.

[12:02] Talia Benson: Irene: any infra blockers.

[12:05] Irene Choi: Only B200 access. We can’t do a full matrix. I can get NVIDIA to lend us more for a week, but not guaranteed.

[12:14] Hiro Tanaka: For v0.3, maybe it’s fine if B200 remains “experimental preview” with limited validation.

[12:22] Talia Benson: That’s consistent with leadership: experimental, gated, clear fallback. No broad enablement.

[12:30] Claire Dubois: Can we ensure docs say “B200 profile requires driver X / CUDA Y” and “not supported in all regions”.

[12:38] Ethan Park: Yes, and runtime logs show compatibility matrix.

[12:42] Benji Okafor: Plus a debug endpoint to dump effective runtime config. Oncall can ask a customer to run it in Private.

[12:50] Sean Gallagher: That’s huge. As long as it’s gated/secured.

[12:54] Benji Okafor: It’s internal-only by default; for Private we require an explicit enable flag and auth.

[13:01] Talia Benson: Cool.

[13:03] (brief pause)

[13:05] Talia Benson: Let’s talk about override precedence edge cases: MIG and multi-GPU nodes. Irene, did we decide per-device vs per-node.

[13:14] Irene Choi: Most of our serving nodes are single GPU, but some Dedicated has multi. MIG is rare but exists.

[13:22] Ethan Park: The current loader selects a profile per process based on detected GPU 0. If you have mixed GPUs, that’s a problem. But we don’t support mixed in one node anyway.

[13:33] Sean Gallagher: What about MIG slices. The device name can include “MIG 1g.10gb” etc.

[13:40] Irene Choi: Yep, that breaks naive string matching. I’ll include the variants we saw.

[13:46] Hiro Tanaka: Kernel presets on MIG are risky. We should treat MIG as “unknown” and choose conservative defaults.

[13:54] Sofia Ivanova: Scheduling also changes; smaller memory means smaller KV budgets. So yes, conservative.

[14:00] Talia Benson: Okay, we’ll add guardrail: if MIG detected, don’t apply tuned profile unless explicitly allowed.

[14:08] Ethan Park: That’s easy.

[14:10] Talia Benson: Now canary rollout plan. Sean, what do you need.

[14:15] Sean Gallagher: I need the runbook to be explicit: which toggle disables profiles for a pool, and where to look. Dashboard should have panels segmented by selected profile. And alert thresholds should be enumerated.

[14:30] Kira Volkov: Observability pack has the new panels. We can link them.

[14:34] Sean Gallagher: Also: who’s on point during rollout windows. I don’t want a Friday night surprise.

[14:40] Talia Benson: We’ll coordinate with release train owner but for now: staged in business hours. Irene, can we commit to that.

[14:47] Irene Choi: Yes.

[14:49] Talia Benson: Great.

[14:51] (transcription note: multiple speakers)

[14:52] Sofia Ivanova: One more thing: the throughput-first preset can cause token latency spikes if the request mix has lots of short prompts. We should keep it opt-in.

[15:02] Hiro Tanaka: Yep.

[15:04] Claire Dubois: That’s also about workload envelope. We should put a table: recommended for “batchy summarization, non-streaming”, not recommended for “interactive streaming chat with tight p95”.

[15:15] Talia Benson: Good, docs will include.

[15:18] Talia Benson: Anything else from Bench.

[15:21] Rina Kobayashi: I want to mention one thing: embedding workloads. The tuned profiles didn’t help much; maybe 1–2% variance. But they didn’t hurt. So we can say “no meaningful change expected.”

[15:33] Talia Benson: Great.

[15:35] Omar El-Sayed: On L40S: we should define safe-by-default memory behavior. Like KV budget is a function of free memory. But we can cap at X. Right now I used 65% of available memory, leaving headroom.

[15:48] Sean Gallagher: Headroom is good. OOMs are the worst.

[15:52] Sofia Ivanova: But if headroom is too big, throughput suffers.

[15:56] Omar El-Sayed: Yep. That’s the trade.

[15:59] Talia Benson: For v0.3: stability > max throughput on L40S.

[16:05] Hiro Tanaka: Agree.

[16:07] Talia Benson: Okay, quick pass on timeline. Today: H100 rerun finishing. Tomorrow: Irene sends SKU variants + reserved L40S runner plan. End of week: v0.3 content freeze pending L40S validation.

[16:23] Benji Okafor: And integration tests for override precedence are in review. I’ll push to merge by Friday.

[16:30] Ethan Park: Schema validation is already merged.

[16:33] Talia Benson: Great.

[16:35] (The transcript continues; mid-section includes detailed Q&A on perf-canary thresholds, startup logging, and B200 gating checks.)

[24:10] Kira Volkov: One thing: gating on p95 as an absolute number is hard because different runs are noisy. That’s why I’m pushing relative change vs baseline on the same runner.

[24:22] Sean Gallagher: Relative change is fine as long as baseline is recent. Otherwise it drifts.

[24:28] Claire Dubois: We can pin baseline artifacts per runtime release. The matrix runner can store last green baseline.

[24:36] Rina Kobayashi: Yeah, the runner emits a summary JSON artifact. We can compare.

[24:44] Talia Benson: Okay.

[31:05] Irene Choi: For the EU-west B200 node: we already saw weird regressions last time. I’d prefer we disable by default there until we know the driver is consistent.

[31:15] Hiro Tanaka: Agreed.

[31:17] Benji Okafor: That can be a pool override that forces profile “generic-safe”.

[31:24] Sean Gallagher: Perfect.

[38:02] Claire Dubois: Quick doc note: please stop saying “guarantee”. Say “expected”. Also we should include “known failure modes”: long prompt distributions, fragmentation, MIG.

[38:16] Talia Benson: Yes.

[42:40] Talia Benson: Recap time. H100: we’re close, one rerun after fairness fix, likely lock balanced preset. L40S: must fix runner flake and validate KV budget guardrail across long-context bucket. B200: experimental flag, strict version checks, disable in EU-west by default. Perf canary: adjust to median-of-3, tighten non-latency metrics. Runbook: concrete rollback thresholds and toggles.

[43:10] Talia Benson: Did I miss anything.

[43:12] (crosstalk)

[43:13] Sofia Ivanova: No, that’s it.

[43:15] Hiro Tanaka: I’ll share the final bucket mapping options in Slack.

[43:18] Rina Kobayashi: I’ll publish the artifact once H100 rerun finishes.

[43:21] Irene Choi: I’ll send SKU strings and MIG variants.

[43:25] Sean Gallagher: Please add rollback criteria draft in the runbook doc by Friday.

[43:32] Talia Benson: Done. Thanks everyone.

End of transcript
H100: lock Balanced preset knobs for v0.3.0 pack and rerun workload matrix with updated prefill/decode fairness fix
L40S: land KV-cache budgeting guardrails and rerun long-context buckets; confirm no OOMs and watch p95 impact
B200: keep experimental flag; add stricter version checks and disable-by-default in EU pools; request more fleet access for a full matrix run
Infra: update GPU SKU string normalization list (PCIe vs SXM variants, provider strings) and feed into detection logic
Perf/Canary: tighten gates to reduce noise; move from single-run thresholds to 3-run median for p95 where possible
Docs/Runbook: draft ‘expected behavior’ curves + explicit non-guarantees; add oncall playbook for quick disable per pool
Hiro Tanaka - Confirm final H100 kernel autoselect seq-len bucket mapping for profile v0.3.0; share diff + rationale in #eng-runtime - Due 2025-12-05
Sofia Ivanova - Re-run streaming-heavy scenarios after fairness fix and report p95 deltas (H100 balanced vs throughput-first) - Due 2025-12-06
Rina Kobayashi - Publish the standardized benchmark artifact for the latest H100 + L40S runs (matrix runner output + notes) - Due 2025-12-05
Claire Dubois - Update workload matrix doc to include tool-calling / stop-token patterns requested by Applied ML (lightweight version for v0.3.0) - Due 2025-12-09
Irene Choi - Provide updated list of GPU SKU strings seen in fleet (incl. MIG suffixes) and confirm detection fallback when ambiguous - Due 2025-12-04
Benji Okafor - Verify override precedence integration test coverage for per-pool disable toggle and per-route override - Due 2025-12-06
Kira Volkov - Propose revised perf-canary gates to reduce flake (median-of-3, widen band on low-QPS buckets) and route for SRE sign-off - Due 2025-12-09
Sean Gallagher - Draft rollback criteria text for runbook (p95, error rate, OOM, queue depth) and confirm alert routing - Due 2025-12-05
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_25adb0559afc49b6baa8bec5a796df32` — Cross-stage microbatch steering and adaptive kernel routing to maximize NCCL overlap
2. `dsid_b01446526c8b4549bbfcd4f9d00dc8a3` — SKU certification catalog and onboarding runbook for HW-specific performance
3. `dsid_a9e031dea0724ffa9d2682a9d0d826ae` — Investigate dynamic kernel recompile thrash causing p95 latency spikes for mixed-quant workloads
4. `dsid_fb6a04eeac3a43d78bc2760430a5f28d` — Variant granularization, fallback ranking, and published profile matrix for GPU families
5. `dsid_35e80f9394cc48279e4c8a10ec6e1946` — eng-runtime
6. `dsid_62469a0762814236aae1cf861191a615` — Optimize CPU-GPU handshake and threadpool to reduce host overhead during prefill/decode
7. `dsid_515cfde3929d42efafcffe5c79c65b56` — SKU-aware wake scheduler for prefill/decode on H100, L40S, A10
8. `dsid_17d162cfdc254d71b08c73af1c923e86` — Runtime oncall scratchpad - Ishaan
9. `dsid_943113c0d3114ce89257a8f46f13e1c2` — Per-model kernel selection matrix and pin/publish workflow for MHA/GQA/MoE onboarding
10. `dsid_466645b7fc644ed8b349b623d256fdea` — Lease-free atomic unpin: prefetch-safe aging for GPU KV cache

### Fill for this row (also include in final JSON array)

```
row_id: 5
question_id: qst_0010::metadata
corpus_scale_size: 40000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 6

- **row_id:** `6`
- **question_id:** `qst_0016::basic`
- **corpus_scale_size:** `40000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What is the company policy for how long contractor access should last by default before it expires, according to the access and permissions playbook?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ba7d1565b0694e359983bccaa4bf5977`
_source: full_erb_file:dsid_ba7d1565b0694e359983bccaa4bf5977__entitlements-and-purchase-pathways-playbook-2030.txt_

```text
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

1) Request process

- Use the Access Portal (accessible from the Redwood Console > Tools > Access Request).
- Provide: justification, target systems (service name and environment), requested role (exact RBAC role), duration, and manager approval.
- For long-lived roles (>90 days), supply quarterly business justification and add reviewer in Access Portal.

2) Approval matrix (summary)

- Day-to-day access to non-prod systems: manager approval.
- Prod read-only access: manager + security notification.
- Prod privileged/infra access (SSH, K8s-admin, DB write): manager + security + infra-owner approval.
- Emergency elevated access: break-glass procedure (see Runbook ID: RG-2026-breakglass).

3) Provisioning and deprovisioning

- Provisioning is automated via Okta + Terraform runbooks (Infra-IAC). On approval, provisioning SLA is 2 business days for standard requests, 8 hours for emergency sprints.
- Access expirations are enforced: default 30 days for contractor requests, 90 days for internal hires unless renewed.

4) Periodic review

- Quarterly access attestation: team owners must validate active entitlements and remove stale accounts. Failure to respond triggers automated revocation notices.

Change management
-----------------

Scope: Any modification to production services, infra provisioning, IAM policies, or customer-facing configuration.

Change categories and approval paths:

- Standard change: pre-approved, repeatable changes (e.g., routine OS patching via controlled pipeline). Requires change ticket and notification to SRE runbook subscribers.
- Normal change: requires Change Review Board (CRB) approval for higher impact (planned releases that affect SLAs). CRB meets twice weekly.
- Emergency change: immediate fixes that must follow the emergency roll-forward checklist and be retroactively documented in the change ticket.

Change windows and freezes:

- Quarterly freeze: last two business days of each quarter are freeze windows for major releases unless exception approved by CTO and SRE lead.
- High-risk releases: require canary rollout and 30% traffic validation for 24 hours before full rollout.

Change request minimum content (ticket):

1. Change owner and contact
2. Rollout and rollback plan with automation steps
3. Expected impact and post-deploy validation steps
4. Backout criteria and timeline
5. Stakeholder notification list

SLOs and audit

- All normal changes must have an associated ticket and be auditable for 12 months.
- Emergency changes must be documented within 48 hours.

Data management and classification
--------------------------------

Classification levels:

- Public: content intended for public consumption.
- Internal: operational information not intended for external distribution.
- Confidential: employee, business, or customer information that requires access controls.
- Restricted: regulated or highly sensitive data (PII, payment data, health data) that requires encryption at rest and in transit, strict access controls, and audit logging.

Handling rules (summary):

- Confidential & Restricted: store only in approved systems (Redwood Console vaults, encrypted S3 with KMS). No vendor transfer without security and legal sign-off.
- Data retention: default retention for logs is 90 days; for customer-facing telemetry retention follows contractual obligations.
- Data deletion: use Data Erasure Request form and verify via automated deletion job.

Procurement and expenses
------------------------

Purchase approval thresholds (effective):

| Amount (USD) | Approvals required | Notes |
|--------------|-------------------|-------|
| < 2,500 | Manager | Auto-approval in VendorHub if budget tag present |
| 2,500 – 50,000 | Manager + Finance | Finance checks budget and tax classification |
| > 50,000 | Manager + Finance + Procurement + Legal | Requires exec sponsor and procurement intake form |

Procurement steps (numbered):

1. Create a request in VendorHub including business justification, vendor name, SOW/quote, and budget tag.
2. Attach vendor compliance docs (SOC2, ISO, insurance certificate) when available.
3. Finance validates budgets and tax treatment within 3 business days.
4. Procurement routes to Legal for >50k or non-standard T&Cs.
5. Once approved, Procurement issues purchase order and coordinates supplier setup.

Expense reimbursement:

- Use ExpenseFlow, attach receipts within 30 days of expense. Per diem caps: domestic $150/day, international $250/day unless pre-approved. Card use: corporate cards are preferred for travel; personal card reimbursements require manager approval.

Vendor management lifecycle
--------------------------

Onboarding checklist (timeline expectations):

- Initial intake: vendor submitted via VendorHub, 1 business day acknowledgement.
- Risk assessment: Security performs questionnaire review; expect 5-7 business days for standard vendors, 15-20 days for those handling Restricted data.
- Contracting: Legal drafts/negotiates terms; standard NDA/SOW templates for low-risk vendors. Time: 5–15 business days depending on terms.
- Procurement & finance: vendor setup (W-9/COI), tax classification, payment terms.

Minimum vendor requirements by risk tier:

- Low risk (no data access): PO, standard SOE, vendor contact, invoice cadence.
- Medium risk (limited data access): PO, signed DPA, security questionnaire, SOC2 Type II preferred.
- High risk (customer data or privileged infra access): PO, DPA, SOC2 Type II or penetration test report, system access plan, contractual breach notification clause, indemnity terms.

Offboarding and termination:

- Termination checklist: revoke credentials, recover assets, enforce data return/deletion, final invoice reconciliation, and a post-termination confirmation from vendor. Procurement must retain termination evidence for 7 years.

Travel policy (high level)
-------------------------

Booking: Use Travel Portal (linked from Redwood Console). Lowest reasonable fare policy applies for economy class. Business class requires exec-level pre-approval for travel over 8 hours.

Approvals: Manager approves travel requests in Travel Portal. International travel must include security and people-ops notification if travel is to high-risk countries listed by People Ops.

Per diems and expenses: See ExpenseFlow caps. Receipts required for all items >$25.

Safety and incident reporting:

- In case of an incident while traveling, contact People Ops emergency line and Security: security@redwood.com. All incidents must be reported within 24 hours.

Templates and forms (where to find)
----------------------------------

- Procurement intake form: VendorHub > New Request > Procurement Intake (use template 'Procurement-Intake-v2').
- Data Erasure Request: Redwood Console > Data Requests.
- Change request template: CRB ticket template in Jira (project: RED-CHANGES).
- Access request template: Access Portal (select role and environment).

Example procurement JSON payload (for VendorHub API)

{
  "requestor": "alice@example.com",
  "vendor": "Acme Analytics",
  "amount_usd": "7500",
  "justification": "Production observability for dedicated clusters",
  "budget_tag": "infra-monitoring",
  "required_by": "2027-02-15"
}

Appendix: enforcement and exceptions
-----------------------------------

- Exceptions: Managers may request a documented exception for short-lived needs; exceptions require a written business case and a compliance review.
- Enforcement: Repeated policy violations (e.g., unmanaged vendor engagements or expired privileged access) will be escalated to the employee's manager and may trigger procurement suspension or disciplinary review.

Contacts and ownership
----------------------

- Policy owner: Finance-Legal (policy owner contact: procurement@redwood.com).
- Security contact for vendor risk: security@redwood.com.
- People Ops travel & benefits: people-ops@redwood.com.

Revision history
----------------

- 2026-11-12: Initial draft published by Maya Chen.
- 2026-12-03: Updated procurement thresholds and added emergency change SLA (reviewed by Luis Alvarez and Priya Nair).

Related artifacts and references
-------------------------------

- Runbook RG-2026-breakglass (eng-sre/runbooks).
- VendorHub API docs (internal link).
- Security questionnaire template (security-and-compliance/audit-logging).

End of document
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_11b4dc5c498c472b9827a245f5a0720e` — Equitable Onboarding and Role Access Playbook
2. `dsid_fdc9b77a90a5434d8c576afdcc0c8a72` — Onboarding Toolchain Access and Career Checkpoints
3. `dsid_c1df83bebd3142bcbd2153c0d9a293b2` — Access, Change & Procurement Playbook — Compact Guide
4. `dsid_3bbea346f853491abd6e9615a41f1c77` — Access Provisioning and Spend Journeys (Company Playbook)
5. `dsid_84edaffcb234432fae7577eeabb7d893` — Role-based access, vendor onboarding, and spend workflows — Playbook
6. `dsid_96dfbf0c384a47a6b460adbd2b84dfbe` — Satellite Team Tool Access and Mentor Pairing Playbook
7. `dsid_6418143d8b5342cd80b308fdab0b726d` — Permissioning Journeys and Expense Approval Patterns
8. `dsid_a5646b96187c4c6db01319035f56dc3d` — Company Access, Change, and Supplier Playbook
9. `dsid_d9671df790c14a618908e8a054276d55` — Authorization Lifecycle and Procurement Patterns Playbook
10. `dsid_2bb2dc1bbe734759964baadd3d166db3` — Onboarding Security Handoff for Customer‑Facing Hires

### Fill for this row (also include in final JSON array)

```
row_id: 6
question_id: qst_0016::basic
corpus_scale_size: 40000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 7

- **row_id:** `7`
- **question_id:** `qst_0024::metadata`
- **corpus_scale_size:** `15000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `HIT` (`True`)
- **gold_id_in_retrieved_top10:** `True`
- **gold_rank_if_hit:** `1`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the eng-sre space, which internal published runbook by Rishi Malhotra covers verification steps to follow after rotating production credentials?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_74ebb73359364bc791707a92a3227e3a`
_source: full_erb_file:dsid_74ebb73359364bc791707a92a3227e3a__post-rotation-verification-checklist.txt_

```text
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

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_74ebb73359364bc791707a92a3227e3a` ★ GOLD — Post-rotation verification checklist (production credentials)
2. `dsid_cf06e75be4f94156ac338f62e3ee028b` — Production secret rotation runbook
3. `dsid_93cf47bd2c3944ff92569797f07ea724` — oncall-rotation-onboarding-and-slo-ownership-runbook-2024
4. `dsid_c790406c34ce484b8d00a19dbeb476a6` — Quarterly Private/VPC Ops Readiness & Governance Playbook
5. `dsid_2fb1fa3db2234ae7aec1d8195f016829` — ingress-gateway-client-cert-rotation-and-ssl-ops-playbook-2026
6. `dsid_7a9d6810cee2497f93113afa7feb0076` — Enterprise Onboarding — Post-Provisioning Stability & Fallback Checklist
7. `dsid_546e110c14144ff9a1a02d9145c43177` — Rotations and Break-Glass Cheatsheet
8. `dsid_8270b31acc864a05abc0d5196281feca` — RBAC Policy Rewind & SIEM Validation — On-Call Runbook
9. `dsid_190d9732b59b411d8a6bcc59fd61b309` — Runbook: Rollback and Post-change Validation (Hosted API + Console)
10. `dsid_8c92178c254d467c9854db67aac7c9be` — Secret management standard (production)

### Fill for this row (also include in final JSON array)

```
row_id: 7
question_id: qst_0024::metadata
corpus_scale_size: 15000
condition: raw
auto_hit_at_10: true
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 8

- **row_id:** `8`
- **question_id:** `qst_0025::metadata`
- **corpus_scale_size:** `75000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the customer-support bug about synchronized retry backoff causing streaming reconnect storms, what production environment is listed for the incident?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_4a2ce3e1be4d4f00a089ccc00ac92b8c`
_source: full_erb_file:dsid_4a2ce3e1be4d4f00a089ccc00ac92b8c__SUP-126007-client-retry-window-desync-burst-queueing.txt_

```text
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
- Support trace id sample: trace-20260310-5f3b (attached).
- Customer-side logs: repeated RetryAttempt events showing identical backoff timestamps across many pods.
- OS counters on infra NAT: short-term ephemeral port exhaustion and large TIME_WAIT count.

- Investigated request-level traces: high correlation between first observed 429s and a large cluster of retries ~200-600ms later.
- SDK release notes: v2.4.0 changed jitter implementation to a lightweight jitter that accidentally behaves like fixed offset when clients start nearly-synchronously.
- Wire-level capture from customer cluster shows burst of SYNs to api.redwood.prod around 17:12Z.
- Gateway logs show queue depth increased and per-route tokenization threads saturated for ~8 minutes.
- No model inference code regressions found; serving runtime CPUs and GPUs remained within normal utilization once requests were accepted — the problem is ingress queuing and connection storming.
- Reproduced locally by starting 500 clients with identical clocks and forcing initial 429s; when jitter set to zero, retries synced and queueing/p95 latency rose sharply.

Immediate mitigation (applied 2026-03-10):
- Recommended customer patch: downgrade SDK to 2.3.8 or apply SDK config override to enable full jitter (backoff_jitter=full), max_retries=3, connection_pool.max = 8. Customer applied overrides and tail latency returned toward baseline within 10 minutes.
- Edge-side temporary throttle change: API gateway accepted soft rate smoothing for the customer's tenant for 15 minutes to let clients recover.

Permanent fix (in progress):
- SDK PR https://github.com/redwood-inference/sdk/pull/4193 enforces full jitter by default and adds randomized start-up jitter for new client processes. Targeted release v2.5.0.
- Add a platform alert that detects synchronized retry patterns (high cross-client retry correlation) and raises a preemptive incident to trigger auto-smoothing.
- Update Dedicated onboarding docs to call out default retry/jitter and recommend connection pool sizing for large fleets.

- Engineering: roll v2.5.0 SDK default to full jitter and add startup jitter (owner: Marcus Liu, ETA 2026-03-20).
- SRE: add alert and dashboard for retry-correlation and ephemeral port pressure (owner: Priya Menon, ETA 2026-03-18).
- Support: update runbook to include immediate customer-side overrides and exact recommended config snippets (owner: Aisha Patel, ETA 2026-03-14).

Support (Aisha Patel) 2026-03-10T17:45Z: Created ticket after NimbleVoice support rep reported streaming stalls. Collected traces and requested customer logs and SDK config.
Customer (NimbleVoice - Jenna Ortiz) 2026-03-10T18:02Z: Confirmed SDK version v2.4.1 and provided deployment manifest. Noted brief autoscaler event at ~17:05Z which increased new pod churn.
SRE (Priya Menon) 2026-03-10T18:20Z: Observed gateway queue depth and SYN bursts. Suggested temporary tenant smoothing and asked customer to reduce max_connections per pod as a workaround.
Engineering (Marcus Liu) 2026-03-11T09:12Z: Found the jitter change in v2.4.0 that can degenerate into fixed offset under near-synchronous start. Drafted PR to restore full jitter by default and add startup jitter. Assigned to SDK team for expedited release.
Customer (Jenna Ortiz) 2026-03-11T13:30Z: Applied recommended SDK config overrides and reported meaningful improvement; tail p95 reduced to ~300ms within 10 minutes of change.
Support (Aisha Patel) 2026-03-12T08:02Z: Follow-up: confirmed monitoring shows no recurrence and customer satisfied with workaround. Will track SDK release and SRE alerting as open action items.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_8401a32f4d644ecab18ee24ad6149873` — Customer reports streaming disconnects + elevated 5xx (Hosted API us-east)
2. `dsid_23ad614501964d5a98fd576afcffa23b` — Intermittent evening 5xx surge from streaming fanout + keepalive mismatch causing upstream worker preemptions
3. `dsid_70124860f38d4604981c3c41c45308ce` — Streaming responses reset mid-generation in prod us-east (Acme AI) — connection resets / truncated streams
4. `dsid_146aa71c437f4d37bf5c91b8d176d180` — Interleaved streaming fallback and tenant priority reshuffle triggered elevated 5xx error rate
5. `dsid_a5bea569752c420a9b198ebd56289baa` — Edge proxy retry loop causes SSE stream freeze during long chat sessions
6. `dsid_4ff51390e491448f95348062bc239d1c` — Intermittent streaming disconnect / stops mid-stream across multiple client networks (NexLayer)
7. `dsid_ba8530d59b1448218b4c54abcd266a31` — Streaming session stalls mid-generation after transient latency spike (mobile carrier)
8. `dsid_d4319ac5979642dfb0612c4f35cd4668` — SundialHealth: partial conversation fragmentation, duplicate followups and rollback action plan
9. `dsid_faec551805a649d69c8ce0849c05c907` — Concurrent streaming requests trigger cascading 5xx amplification due to throttle/starvation
10. `dsid_9cfd5e3dc9e341b58bb1fbd1bcc79b33` — Elevated 5xx wave during long-lived streaming sessions due to proxy retry spin

### Fill for this row (also include in final JSON array)

```
row_id: 8
question_id: qst_0025::metadata
corpus_scale_size: 75000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 9

- **row_id:** `9`
- **question_id:** `qst_0036::basic`
- **corpus_scale_size:** `20000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What telemetry events and alert threshold are required to monitor streaming responses when a downstream tool call fails but the system continues with degraded output?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_f94b93a4bc7948ddab45c371187dc6c6`
_source: full_erb_file:dsid_f94b93a4bc7948ddab45c371187dc6c6__PM-862431-emission-stability-tool-orchestration-soft-fail-acceptance.txt_

```text
Emission Stability and Tool-Orchestration: Soft-Fail & Streaming Acceptance

PRD-style acceptance and behavioral specification for: (A) deterministic structured output envelopes during streaming, (B) robust tool/function-orchestration semantics when downstream tool calls fail or time out (soft-fail modes), and (C) observable signal set for debugging degraded emissions. This ticket captures requirements, tradeoffs, and concrete acceptance tests for engineering to implement and QA to validate.
Teams integrating function-calls and streaming structured output have encountered brittle failure modes: partial JSON emissions, stuck streams when a tool times out, and unclear signals in telemetry for root-cause. Previous specs focused on schema handshakes but did not fully specify soft-fail policies (when to continue vs abort), how to surface partial-but-valid objects, or required observability for production troubleshooting.
1) Define deterministic envelope semantics so consumers can parse incrementally and resume/reconcile partial objects. 2) Specify soft-fail modes for tool invocation: best-effort, fallback-only, and abort. 3) Establish acceptance tests for streaming + tool failures that exercise backpressure, resumability, and idempotent retries. 4) Define telemetry and SLI/alert thresholds to detect degraded emission reliability.
- Streaming text and structured frames emitted from Redwood API. - Function/tool invocation lifecycle (invoke, success, failure, retry). - Soft-fail policies and configuration. - Acceptance criteria and end-to-end test matrix (simulated tool latencies/failures).
- Changes to client SDKs beyond minimal parsing guidance. - New RPC transport protocols. - Billing/quotas changes related to retries (handled by a separate billing review).
- Strict abort-on-tool-failure yields highest data correctness but reduces availability; soft-fail increases availability at the cost of accuracy. We recommend defaulting to best-effort-with-degraded-indicators for hosted API and offering strict-abort configuration for enterprise Dedicated/Private deployments. - Emitting placeholder fields vs removing the field: placeholder maintains schema shape for parsers but may surface misleading data. We prefer placeholder objects with explicit 'soft_fail' enum and provenance metadata.
AC-1: Incremental Envelope Parsing: Streaming responses are emitted as ordered 'frames' where each frame is a top-level JSON object stringified and newline-delimited. Consumers can reconstruct the final object by concatenating frames and applying frame-level 'commit' markers. In tests, a slow client that disconnects and reconnects using resume token can re-sync and reconstruct a consistent object state.
AC-2: Soft-Fail Modes: System exposes three modes: 'abort' (default for strict endpoints), 'best_effort' (continue emitting remaining structured fields, include 'soft_fail' markers), and 'degraded_fallback' (switch to cheaper model or cached result then emit). Implementation must allow per-route configuration. Acceptance tests must validate each mode against simulated downstream tool failures.
AC-3: Partial-Object Validity: When a tool call fails and mode is 'best_effort', the emitted structured object must remain JSON-parseable at frame boundaries and include an explicit 'provenance' map with keys: source_variant, tool_status, tool_error_code, soft_fail=true. Test harness validates JSON validity after each frame and final reconciliation produces a documented 'incomplete' state.
AC-4: Function-Invocation Idempotency & Retry Signals: Tool gateway must return idempotency token on initial invocation. Retries (automatic or client-initiated) must attach token to avoid duplicate side-effects. Acceptance tests include simulated at-least-once delivery and assert idempotent behavior for a provided sample tool (mock webhook that records invocations).
AC-5: Timeouts & Backpressure Behavior: When a tool exceeds configured timeout: - in 'abort' mode, the stream emits an error envelope and closes (status=closed, code=TOOL_TIMEOUT). - in 'best_effort', emit soft-fail metadata and continue. System must not indefinitely block other concurrent streams; load tests will simulate N=500 concurrent streams with 10% slow tool responses and verify 99th percentile latency SLOs remain within target with degraded outputs accounted for.
AC-6: Observability Signals: For every streaming emission that includes a soft-fail, the following telemetry events must be emitted: tool_invocation.start, tool_invocation.end (status), stream.frame.commit, stream.soft_fail.marker, stream.resume.attempt (if consumer reconnects). Each event includes trace_id and frame_offset. Acceptance: Kibana dashboards show these events for a 1-hour test run and an alert rule triggers when soft_fail_rate > 0.5% over 5 minutes for production routes.
AC-7: Compatibility with Existing Schema Negotiation: Handshake must include 'preferred_envelope' and 'resume_token' semantics. Acceptance tests exercise older clients by verifying graceful degradation: if preferred_envelope is unsupported, server falls back to newline-delimited JSON frames and includes a compatibility header explaining the downgrade.
AC-8: Test Harness & E2E Test Cases: Provide automated tests that simulate network partitions, tool errors (500, 429, 504), tool latency spikes, and partial stream consumption. Tests must assert that consumers receive either a valid final object or a documented incomplete object with soft_fail metadata in all tested modes.
AC-9: Docs & Examples: Console docs must include examples for parsing frames, handling soft_fail metadata, configuring per-route mode, and troubleshooting guide with representative log queries. Acceptance: docs reviewed and approved by Developer Experience and Design reviewers and linked in PR.
AC-10: Security & Compliance: When soft-fail includes tool error payloads, sensitive fields must be redacted per PII policy. Acceptance: static analysis and a sample audit record confirm PII redaction for tool error messages containing email/SSN-like patterns.
TC-1: Best-effort tool timeout: Start streaming generation that triggers a tool lookup that sleeps for 8s (config timeout 2s). Mode=best_effort. Expect frames including 'tool_status':'timeout' and 'soft_fail':"true"; final object parseable. Verify telemetry events emitted.
TC-2: Abort mode on rate-limit: Simulate tool returning 429. Mode=abort. Expect error envelope and stream close with code TOOL_RATE_LIMIT. Verify client-observed close code and server-side logs reference idempotency token.
TC-3: Resume after disconnect: Consumer reads first N frames then disconnects. Server persists resume_token. Consumer reconnects with token and receives frames from last commit point through final. Assert final object equivalent to continuous stream.
TC-4: Fallback variant switch: Mode=degraded_fallback. Downstream model returns non-responsive. Server emits warning frame, switches to cached summary variant, emits final object with 'source_variant':'cached-summary' and 'tool_error_code' annotated. Verify SLO accounting attributes.
TC-5: Idempotent webhook verification: Mock tool endpoint records invocations. Trigger multiple retries with the same idempotency token. Verify single recorded invocation and correct response to client of 'duplicate-suppressed' marker.
Minimum telemetry must include trace_id, route, model_variant, frame_offset, resume_token, tool_invocation.id, tool_status, tool_error_code, latency_ms. Dashboards: streaming-frame-latency, soft-fail-rate, tool-timeout-trend. Alerts: soft_fail_rate>0.5% over 5m, resume_failure_rate>0.1% over 15m.
Implementation must include a clear config surface (route-level parameter 'tool_failure_policy' with enum values) and safe defaults for public API. Provide migration notes for existing routes currently using legacy streaming format.
2025-02-12 - Diego Ramirez: Added engineering constraints and initial implementation notes; runtime will add resume_token persistence to shard metadata store.
2025-02-18 - Priya Desai (Design): Reviewed placeholder UX for incomplete objects; approved 'soft_fail' inline marker but asked for explicit CTA in Console docs to avoid developer confusion.
2025-02-24 - Rafael Kim (SRE): Requested load test profiles for 500 concurrent streams; noted need to measure KV-cache impact for resumed streams.
2025-03-01 - Aisha Patel: Updated acceptance matrix to include PII redaction requirement following security review kickoff.
2025-03-03 - Diego Ramirez: Implementation branch opened: https://github.com/redwood-inference/runtimes/pull/8123. Ready for review; QA harness in CI added under ci/e2e/streaming-softfail.
2025-03-03 - QA Lead (Elena Novak): Scheduled test window 2025-03-06 to run full E2E matrix against staging with flaky network injection.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_acb6ff8b0afc4f7ba9ef45714f50fa86` — Keepalive ping storm — playbook draft
2. `dsid_5f884c5669194d698c0be56a1df92b33` — Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling
3. `dsid_5dfe1a03b30b4e728de8fa999bdf88dd` — Intermittent 5xx spike from delayed HTTP/2 ACKs causing streaming sessions to half-close and upstream restarts
4. `dsid_15a9d93cc59c4241a97a7e72f749a216` — Postmortem: Streaming stalls during peak traffic (2026-01-12)
5. `dsid_c22869a06d0a4cb89e595c2caea91299` — Streaming stutter detection and continuity recovery playbook
6. `dsid_24422ce3ea2a4f53b9175e9e82d0e493` — Known issue: Streaming responses stall (SSE stream stops mid-response)
7. `dsid_1b5456e3574541148333459ac1344098` — Known issue: Streaming responses may freeze mid-generation (SSE stalls)
8. `dsid_b0de57c71e834d2680538e64658e9bc9` — Unexpected streaming connection interruption mid-response after worker eviction/autoscale
9. `dsid_504460b1f5884382b02eb3af329ab4fc` — P0 hostedAPI stream churn + memory pressure retro
10. `dsid_46b0bc1e97ae4d8792d08e6f4122b948` — P1 Incident Postmortem: Streaming responses intermittently hang

### Fill for this row (also include in final JSON array)

```
row_id: 9
question_id: qst_0036::basic
corpus_scale_size: 20000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 10

- **row_id:** `10`
- **question_id:** `qst_0038::metadata`
- **corpus_scale_size:** `40000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `HIT` (`True`)
- **gold_id_in_retrieved_top10:** `True`
- **gold_rank_if_hit:** `1`
- **LLM triage (ignore if conflicting):** label=`unsure` mode=`other`

### Question

In the redwood repo, which base branch was the merged PR that added GPU queue depth metrics and a scheduler sampling probe targeting?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_d04ffbe63ea44224892533eb0fe95bc6`
_source: full_erb_file:dsid_d04ffbe63ea44224892533eb0fe95bc6__pr-82145-instrument-gpu-queue-depth-and-scheduler-sample-probes.txt_

```text
Instrument GPU queue-depth counters and scheduler sampling probes

Motivation: We need lightweight visibility into real-time GPU submission queue depth and scheduler backpressure to diagnose latency spikes under mixed workloads. This PR adds a low-overhead queue-depth counter set, a periodic sampling probe for the scheduler hot path, NVTX range helpers for correlating samples to kernel submissions, and a small microbenchmark/harness and dashboard for triage. Summary of changes: added queue_counters.h/cc with atomic counters and scoped increment helpers; added scheduler sampling probe that captures queue depth, epoch-id, and active-batch-size at 250Hz; wired counters into the existing Prometheus exporter and exposed new metrics (redwood_gpu_queue_depth_{min,max,avg,p50,p95,p99}, redwood_scheduler_sample_total); added an NVTX-friendly scoped range wrapper to avoid repeated callsites; added a microbench tool (tools/microbench/gpu_queue_sampler.cc) that exercises submission patterns and exports a JSON summary; added a Grafana dashboard template (docs/perf/grafana_gpu_queue_dashboard.json) and a short README with run instructions and recommended alert thresholds; added unit and integration tests for counter rollover and multi-threaded increments. Checklist: [x] unit tests, [x] integration test in CI, [x] perf microbench added, [x] dashboard JSON, [x] changelog entry. Testing: CI: full build + unit tests passed; integration tests exercise a synthetic workload that mimics our batching distribution and show stable counters. Local perf: in our synthetic mixed-latency workload the scheduler sampling probe identified two submission hotspots and the microbench shows an 80% reduction in observed queue-spin time after reducing unnecessary submission retries (this PR does not change retry behavior; we used the tool to validate impact of a follow-up tuning change). Backwards compatibility: metrics are additive and guarded by config flags; default behavior is unchanged. Related: complements ENG-4892 (batch scheduling visibility) and ENG-5021 (kvcache instrumentation).
Adds low-overhead GPU queue-depth counters, a scheduler sampling probe, and Prometheus/Grafana instrumentation for microbench dashboards. No behavioral changes to scheduler logic.
Miguel: Can we keep the sampler disabled by default and gate with a feature flag?; Author: Yes, the sampler respects profiling.sampler_enabled=false by default and the README documents runtime flags.
Lena: Nit: prefer std::atomic_ref for the counter update to avoid extra loads; Author: switched to atomic_ref in latest commit.
Omar: Please add a short e2e test harness that runs the microbench under CI; Author: added an optional integration test job that runs the microbench with a mocked device in CI.
synthetic-microbench: observed 80% reduction in queue spin time after follow-up tuning (sampling validated hotspot)
median-queue-depth: +0.2 (no functional regressions)
p99-latency: <=1.6% regression in one noisy config; mitigations recommended in runbook
KV-cache hit-rate: unchanged within noise
This PR focuses on observation only; operational runbook included for interpreting metrics.
Follow-up work planned: automatic anomaly alerting and a lightweight agent to pin problematic submission paths.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_d04ffbe63ea44224892533eb0fe95bc6` ★ GOLD — Instrument GPU queue-depth counters and scheduler sampling probes
2. `dsid_e4c9e2896967401f8da2dfca247bba09` — add-async-kernel-latency-sampler-and-batching-simulator-microbench
3. `dsid_13875eadc7d14beb99742d8b1ef48608` — Introduce async-prefetch rotary-aware attention kernel with hybrid-striping and adaptive KV cache gating
4. `dsid_c9a1ca32dae14498a89c2ae1b1d5bfa8` — compact attention core: token-aware scheduler + shadow-kv prefetch to reduce tail latency
5. `dsid_0559f1f4179e432ab8e48ce2afeeac35` — Introduce contextual token-latency drilldown, kernel-queue sampler, and alert squelcher
6. `dsid_0c70f57be1bd4e30b01adf979c51a8cf` — Chronological scratch compaction and ephemeral KV binning
7. `dsid_3c86346bb2e2408e93e740f9877f254e` — Scheduler metrics: prefill/decode split, queue depth histograms, and backpressure counters
8. `dsid_6a27b963a92c41d8b8d7e5b6bbb79fc1` — windowed allreduce aggregation and kernel scheduler tuning
9. `dsid_0ba6ff723dd9400ea5c5aabb8098eeae` — Unify CPU hotpath: lightweight scheduler, zero-copy request path, and KV prefetch to reduce serialization
10. `dsid_986e4ae80b894812b093da87368a41ea` — hierarchical-comm-scheduler-with-layer-aware-kernel-selection-and-kv-prefetch-pipelining

### Fill for this row (also include in final JSON array)

```
row_id: 10
question_id: qst_0038::metadata
corpus_scale_size: 40000
condition: meta
auto_hit_at_10: true
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 11

- **row_id:** `11`
- **question_id:** `qst_0041::metadata`
- **corpus_scale_size:** `50000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`other`

### Question

For the North America based SMB prospect evaluating a hosted API for a support chatbot and summarization, what month is the deal forecast to close?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_4c1c5fb53ca2432995ea42adc4330fca`
_source: full_erb_file:dsid_4c1c5fb53ca2432995ea42adc4330fca__company-sparkbarrel-systems.txt_

```text
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
- Need to finalize SSO + audit controls before Procurement will approve paid plan.
- Their devs have a 2-week POC window and limited test credits — want concrete perf numbers quickly.
- Concern about opaque billing during burst spikes.

Next steps (owner):
- Maya to send short perf summary + recommended endpoint config + suggested timeout/backoff code sample (done 2026-03-05).
- Diego to share streaming + small-model fallback example and a short AB test plan (send by 2026-03-11).
- Schedule 30m technical review/POC wrap on 2026-03-12 to agree success criteria (p95 target, cost cap).

Staging & contract: SMB; likely self-serve to start. If POC meets SLOs and security sign-off, move to paid hosted API with committed monthly credits.

Notes tone: choppy bullets, dev questions, a couple paraphrased quotes — typical CRM entry.
2026-02-12: self-serve signup, trial credits allocated
2026-03-01: discovery call — Maya Chen (AE) — initial latency report
2026-03-03: SE deep-dive (Diego) — collected logs + client config
2026-03-05: sent perf checklist and region recommendation (drive link)
2026-03-06: provided client streaming example and timeout template
2026-03-07: customer AB test -> EU traffic to eu-west-1
2026-03-08: follow-up email; customer requested cost cap details
2026-03-12: scheduled 30m POC review/next-step meeting
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_b9feabcc616a441dadb2e6237166b316` — Silvercove Inbound Solutions
2. `dsid_3ad63e1b88fe489b8e6ca8a586915565` — Banyan Inkworks Systems
3. `dsid_5591b2d92c864adb8551a34c6af33056` — Salubrex Health Labs
4. `dsid_4775b0714f064b6ea5875c519857dd77` — NectarLoop HostedAI
5. `dsid_6ded6cb1fa2d4dfeb489e0e9e3095d16` — Mapleridge AssistWorks
6. `dsid_3d2300add2f94ce7b8fa97aada4a10d4` — Sandbar Analytics
7. `dsid_8e3a782937134f83a06e6d961cb40be0` — Mariner Sprocket Digital
8. `dsid_0cb53fb9b05e42c7a69bd7db8de6012e` — VerbaChat Labs
9. `dsid_c73df6b8cc0645439edeabed43cce6d2` — BentoAssist Cloud
10. `dsid_0e553d2eb09c406bb90fd873d112c787` — Lodestone Frugal AI

### Fill for this row (also include in final JSON array)

```
row_id: 11
question_id: qst_0041::metadata
corpus_scale_size: 50000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 12

- **row_id:** `12`
- **question_id:** `qst_0044::metadata`
- **corpus_scale_size:** `25000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

Who is the sales owner for the mid-market product analytics SaaS account that is evaluating Dedicated after a hosted trial and has a next step scheduled for early March 2025?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_676625b7b7064b30a00da4f53fd24f88`
_source: full_erb_file:dsid_676625b7b7064b30a00da4f53fd24f88__company-coppertrail-saas.txt_

```text
CopperTrail SaaS

CopperTrail ran a Hosted API trial and is evaluating Redwood Dedicated for GA to control costs and meet residency/SLA needs. Key decisions hinge on Dedicated pricing, autoscale burst behavior, and legal sign-offs. SE-led sizing provided baseline concurrency and token throughput estimates; next is procurement and final capacity worksheet review.
Account profile: mid-market B2B SaaS (product analytics) building an in-product assistant + search relevance layer. Team: 3 PMs, 6 backend engineers, 2 infra/ops.
Started Hosted API trial 2025-01-10 for feature gated beta (50 internal users -> 2k external beta users). Goal: validate latency and unit economics before Dedicated commit.
POC summary (two-week hosted trial): average QPS observed = ~8 sustained; peak QPS spikes to 120 during release windows. 95th pct concurrency on our test harness = 40 concurrent requests. Production target (GA): steady 25 QPS with planning for bursts to 120 QPS; target p95 latency <= 250ms for short chat path.
Token mix from POC telemetry: ~70% short interactions (<=100 tokens total), ~20% medium (200-600 tokens), ~10% long (>=1000 tokens, mostly summaries and long-context search). Avg token length per request: input ~120, output ~240 in chat flows.
Cost sensitivity: host-team flagged hosted token spend trending 3x higher than forecast due to long summaries and heavy re-runs in testing. Primary driver for Dedicated interest: predictable unit economics and KV/prefix caching options.
Model preferences: prefer Redwood-curated open models (cost vs. quality tradeoff). Want fallback routing: small open quantized model for tail and a higher-quality model for core assistant responses. Also interested in Redwood Optimize suggestions (quant profiles, batching) to hit cost targets.
Security/ops: require VPC option and KMS integration for keys. SOC2 in place internally; legal asks for data residency options for EU customers and audit logging retention policy.
Quotes: AE notes from 2025-02-18 demo — CTO: 'We need a predictable monthly cap; Hosted is great for dev, but we can't run GA if our token bill is a variable.' PM: 'If Dedicated halves our token spend we can justify commit.'
Redwood interactions: API keys issued and sample traffic routed on 2025-01-17. Mid-POC sync 2025-02-05 (cost trend discussion). Demo + capacity workshop 2025-02-18 (see attached deck). Sales sent draft Dedicated pricing and sizing worksheet 2025-02-20.
Open questions from technical workshop: how does Dedicated handle autoscale burst pricing? What's the expected GPU footprint for our mix (estimate provided below)? Any constraints on pinning model variants per route?
Preliminary Dedicated sizing estimate (internal AE/SE calc): baseline concurrency 60 cores-equivalent (handles steady 25 QPS with batching + caching), burst buffer for 120 QPS requires additional 3-4 cards in a pool. Estimated token throughput: 3.2B tokens/month at projected usage pattern — cost model needs to be mapped to Dedicated commit tiers.
POC artifacts: pricing proposal (drive link), token burn spreadsheet (drive link), demo recording (fireflies ff_98765).
2025-01-10: Trial signup (Hosted API, 14-day) — AE kickoff
2025-01-17: API keys issued; initial integration; smoke tests passed
2025-01-24: Baseline metrics captured — avg QPS 6-9; token mix profile collected
2025-02-05: Mid-POC sync — cost trending higher than forecast; SE recommended batching + cache configs
2025-02-12: Internal infra asked for Dedicated cost model and GPU footprint estimate
2025-02-18: Final demo + capacity workshop (live walkthrough of traffic scenarios)
2025-02-20: Sales sent draft Dedicated pricing & sizing worksheet; awaiting budget approval
Review POC token burn and Dedicated sizing worksheet (scheduled 2025-03-04) — confirm budget owner and procurement timeline
budget approval for Dedicated capacity commit
clarify SLA and regional residency options
legal needs example DPA + security FAQ sign-off
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_fd49ed2b9f0b45c4b2a50ff391dd8e2c` — Sunboard Digital Platforms
2. `dsid_a6ac5e583105485fa029e9f9b18fdc3e` — Brookline Inference Solutions
3. `dsid_1b679d7a5cd54d50b4c86aea8af42ac9` — Moonshore Inference Labs
4. `dsid_85961c2d71ed4e77978c304ed29c929c` — AstraCove Product Labs
5. `dsid_2e8c2f98895a40aaa007c6c060dbe12c` — Solaris Arc Cloudware
6. `dsid_2cff5b6b11ce43a3a574e0982637aef2` — KiteAnchor Labs
7. `dsid_c887f6ded8174824a9b88620e603924d` — Sunerra Product Intelligence
8. `dsid_9324383a7b574c5eb732640f07d12eb9` — AutumnRidge Reorder Labs
9. `dsid_6ee6ef4ce1c84921aec1a07b506541fb` — AeroVerge Labs
10. `dsid_a032658b571d4562a1a98485c5adba4d` — Skyline Scribe Solutions

### Fill for this row (also include in final JSON array)

```
row_id: 12
question_id: qst_0044::metadata
corpus_scale_size: 25000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 13

- **row_id:** `13`
- **question_id:** `qst_0048::metadata`
- **corpus_scale_size:** `10000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `HIT` (`True`)
- **gold_id_in_retrieved_top10:** `True`
- **gold_rank_if_hit:** `1`
- **LLM triage (ignore if conflicting):** label=`unsure` mode=`other`

### Question

In the engineering project about bridging a Responses-style API into a runtime event model with streaming and tool-call handling, what release version is this P0 ticket targeting?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_f3af4a0db68c4b15983439460cc73006`
_source: full_erb_file:dsid_f3af4a0db68c4b15983439460cc73006__ENG-99601-responses-bridge-handshake-and-runtime-parity-roadmap.txt_

```text
Responses API bridge: handshake mapping, partial streaming behavior and parity remediation roadmap

Deliver a pragmatic bridge that maps OpenAI Responses semantics into Redwood's runtime event model with minimum behavioral surprises for customers. Key focus areas: (1) handshake and initial metadata mapping (response.id, model variants, content-type headers), (2) streaming delta semantics vs event stream framing (role/author events, token deltas, partial structured outputs), (3) tool/function-calling interactions during mid-stream (when tool requests are emitted and how call results are re-integrated), (4) structured output attachments and schema enforcement for the Console and Optimize pipelines, and (5) safe fallbacks when parity gaps are detected (e.g., missing stop sequences, unknown tool schemas, or truncated tool responses). This ticket covers design, a reference implementation in the runtime translation layer, integration tests, and a staged canary rollout with observability hooks.
Handshake fields from an OpenAI Responses 'response.create' event are mapped to Redwood request/response metadata with 1:1 mapping for id, model, and role when present
Streaming deltas produce token-level events that preserve role boundaries and sequence ordering, verified by the stream-replay harness
Tool/function call events emitted by OpenAI Responses are translated to Redwood's tool-call API with preserved call_id, argument payload, and a deterministic re-integration path for tool results
Structured output attachments are parsed against provided JSON Schemas; invalid attachments are surfaced as 'structured-output-error' with graceful degradation to raw output
Fallbacks: when a parity mismatch is detected the runtime emits a compatibility warning metric and routes to a pre-configured fallback model variant without dropping requests
Integration tests (unit + e2e) covering 95% of mapped event permutations are added to CI and gate the canary rollout
Canary rollout demonstrates <1% increase in error budget burn and less than 80ms p50 additional latency on instrumented endpoints at 10% traffic shift
2025-02-18: Kickoff meeting with Runtime, SDK, Console and QA. Decided to prioritize handshake and streaming mapping before full tool schema validation.
Design doc: https://confluence.redwood.ai/display/RESP/Responses+Bridge+Design (internal) -- contains event mapping table and state machine diagrams.
Initial spike completed: prototype translator implemented in runtime/translator/responses_adapter (PR: https://github.com/redwood-inference/runtime/pull/12345).
Trade-offs: We debated strict 1:1 fidelity vs pragmatic normalization. Chose normalization for: role aliasing (assistant/system), truncation semantics (normalize to Redwood truncation with telemetry), and rate-mapped streaming events to reduce SDK complexity.
Review feedback from PM (Aisha Patel): include explicit 'compatibility_warning' tag in response metadata for tooling to show in Console when a fallback was applied.
Security note from SecOps (Liam O'Connor): ensure tool-call payloads are scrubbed before being recorded in trace logs. Added runtime toggle to redact tool args in traces.
QA test plan uploaded: https://drive.redwood.ai/drive/folders/resp-interop-qa -- includes stream replay fixtures and synthetic tool-call sequences that exercise nested structured outputs.
Metrics to add: responses.bridge.parity_warnings, responses.bridge.stream_reorders, responses.bridge.toolcall_failures. Dashboards: Console -> Observability -> Responses Interop (draft).
Blockers: need SDK patch for JS streaming API to expose 'partialStructured' event type (ENG-99602). Also dependency on kernel scheduling change that can affect latency (ENG-99603).
Staged rollout plan: feature flag + canary at 1% -> 5% -> 10% with 24h observation windows and automated rollback on SLO breach. Default fallback route will be 'responses-legacy' adapter until parity criteria pass.
Next steps: finalize schema validation logic, harden re-integration path for tool results to avoid duplication, and add fuzz tests that simulate out-of-order streaming frames. Assigned to Miguel for implementation and Sofia for specs.
PR checklist: unit tests, e2e harness fixtures, metrics emissions, docs in Confluence, SDK compatibility tests. Target merge to runtime main by 2025-03-14.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_f3af4a0db68c4b15983439460cc73006` ★ GOLD — Responses API bridge: handshake mapping, partial streaming behavior and parity remediation roadmap
2. `dsid_7c6f649b898746079dcd66302c50f8f8` — Typed output sentinel: compatibility & constrained-decoding benchmark
3. `dsid_8db16dd149b74972ae947d5525043b45` — OpenAI Responses compatibility: mapping plan and parity gaps for streaming, function/tool calling, and structured outputs
4. `dsid_1c9140e818384efca371611858fffcdf` — Launch runbook: SDK + API surface (function-calling, structured output, streaming) — docs & samples handoff
5. `dsid_a3954582c60442ddb1924caa03bed22e` — Contract evolution runbook for streaming + tool interfaces and structured outputs
6. `dsid_e48cba98a7764fa8bc47f32f2837b0b6` — Sync sheet & cut-criteria framework for API/Console/Runtime release
7. `dsid_e813c7bf78644243a06f834d0ab92a78` — continuous-json-safety-truncation-retries-procedures
8. `dsid_d6777ded64504da3813a6b6871c7766f` — Live Stream Assertor, Telemetry, and Fallback Playbook for Constrained-Decoding
9. `dsid_bfd2d47aab5449e3b43866cf38aa5cf5` — Streaming fragment reassembler and typed-event surface for Python SDK
10. `dsid_b44e9b54ae344067ab33fa45b234026a` — SDK/API Bridge: launch roadmap, sample kits, telemetry mapping, and rollback runsheet

### Fill for this row (also include in final JSON array)

```
row_id: 13
question_id: qst_0048::metadata
corpus_scale_size: 10000
condition: meta
auto_hit_at_10: true
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 14

- **row_id:** `14`
- **question_id:** `qst_0053::metadata`
- **corpus_scale_size:** `40000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the late-January 2025 technical deep dive with FinBank about private disaster recovery and backup restore, how long was the call in minutes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_c3be99dbca144db488c037dd2f0831ef`
_source: full_erb_file:dsid_c3be99dbca144db488c037dd2f0831ef__2025-01-29-private-dr-and-backup-restore-technical-deep-dive-finbank.txt_

```text
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
Redwood (Sean Gallagher) - Provide a sample restore validation checklist + what logs/metrics are produced for evidence - due 2025-02-07
Redwood (Markus Klein) - Schedule follow-up: 60-min working session to map FinBank components to backup scope and pick supported storage backend - due 2025-02-04
Redwood to send draft backup/restore + DR overview/runbook links and validation checklist.
FinBank to confirm desired DR archetype (single-region restore-in-place vs multi-region failover) and the acceptable RTO window for control plane vs audit logs.
Schedule a follow-up workshop with FinBank SRE/SecArch to finalize encryption/key handling and air-gapped-ish packaging needs.
Meeting header
Date: 2025-01-29
Start time: 16:00 UTC
Duration: 58 min
Title: FinBank x Redwood — Private DR + backup/restore technical deep dive
Attendees (Redwood): Markus Klein, Colin O'Donnell, Hanae Suzuki, Sean Gallagher
Attendees (FinBank): Aisha Patel, Tom Reyes, Nina Shah, Leo Grant

Auto-generated notes (Fireflies)
Summary: Discussed DR expectations and backup/restore approach for Redwood Private, including encryption and restricted-egress operations. Confirmed scope boundaries between app-level backups and Kubernetes/etcd recovery.
Questions: What’s included in the Redwood backup artifact? How do keys work? Can restores be validated automatically? What about limited outbound egress / "air gap" constraints?

Transcript
[00:00] Markus Klein: Cool, alright. Thanks everyone for making time. Goal today is to go a bit deeper than the usual “yes we support DR” and actually talk through what we back up, how restore works, and what we can do in restricted environments. Aisha, do you want to set context from your side?

[00:18] Aisha Patel: Yeah. Thanks Markus. So we’re evaluating Redwood Private for, basically, an internal gen-AI platform. The big blocker is Day-2 ops. We have to show DR readiness to our risk team. And we have two environments: one normal AWS VPC, and another more constrained enclave where outbound egress is… not zero but very controlled.

[00:39] Tom Reyes: And from SRE side, we need clear RPO/RTO per component. Like, control plane config can be maybe 15 minutes RPO, but audit logs are… we have different retention and export requirements.

[00:53] Nina Shah: Plus encryption. Customer-managed keys, and we want to understand if you ever store secret material in the backup, or if it’s just references. And how you handle KMS outages.

[01:05] Markus Klein: Yep, makes sense. Colin and Sean are here to go into the runbook-y pieces, and Hanae for keys/secrets.

[01:13] Colin O'Donnell: I can start with scope. When we say “backup/restore for Redwood Private,” we’re talking primarily about the Redwood control plane state and critical configuration state required to deterministically recreate the deployment: tenant config, routing policies, model pins, auth config, and the internal config database that tracks those. We’re not trying to replace cluster-level disaster recovery.

[01:34] Tom Reyes: So not like Velero everything in the cluster.

[01:37] Colin O'Donnell: Exactly. We see people reach for Velero as a blunt instrument, and it can work, but it’s also a foot-gun if you restore secrets or CRDs in the wrong order. Our approach is: Redwood produces a versioned backup artifact for Redwood-owned state. If you also want to use Velero, we’ll provide guidance for what to include/exclude, but we don’t rely on it.

[02:00] Sean Gallagher: And from an operational standpoint, our runbooks are basically split into: (1) consistent control-plane backup, (2) restore to a fresh cluster or existing cluster, and (3) DR plans by archetype, like single-region restore-in-place.

[02:15] Aisha Patel: What’s “consistent” mean here? Do you stop the world?

[02:19] Sean Gallagher: Not fully stop-the-world, but we do a quiesce step for writes in the control plane. Think “pause mutations” briefly so we get a coherent snapshot of the config DB plus the related manifests/values we need. It’s on the order of seconds to, worst case, a minute depending on environment.

[02:40] Tom Reyes: That quiesce impacts inference?

[02:42] Colin O'Donnell: Inference data plane stays serving. You might temporarily block admin operations like creating a new tenant or changing routing policy. Existing traffic continues. We’re careful about that separation.

[02:55] Leo Grant: Where does the backup get stored? We’d prefer S3 in-region with KMS.

[03:01] Colin O'Donnell: S3+KMS is the default reference. We also have customers who require NFS. For GCS it’s possible but usually only if the deployment is in GCP. For AWS VPC, we’d recommend S3 with bucket policies that only allow access from the backup service account role, and SSE-KMS with your CMK.

[03:24] Nina Shah: Can you clarify the encryption model? Is it just SSE-KMS or do you do application-level encryption before upload?

[03:32] Hanae Suzuki: Great question. We’re moving toward envelope encryption at the artifact level. So the installer/backup tool generates a data key, encrypts the archive locally (AES-GCM), and then encrypts the data key with KMS (or a KMS provider interface, potentially HSM-backed). That way if someone misconfigures the bucket encryption, the artifact is still encrypted.

[03:57] Nina Shah: And the plaintext data key never leaves memory?

[04:00] Hanae Suzuki: Correct. It’s generated and used in-process, and only the encrypted DEK is stored alongside the artifact metadata.

[04:08] Tom Reyes: What exactly is in the archive? Like do you dump Postgres?

[04:13] Colin O'Donnell: It depends on the backing store, but conceptually yes: a consistent snapshot of the config DB plus a manifest file that describes versions, checksums, and component inventory. In some installs it’s Postgres, in others we’ve seen managed equivalents. The runbook calls out the supported snapshot method per datastore. We also capture critical “installer inputs” like Helm release values so you can redeploy deterministically.

[04:40] Aisha Patel: Do you back up Kubernetes objects? Like CRDs, deployments, secrets?

[04:45] Colin O'Donnell: We do not back up the whole cluster. We’ll capture the Helm values and Redwood-specific config objects that are necessary to reconstruct. For CRDs, the safe path is: reinstall the correct Redwood version (which includes CRDs) then restore state. We’ve had issues when folks restore CRDs from old versions and then controllers behave weird.

[05:09] Sean Gallagher: If the cluster itself is corrupted, then you’re in “cluster DR” territory. That’s where etcd snapshots, managed control plane restore, or IaC rebuild come in. We can provide guidance, but it’s separate from app-level restore.

[05:26] Tom Reyes: Okay, but in a real incident we might need both.

[05:29] Sean Gallagher: Totally. Our DR plan docs basically say: choose the failure mode. If it’s “oops we deleted a namespace” or “config DB is bad,” app restore. If it’s “etcd is toast,” then cluster restore first, then app validation.

[05:45] Leo Grant: In the region loss scenario, do you support cross-region restore?

[05:51] Colin O'Donnell: Today the baseline is single-region restore into a clean cluster in the same region. Cross-region is doable if your dependencies are replicated: S3 CRR or copying artifacts, database snapshots to the other region, and you pre-provision the cluster. We can document the pattern but we won’t magically replicate your infra.

[06:14] Aisha Patel: For our risk review, we need to say something like: “RPO 15 minutes, RTO 2 hours” for control plane. Is that realistic?

[06:22] Sean Gallagher: It can be, depending on the size and your automation. For RPO, if you run scheduled backups every 15 minutes and they complete consistently, yes. For RTO, restore time depends on: provisioning a cluster, pulling images, running the restore job, then validation. Two hours is reasonable if you have infra ready.

[06:49] Tom Reyes: Do you have an automated restore drill? Like we can run weekly in staging.

[06:54] Sean Gallagher: That’s part of what we’re building. The idea is: a scheduled restore drill in a non-prod environment that pulls the latest backup, restores to a staging cluster, runs smoke tests, and emits metrics like restore_duration_seconds and last_restore_success_ts.

[07:14] Nina Shah: Evidence is big for us. We need artifacts. Logs, timestamps, checksums.

[07:19] Hanae Suzuki: The backup tool produces a manifest with: backup format version, platform version, list of components, SHA256 checksums, and the encrypted key blob. That manifest can be stored alongside the archive. You can hand it to auditors. We also plan to emit audit events around backup/restore actions.

[07:43] Tom Reyes: That manifest is signed?

[07:46] Hanae Suzuki: We’re planning two layers. Checksums for integrity, plus bundle signing for offline distribution of the tooling itself. For the backup artifact, we can optionally sign manifests. The core must-have is that the artifact is encrypted and integrity-checked.

[08:08] Leo Grant: On the restricted environment: no outbound calls. How does the restore tool behave if it tries to reach your hosted endpoints?

[08:16] Colin O'Donnell: It should not need to. For Private, the backup/restore operations are local to the cluster. The only external dependency is your storage backend (like S3). In air-gapped or restricted egress, you’d use an internal S3 endpoint or NFS. The tooling and docs would be shipped as an offline bundle.

[08:38] Aisha Patel: We’re not fully air-gapped, but basically NAT is blocked except allow-listed domains. Can you support a mode that never tries to “phone home”?

[08:48] Colin O'Donnell: Yes. We have a “no external calls” posture for on-prem style installs, and we can apply that to restricted VPCs too. For example, image pulls would come from your internal registry mirror.

[09:03] Tom Reyes: Let’s talk about secrets. Are secrets in the backup? Like DB passwords, OAuth client secrets.

[09:10] Hanae Suzuki: By default, no. We don’t want secret material in the backup artifact. We back up references: secret names, where to find them, maybe the ARN of a secret in Secrets Manager, that sort of thing. On restore, you’re expected to have those secrets provisioned in the target environment.

[09:31] Nina Shah: Good. But then restore is not fully self-contained.

[09:34] Sean Gallagher: Right, but it’s deterministic if you treat secrets as inputs. Our restore runbook has a pre-flight checklist: “Confirm secrets exist,” “Confirm KMS key access,” “Confirm bucket access,” etc. In regulated environments, secret exfiltration via backup is usually a bigger problem than requiring re-provisioning.

[09:59] Tom Reyes: What about rotating keys? If we rotate the KMS key, can we still restore old backups?

[10:06] Hanae Suzuki: If you rotate by rewrapping within KMS (keeping old key versions available), you’re fine. If you disable or schedule deletion of old key material, you could lose ability to decrypt. We recommend a key lifecycle policy that preserves decrypt for the retention window.

[10:25] Nina Shah: And if KMS is down during backup?

[10:29] Hanae Suzuki: For backup creation, if we can’t encrypt the DEK with KMS, we fail closed. We don’t want a backup artifact produced that’s not properly encrypted. For restore, if KMS is down, you can’t decrypt the data key, so restore can’t proceed. That’s part of your dependency chain for DR.

[10:52] Leo Grant: So KMS availability impacts RTO.

[10:55] Sean Gallagher: Exactly. Most customers treat KMS as a tier-0 dependency. If you’re in AWS, KMS is pretty reliable, but you can also consider multi-region keys depending on your DR design.

[11:10] Aisha Patel: How do you validate restore? Like, what’s the “smoke test” specifically?

[11:16] Sean Gallagher: Minimum: control plane health endpoints are green, background controllers are running, config DB migrations are at expected version, and the Redwood API responds. Then we run a few synthetic requests: create a test tenant (or check an existing tenant in staging), validate routing policy loads, and run a tiny inference request against a known model with expected output shape.

[11:45] Colin O'Donnell: We also validate that model pins and fallbacks are restored. People forget that routing policies are part of “state.”

[11:53] Tom Reyes: Do you validate audit logs?

[11:56] Sean Gallagher: We can validate that audit logging is enabled and that export jobs are configured. Whether you can “replay” logs depends on your retention pipeline. Separate doc from security covers audit log backup/retention.

[12:14] Nina Shah: In our world, audit logs need 1 year retention, immutable storage. That’s usually separate from app DR.

[12:20] Markus Klein: Yeah, we typically treat audit log export as its own pipeline—like to your SIEM or to WORM storage. We can connect the dots but it’s not in the core control-plane backup.

[12:33] Tom Reyes: I want to pressure-test the “no Velero” thing. In practice, we already use Velero for our clusters.

[12:40] Colin O'Donnell: Totally valid. The reason we’re cautious is ordering and version mismatch. If you use Velero to back up namespaces, you might restore a state where CRDs exist but controllers are a different version, or vice versa. If you do Velero, we recommend: exclude Secrets (or at least be explicit), exclude CRDs, and treat Velero as “cluster resource convenience,” while Redwood backup is the source of truth for control-plane state.

[13:13] Tom Reyes: So two-layer approach.

[13:15] Colin O'Donnell: Exactly.

[13:19] Aisha Patel: Can you walk through a restore into a fresh cluster? Like the order.

[13:25] Sean Gallagher: Sure. High-level order:
1) Provision the target cluster and baseline dependencies (ingress, storage class, cert-manager if used).
2) Install Redwood Private at the target version (same or compatible) via Helm/installer.
3) Ensure required secrets and KMS/bucket access exist.
4) Run restore job: download artifact, verify checksums, decrypt, apply DB restore, apply config objects.
5) Run post-restore validation hook (smoke tests) and produce a validation report.
6) Switch traffic: DNS/TLS, or update internal load balancer targets.

[14:08] Leo Grant: DNS/TLS is a pain. We’d prefer to keep the same endpoint.

[14:12] Sean Gallagher: For same-region restore, you can keep the same DNS name. If you’re restoring to a new cluster, you can reuse the certificate if you manage it centrally, or re-issue with the same SAN. The runbook includes the “don’t forget to update certs” checklist.

[14:31] Nina Shah: For encryption, do you support customer-provided keys in an HSM? We sometimes use CloudHSM.

[14:39] Hanae Suzuki: We’re designing a KMS provider interface. Our first-class is AWS KMS. CloudHSM tends to come in via KMS Custom Key Store or your own service. We’ll need to confirm specifics: do you require all crypto ops in HSM, or just key storage? If it’s KMS Custom Key Store, it can work. If it’s a bespoke API, we’d likely need a provider plugin.

[15:10] Tom Reyes: And in the constrained enclave, we can’t call AWS public endpoints. We use VPC endpoints.

[15:16] Leo Grant: Yeah, PrivateLink endpoints for S3 and KMS.

[15:20] Colin O'Donnell: That’s compatible. We’ll document it: S3 Gateway Endpoint, KMS Interface Endpoint, and then restrict bucket policy by VPC endpoint.

[15:31] Nina Shah: Least privilege on IAM is another risk item. We need to show it doesn’t require broad S3 permissions.

[15:38] Colin O'Donnell: We can share a minimal policy: GetObject/PutObject/ListBucket on the backup prefix, and kms:Encrypt/Decrypt/GenerateDataKey on the CMK, plus maybe DescribeKey. No wildcard admin.

[15:56] Markus Klein: We have Terraform modules we can share as a starting point.

[16:02] Tom Reyes: How do you do retention? Do you delete old backups?

[16:08] Sean Gallagher: We don’t automatically delete unless you configure it. On S3, we recommend lifecycle policies for retention. On NFS, you’d do rotation via cron or the backup job. But we’ll emit metrics like “bytes_written” so you can see growth.

[16:30] Aisha Patel: RPO wise, is 15 minutes the minimum?

[16:34] Sean Gallagher: Technically you can do more frequent, but it’s a tradeoff with load and operator comfort. 15 minutes is a common starting point. Some do hourly, some do 5 minutes for very critical configs.

[16:48] Tom Reyes: What’s the failure mode if a backup partially uploads?

[16:53] Colin O'Donnell: The manifest includes expected size and checksums. Restore verifies checksums. If it’s partial/corrupt, restore fails fast. For backup creation, we upload to a temp key then atomically “promote” (rename/copy) so the “latest” pointer only moves when complete.

[17:18] Nina Shah: That’s good.

[17:20] Markus Klein: Let’s check if we’ve hit the key questions: scope, encryption, restricted egress, validation.

[17:27] Aisha Patel: I have another one: version compatibility. If we upgrade Redwood, can we restore an old backup?

[17:35] Colin O'Donnell: We’re adding backup format versioning. Restore checks compatibility: same major, maybe N-1 minor, depending on migrations. If incompatible, it tells you and points to migration steps. We’re trying to avoid “it restores but subtly breaks.”

[17:57] Tom Reyes: We’ve seen that with other vendors. Like “it worked” but half the config is missing.

[18:02] Sean Gallagher: Yeah, we want deterministic outcomes. Also the validation step is meant to catch missing routing policies or tenant config.

[18:12] Nina Shah: Can you produce a report we can attach to a ticket? Like “restore completed, here’s the checks.”

[18:19] Sean Gallagher: Yes. The restore job can output a JSON-ish report and also human-readable. It will include timestamps, artifact ID, checksums verified, and smoke test results.

[18:36] Leo Grant: On the cluster side, you mentioned etcd snapshots. Do you have a runbook?

[18:42] Sean Gallagher: We do, but it’s more of a Kubernetes ops runbook. For managed EKS, etcd snapshots are not directly accessible. For self-managed, you can restore etcd, but it’s risky. We’d rather you rebuild the cluster from IaC.

[19:02] Tom Reyes: That’s aligned with our current practice.

[19:06] Aisha Patel: One concern: our risk team wants “DR game day” evidence. Do you support that?

[19:12] Markus Klein: We can absolutely support a game day. Rafael on our side usually owns the template, but Sean can share the checklist. Typically we do a staging drill: simulate cluster loss, restore, measure time.

[19:30] Tom Reyes: We’d do it in staging first, then maybe a controlled prod drill.

[19:34] Sean Gallagher: That’s what most do.

[19:37] Nina Shah: I want to circle back on air-gap. You said offline bundle. What does that include?

[19:45] Colin O'Donnell: A deterministic bundle layout: the backup/restore CLI, any required container images (or a way to load them into your registry), checksum manifest, signature file, and offline docs. The idea is you can verify it without network.

[20:06] Nina Shah: Signed with what? GPG?

[20:09] Colin O'Donnell: Likely GPG or Sigstore-like approach depending on your environment. For fully offline, GPG is common. We’ll provide the public key and you verify signature.

[20:23] Tom Reyes: And the backup artifact itself is separate, signed or not.

[20:27] Hanae Suzuki: Correct. Bundle signing is for the tooling so you trust what you’re running. Artifact integrity is via checksums and optional signature.

[20:38] Aisha Patel: Okay. I think we have enough to write the initial risk memo, but we need concrete docs.

[20:44] Markus Klein: Yep. We’ll send what we have in draft plus a short “how to think about DR” guide.

[20:50] Tom Reyes: Before we wrap, can we list the things that are explicitly out of scope so we don’t get surprised later?

[20:57] Colin O'Donnell: Sure. Out of scope for Redwood backup: model weights themselves (unless you store them in your own artifact repo), GPU node images, underlying Kubernetes cluster state, and any external systems like your IdP or SIEM. We back up Redwood control plane config and state needed for deterministic redeploy and routing.

[21:22] Nina Shah: And secrets are references, not payload.

[21:25] Hanae Suzuki: Correct.

[21:27] Leo Grant: And storage backends supported are S3 and NFS primarily.

[21:31] Colin O'Donnell: Yes.

[21:33] Markus Klein: Great. Let’s do next steps. Tom, Nina—can you send us your target RPO/RTO and KMS/HSM constraints? We’ll send over the S3+KMS pattern, plus validation checklist.

[21:48] Tom Reyes: Yep. I’ll send what we have. RPO probably 15, RTO 2 hours for control plane, maybe 24 hours for some logs, but I’ll confirm.

[21:59] Nina Shah: I’ll confirm HSM. We might be okay with KMS multi-region keys. But I need to check.

[22:05] Markus Klein: Perfect. We’ll schedule a follow-up working session early next week.

[22:11] Aisha Patel: Sounds good.

[22:13] Sean Gallagher: Thanks everyone.

[22:15] (crosstalk)
[22:16] Markus Klein: Thanks.

Note: Fireflies transcription ended early due to participant drop; remaining discussion (approx. 35 min) continued on the same themes with deeper Q&A on VPC endpoints, bucket policy examples, and restore drill cadence. Key takeaways and action items above reflect the full call per Redwood notes.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_88ac70470c174934b394dec360f60a62` — Orion AI disaster recovery, SSO/KMS & SLA tabletop
2. `dsid_aa49078d78d24048a24dc79743033225` — Multi-tier fallback and SLA alignment — discovery with Archipelago Ventures
3. `dsid_d3e3da235df940bca76d3202bac77ec5` — Security governance, uptime SLA & escalation workshop with Bluecliff Capital
4. `dsid_4175fd65c25a4c79b9cf3090a11eb870` — Incident Response, BCDR & Escalation Review - Acme Retail Systems
5. `dsid_9ff022b2877240ff86f5fb3efc98ac29` — Strategic Health & Burn Council - Northpoint Health Q1
6. `dsid_cc8d0c4da15b494badd135e32a27fa03` — Resilience, SSO/KMS Orchestration & SLA Tabletop — Northbridge Systems
7. `dsid_c5c7dddf71a444fda03fa312accb9e2f` — Rapid rollback rehearsal and chaos simulation handoff
8. `dsid_f03e9c26da514f7fa2e33fccbb9fda9d` — Fallback policy stress test intake - discovery with Equinox Labs
9. `dsid_0400240ded8b4d1e8a5ecff2b3bffa11` — Regional fallback strategy discovery with Helios Analytics
10. `dsid_909c474ff72047428ba5dcf0f03844a3` — ForestFall degradation fallback & resilience sprint planning

### Fill for this row (also include in final JSON array)

```
row_id: 14
question_id: qst_0053::metadata
corpus_scale_size: 40000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 15

- **row_id:** `15`
- **question_id:** `qst_0054::metadata`
- **corpus_scale_size:** `100000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

Who is listed as the owner of the draft internal notes document about an onramp for a claims connector involving a private deployment in an AWS VPC?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_f8b3bf0c730f44f4a24981a3d4cd9c49`
_source: full_erb_file:dsid_f8b3bf0c730f44f4a24981a3d4cd9c49__mistral-claims-connector-onramp-notes.txt_

```text
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
- Cost sensitivity: They want an initial PoC to run for 6 weeks with cost reporting and a rollout plan to Dedicated reserved capacity if performance looks good.

Initial technical constraints we captured (first-pass):
- Must deploy Redwood Private in-customer VPC with control plane connectivity via peering or private link (no public internet flow for PII).
- Use customer CMK for at-rest and in-flight keys they control.
- Provide an on-prem style connector for their SFTP -> S3 pipeline or a lightweight agent to pull files.
- Model choices: start with a smaller generation model variant for triage/classification and reserve larger LLM for summarization. Need quantization/latency benchmarks in us-east-1 GPU types.
- Tokenization gotcha: OCR produces many line-breaks and weird tokens; need to canonicalize before prompt construction (strip headers, page numbers).

Operational gotchas / risks (call-time impressions):
- KV cache warm-up: their pattern will hit many similar claimant names; if we warm caches incorrectly we might leak identifiers across sessions. Need strict tenant isolation keys and per-claim caches.
- Redaction as a function call: avoid returning raw PII in first-pass responses. Prefer a model->function pipeline: run redaction model, then triage model on redacted text, then attach redaction artifacts to the claim object.
- Attachment OCR cost: OCR volume is significant; propose doing OCR in their infra (they already have OCR cluster) and pass cleaned text to Redwood.
- Backpressure: burstiness during shift changes could exceed their Dedicated burst capacity; suggest autoscale policies + graceful degrade to classification-only tier (cheaper model) instead of failing entirely.
- Logging: must scrub any PII before logs leave host. Trace IDs are fine but avoid having excerpts in open logs.

Suggested Redwood pattern / quick architecture (notes for internal use):
1) Ingest: SFTP -> S3 (customer account). Optional lightweight pull agent (connector repo PR #421) that uploads metadata to customer Kinesis.
2) Preprocess: OCR inside customer's infra; run canonicalizer lambda to remove headers/page nums and emit chunked documents (chunk size target 1200 tokens).
3) Private endpoint: Redwood Private deployed via VPC private link; model routing policy: triage model (cheap) -> redaction function (function-calling) -> summarizer (larger model async).
4) Storage: embeddings for retrieval stored in customer-hosted vector DB (they mentioned Pinecone currently) and we provide emb-only writes; no raw text mirrored in Redwood-control-plane storage.
5) Observability: route SLO metrics to their Datadog; configure token-level cost metrics and a per-route budget alert.

Action items / next steps (owner in parentheses):
- Create intake Jira tickets capturing: connector agent work, VPC provisioning steps, KMS integration, auditing retention, model benching (Daniel). (JIRA: ENG-4821)
- SE -> produce a baseline cost/latency estimate for a PoC (Priya) due 2025-02-20.
- SRE -> validate Dedicated sizing for 1500 daily concurrent agents + 120 r/s bursts; propose autoscale policy parameters (Ethan) due 2025-02-21.
- Legal/security intro: schedule 1:1 with Mistral security to discuss CMK/HSM requirements and compliance paperwork (Priya + Sally in security). Target w/c 2025-02-24.
- Ask Mistral to share a sanitized sample claim + 3 representative PDF attachments to run tokenization and OCR cost baseline (Mistral deliverable).
- Draft an SOW outline for a 6-week PoC including success criteria: average triage precision >= 85%, 95th-latency < 350ms on short prompts, zero data egress outside their account (Priya).

Open questions / blockers we need answers for (captured to avoid follow-up loops):
- Do they require that redaction artifacts (masks, offsets) be retained with the original object only in their S3, or can Redwood store metadata with obfuscated IDs? (Mistral decision)
- Will they accept a Private control plane that communicates with Redwood control plane for telemetry only over PrivateLink? Or must control plane be fully customer-managed? (Tyrell to confirm)
- Is the current Pinecone instance accessible from our Private deployment or do we need to push embeddings only to a customer-managed vector DB? (integration detail)

Notes to self / SE tips for next meeting:
- Bring a simple demo flow showing redaction-as-first-class step (function call pattern) and a canary fallback that returns classification-only when summarizer unavailable.
- Prepare a mini-benchmark with two model variants: fast-gen (for triage) and high-quality (for summarization) on p3/rtx benchmarks in us-east-1.
- Show cost delta between streaming short responses vs non-streamed for agent UI (token-level microcost math).

Meeting artifacts to attach to Jira/Confluence:
- Put sanitized sample files in a secure Confluence page and link in the Jira ticket.
- Link to the connector PR for the lightweight agent and call out known TODOs.

Status: waiting on sanitized sample and Tyrell confirmation re: control plane connectivity. Planning a 45m technical walkthrough (deep dive + SRE sizing) w/ Mistral week of 2025-02-24.

Random scribbles (ignore):
- consider embedding TTL policy for claimant vectors (30 days?) to reduce long-tail storage costs and meet privacy regs.
- if they want HSM later we can swap CMK path with minimal infra changes but call it out in SOW as optional add-on.

End.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_10daee01b2fc4bf98c5a75569af7aabd` — CedarGate VPC Solutions
2. `dsid_a20051645422436ea586508a46255fd0` — StrataGuard Analytics
3. `dsid_cd9f545c273e4883be9f8d52d267466d` — Third-Party Integration Readiness and Compatibility Guidelines for Private Deployments
4. `dsid_4bba2fec619f42a9bf29b58be2cded25` — Pallisade Guardian Cloud
5. `dsid_85593be116884060a4505b103ff3e897` — Archipelago Enterprise Solutions
6. `dsid_573ca1fc195e450e85e3f10d1a068cf6` — HelmBridge Healthcare
7. `dsid_01fbf5f87c9242aca7b31e4f0d0c10a7` — Pinnacle Vaultworks
8. `dsid_c6fec429e5104024a0c749fa14664ab1` — Harborline Insurance Tech
9. `dsid_d98cd5211d01496bbf4d6f650a6f1316` — Seacliff Private Inference
10. `dsid_3c58c6154d1e40ceb3927a04d14f51ed` — Veridian RegTech Labs

### Fill for this row (also include in final JSON array)

```
row_id: 15
question_id: qst_0054::metadata
corpus_scale_size: 100000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 16

- **row_id:** `16`
- **question_id:** `qst_0056::metadata`
- **corpus_scale_size:** `25000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the users drive area, which draft engineering SRE doc owned by Aisha Patel was last modified in early March 2026 about replaying a multi-region fallback incident?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_81323a96121047cf98e958463e33d80a`
_source: full_erb_file:dsid_81323a96121047cf98e958463e33d80a__fallback-replay-command-log.txt_

```text
Fallback replay — command log and breadcrumbs

Notes to self: quick replay checklist and command history for the multi-region fallback incident on 2026-02-11. Intended as a reproducible scratchpad to run later in staging and to hand off to oncall for follow-up.\n\nSummary / what happened\n- Around 2026-02-11T21:06Z we saw a spike of route_ejections + regional fallbacks originating from EU-west (az-eu-3).\n- Clients observed elevated latency and ~2.7% 5xxs for about 18 minutes; smart-routing triggered fallback to compatible model variant in us-central for some traffic.\n- Automatic rollback to primary region was slow; suspect policy hysteresis + bad kvcache priming.\n\nObservations gathered (metrics + quick reads)\n- Route ejection metric: route_policy.eject_count[route=chat-text,region=eu-west] increased from 0 to 106 over 6m.\n- Error class in traces: \"handshake_timeout\" + \"kv_cache_miss\" mixed with failed tcp handshakes.\n- Token lat p50 jumped 30ms -> 220ms for routed requests to fallback target.\n- Tracing showed request ids that crossed regional boundary had missing kv_cache headers (x-kv-prefix absent).\n\nImmediate commands I ran (copy/paste friendly)\n# grab recent traces for region slice (3x sources)\nkubectl -n prod logs deploy/route-proxy --since=25m | rg \"region=eu-west\" -B3 -A4 | sed -n '1,500p' > /tmp/eu-west-traces-20260211.log\n\n# sample telemetry query (metrics backend)\ncurl -s \"https://metrics.internal/api/query?metric=route_policy.eject_count&from=2026-02-11T20:50Z&to=2026-02-11T21:30Z&tag=route:chat-text\" | jq . > /tmp/eject-count.json\n\n# fetch routing table at time of incident (config-db)\nredis-cli -h conf-db.prod.internal HGETALL \"routes:chat-text:2026-02-11T21:00Z\" > /tmp/route-config-snapshot.txt\n\n# check last rollout for model variant used as fallback\ngh pr view 842 --json title,body,commits > /tmp/pr-842-summary.txt\n\n# repro request to emulate region failure by forcing route header (staging)\ncurl -v -H \"X-Client-Region: eu-west\" -H \"X-Force-Route: chat-text\" -H \"Authorization: Bearer $STAGING_KEY\" \\\n  \"https://staging.api.redwood.ai/v1/generate\" -d '{"prompt":"hi","max_tokens":10}' --write-out \"\\\\nHTTP_CODE:%{http_code}\\\\n\" --connect-timeout 6 --max-time 10 > /tmp/repro-response-1.txt 2>&1\n\nObserved snippet (from repro-response-1.txt):\n> * Connection timed out after 6001 milliseconds\n> HTTP_CODE:000\n> curl: (28) Operation timed out after 6002 milliseconds with 0 out of 0 bytes received\n\nHypotheses (ranked)\n1) Prefix/KV cache warming mismatch: some routed requests lost the x-kv-prefix header and hit cold model instances in fallback region -> cold start latency cascades and then triggers ejection policy.\n2) Network egress flakiness between eu-west and internal infra (TCP handshake timeouts) causing route-proxy to mark backend unhealthy and initiate fallback.\n3) Fallback policy threshold combined with slow retries (3 retries x 5s) exaggerated the outage window.\n4) Load/queueing: sudden burst caused queue growth; autoscaler in dedicated pools didn't scale fast enough for fallback targets.\n\nError snippets pulled from logs\n[route-proxy] 2026-02-11T21:07:12Z ERROR route-eject route=chat-text region=eu-west reason=handshake_timeout details=\"tcp handshake failed to 10.12.45.9:443 after 5000ms\" trace_id=tr-0a1b2c\n[kv-sync] 2026-02-11T21:07:14Z WARN kv-cache miss prefix=absent route=chat-text instance=fallback-us-3\n[router] 2026-02-11T21:09:01Z INFO fallback-invoked route=chat-text target_variant=chat-small-v2 reason=policy_eject\n\nReplay / repro plan (staging, controlled)\n- Goal: reproduce route_eject behavior deterministically and capture full packet traces + spans.\n- Steps:\n  1) deploy a config with short eject thresholds in staging (eject_error_rate>1% over 30s) so we can trigger without broad impact. -> config name: test-eject-short\n  2) instrument a small load generator to send 200 qps with X-Client-Region: eu-west header for 10 minutes.\n  3) simultaneously introduce intermittent packet loss to fallback target (tc qdisc netem 100ms delay 10% loss) on staging fallback nodes.\n  4) run the same curl repro above to observe curl timeout behavior.\n\nCommands to set up simulated network flakiness (staging nodes)\n# SSH into fallback node (staging-fb-3)\nssh core@staging-fb-3\nsudo tc qdisc add dev eth0 root netem delay 100ms loss 10% 25%\n# when done:\nsudo tc qdisc del dev eth0 root netem\n\nLoad generator (minimal)\n# quick golang wrk-style loop (run from bastion)\nfor i in {1..200}; do \n  curl -s -o /dev/null -H \"X-Client-Region: eu-west\" -H \"X-Force-Route: chat-text\" -H \"Authorization: Bearer $STAGING_KEY\" \\\n    \"https://staging.api.redwood.ai/v1/generate\" &\n  sleep 0.005\ndone\n\nTrace capture tips\n- Start tcpdump on both sides to capture SYN retransmits and timestamps: sudo tcpdump -i eth0 -w /tmp/fb-syns.pcap 'tcp port 443 and (tcp[tcpflags] & tcp-syn != 0)'\n- Increase sampling rate in tracing (temporarily) for route-proxy: setenv TRACE_SAMPLING=0.8 in deployment config and rollout.\n\nQuick bash 'replay' script prototype (staging)\ncat > /tmp/replay-failover.sh <<'EOF'\n#!/bin/bash\nSTAGING_KEY=REDACTED\nfor i in $(seq 1 60); do\n  curl -s -H \"X-Client-Region: eu-west\" -H \"X-Force-Route: chat-text\" -H \"Authorization: Bearer $STAGING_KEY\" \\\n    \"https://staging.api.redwood.ai/v1/generate\" -d '{"prompt":"ping","max_tokens":6}' --max-time 8 -o /tmp/p.$i.json &\n  sleep 0.1\ndone\nwait\nEOF\nchmod +x /tmp/replay-failover.sh\n\nNotes about traces and correlation\n- Capture request ids (x-request-id) from route-proxy logs and align with trace ids. Some traces from the incident had missing kv-pref tags which correlate with the kv-cache miss warnings.\n- Pay attention to rollout metadata: if fallback target was a different model family (eg chat-small-v2 vs chat-base) we will see tokenization differences and potentially token-level latency variance.\n\nWhat to check post-replay (artifacts to gather)\n- pcap files from both sides /tmp/fb-syns.pcap\n- route-proxy logs with trace ids (time window)\n- redis conf-db snapshot used for routing keys\n- metrics snapshot: route_policy.eject_count, token_latency_p50/p95, instance_cpu, queue_length\n- sample payloads and responses to check for missing x-kv-prefix header\n\nShort-term mitigations to propose (if reproduced)\n- Reduce eject hysteresis or increase sensitivity window to prevent mass-ejection cascades (only as a temporary experiment).\n- Add aggressive KV prefetching for recently-failed routes to avoid cold-start hits on fallback targets.\n- Add a temporary network health proxy to detect cross-region TCP anomalies and mark them for manual review instead of automatic full-eject.\n\nOpen questions / TODOs\n- Did the routing config use 'regional-preference=soft' or 'hard'? need to confirm from conf-db snapshot.\n- Which commit introduced the fallback variant change 2026-02-10? correlate with GH PR 842.\n- Should we add a \"grace window\" for kv-pref absence before ejecting? (hypothesis: 30s)\n\nHand-off checklist (for next oncall)\n- Run replay script in staging, collect pcaps and logs, upload to shared debugging bucket: gs://redwood-debug/fallback-replays/2026-02-11/\n- Attach route-proxy logs + trace ids to JIRA CON-4281 and ping Priya for model-family context.\n- If reproduced, propose rollout of prefetched-kv experiment to prod-canary group.\n\nEnd of scratchpad. Will refine after staging replay.\n\n-- Aisha\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_eafe4383765542a183b7ff9f171ee222` — Consolidate routing drain detection and harden fallback resilience after multi-region misroutings
2. `dsid_5c2f8d2ea0f24dbb9fb0b5e342d669e6` — Surgical traffic remediation and staged rollback playbook for mixed-hosted/dedicated cross-region routing incidents
3. `dsid_e28c2b76f9ae43bdb6e809f2acf37930` — Region failover sequencing bug and priority shed policy consolidation
4. `dsid_aca62fe6a1c84870a36208b32749ea76` — Shadow failback timing exposed circuit-breaker coordination gap causing SLO misses
5. `dsid_3fc55e5263f14129af120e912bb79e0b` — Coordinated cross-region traffic drain with tenant-priority and emergency hotpatch
6. `dsid_4b52a93a47474cb292df6a79917f97ff` — Regional ejection from delayed telemetry leading to fallback amplification — incident retrospective
7. `dsid_90d9b4c489fe4f689324379fd42d5190` — Tiered-region-eviction-and-rollback-protocol + customer-bridge for cross-region KV desync
8. `dsid_97a1326a4ecb49afa2fdb7edd3e985d6` — Stabilize observability fanout after event gap recovery (customer escalations)
9. `dsid_8f050e5e55374b72a2265597eb6fdb1e` — Regional traffic surge, partial SLO degradation: incident analysis and corrective roadmap
10. `dsid_595af30d9c194f8ea1a068a39dd9cedd` — Proactive congestion-island detection and sticky-region guardrails

### Fill for this row (also include in final JSON array)

```
row_id: 16
question_id: qst_0056::metadata
corpus_scale_size: 25000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 17

- **row_id:** `17`
- **question_id:** `qst_0063::metadata`
- **corpus_scale_size:** `100000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

For the SMB edtech account in North America that wants a hosted API for K-12 copilots, who is the sales owner listed in the record?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_15dd15bfbd0f42c485a9b5b9ace6a3d1`
_source: full_erb_file:dsid_15dd15bfbd0f42c485a9b5b9ace6a3d1__company-cobalt-campus-innovations.txt_

```text
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
2026-03-04: sent security questionnaire and sample SLA language (drive:/Redwood/EDU/pricing_edu_tiers_v2.pdf)
2026-03-05: Ben ran quick test against public model; reported moderation flags too aggressive — wants tunable thresholds
2026-03-09: SE follow-up (Aaron) on token budgeting and sample configuration options
2026-03-10: requested sandbox keys and short POC plan; legal indicated district procurement steps required
Planned 2026-03-22: 30m POC kickoff to provision sandbox and walk through integration
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_e555234794034e218991ca49a2ffb3ea` — Cascade Copilot Solutions
2. `dsid_562d40ac95ef4410919e6103788b9b6b` — ZenithClass Education
3. `dsid_cf4056237f4747cab4a5bde4728ce77a` — Papertrail Learning Hub
4. `dsid_715ad99c826a4e1fb5002c553f4b16d7` — Academic Ally AI
5. `dsid_8ad05e98218845e9b5e4fc4275eba6c4` — PencilCore Education
6. `dsid_9a679ab76b7e425dbbd31fa1c7dda1c3` — Lodestar Classroom Tools
7. `dsid_c1c9c05711914698b1c6e97a985af9da` — Snowberry ScholarWorks
8. `dsid_2416d1a0ff034d0586046642daffd0eb` — Cerulean Campus AI
9. `dsid_de9ed80a929e4794854467cf5afd6d63` — Sage Scholar Labs
10. `dsid_917abe74a753481baf00f0bc5f4588a9` — PebblePath Education

### Fill for this row (also include in final JSON array)

```
row_id: 17
question_id: qst_0063::metadata
corpus_scale_size: 100000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 18

- **row_id:** `18`
- **question_id:** `qst_0068::metadata`
- **corpus_scale_size:** `50000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

For the SMB B2B SaaS account in discovery that needs audit logging and is evaluating a hosted API for an in-app chat assistant with streaming latency concerns, who is the assigned solutions engineer?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_d9a7de9e7cfc4fe0b7b57765b6d25ad9`
_source: full_erb_file:dsid_d9a7de9e7cfc4fe0b7b57765b6d25ad9__company-stillwater-dialogue.txt_

```text
Stillwater Dialogue

Lead source: inbound signup + demo request from in-app widget. CTO (Evan Marquez) + Eng lead (Priya Nambiar) on call 2026-02-18.

Context:
- Seed-stage B2B SaaS: product = customer success workflow tool embedded into SaaS apps.
- Primary feature: lightweight in-app chat assistant that answers product-specific FAQs, surfaces relevant docs, and can hand off to live agents.
- Must support streaming tokens for quick perceived latency; desktop web + mobile web delivery.
- Current prototype uses open-source model hosted on small GPU; looking to switch to hosted API for reliability and faster iteration.

Key asks / constraints:
- Target p95 response time (start of stream) &lt;= 120ms, target tail p99 &lt;= 300ms for 1-2 concurrent users per session. Emphasis on perceived latency (streaming first token).
- Cost sensitivity: startup budget, expects pay-as-you-go; interested in cost per 1k tokens and potential token batching suggestions.
- Model preference: prefer smaller low-latency variants (eg Llama 2-Chat family or similar) with good safety defaults.
- Routing: want single-region routing (us-west) initially; may add eu later.
- Security: audit logs required; SSO not a blocker now but will be in Q3.

Recent activity (timeline):
- 2026-02-10: Signup via Hosted API quickstart; created account and ran smoke tests.
- 2026-02-12: Automated email with onboarding links; engaged with docs on streaming endpoints.
- 2026-02-16: Eng questions in Gmail thread about sample code for streaming; sent snippet linking to SDK. (thread-fX2k9q20260216)
- 2026-02-18: Discovery call (ff_0a9b3c-stillwater-call-20260218) — demo of prototype; detailed latency targets; requested pricing examples for 100k tokens/month.
- 2026-02-19: Technical request sent: need sample latency benchmarks in us-west for small chat models; SE assigned.

Quotes / paraphrases from call:
- "We need the assistant to feel instantaneous — users bounce if first token takes too long." — Evan, CTO.
- "If you can show streaming under 150ms most of the time, we can move our traffic off the self-hosted infra." — Priya, Eng Lead.

POC plan discussed:
- Short POC: 2 weeks, endpoints on Hosted API, instrument streaming start times, compare 3 model variants (fast-small, standard, high-quality).
- Success criteria: median time-to-first-token &lt;= 80ms, p95 &lt;= 120ms in us-west under dev load; acceptable cost under $1k/month during POC.

Open questions for Redwood:
- Any streaming SDK options for the frontend that minimize latency (websocket vs SSE best practice)?
- Recommendations for prefix caching across sessions (we have heavy repeated prompts per customer).
- Any sandbox rate limits that will affect realistic POC?

Suggested next steps (AE):
- Send sandbox API keys and quickstart streaming example tailored to their frontend stack (React + mobile web).
- SE to run small benchmark in us-west and share p50/p95/p99 numbers for the three recommended models.
- Share a one-page cost estimate for expected 100k tokens/mo and notes on batching/caching levers.

Internal notes (AE):
- Likely convert to self-serve paying customer if POC shows low tail latency; upsell path to Dedicated in 12-18mo if usage grows.
- Watch for SSO/evidence of enterprise procurement signal — CTO mentioned SOC2 exploratory plans.
- Add to drip sequence for streaming best practices + case studies.

2026-02-10: Signup - created account and smoke tests
2026-02-12: Onboarding email - consumed streaming docs
2026-02-18: Discovery call - demo + latency targets
2026-02-19: SE assigned - requested us-west benchmarks
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_3c69e5d0b7a6462d9c7d54f40dbb914d` — SpruceTop AssistKit
2. `dsid_1c2a8f0a58244503800e031d4e1980a8` — Humble Harbor AIWorks
3. `dsid_3f6b75da6a0745c197dd3ee4f6207e0d` — Mosswood EchoAI LLC
4. `dsid_554b411fbaed4e908d7a5f425a109000` — Crownbrook ConverseHub
5. `dsid_451062cb78a04e08adb918f8c77a3748` — SableBeam Assist
6. `dsid_c73df6b8cc0645439edeabed43cce6d2` — BentoAssist Cloud
7. `dsid_ea23b1139d4141c483f46443089031e0` — Sable Counsel LLC
8. `dsid_a3ff6f6eec4b44f69c0e88303c264c65` — Elmbridge AssistCo
9. `dsid_0d53c29e820a4a9bad06c8b5e00cd889` — Luminaris Chatdesk
10. `dsid_51183030e764419caca09cfe647048e7` — Banyan Loop AI

### Fill for this row (also include in final JSON array)

```
row_id: 18
question_id: qst_0068::metadata
corpus_scale_size: 50000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 19

- **row_id:** `19`
- **question_id:** `qst_0069::metadata`
- **corpus_scale_size:** `10000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

Who is the solutions engineer assigned to the mid-market product analytics SaaS account running a two-week parity POC before moving from a hosted LLM API to dedicated nodes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_b9eb7e39bc2e4f65814c42358089d49b`
_source: full_erb_file:dsid_b9eb7e39bc2e4f65814c42358089d49b__company-mariner-prism-software.txt_

```text
Mariner Prism Software

Mid-market SaaS (product analytics) evaluating Redwood Hosted for a migration from an existing OpenAI-compatible provider. Running a 2-week parity POC to validate prompt parity, latency, and hallucination/regression metrics before moving to Dedicated. Primary concerns: prompt parity, EU data residency, and predictable node pricing.
Background: mid-market product analytics vendor — they provide in-app insights + on-demand NLG for product managers.

Initial ask: migrate from current LLM API provider (uses OpenAI-compatible stack) to Redwood Hosted for speed/cost, then transition to Dedicated for production isolation. Need compatibility layer for existing SDK calls and strict prompt parity for customer-facing features.

Conversation highlights: 
- Demo (2026-02-28): showed Redwood Hosted API latency and streaming; CTO impressed by per-route latency breakdowns.
- Quote from CTO (Evan Morales): "We cannot accept regressions in intent extraction or misclassifications — that's our SLA to customers."
- Technical lead (Maya) emphasized tokenizer / truncation differences and prompt templating causing drift during initial migration.

POC requirements (customer provided): 
- Run a seeded test set (10k prompts) comparing current provider vs Redwood Hosted for intent accuracy, hallucination rate, and token cost.
- Benchmarks: 95% parity on intent labels, <2% delta in hallucination on root-cause search, median tail latency <120ms for single-turn chat, sustainable throughput of 20 req/s per model instance.
- Must validate streaming/stop-sequences behave identically and function/tool calling mapping is 1:1.

Technical notes from SE review (Ravi): 
- Plan: add lightweight compat shim to translate their existing OpenAI-style calls to Redwood API; highlight differences: response-chunk boundaries, newline handling, leading spaces in tokenizer, and default sampling params.
- Suggested mitigation: run prompt normalization layer + deterministic temperature settings in POC; capture token-level diffs.
- Important: KV cache behavior and prefix caching could change cost/latency profile; include tests with long conversation contexts.

Timeline & recent activity: [bulleted] 
- 2026-02-10: Intro call with AE (Alexandra) + TL + CTO; capture pain points.
- 2026-02-18: Security questionnaire received; InfoSec flagged data residency requirement for EU customers.
- 2026-02-28: Hosted API demo (ff_2026-02-28_1258_mariner-demo).
- 2026-03-03: Technical deep-dive with SE (Ravi) — mapping existing RL prompt templates.
- 2026-03-05: Migration plan review meeting (ff_2026-03-05_0943_migration-review).
- 2026-03-08: Shared POC scope & test harness templates (drive link).
- 2026-03-10: Pricing alignment call; customer requested node pricing scenarios for Dedicated (reserved + burst).

Risks & concerns: 
- Prompt parity: small syntactic differences causing large label flips on edge cases.
- Regression detection: Customer insists on automated regression alerts tied to prompt sets (expects Redwood Optimize hook).
- Legal/residency: EU-hosted Dedicated nodes needed for 30% of their user base.

Commercial notes: 
- Current spend with existing provider: ~$40k/month.
- Customer expects 10-20% cost savings after tuning (batching/quantization) on Dedicated.
- Investing in Redwood due to better observability (per-route token breakdown) and rollout controls (canary/A-B).

Next steps (short): 
- Deliver POC test harness and seed dataset by 2026-03-12.
- Start Hosted API parity run week of 2026-03-16 (2 weeks).
- Prepare Dedicated node pricing scenarios and a migration checklist (including drive links and Jira templates).

Quote snippets to use in playbook: 
- "We need parity, not just similar outputs. If it changes user behavior we can't ship." — Evan, CTO.
- "Show me the regressions before we sign; we'll sign if we can quantify and remediate." — Maya, Technical Lead.

AE notes / internal ask: 
- Provide SE time for parity debugging during POC (2-3 days/week).
- Product questions: support for OpenAI-compatible function-calling mappings (edge cases).
- Ask pricing to prepare 12/24 month reserved node scenarios with EU residency option.

2026-02-10 Intro call (Alexandra + TL + CTO)
2026-02-18 Security questionnaire received; InfoSec flagged EU residency
2026-02-28 Hosted API demo (ff_2026-02-28_1258_mariner-demo)
2026-03-03 Technical deep-dive with SE (Ravi)
2026-03-05 Migration plan review (ff_2026-03-05_0943_migration-review)
2026-03-08 Shared POC scope & test harness
2026-03-10 Pricing alignment call
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_de9c1d389e964346a5d863550ba817a2` — Hightide ProductWorks
2. `dsid_8ca703d991844bd195b4b8fdc16040fd` — Copperfield Nimbus Solutions
3. `dsid_2a640cd6a0f44f07bd772d630f650e34` — PillarWave Analytics
4. `dsid_75fff671684246fc80766d44866bf248` — Sparrowtail Insights
5. `dsid_f43c071c3ace43cca4170bdece263a69` — Southbank Sentry Solutions
6. `dsid_d2d62518de7849f8b62097aa09be7701` — VerityLane Product Labs
7. `dsid_f9f5ba9463e148568f19b479f835147b` — PraxisLoop CX Systems
8. `dsid_df25e31bc79b4764ad3945872ee1f87d` — SummitGrove Product Labs
9. `dsid_4b0f5e573e5e4ce8bbbcf370c3ea7eaa` — NorthPoint Signalworks
10. `dsid_947baa655c154bf7a8a853e8c70f9fda` — Lotus Helm Analytics

### Fill for this row (also include in final JSON array)

```
row_id: 19
question_id: qst_0069::metadata
corpus_scale_size: 10000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 20

- **row_id:** `20`
- **question_id:** `qst_0069::metadata`
- **corpus_scale_size:** `50000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

Who is the solutions engineer assigned to the mid-market product analytics SaaS account running a two-week parity POC before moving from a hosted LLM API to dedicated nodes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_b9eb7e39bc2e4f65814c42358089d49b`
_source: full_erb_file:dsid_b9eb7e39bc2e4f65814c42358089d49b__company-mariner-prism-software.txt_

```text
Mariner Prism Software

Mid-market SaaS (product analytics) evaluating Redwood Hosted for a migration from an existing OpenAI-compatible provider. Running a 2-week parity POC to validate prompt parity, latency, and hallucination/regression metrics before moving to Dedicated. Primary concerns: prompt parity, EU data residency, and predictable node pricing.
Background: mid-market product analytics vendor — they provide in-app insights + on-demand NLG for product managers.

Initial ask: migrate from current LLM API provider (uses OpenAI-compatible stack) to Redwood Hosted for speed/cost, then transition to Dedicated for production isolation. Need compatibility layer for existing SDK calls and strict prompt parity for customer-facing features.

Conversation highlights: 
- Demo (2026-02-28): showed Redwood Hosted API latency and streaming; CTO impressed by per-route latency breakdowns.
- Quote from CTO (Evan Morales): "We cannot accept regressions in intent extraction or misclassifications — that's our SLA to customers."
- Technical lead (Maya) emphasized tokenizer / truncation differences and prompt templating causing drift during initial migration.

POC requirements (customer provided): 
- Run a seeded test set (10k prompts) comparing current provider vs Redwood Hosted for intent accuracy, hallucination rate, and token cost.
- Benchmarks: 95% parity on intent labels, <2% delta in hallucination on root-cause search, median tail latency <120ms for single-turn chat, sustainable throughput of 20 req/s per model instance.
- Must validate streaming/stop-sequences behave identically and function/tool calling mapping is 1:1.

Technical notes from SE review (Ravi): 
- Plan: add lightweight compat shim to translate their existing OpenAI-style calls to Redwood API; highlight differences: response-chunk boundaries, newline handling, leading spaces in tokenizer, and default sampling params.
- Suggested mitigation: run prompt normalization layer + deterministic temperature settings in POC; capture token-level diffs.
- Important: KV cache behavior and prefix caching could change cost/latency profile; include tests with long conversation contexts.

Timeline & recent activity: [bulleted] 
- 2026-02-10: Intro call with AE (Alexandra) + TL + CTO; capture pain points.
- 2026-02-18: Security questionnaire received; InfoSec flagged data residency requirement for EU customers.
- 2026-02-28: Hosted API demo (ff_2026-02-28_1258_mariner-demo).
- 2026-03-03: Technical deep-dive with SE (Ravi) — mapping existing RL prompt templates.
- 2026-03-05: Migration plan review meeting (ff_2026-03-05_0943_migration-review).
- 2026-03-08: Shared POC scope & test harness templates (drive link).
- 2026-03-10: Pricing alignment call; customer requested node pricing scenarios for Dedicated (reserved + burst).

Risks & concerns: 
- Prompt parity: small syntactic differences causing large label flips on edge cases.
- Regression detection: Customer insists on automated regression alerts tied to prompt sets (expects Redwood Optimize hook).
- Legal/residency: EU-hosted Dedicated nodes needed for 30% of their user base.

Commercial notes: 
- Current spend with existing provider: ~$40k/month.
- Customer expects 10-20% cost savings after tuning (batching/quantization) on Dedicated.
- Investing in Redwood due to better observability (per-route token breakdown) and rollout controls (canary/A-B).

Next steps (short): 
- Deliver POC test harness and seed dataset by 2026-03-12.
- Start Hosted API parity run week of 2026-03-16 (2 weeks).
- Prepare Dedicated node pricing scenarios and a migration checklist (including drive links and Jira templates).

Quote snippets to use in playbook: 
- "We need parity, not just similar outputs. If it changes user behavior we can't ship." — Evan, CTO.
- "Show me the regressions before we sign; we'll sign if we can quantify and remediate." — Maya, Technical Lead.

AE notes / internal ask: 
- Provide SE time for parity debugging during POC (2-3 days/week).
- Product questions: support for OpenAI-compatible function-calling mappings (edge cases).
- Ask pricing to prepare 12/24 month reserved node scenarios with EU residency option.

2026-02-10 Intro call (Alexandra + TL + CTO)
2026-02-18 Security questionnaire received; InfoSec flagged EU residency
2026-02-28 Hosted API demo (ff_2026-02-28_1258_mariner-demo)
2026-03-03 Technical deep-dive with SE (Ravi)
2026-03-05 Migration plan review (ff_2026-03-05_0943_migration-review)
2026-03-08 Shared POC scope & test harness
2026-03-10 Pricing alignment call
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_5f0f36543c1a4dc3b83c4dab1995c021` — Summit Lake Insightworks
2. `dsid_facae219b4374259b471a45e3ee85c57` — Zenith Helix Software
3. `dsid_a01626c8e33e45a0a876df2f9b499789` — Copper Summit Solutions
4. `dsid_cefd9d05ba684ca98e6be1172ec8cbb9` — Sapphire Helm Solutions
5. `dsid_6d1056e675d442a1a0a2bcd19fe25964` — Marlin Crest Analytics
6. `dsid_9a9b059554874f379b2adbe8be7db281` — Silvershore ProductWorks
7. `dsid_1673cbb4976a4394ab74862d44128eb9` — Stratus Grid Works
8. `dsid_de9c1d389e964346a5d863550ba817a2` — Hightide ProductWorks
9. `dsid_4ccec796173f458889b2801084f777e7` — Ambervale DigitalWorks
10. `dsid_79c12603b0d146dc92f30c8a56847276` — Harrow Cove Solutions

### Fill for this row (also include in final JSON array)

```
row_id: 20
question_id: qst_0069::metadata
corpus_scale_size: 50000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 21

- **row_id:** `21`
- **question_id:** `qst_0079::basic`
- **corpus_scale_size:** `75000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In a morning account blitz note from May 2026, what was the proposed mitigation to address repeated inference timeouts for a healthcare customer with a mid-June renewal?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_9776bd75ffbb4ca7b10669be1512daa3`
_source: full_erb_file:dsid_9776bd75ffbb4ca7b10669be1512daa3__samir-rahman-account-blitz-log-2026-05-10.txt_

```text
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
- [ ] Pull Fortis P95 latency traces (Samir) — 30m
- [ ] Add Fortis error example to pre-brief doc (Aisha) — 15m
- [ ] Ping research about quant impact on Ionata embeddings (Diego) — 1 day follow-up
- [ ] Draft cost-savings note for Nimbus and share with ops (Samir) — 45m
- [ ] Confirm pre-brief invite list + runbook 05-21 (Aisha) — 10m

Conversation snippets / useful lines to use on calls:
- "We saw a repeatable timeout pattern during 02:00–04:00 PT window — want to validate if you're running batch jobs in that window."
- "If we enable KV-prefix caching for your most common prompt prefixes, initial estimates show 18–22% token reduction on that route."

Open questions / parking lot:
- Fortis: is there any internal change on their side that lines up with 04/28 error uptick? (ask CS contact + engineering lead)
- Ionata: which eval set was used to sign off on embeddings initially? Need exact dataset to reproduce drift.
- Nimbus: any contractual constraints that prevent enabling reserved burst? (legal/commercial check)

Notes to self: keep these blitz logs terse — 3 bullets per account max, action + owner + ETA. Use this file to capture morning intent and then expand into per-account doc if a major remediation is needed.

End of AM blitz — next pass 12:30 (post-support clear).

-- Samir
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_872dd780a37c4e9791115a2f73f54d3d` — Intermittent region-affinity flip causing bursty cross-region inference and timeouts for Chronos Health
2. `dsid_06a6ac5f75494a8db16663ef957f6e94` — Healthcheck throttle + runaway backoff causing elevated 5xx and runtime restarts during tenant fairness reshard
3. `dsid_17e77b6582ae4c27b73e3ca4bf81f4a9` — Edge priority fanout amplification causing intermittent 5xx and streaming drops during tenant concurrency ramp
4. `dsid_15407e001bb34739b1116698c4a9a397` — Elevated 502/503 error floor on streaming chat route during priority-handshake stampede for NexaHealth (dedicated)
5. `dsid_045196dc3e594c099b1877ba0cac18c1` — Adaptive batching config swap caused tail-latency cascade; request for safe unwind and verification
6. `dsid_4412fbd468c64de7baf04f9064b80911` — AegisPharm private deployment: multipath failover amplified requests, ordered-stream reassembly failures, and billing exposure
7. `dsid_fb91791924d245218e2b99799d7787bc` — Repeating 429s for tenant caused by delegated service-account refresh loop consuming burst credits
8. `dsid_971ebeb1c4304a27a0d417c37f085a14` — Intermittent 429 bursts for multiplexed websocket chat causing degraded UX
9. `dsid_8fffd704ff4c4744a7ac815e117abda3` — Aggregate latency spike caused by client SDK retry amplification against silent quota enforcement
10. `dsid_461588786f8544a899f5e632f040bcd3` — Clarify rate-limit accounting for internal proxy with per-user signed-keys triggering intermittent throttles

### Fill for this row (also include in final JSON array)

```
row_id: 21
question_id: qst_0079::basic
corpus_scale_size: 75000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 22

- **row_id:** `22`
- **question_id:** `qst_0084::metadata`
- **corpus_scale_size:** `5000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

For the SMB legaltech prospect owned by Alex Martinez that needs SAML SSO and US-only data residency, what month is the close forecasted for?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_1d13149e585f4be398015d748e24e449`
_source: full_erb_file:dsid_1d13149e585f4be398015d748e24e449__company-briefpulse-llc.txt_

```text
BriefPulse LLC

Inbound via website demo signup 2026-02-12 -> used free credits same day
Customer profile: small legaltech SaaS that ingests client docs to power search and summarization for small law firms
Primary concern repeatedly: audit logging and retention policy for confidential docs (they store PII and client privileged information)
Prefer US-only region / data residency; asked whether hosted API can be restricted to us-west/us-east endpoints
AE note: customer tried quick PoC with sample PDF upload + embeddings; saw high token costs and asked about batching/embedding discount strategies
Quote from founder on 2026-02-20 call: "Need clear answers on audit trails and exportable logs before we onboard any production data."
SE note: recommend prefix caching + dedup to reduce embedding calls; show Optimize suggestions in walkthrough
They asked for a short checklist: SOC2 + audit log retention config + encryption at rest + KMS details
Gmail thread contains initial security questionnaire and sample document set (confidential client memos)
AE to send SOC2 + security pack; schedule 30m API walkthrough (week of 2026-03-08)
waiting on SOC2 evidence
legal needs audit log retention details
cost sensitivity for embeddings heavy workflows
2026-02-12: inbound signup via hosted API quickstart; created sandbox org
2026-02-13: auto-email with Getting Started + trial credits (customer replied same day)
2026-02-18: 30m intro call (AE: Alex M, SE: Priya) — demo of embeddings + doc-search
2026-02-20: uploaded 120 sample PDFs to S3; asked about retention and audit logs
2026-02-22: trial API key rotated; customer ran embeddings PoC and flagged cost concerns
2026-02-25: AE sent security pack (prelim); customer requested SOC2 report and confirmation of US-only processing
2026-03-05: follow-up call; customer requested written confirmation of audit-log schema and TTL options
Week 1: full ingest of 120 docs -> embeddings generation (baseline cost measurement)
Week 2: run similarity search and QA pipeline; measure latency and relevance
Week 3: evaluate cost optimizations (batching, quantized model suggestions)
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_3bc3170ead63470eaef9a53ca835cec0` — Trialbridge Legal Solutions
2. `dsid_99da2cf6cc6547e985b1dcb199819ba8` — Pineglen Capital Tech
3. `dsid_39bcc08d966442039e8a9afce31c3aff` — Sable Orbit AI
4. `dsid_48e13d429774409db3aaa152d19407b6` — RiverMark Assist
5. `dsid_1e0fc5d675ce479dbb6fe082402a49c5` — Bayleaf Cartmatic
6. `dsid_d79518c427654533a01173792f51f986` — Onyx Cloud Labs
7. `dsid_de174c9811834eff9929fd6d4efb3d30` — HelixBridge Healthtech
8. `dsid_178f5ada27f64226843c83f032cf3481` — Larkspur KnowledgeWorks
9. `dsid_47063f6493b143959a76a68f294b1b67` — StellarForge SaaSworks
10. `dsid_74f7199105d04593a891d0f2ccdd794d` — Obelisk Dataworks

### Fill for this row (also include in final JSON array)

```
row_id: 22
question_id: qst_0084::metadata
corpus_scale_size: 5000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 23

- **row_id:** `23`
- **question_id:** `qst_0085::basic`
- **corpus_scale_size:** `10000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What are the three request quality and cost tiers proposed in the lightweight interaction tiering model for user facing features?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_2271ae6c393d409093b11b5a6d5b96ed`
_source: full_erb_file:dsid_2271ae6c393d409093b11b5a6d5b96ed__niko-rogers-interaction-tiering-idea-scrapbook.txt_

```text
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
- As a growth PM, I want to A/B test deep vs standard for onboarding flows to measure conversion lift per dollar.

Acceptance signals / metrics:
- Per-route cost per 1k requests by tier (trendable).
- Latency SLO compliance per tier (p95 < tier-defined target).
- Quality regression alerts: micro/standard/deep compare eval set deltas.
- Adoption: percent of new routes assigned a tier within 30 days of creation.

API surface sketch (for devs):
- request param: interaction_tier: "micro" | "standard" | "deep" (optional, default standard).
- server-side config: route->tier override map, emergency downgrade policy, batch/caching hints.
- response metadata: served_tier, model_variant, quant_profile, billed_tokens.

Operator/Runtime implications:
- routing layer needs fast check for route-level override + per-tenant default. Could be implemented as a small routing cache with TTL.
- autoscaler signals should consider weighted qps by tier (deep = higher GPU weight).
- caching: micro tier should prefer aggressive prefix/KV caching; deep should sometimes disable prefix cache for freshness.

Rollout plan (experiment-first):
- Phase 0: instrument only. Add served_tier metadata in responses for 2 weeks on internal traffic.
- Phase 1: opt-in routes. Provide SDK flag and console toggle for "micro"/"deep" per route. Collect cost/latency.
- Phase 2: allow automatic emergency downgrades via policy engine. Pilot with 2 partners.

Open questions / unknowns:
- How granular should tiers be? 3 seems OK but some teams want a "burst" tier for ephemeral high-latency ops.
- Billing integration: map tiers to rate limits/quotas vs to unit-price multipliers? Need billing touch.
- Evaluation: what representative prompts should we use per tier for regression monitoring? Ask research for a seeded eval set.
- Security: does deep tier change redaction requirements (longer context)? Probably same, but call out.

Edge cases and fallback ideas:
- If model_variant unavailable, fallback priority: cached response -> cheaper model variant in same tier -> downgrade tier -> canned message. Need hill for graceful wording to end users.
- Per-tenant overrides: enterprise customers can have custom tiers with different cost targets. Keep schema extensible.

UX bits to consider:
- Console: show heatmap of tiers across routes, quick toggle, cost delta estimates for switching tier.
- SDK helper: recommend a tier based on sample prompt length + estimated tokens. Tiny heuristic in SDK to suggest micro/standard/deep.

Notes to demo at sync:
- Plot: cost vs p95 latency vs perceived quality (subjective) for 3 sample prompts.
- Quick demo: toggle route X from standard->micro and show billing estimate, logs show served_tier change.

Related docs to review before PRD:
- CONFLUENCE-4583 (routing primitives)
- session-economy-playbook draft (internal)
- jira JIRA-PRD-712 (billing integration backlog)

Next steps (for me):
- Pull telemetry on current routes: top 20 by qps and candidate tier.
- Quick prototype SDK flag and server read path (2 day spike).
- Sync with research (Sana) for eval prompts per tier.

Random scribbles:
- individual api keys could have default tier quotas (e.g., free-tier users locked to micro for some endpoints).
- possible names: "lanes", "lanes and lanes", "interaction lanes" (hate cliches), "response-lanes". Pick something short.
- consider mapping a small set of quality tags in the response for downstream UI (concise|verbose|confidence-low).

End of notes. Will tidy to an actual PRD once anchors + telemetry exist.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_09eaf3ba24444871ad5ad1347c0cf22c` — Thunderberry CloudWorks LLC
2. `dsid_a883c3a9f23d4da98c657a76f9870740` — Driftglade Commerce
3. `dsid_92bb1f050a6640dd9d5d7abbfc1a0760` — LumenFold Technologies
4. `dsid_14f8395107244d9fbe00572db0e5aa72` — GroveFuse Chatworks
5. `dsid_080da3e2a82e41158a49f62d4739dc46` — NimbleClasp AIWorks
6. `dsid_d029cb3c0961442282cdbd91013c2857` — SmallCurrent Solutions
7. `dsid_5dbca2a3ac844546b9a4c6aad5af7730` — HarborPoint LLMWorks
8. `dsid_8fe621e97b814937b9b07fb58e38d3d9` — Ironwood Atelier AI
9. `dsid_41f7a51a3feb41a88a3f3c314f070773` — StitchForge AI
10. `dsid_fccd01322b1047fe8b987b3824adcd1e` — Cobalt Clew Analytics

### Fill for this row (also include in final JSON array)

```
row_id: 23
question_id: qst_0085::basic
corpus_scale_size: 10000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 24

- **row_id:** `24`
- **question_id:** `qst_0091::metadata`
- **corpus_scale_size:** `20000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

Which enterprise capital-markets account in North America was last updated in mid March 2026 and has a forecast close month of May 2026?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_c669e9bde8764a1a9636674fce02ff52`
_source: full_erb_file:dsid_c669e9bde8764a1a9636674fce02ff52__company-granite-capital-trading-ai.txt_

```text
Granite Capital Trading AI

Account summary: Granite Capital operates low-latency trading products and wants a production-grade dedicated inference environment for model-driven trade signals and downstream chat alerts. They completed a 4-week realistic load test using Redwood Dedicated emulation.

POC highlights and asks:
- Measured required baseline: sustained 25k tokens/sec across 400 concurrent realtime sessions during simulated market open; p95 target <= 60ms for 384-token contexts.
- Primary negotiation axis now SLA appendix: uptime percentage, credit schedule tied to revenue impact windows, maintenance windows restrictions, support escalation times, and guaranteed sustained throughput per reserved bundle.

SLA negotiation specifics (from 2026-03-11 procurement meeting):
- Granite legal: negotiating for 99.995% annual uptime target for Dedicated + 24/7 oncall. They want automated, revenue-indexed credits for each minute below threshold during defined market-impact windows (pre-market 08:45-09:15, open 09:30-10:00).
- Redwood standard: enterprise dedicated SLA at 99.95% with credits up to 10% for prolonged outages. Proposed compromise: 99.97% base with enhanced credits for named market-impact windows; Redwood requests to limit revenue-indexed credits to verified incidents where Redwood is sole root cause.
- Credit schedule: Granite proposed per-minute credits that escalate quickly (1% per minute up to 10% cap for major incidents). Redwood counters with banded credits by monthly uptime (0.25% credit at <99.97, 1% at <99.95, 4% at <99.9) plus a special clause for market-impact windows subject to incident postmortem validation.
- Maintenance windows: Granite requires no more than 1 scheduled maintenance hour during market-impact windows and prefers maintenance outside of 02:00-10:00 ET. Redwood prefers 2-4 hour windows quarterly for kernel and orchestration updates. Discussion ongoing around offering an SLA opt-out for up to 2 protected market-impact windows per year.
- Support and response: Granite demands P1 acknowledgement <5 minutes, remediation plan within 30 minutes, and a named escalation engineer during market hours. Redwood proposed P1 phone escalation <15 minutes with immediate oncall paging; Redwood can add named ENG on retainer for additional fee.
- Throughput & reserved GPU planning: Based on POC, recommended commit = 12 H100-equivalent reserved for baseline sustained traffic with ability to autoscale +6 GPUs for 30-minute bursts. Finance wants clear monthly amortized price for this commit and an overage rate for burst usage.

Technical POC findings:
- Cold-start KV-cache penalty ~18% for long-tail sessions. Suggest pre-warm on market open and maintain a warm pool of hot keys.
- 4-bit quantization gave 45% cost savings but introduced rare generation artifacts on safety-critical prompts; Granite prefers 8-bit quant for market opens, can accept 4-bit in off-hours for lower-cost batch jobs.
- Failover behavior: require deterministic fallback to a smaller model with documented quality deltas and audit logs for each degraded generation. Redwood to supply comparative evals for both models across Granite's prompt set.

Open action items:
- SE (Omar) to deliver final reserved GPU sizing and cost worksheet (12 vs 16 H100-eq) by 2026-03-16.
- Legal (Redwood) to send SLA appendix redline with alternate credit schedule and maintenance carve-outs by 2026-03-14.
- Infra to provide MTTR commitments and rolling upgrade runbook showing max capacity impact and RTO estimates by 2026-03-18.
- Sales to prepare a commercial summary with two pricing tracks (retainer for named ENG vs standard escalation) for VP approval.

Stubs/refs: POC runbook located at /drive/proposals/granite-dedicated-sow-v5.pdf; Fireflies ff-20260303-4410 covers vendor credit discussion (timestamp 00:15:40).

Quoted notes captured:
- "We must have financial remediation that maps to market reopen losses, not just token-fee credits." 8 - Head of Ops
- "If maintenance hits our morning rebalancing window we'll have serious client churn risk." - Trading Platform Lead
Finalize SLA appendix; confirm reserved-GPU commit quantities and monthly charge; legal sign-off on maintenance carve-outs
internal ops insists on 99.995% uptime or equivalent financial remediation
pricing team needs committed GPU count for quarterly billing cadence
security requires max 1 hour scheduled maintenance during market hours
need proof of mean time to recovery (MTTR) targets for rolling upgrades
2025-09-28: inbound from infra procurement form
2025-10-05: discovery call (owner Marisol + SE Omar)  discussed regulatory and market windows
2025-11-10: 4-week POC kickoff (realtime load simulation)
2026-02-25: POC stress test completed; delivered throughput report
2026-03-03: SLA negotiation call (Fireflies ff-20260303-4410)
2026-03-11: procurement meeting with legal  redline targets set
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_0f991287334d40fbb4d597b305447fd2` — Subscription Flagship Tracker - Q4 2026 (working)
2. `dsid_4ee96635eb8e4dda8b644d0403b6b229` — Customer Lifecycle Convoy — Compact Pipeline Tracker (May 2026)
3. `dsid_2016c4fb92394c21af9f481e0fb4b3ee` — Client Contract Momentum Sheet — Q4 2026
4. `dsid_5fc60be2347646f283ce3d63a2925deb` — Churn risk heatlist + renewal actions (Q1 tracker)
5. `dsid_6b3bf537e0b54d76948f36c106333492` — Renewal Portfolio Snapshot — Brief
6. `dsid_33fe9208812c4384a9ae90c9d84dcf13` — Northern Arc Fintech
7. `dsid_cafcb9b9916a420b9c743beb093794b7` — CS Contract Coverage Inventory — Q2 2026
8. `dsid_85bc31ebe5de4cf7bd0fc36f5d3e5ad8` — Northstar Provenance AI
9. `dsid_e1baae564a6346abade621d30c819226` — Cedar Harbor AI Systems
10. `dsid_0df6e984d47c465ca31f0c9e2beb6142` — Crestfield Payments Inc.

### Fill for this row (also include in final JSON array)

```
row_id: 24
question_id: qst_0091::metadata
corpus_scale_size: 20000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 25

- **row_id:** `25`
- **question_id:** `qst_0096::metadata`
- **corpus_scale_size:** `75000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`other`

### Question

In the customer-support incident about tenant pinning breaking during deferred prewarm and causing mixed model replies in a dedicated prod us-east environment, what is the SLA due date?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ca09c9594d0f4293b971c96fa9ed647c`
_source: full_erb_file:dsid_ca09c9594d0f4293b971c96fa9ed647c__SUP-812999-tenant-stickiness-erosion-during-deferred-prewarm.txt_

```text
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
- Hypothesis B: Pin commit is acknowledged by control plane, but the orchestrator's cohort snapshot for a subset of edge shards lags due to snapshot batching; those shards still advertise legacy mapping until snapshot applied.
- Evidence: Orchestrator commit timestamps show commit at 02:15:12Z, but two edge-proxy instances (ep-12-a and ep-12-c) have configuration refresh at 02:15:27Z and 02:15:38Z respectively.
- Additional evidence: We found prewarm-worker logs that deferred container spin-up due to a transient quota error (reserve-gpu failed with EAGAIN) causing warm capacity for v1 to be delayed ~18s.

Immediate impact mitigation applied:
- Support instructed customer to temporarily disable deferred prewarm for the next promotion.
- Control plane team pushed a high-priority config refresh to the affected edge-proxy shard to force snapshot reconciliation.
- SRE increased prewarm-worker retry timeout and added telemetry alert for repeated EAGAIN reserve-gpu.

Next steps (action items):
- SRE to add guard in orchestrator commit path to ensure edge-proxy does not route to legacy variant if pin commit timestamp exists (owner: Ravi, ETA 2026-03-14).
- Runtime team to add a prewarm gating check: if pin committed but prewarm incomplete, queue a soft-block preventing fallback to legacy (owner: Mei Chen, ETA 2026-03-18).
- Add alert that monitors the delta between control-plane commit timestamp and last-edge refresh per shard; trigger when >5s during promotions (owner: Observability, ETA 2026-03-13).
- Postmortem doc to be drafted and linked to Confluence (owner: Support, ETA 2026-03-19).

Attachments/links:
- Edge traces: link to internal trace id trace-ep12-20260310-0216
- Prewarm worker logs: GH-4821 contains extracted logs with EAGAIN timestamps
- Control plane commit log: confluence/rollout-prewarm-sop#commit-20260310

2026-03-10 03:02 - Support (Alicia Moreno): Customer reports mixed outputs; asked for request IDs and example logs. Customer provided 6 request IDs and example payloads.
2026-03-10 04:10 - SRE (Ravi Patel): Pulled orchestrator commit timeline; observed two edge instances lagging by 15-25s. Kicked forced config refresh to ep-12 shard. Noted prewarm worker errors in GH-4821.
2026-03-10 05:01 - Customer (BrightForms Ops): Confirmed that after disabling deferred prewarm for subsequent promotion, they saw no mixed responses in a follow-up run of 20k requests.
2026-03-11 09:20 - Runtime (Mei Chen): Adding proposal for prewarm gating; will implement a soft block that prevents routing to legacy variant if pin committed but prewarm incomplete. Draft PR GH-4830 opened.
2026-03-12 16:45 - Support (Alicia Moreno): Drafted customer communication summarizing workaround and next steps; scheduled follow-up call for 2026-03-13 10:00 UTC.
Workaround: disable deferred prewarm for sensitive promotions; manual config refresh applied. Long-term fix planned (gating and edge commit checks).
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_9ef76c1d3d354ade932995b6e2ad581a` — Enforced model pin suppressed by fallback-throttle preemption during canary window, causing mixed-model responses
2. `dsid_d84bdbf7547f4feab122ed2f99e23782` — Hosted API: elevated 5xx in us-east; request auto-fallback behavior unclear for pinned customers
3. `dsid_86783f1b3d154ac7b57c6d3d71bb5efc` — Unexpected fallback to degraded variant during staged graceful rollout despite model pin and prewarm success
4. `dsid_4c3b0b28fdb04170860fa7130f328892` — Tenant lease jitter causes pinned model demotion during canary wave
5. `dsid_5c1c408fa554409fac6125db3ce9b387` — Tenant pin corruption during deferred prewarm trigger causes silent transparent fallback
6. `dsid_2369a3a36fb046abb1d8d9355dce86ed` — Priority escalation during regional failover overrides explicit tenant model pin causing degraded routing and unexpected billing
7. `dsid_de78c84196854989820c74f81540de1d` — Tenant edge header rewrite causes pin to be claimed during canary prewarm, producing mixed model responses
8. `dsid_175de838f80642e194b706d3418ff35d` — Intermittent APAC-egress routing observed for EU-pinned dedicated tenant causing p95 latency jitter
9. `dsid_f30e41ac9021447b94eaed3b00f037ec` — Tenant routed to secondary variant despite explicit model pin during orchestrator retry surge
10. `dsid_942cd438bca54d999095774e62b2cbfd` — Edge header stripping evicts tenant model pin during dedicated preemptive rebalancing causing transparent fallback and billing spike

### Fill for this row (also include in final JSON array)

```
row_id: 25
question_id: qst_0096::metadata
corpus_scale_size: 75000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 26

- **row_id:** `26`
- **question_id:** `qst_0144::basic`
- **corpus_scale_size:** `15000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the recent Friday all-hands notes, what was the reported median latency improvement attributed to continuous batching?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a227a7f316c4452eab4c05567edb9404`
_source: full_erb_file:dsid_a227a7f316c4452eab4c05567edb9404__1851234567-allhands-weekly-ask-and-key-highlights.txt_

```text
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
Maya (People Ops): Key takeaways: 1) Sam: 2 new Dedicated customers in EMEA; sales motion is showing improved lead-to-commit conversion. 2) Lina: rollout canary feature out in beta next week; signups via the Console. 3) Devon: continuous batching reduced median token latency by ~8% on our p99 test set; follow-up perf ticket #INF-442. 4) Tom/Olga: infra patch completed Tue; no customer impact. 5) Benefits: parental leave proposal moving to executive review (Maya/Talent).
Sam (CEO): Thanks for the great questions — quick ask to engineers: share one production lesson in #eng-runtime by EOD Monday so we can collect for next all-hands.
Lina (Product): If you missed the demo, check the recording timestamp 12:10 to 18:40 for the rollout walkthrough.
Devon (Eng): Dropping the perf dashboard link here: https://redwoodinternal/metrics/batching (view-only for now) — I'll open a quick office hours on Thursday for anyone who wants deeper dive.
Juno (Talent): Appreciated the benefits update — can we get a one-pager for managers about how the proposed leave changes would operate day-to-day?
Maya (People Ops): Yes, we'll circulate a one-pager early next week and a short feedback form.
Olga (SRE): Adding incident retro cadence note to the shared doc (link in agenda) — will schedule follow-up sync with interested folks.
RecordingBot: Note: Transcript will be available within 24h. :robot_face:
Maya (People Ops): Closing note — thanks for keeping Qs focused and practical. If you have follow-ups for any of the presenters, mention them here or DM. :heart:
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_b4d35e0dc5d944708190a6b25b335c0a` — eng-oncall
2. `dsid_a7ddd026edfe4398a0de803474cb7bad` — eng-runtime
3. `dsid_87c3919424d34ffcbf2638b9157901c8` — eng-ml
4. `dsid_644fae527fe648318b1af179fd2a118d` — eng-runtime
5. `dsid_fe8c351da7fe4f48a1115e12f4ef5005` — eng-runtime
6. `dsid_3f82c6b8c22648828bdb30bdbc4d08b3` — all-hands
7. `dsid_1406539b05e245e7899f6441f78e561f` — incidents
8. `dsid_bdf9d0a3684341c58cebdb98f26464fa` — eng-runtime
9. `dsid_ba3b8c9ea5004dab9b332c9ba9cfc8f9` — eng-platform
10. `dsid_5a8604739f9b42b199a09d5e42eb241c` — eng-ml

### Fill for this row (also include in final JSON array)

```
row_id: 26
question_id: qst_0144::basic
corpus_scale_size: 15000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 27

- **row_id:** `27`
- **question_id:** `qst_0144::basic`
- **corpus_scale_size:** `40000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the recent Friday all-hands notes, what was the reported median latency improvement attributed to continuous batching?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a227a7f316c4452eab4c05567edb9404`
_source: full_erb_file:dsid_a227a7f316c4452eab4c05567edb9404__1851234567-allhands-weekly-ask-and-key-highlights.txt_

```text
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
Maya (People Ops): Key takeaways: 1) Sam: 2 new Dedicated customers in EMEA; sales motion is showing improved lead-to-commit conversion. 2) Lina: rollout canary feature out in beta next week; signups via the Console. 3) Devon: continuous batching reduced median token latency by ~8% on our p99 test set; follow-up perf ticket #INF-442. 4) Tom/Olga: infra patch completed Tue; no customer impact. 5) Benefits: parental leave proposal moving to executive review (Maya/Talent).
Sam (CEO): Thanks for the great questions — quick ask to engineers: share one production lesson in #eng-runtime by EOD Monday so we can collect for next all-hands.
Lina (Product): If you missed the demo, check the recording timestamp 12:10 to 18:40 for the rollout walkthrough.
Devon (Eng): Dropping the perf dashboard link here: https://redwoodinternal/metrics/batching (view-only for now) — I'll open a quick office hours on Thursday for anyone who wants deeper dive.
Juno (Talent): Appreciated the benefits update — can we get a one-pager for managers about how the proposed leave changes would operate day-to-day?
Maya (People Ops): Yes, we'll circulate a one-pager early next week and a short feedback form.
Olga (SRE): Adding incident retro cadence note to the shared doc (link in agenda) — will schedule follow-up sync with interested folks.
RecordingBot: Note: Transcript will be available within 24h. :robot_face:
Maya (People Ops): Closing note — thanks for keeping Qs focused and practical. If you have follow-ups for any of the presenters, mention them here or DM. :heart:
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_a883ceba9c4244bc9297a97a96f5b35e` — support
2. `dsid_b4d35e0dc5d944708190a6b25b335c0a` — eng-oncall
3. `dsid_a7ddd026edfe4398a0de803474cb7bad` — eng-runtime
4. `dsid_77ea2b1d92d94269ad5c55cb9dfdd792` — eng-runtime
5. `dsid_84dd557786524607b1f32119d44f9c97` — eng-ml
6. `dsid_87c3919424d34ffcbf2638b9157901c8` — eng-ml
7. `dsid_644fae527fe648318b1af179fd2a118d` — eng-runtime
8. `dsid_3d2f2b3332f047e3b9e74165001fd24a` — incidents
9. `dsid_84d5400bfd0d4d7781a16c6456c1ca16` — incidents
10. `dsid_cf1e3fbe20b74484971e94f8d7f4fed6` — eng-runtime

### Fill for this row (also include in final JSON array)

```
row_id: 27
question_id: qst_0144::basic
corpus_scale_size: 40000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 28

- **row_id:** `28`
- **question_id:** `qst_0150::basic`
- **corpus_scale_size:** `50000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What are the required permission scopes for an API key when SDK examples fail with a 401 unauthorized error during developer onboarding?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_5af1ed23fd2a4bb3984ec368d0e3b23e`
_source: full_erb_file:dsid_5af1ed23fd2a4bb3984ec368d0e3b23e__devx-onramp-localization-docs-ops-and-canonical-fixes-2026.txt_

```text
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
3. Generate locale-specific examples: ./scripts/generate-localized-examples --locales=en,es,fr --sdk=python
4. Run local docs server including translations: npm run docs:local -- --locale=fr
5. Verify telemetry events appear in staging stream (kinesis-devx-staging): 
   - Expected event: {"event":"example_load","locale":"fr","sdk":"python","version":"0.12.0"}
6. Submit PR to docs-examples with i18n diffs and request docs-site canary deploy via label: docs-canary-request

SDK Localization Checklist (per release)
- [ ] Confirm sample text keys are externalized (no hard-coded English strings in code examples).
- [ ] Provide translation-ready README and example captions in /i18n/{locale}.json.
- [ ] Localized code comments: keep English primary, add short localized caption lines under // LOCAL: ... to avoid syntax churn.
- [ ] Add locale-specific smoke tests: tests/smoke/{locale}/example_test.py (asserts example runs and emits telemetry).
- [ ] Bump telemetry schema version if adding fields: TELEMETRY_SCHEMA: v2 -> notify analytics@redwood.com.

Table: Supported Example Locales and Priority
Locale | Priority | Owner | Notes
------ | -------- | ----- | -----
en (English) | high | devx-eng | baseline; all CI gates run against en
es (Spanish) | medium | intl-ops | customer-facing regions: LATAM, EU-ES
fr (French) | medium | intl-ops | EU-FR customers
de (German) | low | intl-ops | add on request
ja (Japanese) | low | intl-ops | APAC pilot only

Docs-site Operating Procedure (canary -> staged -> prod)
1) Authoring and PRs
   - Create content branch in docs-content repo and include locale JSONs under /i18n.
   - Attach smoke test run output to PR (artifact: smoke-{sha}.zip).
   - Tag PR with labels: [docs-canary-request] or [docs-staged-request] as appropriate.
2) Canary deploy (automatic with label docs-canary-request)
   - Action: GitHub Action docs-canary.yml runs build and deploys to docs-canary.redwood-inference.internal.
   - Checks (must pass): build (exit 0), i18n-linter (no missing keys), smoke-tests (artifacts present), telemetry sanity (at least one example_load event during smoke test).
   - Rollback: manual; revert PR or trigger docs-canary-rollback workflow.
3) Staged deploy (after 48h of Canary uptime and signoff)
   - Add label docs-staged-request. Ops lead runs gated promote: ./tools/promote_docs.sh --from=canary --to=staged --approve="<approver>"
   - Staged URL: docs-staged.redwood-inference.internal. Run translation QA with translator team.
4) Prod promote
   - Window: M-F 9:00-17:00 PT. Approvals: 2 reviewers (author + docs eng). Run promote script with --to=prod and monitor SLOs for 30min.

Operational SLOs for Docs-site during promote windows
- Build success rate >= 99% (30-day rolling).
- Canary smoke-tests pass within 15 minutes after deploy.
- No production downtime > 1 minute caused by new docs push.

Canonical Support Issues and Fixes (top issues during onramp)
Issue A: SDK example fails to authenticate (401)
- Detection: error pattern in logs: "error=unauthorized, code=401, hint=apiKey"; Support: run reproduction script with -v flag.
- Root cause: sample uses environment variable REDWOOD_API_KEY unset or using expired demo key.
- Canonical fix steps:
  1. Confirm env var exists: echo $REDWOOD_API_KEY
  2. If missing, instruct customer to create API key via console (link: internal:product-docs/create-api-key).
  3. For expired keys, rotate and confirm permission scopes: scopes must include: [inference:invoke, metrics:read].
  4. Add small code snippet to sample that fails fast with helpful error message (example below).
- Owner: Support -> escalate to SDK owner if repro fails.

Code snippet: fail-fast auth check (Python)
```python
import os
api_key = os.getenv('REDWOOD_API_KEY')
if not api_key:
    raise RuntimeError('Missing REDWOOD_API_KEY environment variable. Create one at https://console.redwood-inference.internal/settings/api-keys')
# proceed with client
```

Issue B: Streaming responses stall mid-stream
- Detection: client receives first tokens then stalls; metrics show open connection but no bytes.
- Root cause: client-level keepalive mismatch or proxy buffering (common with corporate proxies).
- Canonical fix steps:
  1. Ask customer to test with curl -N to confirm raw stream: 
     curl -H "Authorization: Bearer $REDWOOD_API_KEY" -N \"https://api.redwood-inference.internal/v1/stream?...\"
  2. If curl works, recommend SDK change: prefer chunked transfer decoding and set socket keepalive: true.
  3. Provide fallback example using poll-based generation with polling timeout 5s.
- Owner: SDK eng + DevX docs for the streaming troubleshooting page.

Issue C: Localized examples missing strings or have placeholders ("__MISSING__")
- Detection: i18n-linter failure in CI; smoke test asserts replaceable keys remain.
- Root cause: upstream translations not merged to branch or translation key mismatch after refactor.
- Canonical fix steps:
  1. Run i18n-linter locally: npm run i18n-lint -- --locale=es
  2. Check missing keys report: ./tools/i18n-report --sha <pr-sha>
  3. If keys changed upstream, rebase PR and run ./scripts/merge-i18n.sh
  4. If translation missing, create placeholder and flag translator for fast-turn merge.
- Owner: Docs + Intl-ops.

Issue D: SDK telemetry not appearing in staging (no example_load events)
- Detection: telemetry dashboard shows zero events for smoke-run timeframe.
- Root cause: SDK example uses wrong telemetry endpoint, or telemetry schema mismatch.
- Canonical fix steps:
  1. Confirm telemetry endpoint env var: TELEMETRY_ENDPOINT points to staging ingestion.
  2. Run smoke tests locally with verbose flag and inspect emitted payloads: ./scripts/run-smoke --verbose | jq .
  3. If schema mismatch, check TELEMETRY_SCHEMA in repo and bump analytics contract.
- Owner: DevX instrumentation owner.

Emergency rollback recipe (docs-site)
- Trigger: Canary or staged build causes widespread example breakage or production regressions.
- Steps:
  1. Revert offending PR or tag immediately. Use GitHub UI or: git revert --no-edit <merge-commit> && push.
  2. Run docs-canary-rollback action: ./tools/docs_rollback --env=canary --commit=<last-good-commit>
  3. Notify #devx and #sre-channels with incident summary template (include commit, author, time).
  4. Run postmortem within 72 hours if > 15 developer-impacting incidents occurred.

Telemetry and Monitoring (what to watch)
- Telemetry events: example_load, example_error, docs_build_status
- Dashboards: DevX -> Examples Overview, Docs -> Build Health, Support -> Top SDK Errors
- Alerts: Build failure rate > 5% in 1h (PagerDuty to Docs oncall), Missing telemetry events for a deployed smoke run (Slack alert to #devx-monitor).

Owner matrix and contact points
- DevX Docs (authoring + i18n): Marisol Vega (owner)
- Intl-ops (translation & QA): Sana Ribeiro
- SDK engineering (runtime fixes): Evan Park
- Support triage lead: Luis Moreno

Appendix: Example file layout (minimal)
- /devx-examples/
  - /python/
    - example_quickstart.py
    - README.md
    - /i18n/en.json
    - /i18n/es.json
  - /js/
    - example_quickstart.js
    - /i18n/en.json

Contact and escalation
- For blocked promotes contact: #devx-ops on Slack and add pager: docs-oncall@redwood-inference.internal
- For telemetry contract questions: analytics@redwood-inference.internal

Revision history
- 2025-09-12: Initial draft by Marisol Vega
- 2025-11-03: Added streaming troubleshooting and telemetry checks (review: Evan Park)
- 2026-02-20: Finalized canary/staged procedure and rollback script path updates

Related artifacts and snippets
- Scripts referenced live in repo: https://github.com/redwood/devx-examples/tree/main/scripts
- Translation handoff template: /templates/translation-handoff.md

End of playbook
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_6f37b2b4341947028019bd41748eaff9` — Python SDK sends 'Bearer Bearer' in Authorization header for some configs
2. `dsid_a75a4d9aa7d940009b7966188753d520` — New user quickstart fails with 401 "invalid_api_key" (wrong API key or env var name)
3. `dsid_a8af533a3f89402ca739bfdc5322b42e` — Python SDK returns 401 after API key rotation (works via curl)
4. `dsid_65b12644ea52428b9c032d2cd9b75d8a` — Add SDK guardrail: detect 'Bearer ' prefix in api_key and warn across SDKs
5. `dsid_1a160e1c00934f108e17183f44e3ca77` — Go SDK reports 'invalid API key' when key loaded from file includes trailing newline
6. `dsid_f940e7c95688406cb497b0b1dab44e99` — Known issues: API key rotation/revocation edge cases
7. `dsid_26db0d269ce04474afdae8bf7265e1ca` — Northwind Analytics: rotate/revoke Hosted API key after suspected CI exposure
8. `dsid_c6efd46ecc6449ac8be1e53ed3803e92` — Tolerate trailing newline in API key and improve auth error messaging
9. `dsid_f0b14f9b0cf2409baf9ee85b61b507c7` — API key lifecycle (Hosted): creation, rotation, and revocation
10. `dsid_89c64051f03340b584e438dceebcc4ad` — support

### Fill for this row (also include in final JSON array)

```
row_id: 28
question_id: qst_0150::basic
corpus_scale_size: 50000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 29

- **row_id:** `29`
- **question_id:** `qst_0156::basic`
- **corpus_scale_size:** `50000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the planning meeting about a strict deployment change freeze and automatic fallback during a model rollout, what composite health score thresholds defined green, amber, and red states?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_9c63777c789c4f7db9e391024dd887ae`
_source: full_erb_file:dsid_9c63777c789c4f7db9e391024dd887ae__2027-01-19-deployment-sterile-window-and-fallback-choreography.txt_

```text
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
01:48 Priya Nair: and KMS keys for the private deployments — do we need a different key rotation window during sterile
01:55 Avery Chen: good catch, Priya. no key rotations during sterile unless emergency key compromise, add to runbook
02:03 Ellen Graves: action: runbook edit, add key rotation policy
02:10 Tomas Rivera: (crosstalk) telemetry — we need a composite gating signal, not just error rate. latency spikes + request entropy + model perplexity
02:22 Sofia Ramos: agreed. propose composite health score: [latency P95, token drop rate, perplexity regression]. Thresholds: green<0.6, amber 0.6-0.8, red>0.8
02:36 Jonah Park: how do we compute perplexity in prod cheaply? approximations only
02:42 Sofia Ramos: we can use sampled evaluation on 1% traffic plus the light-weight perplex proxy we prototyped
02:51 Marco Li: (interrupts) sampling might miss edge regressions during high load
02:54 Priya Nair: we can bias sampling towards failed routes and new prompt templates
03:02 Avery Chen: ok, let's settle on sampling plus error-biased sampling. Jonah, you'll put the sampling config in the canary spec
03:12 Jonah Park: yep, I'll own that
03:14 timestamp 03:14
03:16 Ellen Graves: about rollback — automatic vs manual? we discussed auto fallback to variant-small for red>0.8, but manual for perplexity regressions that exceed delta 0.15
03:30 Sofia Ramos: auto fallback to variant-small for infra or latency-only incidents; require manual for quality regressions because of business impact
03:40 Tomas Rivera: manual decisions add latency to mitigation — we should define a fast path for high-severity quality degradation with a dedicated runbook step
03:52 Priya Nair: create a 'fast fallback' runbook where on-call can trigger emergency auto-fallback given an approval token — two clicks pattern
04:03 Avery Chen: good, and require postmortem within 48 hours for any fallback event
04:12 Ellen Graves: agree, and include retrospectives with product and customer success for external communication
04:20 Jonah Park: can we simulate a fallback during the staging window? like a chaos injection that forces a region degrade
04:28 Sofia Ramos: yes, we have a chaos script. needs permission to touch routing tables; schedule with infra
04:36 Marco Li: schedule the simulation in the two weeks before launch, coordinate with SRE page rotation
04:43 Priya Nair: SRE will need a runbook dry run and oncall brief, add to schedule
04:49 timestamp 05:00
05:00 Tomas Rivera: on observability — dashboard checklist: model quality panel, composite health score, canary histogram, latency tail waterfall, KV cache hit-rate
05:12 Sofia Ramos: also add token-level cost meter per route so we can detect cost regressions early
05:18 Jonah Park: note: batcher config changes can affect cost dramatically; include batcher version in telemetry
05:24 Ellen Graves: who owns the dashboard build
05:27 Priya Nair: SRE owns infra panels, runtime owns model panels, product owns the narrative and acceptance criteria
05:34 Avery Chen: assign owners: Tomas dashboard infra, Sofia model panels, Jonah canary specs and sampling, Priya runbook edits, Ellen communications
05:45 Jonah Park: (soft laugh) and me for the sampling, yeah
05:48 timestamp 06:00
06:00 Marco Li: quick discussion on canary schedule — 2% traffic for 30m, 5% for 1h, 20% for 3h then ramp to 100% over 12h if green
06:12 Sofia Ramos: those windows are fine but P95 baseline must be within 10% of baseline or abort
06:18 Priya Nair: also add a hard abort if error rate increases by 50% vs baseline in any window
06:25 Ellen Graves: document the exact metrics and rollback steps in the canary spec and confluence
06:30 Avery Chen: on-call runbook must include checklist: pre-deploy health scan, post-deploy smoke, canary health checks, rollback steps, communication template
06:40 Tomas Rivera: dependency freeze — we need a two-day freeze on runtime-critical libraries and driver updates
06:46 Sofia Ramos: agree. no quant kernels merges 48h before sterile window
06:51 Jonah Park: and mark emergency exemptions for security fixes only
06:55 timestamp 07:15
07:15 Priya Nair: discussion: private deploy customers — we need to surface the fallback behavior in the contract and in customer docs; some customers won't accept cross-region fallback
07:28 Marco Li: yes, legal/product will need an appendix for fallback policies per deployment mode (hosted/dedicated/private)
07:36 Ellen Graves: action: legal to draft fallback appendix and SLO note, product to review
07:42 Avery Chen: add a checkbox to the pre-launch intake: 'customer fallback constraints captured'
07:48 Jonah Park: also add a technical verification for on-prem: KMS behavior during fallback and if we can gracefully use local model artifacts
07:56 Sofia Ramos: on-prem has latency but we can support model variant in same rack; document the artifact sync behavior
08:03 timestamp 08:30
08:30 Tomas Rivera: testing matrix: staging canary + chaos injection, 2 private deploy simulations, regression suite with sampled perplex checks
08:40 Priya Nair: timeline for tests — run 1: next Tuesday, run 2: two days later, dry run for runbook one week before release
08:50 Marco Li: make sure we have SRE rotation aligned that week
08:55 Ellen Graves: communications plan — runbook owners to draft customer comms and release notes two days before rollout
09:02 Jonah Park: small point, quant skew — if quantized variant differs more than 0.12 BLEU-ish equivalent then flag
09:10 Sofia Ramos: we'll map BLEU to our surrogate quality metric
09:15 Avery Chen: ok time check, 12 minutes left. let's recap owners and immediate deliverables
09:22 Tomas Rivera: recap? yeah
09:24 Avery Chen: Jonah — canary spec + sampling config (due 2027-01-22)
09:31 Jonah Park: got it
09:33 Sofia Ramos: Sofia — model panels + composite health score implementation (due 2027-01-24)
09:40 Sofia Ramos: noted
09:42 Priya Nair: Priya — runbook edits and fast-fallback approval token flow (due 2027-01-21)
09:49 Priya Nair: noted
09:51 Ellen Graves: Ellen — customer comms template and legal fallback appendix draft (due 2027-01-23)
09:58 Ellen Graves: i'll get legal synced
10:00 Marco Li: Marco — coordinate chaos sim and oncall rotation (due 2027-01-25)
10:07 Marco Li: confirmed
10:09 Avery Chen: okay, I'll own final go/no-go checklist and ship readiness sig (due 2027-01-26). we'll run a tabletop next week
10:18 Tomas Rivera: one last note, add a metric for 'fallback churn' to track repeated fallbacks
10:24 Sofia Ramos: good KPI
10:30 timestamp 12:00
12:00 Avery Chen: thanks everyone, meeting adjourned

Notes on transcription: occasional overlap, names sometimes misaligned. Some technical terms transcribed imperfectly (KV cache -> K V cache, BLEU-ish -> bluish).
Jonah: publish canary spec + sampling config by 2027-01-22
Sofia: implement composite health score and model panels by 2027-01-24
Priya: update runbook + fast-fallback flow by 2027-01-21
Ellen: draft customer comms and legal appendix by 2027-01-23
Marco: schedule chaos sim and oncall rotation by 2027-01-25
Avery: finalize go/no-go checklist by 2027-01-26
Jonah Park: Canary spec + sampling config -> due 2027-01-22
Sofia Ramos: Composite health score + model panels -> due 2027-01-24
Priya Nair: Runbook edits + approval token flow -> due 2027-01-21
Ellen Graves: Customer comms template + legal appendix draft -> due 2027-01-23
Marco Li: Coordinate chaos simulation + oncall rotation -> due 2027-01-25
Avery Chen: Final go/no-go checklist / ship readiness -> due 2027-01-26
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_83effe9968594d25a5ecb719178034c6` — Composite-signal strategy and rollback heuristics for Optimize evals
2. `dsid_705b5d2b5ddb4e098964fa67911a0daf` — QBR health signal exploration & scoring lab
3. `dsid_d78b80dce604425ebb87797c5835f01d` — Field operational runway and safety windows for private deployments
4. `dsid_93a93dc4fe054f238d6c09ef8d558bd0` — Tenant Urgency Index for Model Deprecation: telemetry, thresholds, and migration playbook
5. `dsid_3af6827a6dd54e7dbe9261d9a530aa17` — traffic-throttle-and-roll-forward-matrix-for-experiments
6. `dsid_0c10879aaadf4314bec81aed9961477a` — Holistic Acceptance Matrix for Model Promotion
7. `dsid_03353a3e32ba43c482e0efc6dff87a86` — Rollout Stoplight Decision Tree & Economic Sentinel
8. `dsid_a6a4d42e97ce47aa9509e779f67a6463` — Adaptive Cohort Guardrails and Decision Flow for Optimize Eval Quality
9. `dsid_3c00e57d05144023b526014bf5a01cb3` — Define tiered resilience metrics and automated deployment gates for inference services
10. `dsid_d208b7227aff40309d40cdadff67b65d` — Distribution Stability Eval and Response Playbook

### Fill for this row (also include in final JSON array)

```
row_id: 29
question_id: qst_0156::basic
corpus_scale_size: 50000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 30

- **row_id:** `30`
- **question_id:** `qst_0166::basic`
- **corpus_scale_size:** `20000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`other`

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`
_source: full_erb_file:dsid_10d018b9cd334ababafa960517492a77__20261127-postcall-eval-roadmap-streaming-coherence-checks.txt_

```text
Post-call: model fit roadmap + streaming coherence follow-ups

From: Camila Reyes <camila.reyes@redwood.ai>
To: Alicia Ramos <alicia.ramos@clearpathhealth.com>, procurement@clearpathhealth.com
Cc: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>
Date: 2026-11-20T14:05:00-08:00
Subject: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Alicia / ClearPath team —

Great to meet today — thanks for walking us through the triage flow and the latency constraints for short, clinician-facing prompts. Quick recap and proposed next steps so everyone is aligned: 

1) Primary goals we heard
- Clinical triage responses should be accurate and concise for short prompts (~20–80 tokens)
- Streaming UX must avoid partial incoherent fragments and respect stop sequences for list-style outputs
- Latency target: ideally <= 300ms for initial tokens on short responses; < 700ms tail for longer follow-ups (we discussed getting you stronger SLOs once we baseline)

2) Recommended model candidates to evaluate (initial):
- redwood-44b-int8 (balanced quality / throughput)
- redwood-44b-ptq (aggressive quantized variant for cost-sensitive seats)
- redmini-8b (low-latency option for high-concurrency endpoints)

3) Benchmarks and artifacts I shared (attached and via Drive):
- initial-bench-summary.pdf — high-level comparison across representatives for streaming latency & coherence
- CPH-PromptSamples.csv — the sample prompt set you agreed to share (I redacted PHI during ingestion)
- Drive folder with the raw run configs: https://drive.google.com/drive/folders/1a2b3c_clearpath_eval

4) Streaming-specific areas we'll prioritize during evaluation:
- Stop-sequence enforcement: verify EOS/stop-token handling when prompts include explicit delimiters
- Partial output coherence: stress tests with incremental decoding — ensure the partial tokens emitted are syntactically coherent and not deceptive mid-sentence
- KV/prefix cache behavior for short-turn dialogs: measure cold vs warm latency
- Sampling settings for clinical tone control (temp, top-p / top-k) and their impact on hallucination risk

5) Next steps / asks for you
- Please confirm the sample prompts are representative and send any additional high-priority prompt batches (preferably <100 examples to start)
- Grant the eval folder access to evals@medbench.ai and procurement@clearpathhealth.com so we can share artifacts
- Confirm procurement timeline (procurement@clearpathhealth.com copied) if you want pricing/commit options in parallel

6) Our immediate internal plan: run streaming bench across the three model candidates with the sample prompts, capture per-token latencies and a coherence score (automated metric + small human pass). I’ll loop Ben and Marissa in for execution and follow-up.

Attachments: CPH-PromptSamples.csv, initial-bench-summary.pdf

Thanks — talk soon.

—Camila Reyes
Enterprise AE | Redwood Inference
camila.reyes@redwood.ai | +1 415-555-0198


From: Alicia Ramos <alicia.ramos@clearpathhealth.com>
To: Camila Reyes <camila.reyes@redwood.ai>
Cc: procurement@clearpathhealth.com
Date: 2026-11-23T10:33:00-08:00
Subject: Re: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Camila —

Thanks for the thorough recap, that tracks with our notes. A few clarifications from my side: 

- Latency: our product team is firm on a <= 300ms guideline for short clinical responses (20–60 tokens). If you can show streaming baselines where initial token emissions are consistently under that threshold on the recommended model(s), that will be a big factor in procurement.
- Coherence: we can tolerate brief grammatical mid-phrase edits during streaming, but not hallucinated assertions or truncated recommendations. Stop sequences are especially important for list outputs (e.g., medications).
- Compliance: we need to confirm that any shared evaluation artifacts have PHI removed — appreciate the redaction note. Our security team will want a short evidence pack (SOC 2 scoping, data handling notes) if we move to a private deployment later.

Procurement: our timeline target is an agreement signed by end of Q1 2027 if benchmarks and security checks align. I’ll loop in procurement with any specific questions.

Can you share a proposed cadence for the benchmark results review (quick sync + a technical deep dive)?

Best,
Alicia
Alicia Ramos
Head of Product — Clinical Systems
ClearPath Health
alicia.ramos@clearpathhealth.com


From: Camila Reyes <camila.reyes@redwood.ai>
To: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-24T09:15:00-08:00
Subject: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Team — forwarding Alicia’s reply and distilling the asks. Please treat this as the internal kickoff for the ClearPath streaming evals. Quick assignment and checklist below: 

Context (from Alicia): strict initial-token latency <= 300ms target for short replies; stop-sequence fidelity for list outputs; PHI must be redacted for any shared artifacts. Procurement timeline aiming for end of Q1 2027.

Action items
- Ben: run the streaming bench across redwood-44b-int8, redwood-44b-ptq, redmini-8b. Focus tests on:
  * Per-token latency (cold vs warm KV cache) at 16/64/128 token prefixes
  * Stop sequence enforcement (explicit tokens like "

--END--
") and eos-bias experiments
  * Coherence meter: automatic n-gram overlap + short human pass (I can coordinate 10 manual checks)
  * Output sampling settings: default, temp 0.0–0.5, top-p 0.85–0.95
- Marissa: draft a short results digest for Alicia (one-pager + proposed SLO table) and propose two slots for a review meeting (30m tech sync; 60m deep dive if they want it)
- Jasmine: prep a minimal security evidence note (SOC 2 scope, PHI redaction process used, link to KMS docs) so we can attach it to the digest if they ask

Attachments to include for internal tracking: streaming-test-plan.md, bench-config.json (I uploaded both to the Drive folder). Ben — aim for a first-pass results set by EOD Friday (the 27th). I’ll prepare the client-facing digest after your pass.

Thanks — Camila


From: Ben Carter <ben_carter@redwood.ai>
To: Camila Reyes <camila.reyes@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-27T11:02:00-08:00
Subject: Re: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Folks — short status and preliminary findings from the bench run (attached CSV + summary). Ran the streaming harness against the CPH prompt set (50 of the provided samples) using the configs in bench-config.json.

Summary highlights (first-pass):
- redwood-44b-int8:
  * Median initial-token latency (warm cache, 16-token prefix): ~285ms — within Alicia’s 300ms guideline on average, but 95th percentile spikes to ~520ms on a few prompts with long context prep
  * Coherence: automated rubric flags ~12% of responses where partial streaming output contains truncated clauses that may read as incomplete (examples attached). Stop-sequence enforcement failed on 3/50 cases where the model emitted a token matching stop delimiter mid-stream and did not truncate output; this looks like eos-bias underflow in the quantized path
- redwood-44b-ptq:
  * Faster median latency (~240ms warm) but coherence regressions rise to ~18% by our metric set — likely sampling + quantization artifacts exacerbating mid-sequence token instability
- redmini-8b:
  * Best consistency for streaming (median ~145ms warm), stop sequences respected in 49/50 tests, but hallucination risk is higher for clinical-detail prompts (we saw omissions / simplifications that could be unsafe without a guardrail)

Immediate hypotheses / mitigation suggestions:
- Enforce stop tokens at the decoder level with an early-check and apply a small positive eos bias when a stop delimiter is in the prompt; this reduces the 3/50 failure cases in redwood-44b-int8 in local tests
- Tighten sampling (temp <= 0.3, top-p 0.9) for clinical slots and add a post-stream deterministic verification pass for critical fields (e.g., medication lists)
- Consider a hybrid: redmini-8b for front-line short responses with a routed verification call to redwood-44b-int8/ptq for detail expansion when the prompt length or classification model signals a high-safety path

Attachments: bench-20261127-results.csv (includes per-prompt latency & coherence flags), snippets of failing streams for redwood-44b-int8

Next steps I propose:
- Share this summary + CSV with Camila for client digest (Marissa, please draft the one-pager)
- Schedule a 30m tech sync with ClearPath next week to walk the numbers and the suggested guardrails (Camila: will you propose times?)
- Follow-up bench pass with eos-bias experiments and low-temp sampling to see coherence deltas (I can run this on Monday morning)

Ben Carter
Senior SRE — Inference Performance
ben_carter@redwood.ai
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_573ca1fc195e450e85e3f10d1a068cf6` — HelmBridge Healthcare
2. `dsid_7ebcb79ae27b49e2ade629edbf764551` — Silverbridge AI Security
3. `dsid_c7018f1cf17b4677a9368dda646702a8` — Galena ProcureWise, Inc.
4. `dsid_03e8e7561d79413ebb487cb9926a1670` — Mantelbridge Support & Governance
5. `dsid_26958e32ed0d4b7080c9e42bc34b1e2e` — Praxis MedTech Regulatory Solutions
6. `dsid_da8b915c58a74bce8ccb88cd9b05d346` — Beacon Health Payments
7. `dsid_4dc77de6649d4e0799648a18290d96b5` — BlueCrest Secure Support
8. `dsid_25d5245f41e349f0ba6c5af9519b9d79` — Summit Clinical Research Inc
9. `dsid_5957ce1d094641c9aea7cf9011ed7ef4` — Zephyr Data Systems
10. `dsid_de174c9811834eff9929fd6d4efb3d30` — HelixBridge Healthtech

### Fill for this row (also include in final JSON array)

```
row_id: 30
question_id: qst_0166::basic
corpus_scale_size: 20000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 31

- **row_id:** `31`
- **question_id:** `qst_0166::basic`
- **corpus_scale_size:** `25000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`
_source: full_erb_file:dsid_10d018b9cd334ababafa960517492a77__20261127-postcall-eval-roadmap-streaming-coherence-checks.txt_

```text
Post-call: model fit roadmap + streaming coherence follow-ups

From: Camila Reyes <camila.reyes@redwood.ai>
To: Alicia Ramos <alicia.ramos@clearpathhealth.com>, procurement@clearpathhealth.com
Cc: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>
Date: 2026-11-20T14:05:00-08:00
Subject: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Alicia / ClearPath team —

Great to meet today — thanks for walking us through the triage flow and the latency constraints for short, clinician-facing prompts. Quick recap and proposed next steps so everyone is aligned: 

1) Primary goals we heard
- Clinical triage responses should be accurate and concise for short prompts (~20–80 tokens)
- Streaming UX must avoid partial incoherent fragments and respect stop sequences for list-style outputs
- Latency target: ideally <= 300ms for initial tokens on short responses; < 700ms tail for longer follow-ups (we discussed getting you stronger SLOs once we baseline)

2) Recommended model candidates to evaluate (initial):
- redwood-44b-int8 (balanced quality / throughput)
- redwood-44b-ptq (aggressive quantized variant for cost-sensitive seats)
- redmini-8b (low-latency option for high-concurrency endpoints)

3) Benchmarks and artifacts I shared (attached and via Drive):
- initial-bench-summary.pdf — high-level comparison across representatives for streaming latency & coherence
- CPH-PromptSamples.csv — the sample prompt set you agreed to share (I redacted PHI during ingestion)
- Drive folder with the raw run configs: https://drive.google.com/drive/folders/1a2b3c_clearpath_eval

4) Streaming-specific areas we'll prioritize during evaluation:
- Stop-sequence enforcement: verify EOS/stop-token handling when prompts include explicit delimiters
- Partial output coherence: stress tests with incremental decoding — ensure the partial tokens emitted are syntactically coherent and not deceptive mid-sentence
- KV/prefix cache behavior for short-turn dialogs: measure cold vs warm latency
- Sampling settings for clinical tone control (temp, top-p / top-k) and their impact on hallucination risk

5) Next steps / asks for you
- Please confirm the sample prompts are representative and send any additional high-priority prompt batches (preferably <100 examples to start)
- Grant the eval folder access to evals@medbench.ai and procurement@clearpathhealth.com so we can share artifacts
- Confirm procurement timeline (procurement@clearpathhealth.com copied) if you want pricing/commit options in parallel

6) Our immediate internal plan: run streaming bench across the three model candidates with the sample prompts, capture per-token latencies and a coherence score (automated metric + small human pass). I’ll loop Ben and Marissa in for execution and follow-up.

Attachments: CPH-PromptSamples.csv, initial-bench-summary.pdf

Thanks — talk soon.

—Camila Reyes
Enterprise AE | Redwood Inference
camila.reyes@redwood.ai | +1 415-555-0198


From: Alicia Ramos <alicia.ramos@clearpathhealth.com>
To: Camila Reyes <camila.reyes@redwood.ai>
Cc: procurement@clearpathhealth.com
Date: 2026-11-23T10:33:00-08:00
Subject: Re: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Camila —

Thanks for the thorough recap, that tracks with our notes. A few clarifications from my side: 

- Latency: our product team is firm on a <= 300ms guideline for short clinical responses (20–60 tokens). If you can show streaming baselines where initial token emissions are consistently under that threshold on the recommended model(s), that will be a big factor in procurement.
- Coherence: we can tolerate brief grammatical mid-phrase edits during streaming, but not hallucinated assertions or truncated recommendations. Stop sequences are especially important for list outputs (e.g., medications).
- Compliance: we need to confirm that any shared evaluation artifacts have PHI removed — appreciate the redaction note. Our security team will want a short evidence pack (SOC 2 scoping, data handling notes) if we move to a private deployment later.

Procurement: our timeline target is an agreement signed by end of Q1 2027 if benchmarks and security checks align. I’ll loop in procurement with any specific questions.

Can you share a proposed cadence for the benchmark results review (quick sync + a technical deep dive)?

Best,
Alicia
Alicia Ramos
Head of Product — Clinical Systems
ClearPath Health
alicia.ramos@clearpathhealth.com


From: Camila Reyes <camila.reyes@redwood.ai>
To: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-24T09:15:00-08:00
Subject: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Team — forwarding Alicia’s reply and distilling the asks. Please treat this as the internal kickoff for the ClearPath streaming evals. Quick assignment and checklist below: 

Context (from Alicia): strict initial-token latency <= 300ms target for short replies; stop-sequence fidelity for list outputs; PHI must be redacted for any shared artifacts. Procurement timeline aiming for end of Q1 2027.

Action items
- Ben: run the streaming bench across redwood-44b-int8, redwood-44b-ptq, redmini-8b. Focus tests on:
  * Per-token latency (cold vs warm KV cache) at 16/64/128 token prefixes
  * Stop sequence enforcement (explicit tokens like "

--END--
") and eos-bias experiments
  * Coherence meter: automatic n-gram overlap + short human pass (I can coordinate 10 manual checks)
  * Output sampling settings: default, temp 0.0–0.5, top-p 0.85–0.95
- Marissa: draft a short results digest for Alicia (one-pager + proposed SLO table) and propose two slots for a review meeting (30m tech sync; 60m deep dive if they want it)
- Jasmine: prep a minimal security evidence note (SOC 2 scope, PHI redaction process used, link to KMS docs) so we can attach it to the digest if they ask

Attachments to include for internal tracking: streaming-test-plan.md, bench-config.json (I uploaded both to the Drive folder). Ben — aim for a first-pass results set by EOD Friday (the 27th). I’ll prepare the client-facing digest after your pass.

Thanks — Camila


From: Ben Carter <ben_carter@redwood.ai>
To: Camila Reyes <camila.reyes@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-27T11:02:00-08:00
Subject: Re: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Folks — short status and preliminary findings from the bench run (attached CSV + summary). Ran the streaming harness against the CPH prompt set (50 of the provided samples) using the configs in bench-config.json.

Summary highlights (first-pass):
- redwood-44b-int8:
  * Median initial-token latency (warm cache, 16-token prefix): ~285ms — within Alicia’s 300ms guideline on average, but 95th percentile spikes to ~520ms on a few prompts with long context prep
  * Coherence: automated rubric flags ~12% of responses where partial streaming output contains truncated clauses that may read as incomplete (examples attached). Stop-sequence enforcement failed on 3/50 cases where the model emitted a token matching stop delimiter mid-stream and did not truncate output; this looks like eos-bias underflow in the quantized path
- redwood-44b-ptq:
  * Faster median latency (~240ms warm) but coherence regressions rise to ~18% by our metric set — likely sampling + quantization artifacts exacerbating mid-sequence token instability
- redmini-8b:
  * Best consistency for streaming (median ~145ms warm), stop sequences respected in 49/50 tests, but hallucination risk is higher for clinical-detail prompts (we saw omissions / simplifications that could be unsafe without a guardrail)

Immediate hypotheses / mitigation suggestions:
- Enforce stop tokens at the decoder level with an early-check and apply a small positive eos bias when a stop delimiter is in the prompt; this reduces the 3/50 failure cases in redwood-44b-int8 in local tests
- Tighten sampling (temp <= 0.3, top-p 0.9) for clinical slots and add a post-stream deterministic verification pass for critical fields (e.g., medication lists)
- Consider a hybrid: redmini-8b for front-line short responses with a routed verification call to redwood-44b-int8/ptq for detail expansion when the prompt length or classification model signals a high-safety path

Attachments: bench-20261127-results.csv (includes per-prompt latency & coherence flags), snippets of failing streams for redwood-44b-int8

Next steps I propose:
- Share this summary + CSV with Camila for client digest (Marissa, please draft the one-pager)
- Schedule a 30m tech sync with ClearPath next week to walk the numbers and the suggested guardrails (Camila: will you propose times?)
- Follow-up bench pass with eos-bias experiments and low-temp sampling to see coherence deltas (I can run this on Monday morning)

Ben Carter
Senior SRE — Inference Performance
ben_carter@redwood.ai
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_a110cebd6e8844afbb800d73e451bf55` — Request to pause trial countdown while procurement completes
2. `dsid_03a70a43e57c4895b63e456c7e836890` — MAP: Alder Health — success criteria, exit gates, and procurement checkpoints
3. `dsid_4fb433d5bc984ee4b7f8a0815bb693b2` — Mutual action preflight: capacity & lead times — MAP for Dedicated/Private
4. `dsid_8bca7188b1ab4065870d0d836f574a44` — Re: MAP cost probe — token economics & batching/caching assumptions
5. `dsid_6e085f20a0ac448e882e94b0d9dd8d7c` — MAP kickoff: draft milestones, who owns what, and target close options
6. `dsid_b3decda0465142bf8bc4b4cc5bb933ae` — Sprint gates & purchase flow: HealthCorps MAP + evaluation plan
7. `dsid_c1a07408bf3c472da41ce5ed8df44c09` — Vendor security questionnaire: SIG vs CAIQ — clarifying asks
8. `dsid_e329f4afaa124f53be372634eb7ab9cb` — PHI boundaries & hosting paths — post-call summary + next steps
9. `dsid_bf0a48f2f2564bc78dbae6b00ce0fcef` — Draft MAP — SDK streaming & toolcall integration: owners, milestones, risks
10. `dsid_9701a2e5d4a54d74acbd973f91ee67f3` — Procurement MAP & sequencing for BlueBridge pilot

### Fill for this row (also include in final JSON array)

```
row_id: 31
question_id: qst_0166::basic
corpus_scale_size: 25000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 32

- **row_id:** `32`
- **question_id:** `qst_0166::basic`
- **corpus_scale_size:** `50000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`
_source: full_erb_file:dsid_10d018b9cd334ababafa960517492a77__20261127-postcall-eval-roadmap-streaming-coherence-checks.txt_

```text
Post-call: model fit roadmap + streaming coherence follow-ups

From: Camila Reyes <camila.reyes@redwood.ai>
To: Alicia Ramos <alicia.ramos@clearpathhealth.com>, procurement@clearpathhealth.com
Cc: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>
Date: 2026-11-20T14:05:00-08:00
Subject: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Alicia / ClearPath team —

Great to meet today — thanks for walking us through the triage flow and the latency constraints for short, clinician-facing prompts. Quick recap and proposed next steps so everyone is aligned: 

1) Primary goals we heard
- Clinical triage responses should be accurate and concise for short prompts (~20–80 tokens)
- Streaming UX must avoid partial incoherent fragments and respect stop sequences for list-style outputs
- Latency target: ideally <= 300ms for initial tokens on short responses; < 700ms tail for longer follow-ups (we discussed getting you stronger SLOs once we baseline)

2) Recommended model candidates to evaluate (initial):
- redwood-44b-int8 (balanced quality / throughput)
- redwood-44b-ptq (aggressive quantized variant for cost-sensitive seats)
- redmini-8b (low-latency option for high-concurrency endpoints)

3) Benchmarks and artifacts I shared (attached and via Drive):
- initial-bench-summary.pdf — high-level comparison across representatives for streaming latency & coherence
- CPH-PromptSamples.csv — the sample prompt set you agreed to share (I redacted PHI during ingestion)
- Drive folder with the raw run configs: https://drive.google.com/drive/folders/1a2b3c_clearpath_eval

4) Streaming-specific areas we'll prioritize during evaluation:
- Stop-sequence enforcement: verify EOS/stop-token handling when prompts include explicit delimiters
- Partial output coherence: stress tests with incremental decoding — ensure the partial tokens emitted are syntactically coherent and not deceptive mid-sentence
- KV/prefix cache behavior for short-turn dialogs: measure cold vs warm latency
- Sampling settings for clinical tone control (temp, top-p / top-k) and their impact on hallucination risk

5) Next steps / asks for you
- Please confirm the sample prompts are representative and send any additional high-priority prompt batches (preferably <100 examples to start)
- Grant the eval folder access to evals@medbench.ai and procurement@clearpathhealth.com so we can share artifacts
- Confirm procurement timeline (procurement@clearpathhealth.com copied) if you want pricing/commit options in parallel

6) Our immediate internal plan: run streaming bench across the three model candidates with the sample prompts, capture per-token latencies and a coherence score (automated metric + small human pass). I’ll loop Ben and Marissa in for execution and follow-up.

Attachments: CPH-PromptSamples.csv, initial-bench-summary.pdf

Thanks — talk soon.

—Camila Reyes
Enterprise AE | Redwood Inference
camila.reyes@redwood.ai | +1 415-555-0198


From: Alicia Ramos <alicia.ramos@clearpathhealth.com>
To: Camila Reyes <camila.reyes@redwood.ai>
Cc: procurement@clearpathhealth.com
Date: 2026-11-23T10:33:00-08:00
Subject: Re: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Camila —

Thanks for the thorough recap, that tracks with our notes. A few clarifications from my side: 

- Latency: our product team is firm on a <= 300ms guideline for short clinical responses (20–60 tokens). If you can show streaming baselines where initial token emissions are consistently under that threshold on the recommended model(s), that will be a big factor in procurement.
- Coherence: we can tolerate brief grammatical mid-phrase edits during streaming, but not hallucinated assertions or truncated recommendations. Stop sequences are especially important for list outputs (e.g., medications).
- Compliance: we need to confirm that any shared evaluation artifacts have PHI removed — appreciate the redaction note. Our security team will want a short evidence pack (SOC 2 scoping, data handling notes) if we move to a private deployment later.

Procurement: our timeline target is an agreement signed by end of Q1 2027 if benchmarks and security checks align. I’ll loop in procurement with any specific questions.

Can you share a proposed cadence for the benchmark results review (quick sync + a technical deep dive)?

Best,
Alicia
Alicia Ramos
Head of Product — Clinical Systems
ClearPath Health
alicia.ramos@clearpathhealth.com


From: Camila Reyes <camila.reyes@redwood.ai>
To: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-24T09:15:00-08:00
Subject: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Team — forwarding Alicia’s reply and distilling the asks. Please treat this as the internal kickoff for the ClearPath streaming evals. Quick assignment and checklist below: 

Context (from Alicia): strict initial-token latency <= 300ms target for short replies; stop-sequence fidelity for list outputs; PHI must be redacted for any shared artifacts. Procurement timeline aiming for end of Q1 2027.

Action items
- Ben: run the streaming bench across redwood-44b-int8, redwood-44b-ptq, redmini-8b. Focus tests on:
  * Per-token latency (cold vs warm KV cache) at 16/64/128 token prefixes
  * Stop sequence enforcement (explicit tokens like "

--END--
") and eos-bias experiments
  * Coherence meter: automatic n-gram overlap + short human pass (I can coordinate 10 manual checks)
  * Output sampling settings: default, temp 0.0–0.5, top-p 0.85–0.95
- Marissa: draft a short results digest for Alicia (one-pager + proposed SLO table) and propose two slots for a review meeting (30m tech sync; 60m deep dive if they want it)
- Jasmine: prep a minimal security evidence note (SOC 2 scope, PHI redaction process used, link to KMS docs) so we can attach it to the digest if they ask

Attachments to include for internal tracking: streaming-test-plan.md, bench-config.json (I uploaded both to the Drive folder). Ben — aim for a first-pass results set by EOD Friday (the 27th). I’ll prepare the client-facing digest after your pass.

Thanks — Camila


From: Ben Carter <ben_carter@redwood.ai>
To: Camila Reyes <camila.reyes@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-27T11:02:00-08:00
Subject: Re: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Folks — short status and preliminary findings from the bench run (attached CSV + summary). Ran the streaming harness against the CPH prompt set (50 of the provided samples) using the configs in bench-config.json.

Summary highlights (first-pass):
- redwood-44b-int8:
  * Median initial-token latency (warm cache, 16-token prefix): ~285ms — within Alicia’s 300ms guideline on average, but 95th percentile spikes to ~520ms on a few prompts with long context prep
  * Coherence: automated rubric flags ~12% of responses where partial streaming output contains truncated clauses that may read as incomplete (examples attached). Stop-sequence enforcement failed on 3/50 cases where the model emitted a token matching stop delimiter mid-stream and did not truncate output; this looks like eos-bias underflow in the quantized path
- redwood-44b-ptq:
  * Faster median latency (~240ms warm) but coherence regressions rise to ~18% by our metric set — likely sampling + quantization artifacts exacerbating mid-sequence token instability
- redmini-8b:
  * Best consistency for streaming (median ~145ms warm), stop sequences respected in 49/50 tests, but hallucination risk is higher for clinical-detail prompts (we saw omissions / simplifications that could be unsafe without a guardrail)

Immediate hypotheses / mitigation suggestions:
- Enforce stop tokens at the decoder level with an early-check and apply a small positive eos bias when a stop delimiter is in the prompt; this reduces the 3/50 failure cases in redwood-44b-int8 in local tests
- Tighten sampling (temp <= 0.3, top-p 0.9) for clinical slots and add a post-stream deterministic verification pass for critical fields (e.g., medication lists)
- Consider a hybrid: redmini-8b for front-line short responses with a routed verification call to redwood-44b-int8/ptq for detail expansion when the prompt length or classification model signals a high-safety path

Attachments: bench-20261127-results.csv (includes per-prompt latency & coherence flags), snippets of failing streams for redwood-44b-int8

Next steps I propose:
- Share this summary + CSV with Camila for client digest (Marissa, please draft the one-pager)
- Schedule a 30m tech sync with ClearPath next week to walk the numbers and the suggested guardrails (Camila: will you propose times?)
- Follow-up bench pass with eos-bias experiments and low-temp sampling to see coherence deltas (I can run this on Monday morning)

Ben Carter
Senior SRE — Inference Performance
ben_carter@redwood.ai
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_8412b7b7ea7d4ba28d0662190d169ff7` — Oxbow Health Systems
2. `dsid_97997d6c05ea451fb63afba925baf9f1` — Procurotics Onboarding
3. `dsid_573ca1fc195e450e85e3f10d1a068cf6` — HelmBridge Healthcare
4. `dsid_7ebcb79ae27b49e2ade629edbf764551` — Silverbridge AI Security
5. `dsid_653df4a231424a6bb4e6b55e03df7dd1` — Granite Harbor Logistics
6. `dsid_70a3499794194af0a1a68476f01a4ea6` — MedPay Bridge LLC
7. `dsid_d8ca6f03b07342d2b58f37aa3e7a8ae7` — Mariner Regulatory HealthData
8. `dsid_c7018f1cf17b4677a9368dda646702a8` — Galena ProcureWise, Inc.
9. `dsid_03e8e7561d79413ebb487cb9926a1670` — Mantelbridge Support & Governance
10. `dsid_a26be99609ac4721b7fe14ef477a27f7` — Cedarbridge Health Systems

### Fill for this row (also include in final JSON array)

```
row_id: 32
question_id: qst_0166::basic
corpus_scale_size: 50000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 33

- **row_id:** `33`
- **question_id:** `qst_0166::basic`
- **corpus_scale_size:** `75000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What procurement target date did ClearPath Health give for signing an agreement after the streaming model benchmark and security review?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_10d018b9cd334ababafa960517492a77`
_source: full_erb_file:dsid_10d018b9cd334ababafa960517492a77__20261127-postcall-eval-roadmap-streaming-coherence-checks.txt_

```text
Post-call: model fit roadmap + streaming coherence follow-ups

From: Camila Reyes <camila.reyes@redwood.ai>
To: Alicia Ramos <alicia.ramos@clearpathhealth.com>, procurement@clearpathhealth.com
Cc: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>
Date: 2026-11-20T14:05:00-08:00
Subject: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Alicia / ClearPath team —

Great to meet today — thanks for walking us through the triage flow and the latency constraints for short, clinician-facing prompts. Quick recap and proposed next steps so everyone is aligned: 

1) Primary goals we heard
- Clinical triage responses should be accurate and concise for short prompts (~20–80 tokens)
- Streaming UX must avoid partial incoherent fragments and respect stop sequences for list-style outputs
- Latency target: ideally <= 300ms for initial tokens on short responses; < 700ms tail for longer follow-ups (we discussed getting you stronger SLOs once we baseline)

2) Recommended model candidates to evaluate (initial):
- redwood-44b-int8 (balanced quality / throughput)
- redwood-44b-ptq (aggressive quantized variant for cost-sensitive seats)
- redmini-8b (low-latency option for high-concurrency endpoints)

3) Benchmarks and artifacts I shared (attached and via Drive):
- initial-bench-summary.pdf — high-level comparison across representatives for streaming latency & coherence
- CPH-PromptSamples.csv — the sample prompt set you agreed to share (I redacted PHI during ingestion)
- Drive folder with the raw run configs: https://drive.google.com/drive/folders/1a2b3c_clearpath_eval

4) Streaming-specific areas we'll prioritize during evaluation:
- Stop-sequence enforcement: verify EOS/stop-token handling when prompts include explicit delimiters
- Partial output coherence: stress tests with incremental decoding — ensure the partial tokens emitted are syntactically coherent and not deceptive mid-sentence
- KV/prefix cache behavior for short-turn dialogs: measure cold vs warm latency
- Sampling settings for clinical tone control (temp, top-p / top-k) and their impact on hallucination risk

5) Next steps / asks for you
- Please confirm the sample prompts are representative and send any additional high-priority prompt batches (preferably <100 examples to start)
- Grant the eval folder access to evals@medbench.ai and procurement@clearpathhealth.com so we can share artifacts
- Confirm procurement timeline (procurement@clearpathhealth.com copied) if you want pricing/commit options in parallel

6) Our immediate internal plan: run streaming bench across the three model candidates with the sample prompts, capture per-token latencies and a coherence score (automated metric + small human pass). I’ll loop Ben and Marissa in for execution and follow-up.

Attachments: CPH-PromptSamples.csv, initial-bench-summary.pdf

Thanks — talk soon.

—Camila Reyes
Enterprise AE | Redwood Inference
camila.reyes@redwood.ai | +1 415-555-0198


From: Alicia Ramos <alicia.ramos@clearpathhealth.com>
To: Camila Reyes <camila.reyes@redwood.ai>
Cc: procurement@clearpathhealth.com
Date: 2026-11-23T10:33:00-08:00
Subject: Re: Post-call: model fit roadmap + streaming coherence follow-ups

Hi Camila —

Thanks for the thorough recap, that tracks with our notes. A few clarifications from my side: 

- Latency: our product team is firm on a <= 300ms guideline for short clinical responses (20–60 tokens). If you can show streaming baselines where initial token emissions are consistently under that threshold on the recommended model(s), that will be a big factor in procurement.
- Coherence: we can tolerate brief grammatical mid-phrase edits during streaming, but not hallucinated assertions or truncated recommendations. Stop sequences are especially important for list outputs (e.g., medications).
- Compliance: we need to confirm that any shared evaluation artifacts have PHI removed — appreciate the redaction note. Our security team will want a short evidence pack (SOC 2 scoping, data handling notes) if we move to a private deployment later.

Procurement: our timeline target is an agreement signed by end of Q1 2027 if benchmarks and security checks align. I’ll loop in procurement with any specific questions.

Can you share a proposed cadence for the benchmark results review (quick sync + a technical deep dive)?

Best,
Alicia
Alicia Ramos
Head of Product — Clinical Systems
ClearPath Health
alicia.ramos@clearpathhealth.com


From: Camila Reyes <camila.reyes@redwood.ai>
To: Ben Carter <ben_carter@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-24T09:15:00-08:00
Subject: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Team — forwarding Alicia’s reply and distilling the asks. Please treat this as the internal kickoff for the ClearPath streaming evals. Quick assignment and checklist below: 

Context (from Alicia): strict initial-token latency <= 300ms target for short replies; stop-sequence fidelity for list outputs; PHI must be redacted for any shared artifacts. Procurement timeline aiming for end of Q1 2027.

Action items
- Ben: run the streaming bench across redwood-44b-int8, redwood-44b-ptq, redmini-8b. Focus tests on:
  * Per-token latency (cold vs warm KV cache) at 16/64/128 token prefixes
  * Stop sequence enforcement (explicit tokens like "

--END--
") and eos-bias experiments
  * Coherence meter: automatic n-gram overlap + short human pass (I can coordinate 10 manual checks)
  * Output sampling settings: default, temp 0.0–0.5, top-p 0.85–0.95
- Marissa: draft a short results digest for Alicia (one-pager + proposed SLO table) and propose two slots for a review meeting (30m tech sync; 60m deep dive if they want it)
- Jasmine: prep a minimal security evidence note (SOC 2 scope, PHI redaction process used, link to KMS docs) so we can attach it to the digest if they ask

Attachments to include for internal tracking: streaming-test-plan.md, bench-config.json (I uploaded both to the Drive folder). Ben — aim for a first-pass results set by EOD Friday (the 27th). I’ll prepare the client-facing digest after your pass.

Thanks — Camila


From: Ben Carter <ben_carter@redwood.ai>
To: Camila Reyes <camila.reyes@redwood.ai>, Marissa Cole <marissa_cole@redwood.ai>, Jasmine Liu <jasmine_liu@redwood.ai>
Date: 2026-11-27T11:02:00-08:00
Subject: Re: Fwd: Post-call: model fit roadmap + streaming coherence follow-ups (internal)

Folks — short status and preliminary findings from the bench run (attached CSV + summary). Ran the streaming harness against the CPH prompt set (50 of the provided samples) using the configs in bench-config.json.

Summary highlights (first-pass):
- redwood-44b-int8:
  * Median initial-token latency (warm cache, 16-token prefix): ~285ms — within Alicia’s 300ms guideline on average, but 95th percentile spikes to ~520ms on a few prompts with long context prep
  * Coherence: automated rubric flags ~12% of responses where partial streaming output contains truncated clauses that may read as incomplete (examples attached). Stop-sequence enforcement failed on 3/50 cases where the model emitted a token matching stop delimiter mid-stream and did not truncate output; this looks like eos-bias underflow in the quantized path
- redwood-44b-ptq:
  * Faster median latency (~240ms warm) but coherence regressions rise to ~18% by our metric set — likely sampling + quantization artifacts exacerbating mid-sequence token instability
- redmini-8b:
  * Best consistency for streaming (median ~145ms warm), stop sequences respected in 49/50 tests, but hallucination risk is higher for clinical-detail prompts (we saw omissions / simplifications that could be unsafe without a guardrail)

Immediate hypotheses / mitigation suggestions:
- Enforce stop tokens at the decoder level with an early-check and apply a small positive eos bias when a stop delimiter is in the prompt; this reduces the 3/50 failure cases in redwood-44b-int8 in local tests
- Tighten sampling (temp <= 0.3, top-p 0.9) for clinical slots and add a post-stream deterministic verification pass for critical fields (e.g., medication lists)
- Consider a hybrid: redmini-8b for front-line short responses with a routed verification call to redwood-44b-int8/ptq for detail expansion when the prompt length or classification model signals a high-safety path

Attachments: bench-20261127-results.csv (includes per-prompt latency & coherence flags), snippets of failing streams for redwood-44b-int8

Next steps I propose:
- Share this summary + CSV with Camila for client digest (Marissa, please draft the one-pager)
- Schedule a 30m tech sync with ClearPath next week to walk the numbers and the suggested guardrails (Camila: will you propose times?)
- Follow-up bench pass with eos-bias experiments and low-temp sampling to see coherence deltas (I can run this on Monday morning)

Ben Carter
Senior SRE — Inference Performance
ben_carter@redwood.ai
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_d36ef5e873bc4b719948073663178630` — Procurement sequencing + condensed MAP & evaluation milestones
2. `dsid_5a7a71032ce149e1b9979bf18bacd6f3` — Post-demo: commercial onramp & security gating — procurement options
3. `dsid_62d0211fd9334dfb85f8ba2194e17a12` — VPC commercial: rebate & support bundling inquiry
4. `dsid_03a70a43e57c4895b63e456c7e836890` — MAP: Alder Health — success criteria, exit gates, and procurement checkpoints
5. `dsid_becda14d664a40bebfc240c766e6c5c2` — Post-call: technical pathway & scope checklist for HealthPath POC
6. `dsid_4fb433d5bc984ee4b7f8a0815bb693b2` — Mutual action preflight: capacity & lead times — MAP for Dedicated/Private
7. `dsid_3ebb269f9c3841fdbdd14c376311e299` — MAP: anchoring the close date — proposed bridge and procurement checkpoints
8. `dsid_fb73513f33204883b0130d2bf88a88b2` — Packaging optimization & tier tradeoffs — ClarityMed
9. `dsid_43a97ef31b374195a66e116b8aa52d68` — MAP cadence lag — forensics and traction plan
10. `dsid_c7110f395ad042769bab6231ca56989c` — Pipeline buffer assessment & mitigation plan — Q2

### Fill for this row (also include in final JSON array)

```
row_id: 33
question_id: qst_0166::basic
corpus_scale_size: 75000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 34

- **row_id:** `34`
- **question_id:** `qst_0200::semantic`
- **corpus_scale_size:** `25000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For the hospital system that wants to run an interactive intake chatbot and auto-generate discharge writeups entirely inside its own locked-down data center with no patient data leaving the network, what end-to-end response time target did they set for producing about 200 tokens under peak load?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_eab7ef95052c4016aff7a3df422131f0`
_source: full_erb_file:dsid_eab7ef95052c4016aff7a3df422131f0__valehealth-implementation-capture.txt_

```text
ValeHealth on-prem implementation capture

Call notes (2024-09-17) — discovery with ValeHealth (CTO: Aaron Li, SecOps: Maya Singh, Arch: Dan Ochoa)\n\n- Context: ValeHealth is a mid-sized digital health provider planning to run conversational triage + discharge-summary generation inside their data center (air-gapped option discussed). They must not send PHI outside their network. Primary asks: private control plane with VPC peering to their corp network, KMS/HSM integration for key material, audit logs for every inference, and 12 month retention for audit records.\n\n- Key constraints called out by customer:\n  - PHI: full PHI scope, must meet SOC2 + HIPAA controls.\n  - Network: strict egress rules; anything that talks to hosted control plane needs explicit allow list.\n  - Hardware: they will provision 2x A100 80GB per zone initially, plan to add 4x after pilot.\n  - Throughput target: 12 concurrent triage sessions, average 40 tokens/response, target p95 token latency per token <= 90ms (end-to-end p95 for a 200-token response <= 18s) — customer expects interactive feel.\n  - Burst behavior: expect spikes morning 8–10AM and post-op 3–5PM.\n\n- Functional reqs (high level):\n  1) On-prem Redwood Private with local model hosting and local KV/prefix caching.\n  2) VPC-only control plane connectivity (can run in their VPC or peered) — no public IPs on inference nodes.\n  3) KMS or HSM integration: must support AWS CloudHSM or on-prem Thales via KMIP.\n  4) Audit logs: immutable tamper-evident logs for each request (user id, route, token counts, prompt hash).\n  5) Structured outputs: discharge summary templates + JSON schema enforcement + function-calling hooks.\n  6) Streaming WebSocket support for triage chat UI.\n  7) Canary deploys and fast rollback; cannot have model drift affecting PHI fidelity.\n\n- Non-functional / ops notes:\n  - Warmup: with A100s expect ~20–40s cold start for large Llama-family models to reach peak throughput. Need pre-warm policy for scheduled windows.\n  - Batch sizing: small batch sizes to preserve latency SLO; recommend continuous batching with low-latency cutoff (15ms).\n  - KV cache: prefix caching will significantly cut token generation for repetitive triage prompts; plan to instrument cache hit rate in pilot.\n  - Quantization: they want FP16 or 4-bit quant for cost; warn: 4-bit may slightly degrade token-level probabilities -> risks for hallucination in medical text. We should plan eval prompts + acceptance criteria.\n  - Telemetry: customer wants token-level cost/latency breakdown exported to Splunk (on-prem) every 1 minute.\n\n- Gotchas / open technical risks:\n  - Network egress policy: Control plane components that check for model updates may require egress. Customer requires whitelisting; need to enumerate IPs and acceptable update cadence. Offline update flow (airgap) must be documented.\n  - HSM cert exchange: support for KMIP versions and cert rotation timeline — Ops needs runbook for emergency rotation.\n  - Model licensing: some open models require attribution; legal to confirm whether ValeHealth agrees to the model license and distribution in-country.\n  - Tokenization mismatch: current front-end uses older tokenizer library; we need to validate prompt/encoding parity to avoid token count surprises and cost overruns.\n  - Long output trimming: discharge summaries sometimes exceed 1,000 tokens; need to support streaming + progressive flush to UI and chunked audit records.\n\n- Example acceptance tests ValeHealth suggested (rough):\n  1) PHI redaction test: send synthetic PHI and ensure logs do not contain raw PHI in plaintext except authorized fields.\n  2) Latency test: 200-token generation p50 < 2s, p95 < 18s under steady load of 12 concurrent sessions.\n  3) Regression test: standard eval suite of 150 prompts for hallucination / clinical accuracy; failure rate < 3% vs baseline model.\n\n- Quick numbers back-of-envelope (for sizing discussion):\n  - If we run Llama-3-classic-70B FP16 on A100-80: single GPU peak concurrency for low-latency ~6–8 simultaneous single-stream sessions (depends on context length). With 2 GPUs expect ~12–16 sessions — matches their initial 12 target.\n  - If they quantize to 4-bit, can increase concurrency ~1.5x but verify regressions.\n\n- Prompts / eval plan notes to self:\n  - Set up a small eval harness with their sample chart notes (deidentified) + golden summaries from clinicians. Use rouge/med-sa metrics and human spot checks.\n  - Create prompt templates that force structured JSON output with explicit \"extractionConfidence\" fields so UI can flag low-confidence sections for clinician review.\n\n- Compliance & legal items to loop in:\n  - Legal: confirm data residency policies and model license acceptability.\n  - Security: run threat model for Private control plane; provide pen-test window.\n  - Privacy: document data retention and deletion for audit logs (they asked 12 months but want ability to purge per request).\n\n- Action items / next steps (owners + dates):\n  - Priya: Draft on-prem architecture sketch & airgap flow; include IP whitelist and update cadence -> due 2024-09-23.\n  - Jordan: Prep rough cost/throughput matrix comparing FP16 vs 4-bit and likely concurrency -> due 2024-09-25.\n  - Evan: Prototype tokenizer parity check using ValeHealth frontend sample prompts; report tokenization deltas -> due 2024-09-26.\n  - Rita: Open legal thread with licensing & PHI handling questions; sync with Legal -> create ticket VALE-124 by 2024-09-20.\n  - Schedule: Book follow-up workshop for pilot scoping (architect deep-dive + security) w/ ValeHealth and infra ops -> target week of 2024-09-30.\n\n- Meeting artifacts to attach to pilot folder (TODO):\n  - Synthetic PHI test vectors (anonymized)\n  - Clinician gold-summaries (deid) for eval harness\n  - Network diagrams and firewall rules template for their infra team\n\n- Notes to self (raw):\n  - Keep canary window small, ensure rollback by model tag (do not rely on in-place weights swap without versioned checkpoints).\n  - Need a short (1–2 slide) cheat sheet on expected latency/cold-start behavior for sales to set expectations.\n  - Consider offering a Managed Updates opt-in where we push vetted model/security updates on a monthly cadence to reduce their ops burden.\n\n- Questions to raise in next call:\n  1) Can ValeHealth provide a stable internal registry (S3 or Artifactory) for model artifacts and container images?\n  2) Which exact HSM vendors do they have on-prem? (Thales, AWS CloudHSM, Gemalto?)\n  3) Do they expect encryption-in-use (SGX/Confidential VMs) beyond KMS-at-rest?\n\nEnd of raw capture.\n\n-- Priya (notes kept informal, will formalize into pilot scoping doc after internal sync)\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_ae34b1a3cb6a47c8aeeaf6eb4cd9fa4c` — Vermillion Hall Platforms
2. `dsid_78643c4ae9f24e7ab7543da3e8c40266` — LatticeBeam QueryCraft
3. `dsid_4df2ca01cc9b427d985c51a63b595a87` — CoveHaven QuickAssist
4. `dsid_43b87c65f81b4e2ca03ef919c456effd` — Moonbeam Sprint AI
5. `dsid_caa8922c528b4bad8c5391ec1e5ad409` — Pyxis Transit Systems
6. `dsid_080da3e2a82e41158a49f62d4739dc46` — NimbleClasp AIWorks
7. `dsid_b558dd44aa6141228f8cafc23dcbfe89` — BrightSail Answers
8. `dsid_627192b1db54474386f0be4d1905f678` — Elm Harbor Assistants
9. `dsid_9a685924a565498f98e609151249d57f` — Fractile CX Economics
10. `dsid_9fad67220fcc4e6596b8f2cc292872d1` — Crimson Lark Assist

### Fill for this row (also include in final JSON array)

```
row_id: 34
question_id: qst_0200::semantic
corpus_scale_size: 25000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 35

- **row_id:** `35`
- **question_id:** `qst_0204::semantic`
- **corpus_scale_size:** `5000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What are the immediate follow up actions for the mid market product analytics SaaS that wants cheaper and more consistent in app assistant responses and is planning a short trial on the shared service before moving to a private network isolated deployment?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a45c07f3daaf47c18b7bc75d3cbf2112`
_source: full_erb_file:dsid_a45c07f3daaf47c18b7bc75d3cbf2112__company-pillarhaven-insightworks.txt_

```text
Pillarhaven Insightworks

Run 2-week Hosted API POC with parity test suite; prepare Dedicated pricing proposal and capacity options; schedule security QA kickoff.
Context: Pillarhaven is a mid-market B2B SaaS (product analytics + in-app help). Currently on OpenAI for chat & embeddings; runs ~120k monthly tokens (prod), expect growth to 700k within 12 months. Primary driver: lower inference unit costs + predictable latency for in-app assistant and automated summarization. Secondary driver: regulatory requirement for stronger audit trails and ability to isolate data in a VPC when migrating to Dedicated.

Key quotes / call highlights:
- "We need output parity for top-5 prompts before we flip traffic; customers notice tone changes." (Head of Product)
- "Pricing predictability matters more than absolute lowest cost — committed capacity + burst are attractive." (VP Eng)

Technical / evaluation details (POC scope):
- Workloads: multi-turn chat (support assistant), long-doc summarization (1k-10k tokens), embeddings for semantic search and reranking.
- Latency targets: 95th percentile < 250ms for <512 token chat responses in Dedicated; Hosted POC target < 300ms at test QPS.
- Throughput: baseline 50 qps peak for chat, 200 qps for bulk embedding jobs (batching acceptable).
- Migration needs: OpenAI-compat API behavior (messages schema, streaming semantics, stop sequences), token counting parity, and identical temperature/penalty mapping.
- Parity testing: run 2k representative prompts through Redwood hosted API with compat layer; compare semantic similarity (embeddings), ROUGE/BLEU and human review for summarization; target regressions <3% on critical prompts.
2026-01-12: Inbound lead from product blog; initial qualification by AE Ethan Brooks.
2026-01-20: Hosted API demo (chat+embeddings) - AE + SE (Priya). Fireflies ff_20260120_9b3f.
2026-02-05: Security call - infra asks about KMS, VPC peering, retention; provided SOC2 evidence.
2026-02-12: Pricing sync - asked for committed throughput tiers and burst allowances; discussed committed-discount model.
2026-02-20: POC kickoff approved - 2-week hosted POC, dataset = 5k historical support chats + 1k long-docs for summarization.
2026-02-26: Parity test run 1 - embeddings parity OK, summarization shows style/regression differences on ~8% samples.
2026-02-28: Internal Redwood follow-up: propose mapping rules for prompt compatibility + regression mitigation plan.
openai_compat_layer
prompt_parity_suite
evals_integration
latency_95p<250ms
throughput_200qps
kv_cache_support
Interested in committed Dedicated tier with monthly commit. Key negotiation items: commit size that covers peak QPS + 20% burst, overage pricing, migration credit for Hosted POC months, and transition timeline (30-60 days). Asked for blended ARR estimate and TCO comparison vs current vendor.
Phase 1: Hosted POC using OpenAI-compat shim + prompt parity tests. Phase 2: Pilot on Dedicated (small reserved pool) with VPC peering and KMS. Phase 3: Cutover using blue/green traffic split and regression monitor; fall back to original provider for 14 days if regressions exceed threshold.
Medium. Biggest risks: subtle prompt-output drift on summarization and code-like responses; SSO/SAML timing for enterprise SSO; contract terms for data residency. Mitigations: run human-in-the-loop comparisons during POC, tune quantization/profile recommendations from Redwood Optimize, schedule SAML integration early.
1) Upload canonical prompt set & 2k sample chats to POC sandbox (engineering to provide). 2) SE to deliver parity-run plan + baseline metrics by 2026-03-04. 3) Redwood to send Dedicated term sheet and committed tier options by 2026-03-10. 4) Schedule security QA with Pillarhaven infra week of 2026-03-08.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_48e13d429774409db3aaa152d19407b6` — RiverMark Assist
2. `dsid_799a1bb8e7234cdf89834a0a17e04ba4` — Elmbridge Apps
3. `dsid_451062cb78a04e08adb918f8c77a3748` — SableBeam Assist
4. `dsid_622d015ee083494eaefdb80d70b7638a` — Sundrop Hollow Analytics
5. `dsid_85d1214a19b44f779a5c844647712756` — Saffron Lane Systems
6. `dsid_5b7ebd1666de42f68602a7663ab34b63` — SummitRidge Cognify
7. `dsid_feb8da8346204b55a30da34d84e24073` — FoxDen FastAI
8. `dsid_3c69e5d0b7a6462d9c7d54f40dbb914d` — SpruceTop AssistKit
9. `dsid_58a34b025e1c4ccf8c97dbc9e042548b` — Indigo Trail Assist
10. `dsid_8ca703d991844bd195b4b8fdc16040fd` — Copperfield Nimbus Solutions

### Fill for this row (also include in final JSON array)

```
row_id: 35
question_id: qst_0204::semantic
corpus_scale_size: 5000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 36

- **row_id:** `36`
- **question_id:** `qst_0208::semantic`
- **corpus_scale_size:** `15000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For the Fortune 500 oriented customer evaluating a dedicated inference setup for an agent assist contact center, what burst traffic level and duration did they ask the vendor to guarantee beyond their steady state request rate?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_c336dcdf965d44b0bcf4c8e3930af440`
_source: full_erb_file:dsid_c336dcdf965d44b0bcf4c8e3930af440__company-ironclad-support-reserve.txt_

```text
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
- Week 3: Integrate tool-calling with ticket API (demo end-to-end: summary -> open ticket -> attach transcript).
- Week 4: Run 72-hour soak, capture metrics for cost modeling and draft SLO suggestions (batching profiles, quantization recommendations from Redwood Optimize).

Open questions / risks:
- Procurement wants Redwood's SOC2 Type II report and FedRAMP? (customer asked for 'FedRAMP-like' controls) — blocker for procurement.
- Networking: need VPC peering + static egress IPs; networking team must complete firewall exception by POC start.
- Spike shaping: they want a hard SLA for 60s burst windows — legal to review.

Quotes / customer color:
- 'We need predictable inference—we can't afford an extra 400ms during a Black Friday–like surge.' — Head of Ops.
- CS leadership prefers a single vendor for inference to simplify incident response.

Next steps (short):
- Send SOC2 evidence pack + security FAQ (owner: Maya). Gmail threads: gt_4d5e6f_security_questions.
- Schedule VPC peering kickoff with NetOps (target 2026-03-15).
- Kick off lab POC (Liam) once firewall exceptions complete.

Internal notes for AE/SE:
- Focus POC metrics on p95/p99 token latency and cold-start frequency. Capture model switch latency when routing to fallback variant.
- Prepare a cost estimate for reserved pool sizes (baseline vs 3x burst reserve).
- Highlight Redwood Console tracing on per-request token breakdown for audit demos.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_4f28f2c0e594459f9bda0cedbce6dda7` — Aurora SpikeGuard CX
2. `dsid_f64d70ed51db4c7c94ae26be93157bb8` — Sequoia Reserve Workshop Co
3. `dsid_0378cb48015d438fac7668e261750bd7` — StratusPeak Surge Systems
4. `dsid_a2e4352770864f679741fd902a51ee87` — Cobalt Finance
5. `dsid_1c22110ff4394bbea631b330f48bdc0f` — Crestline Realtime Assist
6. `dsid_3b8a6d554a994a739449fd95719f32ae` — Obsidian Harbor Inference Labs
7. `dsid_40c1008e9c4c44e1ab69666e14031887` — Mariner Benchmarking Labs
8. `dsid_9b7c033ca2d741b380c38e3edd38273d` — Lumen Reserve Platforms
9. `dsid_79518960a5e94ef099f030986d818a53` — Pegasus Flow Assist
10. `dsid_5ef618fee40741bb9fac512e2448e560` — Ferncrest Inbound AI

### Fill for this row (also include in final JSON array)

```
row_id: 36
question_id: qst_0208::semantic
corpus_scale_size: 15000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 37

- **row_id:** `37`
- **question_id:** `qst_0209::semantic`
- **corpus_scale_size:** `100000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For a small B2B SaaS embedding a live chat helper inside their product that needs partial replies immediately while it fetches recent user-event context, what first-response-time target and concurrent-load threshold were set as the pass criteria for their short trial?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_51183030e764419caca09cfe647048e7`
_source: full_erb_file:dsid_51183030e764419caca09cfe647048e7__company-banyan-loop-ai.txt_

```text
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
2026-02-15 - Sent ask list: Okta SAML, audit logging SLA, cost per 1k tokens on hosted; requested best practices for prefix caching
2026-02-18 - Follow-up call: customer wants short 2-week POC, prioritize streaming latency and rollout plan for feature flags
Schedule 30m demo of streaming SDK + perf notes; send starter prompt set; confirm Okta SAML details
SAML metadata not shared
finance needs clearer ARR estimate
want latency SLA note for hosted tier
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_a7de4ed8e20d4fd784748c38d66c1ee8` — RazorLeaf Chatly
2. `dsid_70b7129b5b5940d8a17b1322f649957a` — QuickReply Stack
3. `dsid_d6ffa7c2fade456ea0e9628164c50e3b` — MicroGlint Assistly
4. `dsid_5607a534089044e99d2422ffe483df27` — TidePointe Assistive AI
5. `dsid_bef1504f9179415bb2ebc5e2be12a7c3` — OrbitLoop Support
6. `dsid_872c0e6b001e4719bcb860b908f9d29a` — NibbleLoop Assistantry
7. `dsid_b558dd44aa6141228f8cafc23dcbfe89` — BrightSail Answers
8. `dsid_6eb7309b85b24fc38090e56f568f6d89` — Driftline Assistly
9. `dsid_d030f33813764880947db98061d277cf` — VelociChat Solutions
10. `dsid_5a28962c1cb44e5699fce877df71bf35` — Slatefold Insights

### Fill for this row (also include in final JSON array)

```
row_id: 37
question_id: qst_0209::semantic
corpus_scale_size: 100000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 38

- **row_id:** `38`
- **question_id:** `qst_0213::semantic`
- **corpus_scale_size:** `40000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For a content templating company planning tens of millions of very short generations during a Q3 ramp, what was the requested plan for a time limited evaluation that included a large free usage allowance?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ad14c3cb06c4494093dfcfff5098d89d`
_source: full_erb_file:dsid_ad14c3cb06c4494093dfcfff5098d89d__company-bramblebox-content-labs.txt_

```text
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
- Question on model fallback: can Redwood route to cheaper variant automatically when quota hit? client likes policy-based routing idea.
Next steps (explicit):
- Provide 14-day trial API keys + 50M free tokens for benchmark.
- SE (Maya) to run 3-scenario benchmark (small, quantized-medium, medium) and return per-token cost and latency percentiles.
- Deliver short doc with recommended batching/timeouts + example SDK snippet for concurrent batch sends.
- Sales to send short T&Cs and expected ARR bands for SMB tier.
Open issues / blockers (short):
- Token cost still primary blocker until benchmark; need clear projected monthly bill for 30-60M tokens.
- Want assurance on per-route rate limits and throttling behavior for multi-tenant customers.
- No SSO yet; not blocking but will be needed if larger pilots proceed.
Notes tone: choppy/actionable. client is pragmatic, focused on unit economics.
Potential: high-volume low-ticket ARR — likely start as self-serve, convert to paying SMB within 1-2 months if cost target met.
"If we can get predictable costs and decent latency, we'll push this into our editor and onboard users next quarter." — Eliza M.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_4b07ee432d54461e8e41640a184a47ef` — PhraseForge Labs
2. `dsid_b65f12db881f41dc9239fe044f4754dd` — FluentForge Mediaworks
3. `dsid_b22b28a8614b4aaf9e0b7a94b1b4e461` — Verblyx Content Suite
4. `dsid_8d95e02dfe9241b78cf697c0b4921c9b` — SparkPlume Marketing Lab
5. `dsid_1f2249d75d8c4f9fb387f2d5a9b599e5` — SierraFold ProductWorks
6. `dsid_4ab355f5e3fa460688f3f24f7ad27d60` — Runway Inferwise
7. `dsid_d65ee44630bc41e690542da2d87fcf89` — SparrowBurst Systems
8. `dsid_8072db5171ba4c0eb05debefe16d5262` — Verbatimly Marketing Platform
9. `dsid_73c78b2ba4f94c8ca693978422ad296a` — Larksong Systems
10. `dsid_e7afaaeaeb2f46619c64a33dd14200c1` — Strandly Marketing Systems

### Fill for this row (also include in final JSON array)

```
row_id: 38
question_id: qst_0213::semantic
corpus_scale_size: 40000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 39

- **row_id:** `39`
- **question_id:** `qst_0224::semantic`
- **corpus_scale_size:** `75000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the public documentation for searching system activity records, what identifier should examples use instead of showing a persons email address to avoid exposing sensitive personal data?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_96088536cbcc449eb676e94bf800486a`
_source: full_erb_file:dsid_96088536cbcc449eb676e94bf800486a__1876543210-audit-log-query-snippet-and-link-rot-fix.txt_

```text
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

compliance_rob: wording pass from compliance with one change: in the retention table replace "indefinite" with "customer-managed (no default)" for Private deployments. Hosted defaults should still show example value 90 days.

sec_ari: security approves the RBAC snippet. Could you add a one-line note: "Do not run queries that export raw tenant PII without customer consent and proper KMS envelope encryption."

jess-docs: added the KMS envelope sentence into the export section and showed a sample export command: ```bash
redwood audit export --filter 'tokenized_actor_id = "tok_..."' --dest s3://my-bucket/audit-bundle.tar --kms-key arn:aws:kms:us-west-2:123456789012:key/abcd-ef01
aws s3 cp audit-bundle.tar s3://my-bucket/ --acl private
```

elaine: pushed a Go SDK snippet for streaming queries: ```go
ctx := context.Background()
opts := audit.QueryOptions{Filter: "event_type = \"login.failure\" AND tokenized_actor_id = 'tok_123'", PageSize: 100}
stream, err := client.Audit.Query(ctx, opts)
for stream.Next() {
    ev := stream.Event()
    fmt.Println(ev.EventType, ev.Timestamp)
}
if err := stream.Err(); err != nil { log.Fatalf("query error: %v", err) }
```

jess-docs: perfect. I also added a short migration checklist for customers upgrading from the legacy schema, and included the CLI flag note `--concurrency` for multi-threaded migration.

docs-bot: CI re-run 7 checks: all passing. Lint: CLI snippet formatting warning fixed.

jess-docs: thanks, folks. Final asks: @compliance_rob can you confirm the hosted retention example (90 days) is OK to ship as an example value? @sec_ari final signoff on the export KMS sentence?

compliance_rob: 90 days is fine as an example. We'll follow up with compliance to finalize defaults for the policy page.

sec_ari: LGTM for security. RBAC + KMS note included.

jess-docs: merging now. I'll also open a follow-up issue to add a tiny note in the internal docs about not using plaintext emails in public examples.

docs-bot: PR #4199 merged by jess-docs  changelog updated.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_34fdaca05c5a4b9e993acc4d874410f2` — Temporary restricted query access to raw inference traces for security investigation
2. `dsid_b107a80048a3416399f3035a2a212897` — Stage-gated anonymized session extract for regulatory data correction request (Acme Health)
3. `dsid_f8188e8b6fea41d6b75280a3448e4a7c` — Time-boxed access to de-identified inference snippets for privacy validation of new redaction rules
4. `dsid_9720935431c34e4b8ec4bbf19058ac10` — Temporary re-identification proof for regression analysis
5. `dsid_54f31ab02427447a9920f9c6004c00a9` — eng-security
6. `dsid_5ae902af66af4638b1f7599937e6ae5a` — Timebound credentialed replay sampler access for data subpoena response
7. `dsid_8227309d1f954048b6690aef8454daa3` — Request: canonical access journal reconciliation & export packaging for SIG
8. `dsid_79de123d71494a34b5e924d4252aba7d` — Approval request: timeboxed obfuscated session handoff to Privacy triage for customer incident
9. `dsid_ee4bbadb32f14a57a022161e7a3183eb` — Tenant-aware SIEM entity crosswalk, deterministic pseudonymization, CSV deliverable and security evidence bundle
10. `dsid_da17037e340a474b947c88433b6eeb28` — Scoped approval: audit-gated snapshot of pseudonymized request traces for replay investigation (enterprise customer)

### Fill for this row (also include in final JSON array)

```
row_id: 39
question_id: qst_0224::semantic
corpus_scale_size: 75000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 40

- **row_id:** `40`
- **question_id:** `qst_0234::semantic`
- **corpus_scale_size:** `40000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

During the rollout of the new version of our inference cost optimizer, what is the suggested traffic ramp schedule for moving from a small canary to full production, including the minimum stabilization wait between increases?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ad58457891774bd7ba480e0bcd13df3a`
_source: full_erb_file:dsid_ad58457891774bd7ba480e0bcd13df3a__optimize-conductor-4-0-release-notes-and-migration-guide-2028-09-15.txt_

```text
Optimize Conductor 4.0 release notes and migration guide

Overview

This document describes the Optimize Conductor 4.0 release: feature highlights, API and UX changes, SLO and cost implications, a step-by-step migration and rollout checklist for customers and internal teams, and known issues and rollback procedures. Optimize Conductor 4.0 ships a new multi-tenant optimization engine, deep integration with the Fidelity Advisor, and kernel-aware scheduling to reduce per-token cost while preserving observed fidelity.

Goals of the release

- Reduce average per-token inference cost for mixed conversational workloads by 15–35% depending on traffic shape.
- Enable live fidelity negotiation between the Optimize Advisor and the serving runtime for dynamic, SLO-aware routing.
- Provide robust, telemetry-first migration paths for existing Conductor 2.x/3.x customers with minimal service disruption.
- Expose a stable API and a migration shim to preserve backwards compatibility for SDKs and partner integrations.

What’s new in 4.0 (high level)

1) Multi-tenant optimization engine
- A federated optimizer that maintains per-tenant batching and caching policies with a global capacity-aware admission controller.
- Benefits: better cross-tenant utilization, fewer cold-start penalties for low-volume tenants.

2) Kernel-aware scheduling and quantization profiles
- Scheduler now uses model architecture and target hardware metadata (kernel fingerprints) to select quantization and execution paths per-batch.
- Benefits: improved throughput for quantized variants, automatic fallbacks to safe execution paths under load.

3) Fidelity Advisor v2 integration
- Live API that negotiates fidelity targets per-request with the serving runtime. Fidelity policies are evaluated against real-time telemetry and historical customer thresholds.
- Benefits: observable, auditable fidelity decisions and automated crediting adjustments.

4) Hybrid KV-prefetch cache coordinator
- Local-prefetch proxy and a cloud-coordinated KV cache eviction protocol reduce repeated KV misses for session-heavy conversational workloads.

5) Telemetry and cost-normalization changes
- New per-route cost attribution fields (cost_estimate, cost_adjuster_id).
- Streaming telemetry schema v3 (see Observability section below).

6) Console UX and API changes
- New Optimize Conductor UI: per-tenant policy editor, rollout simulator, and a migration dashboard.
- API: /optimize/v4/policies, /optimize/v4/migrate, /optimize/v4/simulate

Compatibility and deprecations

- Backwards compatibility: SDKs calling /optimize/v3 will be routed to a compatibility shim which preserves prior semantics for 12 months post-release. We recommend migrating to v4 within 90 days for full performance benefits.
- Deprecated: legacy batch policy fields 'batch_target_ms' and 'kv_strategy: legacy' are deprecated and will be removed in 2029-10-01.

Important SLO and performance notes

- Expected latency impact: median generation latency unchanged for steady-state traffic; p95 may improve for quantized-optimized paths but can increase during initial migration windows by ~5–10% while batchers warm.
- Cost impact: measured 15–35% savings in mixed chat + embeddings workloads in beta; savings are sensitive to session affinity and average prompt length.
- Telemetry SLO: optimize-conductor ingestion should achieve 99.9% delivery for telemetry events; customers relying on fidelity negotiation should ensure <500ms telemetry propagation to meet tight latency SLOs.

Release compatibility matrix (summary)

- Conductor 2.x -> 4.0: Must run migration shim; recommended staged canary rollout (see checklist).
- Conductor 3.0 -> 4.0: Direct upgrade supported; run the compatibility tests in the migration playbook.

Migration plan and checklist (recommended approach)

Ownership: product -> release manager; eng-platform -> rollout; eng-serving-runtime -> runtime compatibility; customer-success -> customer comms.

Phases:
1) Preparation (2 weeks before canary)
- Identify tenants for staged rollout; prefer 5–10% of traffic slice for initial canary.
- Verify that the customer has telemetry-forwarding >= 99% and healthchecks for /v1/health of local-prefetch proxies.
- Run preflight simulator: curl -X POST /optimize/v4/simulate -d '{"traffic_profile":"tenant-sample"}' and confirm cost_estimate delta.

2) Canary (1 week)
- Deploy Optimize Conductor 4.0 to a single region and enable only non-critical tenants.
- Monitor p50/p95 latency, KV miss rate, policy decision error rates, and fidelity negotiation failures.
- Keep compatibility shim active for any SDKs hitting /v3.

3) Gradual rollout (2–6 weeks)
- Increase traffic in doubling increments (10% -> 20% -> 40% -> 80% -> 100%), waiting for stable telemetry after each step (minimum 24 hours).
- Validate cost and quality metrics against baseline.

4) Post-rollout verification (2 weeks)
- Run fidelity regression suites (PRD test harness) and collect customer-reported regressions.
- Disable compatibility shim after confirming zero critical regressions for 14 days.

Migration checklist (detailed)

- [ ] Run preflight simulation and capture cost_estimate baseline.
- [ ] Ensure customers have updated SDKs supporting v4 or confirm compatibility fallback is acceptable.
- [ ] Confirm telemetry schema v3 ingestion is enabled for the tenant.
- [ ] Validate KMS/HSM policies for any encrypted KV prefetch state.
- [ ] Coordinate canary window with customer success for high-value accounts.
- [ ] Record rollback points (cluster snapshots, config versions).

API changes and examples

New endpoints (examples):
- POST /optimize/v4/policies
  payload: {"tenant_id":"t-123","policy":{"fidelity_target":"balanced","batch_budget_ms":60}}
- POST /optimize/v4/migrate
  payload: {"tenant_id":"t-123","target_version":"4.0","dry_run":true}
- POST /optimize/v4/simulate
  payload: {"traffic_profile":"conversational-heavy","seed":42}

Sample migration CLI (internal):
- rwdctl optimize migrate --tenant t-123 --target 4.0 --dry-run

Console changes and operator guidance

- New migration dashboard: shows per-tenant cost delta, fidelity regression flags, and a staged rollout controller.
- Operators should use the simulator to sanity-check policy updates before committing to tenant production.

Observability and telemetry details

Telemetry schema v3 highlights: new fields
- cost_estimate (float): in USD per 1000 tokens estimated by optimizer
- cost_adjuster_id (string): id of the cost normalization rule applied
- fidelity_decision_id (string): cross-reference to Fidelity Advisor decision traces

Recommended dashboards and alerts
- Dashboards: Optimize Conductor 4.0 -> Per-tenant cost trends, Batch utilization heatmap, Fidelity decision trace viewer.
- Alerts (examples):
  - fidelity.negotiation.failures > 1% in 5m -> Sev2 (owner: eng-serving-runtime)
  - kv.miss_rate increase > 2x baseline in 10m -> Sev2 (owner: eng-platform)
  - telemetry.ingestion.failures > 0.1% in 15m -> Sev1 (owner: eng-sre)

Quality and evaluation guidance

- Run the packaged regression harness: tests/regression/optimize_v4/ which includes synthetic traffic shapes: conversational-heavy, short-prompt-burst, embedding-only, mixed-transactional.
- Evaluation metrics to track: response_consistency, hallucination_rate (if available), latency_p95, per_token_cost.

Known issues and limitations

- During heavy partitioning events the hybrid KV-prefetch coordinator may temporarily increase tail latency by up to 40% until evictions stabilize. Workaround: toggle prefetch:fallback_to_local = true.
- Some edge model variants with custom CUDA kernels may not yet benefit from kernel-aware scheduling; consult the compatibility matrix.
- Console migration dashboard can display stale cost deltas for tenants with infrequent traffic; use the simulate endpoint for accurate dry runs.

Rollback plan

- If p95 latency or fidelity regressions exceed defined thresholds during canary:
  1) Pause rollout and revert policy updates via /optimize/v4/policies rollback API.
  2) If regression persists, scale back to previous conductor image using cluster snapshot and disable multi-tenant optimizer feature flag.
  3) Notify customer-success and schedule a hotfix window.

Security and compliance notes

- Conductor 4.0 requires that any prefetch cache state persisted to disk is encrypted with customer KMS keys for customers with restricted confidentiality settings.
- Audit logging: all fidelity negotiation decisions are written to the audit log stream with retention consistent with customer's compliance tier.

Customer communication and enablement

- Outbound comms: send migration playbook and preflight checklist to customers 10 business days before planned migration.
- Include an optional 30-minute technical review call for enterprise customers during canary.

Appendix A: Backwards compatibility shim behavior

- The compat shim translates /optimize/v3 semantics to v4 with the following rules:
  - Legacy batch_target_ms -> batch_budget_ms mapping with normalization factor 0.8.
  - Explicitly disables kernel-aware scheduling for shimmed requests to preserve latency characteristics.
  - Returns a deprecation header: X-Optimize-Deprecation: v3-compat; replacement: /optimize/v4

Appendix B: Telemetry migration sample

- Example event (schema v3):
  {
    "timestamp":"2028-09-15T14:32:05Z",
    "tenant_id":"t-123",
    "route":"/v1/generate",
    "cost_estimate":0.0024,
    "fidelity_decision_id":"fd-789",
    "batch_id":"b-456"
  }

Contacts and ownership

- Release owner: Priya Ramakrishnan (product)
- Runtime compatibility: Anika Patel (eng-serving-runtime)
- Rollout and infra: Marcus Liu (eng-platform)
- Customer enablement: Diego Alvarez (customer-success)

Document history

- 2028-09-15: Draft created by Priya Ramakrishnan
- 2028-09-18: Internal review and expanded migration checklist (reviewers: Diego, Maya)
- 2028-09-20: Published after resolving compatibility shim behavior notes
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_0084c60e481b426d9810bd95581e7cd7` — introduce-adaptive-warmup-probe-and-traffic-rampup-sentinel-for-canary-orchestrator
2. `dsid_af5a00d697a84f3db1d3503eef66b055` — Microphase release conductor: slate, observability notes, and quick rollback
3. `dsid_162a23cfbbe64f50abb0e8cd5e34c023` — traffic-conditional throughput confidence fence and hysteresis rollback policy
4. `dsid_9f02944542c24e8ca28be216bc0e5665` — Canary Playtest & KPI Lighthouse — Go/No-Go Workbook
5. `dsid_d7d4834102c44a4a8c154cd192757da9` — Model serving rollout readiness + KPI escalation ladder
6. `dsid_a66baf012dc248a49ccdd0e9ff14d6e5` — Introduce traffic-conditioned stability sieve for rollout guards
7. `dsid_ef0efd89151944dc91bbd43d90d094ce` — Progressive-traffic experiment playbook with quality-score gates and automated rollback
8. `dsid_b16eb801dbc741558b841c7c3047e98d` — Rollout economics prioritization checklist and calendar — 2026 WIP
9. `dsid_d860b38467164897a12689e77a689d5b` — Roll-forward/Haltable Canary for Optimize Recommendation Enactment
10. `dsid_a2fce6c2cdea4418952592e91372fd6b` — eng-releases

### Fill for this row (also include in final JSON array)

```
row_id: 40
question_id: qst_0234::semantic
corpus_scale_size: 40000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 41

- **row_id:** `41`
- **question_id:** `qst_0234::semantic`
- **corpus_scale_size:** `100000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

During the rollout of the new version of our inference cost optimizer, what is the suggested traffic ramp schedule for moving from a small canary to full production, including the minimum stabilization wait between increases?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ad58457891774bd7ba480e0bcd13df3a`
_source: full_erb_file:dsid_ad58457891774bd7ba480e0bcd13df3a__optimize-conductor-4-0-release-notes-and-migration-guide-2028-09-15.txt_

```text
Optimize Conductor 4.0 release notes and migration guide

Overview

This document describes the Optimize Conductor 4.0 release: feature highlights, API and UX changes, SLO and cost implications, a step-by-step migration and rollout checklist for customers and internal teams, and known issues and rollback procedures. Optimize Conductor 4.0 ships a new multi-tenant optimization engine, deep integration with the Fidelity Advisor, and kernel-aware scheduling to reduce per-token cost while preserving observed fidelity.

Goals of the release

- Reduce average per-token inference cost for mixed conversational workloads by 15–35% depending on traffic shape.
- Enable live fidelity negotiation between the Optimize Advisor and the serving runtime for dynamic, SLO-aware routing.
- Provide robust, telemetry-first migration paths for existing Conductor 2.x/3.x customers with minimal service disruption.
- Expose a stable API and a migration shim to preserve backwards compatibility for SDKs and partner integrations.

What’s new in 4.0 (high level)

1) Multi-tenant optimization engine
- A federated optimizer that maintains per-tenant batching and caching policies with a global capacity-aware admission controller.
- Benefits: better cross-tenant utilization, fewer cold-start penalties for low-volume tenants.

2) Kernel-aware scheduling and quantization profiles
- Scheduler now uses model architecture and target hardware metadata (kernel fingerprints) to select quantization and execution paths per-batch.
- Benefits: improved throughput for quantized variants, automatic fallbacks to safe execution paths under load.

3) Fidelity Advisor v2 integration
- Live API that negotiates fidelity targets per-request with the serving runtime. Fidelity policies are evaluated against real-time telemetry and historical customer thresholds.
- Benefits: observable, auditable fidelity decisions and automated crediting adjustments.

4) Hybrid KV-prefetch cache coordinator
- Local-prefetch proxy and a cloud-coordinated KV cache eviction protocol reduce repeated KV misses for session-heavy conversational workloads.

5) Telemetry and cost-normalization changes
- New per-route cost attribution fields (cost_estimate, cost_adjuster_id).
- Streaming telemetry schema v3 (see Observability section below).

6) Console UX and API changes
- New Optimize Conductor UI: per-tenant policy editor, rollout simulator, and a migration dashboard.
- API: /optimize/v4/policies, /optimize/v4/migrate, /optimize/v4/simulate

Compatibility and deprecations

- Backwards compatibility: SDKs calling /optimize/v3 will be routed to a compatibility shim which preserves prior semantics for 12 months post-release. We recommend migrating to v4 within 90 days for full performance benefits.
- Deprecated: legacy batch policy fields 'batch_target_ms' and 'kv_strategy: legacy' are deprecated and will be removed in 2029-10-01.

Important SLO and performance notes

- Expected latency impact: median generation latency unchanged for steady-state traffic; p95 may improve for quantized-optimized paths but can increase during initial migration windows by ~5–10% while batchers warm.
- Cost impact: measured 15–35% savings in mixed chat + embeddings workloads in beta; savings are sensitive to session affinity and average prompt length.
- Telemetry SLO: optimize-conductor ingestion should achieve 99.9% delivery for telemetry events; customers relying on fidelity negotiation should ensure <500ms telemetry propagation to meet tight latency SLOs.

Release compatibility matrix (summary)

- Conductor 2.x -> 4.0: Must run migration shim; recommended staged canary rollout (see checklist).
- Conductor 3.0 -> 4.0: Direct upgrade supported; run the compatibility tests in the migration playbook.

Migration plan and checklist (recommended approach)

Ownership: product -> release manager; eng-platform -> rollout; eng-serving-runtime -> runtime compatibility; customer-success -> customer comms.

Phases:
1) Preparation (2 weeks before canary)
- Identify tenants for staged rollout; prefer 5–10% of traffic slice for initial canary.
- Verify that the customer has telemetry-forwarding >= 99% and healthchecks for /v1/health of local-prefetch proxies.
- Run preflight simulator: curl -X POST /optimize/v4/simulate -d '{"traffic_profile":"tenant-sample"}' and confirm cost_estimate delta.

2) Canary (1 week)
- Deploy Optimize Conductor 4.0 to a single region and enable only non-critical tenants.
- Monitor p50/p95 latency, KV miss rate, policy decision error rates, and fidelity negotiation failures.
- Keep compatibility shim active for any SDKs hitting /v3.

3) Gradual rollout (2–6 weeks)
- Increase traffic in doubling increments (10% -> 20% -> 40% -> 80% -> 100%), waiting for stable telemetry after each step (minimum 24 hours).
- Validate cost and quality metrics against baseline.

4) Post-rollout verification (2 weeks)
- Run fidelity regression suites (PRD test harness) and collect customer-reported regressions.
- Disable compatibility shim after confirming zero critical regressions for 14 days.

Migration checklist (detailed)

- [ ] Run preflight simulation and capture cost_estimate baseline.
- [ ] Ensure customers have updated SDKs supporting v4 or confirm compatibility fallback is acceptable.
- [ ] Confirm telemetry schema v3 ingestion is enabled for the tenant.
- [ ] Validate KMS/HSM policies for any encrypted KV prefetch state.
- [ ] Coordinate canary window with customer success for high-value accounts.
- [ ] Record rollback points (cluster snapshots, config versions).

API changes and examples

New endpoints (examples):
- POST /optimize/v4/policies
  payload: {"tenant_id":"t-123","policy":{"fidelity_target":"balanced","batch_budget_ms":60}}
- POST /optimize/v4/migrate
  payload: {"tenant_id":"t-123","target_version":"4.0","dry_run":true}
- POST /optimize/v4/simulate
  payload: {"traffic_profile":"conversational-heavy","seed":42}

Sample migration CLI (internal):
- rwdctl optimize migrate --tenant t-123 --target 4.0 --dry-run

Console changes and operator guidance

- New migration dashboard: shows per-tenant cost delta, fidelity regression flags, and a staged rollout controller.
- Operators should use the simulator to sanity-check policy updates before committing to tenant production.

Observability and telemetry details

Telemetry schema v3 highlights: new fields
- cost_estimate (float): in USD per 1000 tokens estimated by optimizer
- cost_adjuster_id (string): id of the cost normalization rule applied
- fidelity_decision_id (string): cross-reference to Fidelity Advisor decision traces

Recommended dashboards and alerts
- Dashboards: Optimize Conductor 4.0 -> Per-tenant cost trends, Batch utilization heatmap, Fidelity decision trace viewer.
- Alerts (examples):
  - fidelity.negotiation.failures > 1% in 5m -> Sev2 (owner: eng-serving-runtime)
  - kv.miss_rate increase > 2x baseline in 10m -> Sev2 (owner: eng-platform)
  - telemetry.ingestion.failures > 0.1% in 15m -> Sev1 (owner: eng-sre)

Quality and evaluation guidance

- Run the packaged regression harness: tests/regression/optimize_v4/ which includes synthetic traffic shapes: conversational-heavy, short-prompt-burst, embedding-only, mixed-transactional.
- Evaluation metrics to track: response_consistency, hallucination_rate (if available), latency_p95, per_token_cost.

Known issues and limitations

- During heavy partitioning events the hybrid KV-prefetch coordinator may temporarily increase tail latency by up to 40% until evictions stabilize. Workaround: toggle prefetch:fallback_to_local = true.
- Some edge model variants with custom CUDA kernels may not yet benefit from kernel-aware scheduling; consult the compatibility matrix.
- Console migration dashboard can display stale cost deltas for tenants with infrequent traffic; use the simulate endpoint for accurate dry runs.

Rollback plan

- If p95 latency or fidelity regressions exceed defined thresholds during canary:
  1) Pause rollout and revert policy updates via /optimize/v4/policies rollback API.
  2) If regression persists, scale back to previous conductor image using cluster snapshot and disable multi-tenant optimizer feature flag.
  3) Notify customer-success and schedule a hotfix window.

Security and compliance notes

- Conductor 4.0 requires that any prefetch cache state persisted to disk is encrypted with customer KMS keys for customers with restricted confidentiality settings.
- Audit logging: all fidelity negotiation decisions are written to the audit log stream with retention consistent with customer's compliance tier.

Customer communication and enablement

- Outbound comms: send migration playbook and preflight checklist to customers 10 business days before planned migration.
- Include an optional 30-minute technical review call for enterprise customers during canary.

Appendix A: Backwards compatibility shim behavior

- The compat shim translates /optimize/v3 semantics to v4 with the following rules:
  - Legacy batch_target_ms -> batch_budget_ms mapping with normalization factor 0.8.
  - Explicitly disables kernel-aware scheduling for shimmed requests to preserve latency characteristics.
  - Returns a deprecation header: X-Optimize-Deprecation: v3-compat; replacement: /optimize/v4

Appendix B: Telemetry migration sample

- Example event (schema v3):
  {
    "timestamp":"2028-09-15T14:32:05Z",
    "tenant_id":"t-123",
    "route":"/v1/generate",
    "cost_estimate":0.0024,
    "fidelity_decision_id":"fd-789",
    "batch_id":"b-456"
  }

Contacts and ownership

- Release owner: Priya Ramakrishnan (product)
- Runtime compatibility: Anika Patel (eng-serving-runtime)
- Rollout and infra: Marcus Liu (eng-platform)
- Customer enablement: Diego Alvarez (customer-success)

Document history

- 2028-09-15: Draft created by Priya Ramakrishnan
- 2028-09-18: Internal review and expanded migration checklist (reviewers: Diego, Maya)
- 2028-09-20: Published after resolving compatibility shim behavior notes
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_0f05d12854974e1e8ab599b93cf46efe` — Canary Scheduler: Cost-Aware Deployment & Rollback Design Spec
2. `dsid_39628c72e38a452689606754ee5616de` — Model Promotion: Canary, Chaos and Load Validation Protocol
3. `dsid_40eb3865fec54d00acf0d86f192151a5` — Mixed-workload scheduler prototype — rollout runbook
4. `dsid_2ce26a1937a3405d9d041a48bddf3a61` — Canary kernel deployment patterns and health matrix
5. `dsid_5267cd82c772437fa0f9dd9e9568388b` — Hosted rollouts: SLO metrics and alerts (cohort-specific)
6. `dsid_037af0f9e58844e78a524f4a0fe969a9` — Canary GPU workload federation and IaC promotion pipeline
7. `dsid_53c73fdd8e1c4156af355c91f69f1cc6` — Quality Gates and Observability Contract for Feature Rollouts
8. `dsid_e757a2d8d46340cd8805e1f6a04247a6` — Runtime Operational Tuning and Triage Playbook
9. `dsid_5d54ce4fb8dd4774be03775516f1c8bb` — SLO deployment gates and capacity safety net
10. `dsid_5fc7774b86ff4d6f92c40a2bb5ac8b89` — Change-Immune Deploy Patterns for LLM Inference Runtime

### Fill for this row (also include in final JSON array)

```
row_id: 41
question_id: qst_0234::semantic
corpus_scale_size: 100000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 42

- **row_id:** `42`
- **question_id:** `qst_0238::semantic`
- **corpus_scale_size:** `15000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

How should I structure a small prompt experiment to reduce overconfident mistakes by mixing a couple of correct examples with one intentionally wrong example plus an immediate fix, while keeping the total examples very short and tracking things like made-up details and format compliance over a few hundred test prompts?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_e528bed025b44f71bc37a54f5a9aefcd`
_source: full_erb_file:dsid_e528bed025b44f71bc37a54f5a9aefcd__template-contrapositives-workbench.txt_

```text
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
5) Negative-control: 2 positive + 1 contrapositive but no correction (to test harm vs. benefit)

Sample few-shot set (working draft) — use for classification / short answer tasks:
---
Instruction: "Summarize the email below in 2 sentences for a senior manager."
Example A (good):
Email: "Q2 numbers beat forecast; need headcount next quarter; see attached table."
Summary: "Q2 exceeded forecast. Request for additional headcount next quarter; details in attached table."

Example B (good):
Email: "Customer reports recurrent API timeout when payload > 10k; repro steps attached."
Summary: "Customer sees timeouts on large payloads; repro steps attached for investigation."

Example C (contrapositive):
Email: "We had a minor display issue on Tuesday; fixed by front-end patch."
Summary: "The product is totally broken and unusable."
Why it's bad: "Overstates severity; misrepresents fix state."
Corrected (immediately after):
Summary: "Display issue observed Tuesday; front-end patch deployed to resolve the problem."
---
Notes: ordering matters — correction should immediately follow contrapositive so the model learns the contrast.

Failure probes (starter list):
- Under-specified numeric boundaries ("Filter users with high churn") where model invents threshold.
- Policy edge: ask for content transformation that skirts moderation (paraphrase a borderline prompt).
- Role confusion: short role labels that could be misinterpreted ("As a legal advisor, say X").

Observed heuristics so far (scratch observations):
- When contrapositive example uses strong negation words ("totally broken"), the model tends to adopt the polarity if correction is absent.
- Short critiques ("Incorrect: overclaims") are more effective than long rationales — keep them terse.
- Putting contrapositive at start vs middle: start makes the model overly cautious; middle achieves better calibration in preliminary runs.

Edge-case safety checks:
- Ensure contrapositive examples do not themselves include disallowed content (e.g., violent or hateful phrasing) — craft sanitised faux-errors.
- Check for adversarial amplification: contrapositive should never be the longest example.

Logging / evaluation plan:
- Run 200 probes per experimental condition across 6 probe types.
- Metrics: semantic accuracy (human-labeled), overclaim rate (model asserts facts not in input), style/length compliance, calibration (model confidence if available), token cost delta.
- Tag runs in Datadog / metrics backend with experiment key: cf:contrap-workbench-2025-07

Implementation notes (quick ops checklist):
- Use hosted-api small-medium model first (cheaper) before scaling to higher-capacity variants.
- Warm-up cache by running 20 benign prompts to stabilize latency.
- Save few-shot templates as templating JSON entries in repo: templating/fewshots/contrap_v1.json (PR reference above).

Open questions / TODOs (short list):
- How many contrapositive examples are optimal before diminishing returns? (1 vs 2)
- Does the approach transfer to multi-turn dialog (yes/no?) — need to test with conversation context preserved.
- Should critiques be free text or a constrained label set ("overclaim", "format error", "tone mismatch") for better model understanding?
- Test on long-form generation tasks (summaries > 200 tokens) — do contrapositives still help?

Next actions (this week):
- Ethan: wire up batch experiment harness and add probes from the 'policy-edge' folder (INFR-4213).
- Maya: craft 10 sanitized contrapositive exemplars for each probe type and add to repo.
- Me (Sofia): run initial 800-query sweep and collect manual labels for 120 samples.

Random notes to self:
- Try variant where critique is encoded as a short tag after the example — "[bad:overclaim]" — might be easier for models to latch onto.
- Consider combining with temperature scheduling: contrapositive+low-temp might reduce hallucination more than either alone.
- If we see regression on style, fall back to A/B rollback logic in console (canary).

Appendix: short list of sample contrapositive templates to copy/paste when building few-shot sets:
- "Incorrect: exaggerates findings; should not change numeric claims."
- "Incorrect: changes the requested format (must be 3 bullets)."
- "Incorrect: introduces unsupported assumptions about the customer."
- "Incorrect: translates but alters sentiment (should be neutral)."

End of draft. Notes deliberately terse; this is a working notebook. Will iterate after first run and record concrete numbers.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_92f56ed27b75455f82f43528f6644f3c` — Shot Blending Heuristics — personal scratchpad
2. `dsid_58396d0a09aa421bbab72f67e955ad23` — Latent Prompt Variables Scratchbook
3. `dsid_032a9f67deb945a0a432e9b75785f422` — Leftover Prompt Curio Cabinet — hunches & micro-experiments
4. `dsid_455031f4831d48feb5d44d543223101f` — Ensemble Prompt Templates Bank
5. `dsid_bf8681ce9427455299245cb2ee67b4a0` — Prompt chaining — error catalog & quick experiments
6. `dsid_7a25e9b6949b4b7da4f050661f626990` — Shot sentinel sneeze test notes
7. `dsid_3d49b09649b941e5998967200b834bea` — Microinstruction Misalignment — fieldnotes and quick experiments
8. `dsid_0f3b9705709c4c949ec53ae2f3d27190` — Macroshot template garden — few-shot and failure probes (scratchpad)
9. `dsid_302e42b1c5be42519f7933c3dd8b9e8f` — Counterfactual prompt probe notes
10. `dsid_f702ebb6e5cd4a8aa92d9b030723b2eb` — Anchorless exemplar curation log

### Fill for this row (also include in final JSON array)

```
row_id: 42
question_id: qst_0238::semantic
corpus_scale_size: 15000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 43

- **row_id:** `43`
- **question_id:** `qst_0239::semantic`
- **corpus_scale_size:** `20000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For the fintech prospect doing merchant reconciliation and dispute handling, what are the specific compliance items their ops and security teams said must be in place before moving past the pilot phase?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_ef492479c7dc4a3c9dd55d6771e5df54`
_source: full_erb_file:dsid_ef492479c7dc4a3c9dd55d6771e5df54__company-saltbloom-payments.txt_

```text
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
Send SOC2 + SSO FAQ and hosted security brief; schedule 30m technical demo week of 2026-03-15
SOC2 evidence needed
Decision deferred pending pricing cap
VPC evaluation for later stage
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_c87bda7c87f4438596851c844134e017` — Northbridge Banking
2. `dsid_4dc77de6649d4e0799648a18290d96b5` — BlueCrest Secure Support
3. `dsid_6db818ee43a94ad88882c91a3fe40491` — Axion Guard
4. `dsid_9019af805aa04f7394fb350b6eb679ae` — Silverbloom Contact Ops
5. `dsid_64470f7c6b15433c9f67cc78b51b16fc` — Lakeview Credit Union
6. `dsid_60903cb34ddb4fae9b5ea1830dae1437` — FuseWave Payments
7. `dsid_780679d5c13d42e5938af847beed38bf` — CloverStripe Fintech
8. `dsid_1df44244f57144619f742ec2e7dfd87d` — Peregrine DataWorks
9. `dsid_f4fbc3f2bcc24bb29f9da2c81e43661f` — Nimbus Compliance Labs
10. `dsid_da8b915c58a74bce8ccb88cd9b05d346` — Beacon Health Payments

### Fill for this row (also include in final JSON array)

```
row_id: 43
question_id: qst_0239::semantic
corpus_scale_size: 20000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 44

- **row_id:** `44`
- **question_id:** `qst_0240::semantic`
- **corpus_scale_size:** `40000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

During a multi region switchover, what is causing some customers to get bursty too many requests and occasional service unavailable responses because different parts of the traffic gatekeeper disagree briefly on the time boundary used for quota calculations?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_5402831508734a51adf649603be4b075`
_source: full_erb_file:dsid_5402831508734a51adf649603be4b075__ENG-158239-rate-policy-jitter-causing-tenant-capacity-starvation.txt_

```text
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
2026-03-08: Small hotfix deployed on hosted to introduce 250ms guard window; reduced severity but did not resolve root cause.
2026-03-10: Added additional logging and correlation IDs across proxy->orchestrator->host rate controllers to capture exact decision timelines.
Race between epoch transitions and policy cache refresh. When a region failover or orchestrator restart occurs, different components evaluate burst policies against inconsistent epoch anchors. The evaluator treats missing/old anchors as 'no-burst' and aggressively evicts inflight capacity rather than deferring or reconciling, resulting in tenant capacity starvation.
1) Rollout guard-window (250-500ms) at proxy and orchestrator to ignore epoch flips for immediate decisions (deployed to hosted; pending dedicated/private rollout),
2) Enable diagnostic sampling for affected tenants to capture full decision traces for postmortem
3) Communicate to CS about temporary throttle behavior and mitigation timeline
A) Implement atomic epoched policy reads: annotate policy cache entries with epoch_id and ensure any admission decision reads a consistent epoch across proxy+orchestrator+host
B) Add idempotent burst-claim reconciliation: when epoch mismatch is detected, reconcile by computing conservative merged credit (min of claims) and schedule background rebalancing instead of immediate eviction
C) Introduce a degraded-mode path that favors availability for previously healthy tenants (soft-degrade) during control-plane transitions
D) Add cross-component integration tests and chaos test that exercises orchestrator/proxy restarts with high-concurrency workloads
Unit + integration tests that validate epoch-aligned policy reads
Chaos test in staging that shows no more than 5% extra rejections for affected tenants during simulated failover
Metric reductions: burst_claim_mismatch rate decreases by 95% in staging failover runs
Documentation updated for Dedicated + Private deployment runbooks
Release notes and customer communication prepared for runtime-2.4
1) Create tiny persistence field epoch_id on policy cache entries and plumb through RPCs (ENG-158240 will track RPC changes)
2) Implement conservative reconciliation algorithm in orchestrator admission path (PR: github.com/redwood-inference/runtime/pull/7852)
3) Expand guard-window to 500ms with feature flag, roll out to dedicated and private with staged canaries
4) Add end-to-end tests in policy-e2e harness; run against chaos monkey
5) Post-deploy telemetry check and 24h on-call monitoring window
2026-03-03 — Maya Chen: Customer call summarized impact; asked for hotfix + timeline. Luis assigned to lead investigation.
2026-03-04 — Luis Alvarez: Reproduced in staging; opening follow-up tickets for RPC and cache versioning.
2026-03-08 — Priya Nair (SRE): Deployed 250ms guard-window on hosted; saw immediate reduction in customer escalations. Need rollout checklist for Dedicated.
2026-03-10 — Kane Patel (Security): Verified no sensitive telemetry left in logs; ok for Private customers after redaction.
2026-03-12 — Luis Alvarez: Draft PR ready, running policy-e2e locally. Planning canary deploy next Tuesday.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_cc4c5c2310714fd99962514beac82e74` — Burst reservation failover triggers degraded P99 throughput and imbalanced batching for dedicated tenant
2. `dsid_ad148b222d31473f8a3d279d679935eb` — INC-2025-0303 Postmortem: Dedicated autoscaler lag + quota ceiling caused sustained throttling
3. `dsid_4507a4e9254b4dd8b5a6d122ab69266d` — Misleading console quota reset after subaccount merge leading to opaque 429s
4. `dsid_141107a294da437e8c6d0ae9aa25bd03` — DST rollover induced quota-refill drift causing soft 429s across geo-edge pools
5. `dsid_f5e17784eba547afad5f09a3287ced08` — Automatic model-fallback causes duplicated quota accounting and transient 429s
6. `dsid_e20aa4d066d14bcdbc90be241cbf8d04` — Tenant overspill causes synchronous fallback and throttled bursts during regional surge
7. `dsid_287214114f8c44778b323430e70eef90` — Intermittent p95/p99 latency spikes when region-pinned traffic falls back to out-of-region egress
8. `dsid_e9e9646d70df41e1813bf84634906671` — Regional affinity routing behavior during capacity surge and pin-unavailable fallthrough
9. `dsid_595af30d9c194f8ea1a068a39dd9cedd` — Proactive congestion-island detection and sticky-region guardrails
10. `dsid_f3bfa55dffa442ef834731b7596981c1` — Clarify burst-window vs sustained-rate delta policy causing intermittent 429s for many short parallel requests

### Fill for this row (also include in final JSON array)

```
row_id: 44
question_id: qst_0240::semantic
corpus_scale_size: 40000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 45

- **row_id:** `45`
- **question_id:** `qst_0240::semantic`
- **corpus_scale_size:** `75000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

During a multi region switchover, what is causing some customers to get bursty too many requests and occasional service unavailable responses because different parts of the traffic gatekeeper disagree briefly on the time boundary used for quota calculations?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_5402831508734a51adf649603be4b075`
_source: full_erb_file:dsid_5402831508734a51adf649603be4b075__ENG-158239-rate-policy-jitter-causing-tenant-capacity-starvation.txt_

```text
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
2026-03-08: Small hotfix deployed on hosted to introduce 250ms guard window; reduced severity but did not resolve root cause.
2026-03-10: Added additional logging and correlation IDs across proxy->orchestrator->host rate controllers to capture exact decision timelines.
Race between epoch transitions and policy cache refresh. When a region failover or orchestrator restart occurs, different components evaluate burst policies against inconsistent epoch anchors. The evaluator treats missing/old anchors as 'no-burst' and aggressively evicts inflight capacity rather than deferring or reconciling, resulting in tenant capacity starvation.
1) Rollout guard-window (250-500ms) at proxy and orchestrator to ignore epoch flips for immediate decisions (deployed to hosted; pending dedicated/private rollout),
2) Enable diagnostic sampling for affected tenants to capture full decision traces for postmortem
3) Communicate to CS about temporary throttle behavior and mitigation timeline
A) Implement atomic epoched policy reads: annotate policy cache entries with epoch_id and ensure any admission decision reads a consistent epoch across proxy+orchestrator+host
B) Add idempotent burst-claim reconciliation: when epoch mismatch is detected, reconcile by computing conservative merged credit (min of claims) and schedule background rebalancing instead of immediate eviction
C) Introduce a degraded-mode path that favors availability for previously healthy tenants (soft-degrade) during control-plane transitions
D) Add cross-component integration tests and chaos test that exercises orchestrator/proxy restarts with high-concurrency workloads
Unit + integration tests that validate epoch-aligned policy reads
Chaos test in staging that shows no more than 5% extra rejections for affected tenants during simulated failover
Metric reductions: burst_claim_mismatch rate decreases by 95% in staging failover runs
Documentation updated for Dedicated + Private deployment runbooks
Release notes and customer communication prepared for runtime-2.4
1) Create tiny persistence field epoch_id on policy cache entries and plumb through RPCs (ENG-158240 will track RPC changes)
2) Implement conservative reconciliation algorithm in orchestrator admission path (PR: github.com/redwood-inference/runtime/pull/7852)
3) Expand guard-window to 500ms with feature flag, roll out to dedicated and private with staged canaries
4) Add end-to-end tests in policy-e2e harness; run against chaos monkey
5) Post-deploy telemetry check and 24h on-call monitoring window
2026-03-03 — Maya Chen: Customer call summarized impact; asked for hotfix + timeline. Luis assigned to lead investigation.
2026-03-04 — Luis Alvarez: Reproduced in staging; opening follow-up tickets for RPC and cache versioning.
2026-03-08 — Priya Nair (SRE): Deployed 250ms guard-window on hosted; saw immediate reduction in customer escalations. Need rollout checklist for Dedicated.
2026-03-10 — Kane Patel (Security): Verified no sensitive telemetry left in logs; ok for Private customers after redaction.
2026-03-12 — Luis Alvarez: Draft PR ready, running policy-e2e locally. Planning canary deploy next Tuesday.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_31059f73d2d2409488178447167534e6` — Burst allocation timebase drift during Private->Dedicated switchover causing opaque throttles
2. `dsid_e20aa4d066d14bcdbc90be241cbf8d04` — Tenant overspill causes synchronous fallback and throttled bursts during regional surge
3. `dsid_595af30d9c194f8ea1a068a39dd9cedd` — Proactive congestion-island detection and sticky-region guardrails
4. `dsid_2cc1acdfe064404eaa81e75adeeb4a7d` — Autoscaler threshold sensitivity causing small-tenant preemption and reserved-pool shortfalls
5. `dsid_b78b3f805e5744408c1b64e9cfc0c395` — Unexpected region cycling triggered a fallback wave leading to high-latency and model variant overload — postmortem
6. `dsid_e5a1cfad51b14cc39727fd1ca235b9cd` — Investigate burst policy fan-out mismatch causing cross-tenant throttles
7. `dsid_eb500d00dfb34dbc80c551f107f59b33` — Adaptive burst smoothing and quota-enforcement failover
8. `dsid_fc34f401b1724cac87b02b53c49b14e9` — hybrid-routing-quota-drift-silent-rejections
9. `dsid_e28c2b76f9ae43bdb6e809f2acf37930` — Region failover sequencing bug and priority shed policy consolidation
10. `dsid_3b4b3f6a33fa42beb71c55e6550fd2cd` — Backpressure amplification from sticky auth lease retries caused regional 429 wave

### Fill for this row (also include in final JSON array)

```
row_id: 45
question_id: qst_0240::semantic
corpus_scale_size: 75000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 46

- **row_id:** `46`
- **question_id:** `qst_0242::semantic`
- **corpus_scale_size:** `10000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the partner integration call about getting a third party AI service into another companys cloud catalog, what date did the security lead target for completing the pre publication image security smoke test?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_3fc14ed9048e4e1f861e0632b06fc39b`
_source: full_erb_file:dsid_3fc14ed9048e4e1f861e0632b06fc39b__2025-03-11-halotech-marketplace-ref-arch-integration-sync.txt_

```text
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
[00:48] Marcus (Redwood SE): Good question. We support both patterns. For hosted SaaS we can emit metering events to the marketplace platform; we also can provide a SaaS connector that calls the marketplace metering API. For AMI/private deployments we usually recommend a license key + periodic heartbeat to our license server (or a passive offline entitlements file for air-gapped). There's tradeoffs on support and latency of enforcement.
[01:05] Liam (HaloTech Security): Quick security callout — if we're doing a managed deployment that touches customer data in their VPC we need to vet KMS usage, key policies, and audit logs. Also need a statement on where logs land and retention. Do you have SOC2 docs?
[01:20] Sophie (Redwood Product): Yes, we have a SOC2 report and an infra attestation — we'll share a redacted excerpt. We also support customer-managed KMS; Redwood Dedicated and Private deployments can be configured to use the customer's KMS/HSM. We'll add a section to the ref-arch about CMEK usage and IAM roles required.
[01:36] Rosa (HaloTech PM): On listing requirements — AWS marketplace (and our private marketplace) require screenshots, a listing description, deployment instructions, a security questionnaire, and a pricing/metering plan. We'll need an AMI or a container image location plus a terraform example that installs networking and LB.
[01:50] Marcus: We'll provide a minimal terraform module that sets up the Redwood node pool, an ALB, and VPC endpoints. Note, for performance we recommend GPU-backed instances for model inference; we'll include a sizing table in the ref-arch (g4dn/g5 equivalents).
[02:05] Daniel: Sizing table is important. Also, marketplace listings often want a 'reference deployment cost estimate' — do you have an expected cost per qps or per-100-token unit for the pre-configured flavors?
[02:17] Marcus: We'll prepare an example cost sheet with expected tokens per second and instance types. It's approximate — depends on model variant and sequence length. We'll call out quantized vs full-precision profiles.
[02:28] Priya: A couple of technical specifics: network path — do you require cross-account roles? Does Redwood need cross-account read access to KMS or will it assume a role in the customer account?
[02:40] Sophie: For Private deployments we recommend a cross-account IAM role that Redwood can assume for management operations; for deployments fully customer-managed, Redwood does not store keys — we use temporary credentials and customers retain full control of their KMS. We'll document both flows.
[02:55] Liam: Also need clarity on telemetry — what does Redwood send back to your control plane? Are we sending prompts, partial inputs, or only anonymized telemetry? Compliance team is concerned about PII leakage.
[03:08] Ava: Important: Redwood's hosted tier can be configured to forward minimal telemetry (only performance metrics, no payloads) or to forward sanitized prompts if customers opt in. For Dedicated / Private we provide a policy-driven telemetry toggle and local-only logging options for air-gapped installs. We'll put explicit fields in the ref-arch about data flow and redaction controls.
[03:28] Daniel: Great. Now on billing — HaloTech expects marketplace integrations to support automated entitlement checks. For SaaS listings, we use the marketplace metering API. For AMI listings, we prefer an entitlement token exchange during onboarding.
[03:41] Marcus: We'll map both: SaaS -> metering API; AMI -> license heartbeat + entitlement validation. We also support a marketplacelike integration where customers procure via HaloTech and receive an entitlement file that the deployment reads at boot.
[03:55] Rosa: Regarding the listing metadata — we need a short and long description, logos, and two deployment flavors (SaaS and BYO) flagged. Can Redwood provide marketing-friendly descriptions and a one-page reference architecture?
[04:09] Sophie: Yes, we'll produce a one-page ref-arch and a 3-slide partner blurb for the marketplace. We'll supply icons and recommended copy.
[04:18] Priya: Operational question: How do upgrades work for AMI/terraform deployments? We need a plan for in-place upgrades vs blue/green and migration steps for KV cache / model weights.
[04:29] Marcus: For AMI-based installs we provide upgrade playbooks. Models and weights can be stored on an EFS or S3 location and swapped by tag; we recommend blue/green for schema migrations. We'll add a step-by-step upgrade checklist to the runbook.
[04:43] Daniel: Competitors — we've seen DeepServe do a marketplace AMI with an automatic metering agent that phone-homes. How is Redwood different from that?
[04:51] Ava: Redwood's differentiation is a unified runtime and explicit observability for token-level costs; we give customers per-route latency/cost breakdowns and tooling for batching/caching so they can hit both cost and latency SLOs. We also support private deployments with customer-managed keys and explicit audit hooks.
[05:05] Liam: On audit — can you surface per-request logs for regulatory review, and do you support immutable audit logging?
[05:12] Marcus: We can stream audit events to the customer's destination (CloudWatch, GCS, or S3) and we support write-once retention policies on the storage side if the customer configures it. We'll document recommended retention windows and query recipes.
[05:25] Rosa: Marketplace also likes a reference customer story or at least an anonymized performance benchmark. Do you have any allowed collateral?
[05:33] Sophie: We can prepare an anonymized benchmark (tokens/sec, 95th-latency, cost/unit) for a typical generative workload. We'll keep company names redacted.
[05:41] Priya: Ok on the terraform module — we need a repo with an example that builds a vpc, subnets, security groups, an ASG or node pool with GPU nodes, and an ALB + target groups. Also startup userdata that registers the node with Redwood control plane.
[05:54] Marcus: We'll deliver that. The userdata will include a bootstrap that fetches an entitlement file (if BYO) or registers with the cloud control plane (if SaaS). We'll provide example env var names and a small config generator script.
[06:10] Daniel: Timeline — HaloTech wants the initial listing in two phases: Phase 1 (SaaS listing + marketing blurb) targeted by end of March; Phase 2 (AMI + terraform examples + private ref-arch) targeted mid-April. Are those dates realistic?
[06:23] Ava: Yes, with the owners aligned that's doable. We'll need docs from HaloTech (listing template, logo assets) and the terraform repo from Priya to hit mid-April.
[06:31] Rosa: Also legal: our marketplace requires a marketplace addendum to the commercial contract that covers billing, refunds, and data responsibilities. Who owns the legal packaging?
[06:40] Ava: Our legal team will work with HaloTech legal. Sophie, I'll loop in our contracts lead and we'll propose the marketplace addendum. We'll flag any SKU/pricing constraints.
[06:50] Liam: For compliance gating, we'll expect SOC2 report and MAA for the image. We'll also run a smoke security test on the AMI. Is that OK?
[06:57] Marcus: Absolutely — we can provide the SOC2 excerpt and we'll coordinate a security QA window for the AMI. We'll also provide hardening guidelines for the AMI images.
[07:10] (brief cross-talk; someone dropped and rejoined, minor audio fuzz)
[07:28] Ava: I'm going to do a quick recap so we have a clear list of owners. 1) Redwood shares the marketplace listing template + example copy + icons (Ava) by 2025-03-14. 2) Redwood provides the terraform module + ref-arch diagrams + upgrade runbook (Marcus) by 2025-03-18. 3) HaloTech shares the marketplace template, logo assets, and internal listing requirements (Rosa/Daniel) by 2025-03-13. 4) HaloTech to provide terraform module repo access or a link to their marketplace deployer (Priya) by 2025-03-18. 5) Security artifacts: Redwood to send SOC2 excerpt and attestation (Sophie) by 2025-03-14; HaloTech to run AMI security QA (Liam) target 2025-03-24.
[07:58] Daniel: That matches our notes. One ask — can Redwood supply a 1-hour demo for our marketplace ops team to show how entitlements and metering appear on your console?
[08:08] Ava: Yes — we'll schedule a dedicated demo with the ops team; I'll propose slots next week.
[08:13] Priya: And billing — we need a follow-up with finance to map metering events to HaloTech billing lines. Let's schedule that in the week of 3/24.
[08:22] Marcus: We'll prepare a sample metering event payload and a short spec doc for the metering integration.
[08:28] Rosa: Any blockers from Redwood side?
[08:31] Ava: None immediate; biggest dependency is getting the terraform example validated in a HaloTech environment. Priya, if you can share access or a reproducible sandbox that helps.
[08:40] Priya: Will do. I'll create a repo entry and invite Marcus.
[08:44] (brief silence)
[08:47] Ava: Ok last few quick clarifications — does HaloTech support private listings for individual customers behind a private catalog?
[08:53] Rosa: Yes, we do private/whitelisted listings. We just need to mark the listing and attach entitlements properly.
[08:59] Liam: For audit, please include sample field names we'll use in our SIEM ingestion so we can map them to our retention rules.
[09:06] Marcus: We'll include a mapping of event names and schemas as part of the ref-arch doc bundle.
[09:12] Daniel: Great. If there are no more questions, let's recap next steps and owners.
[09:18] Ava: Thanks everyone — we will follow up with the artifacts and a proposed demo slot. Expect the draft listing and SOC2 snippet by 2025-03-14.
[09:26] Daniel: Thanks all. Meeting adjourned.

Auto-generated action digest (may be noisy):
- Redwood: share listing template, icons, copy (Ava) by 2025-03-14
- Redwood: terraform module + ref-arch + runbook (Marcus) by 2025-03-18
- HaloTech: provide marketplace template + assets (Rosa) by 2025-03-13
- HaloTech: invite Redwood to sandbox / repo (Priya) by 2025-03-18
- Redwood: SOC2 excerpt and compliance artifacts (Sophie) by 2025-03-14
- HaloTech: AMI security QA window (Liam) target 2025-03-24

End transcript.
Ava Patel - share AWS marketplace checklist and sample listing (due 2025-03-14)
Marcus Lee - export reference architecture diagrams and step-by-step deployment runbook (due 2025-03-18)
Priya Malhotra - send HaloTech terraform module repo link and AMI manifest (due 2025-03-18)
Liam O'Neill - provide SOC2 report excerpt and KMS/HSM attestation (due 2025-03-20)
Redwood to share draft AWS marketplace listing template by 2025-03-14
HaloTech to provide terraform module and AMI details by 2025-03-18
Schedule follow-up billing/integration call with finance (week of 2025-03-24)
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_544c8acb021e44179a154dc218df4d0d` — partnerships
2. `dsid_521ceaa63b844d85940cd637e799da97` — partnerships
3. `dsid_73f4e1dea88c4fc1a39af9720187bfc3` — partnerships
4. `dsid_5aff2c70fbb447a6bd58dfc7e7f72688` — Galena Archive Solutions
5. `dsid_f23926802cf44ae4b85c4410682eab90` — partnerships
6. `dsid_b7f8adc1e56749938ac0fe666319bd33` — Briarwood Network Dynamics
7. `dsid_157aeecf95f543329978debd0f4164e8` — Pegasus VPC Solutions
8. `dsid_4aa62974759543e8b27eaa9d940e2ae3` — BlueHarbor Compliance AI
9. `dsid_03a61b2b31094c4d909de520ac49e75f` — Grenadier Regulated EdgeWorks
10. `dsid_3c18e45fbc064bdeb056d94d621846f2` — partnerships

### Fill for this row (also include in final JSON array)

```
row_id: 46
question_id: qst_0242::semantic
corpus_scale_size: 10000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 47

- **row_id:** `47`
- **question_id:** `qst_0251::semantic`
- **corpus_scale_size:** `15000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`
_source: full_erb_file:dsid_a15c0247e9de4e128293bd820fc4c659__company-pearlgate-embedlabs.txt_

```text
PearlGate Embed Labs

CRM snippets + rep notes. Mid-market SaaS, product team building a contextual search layer for their docs + support chat. Current stack: Postgres for metadata, S3 for raw docs, they plan to use Pinecone (trial) but open to integrating Redwood's routing + batch embed generation. Key ask: reliable nightly batch job (5M documents/month, incremental delta) + on-demand embeddings for user queries. Throughput targets: embedding throughput ~400 qps peak during batch windows (they plan parallel workers), semantic search end-to-end latency target <150ms for top-10 retrieval + re-rank. Cost-sensitive: prefer a Dedicated committed capacity plan if unit economics beat hosted at scale. Want clear per-route token cost breakdowns in Console. Security: SOC2 required, SSO/SAML for engineering/admins, KMS for key management, audit logs retained 1 year (customer-facing compliance). Data residency: majority NA but 15% EU customers — asks whether Dedicated can pin region or require VPC peering to EU region. Model preferences: Open Llama-style quantized variants for cost, but want Redwood-verified performance profile before committing. 
2025-10-07: Intro call (AE Sofia) — product overview, quick fit (embeddings + semantic search)
2025-11-12: Hosted API demo — evaluated streaming vs batch endpoints, initial latency numbers using small dataset
2026-01-20: Security call with infra (asked for SOC2 + SSO details, KMS options) — linked Drive FAQ
2026-02-08: Pricing and capacity conversation (requested committed nodes pricing vs pay-as-you-go)
2026-03-01: Architecture deep-dive with SE (Daniel) — ingestion pipeline, vector DB choices, batching strategy; agreed on POC scope
Run 2-week Dedicated POC (ingest + query load test), deliver sizing + 12-mo pricing
Legal DPA review (data residency clauses)
Procurement needs 3rd vendor quote
SRE needs load test script for nightly batch
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_9e5e6325ff084b08898293033de2d391` — Retina SearchWorks
2. `dsid_a6123856d857425bb7419ea99b49e265` — Pegatrix MassIndexers
3. `dsid_c663f74bce354012a30c0b95849b090a` — Lithic Code Archives
4. `dsid_4f571bb8e6574a93a4a65ca03f9ec89c` — Valorium Enterprise Retrieval
5. `dsid_a935e7827ac34cb49ba446eb24dcd055` — LucidGrove Answersphere
6. `dsid_e611d79c110248d9853fb40b4be0e216` — Pegasus Compass
7. `dsid_6bdbaca3a8d84301a2a4b920fdeca63b` — Cypress Bay Financial Knowledge Mesh
8. `dsid_065ec47b5af54db594c352e0e1dcaf1f` — Northwind Embark
9. `dsid_dfb4ae719e5643248dad81b2de5baa47` — Moonlit Concourse
10. `dsid_7c0f737b0560484796c1a9b012160af1` — Whitewater Vector Integrations

### Fill for this row (also include in final JSON array)

```
row_id: 47
question_id: qst_0251::semantic
corpus_scale_size: 15000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 48

- **row_id:** `48`
- **question_id:** `qst_0251::semantic`
- **corpus_scale_size:** `25000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`
_source: full_erb_file:dsid_a15c0247e9de4e128293bd820fc4c659__company-pearlgate-embedlabs.txt_

```text
PearlGate Embed Labs

CRM snippets + rep notes. Mid-market SaaS, product team building a contextual search layer for their docs + support chat. Current stack: Postgres for metadata, S3 for raw docs, they plan to use Pinecone (trial) but open to integrating Redwood's routing + batch embed generation. Key ask: reliable nightly batch job (5M documents/month, incremental delta) + on-demand embeddings for user queries. Throughput targets: embedding throughput ~400 qps peak during batch windows (they plan parallel workers), semantic search end-to-end latency target <150ms for top-10 retrieval + re-rank. Cost-sensitive: prefer a Dedicated committed capacity plan if unit economics beat hosted at scale. Want clear per-route token cost breakdowns in Console. Security: SOC2 required, SSO/SAML for engineering/admins, KMS for key management, audit logs retained 1 year (customer-facing compliance). Data residency: majority NA but 15% EU customers — asks whether Dedicated can pin region or require VPC peering to EU region. Model preferences: Open Llama-style quantized variants for cost, but want Redwood-verified performance profile before committing. 
2025-10-07: Intro call (AE Sofia) — product overview, quick fit (embeddings + semantic search)
2025-11-12: Hosted API demo — evaluated streaming vs batch endpoints, initial latency numbers using small dataset
2026-01-20: Security call with infra (asked for SOC2 + SSO details, KMS options) — linked Drive FAQ
2026-02-08: Pricing and capacity conversation (requested committed nodes pricing vs pay-as-you-go)
2026-03-01: Architecture deep-dive with SE (Daniel) — ingestion pipeline, vector DB choices, batching strategy; agreed on POC scope
Run 2-week Dedicated POC (ingest + query load test), deliver sizing + 12-mo pricing
Legal DPA review (data residency clauses)
Procurement needs 3rd vendor quote
SRE needs load test script for nightly batch
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_3388f6da93134707a1fb443e775eabc7` — Storied Searchworks
2. `dsid_751af885e0d8442a9b4e167b33ff7841` — Inkwell Answers
3. `dsid_9e5e6325ff084b08898293033de2d391` — Retina SearchWorks
4. `dsid_a6123856d857425bb7419ea99b49e265` — Pegatrix MassIndexers
5. `dsid_c663f74bce354012a30c0b95849b090a` — Lithic Code Archives
6. `dsid_4f571bb8e6574a93a4a65ca03f9ec89c` — Valorium Enterprise Retrieval
7. `dsid_c29508f784174459926dcfcf31a58b50` — Reverie Botsight
8. `dsid_a935e7827ac34cb49ba446eb24dcd055` — LucidGrove Answersphere
9. `dsid_5be817654250421db53ca7552b9a3d00` — FathomLine Support Intelligence
10. `dsid_e611d79c110248d9853fb40b4be0e216` — Pegasus Compass

### Fill for this row (also include in final JSON array)

```
row_id: 48
question_id: qst_0251::semantic
corpus_scale_size: 25000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 49

- **row_id:** `49`
- **question_id:** `qst_0251::semantic`
- **corpus_scale_size:** `100000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`unsure` mode=`other`

### Question

For a mid sized subscription software company adding AI powered lookup across internal docs and support chats, what are the performance targets for the overnight vectorization run and the interactive top ten results response time that were discussed in the pre sales notes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a15c0247e9de4e128293bd820fc4c659`
_source: full_erb_file:dsid_a15c0247e9de4e128293bd820fc4c659__company-pearlgate-embedlabs.txt_

```text
PearlGate Embed Labs

CRM snippets + rep notes. Mid-market SaaS, product team building a contextual search layer for their docs + support chat. Current stack: Postgres for metadata, S3 for raw docs, they plan to use Pinecone (trial) but open to integrating Redwood's routing + batch embed generation. Key ask: reliable nightly batch job (5M documents/month, incremental delta) + on-demand embeddings for user queries. Throughput targets: embedding throughput ~400 qps peak during batch windows (they plan parallel workers), semantic search end-to-end latency target <150ms for top-10 retrieval + re-rank. Cost-sensitive: prefer a Dedicated committed capacity plan if unit economics beat hosted at scale. Want clear per-route token cost breakdowns in Console. Security: SOC2 required, SSO/SAML for engineering/admins, KMS for key management, audit logs retained 1 year (customer-facing compliance). Data residency: majority NA but 15% EU customers — asks whether Dedicated can pin region or require VPC peering to EU region. Model preferences: Open Llama-style quantized variants for cost, but want Redwood-verified performance profile before committing. 
2025-10-07: Intro call (AE Sofia) — product overview, quick fit (embeddings + semantic search)
2025-11-12: Hosted API demo — evaluated streaming vs batch endpoints, initial latency numbers using small dataset
2026-01-20: Security call with infra (asked for SOC2 + SSO details, KMS options) — linked Drive FAQ
2026-02-08: Pricing and capacity conversation (requested committed nodes pricing vs pay-as-you-go)
2026-03-01: Architecture deep-dive with SE (Daniel) — ingestion pipeline, vector DB choices, batching strategy; agreed on POC scope
Run 2-week Dedicated POC (ingest + query load test), deliver sizing + 12-mo pricing
Legal DPA review (data residency clauses)
Procurement needs 3rd vendor quote
SRE needs load test script for nightly batch
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_3388f6da93134707a1fb443e775eabc7` — Storied Searchworks
2. `dsid_447b145145ac475da57a16ae41af5f0b` — AnchorBright Search
3. `dsid_7032728f84204589803d0ee2cc72ac84` — EchoQuarry SupportSearch
4. `dsid_c9afc162f3b04610a5edc3f68287972d` — Aquifer Lookup
5. `dsid_751af885e0d8442a9b4e167b33ff7841` — Inkwell Answers
6. `dsid_af63752ecdc44ba3a8ec5f8082ac3d89` — Midtown Retrieval Works
7. `dsid_dde0b07ea5fe4658b918743a264291ce` — Praxis Echelon
8. `dsid_5b4d475cf8ea46dba627b40368b1ac00` — LumenBridge CodexSearch
9. `dsid_9e5e6325ff084b08898293033de2d391` — Retina SearchWorks
10. `dsid_d350205a78c0485cafc26c52837a95b4` — Sentinel VectorWorks

### Fill for this row (also include in final JSON array)

```
row_id: 49
question_id: qst_0251::semantic
corpus_scale_size: 100000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 50

- **row_id:** `50`
- **question_id:** `qst_0252::semantic`
- **corpus_scale_size:** `15000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In our incident response process, what is the rule for when a quick time-boxed after-action review is acceptable instead of writing the full formal analysis, based on impact duration and whether the issue hit one customer versus many?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_01eaeaf6045941beaeaf74e6170aceea`
_source: full_erb_file:dsid_01eaeaf6045941beaeaf74e6170aceea__responder-rotation-synthesis-and-deferred-postmortem-protocol-2026.txt_

```text
Responder rotation synthesis and deferred postmortem protocol

Overview:\n\nThis playbook describes Redwood's responder rotation synthesis process and a lightweight Deferred Postmortem (DPM) protocol for incidents that meet defined criteria. It combines on-call scheduling practices, a structured bridge handoff procedure, and customer-facing messaging templates designed for speed and clarity. The goal is to reduce cognitive load during high-impact events and to ensure timely learning when full postmortems are not immediately practical.\n\nScope:\n- Applies to: SRE, Serving Runtime, Platform, and Incident Response stakeholders.\n- Excludes: low-priority alerts that resolve without human intervention (see 'Auto-resolved alerts' below).\n\nDefinitions:\n- Responder rotation synthesis: periodic review and rebalancing of on-call shifts, handoffs, and escalation ladders to maintain equitable load and coverage.\n- Deferred Postmortem (DPM): a time-boxed post-incident review that defers non-critical analysis until stakeholders are available, while still capturing root evidence and action items immediately.\n\nKey principles:\n1) Fast stabilization first: prioritize containment and customer impact minimization.\n2) Minimal friction handoffs: standardized bridge transfer reduces repeated context overhead.\n3) Continuous learning: short DPMs for low-severity incidents; full postmortems for Sev1/Sev2.\n4) Equity in rotations: no responder assigned >36 hours continuous duty without relief.\n\nOn-call rotation design (synthesis process):\n1. Quarterly synthesis review (owner: SRE lead):\n   - Pull the last quarter's on-call logs and pager counts.\n   - Calculate median and 95th percentile pager counts per responder.\n   - Identify top-10% busiest windows and common root causes.\n2. Rebalance rules:\n   - Move noisy services to a dedicated micro-rotation if they account for >25% of pages.\n   - Limit night-weekend primary duty to volunteers in the rotation unless emergency staffing required.\n3. Local fairness check (monthly):\n   - Team leads run a 15-minute review in the first week of each month to confirm schedule fairness and swap if needed.\n\nRotation constraints (config):\n| Constraint | Value | Rationale |\n|---|---:|---|\n| Max continuous on-call | 36h | Prevent fatigue and degraded decision-making |\n| Minimum handoff overlap | 15m | Time to summarize bridge state and outstanding actions |\n| Max weekly duty | 56h | Prevent single-responder overload across teams |\n| Handoff notes retention | 90d | Auditability and incident reconstruction |\n\nBridge handoff procedure (step-by-step):\n1) Pre-handoff checklist (outgoing):\n   - Summarize incident timeline, current hypotheses, mitigation steps in progress, and customer impact.\n   - Confirm runbook page(s) in Bridge tab are current and link to traces/log queries.\n2) Live handoff (over bridge):\n   - 5–15 minute verbal summary; ensure incoming acknowledges critical mitigations.\n   - If unresolved customer-impacting work remains, assign an owner and ETA.\n3) Post-handoff (incoming):\n   - Record a 1-line status in the incident timeline and attach a minimum evidence set (logs, traces, alert IDs).\n\nIncident lifecycle and DPM decision matrix:\n- If incident is Sev1 or multi-tenant Sev2 -> full postmortem required within 72 hours of remediation.\n- If incident meets ALL of the following, use DPM: single-tenant, <30 minutes customer-visible impact, known cause, effective mitigation applied at resolution.\n- Otherwise triage for full postmortem.\n\nDeferred Postmortem (DPM) protocol (when to use and how):\nPurpose: capture essential facts and actions quickly when resource constraints or ongoing high operational tempo would make a full postmortem impractical in 72 hours.\nDPM steps (owner: incident lead):\n1) Within 8 hours of incident resolution: populate DPM template with\n   - 1-line summary, impact window (start/end), services affected, severity, and customer impact.\n   - Evidence snapshot (link to logs, runbook used, mitigation commands).\n2) Create action items with clear owners and SLAs (default: 14-day action SLA).\n3) Flag DPM for follow-up in the next synthesis meeting.\n4) If DPM reveals systemic risk or unresolved unknowns, escalate to full postmortem.\n\nDPM template (minimum fields):\n- Title (1 line)\n- Date/time window\n- Affected services and teams (comma-separated)\n- Immediate mitigations executed\n- Evidence links (logs, traces, alert IDs)\n- Action items (owner | due date | description)\n- Decision to close DPM or escalate (yes/no)\n\nEscalation and timeline expectations:\n- Immediate: severity declaration and customer status update within 30 minutes of detection for Sev1/Sev2.\n- Short window: initial triage and bridge stand-up within 60 minutes.\n- DPM creation: within 8 hours.\n- Full postmortem: published within 72 hours for Sev1/Sev2.\n\nCustomer communications templates (for bridge operator use):\n- Initial status (first 30m):\n  \"We have identified an issue affecting [feature/service]. Our team has engaged and is investigating. We will provide an update within 30 minutes.\"\n\n- Follow-up status (post-triage):\n  \"Update: The issue is caused by [brief cause]. Mitigations underway include [actions]. Current impact: [scope]. Next update scheduled at [time/ETA].\"\n\n- Resolution notice:\n  \"Resolved: The issue affecting [service] has been mitigated at [time]. Root cause and next steps will be published in a follow-up note or postmortem.\"\n\n- SLA-credit preliminary message (if applicable):\n  \"We are assessing impact against our SLA commitments. If you are eligible, we will follow up with credit details once our postmortem is complete.\"\n\nGame day design and schedule (90-minute template):\n- Goal: validate handoff, DPM creation, and customer comms speed.\n- Attendees: 1 bridge operator, 2 responders, 1 product EM, 1 customer success observer.\n- Timeline:\n  00:00 — Inject alert and distribute pager\n  00:05 — Bridge up and first customer status sent\n  00:20 — Handoff simulation between responders\n  00:45 — DPM skeleton completed and action items assigned\n  01:05 — Demo of status page update flow and mock SLA notice\n  01:20 — 15-minute retro and lessons logged\n\nRunbook snippets (examples):\n- Quick KV-cache eviction (serving-runtime):\n  \"# Commands\n  kubectl exec -n runtime svc/cache-operator -- cache evict --pattern=*\n  # Verify: tail logs for 200 responses to health endpoint for 5m\"\n\n- Throttle mitigation (traffic spike):\n  \"1) Move non-critical traffic to burst_throttle=true route.\n   2) Increase instance headroom by policy 'scale-now' for model-serving service.\n   3) Notify customers via status page if >5% error rate persists after 5m.\"\n\nOwnership and metrics (who owns what):\n- On-call synthesis owner: SRE manager (quarterly cadence).\n- DPM governance: Incident review council (product + SRE rep)\n- Bridge operator: maintains status templates and runbook links.\n- Metrics to track: mean time to ack (MTTA), mean time to remediate (MTTR), percentage of incidents resolved with DPM, action-item closure rate within 14 days.\n\nAudit and retention:\n- DPMs and postmortems retained for 2 years in the incident archive.\n- Handoff notes retained for 90 days.\n\nRelated pages and references:\n- Link: /confluence/oncall-and-incident-response/incident-evidence-collection-standard (internal)\n- Link: /confluence/eng-sre/runbooks/kv-cache-eviction (internal)\n\nAppendix: triage decision quick chart:\n- High latency + multi-tenant -> Sev1 -> full postmortem\n- Short outage <30m + single-tenant + known fix -> DPM\n- Repeated flapping events -> escalate to hypothesis-driven postmortem\n\nRevision history:\n- 2026-01-12 — created by Priya Shah\n- 2026-02-02 — added DPM SLA guidance (review: Miguel Alvarez)\n- 2026-03-01 — formalized rotation constraints and game day template (review: Sara Kim)\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_d0f651d038ca44868cc31facb0331d84` — External outage chronicle and technical safeguards brief
2. `dsid_4f82a120ef1442fa9bd7189c9833e3ae` — emergency-comms-runbook-and-status-templates
3. `dsid_4c9c686c513a4946b335f17a8da911f1` — Oncall Hackbook: Fast Repair Patterns for API Stalls and Rate Surges
4. `dsid_b360d00be3f84b08b1a879d102835d2f` — Post-incident summary template (publishable)
5. `dsid_3b7139962b28486aaa3a498cb375b2a9` — Incident Orchestration Decision Canvas and Runbook
6. `dsid_aaf549b678034217953d420252250815` — Urgent service degradation — spokes notes and Q&A (standby)
7. `dsid_51877a563b0d4f42a63e33d7735913ff` — Responder Guidance and Simulation Labs with Templates
8. `dsid_c24658680cc94dcfb0a25ff8103ac916` — Incident brief and customer action plan — May 5 impact on inference latency
9. `dsid_8cc9488676c647e2a22ee8b8bc7e890a` — Critical Latency Fast-Recovery Playbook and On‑Call Toolkit
10. `dsid_9b4db0cb7a42489a91686818c91882a1` — Incident tactical brief & customer-facing templates

### Fill for this row (also include in final JSON array)

```
row_id: 50
question_id: qst_0252::semantic
corpus_scale_size: 15000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 51

- **row_id:** `51`
- **question_id:** `qst_0252::semantic`
- **corpus_scale_size:** `50000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In our incident response process, what is the rule for when a quick time-boxed after-action review is acceptable instead of writing the full formal analysis, based on impact duration and whether the issue hit one customer versus many?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_01eaeaf6045941beaeaf74e6170aceea`
_source: full_erb_file:dsid_01eaeaf6045941beaeaf74e6170aceea__responder-rotation-synthesis-and-deferred-postmortem-protocol-2026.txt_

```text
Responder rotation synthesis and deferred postmortem protocol

Overview:\n\nThis playbook describes Redwood's responder rotation synthesis process and a lightweight Deferred Postmortem (DPM) protocol for incidents that meet defined criteria. It combines on-call scheduling practices, a structured bridge handoff procedure, and customer-facing messaging templates designed for speed and clarity. The goal is to reduce cognitive load during high-impact events and to ensure timely learning when full postmortems are not immediately practical.\n\nScope:\n- Applies to: SRE, Serving Runtime, Platform, and Incident Response stakeholders.\n- Excludes: low-priority alerts that resolve without human intervention (see 'Auto-resolved alerts' below).\n\nDefinitions:\n- Responder rotation synthesis: periodic review and rebalancing of on-call shifts, handoffs, and escalation ladders to maintain equitable load and coverage.\n- Deferred Postmortem (DPM): a time-boxed post-incident review that defers non-critical analysis until stakeholders are available, while still capturing root evidence and action items immediately.\n\nKey principles:\n1) Fast stabilization first: prioritize containment and customer impact minimization.\n2) Minimal friction handoffs: standardized bridge transfer reduces repeated context overhead.\n3) Continuous learning: short DPMs for low-severity incidents; full postmortems for Sev1/Sev2.\n4) Equity in rotations: no responder assigned >36 hours continuous duty without relief.\n\nOn-call rotation design (synthesis process):\n1. Quarterly synthesis review (owner: SRE lead):\n   - Pull the last quarter's on-call logs and pager counts.\n   - Calculate median and 95th percentile pager counts per responder.\n   - Identify top-10% busiest windows and common root causes.\n2. Rebalance rules:\n   - Move noisy services to a dedicated micro-rotation if they account for >25% of pages.\n   - Limit night-weekend primary duty to volunteers in the rotation unless emergency staffing required.\n3. Local fairness check (monthly):\n   - Team leads run a 15-minute review in the first week of each month to confirm schedule fairness and swap if needed.\n\nRotation constraints (config):\n| Constraint | Value | Rationale |\n|---|---:|---|\n| Max continuous on-call | 36h | Prevent fatigue and degraded decision-making |\n| Minimum handoff overlap | 15m | Time to summarize bridge state and outstanding actions |\n| Max weekly duty | 56h | Prevent single-responder overload across teams |\n| Handoff notes retention | 90d | Auditability and incident reconstruction |\n\nBridge handoff procedure (step-by-step):\n1) Pre-handoff checklist (outgoing):\n   - Summarize incident timeline, current hypotheses, mitigation steps in progress, and customer impact.\n   - Confirm runbook page(s) in Bridge tab are current and link to traces/log queries.\n2) Live handoff (over bridge):\n   - 5–15 minute verbal summary; ensure incoming acknowledges critical mitigations.\n   - If unresolved customer-impacting work remains, assign an owner and ETA.\n3) Post-handoff (incoming):\n   - Record a 1-line status in the incident timeline and attach a minimum evidence set (logs, traces, alert IDs).\n\nIncident lifecycle and DPM decision matrix:\n- If incident is Sev1 or multi-tenant Sev2 -> full postmortem required within 72 hours of remediation.\n- If incident meets ALL of the following, use DPM: single-tenant, <30 minutes customer-visible impact, known cause, effective mitigation applied at resolution.\n- Otherwise triage for full postmortem.\n\nDeferred Postmortem (DPM) protocol (when to use and how):\nPurpose: capture essential facts and actions quickly when resource constraints or ongoing high operational tempo would make a full postmortem impractical in 72 hours.\nDPM steps (owner: incident lead):\n1) Within 8 hours of incident resolution: populate DPM template with\n   - 1-line summary, impact window (start/end), services affected, severity, and customer impact.\n   - Evidence snapshot (link to logs, runbook used, mitigation commands).\n2) Create action items with clear owners and SLAs (default: 14-day action SLA).\n3) Flag DPM for follow-up in the next synthesis meeting.\n4) If DPM reveals systemic risk or unresolved unknowns, escalate to full postmortem.\n\nDPM template (minimum fields):\n- Title (1 line)\n- Date/time window\n- Affected services and teams (comma-separated)\n- Immediate mitigations executed\n- Evidence links (logs, traces, alert IDs)\n- Action items (owner | due date | description)\n- Decision to close DPM or escalate (yes/no)\n\nEscalation and timeline expectations:\n- Immediate: severity declaration and customer status update within 30 minutes of detection for Sev1/Sev2.\n- Short window: initial triage and bridge stand-up within 60 minutes.\n- DPM creation: within 8 hours.\n- Full postmortem: published within 72 hours for Sev1/Sev2.\n\nCustomer communications templates (for bridge operator use):\n- Initial status (first 30m):\n  \"We have identified an issue affecting [feature/service]. Our team has engaged and is investigating. We will provide an update within 30 minutes.\"\n\n- Follow-up status (post-triage):\n  \"Update: The issue is caused by [brief cause]. Mitigations underway include [actions]. Current impact: [scope]. Next update scheduled at [time/ETA].\"\n\n- Resolution notice:\n  \"Resolved: The issue affecting [service] has been mitigated at [time]. Root cause and next steps will be published in a follow-up note or postmortem.\"\n\n- SLA-credit preliminary message (if applicable):\n  \"We are assessing impact against our SLA commitments. If you are eligible, we will follow up with credit details once our postmortem is complete.\"\n\nGame day design and schedule (90-minute template):\n- Goal: validate handoff, DPM creation, and customer comms speed.\n- Attendees: 1 bridge operator, 2 responders, 1 product EM, 1 customer success observer.\n- Timeline:\n  00:00 — Inject alert and distribute pager\n  00:05 — Bridge up and first customer status sent\n  00:20 — Handoff simulation between responders\n  00:45 — DPM skeleton completed and action items assigned\n  01:05 — Demo of status page update flow and mock SLA notice\n  01:20 — 15-minute retro and lessons logged\n\nRunbook snippets (examples):\n- Quick KV-cache eviction (serving-runtime):\n  \"# Commands\n  kubectl exec -n runtime svc/cache-operator -- cache evict --pattern=*\n  # Verify: tail logs for 200 responses to health endpoint for 5m\"\n\n- Throttle mitigation (traffic spike):\n  \"1) Move non-critical traffic to burst_throttle=true route.\n   2) Increase instance headroom by policy 'scale-now' for model-serving service.\n   3) Notify customers via status page if >5% error rate persists after 5m.\"\n\nOwnership and metrics (who owns what):\n- On-call synthesis owner: SRE manager (quarterly cadence).\n- DPM governance: Incident review council (product + SRE rep)\n- Bridge operator: maintains status templates and runbook links.\n- Metrics to track: mean time to ack (MTTA), mean time to remediate (MTTR), percentage of incidents resolved with DPM, action-item closure rate within 14 days.\n\nAudit and retention:\n- DPMs and postmortems retained for 2 years in the incident archive.\n- Handoff notes retained for 90 days.\n\nRelated pages and references:\n- Link: /confluence/oncall-and-incident-response/incident-evidence-collection-standard (internal)\n- Link: /confluence/eng-sre/runbooks/kv-cache-eviction (internal)\n\nAppendix: triage decision quick chart:\n- High latency + multi-tenant -> Sev1 -> full postmortem\n- Short outage <30m + single-tenant + known fix -> DPM\n- Repeated flapping events -> escalate to hypothesis-driven postmortem\n\nRevision history:\n- 2026-01-12 — created by Priya Shah\n- 2026-02-02 — added DPM SLA guidance (review: Miguel Alvarez)\n- 2026-03-01 — formalized rotation constraints and game day template (review: Sara Kim)\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_15e23a53f5124b67ac74eec12a9c59a0` — Postmortem-to-QBR Translation and Customer Readout Playbook
2. `dsid_bb8ff87e19ec43afa947c80233d3dbaf` — Containment Checklists and Post-Incident Learning Path
3. `dsid_f1f8c246c42d4b9e8030b6320d6fb0ad` — Ten-Minute Stabilization Checklist and Customer Briefs
4. `dsid_16af07ca08904644989072866aab7b6d` — QBR action plan template for model quality regression
5. `dsid_eea56bf657db4ee59d2f2e7f234ae077` — Swift Response Taskforce Playbook and CSR Briefing Protocol
6. `dsid_b720475c75e34ca88f256003e5258d63` — Fast-Path Escalation and Restoration Index
7. `dsid_b360d00be3f84b08b1a879d102835d2f` — Post-incident summary template (publishable)
8. `dsid_3b7139962b28486aaa3a498cb375b2a9` — Incident Orchestration Decision Canvas and Runbook
9. `dsid_82c0781b50cb47668b5d37a67a9a157d` — Containment and Recovery Runbook — Customer Impact Incidents
10. `dsid_51877a563b0d4f42a63e33d7735913ff` — Responder Guidance and Simulation Labs with Templates

### Fill for this row (also include in final JSON array)

```
row_id: 51
question_id: qst_0252::semantic
corpus_scale_size: 50000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 52

- **row_id:** `52`
- **question_id:** `qst_0265::semantic`
- **corpus_scale_size:** `5000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

Why do some long range analytics charts in the US East production console briefly show zero or outdated values and the drill through to traces disappears, then fixes itself after about 10 to 30 minutes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_876b1a31bcc7409ab560b9ccbe5a0d41`
_source: full_erb_file:dsid_876b1a31bcc7409ab560b9ccbe5a0d41__SUP-835120-historical-panel-staleness-after-retention-compact-warmup.txt_

```text
Historical dashboard panels show stale counts and lose trace links after retention compaction warmup

Issue summary: Several customers (notably LumenHealth) report that historical dashboard panels (time ranges > 30 days) intermittently show zeroed or stale metric counts and their trace links are missing. The problem is transient: panels become correct again after ~10-30 minutes without user action. Impact: dashboards with SLA and usage rollups show incorrect historical values; alerting based on those rollups can under- or over-fire. This affects customer trust in console analytics and can mask billing/usage anomalies. Environment: production us-east region. Affected customers reported on enterprise tier; observed across multiple orgs.
1) Open Console -> Dashboards -> choose a dashboard with weekly/monthly rollups (time range > 30 days). 2) Observe counts for a low-cardinality metric (e.g., route_success_rate, total_tokens) and trace-link anchors. 3) Rapidly change time window back and forth (e.g., 90d -> 30d -> 90d) and refresh. 4) Some panels will render with zeroed or very old counts and trace-link buttons show 'No traces' instead of opening the trace view. 5) Wait 10-30 minutes; panels recover without manual cache clear. Repro is intermittent (~1 in 10 attempts during retention compaction windows).
console-frontend: panel-render: query=rollup_v2 start=2025-12-01 end=2026-03-01 shard=warm-compact read_mode=primary; retention-indexer: compaction job id=cmp-2026-03-12-08 warmup=true; indexer-lag: lag=18m; kv-cache: miss-rate spike to 78%. Trace-hook service logs show O(200) missing anchors during query window. No 5xx in api-gateway. No token auth errors. Relevant links: https://grafana.redwood.internal/d/retention/indexer-run-03-12, https://kibana.redwood.internal/app/discover#/logs?q=cmp-2026-03-12-08
Initial hypothesis: retention compaction warmup job is causing a temporary partition state where rollup queries hit compacted partitions that are in 'read-repair' mode; dashboard renderer treats empty result as zero and trace-hook anchor resolution returns empty. Confirmed with SRE that a compaction job ran with warmup=true and indexer lag spiked ~18 minutes. Queries during warmup hit a mix of old and compacted store replicas; read-repair and backfill to hot replicas happen asynchronously. Observed that the console frontend does not fallback to hot-replica read-path when primary returns empty for rollups, so panels show stale/zeroed values. Trace-links are resolved by joining rollup keys to trace-anchor index which is being reindexed during compaction; when anchor index is temporarily empty, UI shows 'No traces'. Repro correlates strongly with compaction windows and indexer backfill events.
- Affects historical panels (>30d) across multiple enterprise orgs in us-east during retention compaction windows.
- Observed on ~4 orgs in last 72h, including LumenHealth and 2 other enterprise accounts.
- Alerts relying on those rollups may be suppressed or show incorrect counts for the duration of compaction warmup.
- No data loss: data is present after reindex/backfill; this is a read-path consistency/window problem.
Short term: ask customer to (a) avoid rapidly toggling large time windows during the scheduled compaction window, or (b) use a narrower time range (<=30d) which reads from hot partitions. Support can also force a panel refresh via console 'Force reload' (admin button) which triggers a hot-replica read. We have provided LumenHealth with instructions for forced refresh and notified them of the scheduled compaction window.
Race between retention compaction warmup and dashboard read-path: compaction marks partitions compacted while the indexer backfills the hot replica asynchronously. Dashboard queries hitting compacted-but-not-yet-backfilled partitions return empty rollups; UI treats empty as zero. Trace-anchor index reindex causes temporary absence of anchor joins. No write-side data loss.
1) Frontend: treat empty rollup responses as 'retry with hot-replica' instead of rendering zero. 2) API layer: add fallback read-path to hot replicas when compaction-warmup flag is set for the partition. 3) Indexer: reduce warmup aggressiveness and emit explicit 'warmup-in-progress' header that the API can use to select fallback. 4) Add an observability alert for 'rollup-empty-during-compaction' so SRE is alerted earlier. Implementation PR: https://github.com/redwood/reindexer/pull/1189 (adds warmup header); https://github.com/redwood/console/pull/4712 (frontend retry).
2026-03-12 Priya Sharma (Support): Customer LumenHealth reported dashboards showing 0 tokens and missing trace links for month view. They attached screenshots and time of occurrence (2026-03-12 08:17 UTC). No API 5xx from their account.
2026-03-12 Ethan Park (SRE): Confirmed compaction job cmp-2026-03-12-08 ran in us-east and indexer laged ~18m. Observed kv-cache miss spike. Investigating read-path behavior when warmup=true.
2026-03-12 LumenHealth - Mary O'Neill (Customer): We rely on monthly usage dashboards for billing reconciliations. Can you provide a short-term mitigation? We saw panels return to normal after ~25 minutes but need assurance this won't affect month-end reports.
2026-03-12 Priya Sharma (Support): Shared workaround: avoid wide time toggles and use Force reload. Scheduled notification to the customer for next compaction window. Escalated to engineering for fix prioritization.
2026-03-13 Ethan Park (SRE): Created hotfix PRs to add warmup header and frontend fallback. Deploying to staging for validation. Will schedule prod rollout during low-traffic window and notify customers.
2026-03-13 Support (Priya): Updated customer with ETA for fix and added LumenHealth to early verification list.
In Progress: Hotfix PRs opened and staged. Short-term guidance provided to customer; monitoring for recurrence. Final resolution pending deployment of API fallback and frontend retry. Follow-up postmortem to be created after prod rollout.
Deploy reindexer warmup-header to prod behind feature flag
Update console to retry rollup reads from hot-replica when empty
Add observability alert for rollup-empty-during-compaction
Postmortem documenting mitigation and scheduling change to compaction windows
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_2e39cd2d813b4399b28a20543130d48e` — Live trace stream produces duplicate session metrics when Live Trace toggle is enabled in Console
2. `dsid_096e4752a7ed47e680ddc1fe7d3488dc` — Intermittent egress routing loop during failover causing p99 latency spikes for enterprise customer
3. `dsid_4a74904e96de469eb6959ac78443f035` — Dashboard time-series shows transient spikes when tracing hook updates trace tags
4. `dsid_bad6bd97d4db46a59cb15721b6537cd8` — Console route experiment results appear stale / not updating for active experiment (aggregation + propagation lag suspected)
5. `dsid_a0f25cffcb264f0ea6eba5e501de0e08` — Unexpected egress flip from EU to APAC during high-rate embedding batch causing P99 latency burst
6. `dsid_5b0ffeac1ea64dbda6a6e9db4e98afec` — GPU demand bucketed weekly rollup (cluster & pool)
7. `dsid_124b2cc184714cbbbfe3bffb46c1eaf0` — Route-level token/cost breakdown omits prefix/KV cache token contributions causing underreported usage
8. `dsid_2cd6d5100fbe4334bd47b237f3f30678` — Trace Orchestra Conductor Profiling
9. `dsid_343773ee53ee474bbf3743a366c113dc` — Console quota readout shows refreshed tokens but requests continue 429ing during geo failover
10. `dsid_f9292a8538ea407e969b854176e438b7` — Drilldown latency percentiles on dashboard show stale per-route values after prefix-cache TTL rollover in eu-west

### Fill for this row (also include in final JSON array)

```
row_id: 52
question_id: qst_0265::semantic
corpus_scale_size: 5000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 53

- **row_id:** `53`
- **question_id:** `qst_0265::semantic`
- **corpus_scale_size:** `20000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

Why do some long range analytics charts in the US East production console briefly show zero or outdated values and the drill through to traces disappears, then fixes itself after about 10 to 30 minutes?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_876b1a31bcc7409ab560b9ccbe5a0d41`
_source: full_erb_file:dsid_876b1a31bcc7409ab560b9ccbe5a0d41__SUP-835120-historical-panel-staleness-after-retention-compact-warmup.txt_

```text
Historical dashboard panels show stale counts and lose trace links after retention compaction warmup

Issue summary: Several customers (notably LumenHealth) report that historical dashboard panels (time ranges > 30 days) intermittently show zeroed or stale metric counts and their trace links are missing. The problem is transient: panels become correct again after ~10-30 minutes without user action. Impact: dashboards with SLA and usage rollups show incorrect historical values; alerting based on those rollups can under- or over-fire. This affects customer trust in console analytics and can mask billing/usage anomalies. Environment: production us-east region. Affected customers reported on enterprise tier; observed across multiple orgs.
1) Open Console -> Dashboards -> choose a dashboard with weekly/monthly rollups (time range > 30 days). 2) Observe counts for a low-cardinality metric (e.g., route_success_rate, total_tokens) and trace-link anchors. 3) Rapidly change time window back and forth (e.g., 90d -> 30d -> 90d) and refresh. 4) Some panels will render with zeroed or very old counts and trace-link buttons show 'No traces' instead of opening the trace view. 5) Wait 10-30 minutes; panels recover without manual cache clear. Repro is intermittent (~1 in 10 attempts during retention compaction windows).
console-frontend: panel-render: query=rollup_v2 start=2025-12-01 end=2026-03-01 shard=warm-compact read_mode=primary; retention-indexer: compaction job id=cmp-2026-03-12-08 warmup=true; indexer-lag: lag=18m; kv-cache: miss-rate spike to 78%. Trace-hook service logs show O(200) missing anchors during query window. No 5xx in api-gateway. No token auth errors. Relevant links: https://grafana.redwood.internal/d/retention/indexer-run-03-12, https://kibana.redwood.internal/app/discover#/logs?q=cmp-2026-03-12-08
Initial hypothesis: retention compaction warmup job is causing a temporary partition state where rollup queries hit compacted partitions that are in 'read-repair' mode; dashboard renderer treats empty result as zero and trace-hook anchor resolution returns empty. Confirmed with SRE that a compaction job ran with warmup=true and indexer lag spiked ~18 minutes. Queries during warmup hit a mix of old and compacted store replicas; read-repair and backfill to hot replicas happen asynchronously. Observed that the console frontend does not fallback to hot-replica read-path when primary returns empty for rollups, so panels show stale/zeroed values. Trace-links are resolved by joining rollup keys to trace-anchor index which is being reindexed during compaction; when anchor index is temporarily empty, UI shows 'No traces'. Repro correlates strongly with compaction windows and indexer backfill events.
- Affects historical panels (>30d) across multiple enterprise orgs in us-east during retention compaction windows.
- Observed on ~4 orgs in last 72h, including LumenHealth and 2 other enterprise accounts.
- Alerts relying on those rollups may be suppressed or show incorrect counts for the duration of compaction warmup.
- No data loss: data is present after reindex/backfill; this is a read-path consistency/window problem.
Short term: ask customer to (a) avoid rapidly toggling large time windows during the scheduled compaction window, or (b) use a narrower time range (<=30d) which reads from hot partitions. Support can also force a panel refresh via console 'Force reload' (admin button) which triggers a hot-replica read. We have provided LumenHealth with instructions for forced refresh and notified them of the scheduled compaction window.
Race between retention compaction warmup and dashboard read-path: compaction marks partitions compacted while the indexer backfills the hot replica asynchronously. Dashboard queries hitting compacted-but-not-yet-backfilled partitions return empty rollups; UI treats empty as zero. Trace-anchor index reindex causes temporary absence of anchor joins. No write-side data loss.
1) Frontend: treat empty rollup responses as 'retry with hot-replica' instead of rendering zero. 2) API layer: add fallback read-path to hot replicas when compaction-warmup flag is set for the partition. 3) Indexer: reduce warmup aggressiveness and emit explicit 'warmup-in-progress' header that the API can use to select fallback. 4) Add an observability alert for 'rollup-empty-during-compaction' so SRE is alerted earlier. Implementation PR: https://github.com/redwood/reindexer/pull/1189 (adds warmup header); https://github.com/redwood/console/pull/4712 (frontend retry).
2026-03-12 Priya Sharma (Support): Customer LumenHealth reported dashboards showing 0 tokens and missing trace links for month view. They attached screenshots and time of occurrence (2026-03-12 08:17 UTC). No API 5xx from their account.
2026-03-12 Ethan Park (SRE): Confirmed compaction job cmp-2026-03-12-08 ran in us-east and indexer laged ~18m. Observed kv-cache miss spike. Investigating read-path behavior when warmup=true.
2026-03-12 LumenHealth - Mary O'Neill (Customer): We rely on monthly usage dashboards for billing reconciliations. Can you provide a short-term mitigation? We saw panels return to normal after ~25 minutes but need assurance this won't affect month-end reports.
2026-03-12 Priya Sharma (Support): Shared workaround: avoid wide time toggles and use Force reload. Scheduled notification to the customer for next compaction window. Escalated to engineering for fix prioritization.
2026-03-13 Ethan Park (SRE): Created hotfix PRs to add warmup header and frontend fallback. Deploying to staging for validation. Will schedule prod rollout during low-traffic window and notify customers.
2026-03-13 Support (Priya): Updated customer with ETA for fix and added LumenHealth to early verification list.
In Progress: Hotfix PRs opened and staged. Short-term guidance provided to customer; monitoring for recurrence. Final resolution pending deployment of API fallback and frontend retry. Follow-up postmortem to be created after prod rollout.
Deploy reindexer warmup-header to prod behind feature flag
Update console to retry rollup reads from hot-replica when empty
Add observability alert for rollup-empty-during-compaction
Postmortem documenting mitigation and scheduling change to compaction windows
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_b127efa7f884490fb4704c90cc8f0592` — Saved dashboard query times out for >24h ranges and associated tracing links return 404
2. `dsid_02ae04b078dd456e825c2d2d5a87175c` — Trace span anchor misalignment in console causing dashboard 'open logs' to jump to wrong time window
3. `dsid_c1f90c472e1946e88bda0de64a95ff70` — Console dashboard panel goes blank when timeframe crosses retention cutoff
4. `dsid_a8302bc5f129440a880dc1ddaced54e9` — Dashboard series facet ordering appears randomized after live refresh, breaking drilldowns
5. `dsid_4866ef84859a43b89d77178c28d9513c` — Console dynamic filter debounce causes trace-link disappearance on dashboard update
6. `dsid_5f4aa0a4548647ae8553a0929723e4cd` — Console usage heatmap bucketization produces missing hourly spikes when zooming/adjusting timescale
7. `dsid_5ef9f435fc9d40be94e4d8ba2ab7c34c` — Realtime Console 'Usage Snapshot' shows inflated tokens after editing query filters
8. `dsid_2e39cd2d813b4399b28a20543130d48e` — Live trace stream produces duplicate session metrics when Live Trace toggle is enabled in Console
9. `dsid_0eba0717ee044630af6afd0d633a8261` — Anomaly detection alerts link to stale model-version traces after nightly compaction
10. `dsid_096e4752a7ed47e680ddc1fe7d3488dc` — Intermittent egress routing loop during failover causing p99 latency spikes for enterprise customer

### Fill for this row (also include in final JSON array)

```
row_id: 53
question_id: qst_0265::semantic
corpus_scale_size: 20000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 54

- **row_id:** `54`
- **question_id:** `qst_0268::semantic`
- **corpus_scale_size:** `10000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

In the March 2026 production incident where long streamed chat replies started arriving chopped up and in the wrong order and the customers usage charges jumped because their client kept reissuing the same request, what was identified as the underlying platform cause?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a990e708840f481795741cfd3fb55691`
_source: full_erb_file:dsid_a990e708840f481795741cfd3fb55691__SUP-376545-cinderlabs-session-tear-retry-amplification-billing-spike-postincident.txt_

```text
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
- 17:42 UTC: Disabled aggressive client-side retry guidance sent to Cinder Labs; asked temporary SDK toggle to backoff.
- 18:10 UTC: Rolling kernel-selection rollback (PR linked) deployed for us-east pool which stopped KV prefix evictions during active streaming.
- 19:00 UTC: Error rates returned to baseline; streaming behavior normalized.

Timeline and findings:
- 2026-03-09 17:22 UTC: first elevated 5xx and streaming truncations for Cinder Labs observed (api-gateway metrics + their telemetry).
- Root cause hypothesis: interaction between a recent kernel-selection tweak (PR 4821) and aggressive KV compaction led to transient state loss for long-lived sessions.
- Evidence: heap/kvcache flush logs on serving nodes show compaction events coincident with affected session IDs.
- Replay of workload on staging reproduced token reordering when compaction was force-triggered during active streaming.
- Throttle amplification: client SDK retry logic started new requests that did not enforce session-affinity, creating fanout and repeated token generation for the same logical conversation.
- Billing delta analysis: aggregated request counts for Cinder Labs during the window were 2.4x baseline; cost-weighted tokens increased proportionally.
- Contrib factors: recent autoscaler tuning reduced pre-warmed buffer by 20% in us-east pool, increasing likelihood that compaction/eviction occurred under pressure.

Support (Maya Chen) — 2026-03-09 17:30 UTC: Customer reported truncated streams and repeated partial messages. Opened incident and paged SRE.
SRE (Arjun Patel) — 2026-03-09 17:38 UTC: Identified KV compaction entries correlated with session IDs. Temporarily rerouted traffic to healthy pool.
Customer (Elena Ruiz, Cinder Labs) — 2026-03-09 17:45 UTC: Confirmed temporary improvement after reroute; requested timeline and credit for billing spike.
Eng (Tomasz Novak) — 2026-03-09 18:05 UTC: Rolled back kernel-selection change (PR 4821) in us-east as mitigation; monitoring for regressions.
Billing (Priya Shah) — 2026-03-10 09:12 UTC: Preliminary credit calculation prepared; recommended 50% credit for the affected window pending final audit.
Support (Maya Chen) — 2026-03-11 11:02 UTC: Sent post-incident summary and next steps to Cinder Labs; scheduled follow-up review on 2026-03-12.
Customer (Elena Ruiz) — 2026-03-11 15:40 UTC: Appreciated rapid response; requested concrete SDK guidance to avoid amplification in future.
Root cause: interaction between a kernel-selection optimization and KV compaction behavior on serving nodes caused transient session state loss for long chat contexts, leading to token reordering. Secondary amplification: client SDK retries without enforced session-affinity produced duplicate inflight completions and a billing spike.

Fixes applied:
- Rolled back kernel-selection tweak in us-east (PR 4821) and deployed a guarded kernel rollout that disables compaction during active streams.
- Temporary routing to pre-warmed pool restored stability during the rollout.
- Issued a targeted billing credit to Cinder Labs (50% of the two-hour delta) and submitted final audit for adjustment.

Status: Mitigation deployed, monitoring in place, customer credited; incident closed after validation period.
Implement server-side session-affinity enforcement for streaming continuations (owner: Eng/Serving Runtime) — ETA 2026-04-07
Add a compaction-safe flag to the runtime that prevents KV prefix eviction during active streams (owner: Eng/Serving Runtime) — ETA 2026-03-25
Enhance SDKs to surface and opt-in to conservative retry modes for enterprise tiers (owner: DevX/SDK) — ETA 2026-04-01
Create billing audit dashboard to detect anomalous retry amplification per customer (owner: Finance/Platform) — ETA 2026-03-20
Run tabletop with top enterprise customers to validate failover behaviors and communication playbooks (owner: Support/GTM) — ETA 2026-04-15
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_576496e2926e4747980636f3ee519243` — Axiom Payments - duplicate streaming replies and sudden throttling causing transaction failures
2. `dsid_5f884c5669194d698c0be56a1df92b33` — Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling
3. `dsid_97992c0043184c7b9c10ed2106482ae1` — Hosted API: client-side context deadline exceeded on streaming chat (us-west)
4. `dsid_04e4f59077354c05986cd31b1986c6ac` — Intermittent multiplexed SSE session stall when mobile app is backgrounded, partial final output on reconnect
5. `dsid_c7bcf2745c8f44228768c7650ed1358f` — Streaming sometimes stops mid-generation (no final chunk) on Hosted API
6. `dsid_0eb30895fb1a4009bc8c443055718882` — SapphireLine multi-region routing race caused streaming truncation during end-of-day batches — customer escalation and action plan
7. `dsid_a7baddf163ef4946a97b4765bf1cf08b` — Invoice shows unexpected token usage and model charges
8. `dsid_3042eea9b36942ae8084eab2f28c3012` — Rate-shedding policy misfire during tenant surge leading to 5xx retry cascade
9. `dsid_fd4ca30984c8455a9e77b5a324cc1b80` — Intercontinental multipath crossover causing chunked response delays for streaming inference
10. `dsid_891626ad3966452c8afa7297f4f27485` — Sustained TTFB drift on long-running HTTP/2 sessions caused by proxy flush delay and stream multiplexing

### Fill for this row (also include in final JSON array)

```
row_id: 54
question_id: qst_0268::semantic
corpus_scale_size: 10000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 55

- **row_id:** `55`
- **question_id:** `qst_0268::semantic`
- **corpus_scale_size:** `75000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the March 2026 production incident where long streamed chat replies started arriving chopped up and in the wrong order and the customers usage charges jumped because their client kept reissuing the same request, what was identified as the underlying platform cause?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_a990e708840f481795741cfd3fb55691`
_source: full_erb_file:dsid_a990e708840f481795741cfd3fb55691__SUP-376545-cinderlabs-session-tear-retry-amplification-billing-spike-postincident.txt_

```text
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
- 17:42 UTC: Disabled aggressive client-side retry guidance sent to Cinder Labs; asked temporary SDK toggle to backoff.
- 18:10 UTC: Rolling kernel-selection rollback (PR linked) deployed for us-east pool which stopped KV prefix evictions during active streaming.
- 19:00 UTC: Error rates returned to baseline; streaming behavior normalized.

Timeline and findings:
- 2026-03-09 17:22 UTC: first elevated 5xx and streaming truncations for Cinder Labs observed (api-gateway metrics + their telemetry).
- Root cause hypothesis: interaction between a recent kernel-selection tweak (PR 4821) and aggressive KV compaction led to transient state loss for long-lived sessions.
- Evidence: heap/kvcache flush logs on serving nodes show compaction events coincident with affected session IDs.
- Replay of workload on staging reproduced token reordering when compaction was force-triggered during active streaming.
- Throttle amplification: client SDK retry logic started new requests that did not enforce session-affinity, creating fanout and repeated token generation for the same logical conversation.
- Billing delta analysis: aggregated request counts for Cinder Labs during the window were 2.4x baseline; cost-weighted tokens increased proportionally.
- Contrib factors: recent autoscaler tuning reduced pre-warmed buffer by 20% in us-east pool, increasing likelihood that compaction/eviction occurred under pressure.

Support (Maya Chen) — 2026-03-09 17:30 UTC: Customer reported truncated streams and repeated partial messages. Opened incident and paged SRE.
SRE (Arjun Patel) — 2026-03-09 17:38 UTC: Identified KV compaction entries correlated with session IDs. Temporarily rerouted traffic to healthy pool.
Customer (Elena Ruiz, Cinder Labs) — 2026-03-09 17:45 UTC: Confirmed temporary improvement after reroute; requested timeline and credit for billing spike.
Eng (Tomasz Novak) — 2026-03-09 18:05 UTC: Rolled back kernel-selection change (PR 4821) in us-east as mitigation; monitoring for regressions.
Billing (Priya Shah) — 2026-03-10 09:12 UTC: Preliminary credit calculation prepared; recommended 50% credit for the affected window pending final audit.
Support (Maya Chen) — 2026-03-11 11:02 UTC: Sent post-incident summary and next steps to Cinder Labs; scheduled follow-up review on 2026-03-12.
Customer (Elena Ruiz) — 2026-03-11 15:40 UTC: Appreciated rapid response; requested concrete SDK guidance to avoid amplification in future.
Root cause: interaction between a kernel-selection optimization and KV compaction behavior on serving nodes caused transient session state loss for long chat contexts, leading to token reordering. Secondary amplification: client SDK retries without enforced session-affinity produced duplicate inflight completions and a billing spike.

Fixes applied:
- Rolled back kernel-selection tweak in us-east (PR 4821) and deployed a guarded kernel rollout that disables compaction during active streams.
- Temporary routing to pre-warmed pool restored stability during the rollout.
- Issued a targeted billing credit to Cinder Labs (50% of the two-hour delta) and submitted final audit for adjustment.

Status: Mitigation deployed, monitoring in place, customer credited; incident closed after validation period.
Implement server-side session-affinity enforcement for streaming continuations (owner: Eng/Serving Runtime) — ETA 2026-04-07
Add a compaction-safe flag to the runtime that prevents KV prefix eviction during active streams (owner: Eng/Serving Runtime) — ETA 2026-03-25
Enhance SDKs to surface and opt-in to conservative retry modes for enterprise tiers (owner: DevX/SDK) — ETA 2026-04-01
Create billing audit dashboard to detect anomalous retry amplification per customer (owner: Finance/Platform) — ETA 2026-03-20
Run tabletop with top enterprise customers to validate failover behaviors and communication playbooks (owner: Support/GTM) — ETA 2026-04-15
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_576496e2926e4747980636f3ee519243` — Axiom Payments - duplicate streaming replies and sudden throttling causing transaction failures
2. `dsid_46673c0aed2445bba9152d27087585e1` — Starlane Chat: out-of-order completions across multiplexed shards causing inconsistent conversation state and urgent customer escalation
3. `dsid_5f884c5669194d698c0be56a1df92b33` — Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling
4. `dsid_0be5b3eafb744671a8f21b6e4d01c814` — Elevated initial response latency for chat completions after inference compiler swap and model handoff
5. `dsid_cb214acea1614a5989b59174093df168` — Intermittent 5xx spike during priority rebalancing and IO slab fragmentation
6. `dsid_97992c0043184c7b9c10ed2106482ae1` — Hosted API: client-side context deadline exceeded on streaming chat (us-west)
7. `dsid_75a5de7f48ae4b65a0ef4384f7ae97d4` — Rivermark: streamed completions stop delivering chunks (chunked transfer stalls)
8. `dsid_347eff5fb54c4409ad954708536363ad` — Midday throughput lull in dedicated pool during short-stream bursts causing autoscaler lag and per-tenant GPU scarcity
9. `dsid_211bee1cefa643279441e2a59eea9965` — Chat streaming truncated after transient pipeline reset for dedicated customer
10. `dsid_ab2164509b734a2c8e1a33bb5182ea33` — CumulusMart — intermittent streaming fragment interleaving due to routing oscillation (post-incident escalation)

### Fill for this row (also include in final JSON array)

```
row_id: 55
question_id: qst_0268::semantic
corpus_scale_size: 75000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 56

- **row_id:** `56`
- **question_id:** `qst_0310::intra_document_reasoning`
- **corpus_scale_size:** `100000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`other`

### Question

In the on-prem cutover readiness weekly sync meeting, who attended, and what two checkpoint meetings (with dates) were scheduled around the staging soak test?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_b9025f196ac14b2cb7a2905654dd42d7`
_source: full_erb_file:dsid_b9025f196ac14b2cb7a2905654dd42d7__2026-09-30-onprem-cutover-readiness-egress-capacity-playbook.txt_

```text
On-prem Cutover Readiness: Egress & Capacity Playbook - weekly sync

Meeting header:\nDate/Time: 2026-09-30 15:00 UTC\nDuration: 48 minutes\nAttendees: Samir Patel (Redwood AE), Lila Novak (Redwood SE), Diego Ramos (Redwood), Marco Rivera (Aurelia CTO), Priya Singh (Aurelia NetOps), Ethan Cole (Aurelia SRE)\n\nAuto-summary (auto-gen, may be rough):\n- Week 5 of on-prem pilot; focus on cutover readiness, egress routing, kernel upgrade and capacity shaping.\n- Identified two main blockers: egress firewall rules & kernel compatibility test failures in one host.\n- Agreed next steps: run soak test, share runbook, provide firewall rules, finalize rollback steps.\n\nTopics: cutover readiness, egress NAT/allowlist, kernel upgrade 6.x, capacity/traffic shaping, fallback policies, soak tests\n\nAction items (captured in metadata too)\n\nTranscript body:\n[00:00] Samir (AE): okay, hi everyone, thanks for joining. good to see you. this is our weekly sync for the on-prem pilot, focused on cutover readiness. we have samir, lila, diego on redwood side. aurelia: marco, priya, ethan, thanks for making time.\n\n[00:22] Marco (CTO): yeah thanks, morning for us. short timezone note, we're on a hard deadline for a staged cutover in two weeks so want to make sure blockers are surfaced.\n\n[00:35] Lila (SE): quick agenda I have — egress readiness, kernel upgrade status, capacity shaping + soak plan, and then open issues. if that works for you we can dive in.\n\n[00:48] Priya (NetOps): works. first item, priya here, egress. we tried to lock down the firewall allowlist but there are some internal groups that route via a proxy and we saw some TLS handshake fails when we hit the redwood private endpoints from our test lab. not sure if it's our proxy or the egress ip set.\n\n[01:12] Samir: got it. can you paste the exact error / log snippet? sometimes the handshake looks like a cert chain timing out vs ip-level block.\n\n[01:24] Priya: (typing sound) i've pasted a snippet in the chat — "tcp reset after 3s handshake timeout, peer cert not found" — and the source ip is from our transit proxy 10.88.4.23, which I believe isn't in your allowlist.\n\n[01:40] Diego: hmm, our NAT egress pool for your VPC should include the proxy range. it's possible the mapping didn't include the transit subnet when we provisioned the private connectors. i can check that mapping now.\n\n[02:00] Ethan (SRE): quick note — when we ran the preflight yesterday one of the nodes failed the kernel self-test after the inference kernel install, showing a page-fault under 95th percentile memmap op. we reverted that host but want a root cause.\n\n[02:18] Lila: memory map page fault, interesting. do you have the kernel version? is that the 6.4 pre-release we pushed? sometimes the jemalloc path and the inference kernel's custom mmap path collide.\n\n[02:32] Ethan: it's 6.4-rc1, yes. test host showed crash on first warmup batch for the redwood runtime, with logs mentioning unknown symbol for fast-attn.\n\n[02:47] Samir: okay that aligns with a note we had — some early 6.4 kernels changed the module symbol resolution, causing our custom fast-attn kernel to fail to load, which causes fallback to slower op path and on some images to segfault. we pushed a patch to the kernel adaptor last week but haven't verified across images.\n\n[03:06] Marco: so is that a blocker for cutover? our timeline is 14 days out, we need a firm yes/no.\n\n[03:15] Lila: at present it's a risk. we have two mitigation paths: 1) pin hosts that will run the pilot to a known-good kernel (6.3.x) until we finish validation; or 2) apply the redwood kernel adaptor patch and run a quick validation across staging nodes. option 1 is faster rollback but means a temporary policy to avoid 6.4. option 2 is more future-proof but needs 24-72 hour validation window.\n\n[03:41] Priya: pinned older kernel sounds easier for our ops team — less change. but we have a corporate policy to keep kernels updated monthly, so it would need an exception.\n\n[03:54] Diego: i can prepare a short pre-check list for the kernel update that includes module load tests, fast-attn probe, and a small-batch inference run. that checklist will let you decide to approve the patch route.\n\n[04:10] Samir: diego will own the checklist and the rollback steps. diego, can you give a timeline?\n\n[04:18] Diego: yes — i can produce the checklist today and run the adaptor patch validation tomorrow on two staging nodes, that'll take about 6 hours of total run time but we need access and the same image set you plan to use.\n\n[04:33] Marco: we'll provision two staging nodes with the same image and grant access. marco to coordinate with ethan to provide creds.\n\n[04:42] Ethan: i'll do that after the call. next topic — capacity shaping. we measured steady token throughput on your sample workload and saw CPU steal and occasional queuing that increased p95 latency when batch size > 8.\n\n[04:59] Lila: right, that's the batching threshold where our continuous-batching heuristic swings from sub-ms to burst mode. we can tune the target batch size and the max latency threshold. generally recommend target batch 6-8 for your LLM family, but if you need lower p95 we can drop to 4 and accept a higher cost per token.\n\n[05:20] Priya: cost vs latency tradeoff — what do you estimate for our projected QPS? we gave a sample of 120 qps average overnight, peaks at 450 qps.\n\n[05:33] Samir: with those numbers, on our Dedicated VMs for private you could expect X tokens/sec per GPU. (note: Samir points to a shared spreadsheet link) quick back-of-envelope: if we target batch size 6, you see 18% cost improvement vs batch 4 but p95 goes up ~20ms. if we reduce batch to 4 p95 improves by ~25ms but cost increases ~22%.\n\n[05:59] Marco: send that table. the spreadsheet link in chat isn't accessible to me.\n\n[06:06] Samir: will resend with org-level perms. link: https://redwood.app/sheets/pilot-aurelia-capacity (placeholder)\n\n[06:15] Lila: also note prefix caching can help — your workload has many repeated system prompts so we could enable prefix/KV cache behavior to cut token compute by 10-15% at little latency cost. needs a small policy change on your side regarding cache TTL.\n\n[06:33] Priya: TTL question — how long do cached prefixes live and is that compliant with our data retention? we can't keep unencrypted user data in cache longer than 48 hours per policy.\n\n[06:46] Diego: our prefix cache stores KV only, not user-identifying metadata unless you opt in. we can set TTL at 12 hours for the pilot to be safe. encryption at rest is via customer KMS if you want.\n\n[06:59] Priya: okay if KMS integration is enabled, 12 hour TTL is fine. please document that.\n\n[07:06] Samir: noted — document in runbook. next — egress allowlist specifics, who has the list?\n\n[07:14] Priya: i do. sending... (chat) list contains the corporate NAT ranges and transit proxies. i see in the snippet you have 3 public IP ranges, but ours uses a shared egress IP that goes through a floating NAT behind the proxy.\n\n[07:31] Diego: that's probably the gap — our automation maps VPC subnets to egress ip pools but floating nat from your proxy might show as multiple ephemeral IPs. we can accept a CIDR block instead of single IPs if that helps.\n\n[07:45] Priya: we can provide a /24, but security insists on narrow allowlists. i'll file a waiver but need to show proof-of-control.\n\n[07:57] Marco: can redwood provide a signed cert or token that proves the endpoint identity so we can allow wildcard but limit to verified TLS endpoints?\n\n[08:08] Lila: we have mTLS options and client-cert verification for private connectors. we can provide a cert bundle and an SNI-based validation. not a signed token per se but a cert chain that your proxy can validate.\n\n[08:24] Ethan: good — how quickly can we get that cert shipped?\n\n[08:29] Samir: we can generate a cert bundle after you confirm a CSR; timeline 24-48 hours. we'll attach the CSR template to the runbook.\n\n[08:38] Priya: excellent. next: soak tests — we want a 3-hour latency soak in staging that mirrors peak. are there scripts we can run?\n\n[08:46] Lila: yes, we have a harness that replayed your sample traces. i'll share the script and a docker container. it will drive the same distribution including ramp and peak. we need your staging creds and a window during off hours.\n\n[09:01] Ethan: proposed window: 2026-10-07 02:00 - 05:00 UTC. works for our ops.\n\n[09:10] Diego: we'll bring extra monitoring hooks during that test — token-level latency, queue depth, kernel module load traces and kernel dmesg. if we hit the earlier crash signature we'll auto-roll back that host.\n\n[09:23] Marco: rollback behavior then — what exactly is the automatic rollback?\n\n[09:27] Diego: if the host shows the mmap pagefault signature or segfault in inference runtime, our orchestration will cordon and drain the host, move incumbent tasks to other hosts, and if host doesn't recover under 20 minutes we mark it for reprovision. rollback playbook will be in runbook.\n\n[09:46] Priya: question about tracing — can the logs be forwarded to our Splunk instance? we prefer central observability.\n\n[09:54] Lila: yes, we can configure log forwarding via syslog/HTTP ingest; most customers forward to Splunk or S3. we'll add example config. note there is PII scrub option on logs.\n\n[10:10] Samir: quick pause — does anyone have any other blockers we haven't covered?\n\n[10:16] Marco: yes, licensing question — if we pin kernels to 6.3 for some hosts, does that change the pricing? we had a quoted price for mixed throughout.\n\n[10:26] Samir: short answer: no immediate change. kernel pinning itself doesn't affect cost unless you require dedicated reserved capacity for older images. if you keep the same instance sizes and GPUs it's cost-neutral.\n\n[10:36] Marco: okay good. next item — fallback routing and traffic shaping during cutover. how do we route traffic if the new egress path fails?\n\n[10:45] Lila: we propose a staged fallback: primary -> regional fallback -> global fallback. primary is direct private connector, regional fallback routes to a non-private but dedicated path with IP ACLs, global fallback uses a lower-tier model variant we host in our public infra. global fallback degrades quality but keeps service online.\n\n[11:05] Priya: for compliance we need explicit audit/tracing when we cross from private to public infra. do you log that event?\n\n[11:12] Diego: yes every routing decision is logged with token counts and model id; those logs are forwarded and can be retained per your retention policy. we'll surface an event in console and send an alert.\n\n[11:25] Ethan: one more item — the perf discrepancy we saw between nodes. one node shows 8-10% higher latency under same load. we suspect CPU frequency scaling or NUMA misconfig. any suggestions?\n\n[11:36] Lila: check governor settings and ensure CPU turbo is enabled and cpufreq governor set to performance for inference hosts. also verify NIC interrupts and IRQ affinity — sometimes NICs are pinned wrong causing CPU steal.\n\n[11:50] Marco: we'll run that ops checklist. marco to confirm.\n\n[12:00] Samir: to recap, we have: diego creates kernel pre-check and rollback playbook; lila will share soak test harness and scripts; samir to update runbook with egress CSR template and pricing sheet; priya to share firewall rules; ethan to provision staging and run the soak. agreed?\n\n[12:21] Priya: agreed. quick note on docs sharing — please use our secure share link.\n\n[12:27] Samir: will do. i'm going to attach the runbook draft after this call.\n\n[12:33] Marco: any risks we haven't discussed? performance regressions on quantization settings — we should ensure quality checks post-quant.\n\n[12:42] Lila: yes let's add a quality regression eval: sample prompts and an automated rouge/bertscore probe for structural/regression detection. we'll add to runbook.\n\n[12:55] Ethan: for the soak test I'd like to capture full kv-cache hit ratio and batch occupancy percentiles — can your harness emit those?\n\n[13:05] Lila: yes, the harness can capture batch occupancy and kv hits. we'll add those metrics to the test output.\n\n[13:14] Samir: final administrative — next sync same time next week? or do we want a pre-soak checkpoint?\n\n[13:21] Marco: let's do a short pre-soak check on 2026-10-06 and a full post-soak review on 2026-10-08.\n\n[13:30] Samir: noted. i'll send invites. thanks all.\n\n[13:36] (call ends)\n\nNotes on transcription quality: conversational with some auto-caption errors (e.g., "kayvee cache" vs "KV cache", "fast-attn" sometimes transcribed as "fast ten"). speaker labels auto-assigned.\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_8463a5db671f40318362748fc9e9edb4` — Deployment safety checks and A/B cutover sync
2. `dsid_eb3969b49ce444c092e6ef7aa1d10f55` — Weekly POC Sync — heuristic tuning and emergency routes
3. `dsid_00b1aa8661ca40c6bee153cfbc57e18d` — Helios pilot readiness & cutover rehearsal
4. `dsid_e4f5c5e330fb4acba12b78927d0bb632` — Governance Handoff and Cutover Ops Walkthrough
5. `dsid_eb9ab34e2572447095904775e6269dbc` — Silverpine Pilot - Gov Ops Tuning Sync
6. `dsid_25034eed301f4aaf8ef8f45d5313dd9d` — Pilot: canary rollforward readiness & nested routing check
7. `dsid_026159f20b7d493ca45e7a3d924b5220` — POC weekly sync — signal calibration, on-call rotations, and cutover scripting
8. `dsid_85ca1944512a40418dd9c8fc5b0dae0d` — POC Weekly - Incident triage + telemetry gaps
9. `dsid_44e5f0ab26224c7787364fadac519579` — POC Network Rehearsal & Routing Acceptance — AstraVault
10. `dsid_484f118b24dd4bd3b290e59dce06e8f8` — Pilot safety matrix, runbook rehearsal, and A/B traffic concord

### Fill for this row (also include in final JSON array)

```
row_id: 56
question_id: qst_0310::intra_document_reasoning
corpus_scale_size: 100000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 57

- **row_id:** `57`
- **question_id:** `qst_0349::project_related`
- **corpus_scale_size:** `75000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

What caused the EU-West activation funnel and onboarding email issues in late January, and which code/config changes fixed them?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_21d6b99dc771418287d61444f373852e`
_source: full_erb_file:dsid_21d6b99dc771418287d61444f373852e__SUP-24871-not-receiving-onboarding-emails.txt_

```text
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
Created after 3 similar HelpScout pings escalated to Growth Ops. This one is the cleanest repro: eu-west signup, no send events at all. Assigning to Ethan (trigger logic owner) + tagging Logan for event pipeline visibility.

Customer email excerpt:
“Signed up yesterday; didn’t get any onboarding emails my coworker mentioned. We checked spam. Can you resend or confirm where the setup steps are?”
2026-01-31 10:03 UTC — Ethan Park (Assignee)
Acknowledged. Looking at lifecycle-trigger service metrics. Quick check: send volume in us-east looks normal; eu-west near zero since 01/29 deploy window. That suggests we’re not consuming signup events in eu-west.

Next steps:
- Verify Kafka/topic replication for user.signup events into eu-west consumer group
- Confirm eu-west deployment of lifecycle-trigger (possible missing deployment or wrong cluster config)
- Provide workaround: manual resend + direct docs link
2026-01-31 10:26 UTC — Logan Wright
Pulled data from analytics dataset: funnel shows signups in eu-west continue, but downstream lifecycle_email_send_requested is flat. This aligns with no trigger execution, not deliverability.

Notably: activation events were recently deduped (PR-28521), but that shouldn’t eliminate sends entirely in one region.
2026-01-31 11:05 UTC — Ethan Park
Root cause found: lifecycle-trigger eu-west deployment is pointing to the us-east event bus endpoint (legacy), which rejects cross-region auth. Errors were being logged but not surfaced in dashboards.

Evidence:
- eu-west pod logs show repeated “401 from eventbus publish” when attempting to enqueue lifecycle sends
- No retries making it into queue

Fix plan:
- Update eu-west config to use regional event bus endpoint + rotate service token scope
- Add alert on publish error rate > 1% for 5m

ETA: config change + restart within 2–3 hours.
2026-01-31 12:10 UTC — Tyler Benson
Customer update drafted (pending confirmation fix is live). Also sending them quickstart links now to unblock:
- Hosted API quickstart
- “Hello world” first request snippet

Request to Eng: can we trigger a one-time backfill send for signups since 01/29 in eu-west (limited volume) after fix? If not, Support can do manual resends for known affected accounts.
2026-01-31 14:42 UTC — Ethan Park
Fix deployed to eu-west. Observing sends resume over last 20 minutes.

Backfill:
We can run a one-off job to enqueue Email #1 for eligible eu-west signups in last 48h where no send_requested event exists. Will coordinate with Tyler to avoid duplicates + honor unsubscribes.

Also created follow-up note for INT-3310 to include regional publish failure in the discrepancy investigation.
2026-01-31 15:18 UTC — Tyler Benson
Confirmed in SendGrid: Lumen Support address received the resent welcome email (delivered event present). Customer replied “Got it, thanks.”

Marking customer unblocked.

Please keep monitoring complaints in case other cohorts were affected.
2026-02-02 09:05 UTC — Ethan Park
Backfill completed for eu-west (01/29–01/31) with guardrails:
- Only users with lifecycle_email_enabled=true
- No prior send_requested
- Not in suppression/unsubscribed

Monitoring:
- Added dashboard panel for lifecycle publish errors by region
- Alert created for sustained 401/403 on eventbus publish

Resolution is stable as of 02/02.
2026-02-02 09:22 UTC — Tyler Benson
Closing ticket. Customer confirmed receipt and activation guidance is unblocked. Linking this to ongoing deliverability work (INT-3301) but this incident was trigger/config, not inbox placement.
Resolved by correcting eu-west lifecycle-trigger configuration to publish to the regional event bus endpoint (previously misconfigured to us-east, causing auth failures and zero send requests). Ran a one-time backfill to enqueue missed welcome emails for eligible eu-west signups (01/29–01/31) and added regional error monitoring/alerts. Customer (Lumen Support) received manual resend and confirmed receipt.
```

#### GOLD `dsid_44cf2d75d70d4365914aa46947a94b1d`
_source: full_erb_file:dsid_44cf2d75d70d4365914aa46947a94b1d__pr-28521-fix-duplicate-signup-event-emission.txt_

```text
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
- Staging load test (forced refresh + retry): 1.00 `signup_completed` events per distinct `user_id`
- Prod canary (5% of traffic for 3 hours): 1.01 events per distinct `user_id` (small remainder due to legacy clients still in flight)
- Funnel conversion rates returned to expected ranges and the signup stage volume dropped ~35% relative to distinct users (consistent with prior duplication rate)

## Rollout
- Ship as hotfix to `main`
- No migrations
- Dashboard owners: Sergio Costa / Allison Grant are aware; update their sanity-check query to use distinct users as a guardrail until the canary completes.

## Checklist
- [x] Confirmed no downstream systems require client-side emission
- [x] Added tests
- [x] Verified event schema unchanged (only emission sites)
- [x] Coordinated with Growth (Ben Carter) on expected dashboard deltas

Refs:
- INT-3310 (activation funnel discrepancy)
- Lifecycle growth sprint instrumentation (ENG-10492)
- Activation funnel dashboard work (ENG-10533)
Logan Wright (review): Can we confirm we’re not suppressing legitimate replays if a user opens two tabs during signup? Also, why 30 minutes for the dedupe window?
Nadia Rahman (author): Yes—two tabs will hit the same user_id and we *do* want one logical signup event. 30m is meant to cover retries/refreshes around auth callback + console bootstrap; we can tune shorter if you prefer. Also keyed by (event_name,user_id) only, so it won’t affect other funnel events.
Dylan Brooks (review): Removing the client emission makes sense. Any chance older console builds still rely on the client event for experiment cohort assignment?
Nadia Rahman (author): Cohort assignment is via feature flag service on signup timestamp + user id; not tied to this event. Confirmed with Ethan/Benji on ENG-10501 thread; this event is analytics-only.
Paula Mendes (review): Please add a note in the PR about the legacy alias event name (`activation_signup`) so we don’t get bitten again in SQL.
Nadia Rahman (author): Added to “What changed” + validation section; also dedupes both names. Good call.
Logan Wright (review): Test looks good. One suggestion: make the redis key include environment to avoid any weirdness in shared infra.
Nadia Rahman (author): Updated key prefix to include env namespace (already present in redis client config, but now explicit in the key builder).
CI (bot): ✅ build / unit-tests (pass) | ✅ lint (pass) | ✅ console-e2e-smoke (pass)
Dylan Brooks (review): Approved. Let’s monitor funnel dashboard after merge; we should expect a visible drop in signup counts.
Logan Wright (review): Approved.
Paula Mendes (review): Approved after key prefix change.
```

#### GOLD `dsid_fe7a496e795b4baca997e655f9316fc5`
_source: full_erb_file:dsid_fe7a496e795b4baca997e655f9316fc5__INT-3310-event-tracking-discrepancy-activation-funnel.txt_

```text
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
- Cross-checked three sources for the same window (2026-01-21 00:00–2026-01-22 23:59 UTC):
  - Raw collector logs: stable event counts in eu-west.
  - Warehouse fact_events table: stable api_key_created events in eu-west.
  - Activation Funnel dashboard: apparent eu-west drop.
- Found the discrepancy was query-side + dedupe behavior:
  - The funnel panel’s Step 1 “signup” was keyed off signup_created events and deduped by (user_id, day), but the Step 1 event was being emitted twice for a subset of flows in US-East due to a console/auth edge case.
  - EU-West had fewer duplicates, so the “conversion rate” (step2/step1) looked artificially worse in EU-West when comparing regions.
  - Additionally, the dashboard query used a join that unintentionally filtered some EU users when event_time skew occurred near midnight UTC (session boundary + region bucket), amplifying the appearance of a regional issue.

Root cause
- Duplicate emission of signup_created/signup_completed for users who hit both (a) email verification completion and (b) immediate console onboarding flow that retriggered the signup event. This was more common in US-East due to traffic mix and a feature-flag exposure path.
- Dashboard query logic for Step 1 + Step 2 used inconsistent dedupe keys (Step 1 deduped by user_id/day; Step 2 deduped by event_id) and a region/date join condition that excluded a portion of EU events at boundary times.
- Net effect: inflated Step 1 counts in US-East and undercounted Step 2 in EU-West in the visualization layer, while the warehouse raw events were largely correct.

Resolution
- Engineering fix: PR-28521 shipped to stop duplicate signup event emission; verified by before/after comparison on a canary cohort and then full rollout.
- Analytics fix: updated Activation Funnel panel query to use consistent dedupe (event_id preferred, fallback to (user_id, event_name, request_id) for older records) and removed the join condition that filtered EU events at UTC boundaries.
- Backfill: no backfill required for canonical fact tables; dashboard now recomputes accurately from warehouse. Noted that historical conversion rates for 2026-01-19 to 2026-01-22 should be interpreted with caution; we annotated the dashboard.

Validation
- Post-fix checks (2026-01-26):
  - Regional conversion rates are within expected variance (eu-west no longer showing step-change).
  - New user counts align within ~1–2% between auth table and deduped signup events.
  - Funnel step drop-offs align with expected product behavior and match secondary metrics (API key creation table).

Follow-ups
- Add a data-quality alert: spike in duplicate rate for signup_created and api_key_created by region.
- Add unit tests/contract tests for event emission idempotency in console/auth flows.
- Document dedupe keys and “source of truth” definitions in the activation metrics notes + dashboard README.

Stakeholders
- Growth: Ben Carter (experiment owner), Tyler Benson (attribution)
- Product: Marissa Cole (console), Paula Mendes (telemetry/rollouts)
- Eng/Analytics: Logan Wright (assigned), Nadia Rahman, Mei Lin

References
- Slack: #help (tracking discrepancy), #eng-platform (taxonomy + dedupe)
- Related PRs: PR-28431, PR-28521, Observability Pack PR-241
2026-01-22 10:18 UTC — Allison Grant (Reporter): Flagging as INT because this is blocking lifecycle sprint measurement. Dashboard shows eu-west signup→api_key_created down ~15% vs yesterday; warehouse counts don’t match. Linking Slack thread from #help where Growth asked who can debug regional missing events.
2026-01-22 12:05 UTC — Logan Wright (Assignee): Acknowledged. Pulling collector + warehouse comparisons for eu-west vs us-east. Initial glance: no obvious collector ingestion lag; going to compare dedupe rates by region for signup_created.
2026-01-22 14:40 UTC — Mei Lin: In Snowflake, api_key_created counts by region look stable; signup_created seems inflated in us-east starting 1/21 evening. Suspect duplicate emission rather than eu-west loss. Can share query if needed.
2026-01-22 16:10 UTC — Nadia Rahman: I see two signup events per user for a subset with the same user_id but different request_id. Likely from console onboarding + auth verification both firing. Repro attempt ongoing; will coordinate with Dylan/Chloe.
2026-01-23 09:30 UTC — Logan Wright: Confirmed: funnel visualization is using inconsistent dedupe keys across steps and an extra join that drops some eu-west events around UTC day boundary. Short-term mitigation: pause region comparison in readouts; use warehouse deduped table for activation rate until we patch dashboards.
2026-01-23 13:55 UTC — Dylan Brooks: We can patch duplicate event emission quickly. There’s a known console/auth edge case where the signup event fires twice after verification redirect. Will ship fix behind a small canary first.
2026-01-24 11:12 UTC — Logan Wright: PR-28521 opened to fix duplicate signup emission; requesting fast review from platform + console owners. Once merged, we’ll update dashboard query to use event_id-first dedupe and remove the problematic join.
2026-01-25 18:20 UTC — Logan Wright: PR-28521 merged + deployed. Duplicate rate on signup_created dropped from ~7–9% to <0.5% in us-east within 2 hours. Updating Observability Pack funnel query now; will annotate dashboard for the impacted window.
2026-01-26 09:05 UTC — Sergio Costa: Dashboard panels updated; verified against Mei’s warehouse query. EU-West conversion no longer shows the step-change. Added a note on the dashboard for 1/19–1/22 data interpretation.
2026-01-26 09:30 UTC — Allison Grant: Closing. Please add follow-up to create an automated alert on duplicate event rates by region; this should be caught before Growth sees it in readouts.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_140d90d0c1af492a89a8f6e52230ae5d` — Postmortem: EU API latency and elevated 5xx (edge routing cache)
2. `dsid_0f4afe0e4f4c467bb33500c021f2f394` — Storm Harbor AI
3. `dsid_d3edd63b9ec54523ad12bd9be3d7e996` — Postmortem: EU-West capacity shortage and region fallback (2025-03-03)
4. `dsid_87fcd4642ef645919bb04b48e043a0c7` — Copper Harbor Assistants
5. `dsid_c9728b8229b84c9a9a1c61f51a31c930` — Sparkwell Lumenify
6. `dsid_5262d75d9e954e94b2cb2f73387196b5` — CopperClasp Onboarding
7. `dsid_b48d3d3042e846059fcde82a3ae771ab` — Amberwell Assistify
8. `dsid_f1c8b96a990145038be9e21d4275af61` — Aftershock: failover oscillation and aggressive shedding during cross-region surge
9. `dsid_1736ae85d6ca46deab8d7b192f551c18` — Little Owl AI Tools
10. `dsid_5165a7e247c4402598a0005b092aa4b6` — Velvetloom Digital

### Fill for this row (also include in final JSON array)

```
row_id: 57
question_id: qst_0349::project_related
corpus_scale_size: 75000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 58

- **row_id:** `58`
- **question_id:** `qst_0391::constrained`
- **corpus_scale_size:** `25000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In the hosted API incident in late April 2026 where streaming requests started returning 502/504 and non-streaming requests also saw a sharp tail-latency increase, what was the underlying trigger (involving an edge keepalive/connection-TTL change) and what immediate mitigations were used to restore service?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_0b0595a6d39247ada6238d8311b587f8`
_source: full_erb_file:dsid_0b0595a6d39247ada6238d8311b587f8__streaming-write-stall-ttl-regression-postmortem-2026-04-25.txt_

```text
Streaming write-stall + TTL regression — hosted API outage postmortem (2026-04-25)

Summary:\n\nOn 2026-04-25 at ~02:12 UTC the hosted streaming API experienced a high-severity outage that manifested as 5xx errors for streaming sessions and extreme tail latency for non-streaming requests. Impact lasted ~43 minutes for customers on affected regions and degraded for another 90 minutes during mitigation rollouts. Root cause: an unintended change to a per-connection TTL/keepalive config combined with an edge buffer write-stall bug in the streaming proxy, which caused head-of-line stalls and backlog amplification under normal traffic spikes.\n\nImpact:\n- Scope: ~11% of streaming sessions experienced repeated 5xx (502/504) immediately; additional ~7% of non-streaming requests saw 95th+ latency spikes from 600ms -> 3.2s.\n- Customers: 23 enterprise tenants saw visible error rates; a handful of PLG customers reported degraded developer experience. No data loss or model correctness issues were observed.\n- Business: Incidents triggered PagerDuty P0 and on-call SREs initiated incident response. External status page was updated.\n\nHow it was detected:\n- First alert: custom anomaly detector on streaming session error-rate crossed threshold at 02:13 UTC (SRE paging).\n- Secondary signals: edge response-time dashboards and increased connection resets observed in edge logs.\n- Pager: 02:14 UTC, SRE lead ack at 02:15 UTC.\n\nTimeline (UTC):\n- 02:12 — initial spike in streaming session errors; error rate rose from baseline 0.3% to 18% in 2 minutes.\n- 02:13 — anomaly alert fires; on-call SRE starts investigation.\n- 02:14 — correlating logs show write stall metrics on streaming proxy (high write queue depth).\n- 02:18 — quick mitigation: rolling restart of streaming-proxy fleet in affected region, partial drop in errors but tail latency persisted.\n- 02:25 — rollback of a recent edge-config change that adjusted connection TTL made at 01:55 UTC. Edge config rollback began.\n- 02:35 — error rates fall to ~2%; tail latency trending down but not fully recovered.\n- 02:55 — full rollback complete and additional throttling rules temporarily applied; streaming success rates returned to baseline.\n- 03:00 — status page updated to reflect mitigation progress.\n- 04:30 — follow-up remediation runs and validation; monitoring shows stable behavior. Incident declared mitigated at 04:35.\n\nRoot cause analysis (why):\n- Primary bug: an existing bug in streaming-proxy write handling where a stalled TCP write (EAGAIN/later drain) could leave per-connection buffers frozen while the proxy's internal queue accounting incorrectly marked the connection as writable. This allowed the proxy to continue accepting streaming state and buffer memory without advancing network writes, producing head-of-line stalls.\n- Trigger: a separately deployed edge config tweak at 01:55 UTC reduced keepalive/TTL for upstream connections from 90s -> 10s to aggressively free idle connectors for recent scaling changes. This increased connection churn during normal traffic bursts and surfaced the proxy write-stall bug.\n- Amplification: the serving runtime's KV cache prefetch caused more concurrent active streaming sessions per process during a traffic spike at 02:10 UTC, compounding queue depth and memory pressure on streaming-proxy workers.\n\nContributing factors:\n- A config change (edge TTL) was rolled without a targeted canary to measure streaming-specific impact.\n- The proxy bug existed in the binary for ~3 months but was low-probability; normal workloads had not triggered it at scale.\n- Alerts were configured for absolute error-rate thresholds but not for queue depth or write stall latency in the streaming-proxy.\n- Rollback of edge-change required coordination across teams and took longer than expected because the change was bundled with other minor fixes.\n\nImmediate remediation performed:\n- 02:18 — rolling restart of streaming-proxy processes to clear stuck write buffers (short-term relief).\n- 02:25 — rollback of edge TTL config to previous value (90s).\n- 02:55 — deploy temporary traffic shaping: soft concurrency limit per upstream instance and reject-new-session policy for overloaded proxies.\n\nLonger-term fixes and planned actions:\n(Planned timeline + owner)\n- Fix proxy write-stall bug in runtime and add explicit writeback checks (PR: runtime#657). Owner: Miguel Torres. ETA: 2026-05-03.\n- Add unit+integration tests that simulate partial write backpressure and verify buffer accounting. Owner: Juno Kim. ETA: 2026-05-10.\n- Update deployment practices: require streaming-sensitive canary (1% traffic for 30m) for edge/TCP-level TTL or connection lifecycle changes. Owner: Priya Raman (edge infra). ETA: 2026-05-01.\n- Implement alerting for streaming-proxy write-queue depth and per-connection write latency (new SLI). Owner: Liam O'Connor. ETA: 2026-04-30.\n- Run a chaos experiment to model connection churn under reduced TTLs to ensure proxy resilience. Owner: Evelyn Zhang. ETA: 2026-05-07.\n\nRunbook and playbook changes (immediate edits):\n- Add a new streaming runbook section: \"Detect and mitigate write stalls\" including commands for probing write queue depth, safe rolling restart procedure, and temp traffic shaping knobs. Owner: Ana Patel. Actioned: draft added to Confluence, see linked runbook.\n- Add step that any edge-level connection/TTL changes must include a streaming-canary approval checkbox. Owner: Priya Raman.\n\nMonitoring & alerts to add/modify:\n- New alert: streaming-proxy.write_queue_depth > 500 for > 2m -> P1.\n- New alert: streaming-proxy.per_conn_write_latency_p95 > 1s -> P1.\n- Adjust anomaly detector to correlate streaming error-rate with write-queue depth before auto-scaling decisions.\n- Dashboard: new streaming health panel with per-region metrics: conn churn, write queue depth, buffer memory, and per-second stream accepts.\n\nCustomer communication:\n- At 02:20 UTC we published a short status page update.\n- Post-incident public note to affected tenants drafted and queued for account team review. Owner: Customer Success (cc: Ana Patel). ETA for send: 2026-04-27.\n\nAction items (owner — due):\n- Miguel Torres — land runtime fix and coordinate canary release (2026-05-03).\n- Juno Kim — add integration tests and run pre-merge CI scenarios (2026-05-10).\n- Priya Raman — update edge deployment checklist + canary gating (2026-05-01).\n- Liam O'Connor — implement monitoring alerts + dashboard (2026-04-30).\n- Evelyn Zhang — run chaos/connection-churn experiment and share findings (2026-05-07).\n- Ana Patel — finalize runbook writeup and schedule SRE runbook walk-through (2026-04-29).\n\nLessons learned / retrospective notes:\n- Low-probability bugs can become high-impact when paired with seemingly innocuous config changes (keepalive/TTL tweaks).\n- Edge-level changes touching connection lifecycle must be treated as high-risk for streaming customers; they require a streaming-aware canary path.\n- Having more fine-grained streaming proxy SLIs (queue depth & per-conn write latency) would have accelerated detection and reduced MTTR.\n- Rolling restarts are effective short-term mitigation but we need faster rollback paths for edge configs (decouple TTL change from unrelated cleanup fixes).\n\nAppendix (commands and quick diagnostics):\n- Check streaming proxy write queue depth: \n  - curl -s http://proxy-metrics/metrics | grep write_queue_depth | awk '{print $2}'\n- Live tail to detect stuck writes: \n  - ssh proxy-node && sudo journalctl -u streaming-proxy -f | grep \"write stall\"\n- Safe rolling restart (recommended): \n  - kubectl rollout restart deployment/streaming-proxy -n hosted-api --selector=region=<region> --max-unavailable=2\n\nDocument history:\n- Drafted: 2026-04-25 by Ana Patel\n- Updated with timeline & remediation 2026-04-26 by Miguel Torres\n- Final review notes added 2026-04-27 by Priya Raman\n\nIf you have questions or need clarifications on any section ping #sre-incident or @ana.patel on Slack.\n
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_5f884c5669194d698c0be56a1df92b33` — Persistent 5xx spike after TLS handshake delays led to streaming fallback loop and API gateway throttling
2. `dsid_966a7c4df170438c8ce53f99d9f5a12d` — In-flight header growth + edge proxy slow-flush causing delayed TTFB and intermittent 502/504 for streaming completions
3. `dsid_9cfb4812f31542038a01ee9329290d01` — Edge connection-hold flood from long-lived keepalive clients causing 5xx spike and runtime CPU pressure for dedicated tenant
4. `dsid_b9e867d7f1614b118214334b9ae82405` — Gateway buffer pressure from long-polling sessions causing intermittent 5xx pulses
5. `dsid_08ad719d23bb43e4a66b6e52fa079c0b` — Intermittent high TTFB and 504s caused by proxy write stalls when request-metadata headers grow during streaming
6. `dsid_20da692d9b2e4db98d4c410dd70c85b4` — Intermittent TTFB regressions for streaming completions when API gateway connection reuse interacts with proxy buffering
7. `dsid_5dfe1a03b30b4e728de8fa999bdf88dd` — Intermittent 5xx spike from delayed HTTP/2 ACKs causing streaming sessions to half-close and upstream restarts
8. `dsid_73bbb963f3f04ef09e110be84f50d1e1` — HPACK header-table mismatch in edge proxy causing intermittent 5xx for long-lived streaming sessions
9. `dsid_6e0a74dab08c4a1ab3d31ae2752e668b` — Edge proxy connection stall from slow chunked uploads and header growth causing delayed TTFB for long completions
10. `dsid_1e20852dbc9d4a9192a7b8a393f65133` — 502/503 surge at edge during short-lived streaming bursts causing elevated error rate for dedicated customer

### Fill for this row (also include in final JSON array)

```
row_id: 58
question_id: qst_0391::constrained
corpus_scale_size: 25000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 59

- **row_id:** `59`
- **question_id:** `qst_0423::conflicting_info`
- **corpus_scale_size:** `100000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

For the office keycard audit, how many months of access logs should we export?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_03b2db544a6d4cf886fb9869058a05f2`
_source: full_erb_file:dsid_03b2db544a6d4cf886fb9869058a05f2__INT-2043-office-inventory-keycard-audit-and-disposal-request.txt_

```text
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
- Some badge IDs show up in access logs in 2024 despite being physically in lost-and-found; need cross-check against HR termination list and replacement cards.
- Facilities prefers completion before holiday break; if we slip, we should at minimum complete the keycard deprovisioning and isolate data-bearing media.

Links / artifacts
- Initial scan (older): drive:/shared_drives/operations/office-inventory/initial-scan.csv

If any item is sensitive (hard drives, HSM parts, private compute media) escalate to Security and open a separate INT ticket with chain-of-custody notes.
2025-11-13 - Maya Chen (Reporter): Filed as INT so Facilities/Security can track this centrally. Prior linear tracker reference: ENG-4721.
2025-11-14 - Omar Singh (Assignee): Spoke with Security; they want a 12-month access export first. They also want any "found" keycards photographed (front/back) before destruction. Will coordinate export + deprovision list.
2025-11-15 - Facilities Bot: Storage sweep time moved to 2025-11-19 10:30 (3A storage room). Please RSVP so we have enough labelers and carts.
2025-11-19 - Omar Singh (Assignee): Sweep completed. ~37 items logged, 6 marked for Security review (possible data-bearing). Draft disposal list prepared; waiting on Facilities approval for donation vs recycle for monitors with no asset tags. Starting keycard cross-check next.
2025-11-19 - Maya Chen (Reporter): Added new CSV column "notes" to capture condition + missing power supplies. Please ensure we do not dispose of anything with storage media until Security signs off.
```

#### GOLD `dsid_c5288dd4874345adb80f4a71c9a18773`
_source: full_erb_file:dsid_c5288dd4874345adb80f4a71c9a18773__ENG-4721-misc-chores-office-inventory-and-keycard-cleanup.txt_

```text
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

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_a7e036d237404f23991aaef36997406f` — eng-security
2. `dsid_dea9de3e5e904e4aa4e173e254e785c7` — Audit & access log TTLs, export formats, and customer-driven deletion walkthrough
3. `dsid_33b8ef3fa0134aec892debb7dcaae434` — Bulk audit log delivery and security assertions for upcoming vendor audit (SIEM ingestion + AUP attestation)
4. `dsid_a7cdd5969e4043c68b02f1b8ed6a4487` — eng-security
5. `dsid_abef073a060547cc9d242425f89be3e2` — Access authority request: timeboxed prod log segment for external privacy assessor
6. `dsid_67677fea63eb416b9f2023f09d329302` — Orion Compliance Networks
7. `dsid_ae3841f2fcc84484bdcb89dcdb66874e` — Customer session export + compliance SOP for third-party audit request
8. `dsid_fafcd864f11843a28182c451fe0e5a61` — customer-success
9. `dsid_2f6f2eb442c9423993d657259b4fcee3` — Prod API-key usage trace provisioning request for regulatory billing review
10. `dsid_325127fefd874655adaeb228f5353682` — Forensic playback export, chain-of-custody manifest and HSM key-rotation attestation for eDiscovery

### Fill for this row (also include in final JSON array)

```
row_id: 59
question_id: qst_0423::conflicting_info
corpus_scale_size: 100000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 60

- **row_id:** `60`
- **question_id:** `qst_0444::completeness`
- **corpus_scale_size:** `10000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`lexical_mismatch`

### Question

What is Redwood Inference's end-to-end internal process for launching a new third-party LLM into the Hosted API model catalog-from intake to post-launch monitoring-including every required gate, owner, and artifact?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_117e5a150aa94adc86295786bd6b7843`
_source: full_erb_file:dsid_117e5a150aa94adc86295786bd6b7843__hosted-api-model-intake.txt_

```text
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
   - Artifact: link to Security risk review page entry (see Security space)
2. **Baseline evaluation plan** (Owner: Applied ML)
   - Outcome: evaluation suites selected + success criteria
   - Artifact: eval plan comment in Linear + link to eval harness run(s)
3. **Feasibility / runtime fit** (Owner: Serving Runtime)
   - Confirm tokenizer handling, KV cache behavior, and kernel coverage
   - Artifact: short feasibility note + any required runtime flags

# Artifacts produced during intake (and where they live)
- Model intake summary: Linear ticket (single source of truth)
- Eval plan + results: Eval harness run links and Confluence (Applied ML and Evals)
- Performance benchmark results: Confluence Performance Standards page + attached benchmark run IDs
- Quantization plan/results: Confluence Quantization Profiles space
- Security risk review: Confluence Security & Compliance space
- Rollout plan and fallback: Confluence Eng Platform runbook
- Model registry change: GitHub PR in `redwood-model-registry`

# Definition of “ready for implementation”
A model is ready to move from intake to implementation when all of the following are true:
- License is approved (or approved with documented restrictions)
- Eval plan includes at least one internal prompt set and one public benchmark
- Runtime owner has stated no known blockers
- A rollout owner is named (release + platform)

# Related pages
- Eval gates for model launch (Applied ML and Evals)
- Hosted model performance bar (Architecture and Standards)
- Quant profile requirements for catalog (Applied ML and Evals)
- Third-party model risk review workflow (Security and Compliance)
- Hosted model rollout and fallback runbook (Eng Platform)
```

#### GOLD `dsid_2ad75f27c36b492f847d5b9c63492e4b`
_source: full_erb_file:dsid_2ad75f27c36b492f847d5b9c63492e4b__hosted-model-rollout-and-fallback.txt_

```text
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
- Increase to 5% in us-east-1, then add eu-west-1, then ap-southeast-1 (if applicable).
- If the model is replacing a default/alias, keep the old model as the first fallback for at least 7 days.

## 5) GA and documentation
- When traffic reaches 100% for the intended routes, mark the Linear ticket as `shipped`.
- DevEx must publish docs updates with:
  - model ID, default settings, limitations, and restriction text (if any)

# Fallback and rollback
## Fallback policy (required)
Each new catalog model must specify:
- Primary: new model ID
- Fallback #1: previous stable model in same family
- Fallback #2: cross-family safe default (product-approved)

## Rollback triggers (examples)
- Sustained TTFT p95 regression > 20% vs baseline for 30 minutes
- Elevated 5xx > 0.5% for 10 minutes
- Confirmed quality regression on `p0` prompts post-launch

## Rollback steps
1. Disable routing rule for new model (set weight to 0)
2. Promote fallback #1 to 100%
3. Notify #incidents if customer-impacting; otherwise update #eng-releases
4. File post-incident ticket referencing dashboards and logs

# Post-launch (first 7 days)
- Keep canary/quality shadowing enabled where possible
- Watch for:
  - tokenizer edge cases (stop sequences, special tokens)
  - intermittent OOMs due to KV cache fragmentation
  - higher-than-expected safety blocks (policy tuning may be needed)

# Related pages
- Hosted API model intake
- Model launch evaluation gates
- Hosted model performance bar
- Third-party model risk review workflow
```

#### GOLD `dsid_40471ba4cd3b430eab3ac0877eef0972`
_source: full_erb_file:dsid_40471ba4cd3b430eab3ac0877eef0972__third-party-model-risk-review.txt_

```text
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
- Link the exception record in the Linear model intake ticket and in the GitHub model registry PR.

# Related pages
- Hosted API model intake
- Hosted model rollout and fallback runbook
```

#### GOLD `dsid_5cde26f232454906879617dab1800fae`
_source: full_erb_file:dsid_5cde26f232454906879617dab1800fae__model-launch-eval-gates.txt_

```text
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
A launch packet must include:
1. Eval harness run URLs for all required suites
2. A one-paragraph risk assessment (what could go wrong in prod)
3. A recommended default inference config (temperature/top_p/max_tokens defaults)
4. Known limitations (e.g., cannot do reliable tool calling; poor multilingual)

# Escalations and exceptions
- Exceptions must be approved by the Applied ML gate owner and recorded as a label `eval-exception` on the Linear ticket.
- If Suite A fails on any `p0` prompt, do not ship.

# Post-launch monitoring requirement
For the first 7 days after GA:
- Enable quality canary (1% traffic shadow to baseline, where possible)
- Watch `quality_regression_alerts` dashboard and error budget burn
- File a follow-up ticket if any metric crosses thresholds (see Platform runbook)

# Related pages
- Hosted API model intake
- Hosted model performance bar
- Hosted model rollout and fallback runbook
```

#### GOLD `dsid_92d0d471ddc941288bcb51b3ded6ec36`
_source: full_erb_file:dsid_92d0d471ddc941288bcb51b3ded6ec36__hosted-model-performance-bar.txt_

```text
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

# Related pages
- Model launch evaluation gates (Applied ML and Evals)
- Quant profile requirements for catalog (Applied ML and Evals)
- Hosted model rollout and fallback runbook (Eng Platform)
```

#### GOLD `dsid_d8d194e311b9482cb38c61134b6d26fa`
_source: full_erb_file:dsid_d8d194e311b9482cb38c61134b6d26fa__quant-profile-requirements-for-catalog.txt_

```text
Quant profile requirements for Hosted API catalog models

# Overview
This page defines the minimum set of quantization profiles and validation checks required for a model to be eligible for the Hosted API catalog.

# Why we require multiple profiles
Hosted traffic varies significantly by latency sensitivity and context length. Having pre-validated quantization profiles ensures we can route cost-sensitive workloads without surprise quality regressions.

# Required profiles (per model)
For every new catalog model, you must produce and validate *at least* the following profiles:
- `fp16` (reference)
- `int8-weight-only` (cost-optimized)
- `int4-weight-only` (when supported by kernels/hardware; if not supported, document as N/A with Runtime owner signoff)

# Validation checks (required)
Each profile must pass:
1. **Correctness smoke** (Owner: Serving Runtime)
   - Generate determinism check (same seed, same output distribution tolerance)
   - Tokenizer round-trip sanity
2. **Quality delta check** (Owner: Applied ML)
   - Run Suite A from "Model launch evaluation gates" on `fp16` and on the candidate default profile
   - Pass criteria: no `p0` regressions; overall win-rate delta vs fp16 >= -5%
3. **Performance check** (Owner: Serving Runtime)
   - Meet the "Hosted model performance bar" thresholds for the default profile

# Default profile selection
- Default should be the fastest profile that passes the quality delta check and meets TTFT p95 targets.
- If `int4` passes but shows > 2% increase in error rate under load, do not ship `int4` as default.

# Naming and registry requirements
- Profile names must match the runtime config keys used by the model registry.
- The model registry PR must include the profile list and indicate which is default.

# Required artifacts
- Link to quant build logs (Drive)
- Eval harness run links for fp16 and default
- Perf suite run IDs for default

# Exceptions
Exceptions require:
- Runtime owner signoff (why kernel support is missing) and
- Applied ML signoff (why quality risk is acceptable)
Recorded on the Linear ticket with label `quant-exception`.

# Related pages
- Hosted API model intake
- Model launch evaluation gates
- Hosted model performance bar
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_d705b886ca6c4aa9854dc193043a3963` — Inference Platform Sales Brief — Developer & Enterprise Messaging
2. `dsid_7715a1d6ffa047389f4ea1bf862bb9ff` — Lodehaven RerankWorks
3. `dsid_c7cff0205a3844bb90782190a42a390b` — VouchLaw Digital LLC
4. `dsid_713b7766c60948e7b9b30bfc3008df4d` — Channel Partner Win Playbook: Technical Value, Pricing & Security Matrix
5. `dsid_69e0d85cdd4443b8b38f285dd39bf940` — Lighthouse Archive Search
6. `dsid_58da53c74d2d4dbab0f19661d4f8eda3` — QueryHarbor KB Solutions
7. `dsid_b414948508a24e8ca0df504dd7944601` — Partner Technical & Commercial Onboarding Guide
8. `dsid_06464e95b7cc44de8a9677f3260c336e` — Platform Brief: SaaS GTM — Inference Value Metrics & Battlecards
9. `dsid_09153a5878ee4614abb9a0522549b508` — AspenField Analytics Labs
10. `dsid_1fb32aada9624d7c862713bfec09e2a1` — Oakridge SlateWorks

### Fill for this row (also include in final JSON array)

```
row_id: 60
question_id: qst_0444::completeness
corpus_scale_size: 10000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 61

- **row_id:** `61`
- **question_id:** `qst_0448::completeness`
- **corpus_scale_size:** `75000`
- **condition:** `meta`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

Which customers have been granted an exception to Redwood’s default inference request log retention policy, and what retention period was approved for each?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_5f0ab47fe8de47a89bb6668f8722becf`
_source: full_erb_file:dsid_5f0ab47fe8de47a89bb6668f8722becf__20251022-quantagov-logging-retention-questionnaire.txt_

```text
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

 Olga
```

#### GOLD `dsid_67a8c3300752435296938175e9a1daf5`
_source: full_erb_file:dsid_67a8c3300752435296938175e9a1daf5__helio-health-log-retention-addendum.txt_

```text
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
_source: full_erb_file:dsid_6933f9241ef140da9d3bf98be52be867__INT-1974-log-retention-exception-quantagov.txt_

```text
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
_source: full_erb_file:dsid_84ec014ad9f14f1481b45484da41181a__20250212-northstar-log-retention-confirmation.txt_

```text
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
_source: full_erb_file:dsid_b72bd7e0c91a4f8c9d9a13daf6ff3d28__1739276405-northstar-no-payload-logging.txt_

```text
eng-security

Aisha Rahman: Need quick approval: Northstar Bank (Dedicated) wants *no prompt/completion logging* + metadata only for 30d. Blocking go-live. Any issues?

Priya Natarajan: Approved. Set payload retention to 0 (dont persist prompts/completions). Metadata retention 30d is fine. Please record in INT ticket + exception register. :thumbsup:

Alex Martinez: Cool. Ill implement via log pipeline drop + TTL override. Will post verification.

Hannah Schmitt: +1. Make sure customer acceptance is captured (email) and link it in INT-1842.
```

#### GOLD `dsid_b793b06789ae4147884e94681c6beae1`
_source: full_erb_file:dsid_b793b06789ae4147884e94681c6beae1__INT-1907-log-retention-exception-helio-health.txt_

```text
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
_source: full_erb_file:dsid_e91e68b31a6f4935b87d6f74dd07e1f6__INT-1842-log-retention-exception-northstar-bank.txt_

```text
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

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_5a060c16f9e943dfb6556b74d1bee39e` — Re: Redwood Inference security review: retention & deletion timelines
2. `dsid_f7d5fea86ebc4266abc8a92f79b93565` — Clarify: default retention for prompts vs inference outputs
3. `dsid_97200e6e3c2b4062a8cb3c13047a464c` — Retention granularity & customer-held logs: workflow and attestation
4. `dsid_615b95b58757481a96975cbe5ea4f65c` — Storage horizon primer — concrete examples for requests vs. results
5. `dsid_107b32582f064c0481b84fcc630e026c` — Clarifying Redwood default log retention, residency, and delete options
6. `dsid_a1f5902940664452bd4113c082397954` — Clarification on non-training guarantee and retention edge cases
7. `dsid_b872e1fd54d94b0488655e58d71d814f` — Conditional archive escrow and TTL alignment discussion
8. `dsid_ac17673b4827489cbc0c55136fb48d8b` — Data governance: triage for Sigma Health audit log / retention asks
9. `dsid_dffa4ad88a014af1afda8e2835666e85` — Preserving logs during incident — data retention & hold request
10. `dsid_23f5d21106034c2c9c442e8871fa7a4c` — SIG: audit log export formats + delivery options

### Fill for this row (also include in final JSON array)

```
row_id: 61
question_id: qst_0448::completeness
corpus_scale_size: 75000
condition: meta
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---

## Row 62

- **row_id:** `62`
- **question_id:** `qst_0470::miscellaneous`
- **corpus_scale_size:** `100000`
- **condition:** `raw`
- **auto_hit_at_10 (L1):** `MISS` (`False`)
- **gold_id_in_retrieved_top10:** `False`
- **gold_rank_if_hit:** `None`
- **LLM triage (ignore if conflicting):** label=`n` mode=`embedding_near_miss`

### Question

In a backend inference engineer interview about multi-tenant GPU scheduling, what strategy did the candidate propose to reduce cold misses for growing attention cache in long chat histories?

### Expected gold document(s) — FULL TEXT

#### GOLD `dsid_aea4790d4bcc45859208d7d705f682a1`
_source: full_erb_file:dsid_aea4790d4bcc45859208d7d705f682a1__2026-03-21-interview-jordan-lee.txt_

```text
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
[01:45] Priya: How would you incorporate KV cache behavior? For large chat histories the KV cache grows — what tradeoffs do you consider?
[01:55] Jordan: If the KV cache (kay-vee cache) is per-model shard, you want to minimize cold-cache misses. Techniques: pin recent active conversations to same GPU, use LRU eviction tuned by sequence length, and optionally offload cold-kv to host memory with on-demand fetching. But that increases latency, so prefer sharding customer affinity.
[02:20] Priya: What about memory-limited GPUs; how would you handle quantized models and cache memory?
[02:28] Jordan: Quantization reduces model size but KV cache still consumes a lot. I'd explore 4-bit quantization for weights and mixed precision for activations. For KV caching, you could compress keys or use 8-bit storage for cached kv pairs; there's a tradeoff with decode cost. Also tiered caching: hot kv stays on GPU, warm kv on fast host RAM, and cold kv in a slower store.
[02:55] Samir: Do you have experience with specific quantization libraries or tooling?
[03:00] Jordan: I've used bitsandbytes for 4-bit and a custom offline quantizer for 6-bit experiments. I haven't used Redwood-specific tooling but I worked on a similar stack at OpenEmbeddings.
[03:12] Priya: Cool. Follow-up: suppose a customer sends 200 concurrent short requests — how does your scheduler avoid head-of-line blocking?
[03:22] Jordan: Use priority lanes and per-customer concurrency limits. Implement fairness via weighted round robin between tenants and preemption for high-priority requests. Also allow small fast-path shards that bypass large batching windows.
[03:35] Samir: You mentioned preemption — how do you implement preemption at the GPU kernel level?
[03:41] Jordan: Full kernel preemption is hard; prefer request-level scheduling: if a queued large batch is waiting, you can reorder queues before dispatch, or split large batches into smaller micro-batches. Use CUDA streams to overlap work where possible, though synchronization is tough.
[03:58] Priya: Let's pivot to a whiteboard: design a scheduler that decides which model variant to route to when capacity is constrained — e.g., you have full-precision, quantized, and distilled variants.
[04:10] Jordan: Okay — objective: maximize throughput while meeting latency SLOs and minimizing cost. Have a multi-armed routing policy that considers: estimated latency on variant, quality delta, customer tier, and current load. For each request compute expected utility = quality_weight*quality - cost_weight*latency_estimate and pick highest utility under SLO constraints.
[04:45] Samir: How do you estimate latency for a given request?
[04:49] Jordan: Use a learned model or empiric histograms: features include sequence length, batch size, model variant, and GPU utilization. Keep online calibration.
[04:58] Priya: Any thoughts on rollback/fallback if quality regressions happen?
[05:02] Jordan: Maintain a canary pool and do shadow traffic to evaluate quality metrics. If regressions detected, fallback to next-best variant and trigger alerts. Also use prompt-level checks where applicable.
[05:15] Samir: Let's surface an ambiguity: how do you measure 'quality' programmatically?
[05:20] Jordan: Use task-specific metrics — perplexity for language models, BLEU/ROUGE for summarization, or cosine similarity for embeddings. For chat, may need human evaluations or downstream signal like user satisfaction.
[05:35] Priya: Good. Quick behavioral: tell us about a time you had an incident in production and how you resolved it.
[05:42] Jordan: At my last role we had a GPU OOM cascade after a recent release that increased sequence-length handling. Root cause was a regression in a padding calculation that duplicated KV entries. We mitigated by throttling ingress and rolling back the deploy, then patched the padding logic and added e2e tests for long sequences.
[06:05] Samir: Nice. Any telemetry changes you added?
[06:08] Jordan: Added a long-tail sequence length histogram, per-request KV size metric, and an alert when average KV per request exceeded threshold.

[06:20] Priya: We're about halfway; let's do a short coding/design exercise: outline an API and data model for a take-home that tests batching logic. What would you ask?
[06:30] Jordan: I'd ask them to implement a simple router that ingests requests with (tenant_id, priority, expected_tokens) and outputs batch assignments with a max batch size and max wait. Provide a simulator of incoming load and assert latency percentiles under different scenarios. Also include unit tests for edge cases like starvation.
[06:50] Samir: How would you validate correctness and fairness?
[06:54] Jordan: Validate with synthetic workloads, check p50/p95 latency per tenant, and enforce per-tenant concurrency caps. For fairness, compute Jain's fairness index across tenants' latencies.
[07:10] Priya: Perfect. Final 10 minutes for candidate questions. Anything you'd like to ask us?
[07:16] Jordan: Yeah — how tightly coupled is the inference runtime to the control plane? Are rollouts handled automatically by the platform or handled by SRE?
[07:26] Priya: Our platform provides routing policies and rollout primitives, but SRE owns infra-level rollouts and emergency fallbacks. Engineers can set policies in the control plane and manage model variants.
[07:38] Jordan: Nice. Also curious about hybrid on-prem/private deployments — do teams usually run the same runtime?
[07:44] Samir: Yes, same runtime with optional private deployment packaging; differences are in networking and key management.

[07:52] Priya: Thanks Jordan. We'll send a take-home exercise; expect it by Tues. Any final notes?
[07:58] Jordan: No, thanks for the thoughtful questions.

Notes: transcript contains some disfluency and occasional word substitutions (kay-vee for KV). Action: Priya to send exercise. End of transcript.
```

### Retrieved top-10 (IDs only; ★ = gold)

1. `dsid_8dc419eccd7744939b1ee86da30e078d` — Foreground/Background Cache Thaw Investigation — personal scratchpad
2. `dsid_a408d0c23fe14754a036e2d2f12be9ad` — Nanopause context-switch penalty — exploratory logs
3. `dsid_43dc7bb3227b4897b1ed21a6b838c647` — Hot/Cold prefix stratification and GPU page-aware eviction hints for continuous batching
4. `dsid_5edb76bdee774249af7a01dacb69b3c6` — eng-platform
5. `dsid_aa8906c3e0b34f8697dd3db42c875fa2` — Context-cache tiered quantization + routing probe (FP8/INT8/INT4) with continuous-batching interaction
6. `dsid_80992442edfa4cdeac127d5e38c93548` — Zenara Inference Ops
7. `dsid_13f943e69e174ec598db02603ddc82c0` — memory-fragmentation-lit-scraps-rina-kapoor
8. `dsid_b8e8babc72c443b9a0469590ce3fbf62` — Stratix Inference Group
9. `dsid_562322d06ecd48409b91c0f84852b393` — memory-pressure-backpressure-arch-deepdive-notes
10. `dsid_ca7dee5f843c4011aed8e515e08dbe47` — SummitRidge Logistics AI

### Fill for this row (also include in final JSON array)

```
row_id: 62
question_id: qst_0470::miscellaneous
corpus_scale_size: 100000
condition: raw
auto_hit_at_10: false
gold_answers_question: true|false
human_label_correct: y|n|unsure
human_failure_mode: null|label_noise|...
answer_span: "..."|null
human_notes:
```

---
