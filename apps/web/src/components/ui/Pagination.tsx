import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/20/solid'

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

function pageRange(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages: (number | 'ellipsis')[] = [1]
  if (current > 3) pages.push('ellipsis')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('ellipsis')
  pages.push(total)
  return pages
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  const pages = pageRange(page, totalPages)

  return (
    <nav className="flex items-center justify-center gap-1" aria-label="Pagination">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium text-gray-300 ring-1 ring-surface-600 hover:bg-surface-700 disabled:opacity-40"
      >
        <ChevronLeftIcon className="size-4" />
        Previous
      </button>

      <div className="hidden sm:flex sm:items-center sm:gap-1">
        {pages.map((p, i) =>
          p === 'ellipsis' ? (
            <span key={`e-${i}`} className="px-2 text-gray-500">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              aria-current={p === page ? 'page' : undefined}
              className={`min-w-9 rounded-md px-3 py-2 text-sm font-medium ${
                p === page
                  ? 'bg-brand-600 text-white'
                  : 'text-gray-300 ring-1 ring-surface-600 hover:bg-surface-700'
              }`}
            >
              {p}
            </button>
          ),
        )}
      </div>

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium text-gray-300 ring-1 ring-surface-600 hover:bg-surface-700 disabled:opacity-40"
      >
        Next
        <ChevronRightIcon className="size-4" />
      </button>
    </nav>
  )
}
