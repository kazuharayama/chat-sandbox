import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Settings, Save, RotateCcw, ChevronDown, ChevronRight, Bot, Brain, Database } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  agent_type: string;
  is_enabled: boolean;
}

interface Prompt {
  id: string;
  agent_id: string;
  prompt_key: string;
  content: string;
  version: number;
  is_active: boolean;
  updated_by: string | null;
  created_at: string;
}

interface LLMModel {
  id: string;
  name: string;
  deployment_name: string;
  temperature: number | null;
  max_tokens: number | null;
  is_default: boolean;
}

interface KnowledgeSource {
  id: string;
  name: string;
  source_type: string;
  collection_name: string;
  config: Record<string, any>;
  is_enabled: boolean;
}

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

  const baseUrl = 'http://localhost:8000';

  useEffect(() => {
    Promise.all([
      fetch(`${baseUrl}/admin/agents`).then(r => r.json()),
      fetch(`${baseUrl}/admin/models`).then(r => r.json()),
      fetch(`${baseUrl}/admin/knowledge-sources`).then(r => r.json()),
    ]).then(([a, m, s]) => {
      setAgents(a);
      setModels(m);
      setSources(s);
      if (a.length > 0) selectAgent(a[0]);
    });
  }, []);

  const selectAgent = async (agent: Agent) => {
    setSelectedAgent(agent);
    setEditingPrompt(null);
    setShowVersions(null);
    const res = await fetch(`${baseUrl}/admin/agents/${agent.id}/prompts`);
    setPrompts(await res.json());
  };

  const startEdit = (prompt: Prompt) => {
    setEditingPrompt({ key: prompt.prompt_key, content: prompt.content });
  };

  const savePrompt = async () => {
    if (!editingPrompt || !selectedAgent) return;
    setSaving(true);
    try {
      const res = await fetch(`${baseUrl}/admin/prompts/${selectedAgent.id}/${editingPrompt.key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editingPrompt.content, updated_by: 'admin' }),
      });
      if (!res.ok) throw new Error('保存に失敗');
      setMessage({ type: 'success', text: 'プロンプトを更新しました' });
      setEditingPrompt(null);
      // Refresh prompts
      const p = await fetch(`${baseUrl}/admin/agents/${selectedAgent.id}/prompts`);
      setPrompts(await p.json());
    } catch {
      setMessage({ type: 'error', text: '保存に失敗しました' });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const loadVersions = async (promptKey: string) => {
    if (!selectedAgent) return;
    if (showVersions === promptKey) {
      setShowVersions(null);
      return;
    }
    const res = await fetch(`${baseUrl}/admin/prompts/${selectedAgent.id}/${promptKey}/versions`);
    setVersions(await res.json());
    setShowVersions(promptKey);
  };

  const rollback = async (promptKey: string, version: number) => {
    if (!selectedAgent) return;
    const res = await fetch(`${baseUrl}/admin/prompts/${selectedAgent.id}/${promptKey}/rollback/${version}`, {
      method: 'POST',
    });
    if (res.ok) {
      setMessage({ type: 'success', text: `v${version} にロールバックしました` });
      const p = await fetch(`${baseUrl}/admin/agents/${selectedAgent.id}/prompts`);
      setPrompts(await p.json());
      setShowVersions(null);
    }
    setTimeout(() => setMessage(null), 3000);
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

        {/* Models */}
        <div className="p-3 border-t border-gray-100">
          <h3 className="text-xs font-medium text-gray-400 uppercase mb-2 px-2">LLMモデル</h3>
          {models.map(model => (
            <div key={model.id} className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600">
              <Brain className="w-4 h-4 text-gray-400" />
              <span>{model.name}</span>
              {model.is_default && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">default</span>}
            </div>
          ))}
        </div>

        {/* Knowledge Sources */}
        <div className="p-3 border-t border-gray-100">
          <h3 className="text-xs font-medium text-gray-400 uppercase mb-2 px-2">知識ソース</h3>
          {sources.map(src => (
            <div key={src.id} className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600">
              <Database className="w-4 h-4 text-gray-400" />
              <span className="truncate">{src.name}</span>
              <span className="text-xs text-gray-400">k={src.config?.similarity_k}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {selectedAgent?.display_name || 'エージェントを選択'}
              </h2>
              <p className="text-sm text-gray-500">{selectedAgent?.description}</p>
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

        {/* Prompts */}
        <div className="flex-1 overflow-auto p-6">
          {prompts.length === 0 ? (
            <p className="text-gray-400 text-center mt-20">エージェントを選択してください</p>
          ) : (
            <div className="space-y-4 max-w-4xl">
              {prompts.map(prompt => (
                <div key={prompt.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  {/* Prompt header */}
                  <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">{prompt.prompt_key}</span>
                      <span className="text-xs text-gray-400">v{prompt.version}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => loadVersions(prompt.prompt_key)}
                        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        {showVersions === prompt.prompt_key ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        履歴
                      </button>
                      {editingPrompt?.key === prompt.prompt_key ? (
                        <button
                          onClick={savePrompt}
                          disabled={saving}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300 transition-colors"
                        >
                          <Save className="w-3 h-3" />
                          {saving ? '保存中...' : '保存'}
                        </button>
                      ) : (
                        <button
                          onClick={() => startEdit(prompt)}
                          className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded transition-colors"
                        >
                          編集
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Prompt content */}
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

                  {/* Version history */}
                  {showVersions === prompt.prompt_key && versions.length > 0 && (
                    <div className="border-t border-gray-200 bg-gray-50 px-4 py-2">
                      <div className="text-xs font-medium text-gray-500 mb-1">バージョン履歴</div>
                      {versions.map(v => (
                        <div key={v.id} className="flex items-center justify-between py-1.5 text-xs">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${v.is_active ? 'text-green-600' : 'text-gray-500'}`}>
                              v{v.version} {v.is_active && '(active)'}
                            </span>
                            <span className="text-gray-400">
                              {new Date(v.created_at).toLocaleString('ja-JP')}
                            </span>
                            {v.updated_by && <span className="text-gray-400">by {v.updated_by}</span>}
                          </div>
                          {!v.is_active && (
                            <button
                              onClick={() => rollback(prompt.prompt_key, v.version)}
                              className="flex items-center gap-1 text-blue-500 hover:text-blue-700"
                            >
                              <RotateCcw className="w-3 h-3" />
                              戻す
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
