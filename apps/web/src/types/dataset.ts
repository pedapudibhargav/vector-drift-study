export interface StageCount {
  complete: number
  total: number
}

export interface CorpusScaleSummary {
  snapshot: string
  total: number
  noise: number
  group_200: number
}

export interface DatasetSummary {
  total_ingested: number
  group_200_count: number
  noise_batch_count: number
  manifest_available: boolean
  manifest_url?: string
  html_ready?: number
  db_available: boolean
  corpus_scales?: CorpusScaleSummary[]
  stages?: {
    identified: StageCount
    text_ingested: StageCount
    embedded: StageCount
  }
  ingestion?: Record<string, number>
  crawl?: Record<string, unknown>
  document_chunks?: number
  embedded_chunks?: number
}

export type PipelineStage = 'identified' | 'text_ingested' | 'embedded' | 'failed'

export interface DatasetUrl {
  id?: number
  url: string
  title: string
  corpus_group: string | null
  corpus_scale: string | null
  tier_group: string | null
  service_category: string | null
  page_type: string | null
  doc_type?: string | null
  is_primary: boolean
  status: number | string
  identified_at?: string | null
  ingestion_status?: string
  pipeline_stage?: PipelineStage | string
  current_stage?: string
  chunk_count?: number
  gold_chunk_count?: number
  non_gold_chunk_count?: number
  has_chunks?: boolean
}

export interface DatasetUrlList {
  items: DatasetUrl[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CrawlProgress {
  stored?: number
  target?: number
  fetched?: number
  primary_stored?: number
  primary_in_db?: number
  skipped_non_200?: number
  skipped_duplicate?: number
  skipped_invalid_html?: number
  queue?: number
  total_in_db?: number
  url_count?: number
  html_ready?: number
  html_stored?: number
  text_ready?: number
  inserted?: number
  backfilled?: number
  elapsed_s?: number
  mode?: string
  run_id?: number
  resumed?: boolean
  url?: string
  title?: string
  message?: string
}

export interface IngestWorkerStatus {
  ingest_running: boolean
  ingest_processed: number
  ingest_passed: number
  ingest_failed: number
  ingest_chunks_added?: number
  text_ingested?: number
  document_chunks?: number
  pending?: number
  text_failed?: number
  quality_sample?: {
    sample_size: number
    avg_tokens: number
    max_tokens: number
    over_max: number
    under_min: number
  } | null
  pipeline?: Record<string, number>
}

export interface IngestProgress {
  limit?: number
  processed?: number
  passed?: number
  failed?: number
  url?: string
  text_preview?: string
  chunk_previews?: { index: number; tokens: number; preview: string }[]
  gates?: Record<string, unknown>
  message?: string
}
