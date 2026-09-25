import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import ChatPage from './pages/ChatPage'
import ComparePage from './pages/ComparePage'
import CorpusPage from './pages/CorpusPage'
import DocsPage from './pages/DocsPage'
import ReviewPage from './pages/ReviewPage'

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<ChatPage />} />
          <Route path="/corpus" element={<CorpusPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
