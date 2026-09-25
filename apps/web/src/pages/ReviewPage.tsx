/** L4 audit hub — default: author spot-check of LLM fairness labels; chunks expanded. */
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import reviewQueueCsv from '../data/review_queue_openai.csv?raw'
import spotcheckQueueCsv from '../data/l4_spotcheck_queue.csv?raw'

type Tab = 'rows' | 'checklist' | 'overview' | 'llm' | 'export'
type QueueFilter = 'spotcheck' | 'high' | 'all'

type Status = {
  samples: number
  human_labels_done: number
  llm_labels: number
  llm_budget_usd: number
  llm_spent_usd: number
  llm_remaining_usd: number
  llm_model: string
  failure_modes: string[]
  target_human_labels: number
}

type Overview = {
  fit: Record<string, unknown>
  sweep_summary: Record<string, unknown>
  progress_by_scale: {
    corpus_scale_size: number
    condition: string
    n_samples: number
    n_labeled: number
  }[]
  auditors: { auditor_id: string; n: number }[]
  failure_mode_counts: { corpus_scale_size: number; failure_mode: string; n: number }[]
  llm: {
    budget_usd: number
    spent_usd: number
    remaining_usd: number
    model: string
  }
  formulas: { hit_at_k: string; scaling: string; delta_meta: string }
  reviewer_guidance: string[]
}

type QueueItem = {
  question_id: string
  corpus_scale_size: number
  condition: string
  hit_at_10: boolean | null
  rank: number | null
  document_recall: number | null
  label_correct: string | null
  failure_mode: string | null
  n_human_labels: number
  n_llm_labels: number
  priority?: string
  llm_label?: string | null
  llm_reasoning?: string | null
  spot_reason?: string | null
  spot_llm_notes?: string | null
  gold_answers_llm?: string | null
}

type Chunk = {
  doc_id: string
  preview: string
  source?: string
  source_type?: string | null
  title?: string | null
  rank?: number
  is_gold?: boolean
}

type ItemDetail = {
  sample: {
    question_id: string
    corpus_scale_size: number
    condition: string
    hit_at_10: boolean | null
    rank: number | null
    document_recall: number | null
    expected_doc_ids: string[]
    retrieved_doc_ids: string[]
    priority?: string | null
  }
  question_text: string
  question_type?: string | null
  id_membership_hit: boolean
  hit_flag_consistent: boolean
  gold_chunks: Chunk[]
  retrieved_chunks: Chunk[]
  evaluations: {
    evaluator_kind: string
    auditor_id: string
    label_correct: string | null
    failure_mode: string | null
    notes: string | null
    status: string
    relevance_score: number | null
    reasoning_summary: string | null
    model: string | null
    cost_usd: number | null
  }[]
  my_label: {
    label_correct: string | null
    failure_mode: string | null
    notes: string | null
    status: string
    updated_at?: string | null
  } | null
  failure_modes: string[]
  triage?: {
    priority?: string
    llm_label?: string | null
    llm_failure_mode?: string | null
    llm_reasoning?: string | null
  }
  how_to_decide?: string[]
}

type ChecklistItem = {
  claim_key: string
  title: string
  detail: string
  category: string
  status: string
  label_correct: string | null
  notes: string | null
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

async function apiSend<T>(path: string, method: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<T>
}

function TruncText({ text, max = 1200, defaultOpen = true }: { text: string; max?: number; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  if (!text) return <span className="text-amber-400">(empty — flag chunk_too_thin / other)</span>
  const long = text.length > max
  const shown = open || !long ? text : `${text.slice(0, max)}…`
  return (
    <div>
      <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-gray-200">
        {shown}
      </pre>
      {long && (
        <button
          type="button"
          className="mt-1 text-xs text-brand-400 hover:underline"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? 'Show less' : 'Show full chunk'}
        </button>
      )}
    </div>
  )
}

const SCALES = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]

type TriageRow = {
  priority: string
  llm_label: string | null
  llm_failure_mode: string | null
  llm_reasoning: string | null
}

type SpotRow = {
  order: number
  spot_reason: string
  gold_answers_llm: string
  human_label_correct: string
  human_notes: string
}

function rowKey(qid: string, scale: number, cond: string) {
  return `${qid}||${scale}||${cond}`
}

function parseCsvLine(line: string): string[] {
  const cols: string[] = []
  let cur = ''
  let inQ = false
  for (let c = 0; c < line.length; c++) {
    const ch = line[c]
    if (ch === '"') {
      inQ = !inQ
      continue
    }
    if (ch === ',' && !inQ) {
      cols.push(cur)
      cur = ''
      continue
    }
    cur += ch
  }
  cols.push(cur)
  return cols
}

async function loadTriageMap(): Promise<Map<string, TriageRow>> {
  const map = new Map<string, TriageRow>()
  const lines = reviewQueueCsv.trim().split('\n')
  if (lines.length < 2) return map
  const headers = lines[0].split(',')
  const idx = (name: string) => headers.indexOf(name)
  for (let i = 1; i < lines.length; i++) {
    const cols = parseCsvLine(lines[i])
    const qid = cols[idx('question_id')] || ''
    const scale = Number(cols[idx('corpus_scale_size')] || 0)
    const cond = cols[idx('condition')] || 'raw'
    if (!qid) continue
    map.set(rowKey(qid, scale, cond), {
      priority: cols[idx('priority')] || 'normal',
      llm_label: cols[idx('llm_label')] || null,
      llm_failure_mode: cols[idx('llm_failure_mode')] || null,
      llm_reasoning: cols[idx('llm_reasoning')] || null,
    })
  }
  return map
}

function loadSpotMap(): Map<string, SpotRow> {
  const map = new Map<string, SpotRow>()
  const lines = spotcheckQueueCsv.trim().split('\n')
  if (lines.length < 2) return map
  const headers = lines[0].split(',')
  const idx = (name: string) => headers.indexOf(name)
  for (let i = 1; i < lines.length; i++) {
    const cols = parseCsvLine(lines[i])
    const qid = cols[idx('question_id')] || ''
    const scale = Number(cols[idx('corpus_scale_size')] || 0)
    const cond = cols[idx('condition')] || 'raw'
    if (!qid) continue
    map.set(rowKey(qid, scale, cond), {
      order: i,
      spot_reason: cols[idx('spot_reason')] || '',
      gold_answers_llm: cols[idx('gold_answers_question')] || '',
      human_label_correct: cols[idx('human_label_correct')] || '',
      human_notes: cols[idx('human_notes')] || '',
    })
  }
  return map
}

const SPOT_REASON_LABEL: Record<string, string> = {
  irene_choi_auditor_inconsistency: 'Irene Choi — check due date at end of gold',
  hit_gold_ok: 'HIT + LLM says gold answers',
  miss_gold_ok_true_miss: 'MISS + LLM says gold answers (true miss)',
  miss_gold_false_check_label: 'MISS + LLM says gold does NOT answer',
}

export default function ReviewPage() {
  const [tab, setTab] = useState<Tab>('rows')
  const [auditorId, setAuditorId] = useState(() => localStorage.getItem('audit_auditor_id') || 'BP')
  const [scaleFilter, setScaleFilter] = useState<string>('')
  const [conditionFilter, setConditionFilter] = useState<string>('')
  const [queueFilter, setQueueFilter] = useState<QueueFilter>('spotcheck')
  const [unlabeledOnly, setUnlabeledOnly] = useState(false)
  const [triageMap, setTriageMap] = useState<Map<string, TriageRow>>(() => new Map())
  const [spotMap] = useState<Map<string, SpotRow>>(() => loadSpotMap())
  const [status, setStatus] = useState<Status | null>(null)
  const [overview, setOverview] = useState<Overview | null>(null)
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [detail, setDetail] = useState<ItemDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [label, setLabel] = useState<'y' | 'n' | 'unsure'>('y')
  const [failureMode, setFailureMode] = useState('')
  const [notes, setNotes] = useState('')
  /** Persisted DB decision for this auditor + row (null = never saved). */
  const [savedDecision, setSavedDecision] = useState<{
    label_correct: 'y' | 'n' | 'unsure'
    failure_mode: string | null
    notes: string | null
    updated_at?: string | null
  } | null>(null)
  const [checklist, setChecklist] = useState<ChecklistItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [exportPreview, setExportPreview] = useState('')
  const [saveFlash, setSaveFlash] = useState<string | null>(null)
  const [llmReport, setLlmReport] = useState<{
    file_report: {
      n_evaluated?: number
      spent_usd?: number
      budget_usd?: number
      label_counts?: Record<string, number>
      failure_mode_counts?: Record<string, number>
      pipeline_issue_counts?: Record<string, number>
      flagged_rows?: {
        question_id: string
        corpus_scale_size: number
        hit_at_10: boolean
        label_correct: string | null
        reasoning_summary: string | null
      }[]
      n_flagged?: number
      paper_paragraph_draft?: string
    } | null
    db_llm_count: number
    llm_spent_usd: number
    llm_budget_usd: number
  } | null>(null)

  useEffect(() => {
    localStorage.setItem('audit_auditor_id', auditorId)
  }, [auditorId])

  useEffect(() => {
    void loadTriageMap().then(setTriageMap)
  }, [])

  const selected = queue[selectedIdx] ?? null

  const loadStatus = useCallback(async () => {
    setStatus(await apiGet<Status>('/api/audit/status'))
  }, [])

  const loadOverview = useCallback(async () => {
    setOverview(await apiGet<Overview>('/api/audit/overview'))
  }, [])

  const loadQueue = useCallback(
    async (opts?: { resetIndex?: boolean }) => {
      const params = new URLSearchParams({
        auditor_id: auditorId,
        unlabeled_only: String(unlabeledOnly),
      })
      if (scaleFilter) params.set('scale', scaleFilter)
      if (conditionFilter) params.set('condition', conditionFilter)
      if (queueFilter === 'high') params.set('priority', 'high')
      const data = await apiGet<{ items: QueueItem[] }>(`/api/audit/queue?${params}`)
      let items = data.items.map((it) => {
        const t = triageMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
        const s = spotMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
        return {
          ...it,
          priority: s ? 'spotcheck' : it.priority || t?.priority || 'normal',
          llm_label: it.llm_label ?? t?.llm_label ?? s?.human_label_correct ?? null,
          llm_reasoning: it.llm_reasoning ?? t?.llm_reasoning ?? s?.human_notes ?? null,
          spot_reason: s?.spot_reason ?? null,
          spot_llm_notes: s?.human_notes ?? null,
          gold_answers_llm: s?.gold_answers_llm ?? null,
        }
      })

      if (queueFilter === 'spotcheck') {
        items = items
          .filter((it) => spotMap.has(rowKey(it.question_id, it.corpus_scale_size, it.condition)))
          .sort((a, b) => {
            const oa = spotMap.get(rowKey(a.question_id, a.corpus_scale_size, a.condition))?.order ?? 999
            const ob = spotMap.get(rowKey(b.question_id, b.corpus_scale_size, b.condition))?.order ?? 999
            return oa - ob
          })
        // Rebuild from full queue if API priority filter hid spot rows
        if (items.length === 0 && spotMap.size > 0) {
          const params2 = new URLSearchParams({
            auditor_id: auditorId,
            unlabeled_only: String(unlabeledOnly),
          })
          if (scaleFilter) params2.set('scale', scaleFilter)
          if (conditionFilter) params2.set('condition', conditionFilter)
          const all = await apiGet<{ items: QueueItem[] }>(`/api/audit/queue?${params2}`)
          items = all.items
            .map((it) => {
              const t = triageMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
              const s = spotMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
              return {
                ...it,
                priority: s ? 'spotcheck' : t?.priority || 'normal',
                llm_label: t?.llm_label ?? s?.human_label_correct ?? null,
                llm_reasoning: t?.llm_reasoning ?? s?.human_notes ?? null,
                spot_reason: s?.spot_reason ?? null,
                spot_llm_notes: s?.human_notes ?? null,
                gold_answers_llm: s?.gold_answers_llm ?? null,
              }
            })
            .filter((it) => spotMap.has(rowKey(it.question_id, it.corpus_scale_size, it.condition)))
            .sort((a, b) => {
              const oa = spotMap.get(rowKey(a.question_id, a.corpus_scale_size, a.condition))?.order ?? 999
              const ob = spotMap.get(rowKey(b.question_id, b.corpus_scale_size, b.condition))?.order ?? 999
              return oa - ob
            })
        }
      } else if (queueFilter === 'high') {
        items = items.filter((it) => {
          const t = triageMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
          return (it.priority || t?.priority) === 'high'
        })
        if (items.length === 0 && triageMap.size > 0) {
          const params2 = new URLSearchParams({
            auditor_id: auditorId,
            unlabeled_only: String(unlabeledOnly),
          })
          if (scaleFilter) params2.set('scale', scaleFilter)
          if (conditionFilter) params2.set('condition', conditionFilter)
          const all = await apiGet<{ items: QueueItem[] }>(`/api/audit/queue?${params2}`)
          items = all.items
            .map((it) => {
              const t = triageMap.get(rowKey(it.question_id, it.corpus_scale_size, it.condition))
              return {
                ...it,
                priority: t?.priority || 'normal',
                llm_label: t?.llm_label ?? null,
                llm_reasoning: t?.llm_reasoning ?? null,
              }
            })
            .filter((it) => it.priority === 'high')
            .sort((a, b) => Number(a.hit_at_10) - Number(b.hit_at_10))
        }
      }

      setQueue(items)
      if (opts?.resetIndex !== false) {
        setSelectedIdx(0)
      } else {
        setSelectedIdx((i) => (items.length === 0 ? 0 : Math.min(i, items.length - 1)))
      }
    },
    [auditorId, scaleFilter, conditionFilter, unlabeledOnly, queueFilter, triageMap, spotMap],
  )

  const loadDetail = useCallback(async () => {
    if (!selected) {
      setDetail(null)
      setSavedDecision(null)
      return
    }
    setDetailLoading(true)
    try {
      const params = new URLSearchParams({
        question_id: selected.question_id,
        corpus_scale_size: String(selected.corpus_scale_size),
        condition: selected.condition,
        auditor_id: auditorId,
      })
      const data = await apiGet<ItemDetail>(`/api/audit/item?${params}`)
      const t = triageMap.get(
        rowKey(selected.question_id, selected.corpus_scale_size, selected.condition),
      )
      if (t && !data.triage?.llm_reasoning) {
        data.triage = {
          priority: t.priority,
          llm_label: t.llm_label,
          llm_failure_mode: t.llm_failure_mode,
          llm_reasoning: t.llm_reasoning,
        }
      }
      setDetail(data)
      const mine = data.my_label
      if (mine?.label_correct === 'y' || mine?.label_correct === 'n' || mine?.label_correct === 'unsure') {
        setLabel(mine.label_correct)
        setSavedDecision({
          label_correct: mine.label_correct,
          failure_mode: mine.failure_mode || null,
          notes: mine.notes || null,
          updated_at: mine.updated_at ?? null,
        })
      } else {
        setSavedDecision(null)
        if (!data.hit_flag_consistent) {
          setLabel('unsure')
        } else {
          setLabel('y')
        }
      }
      setFailureMode(mine?.failure_mode || '')
      setNotes(mine?.notes || '')
    } finally {
      setDetailLoading(false)
    }
  }, [selected, auditorId, triageMap])

  const loadChecklist = useCallback(async () => {
    const data = await apiGet<{ items: ChecklistItem[] }>(
      `/api/audit/checklist?auditor_id=${encodeURIComponent(auditorId)}`,
    )
    setChecklist(data.items)
  }, [auditorId])

  const loadLlmReport = useCallback(async () => {
    setLlmReport(await apiGet('/api/audit/llm-report'))
  }, [])

  const refreshAll = useCallback(async () => {
    setError(null)
    try {
      await Promise.all([loadStatus(), loadOverview(), loadQueue(), loadChecklist(), loadLlmReport()])
    } catch (e) {
      setError(
        e instanceof Error
          ? `${e.message} — Is the API up? Try: docker compose up -d && Refresh`
          : 'load failed',
      )
    }
  }, [loadStatus, loadOverview, loadQueue, loadChecklist, loadLlmReport])

  useEffect(() => {
    void refreshAll()
  }, [refreshAll])

  useEffect(() => {
    void loadDetail().catch((e) => setError(e instanceof Error ? e.message : 'detail failed'))
  }, [loadDetail])

  const progressPct = useMemo(() => {
    if (!status) return 0
    return Math.min(100, Math.round((status.human_labels_done / status.target_human_labels) * 100))
  }, [status])

  const decisionDirty = useMemo(() => {
    if (!savedDecision) return true
    return (
      savedDecision.label_correct !== label ||
      (savedDecision.failure_mode || '') !== (failureMode || '') ||
      (savedDecision.notes || '') !== (notes || '')
    )
  }, [savedDecision, label, failureMode, notes])

  async function saveLabel(opts?: {
    nextLabel?: 'y' | 'n' | 'unsure'
    nextFailureMode?: string
    nextNotes?: string
    advance?: boolean
  }) {
    if (!selected) return
    const nextLabel = opts?.nextLabel ?? label
    const nextFailureMode = opts?.nextFailureMode ?? failureMode
    const nextNotes = opts?.nextNotes ?? notes
    const advance = opts?.advance ?? true
    if (nextLabel === 'n' && !nextFailureMode) {
      setError('Pick a failure mode when labeling n (miss / disagree).')
      setLabel('n')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await apiSend('/api/audit/label', 'PUT', {
        question_id: selected.question_id,
        corpus_scale_size: selected.corpus_scale_size,
        condition: selected.condition,
        auditor_id: auditorId,
        label_correct: nextLabel,
        failure_mode: nextFailureMode || null,
        notes: nextNotes || null,
        status: 'done',
      })
      setLabel(nextLabel)
      setFailureMode(nextFailureMode)
      setNotes(nextNotes)
      setSavedDecision({
        label_correct: nextLabel,
        failure_mode: nextFailureMode || null,
        notes: nextNotes || null,
        updated_at: new Date().toISOString(),
      })
      setQueue((prev) =>
        prev.map((q, i) =>
          i === selectedIdx
            ? { ...q, label_correct: nextLabel, failure_mode: nextFailureMode || null }
            : q,
        ),
      )
      const pretty =
        nextLabel === 'y' ? 'Agree (fair)' : nextLabel === 'n' ? 'Disagree' : 'Unsure'
      setSaveFlash(`Saved in DB: ${pretty}`)
      setTimeout(() => setSaveFlash(null), 2500)
      if (advance) {
        if (unlabeledOnly) {
          await loadQueue({ resetIndex: true })
        } else {
          await loadQueue({ resetIndex: false })
          setSelectedIdx((i) => Math.min(i + 1, Math.max(0, queue.length - 1)))
        }
      } else {
        await loadQueue({ resetIndex: false })
      }
      await loadStatus()
      await loadOverview()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'save failed')
    } finally {
      setBusy(false)
    }
  }

  /** One-click decide: y/unsure save immediately; n waits for failure mode. */
  function chooseDecision(v: 'y' | 'n' | 'unsure') {
    setLabel(v)
    setError(null)
    if (v === 'n') {
      if (failureMode) {
        void saveLabel({ nextLabel: 'n', advance: false })
      } else {
        setError('Disagree selected — pick a failure mode, then it will save (or press Save).')
      }
      return
    }
    void saveLabel({ nextLabel: v, advance: false })
  }

  // Keyboard: y / n / u / s save / arrows
  useEffect(() => {
    if (tab !== 'rows') return
    const onKey = (ev: KeyboardEvent) => {
      const tag = (ev.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      if (ev.key === 'y' || ev.key === 'Y') {
        ev.preventDefault()
        chooseDecision('y')
      }
      if (ev.key === 'n' || ev.key === 'N') {
        ev.preventDefault()
        chooseDecision('n')
      }
      if (ev.key === 'u' || ev.key === 'U') {
        ev.preventDefault()
        chooseDecision('unsure')
      }
      if (ev.key === 's' || ev.key === 'S') {
        ev.preventDefault()
        void saveLabel({ advance: true })
      }
      if (ev.key === 'ArrowDown') {
        ev.preventDefault()
        setSelectedIdx((i) => Math.min(i + 1, Math.max(0, queue.length - 1)))
      }
      if (ev.key === 'ArrowUp') {
        ev.preventDefault()
        setSelectedIdx((i) => Math.max(i - 1, 0))
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, queue.length, selected, label, failureMode, notes, busy, selectedIdx, unlabeledOnly])

  async function saveCheckItem(item: ChecklistItem, patch: Partial<ChecklistItem>) {
    setBusy(true)
    try {
      await apiSend('/api/audit/checklist', 'PUT', {
        claim_key: item.claim_key,
        auditor_id: auditorId,
        status: patch.status ?? item.status,
        label_correct:
          patch.label_correct ??
          (item.label_correct === 'y' || item.label_correct === 'n' || item.label_correct === 'unsure'
            ? item.label_correct
            : null),
        notes: patch.notes ?? item.notes,
      })
      await loadChecklist()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'checklist save failed')
    } finally {
      setBusy(false)
    }
  }

  async function loadExport(fmt: 'markdown' | 'json') {
    setBusy(true)
    try {
      if (fmt === 'markdown') {
        const res = await fetch('/api/audit/export?format=markdown')
        setExportPreview(await res.text())
      } else {
        const data = await apiGet<{ summary: { paper_paragraph_draft: string } }>(
          '/api/audit/export?format=json',
        )
        setExportPreview(JSON.stringify(data.summary, null, 2))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'export failed')
    } finally {
      setBusy(false)
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'rows', label: '1. Row audit' },
    { id: 'checklist', label: '2. Paper checklist' },
    { id: 'overview', label: 'Overview' },
    { id: 'llm', label: 'LLM triage' },
    { id: 'export', label: 'Export' },
  ]

  const goldInTop = detail?.id_membership_hit ?? false

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">L4 spot-check (author)</h1>
          <p className="mt-1 max-w-3xl text-sm text-gray-400">
            Full LLM fairness pass already ran (62/62 Agree). Review these{' '}
            <strong className="font-medium text-gray-200">~10 spot-check rows</strong> only — gold +
            retrieved chunks are expanded. Paper claims stay L1; this corroborates L4 wording.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-gray-400">
            Your name / Auditor ID
            <input
              className="ml-2 rounded border border-surface-600 bg-surface-800 px-2 py-1 font-mono text-sm text-white"
              value={auditorId}
              onChange={(e) => setAuditorId(e.target.value.trim() || 'BP')}
            />
          </label>
          <button
            type="button"
            onClick={() => void refreshAll()}
            className="rounded bg-surface-700 px-3 py-1.5 text-sm text-gray-200 hover:bg-surface-600"
          >
            Refresh
          </button>
        </div>
      </header>

      <div className="rounded-lg border border-brand-700/40 bg-brand-950/30 px-4 py-3 text-sm text-gray-200">
        <p className="font-medium text-brand-300">Spot-check one row (≈2–3 min)</p>
        <ol className="mt-1 list-decimal space-y-0.5 pl-5 text-gray-300">
          <li>Read why this row is in the queue (amber banner).</li>
          <li>Read the <em>question</em>, then full <em>Gold</em> (scroll to the end for due dates / action items).</li>
          <li>
            Confirm Hit@10: is gold doc_id in Retrieved #1–#10? Agree if the auto flag matches.
          </li>
          <li>
            Press <kbd className="rounded bg-surface-800 px-1">y</kbd> if fair /{' '}
            <kbd className="rounded bg-surface-800 px-1">n</kbd> if unfair /{' '}
            <kbd className="rounded bg-surface-800 px-1">s</kbd> save &amp; next.
          </li>
        </ol>
      </div>

      {status && (
        <div className="grid gap-3 sm:grid-cols-4">
          <Stat
            label="Your progress"
            value={`${status.human_labels_done} / ${queueFilter === 'spotcheck' ? spotMap.size : status.target_human_labels}`}
            sub={
              queueFilter === 'spotcheck'
                ? `spot-check target ${spotMap.size}`
                : `${progressPct}% · optional full queue`
            }
          />
          <Stat label="In DB queue" value={String(status.samples)} sub="seeded from published CSVs" />
          <Stat
            label="This filter"
            value={String(queue.length)}
            sub={
              queueFilter === 'spotcheck'
                ? 'author spot-check'
                : queueFilter === 'high'
                  ? 'high priority'
                  : 'all rows'
            }
          />
          <Stat
            label="LLM L4 fairness"
            value="62/62 y"
            sub="secondary — see Methods"
          />
        </div>
      )}

      <div className="flex flex-wrap gap-1 border-b border-surface-600 pb-px">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-t px-3 py-2 text-sm font-medium ${
              tab === t.id
                ? 'bg-surface-800 text-brand-400'
                : 'text-gray-400 hover:bg-surface-800 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}
      {saveFlash && <div className="text-sm text-emerald-400">{saveFlash}</div>}

      {tab === 'rows' && (
        <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
          <aside className="space-y-3">
            <div className="flex flex-col gap-2 rounded border border-surface-600 bg-surface-800 p-3">
              <label className="text-xs text-gray-400">
                Scale N
                <select
                  className="mt-1 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm"
                  value={scaleFilter}
                  onChange={(e) => setScaleFilter(e.target.value)}
                >
                  <option value="">All scales</option>
                  {SCALES.map((n) => (
                    <option key={n} value={String(n)}>
                      N={n}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs text-gray-400">
                Condition
                <select
                  className="mt-1 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm"
                  value={conditionFilter}
                  onChange={(e) => setConditionFilter(e.target.value)}
                >
                  <option value="">raw + meta</option>
                  <option value="raw">raw only</option>
                  <option value="meta">meta only</option>
                </select>
              </label>
              <label className="text-xs text-gray-400">
                Queue
                <select
                  className="mt-1 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm"
                  value={queueFilter}
                  onChange={(e) => setQueueFilter(e.target.value as QueueFilter)}
                >
                  <option value="spotcheck">Spot-check only ({spotMap.size} rows)</option>
                  <option value="high">High priority (62)</option>
                  <option value="all">All rows</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-300">
                <input
                  type="checkbox"
                  checked={unlabeledOnly}
                  onChange={(e) => setUnlabeledOnly(e.target.checked)}
                />
                Unlabeled only
              </label>
            </div>
            <div className="max-h-[70vh] overflow-auto rounded border border-surface-600">
              {queue.length === 0 && (
                <p className="p-3 text-sm text-amber-300">
                  No rows for these filters. Try Queue=Spot-check or All, Scale=All, then Refresh.
                </p>
              )}
              {queue.map((q, i) => {
                const done = !!q.label_correct
                return (
                <button
                  key={`${q.question_id}-${q.corpus_scale_size}-${q.condition}`}
                  type="button"
                  onClick={() => setSelectedIdx(i)}
                  className={`block w-full border-b border-surface-700 px-3 py-2 text-left text-xs ${
                    i === selectedIdx ? 'bg-brand-600/20' : 'hover:bg-surface-800'
                  } ${done ? 'border-l-2 border-l-emerald-500' : 'border-l-2 border-l-transparent'}`}
                >
                  <div className="flex justify-between gap-2 font-mono text-gray-200">
                    <span className="flex min-w-0 items-center gap-1.5 truncate">
                      {done ? (
                        <span
                          className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white"
                          title="Labeled"
                        >
                          ✓
                        </span>
                      ) : (
                        <span
                          className="inline-flex h-4 w-4 shrink-0 rounded-full border border-surface-500"
                          title="Unlabeled"
                        />
                      )}
                      <span className="truncate">{q.question_id}</span>
                    </span>
                    <span className={q.hit_at_10 ? 'text-emerald-400' : 'text-amber-400'}>
                      {q.hit_at_10 ? 'HIT' : 'MISS'}
                    </span>
                  </div>
                  <div className="mt-0.5 text-gray-500">
                    {q.spot_reason && (
                      <span className="mr-1 rounded bg-violet-900/70 px-1 text-violet-100">
                        SPOT
                      </span>
                    )}
                    {q.priority === 'high' && !q.spot_reason && (
                      <span className="mr-1 rounded bg-amber-900/60 px-1 text-amber-200">HIGH</span>
                    )}
                    {done && (
                      <span className="mr-1 rounded bg-emerald-900/70 px-1 font-medium text-emerald-200">
                        DONE · {q.label_correct}
                      </span>
                    )}
                    <span>
                      N={q.corpus_scale_size} · {q.condition}
                      {!done && ' · unlabeled'}
                    </span>
                  </div>
                </button>
                )
              })}
            </div>
          </aside>

          <div className="space-y-4">
            {detailLoading && <p className="text-sm text-gray-500">Loading question + chunks…</p>}
            {!detail && !detailLoading && (
              <p className="text-sm text-gray-500">Select a row on the left.</p>
            )}
            {detail && (
              <>
                <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-gray-500">Question</p>
                      <h2 className="mt-1 font-mono text-sm text-gray-400">
                        {detail.sample.question_id}
                      </h2>
                      <p className="text-xs text-gray-500">
                        N={detail.sample.corpus_scale_size} · {detail.sample.condition}
                        {detail.question_type ? ` · ${detail.question_type}` : ''}
                        {detail.sample.rank != null ? ` · gold rank=${detail.sample.rank}` : ''}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      <Badge ok={!!detail.sample.hit_at_10}>
                        auto Hit@10 = {String(detail.sample.hit_at_10)}
                      </Badge>
                      <Badge ok={goldInTop}>gold in top-10 = {String(goldInTop)}</Badge>
                      <Badge ok={detail.hit_flag_consistent}>
                        flags consistent = {String(detail.hit_flag_consistent)}
                      </Badge>
                    </div>
                  </div>
                  <p className="mt-4 text-lg leading-snug text-white">
                    {detail.question_text || (
                      <span className="text-amber-400">
                        Question text missing — Refresh; API should resolve from ERB manifest.
                      </span>
                    )}
                  </p>
                  {!detail.hit_flag_consistent && (
                    <p className="mt-2 rounded border border-amber-800 bg-amber-950/40 px-2 py-1 text-xs text-amber-200">
                      Auto Hit@10 disagrees with ID membership — treat carefully; often label{' '}
                      <strong>n</strong> or <strong>unsure</strong>.
                    </p>
                  )}
                  {selected?.spot_reason && (
                    <div className="mt-3 rounded border border-violet-700/60 bg-violet-950/40 px-3 py-2 text-sm text-violet-100">
                      <p className="font-medium text-violet-200">
                        Why spot-check:{' '}
                        {SPOT_REASON_LABEL[selected.spot_reason] || selected.spot_reason}
                      </p>
                      <p className="mt-1 text-xs text-violet-200/80">
                        LLM L4: fairness=
                        <span className="font-mono">{selected.llm_label ?? '—'}</span>
                        {' · '}gold_answers=
                        <span className="font-mono">{selected.gold_answers_llm ?? '—'}</span>
                        {selected.spot_llm_notes ? ` — ${selected.spot_llm_notes}` : ''}
                      </p>
                    </div>
                  )}
                </section>

                {detail.triage?.llm_reasoning && (
                  <section className="rounded-lg border border-surface-700 bg-surface-900/80 p-3 text-xs text-gray-400">
                    <span className="font-semibold text-gray-300">LLM triage (optional hint): </span>
                    label={detail.triage.llm_label ?? '—'}
                    {detail.triage.llm_failure_mode
                      ? ` · ${detail.triage.llm_failure_mode}`
                      : ''}{' '}
                    — {detail.triage.llm_reasoning}
                  </section>
                )}

                <div className="grid gap-4 xl:grid-cols-2">
                  <ChunkPanel title="Gold / expected answer document" chunks={detail.gold_chunks} gold />
                  <ChunkPanel
                    title="Retrieved top-10 (search results)"
                    chunks={detail.retrieved_chunks}
                  />
                </div>

                <section className="sticky bottom-2 z-10 rounded-lg border border-brand-700/50 bg-surface-900/95 p-4 shadow-lg backdrop-blur">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-white">Your decision</h3>
                    {savedDecision ? (
                      <span className="rounded-full bg-emerald-900/80 px-2.5 py-0.5 text-xs font-medium text-emerald-200">
                        ✓ Saved in DB ·{' '}
                        {savedDecision.label_correct === 'y'
                          ? 'Agree (fair)'
                          : savedDecision.label_correct === 'n'
                            ? 'Disagree'
                            : 'Unsure'}
                        {savedDecision.failure_mode ? ` · ${savedDecision.failure_mode}` : ''}
                        {decisionDirty ? ' · editing…' : ''}
                      </span>
                    ) : (
                      <span className="rounded-full bg-surface-700 px-2.5 py-0.5 text-xs text-gray-400">
                        Not saved yet
                      </span>
                    )}
                  </div>
                  {saveFlash && (
                    <p className="mt-2 rounded border border-emerald-700 bg-emerald-950/50 px-2 py-1 text-xs text-emerald-200">
                      {saveFlash}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    Click a choice to <strong className="text-white">save immediately</strong> (Disagree
                    needs a failure mode first). Keys:{' '}
                    <kbd className="rounded bg-surface-800 px-1">y</kbd>/
                    <kbd className="rounded bg-surface-800 px-1">n</kbd>/
                    <kbd className="rounded bg-surface-800 px-1">u</kbd> ·{' '}
                    <kbd className="rounded bg-surface-800 px-1">s</kbd> save &amp; next · ↑↓ change
                    row.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(
                      [
                        ['y', 'Agree (fair)'],
                        ['n', 'Disagree'],
                        ['unsure', 'Unsure'],
                      ] as const
                    ).map(([v, title]) => {
                      const isSavedChoice = savedDecision?.label_correct === v
                      const isActive = label === v
                      return (
                        <button
                          key={v}
                          type="button"
                          disabled={busy}
                          onClick={() => chooseDecision(v)}
                          className={`rounded px-4 py-2 text-sm font-medium disabled:opacity-50 ${
                            isActive
                              ? 'bg-brand-600 text-white ring-2 ring-brand-400/60'
                              : 'bg-surface-700 text-gray-300 hover:bg-surface-600'
                          } ${isSavedChoice && !isActive ? 'outline outline-1 outline-emerald-500/70' : ''}`}
                        >
                          {title}
                          {isSavedChoice ? ' ✓' : ''}
                        </button>
                      )
                    })}
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <label className="text-xs text-gray-400">
                      Failure mode {label === 'n' ? '(required)' : '(if miss / n)'}
                      <select
                        className="mt-1 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm text-white"
                        value={failureMode}
                        onChange={(e) => {
                          const v = e.target.value
                          setFailureMode(v)
                          if (label === 'n' && v) {
                            void saveLabel({
                              nextLabel: 'n',
                              nextFailureMode: v,
                              advance: false,
                            })
                          }
                        }}
                      >
                        <option value="">—</option>
                        {(detail.failure_modes || []).map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="text-xs text-gray-400">
                      Notes
                      <input
                        className="mt-1 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm text-white"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        onBlur={() => {
                          if (savedDecision && decisionDirty && !(label === 'n' && !failureMode)) {
                            void saveLabel({ advance: false })
                          }
                        }}
                        placeholder="e.g. gold off-topic; near-miss at rank 12"
                      />
                    </label>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      disabled={busy || !decisionDirty}
                      onClick={() => void saveLabel({ advance: true })}
                      className="rounded bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-50"
                    >
                      {savedDecision ? 'Update & next' : 'Save & next'}
                    </button>
                    <button
                      type="button"
                      disabled={!selected || selectedIdx >= queue.length - 1}
                      onClick={() => setSelectedIdx((i) => i + 1)}
                      className="rounded px-3 py-2 text-sm text-gray-400 hover:text-white"
                    >
                      Skip →
                    </button>
                    {decisionDirty && savedDecision && (
                      <span className="text-xs text-amber-300">Unsaved edits</span>
                    )}
                  </div>
                </section>

                {detail.evaluations.length > 0 && (
                  <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
                    <h3 className="text-sm font-semibold text-gray-300">Prior evaluations</h3>
                    <div className="mt-2 space-y-2">
                      {detail.evaluations.map((e) => (
                        <div
                          key={`${e.evaluator_kind}-${e.auditor_id}`}
                          className="rounded bg-surface-900 px-3 py-2 text-xs text-gray-300"
                        >
                          <span className="font-mono text-brand-400">
                            {e.evaluator_kind}/{e.auditor_id}
                          </span>
                          {' · '}
                          label={e.label_correct ?? '—'}
                          {e.failure_mode ? ` · ${e.failure_mode}` : ''}
                          {e.reasoning_summary && (
                            <p className="mt-1 text-gray-400">{e.reasoning_summary}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {tab === 'checklist' && (
        <div className="space-y-4">
          <div className="rounded border border-surface-600 bg-surface-800 p-4 text-sm text-gray-300">
            <p className="font-medium text-white">How to verify the paper (no DB needed)</p>
            <ol className="mt-2 list-decimal space-y-1 pl-5">
              <li>
                Open PDF:{' '}
                <code className="text-brand-400">papers/ieee-vector-drift/access/main.pdf</code>
              </li>
              <li>
                Numbers source:{' '}
                <code className="text-brand-400">artifacts/published/CANONICAL_METRICS.json</code>
              </li>
              <li>Tick each item below as you confirm it (status → done).</li>
              <li>
                Full list also in{' '}
                <code className="text-brand-400">papers/ieee-vector-drift/access/CHECKLIST_ACCESS.md</code>
              </li>
            </ol>
          </div>
          {checklist.map((item) => (
            <div
              key={item.claim_key}
              className="rounded-lg border border-surface-600 bg-surface-800 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="max-w-3xl">
                  <p className="text-xs uppercase tracking-wide text-gray-500">{item.category}</p>
                  <h3 className="font-medium text-white">{item.title}</h3>
                  <p className="mt-1 text-sm text-gray-400">{item.detail}</p>
                </div>
                <select
                  className="rounded border border-surface-600 bg-surface-900 px-2 py-1 text-sm"
                  value={item.status}
                  onChange={(e) =>
                    void saveCheckItem(item, {
                      status: e.target.value,
                      label_correct: e.target.value === 'done' ? 'y' : item.label_correct,
                    })
                  }
                >
                  <option value="pending">pending</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                  <option value="skipped">skipped</option>
                </select>
              </div>
              <input
                className="mt-2 w-full rounded border border-surface-600 bg-surface-900 px-2 py-1.5 text-sm text-white"
                placeholder="notes (what you checked)"
                defaultValue={item.notes || ''}
                onBlur={(e) => {
                  if (e.target.value !== (item.notes || '')) {
                    void saveCheckItem(item, { notes: e.target.value })
                  }
                }}
              />
            </div>
          ))}
        </div>
      )}

      {tab === 'overview' && overview && (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
              Formulas
            </h2>
            <ul className="mt-3 space-y-2 text-sm text-gray-200">
              <li>
                <span className="text-gray-500">Hit@k:</span> {overview.formulas.hit_at_k}
              </li>
              <li>
                <span className="text-gray-500">Scaling:</span>{' '}
                <code className="text-brand-400">{overview.formulas.scaling}</code>
              </li>
              <li>
                <span className="text-gray-500">Δ meta:</span>{' '}
                <code className="text-brand-400">{overview.formulas.delta_meta}</code>
              </li>
            </ul>
            <pre className="mt-3 overflow-auto rounded bg-surface-900 p-2 text-xs text-gray-400">
              {JSON.stringify(
                {
                  fit_hit_at_10: overview.fit.fit_hit_at_10,
                  n0: overview.fit.n0,
                  tau: overview.fit.tau,
                },
                null,
                2,
              )}
            </pre>
          </section>
          <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
              Progress by scale
            </h2>
            <table className="mt-2 w-full text-left text-sm">
              <thead className="text-xs text-gray-500">
                <tr>
                  <th className="py-1">N</th>
                  <th>cond</th>
                  <th>labeled</th>
                  <th>samples</th>
                </tr>
              </thead>
              <tbody>
                {overview.progress_by_scale.map((r) => (
                  <tr
                    key={`${r.corpus_scale_size}-${r.condition}`}
                    className="border-t border-surface-700"
                  >
                    <td className="py-1 font-mono">{r.corpus_scale_size}</td>
                    <td>{r.condition}</td>
                    <td>{r.n_labeled}</td>
                    <td>{r.n_samples}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      )}

      {tab === 'llm' && (
        <div className="space-y-4 text-sm text-gray-300">
          <p>
            LLM triage already ran on the stratified queue. Use it as a hint on each row — your
            human label wins for the paper.
          </p>
          <div className="rounded border border-surface-600 bg-surface-800 p-4">
            File report: {llmReport?.file_report ? `${llmReport.file_report.n_evaluated ?? 0} rows` : '—'}{' '}
            · DB LLM rows: {llmReport?.db_llm_count ?? 0}
          </div>
          {llmReport?.file_report?.paper_paragraph_draft && (
            <div className="rounded border border-surface-600 bg-surface-800 p-4">
              <h3 className="text-xs font-semibold uppercase text-gray-500">Draft paragraph</h3>
              <p className="mt-2">{llmReport.file_report.paper_paragraph_draft}</p>
            </div>
          )}
        </div>
      )}

      {tab === 'export' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <a
              href="/api/audit/export?format=csv"
              className="rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
            >
              Download labeled CSV
            </a>
            <button
              type="button"
              className="rounded border border-surface-600 px-4 py-2 text-sm text-gray-200"
              onClick={() => void loadExport('markdown')}
            >
              Preview paper blurb
            </button>
          </div>
          {exportPreview && (
            <pre className="max-h-[480px] overflow-auto rounded border border-surface-600 bg-surface-900 p-4 text-xs text-gray-300">
              {exportPreview}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border border-surface-600 bg-surface-800 px-3 py-3">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-white">{value}</p>
      <p className="text-xs text-gray-500">{sub}</p>
    </div>
  )
}

function Badge({ ok, children }: { ok: boolean; children: ReactNode }) {
  return (
    <span
      className={`rounded px-2 py-0.5 font-mono ${
        ok ? 'bg-emerald-950 text-emerald-300' : 'bg-amber-950 text-amber-300'
      }`}
    >
      {children}
    </span>
  )
}

function ChunkPanel({
  title,
  chunks,
  gold,
}: {
  title: string
  chunks: Chunk[]
  gold?: boolean
}) {
  return (
    <section className="rounded-lg border border-surface-600 bg-surface-800 p-4">
      <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
      <p className="mt-0.5 text-xs text-gray-500">
        {chunks.length} document(s) · full text expanded
      </p>
      <div className="mt-3 space-y-3">
        {chunks.length === 0 && (
          <p className="text-sm text-amber-400">No documents — cannot audit this row yet.</p>
        )}
        {chunks.map((c) => (
          <div
            key={`${c.doc_id}-${c.rank ?? 'g'}`}
            className={`rounded border px-3 py-2 ${
              c.is_gold || gold
                ? 'border-emerald-700 bg-emerald-950/30'
                : 'border-surface-700 bg-surface-900'
            }`}
          >
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {c.rank != null && (
                <span className="rounded bg-surface-800 px-1.5 font-mono text-gray-300">#{c.rank}</span>
              )}
              <span className="font-mono text-brand-400">{c.doc_id}</span>
              {c.is_gold && (
                <span className="rounded bg-emerald-800 px-1.5 text-emerald-100">GOLD MATCH</span>
              )}
              {c.source && <span className="text-gray-600">via {c.source}</span>}
            </div>
            {(c.title || c.source_type) && (
              <p className="mt-1 text-xs text-gray-500">
                {c.title} {c.source_type ? `· ${c.source_type}` : ''}
              </p>
            )}
            <div className="mt-2">
              <TruncText text={c.preview || ''} max={50000} defaultOpen />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
