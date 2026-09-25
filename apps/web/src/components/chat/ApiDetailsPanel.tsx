import type { ApiCallEvent } from '../../types'

interface ApiDetailsPanelProps {
  events: ApiCallEvent[]
  isStreaming: boolean
}

const eventColors: Record<string, string> = {
  status: 'bg-blue-50 text-blue-700 border-blue-200',
  embedding: 'bg-purple-50 text-purple-700 border-purple-200',
  retrieval: 'bg-amber-50 text-amber-700 border-amber-200',
  token: 'bg-green-50 text-green-700 border-green-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  done: 'bg-gray-50 text-gray-700 border-gray-200',
}

export default function ApiDetailsPanel({ events, isStreaming }: ApiDetailsPanelProps) {
  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">API Call Details</h2>
            <p className="text-xs text-gray-500">NDJSON stream — live retrieval transparency</p>
          </div>
          {isStreaming && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
              <span className="size-1.5 animate-pulse rounded-full bg-green-500" />
              Streaming
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {events.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-xs text-gray-400">
              API events will appear here during chat interactions
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((evt) => (
              <div
                key={evt.id}
                className={`rounded-lg border p-3 ${eventColors[evt.event] ?? 'bg-gray-50 border-gray-200'}`}
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wide">
                    {evt.event}
                  </span>
                  <span className="text-[10px] opacity-60">{evt.timestamp}</span>
                </div>
                <pre className="overflow-x-auto text-xs whitespace-pre-wrap">
                  {JSON.stringify(evt.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
