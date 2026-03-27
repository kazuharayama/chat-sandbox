import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { Document, DocumentUploadRequest } from '../services/api';
import { FileText, Upload, Trash2, RefreshCw, File as FileIcon, LayoutGrid, List } from 'lucide-react';

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<string>('text');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // ドキュメント一覧を取得
  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getDocuments();
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ドキュメント一覧の取得中にエラーが発生しました');
      console.error('Documents fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 初回レンダリング時にドキュメント一覧を取得
  useEffect(() => {
    fetchDocuments();
  }, []);

  // ファイル選択ハンドラ
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // ドキュメントタイプ選択ハンドラ
  const handleDocumentTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDocumentType(e.target.value);
  };

  // ドキュメントアップロードハンドラ
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('ファイルが選択されていません');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const request: DocumentUploadRequest = {
        file: selectedFile,
        document_type: documentType,
      };

      await apiService.uploadDocument(request);
      setSelectedFile(null);
      // アップロード後にドキュメント一覧を更新
      await fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ドキュメントのアップロード中にエラーが発生しました');
      console.error('Document upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  // ファイルサイズのフォーマット
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    else return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  // 日付のフォーマット
  const formatDate = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString('ja-JP');
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-semibold text-gray-900">ドキュメント管理</h1>
          </div>
        </div>

        {/* Upload Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">ドキュメントのアップロード</h3>
          
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-500 mb-1">ドキュメントタイプ</label>
            <select
              value={documentType}
              onChange={handleDocumentTypeChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm"
            >
              <option value="text">テキスト (.txt)</option>
              <option value="pdf">PDF (.pdf)</option>
              <option value="markdown">Markdown (.md)</option>
              <option value="csv">CSV (.csv)</option>
              <option value="image">画像 (.png, .jpg, .gif)</option>
            </select>
          </div>
          
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-500 mb-1">ファイル</label>
            <input
              type="file"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-medium
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
            />
            {selectedFile && (
              <p className="mt-1 text-xs text-gray-500">
                選択されたファイル: {selectedFile.name}
              </p>
            )}
          </div>
          
          <button
            onClick={handleUpload}
            disabled={uploading || !selectedFile}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                アップロード中...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                アップロード
              </>
            )}
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 p-4">
          <nav className="space-y-1">
            <a href="/" className="flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-600 hover:bg-gray-50">
              チャット画面に戻る
            </a>
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Content Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">ドキュメント一覧</h2>
              <p className="text-sm text-gray-500">
                アップロードされたドキュメントの一覧
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex bg-gray-100 rounded-lg p-0.5">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-400 hover:text-gray-600'}`}
                  title="グリッド表示"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-400 hover:text-gray-600'}`}
                  title="リスト表示"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={fetchDocuments}
                disabled={loading}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                更新
              </button>
            </div>
          </div>
          {error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 px-3 py-1 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
              <span className="ml-2 text-gray-600">読み込み中...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <FileText className="w-12 h-12 mb-2 text-gray-300" />
              <p>ドキュメントがありません</p>
            </div>
          ) : (
            viewMode === 'grid' ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {documents.map((doc) => (
                  <div
                    key={doc.document_id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        <FileIcon className="w-8 h-8 text-blue-500 mr-3" />
                        <div>
                          <h3 className="font-medium text-gray-900 truncate max-w-xs" title={doc.filename}>
                            {doc.filename}
                          </h3>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(doc.size)} • {formatDate(doc.last_modified)}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={async () => {
                          if (!confirm(`${doc.filename} を削除しますか？`)) return;
                          try {
                            await apiService.deleteDocument(doc.document_id);
                            await fetchDocuments();
                          } catch (err) {
                            setError('削除中にエラーが発生しました');
                          }
                        }}
                        className="text-gray-400 hover:text-red-500 transition-colors"
                        title="削除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
                {documents.map((doc) => (
                  <div
                    key={doc.document_id}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                  >
                    <FileIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                    <span className="flex-1 text-sm font-medium text-gray-900 truncate" title={doc.filename}>
                      {doc.filename}
                    </span>
                    <span className="text-xs text-gray-400 w-20 text-right flex-shrink-0">
                      {formatFileSize(doc.size)}
                    </span>
                    <span className="text-xs text-gray-400 w-36 text-right flex-shrink-0">
                      {formatDate(doc.last_modified)}
                    </span>
                    <button
                      onClick={async () => {
                        if (!confirm(`${doc.filename} を削除しますか？`)) return;
                        try {
                          await apiService.deleteDocument(doc.document_id);
                          await fetchDocuments();
                        } catch (err) {
                          setError('削除中にエラーが発生しました');
                        }
                      }}
                      className="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
                      title="削除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
