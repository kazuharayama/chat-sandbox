import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { LLMModel, Agent, Prompt, KnowledgeSource } from '../services/api';
import { Settings, Save, RotateCcw, ChevronDown, ChevronRight, Bot, Brain, Database, Star, Plus, Trash2, RefreshCw } from 'lucide-react';

export default function Admin() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [editingPrompt, setEditingPrompt] = useState<{ key: string; content: string } | null>(null);
  const [versions, setVersions] = useState<Prompt[]>([]);
  const [showVersions, setShowVersions] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Model editing
  const [editingModel, setEditingModel] = useState<string | null>(null);
  const [modelForm, setModelForm] = useState<{ temperature: number; max_tokens: number | null }>({ temperature: 0.7, max_tokens: null });

  // New model form
  const [showNewModel, setShowNewModel] = useState(false);
  const [newModelForm, setNewModelForm] = useState({ name: '', provider: 'ollama', deployment_name: '', temperature: 0.7, base_url: '' });

  // Knowledge source editing
  const [editingSource, setEditingSource] = useState<string | null>(null);
  const [sourceForm, setSourceForm] = useState<{ similarity_k: number }>({ similarity_k: 3 });

  // Active tab
  const [activeTab, setActiveTab] = useState<'prompts' | 'models' | 'sources'>('prompts');

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    const [a, m, s] = await Promise.all([
      apiService.listAgents(),
      apiService.listModels(),
      apiService.listKnowledgeSources(),
    ]);
    setAgents(a);
    setModels(m);
    setSources(s);
    if (a.length > 0 && !selectedAgent) selectAgent(a[0]);
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const selectAgent = async (agent: Agent) => {
    setSelectedAgent(agent);
    setEditingPrompt(null);
    setShowVersions(null);
    const p = await apiService.getAgentPrompts(agent.id);
    setPrompts(p);
  };

  const startEdit = (prompt: Prompt) => {
    setEditingPrompt({ key: prompt.prompt_key, content: prompt.content });
  };

  const savePrompt = async () => {
    if (!editingPrompt || !selectedAgent) return;
    setSaving(true);
    try {
      await apiService.updatePrompt(selectedAgent.id, editingPrompt.key, editingPrompt.content);
      showMessage('success', 'プロンプトを更新しました');
      setEditingPrompt(null);
      const p = await apiService.getAgentPrompts(selectedAgent.id);
      setPrompts(p);
    } catch {
      showMessage('error', '保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const loadVersions = async (promptKey: string) => {
    if (!selectedAgent) return;
    if (showVersions === promptKey) { setShowVersions(null); return; }
    const v = await apiService.getPromptVersions(selectedAgent.id, promptKey);
    setVersions(v);
    setShowVersions(promptKey);
  };

  const rollback = async (promptKey: string, version: number) => {
    if (!selectedAgent) return;
    await apiService.rollbackPrompt(selectedAgent.id, promptKey, version);
    showMessage('success', `v${version} にロールバックしました`);
    const p = await apiService.getAgentPrompts(selectedAgent.id);
    setPrompts(p);
    setShowVersions(null);
  };

  // Model actions
  const startEditModel = (model: LLMModel) => {
    setEditingModel(model.id);
    setModelForm({ temperature: model.temperature || 0.7, max_tokens: model.max_tokens });
  };

  const saveModel = async (modelId: string) => {
    try {
      await apiService.updateModel(modelId, {
        temperature: modelForm.temperature,
        max_tokens: modelForm.max_tokens || undefined,
      });
      showMessage('success', 'モデルを更新しました');
      setEditingModel(null);
      setModels(await apiService.listModels());
    } catch {
      showMessage('error', 'モデル更新に失敗しました');
    }
  };

  const setDefaultModel = async (modelId: string) => {
    try {
      await apiService.updateModel(modelId, { is_default: true });
      showMessage('success', 'デフォルトモデルを変更しました');
      setModels(await apiService.listModels());
    } catch {
      showMessage('error', 'デフォルト変更に失敗しました');
    }
  };

  const addModel = async () => {
    try {
      const config: Record<string, string> = {};
      if (newModelForm.provider === 'ollama') {
        config.base_url = newModelForm.base_url || 'http://ollama:11434';
      } else if (newModelForm.provider === 'openai_compatible') {
        config.base_url = newModelForm.base_url || 'http://vllm:8000/v1';
      }
      await apiService.createModel({
        name: newModelForm.name,
        provider: newModelForm.provider,
        deployment_name: newModelForm.deployment_name,
        temperature: newModelForm.temperature,
        config,
      });
      showMessage('success', 'モデルを追加しました');
      setShowNewModel(false);
      setNewModelForm({ name: '', provider: 'ollama', deployment_name: '', temperature: 0.7, base_url: '' });
      setModels(await apiService.listModels());
    } catch {
      showMessage('error', 'モデル追加に失敗しました');
    }
  };

  // Knowledge source actions
  const startEditSource = (src: KnowledgeSource) => {
    setEditingSource(src.id);
    setSourceForm({ similarity_k: src.config?.similarity_k || 3 });
  };

  const saveSource = async (sourceId: string) => {
    try {
      await apiService.updateKnowledgeSource(sourceId, { config: { similarity_k: sourceForm.similarity_k } });
      showMessage('success', 'ナレッジソースを更新しました');
      setEditingSource(null);
      setSources(await apiService.listKnowledgeSources());
    } catch {
      showMessage('error', '更新に失敗しました');
    }
  };

  const clearCache = async () => {
    await apiService.clearCache();
    showMessage('success', 'キャッシュをクリアしました');
  };

  const providerLabel = (provider: string) => {
    switch (provider) {
      case 'ollama': return 'Ollama';
      case 'openai_compatible': return 'OpenAI互換';
      default: return provider;
    }
  };

  const providerColor = (provider: string) => {
    switch (provider) {
      case 'ollama': return 'bg-purple-100 text-purple-700';
      case 'openai_compatible': return 'bg-emerald-100 text-emerald-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-500" />
            <h1 className="text-base font-semibold text-gray-900">管理画面</h1>
          </div>
        </div>

        {/* Agents */}
        <div className="p-3">
          <h3 className="text-xs font-medium text-gray-400 uppercase mb-2 px-2">エージェント</h3>
          {agents.map(agent => (
            <button
              key={agent.id}
              onClick={() => selectAgent(agent)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5 ${
                selectedAgent?.id === agent.id ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span className="truncate">{agent.display_name}</span>
            </button>
          ))}
        </div>

        {/* Tab buttons */}
        <div className="p-3 border-t border-gray-100">
          <h3 className="text-xs font-medium text-gray-400 uppercase mb-2 px-2">表示</h3>
          {[
            { key: 'prompts' as const, label: 'プロンプト', icon: Bot },
            { key: 'models' as const, label: 'LLMモデル', icon: Brain },
            { key: 'sources' as const, label: '知識ソース', icon: Database },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5 ${
                activeTab === tab.key ? 'bg-gray-100 text-gray-900 font-medium' : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Cache clear */}
        <div className="mt-auto p-3 border-t border-gray-100">
          <button onClick={clearCache} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50 transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span>キャッシュクリア</span>
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {activeTab === 'prompts' ? (selectedAgent?.display_name || 'エージェントを選択') :
                 activeTab === 'models' ? 'LLMモデル管理' : '知識ソース管理'}
              </h2>
              <p className="text-sm text-gray-500">
                {activeTab === 'prompts' ? selectedAgent?.description :
                 activeTab === 'models' ? 'プロバイダーの切り替え・パラメータ調整' : 'ベクトル検索の設定'}
              </p>
            </div>
            {message && (
              <div className={`text-sm px-3 py-1 rounded-lg ${
                message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                {message.text}
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-4xl">

            {/* Prompts Tab */}
            {activeTab === 'prompts' && (
              prompts.length === 0 ? (
                <p className="text-gray-400 text-center mt-20">エージェントを選択してください</p>
              ) : (
                <div className="space-y-4">
                  {prompts.map(prompt => (
                    <div key={prompt.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-700">{prompt.prompt_key}</span>
                          <span className="text-xs text-gray-400">v{prompt.version}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button onClick={() => loadVersions(prompt.prompt_key)} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors">
                            {showVersions === prompt.prompt_key ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            履歴
                          </button>
                          {editingPrompt?.key === prompt.prompt_key ? (
                            <button onClick={savePrompt} disabled={saving} className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300 transition-colors">
                              <Save className="w-3 h-3" />{saving ? '保存中...' : '保存'}
                            </button>
                          ) : (
                            <button onClick={() => startEdit(prompt)} className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded transition-colors">
                              編集
                            </button>
                          )}
                        </div>
                      </div>
                      {editingPrompt?.key === prompt.prompt_key ? (
                        <textarea
                          value={editingPrompt.content}
                          onChange={(e) => setEditingPrompt({ ...editingPrompt, content: e.target.value })}
                          className="w-full p-4 text-sm font-mono text-gray-800 focus:outline-none resize-none min-h-[200px]"
                          rows={10}
                        />
                      ) : (
                        <pre className="p-4 text-sm font-mono text-gray-700 whitespace-pre-wrap">{prompt.content}</pre>
                      )}
                      {showVersions === prompt.prompt_key && versions.length > 0 && (
                        <div className="border-t border-gray-200 bg-gray-50 px-4 py-2">
                          <div className="text-xs font-medium text-gray-500 mb-1">バージョン履歴</div>
                          {versions.map(v => (
                            <div key={v.id} className="flex items-center justify-between py-1.5 text-xs">
                              <div className="flex items-center gap-2">
                                <span className={`font-medium ${v.is_active ? 'text-green-600' : 'text-gray-500'}`}>
                                  v{v.version} {v.is_active && '(active)'}
                                </span>
                                <span className="text-gray-400">{new Date(v.created_at).toLocaleString('ja-JP')}</span>
                                {v.updated_by && <span className="text-gray-400">by {v.updated_by}</span>}
                              </div>
                              {!v.is_active && (
                                <button onClick={() => rollback(prompt.prompt_key, v.version)} className="flex items-center gap-1 text-blue-500 hover:text-blue-700">
                                  <RotateCcw className="w-3 h-3" />戻す
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}

            {/* Models Tab */}
            {activeTab === 'models' && (
              <div className="space-y-4">
                {models.map(model => (
                  <div key={model.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Brain className="w-5 h-5 text-gray-400" />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">{model.name}</span>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${providerColor(model.provider)}`}>
                              {providerLabel(model.provider)}
                            </span>
                            {model.is_default && (
                              <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded flex items-center gap-1">
                                <Star className="w-3 h-3" />default
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-gray-400">{model.deployment_name}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {!model.is_default && (
                          <button onClick={() => setDefaultModel(model.id)} className="text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded px-2 py-1 transition-colors">
                            デフォルトに設定
                          </button>
                        )}
                        {editingModel === model.id ? (
                          <button onClick={() => saveModel(model.id)} className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
                            <Save className="w-3 h-3" />保存
                          </button>
                        ) : (
                          <button onClick={() => startEditModel(model)} className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded transition-colors">
                            編集
                          </button>
                        )}
                      </div>
                    </div>
                    {editingModel === model.id && (
                      <div className="flex items-center gap-6 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-500">temperature</label>
                          <input
                            type="range" min="0" max="2" step="0.1"
                            value={modelForm.temperature}
                            onChange={e => setModelForm({ ...modelForm, temperature: parseFloat(e.target.value) })}
                            className="w-32"
                          />
                          <span className="text-xs text-gray-700 w-8">{modelForm.temperature}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-500">max_tokens</label>
                          <input
                            type="number" min="1" max="128000"
                            value={modelForm.max_tokens || ''}
                            onChange={e => setModelForm({ ...modelForm, max_tokens: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-24 text-xs border border-gray-300 rounded px-2 py-1"
                            placeholder="制限なし"
                          />
                        </div>
                      </div>
                    )}
                    {!editingModel && (
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span>temperature: {model.temperature ?? 0.7}</span>
                        <span>max_tokens: {model.max_tokens ?? '制限なし'}</span>
                      </div>
                    )}
                  </div>
                ))}

                {/* Add new model */}
                {showNewModel ? (
                  <div className="bg-white border-2 border-dashed border-blue-300 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">新しいモデルを追加</h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-gray-500">名前</label>
                        <input
                          type="text" value={newModelForm.name}
                          onChange={e => setNewModelForm({ ...newModelForm, name: e.target.value })}
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 mt-1"
                          placeholder="llama3.1:8b / gemma2:9b"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">プロバイダー</label>
                        <select
                          value={newModelForm.provider}
                          onChange={e => setNewModelForm({ ...newModelForm, provider: e.target.value })}
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 mt-1"
                        >
                          <option value="ollama">Ollama</option>
                          <option value="openai_compatible">OpenAI互換 (vLLM/llama.cpp/LM Studio等)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">モデル名 / デプロイメント名</label>
                        <input
                          type="text" value={newModelForm.deployment_name}
                          onChange={e => setNewModelForm({ ...newModelForm, deployment_name: e.target.value })}
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 mt-1"
                          placeholder="llama3.1:8b / gemma2:9b"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Base URL (ローカルLLM)</label>
                        <input
                          type="text" value={newModelForm.base_url}
                          onChange={e => setNewModelForm({ ...newModelForm, base_url: e.target.value })}
                          className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 mt-1"
                          placeholder={newModelForm.provider === 'ollama' ? 'http://ollama:11434' : 'http://vllm:8000/v1'}
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <button onClick={addModel} className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">追加</button>
                      <button onClick={() => setShowNewModel(false)} className="px-3 py-1.5 text-xs text-gray-500 border border-gray-300 rounded hover:bg-gray-50 transition-colors">キャンセル</button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowNewModel(true)}
                    className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
                  >
                    <Plus className="w-4 h-4" />モデルを追加
                  </button>
                )}
              </div>
            )}

            {/* Sources Tab */}
            {activeTab === 'sources' && (
              <div className="space-y-4">
                {sources.map(src => (
                  <div key={src.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Database className="w-5 h-5 text-gray-400" />
                        <div>
                          <span className="text-sm font-medium text-gray-900">{src.name}</span>
                          <span className="text-xs text-gray-400 ml-2">collection: {src.collection_name}</span>
                        </div>
                      </div>
                      {editingSource === src.id ? (
                        <button onClick={() => saveSource(src.id)} className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
                          <Save className="w-3 h-3" />保存
                        </button>
                      ) : (
                        <button onClick={() => startEditSource(src)} className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded transition-colors">
                          編集
                        </button>
                      )}
                    </div>
                    {editingSource === src.id ? (
                      <div className="flex items-center gap-4 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-500">similarity_k</label>
                          <input
                            type="range" min="1" max="20" step="1"
                            value={sourceForm.similarity_k}
                            onChange={e => setSourceForm({ similarity_k: parseInt(e.target.value) })}
                            className="w-32"
                          />
                          <span className="text-xs text-gray-700 w-6">{sourceForm.similarity_k}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">
                        similarity_k: {src.config?.similarity_k ?? 'N/A'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
