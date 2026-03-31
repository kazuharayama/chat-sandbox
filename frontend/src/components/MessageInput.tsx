import { useState, useRef, useEffect } from 'react';
import { Plus, Send, X, FileText, Paperclip, Mic, MicOff, Loader2 } from 'lucide-react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { apiService } from '../services/api';

interface MessageInputProps {
  onSendMessage: (message: string, file?: File) => void;
  disabled?: boolean;
}

const ACCEPT_TYPES = '.txt,.pdf,.md,.csv,.png,.jpg,.jpeg,.gif,.bmp,.webp';

export default function MessageInput({
  onSendMessage,
  disabled = false,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showMenu, setShowMenu] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const { isRecording, startRecording, stopRecording } = useAudioRecorder();

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMenu]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((!message.trim() && !attachedFile) || disabled) return;

    onSendMessage(message.trim(), attachedFile || undefined);
    setMessage('');
    clearAttachment();
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleFileSelect = () => {
    setShowMenu(false);
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile(file);
    if (file.type.startsWith('image/')) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
    e.target.value = '';
  };

  const handleMicClick = async () => {
    if (isRecording) {
      const blob = await stopRecording();
      setIsTranscribing(true);
      try {
        const text = await apiService.speechToText(blob);
        if (text) {
          setMessage((prev) => (prev ? prev + ' ' + text : text));
        }
      } catch {
        // Silently fail - user can retry
      } finally {
        setIsTranscribing(false);
      }
    } else {
      try {
        await startRecording();
      } catch {
        // Mic permission denied
      }
    }
  };

  const clearAttachment = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setAttachedFile(null);
    setPreviewUrl(null);
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-6">
      {/* Attached file preview */}
      {attachedFile && (
        <div className="mb-2 flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl p-2.5 mx-1">
          {previewUrl ? (
            <img src={previewUrl} alt="preview" className="w-12 h-12 object-cover rounded-lg" />
          ) : (
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-500" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-700 truncate">{attachedFile.name}</p>
            <p className="text-xs text-gray-400">{(attachedFile.size / 1024).toFixed(1)} KB</p>
          </div>
          <button type="button" onClick={clearAttachment} className="p-1 hover:bg-gray-200 rounded-full">
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      )}

      <div className="relative" ref={menuRef}>
        {/* Popup Menu */}
        {showMenu && (
          <div className="absolute bottom-full left-0 mb-2 bg-white rounded-xl shadow-lg border border-gray-200 py-2 w-64 z-50">
            <button
              onClick={handleFileSelect}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <span className="text-gray-500"><Paperclip className="w-5 h-5" /></span>
              <span className="flex-1 text-left">写真とファイルを追加</span>
            </button>
          </div>
        )}

        {/* Input Bar */}
        <form onSubmit={handleSubmit} className="flex items-end gap-2 bg-gray-100 rounded-full px-2 py-1.5">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT_TYPES}
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Plus Button */}
          <button
            type="button"
            onClick={() => setShowMenu(!showMenu)}
            className="flex-shrink-0 w-10 h-10 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
            disabled={disabled}
          >
            <Plus className={`w-5 h-5 text-gray-500 transition-transform ${showMenu ? 'rotate-45' : ''}`} />
          </button>

          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="質問してみましょう"
            disabled={disabled}
            className="flex-1 bg-transparent px-2 py-2.5 resize-none focus:outline-none max-h-32 min-h-[40px] text-sm text-gray-900 placeholder-gray-400"
            rows={1}
          />

          {/* Mic Button */}
          <button
            type="button"
            onClick={handleMicClick}
            disabled={disabled || isTranscribing}
            className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600'
                : isTranscribing
                  ? 'bg-gray-200'
                  : 'hover:bg-gray-200'
            }`}
            title={isRecording ? '録音停止' : isTranscribing ? '変換中...' : '音声入力'}
          >
            {isTranscribing ? (
              <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
            ) : isRecording ? (
              <MicOff className="w-5 h-5 text-white" />
            ) : (
              <Mic className="w-5 h-5 text-gray-500" />
            )}
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={(!message.trim() && !attachedFile) || disabled}
            className="flex-shrink-0 w-10 h-10 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 rounded-full flex items-center justify-center transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </form>
      </div>
    </div>
  );
}
