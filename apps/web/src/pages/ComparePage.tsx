/** OpenAI vs Titan A8 ladder comparison */
import { useCallback, useEffect, useState } from 'react'

type LadderRun = {
  corpus_scale_size: number
  condition: string
  n: number
  hit_at_1: number
  hit_at_5: number
  hit_at_10: number
  mrr: number
}

type LadderPayload = {
  embedder: string
  embedding_model: string
  results_table: string
  runs: LadderRun[]
}

type ComparePayload = {
  status: string
  message?: string
  openai_embedding_model?: string
  titan_embedding_model?: string
  shared_scales?: number[]
  drift_replication?: {
    raw: {
      hit_at_10: boolean | null
      hit_at_1: boolean | null
      mrr: boolean | null
      all_three_replicate: boolean | null
    }
  }
  endpoint_deltas?: Record<
    string,
    Record<
      string,
      {
        openai: { value_at_low: number | null; value_at_high: number | null; delta_high_minus_low: number | null }
        titan: { value_at_low: number | null; value_at_high: number | null; delta_high_minus_low: number | null }
        drift_replicates: boolean | null
      }
    >
  >
  comparisons?: {
    corpus_scale_size: number
    condition: string
    openai: Record<string, number>
    titan: Record<string, number>
    delta_titan_minus_openai: Record<string, number>
  }[]
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

function fmt(v: number | null | undefined) {
  if (v == null || Number.isNaN(v)) return '—'
  return v.toFixed(3)
}

export default function ComparePage() {
  const [openai, setOpenai] = useState<LadderPayload | null>(null)
  const [titan, setTitan] = useState<LadderPayload | null>(null)
  const [compare, setCompare] = useState<ComparePayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [condition, setCondition] = useState<'raw' | 'meta'>('raw')

  const load = useCallback(async () => {
    setError(null)
    try {
      const [o, t] = await Promise.all([
        apiGet<LadderPayload>(`/api/metrics/vector-drift?embedder=openai&condition=${condition}`),
        apiGet<LadderPayload>(`/api/metrics/vector-drift?embedder=titan&condition=${condition}`),
      ])
      setOpenai(o)
      setTitan(t)
      try {
        setCompare(await apiGet<ComparePayload>('/api/metrics/openai-vs-titan'))
      } catch {
        setCompare(null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    }
  }, [condition])

  useEffect(() => {
    void load()
  }, [load])

  const scales = Array.from(
    new Set([
      ...(openai?.runs.map((r) => r.corpus_scale_size) || []),
      ...(titan?.runs.map((r) => r.corpus_scale_size) || []),
    ]),
  ).sort((a, b) => a - b)

  const byScale = (runs: LadderRun[] | undefined, n: number) =>
    runs?.find((r) => r.corpus_scale_size === n && r.condition === condition)

  const rep = compare?.drift_replication?.raw

  return (
    <div className="space-y-8 text-gray-200">
      <div>
        <h1 className="text-2xl font-semibold text-white">OpenAI vs Titan</h1>
        <p className="mt-1 text-sm text-gray-400">
          Same gold-pinned ERB ladder (primary-200). Titan results live in{' '}
          <code className="text-brand-400">vector_drift_results_titan</code>.
        </p>
      </div>

      {error && (
        <p className="rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-gray-400">
          Condition{' '}
          <select
            className="ml-2 rounded border border-surface-600 bg-surface-900 px-2 py-1 text-sm"
            value={condition}
            onChange={(e) => setCondition(e.target.value as 'raw' | 'meta')}
          >
            <option value="raw">raw</option>
            <option value="meta">meta</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded bg-brand-600 px-3 py-1.5 text-sm text-white hover:bg-brand-500"
        >
          Refresh
        </button>
        <span className="text-xs text-gray-500">
          OpenAI: {openai?.embedding_model || '—'} · Titan: {titan?.embedding_model || '—'} ·
          Titan runs: {titan?.runs.length ?? 0}
        </span>
      </div>

      {compare?.status === 'complete' && rep && (
        <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
          <h2 className="text-sm font-medium text-white">Drift replication (5k → 100k)</h2>
          <ul className="mt-2 grid gap-2 text-sm sm:grid-cols-3">
            <li>Hit@10: {String(rep.hit_at_10)}</li>
            <li>Hit@1: {String(rep.hit_at_1)}</li>
            <li>MRR: {String(rep.mrr)}</li>
          </ul>
          <p className="mt-2 text-xs text-gray-500">
            All three raw metrics replicate: <span className="text-brand-400">{String(rep.all_three_replicate)}</span>
          </p>
        </section>
      )}

      {compare?.status === 'complete' && compare.endpoint_deltas?.raw && (
        <section className="overflow-x-auto rounded-lg border border-surface-600 bg-surface-800 p-4">
          <h2 className="mb-3 text-sm font-medium text-white">Endpoint deltas (raw)</h2>
          <table className="w-full text-left text-sm">
            <thead className="text-gray-400">
              <tr>
                <th className="py-1 pr-3">Metric</th>
                <th className="py-1 pr-3">OpenAI 5k</th>
                <th className="py-1 pr-3">OpenAI 100k</th>
                <th className="py-1 pr-3">Δ</th>
                <th className="py-1 pr-3">Titan 5k</th>
                <th className="py-1 pr-3">Titan 100k</th>
                <th className="py-1 pr-3">Δ</th>
                <th className="py-1">Replicates</th>
              </tr>
            </thead>
            <tbody>
              {(['hit_at_1', 'hit_at_5', 'hit_at_10', 'mrr'] as const).map((m) => {
                const cell = compare.endpoint_deltas!.raw[m]
                return (
                  <tr key={m} className="border-t border-surface-700 font-mono text-xs">
                    <td className="py-1.5 pr-3 text-gray-300">{m}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.openai.value_at_low)}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.openai.value_at_high)}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.openai.delta_high_minus_low)}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.titan.value_at_low)}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.titan.value_at_high)}</td>
                    <td className="py-1.5 pr-3">{fmt(cell.titan.delta_high_minus_low)}</td>
                    <td className="py-1.5">{String(cell.drift_replicates)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </section>
      )}

      <section className="overflow-x-auto rounded-lg border border-surface-600 bg-surface-800 p-4">
        <h2 className="mb-3 text-sm font-medium text-white">
          Ladder Hit@10 ({condition}) — live DB
        </h2>
        {scales.length === 0 ? (
          <p className="text-sm text-gray-500">No Titan ladder rows yet — sweep still running.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-gray-400">
              <tr>
                <th className="py-1 pr-3">N</th>
                <th className="py-1 pr-3">OpenAI Hit@10</th>
                <th className="py-1 pr-3">Titan Hit@10</th>
                <th className="py-1 pr-3">Δ (T−O)</th>
                <th className="py-1 pr-3">OpenAI MRR</th>
                <th className="py-1">Titan MRR</th>
              </tr>
            </thead>
            <tbody>
              {scales.map((n) => {
                const o = byScale(openai?.runs, n)
                const t = byScale(titan?.runs, n)
                const d =
                  o && t ? t.hit_at_10 - o.hit_at_10 : null
                return (
                  <tr key={n} className="border-t border-surface-700 font-mono text-xs">
                    <td className="py-1.5 pr-3">{n.toLocaleString()}</td>
                    <td className="py-1.5 pr-3">{fmt(o?.hit_at_10)}</td>
                    <td className="py-1.5 pr-3">{fmt(t?.hit_at_10)}</td>
                    <td className="py-1.5 pr-3">{fmt(d)}</td>
                    <td className="py-1.5 pr-3">{fmt(o?.mrr)}</td>
                    <td className="py-1.5">{fmt(t?.mrr)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
