import { Link, Outlet, useLocation } from 'react-router-dom'
import {
  ChartBarSquareIcon,
  ChatBubbleLeftRightIcon,
  CircleStackIcon,
  ClipboardDocumentCheckIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'

const topNavigation = [
  { name: 'Chat', href: '/', icon: ChatBubbleLeftRightIcon },
  { name: 'Corpus', href: '/corpus', icon: CircleStackIcon },
  { name: 'Compare', href: '/compare', icon: ChartBarSquareIcon },
  { name: 'Review', href: '/review', icon: ClipboardDocumentCheckIcon },
  { name: 'Documentation', href: '/docs', icon: DocumentTextIcon },
]

export default function AppShell() {
  const location = useLocation()
  const wide = location.pathname === '/review'

  return (
    <div className="min-h-screen bg-surface-900">
      <nav className="border-b border-surface-600 bg-surface-800">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="flex size-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
                VD
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Vector Drift</p>
                <p className="text-xs text-gray-500">EnterpriseRAG Scaling Study</p>
              </div>
            </Link>
            <div className="hidden sm:flex sm:items-center sm:gap-x-1">
              {topNavigation.map((item) => {
                const active = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
                      active
                        ? 'bg-brand-600/20 text-brand-400'
                        : 'text-gray-400 hover:bg-surface-700 hover:text-gray-200'
                    }`}
                  >
                    <item.icon className="size-4" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </nav>
      <main
        className={`mx-auto px-4 py-6 sm:px-6 lg:px-8 ${wide ? 'max-w-[1400px]' : 'max-w-7xl'}`}
      >
        <Outlet />
      </main>
    </div>
  )
}
