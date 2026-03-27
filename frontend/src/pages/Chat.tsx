import { useState } from 'react';
import { apiService } from '../services/api';
import ChatWindow from '../components/ChatWindow';
import MessageInput from '../components/MessageInput';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  fileName?: string;
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = async (content: string, file?: File) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: file
        ? `${content || 'ファイルをアップロードしました'}\n📎 ${file.name}`
        : content,
      sender: 'user',
      timestamp: new Date(),
      fileName: file?.name,
    };

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

      const response = await apiService.sendMessage({
        message: content || `${file?.name} の内容を教えてください`,
        language: '日本語',
        hasAttachment: !!file,
        use_rag: true,
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleStartRecording = () => {
    console.log('音声録音機能（未実装）');
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Error banner */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-100">
          <p className="text-sm text-red-600 text-center">{error}</p>
        </div>
      )}

      {/* Messages */}
      <ChatWindow messages={messages} loading={loading} />

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        onStartRecording={handleStartRecording}
        disabled={loading}
      />
    </div>
  );
}
