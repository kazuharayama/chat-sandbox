import { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  fileName?: string;
}

interface ChatWindowProps {
  messages: Message[];
  loading?: boolean;
}

export default function ChatWindow({ messages, loading = false }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Empty state - Gemini style welcome
  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <h1 className="text-3xl font-semibold text-gray-900">
          お手伝いできることはありますか？
        </h1>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {messages.map((message) => (
          <div key={message.id}>
            {message.sender === 'user' ? (
              /* User message - right aligned bubble */
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-blue-50 text-gray-900 rounded-2xl px-5 py-3">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ) : (
              /* Bot message - left aligned, no bubble */
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-7 h-7 bg-white border border-gray-200 rounded-full flex items-center justify-center mt-0.5">
                  <Sparkles className="w-4 h-4 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-7 h-7 bg-white border border-gray-200 rounded-full flex items-center justify-center mt-0.5">
              <Sparkles className="w-4 h-4 text-blue-500" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-1 py-2">
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
