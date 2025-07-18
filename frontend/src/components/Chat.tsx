import { useState, useRef, useEffect } from 'react';
import ChatRichTextarea from './ChatRichTextarea';
import '../App.css';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isEditing?: boolean;
  attachments?: {
    type: 'image';
    url: string;
  }[];
}

export default function Chat() {
  // チャット履歴を保存する配列
  const [messages, setMessages] = useState<Message[]>([]);
  // 現在入力中のメッセージテキスト
  const [currentMessage, setCurrentMessage] = useState('');
  // 言語設定（日本語/英語）
  const [language, setLanguage] = useState('日本語');
  // API通信中のローディング状態
  const [loading, setLoading] = useState(false);
  // エラーメッセージ
  const [error, setError] = useState('');
  // 音声録音中かどうかのフラグ
  const [isRecording, setIsRecording] = useState(false);
  
  // 画像アップロード用のinput要素への参照
  const fileInputRef = useRef<HTMLInputElement>(null);
  // 画像プレビュー用のURL
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  // 音声録音用のMediaRecorderオブジェクトへの参照
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  // 録音中の音声データチャンクを保存する配列
  const audioChunksRef = useRef<Blob[]>([]);
  // メッセージリストの最下部要素への参照（自動スクロール用）
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  /**
   * メッセージの一意識別子を生成する関数
   * タイムスタンプと乱数を組み合わせてユニークなIDを生成
   */
  const generateId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  };

  /**
   * メッセージ送信処理を行う関数
   * 1. ユーザーメッセージを作成して表示
   * 2. 画像が添付されていれば処理
   * 3. APIにメッセージを送信してレスポンスを取得
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // メッセージが空で、画像もない場合は何もしない
    if (!currentMessage.trim() && !fileInputRef.current?.files?.length) return;
    
    const newMessageId = generateId();
    const attachments = [];
    
    // 画像添付があれば処理
    if (fileInputRef.current?.files?.length) {
      const file = fileInputRef.current.files[0];
      // ブラウザ上で表示するためのURLを生成
      const imageUrl = URL.createObjectURL(file);
      attachments.push({
        type: 'image' as const,
        url: imageUrl
      });
    }
    
    // ユーザーメッセージオブジェクトを作成
    const userMessage: Message = {
      id: newMessageId,
      content: currentMessage,
      sender: 'user',
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined
    };
    
    // メッセージリストに追加してUIを更新
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setLoading(true);
    setError('');
    
    // ファイル入力とプレビューをリセット
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setImagePreview(null);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: currentMessage, 
          language,
          hasAttachment: attachments.length > 0
        }),
      });

      if (!response.ok) {
        throw new Error(`エラー: ${response.status}`);
      }

      const data = await response.json();
      
      // Add bot response
      const botMessage: Message = {
        id: generateId(),
        content: data.response || 'No response received',
        sender: 'bot',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知のエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 音声録音機能の管理
   * ユーザーのマイクから音声を録音し、音声認識をシミュレートする
   */

  /**
   * 音声録音を開始する関数
   * 1. マイクへのアクセス権限を取得
   * 2. MediaRecorderを初期化して録音開始
   * 3. 録音状態を管理
   */
  const startRecording = async () => {
    try {
      // マイクからの音声ストリームを取得
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // 音声データが利用可能になったときのイベントハンドラ
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      // 録音停止時の処理
      mediaRecorder.onstop = async () => {
        // 録音された音声データをBlobに変換
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        // 実際の実装ではここで音声認識APIに送信する
        try {
          // デバッグ用に音声URLを生成
          const audioUrl = URL.createObjectURL(audioBlob);
          console.log('Audio recording available at:', audioUrl);
          
          // 実際の実装では、ここでaudioBlobをバックエンドに送信する
          // 現時点では音声認識をシミュレートする
          
          // 音声処理の遅延をシミュレート
          setTimeout(() => {
            // メモリリークを避けるためにURLを解放
            URL.revokeObjectURL(audioUrl);
            
            // シミュレートされた音声認識結果をメッセージ入力欄に挿入
            const simulatedText = '音声入力のテキスト例です';
            setCurrentMessage(prev => prev + simulatedText);
          }, 1000);
        } catch (error) {
          console.error('Error processing audio:', error);
          setError('音声処理中にエラーが発生しました');
        }
      };

      // 録音開始
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('録音を開始できませんでした');
    }
  };

  /**
   * 音声録音を停止する関数
   * 1. MediaRecorderの録音を停止
   * 2. 音声トラックを停止してリソースを解放
   */
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // すべての音声トラックを停止してリソースを解放
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  /**
   * 画像アップロード機能
   */

  /**
   * 画像アップロードボタンクリック時の処理
   * 非表示のファイル入力要素をクリックしてファイル選択ダイアログを開く
   */
  const handleImageUploadClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * メッセージ編集機能
   */

  /**
   * メッセージの編集モードを開始する関数
   * 指定されたIDのメッセージのisEditingフラグをtrueに設定
   */
  const startEditingMessage = (id: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === id ? { ...msg, isEditing: true } : msg
      )
    );
  };

  /**
   * 編集したメッセージを保存する関数
   * 指定されたIDのメッセージの内容を更新し、編集モードを終了する
   */
  const saveEditedMessage = (id: string, newContent: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === id ? { ...msg, content: newContent, isEditing: false } : msg
      )
    );
  };

  /**
   * メッセージの編集をキャンセルする関数
   * 内容を更新せずに編集モードを終了する
   */
  const cancelEditingMessage = (id: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === id ? { ...msg, isEditing: false } : msg
      )
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h1 className="text-lg font-bold">チャットインターフェース</h1>
      </div>

      {/* <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          className="block w-32 px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400"
        >
          <option value="日本語">日本語</option>
          <option value="英語">英語</option>
        </select>
      </div> */}

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[70%] rounded-lg p-3 ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'}`}>
              {message.isEditing ? (
                <div className="flex flex-col space-y-2">
                  <textarea
                    defaultValue={message.content}
                    className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        saveEditedMessage(message.id, e.currentTarget.value);
                      }
                      if (e.key === 'Escape') {
                        cancelEditingMessage(message.id);
                      }
                    }}
                  />
                  <div className="flex space-x-2 justify-end">
                    <button 
                      className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded"
                      onClick={(e) => saveEditedMessage(message.id, (e.currentTarget.parentElement?.previousSibling as HTMLTextAreaElement).value)}
                    >
                      保存
                    </button>
                    <button 
                      className="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded"
                      onClick={() => cancelEditingMessage(message.id)}
                    >
                      キャンセル
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="whitespace-pre-wrap break-words">{message.content}</div>
                  
                  {message.attachments?.map((attachment, index) => (
                    <div key={index} className="mt-2">
                      {attachment.type === 'image' && (
                        <img src={attachment.url} alt="Uploaded content" className="rounded max-w-full h-auto" />
                      )}
                    </div>
                  ))}
                  
                  <div className="flex justify-between items-center mt-2 text-xs">
                    <span className="text-gray-500 dark:text-gray-400">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.sender === 'user' && (
                      <button 
                        className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400" 
                        onClick={() => startEditingMessage(message.id)}
                        title="編集"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                          <path d="M21.731 2.269a2.625 2.625 0 00-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 000-3.712zM19.513 8.199l-3.712-3.712-12.15 12.15a5.25 5.25 0 00-1.32 2.214l-.8 2.685a.75.75 0 00.933.933l2.685-.8a5.25 5.25 0 002.214-1.32L19.513 8.2z" />
                        </svg>
                      </button>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="p-3 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-md mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
        <div className="flex flex-col space-y-3">
          {/* 画像プレビュー表示 */}
          {imagePreview && (
            <div className="flex items-center space-x-2">
              <div className="relative">
                <img 
                  src={imagePreview} 
                  alt="プレビュー" 
                  className="h-16 w-16 object-cover rounded-md border border-gray-300 dark:border-gray-600" 
                />
                <button
                  type="button"
                  className="absolute -top-3 -right-3 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 shadow-sm"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setImagePreview(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                >
                  ×
                </button>
              </div>
            </div>
          )}
          
          {/* 入力エリア */}
          <div className="flex space-x-2">
            <div className="flex-1">
              <ChatRichTextarea 
                value={currentMessage}
                placeholder="メッセージを入力..."
                disabled={loading}
                onSend={(text) => {
                  setCurrentMessage(text);
                  handleSubmit(new Event('submit') as any);
                }}
                onAttach={handleImageUploadClick}
                footerSlot={
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        const previewUrl = URL.createObjectURL(file);
                        setImagePreview(previewUrl);
                      }
                    }}
                  />
                }
              />
            </div>
            
            <button 
              type="button" 
              className={`flex items-center justify-center p-2 rounded-full h-12 w-12 ${isRecording ? 'bg-red-500 text-white' : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200'}`}
              onClick={isRecording ? stopRecording : startRecording}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
                <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-7.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
              </svg>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
