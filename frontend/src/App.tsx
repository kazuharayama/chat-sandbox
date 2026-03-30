import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import Admin from './pages/Admin'
import ContextLab from './pages/ContextLab'
import AuthGuard from './auth/AuthGuard'
import { isAuthEnabled } from './auth/msalConfig'
import { useMsal } from '@azure/msal-react'
import { useAuthSetup } from './auth/useAuthSetup'
import { MessageSquare, FileText, Settings, Activity, FlaskConical, LogOut } from 'lucide-react'

const tabs = [
  { path: '/', icon: <MessageSquare className="w-4 h-4" />, label: 'チャット' },
  { path: '/documents', icon: <FileText className="w-4 h-4" />, label: 'ドキュメント' },
  { path: '/context-lab', icon: <FlaskConical className="w-4 h-4" />, label: 'Context Lab' },
  { path: '/admin', icon: <Settings className="w-4 h-4" />, label: '管理' },
]

function UserMenu() {
  const { instance, accounts } = useMsal();
  const account = accounts[0];
  if (!account) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500">{account.name || account.username}</span>
      <button
        onClick={() => instance.logoutRedirect()}
        className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
        title="ログアウト"
      >
        <LogOut className="w-4 h-4" />
      </button>
    </div>
  );
}

function App() {
  useAuthSetup();

  return (
    <AuthGuard>
      <div className="flex flex-col h-screen w-full overflow-hidden bg-white">
        <header className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <NavLink to="/" className="text-lg font-semibold text-gray-900 hover:text-gray-700 transition-colors">
              Chat AI
            </NavLink>
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
          <div className="flex items-center gap-3">
            <nav className="flex items-center gap-1 bg-gray-100 rounded-full p-1">
              {tabs.map(tab => (
                <NavLink
                  key={tab.path}
                  to={tab.path}
                  end={tab.path === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`
                  }
                >
                  {tab.icon}
                  {tab.label}
                </NavLink>
              ))}
            </nav>
            {isAuthEnabled && <UserMenu />}
          </div>
        </header>

        <main className="flex-1 overflow-hidden flex flex-col">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/context-lab" element={<ContextLab />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </AuthGuard>
  )
}

export default App
