export default function DocsPage() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Study documentation</h2>
      <p className="mt-2 text-sm text-gray-500">
        EnterpriseRAG-Bench vector drift study — gold-pinned scale ladder through N=100k with
        Hit@1/5/10, metadata rescue Delta_meta, and N-star.
      </p>

      <div className="mt-8 space-y-6 text-sm text-gray-600">
        <section>
          <h3 className="text-sm font-semibold text-gray-900">Public artifacts</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <a
                className="text-blue-700 underline"
                href="https://pedapudibhargav.github.io/vector-drift-study/"
                target="_blank"
                rel="noreferrer"
              >
                GitHub Pages artifact site
              </a>
            </li>
            <li>
              <a
                className="text-blue-700 underline"
                href="https://github.com/pedapudibhargav/vector-drift-study"
                target="_blank"
                rel="noreferrer"
              >
                GitHub repository
              </a>
            </li>
          </ul>
        </section>

        <section>
          <h3 className="text-sm font-semibold text-gray-900">In-repo docs</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 font-mono text-xs text-gray-800">
            <li>docs/STUDY_PROTOCOL.md</li>
            <li>docs/REPLICATE.md</li>
            <li>docs/THREATS_TO_VALIDITY.md</li>
            <li>docs/VERIFICATION_UI_AND_STATIC_HOSTING.md</li>
            <li>docs/HUMAN_AUDIT.md</li>
            <li>artifacts/published/*.json</li>
          </ul>
        </section>

        <section>
          <h3 className="text-sm font-semibold text-gray-900">Local stack</h3>
          <pre className="mt-2 overflow-x-auto rounded-lg bg-gray-900 p-4 text-xs text-gray-100">
{`cp .env.example .env   # OPENAI_API_KEY
docker compose up -d
# API :8000 · Web :5173 · Adminer :8081 (profile: tools)`}
          </pre>
          <p className="mt-2 text-xs text-gray-500">
            Per-query Hit@k rows: OpenAI in <span className="font-mono">vector_drift_results</span>;
            Titan V2 in <span className="font-mono">vector_drift_results_titan</span>. Compare arms on{' '}
            <a className="text-brand-400 hover:underline" href={`${import.meta.env.BASE_URL}compare`}>
              Compare
            </a>
            . Chunk text in <span className="font-mono">document_chunks</span> /{' '}
            <span className="font-mono">document_chunks_titan</span>. Use the{' '}
            <a className="text-brand-400 hover:underline" href={`${import.meta.env.BASE_URL}review`}>
              Review
            </a>{' '}
            page for L4 human audit (chunk text + DB-backed labels) and paper checklist. see
            VERIFICATION_UI_AND_STATIC_HOSTING.md.
          </p>
        </section>
      </div>
    </div>
  )
}
