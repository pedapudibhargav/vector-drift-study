export interface NdjsonEvent {
  event: string
  data: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface HealthStatus {
  status: string
  openai: string
  vector_db: string
  postgres: string
  version: string
}

export interface ApiCallEvent {
  id: string
  timestamp: string
  event: string
  data: Record<string, unknown>
}
