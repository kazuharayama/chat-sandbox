import { useState } from 'react'
import Chat from './pages/Chat'
import Documents from './pages/Documents'

function App() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'documents'>('chat')

  // ページ切り替え関数
  const navigateTo = (page: 'chat' | 'documents') => {
    setCurrentPage(page)
  }

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      {/* ナビゲーションヘッダー */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">Chat AI</h1>
              </div>
              <nav className="ml-6 flex space-x-8">
                <button
                  onClick={() => navigateTo('chat')}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    currentPage === 'chat'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  チャット
                </button>
                <button
                  onClick={() => navigateTo('documents')}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    currentPage === 'documents'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  ドキュメント管理
                </button>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* ページコンテンツ */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {currentPage === 'chat' ? <Chat /> : <Documents />}
      </main>
    </div>
  )
}

export default App
