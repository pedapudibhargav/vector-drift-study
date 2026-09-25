/** Corpus browser + vector search for ERB study */
import { useCallback, useEffect, useState } from 'react'

type Stats = {
  embedded: number
  total_rows: number
  under_100k?: number
  by_source: { source_type: string; count: number }[]
}

type ChunkItem = {
  id: number
  doc_id: string
  title: string | null
  source_type: string | null
  scale_rank: number | null
  is_gold_anchor: boolean
  preview: string
}

type Hit = {
  rank: number
  doc_id: string
  score: number
  source_type?: string
  title?: string
  preview: string
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

export default function CorpusPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [items, setItems] = useState<ChunkItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [sourceType, setSourceType] = useState('')
  const [q, setQ] = useState('')
  const [goldOnly, setGoldOnly] = useState(false)
  const [maxScale, setMaxScale] = useState('')
  const [searchQ, setSearchQ] = useState('')
  const [searchScale, setSearchScale] = useState('5000')
  const [hits, setHits] = useState<Hit[]>([])
  const [error, setError] = useState<string | null>(null)
  const [embedder, setEmbedder] = useState<'openai' | 'titan'>('openai')
  const pageSize = 20

  const load = useCallback(async () => {
    setError(null)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        embedder,
      })
      if (sourceType) params.set('source_type', sourceType)
      if (q.trim()) params.set('q', q.trim())
      if (goldOnly) params.set('gold_only', 'true')
      if (maxScale) params.set('max_scale_rank', maxScale)
      const data = await apiGet<{ items: ChunkItem[]; total: number }>(
        `/api/corpus/chunks?${params}`,
      )
      setItems(data.items)
      setTotal(data.total)
      setStats(await apiGet<Stats>(`/api/corpus/stats?embedder=${embedder}`))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    }
  }, [page, sourceType, q, goldOnly, maxScale, embedder])

  useEffect(() => {
    void load()
  }, [load])

  const runSearch = async () => {
    setError(null)
    try {
      const data = await apiPost<{ hits: Hit[] }>('/api/corpus/search', {
        query: searchQ,
        top_k: 3,
        corpus_scale_size: searchScale ? Number(searchScale) : null,
        source_type: sourceType || null,
      })
      setHits(data.hits)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'search failed')
    }
  }

  const pages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="space-y-8 text-gray-200">
      <div>
        <h1 className="text-2xl font-semibold text-white">Corpus browser</h1>
        <p className="mt-1 text-sm text-gray-400">
          Paginated document vectors with filters. Toggle OpenAI vs Titan tables. Chat search is
          OpenAI-only; eval ladders use Hit@10 on each arm.
        </p>
        {stats && (
          <p className="mt-2 text-sm text-brand-400">
            Embedded {stats.embedded.toLocaleString()} / rows {stats.total_rows.toLocaleString()}
            {typeof stats.under_100k === 'number' && (
              <> · under 100k {stats.under_100k.toLocaleString()}</>
            )}
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {(['openai', 'titan'] as const).map((e) => (
          <button
            key={e}
            type="button"
            onClick={() => {
              setEmbedder(e)
              setPage(1)
            }}
            className={`rounded px-3 py-1.5 text-sm ${
              embedder === e
                ? 'bg-brand-600 text-white'
                : 'border border-surface-600 text-gray-400 hover:bg-surface-700'
            }`}
          >
            {e === 'openai' ? 'OpenAI (1536-d)' : 'Titan V2 (1024-d)'}
          </button>
        ))}
      </div>

      {error && <p className="rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</p>}

      <section className="space-y-3 rounded-lg border border-surface-600 bg-surface-800 p-4">
        <h2 className="text-sm font-medium text-white">Vector search (top-3)</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="min-w-[240px] flex-1 rounded border border-surface-600 bg-surface-900 px-3 py-2 text-sm"
            placeholder="Ask a question…"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
          />
          <input
            className="w-28 rounded border border-surface-600 bg-surface-900 px-3 py-2 text-sm"
            placeholder="scale N"
            value={searchScale}
            onChange={(e) => setSearchScale(e.target.value)}
          />
          <button
            type="button"
            onClick={() => void runSearch()}
            className="rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
          >
            Search
          </button>
        </div>
        <ul className="space-y-2">
          {hits.map((h) => (
            <li key={`${h.rank}-${h.doc_id}`} className="rounded border border-surface-600 bg-surface-900 p-3 text-sm">
              <div className="flex justify-between gap-2">
                <span className="font-mono text-brand-400">#{h.rank} {h.doc_id}</span>
                <span className="text-gray-400">{h.score?.toFixed(4)} · {h.source_type}</span>
              </div>
              <p className="mt-1 text-gray-300">{h.title}</p>
              <p className="mt-1 line-clamp-3 text-gray-500">{h.preview}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3 rounded-lg border border-surface-600 bg-surface-800 p-4">
        <h2 className="text-sm font-medium text-white">Browse</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="rounded border border-surface-600 bg-surface-900 px-3 py-2 text-sm"
            placeholder="Filter text / doc_id"
            value={q}
            onChange={(e) => {
              setPage(1)
              setQ(e.target.value)
            }}
          />
          <select
            className="rounded border border-surface-600 bg-surface-900 px-3 py-2 text-sm"
            value={sourceType}
            onChange={(e) => {
              setPage(1)
              setSourceType(e.target.value)
            }}
          >
            <option value="">All sources</option>
            {(stats?.by_source || []).map((s) => (
              <option key={s.source_type} value={s.source_type || ''}>
                {s.source_type} ({s.count})
              </option>
            ))}
          </select>
          <input
            className="w-32 rounded border border-surface-600 bg-surface-900 px-3 py-2 text-sm"
            placeholder="max scale_rank"
            value={maxScale}
            onChange={(e) => {
              setPage(1)
              setMaxScale(e.target.value)
            }}
          />
          <label className="inline-flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" checked={goldOnly} onChange={(e) => { setPage(1); setGoldOnly(e.target.checked) }} />
            Gold anchors only
          </label>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-gray-400">
              <tr>
                <th className="px-2 py-2">rank</th>
                <th className="px-2 py-2">doc_id</th>
                <th className="px-2 py-2">source</th>
                <th className="px-2 py-2">title / preview</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-t border-surface-600 align-top">
                  <td className="px-2 py-2 font-mono text-gray-400">{it.scale_rank}</td>
                  <td className="px-2 py-2 font-mono text-xs text-brand-400">
                    {it.doc_id}
                    {it.is_gold_anchor ? ' ★' : ''}
                  </td>
                  <td className="px-2 py-2">{it.source_type}</td>
                  <td className="px-2 py-2">
                    <div className="text-white">{it.title}</div>
                    <div className="mt-1 line-clamp-2 text-gray-500">{it.preview}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-400">
          <span>
            Page {page} / {pages} · {total.toLocaleString()} docs
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded border border-surface-600 px-3 py-1 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={page >= pages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-surface-600 px-3 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
