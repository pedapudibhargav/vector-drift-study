import { useRef, useEffect } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'
import type { ChatMessage } from '../../types'

interface ChatPanelProps {
  messages: ChatMessage[]
  input: string
  isStreaming: boolean
  onInputChange: (value: string) => void
  onSubmit: () => void
}

export default function ChatPanel({
  messages,
  input,
  isStreaming,
  onInputChange,
  onSubmit,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">Research Chat</h2>
        <p className="text-xs text-gray-500">
          Query the vector index and observe retrieval transparency
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-900">Start a research query</p>
              <p className="mt-1 text-xs text-gray-500">
                Ask about retrieved documents, corpus scaling, or Hit@k drift behavior
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-brand-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about the corpus..."
            rows={2}
            disabled={isStreaming}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
          />
          <button
            onClick={onSubmit}
            disabled={isStreaming || !input.trim()}
            className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 text-white hover:bg-brand-700 disabled:opacity-50"
          >
            <PaperAirplaneIcon className="size-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
