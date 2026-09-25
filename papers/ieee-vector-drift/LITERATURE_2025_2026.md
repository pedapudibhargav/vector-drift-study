# Latest literature refresh (2025–2026)

Checked beyond classic DPR/RAG when updating Related Work. Key takeaways for our paper:

| Paper | Year | What it claims | How we use it |
|-------|------|----------------|---------------|
| Less LLM, More Documents (arXiv:2510.02657) | 2025 | Larger corpus ↑ end-to-end RAG via **coverage** | Contrast: we measure Hit@k with gold **already present** → crowding, not coverage |
| To Memorize or to Retrieve (arXiv:2604.00715) | 2026 | 3D scaling: model × pretrain tokens × retrieval store | Cite as corpus-size axis in RAG scaling laws |
| EnterpriseRAG-Bench (arXiv:2605.05253) | 2026 | Official ERB paper; BM25 vs dense vs agentic | Primary dataset citation (replace GitHub-only cite) |
| RAG Fusion industry (arXiv:2603.02153) | 2026 | Hit@10 + metadata scoping in prod | Metadata as operational lever; Hit@k reporting style |
| Vector DBs under realistic workloads (ICAISET) | 2026 | Filtered search / churn / restart | Motivates filtered (meta) condition + systems realism |
| Search quality differences / RCheck (arXiv:2608.25185) | 2026 | Mean recall hides per-query inequality (pgvector) | Motivates bootstrap CIs + error analysis |
| Data–query misalignment in streaming ANNS | 2026 | Recall drop from relationship shift | Threats / future streaming growth |

**Narrative gap we fill:** recent corpus-scaling papers mostly argue “more docs help RAG.” We argue a different, practitioner-critical claim: when answer docs are already indexed, growing distractors can **hurt labeled first-stage Hit@k**—and we quantify when metadata still helps ($N^\star$).
