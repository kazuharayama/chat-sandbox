import { useState, useCallback, useEffect } from 'react';
import { apiService } from '../services/api';
import type { Session } from '../services/api';
import ChatWindow from '../components/ChatWindow';
import MessageInput from '../components/MessageInput';
import { MessageSquare, Plus, Trash2, PanelLeftClose, PanelLeftOpen } from 'lucide-react';

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sources?: string[];
}

function getDocumentType(file: File): string {
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  const map: Record<string, string> = {
    pdf: 'pdf', txt: 'text', md: 'markdown', csv: 'csv',
    png: 'image', jpg: 'image', jpeg: 'image', gif: 'image',
    bmp: 'image', webp: 'image',
  };
  return map[ext] || 'text';
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Load sessions on mount
  useEffect(() => {
    apiService.listSessions().then(setSessions).catch(console.error);
  }, []);

  const refreshSessions = async () => {
    const list = await apiService.listSessions();
    setSessions(list);
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  };

  const handleSelectSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setError(null);
    try {
      const msgs = await apiService.getSessionMessages(sessionId);
      setMessages(
        msgs.map((m) => ({
          id: m.id,
          content: m.content,
          sender: m.role as 'user' | 'bot',
          timestamp: new Date(m.created_at),
          sources: m.sources,
        }))
      );
    } catch {
      setError('履歴の読み込みに失敗しました');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    await apiService.deleteSession(sessionId);
    if (currentSessionId === sessionId) handleNewChat();
    await refreshSessions();
  };

  const handleSendMessage = useCallback(
    async (content: string, file?: File) => {
      const userMessage: Message = {
        id: Date.now().toString(),
        content: file
          ? `${content || 'ファイルをアップロードしました'}\n📎 ${file.name}`
          : content,
        sender: 'user',
        timestamp: new Date(),
      };

      const botId = (Date.now() + 1).toString();

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      try {
        if (file) {
          await apiService.uploadDocument({
            file,
            document_type: getDocumentType(file),
          });
        }

        // Add empty bot message for streaming
        setMessages((prev) => [
          ...prev,
          { id: botId, content: '', sender: 'bot', timestamp: new Date(), sources: [] },
        ]);

        await apiService.sendMessageStream(
          {
            message: content || `${file?.name} の内容を教えてください`,
            session_id: currentSessionId,
            language: '日本語',
            hasAttachment: !!file,
            use_rag: true,
          },
          {
            onToken: (token) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, content: m.content + token } : m
                )
              );
            },
            onSession: (sessionId) => {
              setCurrentSessionId(sessionId);
            },
            onSources: (sources) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, sources } : m
                )
              );
            },
            onDone: () => {
              setLoading(false);
              refreshSessions();
            },
            onError: (err) => {
              setError(err.message);
              setLoading(false);
            },
          }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
        setLoading(false);
      }
    },
    [currentSessionId]
  );

  return (
    <div className="flex h-full bg-white">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden transition-all duration-200`}>
        <div className="p-3 flex items-center gap-2">
          <button
            onClick={handleNewChat}
            className="flex-1 flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            新しいチャット
          </button>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            title="サイドバーを閉じる"
          >
            <PanelLeftClose className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-center gap-1 px-3 py-2 mb-0.5 rounded-lg cursor-pointer text-sm transition-colors ${
                currentSessionId === session.id
                  ? 'bg-gray-200 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
              onClick={() => handleSelectSession(session.id)}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0 text-gray-400" />
              <span className="flex-1 truncate">{session.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteSession(session.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Sidebar open button (shown when closed) */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute top-20 left-4 z-10 p-3 text-gray-400 hover:text-gray-600 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
            title="サイドバーを開く"
          >
            <PanelLeftOpen className="w-5 h-5" />
          </button>
        )}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-100">
            <p className="text-sm text-red-600 text-center">{error}</p>
          </div>
        )}
        <ChatWindow messages={messages} loading={loading} />
        <MessageInput onSendMessage={handleSendMessage} disabled={loading} />
      </div>
    </div>
  );
}
