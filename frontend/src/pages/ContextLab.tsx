import { useState } from 'react';
import { apiService } from '../services/api';
import type { ChunkResult, ContextPreviewResponse } from '../services/api';
import { Search, Eye, Play, Loader2 } from 'lucide-react';

export default function ContextLab() {
  // Parameters
  const [query, setQuery] = useState('');
  const [similarityK, setSimilarityK] = useState(3);
  const [threshold, setThreshold] = useState(0.0);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState<number | null>(null);

  // Results
  const [chunks, setChunks] = useState<ChunkResult[]>([]);
  const [contextPreview, setContextPreview] = useState<ContextPreviewResponse | null>(null);
  const [testResponse, setTestResponse] = useState('');

  // Loading states
  const [loadingRetrieval, setLoadingRetrieval] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);

  // Active view
  const [activeView, setActiveView] = useState<'retrieval' | 'context' | 'chat'>('retrieval');

  const runRetrieval = async () => {
    if (!query.trim()) return;
    setLoadingRetrieval(true);
    setActiveView('retrieval');
    try {
      const result = await apiService.testRetrieval({ query, similarity_k: similarityK, threshold });
      setChunks(result.chunks);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRetrieval(false);
    }
  };

  const runContextPreview = async () => {
    if (!query.trim()) return;
    setLoadingPreview(true);
    setActiveView('context');
    try {
      const result = await apiService.contextPreview({ query, similarity_k: similarityK, threshold });
      setContextPreview(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPreview(false);
    }
  };

  const runTestChat = async () => {
    if (!query.trim()) return;
    setLoadingChat(true);
    setTestResponse('');
    setActiveView('chat');
    try {
      await apiService.testChatStream(
        { query, similarity_k: similarityK, threshold, temperature, max_tokens: maxTokens || undefined },
        {
          onToken: (token) => setTestResponse(prev => prev + token),
          onDone: () => setLoadingChat(false),
          onError: () => setLoadingChat(false),
        }
      );
    } catch (e) {
      console.error(e);
      setLoadingChat(false);
    }
  };

  const scoreColor = (score: number) => {
    if (score < 0.3) return 'bg-green-500';
    if (score < 0.5) return 'bg-yellow-500';
    if (score < 0.7) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Left: Parameters */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">Context Lab</h2>
          <p className="text-xs text-gray-400 mt-0.5">RAGパラメータの実験・検証</p>
        </div>

        {/* Query */}
        <div className="p-4 border-b border-gray-100">
          <label className="text-xs font-medium text-gray-500 uppercase">クエリ</label>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="w-full mt-1.5 p-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
            rows={3}
            placeholder="検索クエリを入力..."
          />
        </div>

        {/* RAG Parameters */}
        <div className="p-4 border-b border-gray-100">
          <label className="text-xs font-medium text-gray-500 uppercase">検索パラメータ</label>

          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>similarity_k</span>
              <span className="font-mono font-medium">{similarityK}</span>
            </div>
            <input type="range" min="1" max="20" step="1" value={similarityK}
              onChange={e => setSimilarityK(parseInt(e.target.value))}
              className="w-full mt-1" />
          </div>

          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>threshold</span>
              <span className="font-mono font-medium">{threshold.toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="1" step="0.05" value={threshold}
              onChange={e => setThreshold(parseFloat(e.target.value))}
              className="w-full mt-1" />
            <p className="text-xs text-gray-400 mt-0.5">0 = フィルタなし</p>
          </div>
        </div>

        {/* LLM Parameters */}
        <div className="p-4 border-b border-gray-100">
          <label className="text-xs font-medium text-gray-500 uppercase">LLMパラメータ</label>

          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>temperature</span>
              <span className="font-mono font-medium">{temperature.toFixed(1)}</span>
            </div>
            <input type="range" min="0" max="2" step="0.1" value={temperature}
              onChange={e => setTemperature(parseFloat(e.target.value))}
              className="w-full mt-1" />
          </div>

          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>max_tokens</span>
            </div>
            <input type="number" min="1" max="128000"
              value={maxTokens || ''}
              onChange={e => setMaxTokens(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full mt-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="制限なし" />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-4 space-y-2">
          <button onClick={runRetrieval} disabled={loadingRetrieval || !query.trim()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors">
            {loadingRetrieval ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            検索プレビュー
          </button>
          <button onClick={runContextPreview} disabled={loadingPreview || !query.trim()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 transition-colors">
            {loadingPreview ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
            コンテキスト確認
          </button>
          <button onClick={runTestChat} disabled={loadingChat || !query.trim()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-green-500 rounded-lg hover:bg-green-600 disabled:bg-gray-300 transition-colors">
            {loadingChat ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            テスト実行
          </button>
        </div>
      </div>

      {/* Right: Results */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Tab bar */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-200 bg-white">
          {[
            { key: 'retrieval' as const, label: '検索結果', count: chunks.length },
            { key: 'context' as const, label: 'コンテキスト', count: contextPreview ? contextPreview.token_estimate : null },
            { key: 'chat' as const, label: 'テスト応答', count: null },
          ].map(tab => (
            <button key={tab.key} onClick={() => setActiveView(tab.key)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                activeView === tab.key ? 'bg-gray-100 text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-700'
              }`}>
              {tab.label}
              {tab.count !== null && tab.count > 0 && (
                <span className="ml-1.5 text-xs text-gray-400">
                  {tab.key === 'context' ? `~${tab.count}tok` : tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Results content */}
        <div className="flex-1 overflow-auto p-4">

          {/* Retrieval results */}
          {activeView === 'retrieval' && (
            chunks.length === 0 ? (
              <div className="text-center text-gray-400 mt-20">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">クエリを入力して「検索プレビュー」を実行</p>
              </div>
            ) : (
              <div className="space-y-3">
                {chunks.map((chunk, i) => (
                  <div key={i} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-100">
                      <span className="text-xs font-medium text-gray-500">#{i + 1}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${scoreColor(chunk.score)}`}
                            style={{ width: `${Math.max(5, (1 - chunk.score) * 100)}%` }} />
                        </div>
                        <span className="text-xs font-mono text-gray-500">score: {chunk.score}</span>
                      </div>
                    </div>
                    <div className="p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{chunk.content}</p>
                      {chunk.metadata?.source && (
                        <p className="mt-2 text-xs text-gray-400">source: {chunk.metadata.source}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {/* Context preview */}
          {activeView === 'context' && (
            !contextPreview ? (
              <div className="text-center text-gray-400 mt-20">
                <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">「コンテキスト確認」を実行するとLLMに渡す全文を表示</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-xs text-gray-400 mb-2">
                  推定トークン数: ~{contextPreview.token_estimate}
                </div>
                {contextPreview.messages.map((msg, i) => (
                  <div key={i} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <div className={`px-4 py-2 border-b border-gray-100 ${
                      msg.role === 'system' ? 'bg-purple-50' : 'bg-blue-50'
                    }`}>
                      <span className={`text-xs font-medium ${
                        msg.role === 'system' ? 'text-purple-600' : 'text-blue-600'
                      }`}>{msg.role}</span>
                    </div>
                    <pre className="p-4 text-sm text-gray-700 whitespace-pre-wrap font-mono overflow-x-auto">{msg.content}</pre>
                  </div>
                ))}
              </div>
            )
          )}

          {/* Test chat response */}
          {activeView === 'chat' && (
            !testResponse && !loadingChat ? (
              <div className="text-center text-gray-400 mt-20">
                <Play className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">「テスト実行」でパラメータを変えた応答を確認</p>
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
                  <span className="text-xs font-medium text-gray-500">応答</span>
                  <span className="text-xs text-gray-400">
                    temp={temperature} | k={similarityK} | threshold={threshold}
                  </span>
                  {loadingChat && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
                </div>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">{testResponse}</div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
