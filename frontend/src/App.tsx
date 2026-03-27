import { useState } from 'react'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import Admin from './pages/Admin'
import { MessageSquare, FileText, Settings, Activity } from 'lucide-react'

type Page = 'chat' | 'documents' | 'admin'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('chat')

  const tabs: { page: Page; icon: React.ReactNode; label: string }[] = [
    { page: 'chat', icon: <MessageSquare className="w-4 h-4" />, label: 'チャット' },
    { page: 'documents', icon: <FileText className="w-4 h-4" />, label: 'ドキュメント' },
    { page: 'admin', icon: <Settings className="w-4 h-4" />, label: '管理' },
  ]

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-white">
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-gray-900">Chat AI</span>
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-blue-500 transition-colors"
            title="Langfuse トレース"
          >
            <Activity className="w-3.5 h-3.5" />
            Langfuse
          </a>
        </div>
        <nav className="flex items-center gap-1 bg-gray-100 rounded-full p-1">
          {tabs.map(tab => (
            <button
              key={tab.page}
              onClick={() => setCurrentPage(tab.page)}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                currentPage === tab.page
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 overflow-hidden flex flex-col">
        {currentPage === 'chat' && <Chat />}
        {currentPage === 'documents' && <Documents />}
        {currentPage === 'admin' && <Admin />}
      </main>
    </div>
  )
}

export default App
