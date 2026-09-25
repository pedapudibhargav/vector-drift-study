/** Lightweight markdown preview for chunk text (headings, links, lists). */

import type { ReactNode } from 'react'

const INLINE_RE = /(\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*)/g

function inlineFormat(text: string): ReactNode[] {
  const parts: ReactNode[] = []
  let last = 0
  let m: RegExpExecArray | null
  let key = 0
  const re = new RegExp(INLINE_RE.source, 'g')
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index))
    if (m[2] && m[3]) {
      parts.push(
        <a key={key++} href={m[3]} target="_blank" rel="noopener noreferrer" className="text-brand-400 underline">
          {m[2]}
        </a>,
      )
    } else if (m[4]) {
      parts.push(<strong key={key++} className="font-semibold text-gray-200">{m[4]}</strong>)
    }
    last = m.index + m[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts.length ? parts : [text]
}

export default function MarkdownPreview({ content }: { content: string }) {
  const lines = content.split('\n')
  const nodes: ReactNode[] = []
  let key = 0

  for (const line of lines) {
    const h6 = line.match(/^######\s+(.+)/)
    const h5 = line.match(/^#####\s+(.+)/)
    const h4 = line.match(/^####\s+(.+)/)
    const h3 = line.match(/^###\s+(.+)/)
    const h2 = line.match(/^##\s+(.+)/)
    const h1 = line.match(/^#\s+(.+)/)
    const li = line.match(/^\s*[-*]\s+(.+)/)

    if (h6) nodes.push(<h6 key={key++} className="mb-1 mt-3 text-xs font-semibold text-gray-300">{inlineFormat(h6[1])}</h6>)
    else if (h5) nodes.push(<h5 key={key++} className="mb-1 mt-3 text-sm font-semibold text-gray-300">{inlineFormat(h5[1])}</h5>)
    else if (h4) nodes.push(<h4 key={key++} className="mb-1 mt-3 text-sm font-semibold text-gray-200">{inlineFormat(h4[1])}</h4>)
    else if (h3) nodes.push(<h3 key={key++} className="mb-2 mt-4 text-base font-semibold text-white">{inlineFormat(h3[1])}</h3>)
    else if (h2) nodes.push(<h2 key={key++} className="mb-2 mt-4 text-lg font-semibold text-white">{inlineFormat(h2[1])}</h2>)
    else if (h1) nodes.push(<h1 key={key++} className="mb-3 mt-4 text-xl font-bold text-white">{inlineFormat(h1[1])}</h1>)
    else if (li) nodes.push(<li key={key++} className="ml-4 list-disc text-sm text-gray-300">{inlineFormat(li[1])}</li>)
    else if (line.trim() === '') nodes.push(<div key={key++} className="h-2" />)
    else nodes.push(<p key={key++} className="text-sm leading-relaxed text-gray-300">{inlineFormat(line)}</p>)
  }

  return <div className="space-y-0.5">{nodes}</div>
}
