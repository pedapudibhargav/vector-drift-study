import { useId, useState, type KeyboardEvent, type ReactNode } from 'react'

export interface TabItem {
  id: string
  label: ReactNode
  content: ReactNode
}

interface TabsProps {
  items: TabItem[]
  defaultIndex?: number
  className?: string
}

export default function Tabs({ items, defaultIndex = 0, className = '' }: TabsProps) {
  const baseId = useId()
  const [selected, setSelected] = useState(defaultIndex)

  if (items.length === 0) return null

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const delta = e.key === 'ArrowRight' ? 1 : -1
    setSelected((i) => (i + delta + items.length) % items.length)
  }

  return (
    <div className={`flex min-h-0 flex-1 flex-col ${className}`}>
      <div
        role="tablist"
        aria-orientation="horizontal"
        className="flex shrink-0 gap-1 overflow-x-auto border-b border-surface-600 bg-surface-900/50 px-4"
        onKeyDown={onKeyDown}
      >
        {items.map((item, index) => {
          const active = selected === index
          const tabId = `${baseId}-tab-${item.id}`
          const panelId = `${baseId}-panel-${item.id}`
          return (
            <button
              key={item.id}
              id={tabId}
              type="button"
              role="tab"
              aria-selected={active}
              aria-controls={panelId}
              tabIndex={active ? 0 : -1}
              onClick={() => setSelected(index)}
              className={[
                'shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors outline-none',
                active
                  ? 'border-brand-500 text-white'
                  : 'border-transparent text-gray-400 hover:border-surface-600 hover:text-gray-200',
              ].join(' ')}
            >
              {item.label}
            </button>
          )
        })}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {items.map((item, index) => {
          const tabId = `${baseId}-tab-${item.id}`
          const panelId = `${baseId}-panel-${item.id}`
          const active = selected === index
          return (
            <div
              key={item.id}
              id={panelId}
              role="tabpanel"
              aria-labelledby={tabId}
              hidden={!active}
              tabIndex={0}
              className="outline-none"
            >
              {active ? item.content : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
