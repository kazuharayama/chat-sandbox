interface ChatRequest {
  message: string;
  session_id?: string | null;
  language?: string;
  hasAttachment?: boolean;
  use_rag?: boolean;
}

interface ChatResponse {
  response: string;
  sources?: string[];
}

interface DocumentUploadRequest {
  file: File;
  document_type: string;
}

interface DocumentResponse {
  document_id: string;
  filename: string;
  status: string;
}

interface Document {
  document_id: string;
  filename: string;
  size: number;
  last_modified: number;
}

interface DocumentListResponse {
  documents: Document[];
}

interface StreamCallbacks {
  onToken: (token: string) => void;
  onSources: (sources: string[]) => void;
  onSession?: (sessionId: string) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'http://localhost:8000';
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: request.message,
        language: request.language || '日本語',
        hasAttachment: request.hasAttachment || false,
        use_rag: request.use_rag !== undefined ? request.use_rag : true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async sendMessageStream(request: ChatRequest, callbacks: StreamCallbacks): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: request.message,
        session_id: request.session_id || null,
        language: request.language || '日本語',
        hasAttachment: request.hasAttachment || false,
        use_rag: request.use_rag !== undefined ? request.use_rag : true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = JSON.parse(line.slice(6));

          if (data.type === 'token') {
            callbacks.onToken(data.content);
          } else if (data.type === 'sources') {
            callbacks.onSources(data.sources);
          } else if (data.type === 'session') {
            callbacks.onSession?.(data.session_id);
          } else if (data.type === 'done') {
            callbacks.onDone();
          }
        }
      }
    } catch (error) {
      callbacks.onError(error instanceof Error ? error : new Error('Stream error'));
    }
  }

  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('document_type', request.document_type);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async getDocuments(): Promise<DocumentListResponse> {
    const response = await fetch(`${this.baseUrl}/documents`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  // Admin - Models
  async listModels(): Promise<LLMModel[]> {
    const response = await fetch(`${this.baseUrl}/admin/models`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async createModel(data: LLMModelCreate): Promise<LLMModel> {
    const response = await fetch(`${this.baseUrl}/admin/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async updateModel(modelId: string, data: LLMModelUpdate): Promise<LLMModel> {
    const response = await fetch(`${this.baseUrl}/admin/models/${modelId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  // Admin - Agents
  async listAgents(): Promise<Agent[]> {
    const response = await fetch(`${this.baseUrl}/admin/agents`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async getAgentPrompts(agentId: string): Promise<Prompt[]> {
    const response = await fetch(`${this.baseUrl}/admin/agents/${agentId}/prompts`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async updatePrompt(agentId: string, promptKey: string, content: string, updatedBy?: string): Promise<Prompt> {
    const response = await fetch(`${this.baseUrl}/admin/prompts/${agentId}/${promptKey}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, updated_by: updatedBy || 'admin' }),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async getPromptVersions(agentId: string, promptKey: string): Promise<Prompt[]> {
    const response = await fetch(`${this.baseUrl}/admin/prompts/${agentId}/${promptKey}/versions`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async rollbackPrompt(agentId: string, promptKey: string, version: number): Promise<Prompt> {
    const response = await fetch(`${this.baseUrl}/admin/prompts/${agentId}/${promptKey}/rollback/${version}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  // Admin - Knowledge Sources
  async listKnowledgeSources(): Promise<KnowledgeSource[]> {
    const response = await fetch(`${this.baseUrl}/admin/knowledge-sources`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async updateKnowledgeSource(sourceId: string, data: KnowledgeSourceUpdate): Promise<KnowledgeSource> {
    const response = await fetch(`${this.baseUrl}/admin/knowledge-sources/${sourceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  // Admin - Cache
  async clearCache(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/admin/cache/clear`, { method: 'POST' });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  }

  // Sessions
  async createSession(): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/sessions`, { method: 'POST' });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async listSessions(): Promise<Session[]> {
    const response = await fetch(`${this.baseUrl}/sessions`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async getSessionMessages(sessionId: string): Promise<SessionMessage[]> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/messages`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  }
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface SessionMessage {
  id: string;
  session_id: string;
  role: 'user' | 'bot';
  content: string;
  sources: string[];
  created_at: string;
}

// Admin types
interface LLMModel {
  id: string;
  name: string;
  provider: string;
  deployment_name: string;
  temperature: number | null;
  max_tokens: number | null;
  is_default: boolean;
  config: Record<string, any>;
}

interface LLMModelCreate {
  name: string;
  provider: string;
  deployment_name: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
  config?: Record<string, any>;
}

interface LLMModelUpdate {
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
  config?: Record<string, any>;
}

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
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

interface KnowledgeSource {
  id: string;
  name: string;
  source_type: string;
  collection_name: string;
  config: Record<string, any>;
  is_enabled: boolean;
}

interface KnowledgeSourceUpdate {
  config?: Record<string, any>;
  is_enabled?: boolean;
}

export const apiService = new ApiService();
export type {
  ChatRequest,
  ChatResponse,
  DocumentUploadRequest,
  DocumentResponse,
  Document,
  DocumentListResponse,
  StreamCallbacks,
  Session,
  SessionMessage,
  LLMModel,
  LLMModelCreate,
  LLMModelUpdate,
  Agent,
  Prompt,
  KnowledgeSource,
  KnowledgeSourceUpdate,
};
