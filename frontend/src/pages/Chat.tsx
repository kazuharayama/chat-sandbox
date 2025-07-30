import { useState } from 'react';
import { apiService } from '../services/api';
import ChatWindow from '../components/ChatWindow';
import MessageInput from '../components/MessageInput';
import { MessageSquare, Settings, User } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.sendMessage({
        message: content,
        language: '日本語',
        hasAttachment: false,
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAttachFile = () => {
    // TODO: ファイル添付機能の実装
    console.log('ファイル添付機能（未実装）');
  };

  const handleStartRecording = () => {
    // TODO: 音声録音機能の実装
    console.log('音声録音機能（未実装）');
  };

  return (
    <div className="flex flex-1 h-full bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-semibold text-gray-900">Chat AI</h1>
          </div>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className="mb-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              最近の会話
            </h3>
            {Array.from({ length: 5 }, (_, i) => (
              <div 
                key={i} 
                className="p-3 mb-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
              >
                会話履歴 {i + 1}
              </div>
            ))}
          </div>
        </div>

        {/* User Section */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-gray-600" />
              </div>
              <span className="text-sm font-medium text-gray-700">ユーザー</span>
            </div>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-white overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">AI アシスタント</h2>
              <p className="text-sm text-gray-500">
                {loading ? 'AI が返答を生成中...' : 'オンライン'}
              </p>
            </div>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 px-3 py-1 rounded-lg">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <ChatWindow messages={messages} loading={loading} />

        {/* Input */}
        <MessageInput
          onSendMessage={handleSendMessage}
          onAttachFile={handleAttachFile}
          onStartRecording={handleStartRecording}
          disabled={loading}
        />
      </div>
    </div>
  );
}
