import { useState } from 'react'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import { MessageSquare, FileText } from 'lucide-react'

function App() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'documents'>('chat')

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-white">
      {/* Minimal header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-gray-900">Chat AI</span>
        </div>
        <nav className="flex items-center gap-1 bg-gray-100 rounded-full p-1">
          <button
            onClick={() => setCurrentPage('chat')}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              currentPage === 'chat'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            チャット
          </button>
          <button
            onClick={() => setCurrentPage('documents')}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              currentPage === 'documents'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <FileText className="w-4 h-4" />
            ドキュメント
          </button>
        </nav>
      </header>

      {/* Page content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {currentPage === 'chat' ? <Chat /> : <Documents />}
      </main>
    </div>
  )
}

export default App
