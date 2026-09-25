# LLM L4 Audit Report

_Generated 2026-09-20T21:56:30.472021+00:00_

- Model: `qwen2.5:7b-instruct`
- Report stem: `llm_audit_report_ollama`
- Evaluated: **180** / 180 unique samples
- Spend: **$0.0000** / $50.00
- Labels: {'y': 1, 'n': 3, 'unsure': 176}
- Failure modes: {'embedding_near_miss': 3, 'other': 176}
- Pipeline issues: {'json_parse_error': 1, 'llm_call_failed': 175}
- CSV anomalies: **0**
- Flagged for human review: **179**

## Draft paragraph

LLM L4 assist (qwen2.5:7b-instruct) labeled 180 stratified audit rows (y=1, n=3, unsure=176; spend $0.000 of $50.00). Top pipeline issues: {'llm_call_failed': 175, 'json_parse_error': 1}. CSV anomalies detected: 0. Human confirmation remains authoritative for camera-ready counts.

## CSV anomalies

```json
[]
```

## Flagged rows

- `qst_0002::metadata` N=20000 hit=False label=n issues=[]: The expected document ID is not in the top-10 retrieved IDs. The retrieved chunks are relevant but not on-topic, and the ID membership is incorrect.
- `qst_0239::semantic` N=20000 hit=False label=n issues=[]: The expected_doc_id is not in the top-10 retrieved IDs, and the retrieved chunks are not relevant to the question. The gold chunk mentions SOC2 evidence, which is a key compliance item, but it is not present in the top-10 retrieved documents.
- `qst_0240::semantic` N=40000 hit=False label=n issues=[]: The expected document is not in the top-10 retrieved documents. The retrieved chunks are relevant but not directly addressing the question about rate-policy jitter during regional failovers. The chunks are non-empty but the retrieval is not accurate.
- `qst_0423::conflicting_info` N=100000 hit=False label=unsure issues=['json_parse_error']: ```json
{
  "label_correct": "n",
  "failure_mode": "embedding_near_miss",
  "relevance_score": 1,
  "chunk_quality_score": 2,
  "id_membership_ok": false,
  "pipeline_issues": [],
  "severity_flags": [],
  "reasoning_summary": "Hit@10 is False as neither expected_doc_id is in the top-10 retrieved IDs. The retrieved chunks are relevant but not directly on-topic, and the IDs are not consistent with the expected ones."
}
```
- `qst_0080::basic` N=20000 hit=True label=unsure issues=['llm_call_failed']: llm_error: Remote end closed connection without response
- `qst_0415::conflicting_info` N=40000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0022::metadata` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0470::miscellaneous` N=100000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0156::basic` N=50000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0224::semantic` N=75000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0150::basic` N=50000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0048::basic` N=15000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0144::basic` N=15000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0054::metadata` N=100000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0017::metadata` N=40000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0209::semantic` N=100000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0062::basic` N=75000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0023::metadata` N=5000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0368::project_related` N=15000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0347::project_related` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0238::semantic` N=15000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0392::constrained` N=5000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0141::basic` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0048::metadata` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0107::basic` N=40000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0096::metadata` N=5000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0313::intra_document_reasoning` N=100000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0339::intra_document_reasoning` N=20000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0175::basic` N=20000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0044::metadata` N=25000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0312::intra_document_reasoning` N=15000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0349::project_related` N=75000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0063::metadata` N=100000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0393::constrained` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0368::project_related` N=40000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0116::basic` N=15000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0041::metadata` N=50000 hit=False label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0203::semantic` N=50000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0392::constrained` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
- `qst_0323::intra_document_reasoning` N=10000 hit=True label=unsure issues=['llm_call_failed']: llm_error: <urlopen error [Errno 111] Connection refused>
