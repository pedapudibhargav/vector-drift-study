import { useCallback, useState } from 'react'
import ChatPanel from '../components/chat/ChatPanel'
import ApiDetailsPanel from '../components/chat/ApiDetailsPanel'
import BackendNotice from '../components/shared/BackendNotice'
import ConnectionStatus from '../components/shared/ConnectionStatus'
import { isGhPagesHost, streamChat } from '../lib/api'
import type { ApiCallEvent, ChatMessage } from '../types'

let msgCounter = 0
const nextId = () => `msg-${++msgCounter}`

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [apiEvents, setApiEvents] = useState<ApiCallEvent[]>([])

  const handleSubmit = useCallback(async () => {
    const text = input.trim()
    if (!text || isStreaming) return

    if (isGhPagesHost()) {
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'user', content: text },
        {
          id: nextId(),
          role: 'assistant',
          content:
            'Backend is not available on GitHub Pages. Please run the Docker setup locally with your API keys.',
        },
      ])
      setInput('')
      return
    }

    const userMsg: ChatMessage = { id: nextId(), role: 'user', content: text }
    const assistantId = nextId()
    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '' }])
    setInput('')
    setIsStreaming(true)
    setApiEvents([])

    try {
      for await (const event of streamChat(text)) {
        const apiEvent: ApiCallEvent = {
          id: nextId(),
          timestamp: new Date().toISOString(),
          event: event.event,
          data: event.data,
        }
        setApiEvents((prev) => [...prev, apiEvent])

        if (event.event === 'token') {
          const token = (event.data.content as string) ?? ''
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m,
            ),
          )
        }

        if (event.event === 'error') {
          const errMsg = (event.data.message as string) ?? 'Unknown error'
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: `Error: ${errMsg}` } : m,
            ),
          )
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Connection error: ${err instanceof Error ? err.message : 'Unknown'}` }
            : m,
        ),
      )
    } finally {
      setIsStreaming(false)
    }
  }, [input, isStreaming])

  return (
    <div>
      {isGhPagesHost() && <BackendNotice />}
      <ConnectionStatus />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChatPanel
          messages={messages}
          input={input}
          isStreaming={isStreaming}
          onInputChange={setInput}
          onSubmit={handleSubmit}
        />
        <ApiDetailsPanel events={apiEvents} isStreaming={isStreaming} />
      </div>
    </div>
  )
}
