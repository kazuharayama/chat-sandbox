import { useEffect, useRef } from 'react';
import { Sparkles, FileText } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sources?: string[];
  fileName?: string;
}

interface ChatWindowProps {
  messages: Message[];
  loading?: boolean;
}

function SourceBadges({ sources }: { sources: string[] }) {
  if (!sources || sources.length === 0) return null;
  // Deduplicate and extract filename
  const unique = [...new Set(sources)].map((s) => {
    const parts = s.split('/');
    return parts[parts.length - 1];
  });

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {unique.map((name, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs"
        >
          <FileText className="w-3 h-3" />
          {name}
        </span>
      ))}
    </div>
  );
}

export default function ChatWindow({ messages, loading = false }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

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
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-blue-50 text-gray-900 rounded-2xl px-5 py-3">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ) : (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-7 h-7 bg-white border border-gray-200 rounded-full flex items-center justify-center mt-0.5">
                  <Sparkles className="w-4 h-4 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap">
                    {message.content}
                    {/* Blinking cursor while streaming */}
                    {loading && message.id === messages[messages.length - 1]?.id && message.content && (
                      <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5 align-text-bottom" />
                    )}
                  </p>
                  <SourceBadges sources={message.sources || []} />
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && messages[messages.length - 1]?.sender !== 'bot' && (
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
