import { useEffect, useState } from 'react'
import { fetchHealth, isGhPagesHost } from '../../lib/api'
import type { HealthStatus } from '../../types'

export default function ConnectionStatus() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (isGhPagesHost()) return

    fetchHealth()
      .then(async (res) => {
        if (res.ok) setHealth(await res.json())
        else setError(true)
      })
      .catch(() => setError(true))
  }, [])

  if (isGhPagesHost()) return null

  const dotColor = error
    ? 'bg-red-500'
    : health?.status === 'healthy'
      ? 'bg-green-500'
      : 'bg-amber-500'

  const label = error
    ? 'Backend unreachable'
    : health
      ? `${health.status} — PG: ${health.postgres}, Vector: ${health.vector_db}, OpenAI: ${health.openai}`
      : 'Checking...'

  return (
    <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
      <span className={`size-2 rounded-full ${dotColor}`} />
      {label}
    </div>
  )
}
