import { MessageSquare, Settings, User } from 'lucide-react';

interface ChatHistoryItem {
  id: string;
  title: string;
  timestamp: Date;
}

interface SidebarProps {
  chatHistory: ChatHistoryItem[];
  onSelectChat: (chatId: string) => void;
  activeChatId?: string;
}

export default function Sidebar({ chatHistory, onSelectChat, activeChatId }: SidebarProps) {
  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold text-gray-900">Chat History</h1>
        </div>
      </div>

      {/* Chat History List */}
      <div className="flex-1 overflow-y-auto p-2">
        {chatHistory.map((chat) => (
          <button
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={`w-full text-left p-3 rounded-lg mb-2 transition-colors hover:bg-gray-50 ${
              activeChatId === chat.id ? 'bg-blue-50 border border-blue-200' : ''
            }`}
          >
            <div className="text-sm font-medium text-gray-900 truncate">
              {chat.title}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {chat.timestamp.toLocaleDateString()}
            </div>
          </button>
        ))}
        
        {/* Placeholder items when no history */}
        {chatHistory.length === 0 && (
          <>
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="w-full p-3 rounded-lg mb-2 bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="text-sm text-gray-400">xxxxxxxxxx</div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* User Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600" />
            </div>
            <span className="text-sm font-medium text-gray-900">User name</span>
          </div>
          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
            <Settings className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  );
} 