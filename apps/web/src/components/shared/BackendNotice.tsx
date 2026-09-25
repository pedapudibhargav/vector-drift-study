import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

export default function BackendNotice() {
  return (
    <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex gap-3">
        <ExclamationTriangleIcon className="size-5 shrink-0 text-amber-600" />
        <div>
          <h3 className="text-sm font-semibold text-amber-800">
            Backend not available on GitHub Pages
          </h3>
          <p className="mt-1 text-sm text-amber-700">
            This demo UI is hosted statically. To run chat, ingestion, and vector search locally:
          </p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-amber-700">
            <li>Clone the repository and copy <code className="rounded bg-amber-100 px-1">.env.example</code> to <code className="rounded bg-amber-100 px-1">.env</code></li>
            <li>Add your <strong>OpenAI</strong> API key (vectors use local pgvector)</li>
            <li>Run <code className="rounded bg-amber-100 px-1">docker compose up vector-drift-research</code></li>
            <li>Open <code className="rounded bg-amber-100 px-1">http://localhost:5173</code></li>
          </ol>
        </div>
      </div>
    </div>
  )
}
