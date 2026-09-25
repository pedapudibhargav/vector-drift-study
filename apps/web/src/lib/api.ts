import type { NdjsonEvent } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export function isGhPagesHost(): boolean {
  if (typeof window === 'undefined') return false
  return window.location.hostname.endsWith('github.io')
}

export async function fetchHealth(): Promise<Response> {
  return fetch(`${API_BASE}/api/health`)
}

export async function* streamChat(
  message: string,
  options: { topK?: number; useMetadataFilter?: boolean } = {},
): AsyncGenerator<NdjsonEvent> {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      top_k: options.topK ?? 5,
      use_metadata_filter: options.useMetadataFilter ?? false,
    }),
  })

  if (!response.ok) {
    throw new Error(`Chat stream failed: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.trim()) {
        yield JSON.parse(line) as NdjsonEvent
      }
    }
  }

  if (buffer.trim()) {
    yield JSON.parse(buffer) as NdjsonEvent
  }
}
