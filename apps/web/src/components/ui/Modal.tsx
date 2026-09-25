import { useEffect, useId, type ReactNode } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: ReactNode
  subtitle?: ReactNode
  meta?: ReactNode
  children: ReactNode
  size?: 'md' | 'lg' | 'xl'
}

const SIZE_CLASS = {
  md: 'max-w-2xl',
  lg: 'max-w-4xl',
  xl: 'max-w-5xl',
} as const

export default function Modal({ open, onClose, title, subtitle, meta, children, size = 'lg' }: ModalProps) {
  const titleId = useId()

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="relative z-50" role="presentation">
      <div className="fixed inset-0 bg-black/70" aria-hidden="true" onClick={onClose} />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          className={`flex max-h-[90vh] w-full ${SIZE_CLASS[size]} flex-col overflow-hidden rounded-xl border border-surface-600 bg-surface-800 shadow-2xl`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex shrink-0 items-start justify-between border-b border-surface-600 px-5 py-4">
            <div className="min-w-0 pr-4">
              <h2 id={titleId} className="truncate text-base font-semibold text-white">
                {title}
              </h2>
              {subtitle && <p className="mt-0.5 truncate text-xs text-gray-500">{subtitle}</p>}
              {meta && <div className="mt-1 text-xs text-gray-400">{meta}</div>}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1 text-gray-400 hover:bg-surface-700 hover:text-white"
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="size-5" />
            </button>
          </div>

          <div className="flex min-h-0 flex-1 flex-col">{children}</div>
        </div>
      </div>
    </div>
  )
}
