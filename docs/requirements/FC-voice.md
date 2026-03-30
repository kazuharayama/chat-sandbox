# FC: WebRTC Voice対話

| 項目 | 内容 |
|------|------|
| 優先度 | P2 |
| 複雑度 | XL |
| 依存 | なし (独立) |

## 1. 目的

ブラウザのマイクから音声を入力し、STT → RAGチャット → TTS → 音声出力の全パイプラインをWebRTCで実現する。全ステップをログ・Langfuseでトレースできるようにする。

## 2. ユーザーストーリー

1. ユーザーとして、チャット画面のマイクボタンを押して話すと、AIが音声で回答してくれる
2. ユーザーとして、音声入力のテキスト化結果がチャット履歴に表示される
3. ユーザーとして、AIの回答テキストもチャット履歴に表示される (音声と同時にテキストも見える)
4. 開発者として、Langfuseで WebRTCセッション → STT → LLM → TTS の end-to-endトレースを確認できる
5. 開発者として、WebRTC接続の状態遷移 (ICE/offer/answer/connection state) をログで追跡できる

## 3. 受入基準

1. ブラウザでWebRTCを使ってマイク音声をバックエンドに送信できること
2. STT (Azure Speech or Whisper) でテキスト変換されること
3. 変換テキストが既存のRAGパイプライン (ChatService) に渡されること
4. TTSで生成された音声がWebRTCでブラウザに返されること
5. 一連のフロー全体がLangfuseに1つのtraceとして記録されること
6. WebRTC接続のICE/offer/answer/connection stateが `voice_events` テーブルに記録されること
7. ネットワーク切断時にグレースフルにフォールバック (テキスト入力に戻る) すること

## 4. 技術アプローチ

### 4.1 新規依存関係

```
aiortc>=1.9.0                          # Python WebRTC
azure-cognitiveservices-speech>=1.37.0  # Azure Speech SDK (STT + TTS)
```

### 4.2 バックエンド

**新規: `backend/services/voice_service.py`**
- WebRTCシグナリング (offer/answer/ICE candidate exchange)
- AudioTrackの受信 → PCMバッファ → STT
- STT結果 → `ChatService.chat()` 呼び出し
- LLM応答テキスト → TTS → AudioTrack送信
- Langfuse span: `voice_session` → `stt` → `llm` → `tts`

**新規: `backend/routers/voice.py`**
- `POST /voice/offer` — WebRTC SDP offer受信、answer返却
- `POST /voice/ice-candidate` — ICE candidate交換
- `GET /voice/sessions/{id}/events` — イベントログ取得

**新規: `backend/repositories/voice_repository.py`**
- `voice_sessions` テーブルのCRUD
- `voice_events` テーブルへのイベント記録

### 4.3 フロントエンド

**新規: `frontend/src/hooks/useWebRTC.ts`**
- RTCPeerConnection管理
- マイクのMediaStream取得
- AudioTrackの送受信
- 接続状態の管理 + エラーハンドリング

**新規: `frontend/src/components/VoiceButton.tsx`**
- マイクボタンUI (録音中アニメーション)
- `useWebRTC` hookの呼び出し
- ChatWindowへの統合

### 4.4 設定追加

**`backend/core/config.py`**:
```python
azure_speech_key: str = ""
azure_speech_region: str = ""
```

### 4.5 ログ設計

#### voice_eventsに記録するイベント

| event_type | event_data | タイミング |
|-----------|-----------|----------|
| `offer_received` | `{sdp_type}` | SDP offer受信時 |
| `answer_sent` | `{sdp_type}` | SDP answer送信時 |
| `ice_candidate` | `{candidate, sdpMid}` | ICE candidate交換時 |
| `connection_state` | `{state}` | connecting/connected/disconnected/failed |
| `stt_start` | `{}` | 音声認識開始 |
| `stt_result` | `{text, confidence, duration_ms}` | 音声認識完了 |
| `llm_start` | `{query}` | LLM呼び出し開始 |
| `llm_end` | `{response_length, duration_ms}` | LLM応答完了 |
| `tts_start` | `{text_length}` | TTS開始 |
| `tts_end` | `{audio_duration_ms}` | TTS完了 |
| `session_closed` | `{reason}` | セッション終了 |
| `error` | `{error_type, message}` | エラー発生 |

#### Langfuseトレース構造

```
voice_session (trace)
├── webrtc_setup (span) — offer/answer/ICE
├── stt (span) — 音声→テキスト
│   └── audio_duration, confidence
├── llm (span) — RAGチャット (既存のLangfuseトレースと統合)
│   ├── retrieve (span)
│   └── generate (span)
└── tts (span) — テキスト→音声
    └── audio_duration
```

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/voice/offer` | `{sdp, type, session_id?}` | `{sdp, type, voice_session_id}` |
| POST | `/voice/ice-candidate` | `{candidate, sdpMid, sdpMLineIndex, voice_session_id}` | `{status: "ok"}` |
| GET | `/voice/sessions/{id}/events` | query: `?event_type=stt_result` | `[{event_type, event_data, created_at}]` |

## 6. DB変更

### voice_sessions

```sql
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_session_id UUID REFERENCES chat_sessions(id),
    webrtc_connection_id VARCHAR(200),
    status VARCHAR(50),  -- connecting, active, closed, error
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);
```

### voice_events

```sql
CREATE TABLE voice_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voice_session_id UUID REFERENCES voice_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_voice_events_session ON voice_events(voice_session_id, created_at);
CREATE INDEX idx_voice_events_type ON voice_events(event_type);
```

## 7. リスク・留意事項

- **NAT/ファイアウォール**: ローカル環境以外ではTURNサーバー (coturn) が必要。docker-composeに追加を検討
- **aiortcのPython互換性**: Python 3.11との互換性を事前検証。問題があればWebSocket + AudioWorkletを代替案として検討
- **音声品質**: WebRTCのコーデック (Opus) とSTTの入力要件 (16kHz PCM等) の変換が必要
- **同時接続**: aiortcのメモリ使用量に注意。同時WebRTCセッション数を制限することを検討
- **フォールバック**: WebRTC接続に失敗した場合、既存のテキストチャットにシームレスに戻れること
