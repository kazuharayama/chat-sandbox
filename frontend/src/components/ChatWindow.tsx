import { useEffect, useRef } from 'react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ChatWindowProps {
  messages: Message[];
  loading?: boolean;
}

export default function ChatWindow({ messages, loading = false }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-gray-400 text-lg mb-2">Welcome to Chat</div>
              <div className="text-gray-500 text-sm">Start a conversation by typing a message</div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                  message.sender === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </div>
                <div
                  className={`text-xs mt-2 ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Example messages for demonstration */}
        {messages.length === 0 && (
          <>
            <div className="flex justify-start">
              <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-gray-100 text-gray-900">
                <div className="text-sm leading-relaxed">AI answer</div>
              </div>
            </div>
            <div className="flex justify-end">
              <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-blue-50 text-gray-700 border border-gray-200">
                <div className="text-sm leading-relaxed">User questing or asking</div>
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-gray-100 text-gray-900">
                <div className="text-sm leading-relaxed">AI answer</div>
              </div>
            </div>
            <div className="flex justify-end">
              <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-blue-50 text-gray-700 border border-gray-200">
                <div className="text-sm leading-relaxed">User questing or asking</div>
              </div>
            </div>
          </>
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-gray-100 text-gray-900">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-gray-500">AI is typing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
} 