# FC: 音声対話 (STT/TTS ファイルベース)

| 項目 | 内容 |
|------|------|
| 優先度 | P2 |
| 複雑度 | M |
| 依存 | なし (独立) |
| 状態 | **完了** (Whisper + Piper) |

> **更新 (2026-06-17)**: 当初は WebRTC + aiortc + Azure Speech SDK を想定していたが、
> 実装は **ブラウザ録音 → HTTP アップロード → Whisper(STT) / Piper(TTS)** のファイルベース構成で完了した。
> 本文は実装に合わせて改訂済み。WebRTC/aiortc/Azure Speech/`voice_sessions` 等は採用していない。

## 1. 目的

ブラウザのマイクで録音した音声をテキスト化 (STT) してチャット入力に渡し、AIの回答テキストを音声合成 (TTS) して再生する。Azure等の外部サービスに依存せず、ローカル (Whisper + Piper) で完結させる。

## 2. ユーザーストーリー

1. ユーザーとして、チャット画面のマイクボタンを押して話すと、内容がテキスト化されて入力欄に入る
2. ユーザーとして、テキスト化された内容をそのまま送信して通常のRAGチャットができる
3. ユーザーとして、AIの回答を音声で再生して聞ける
4. 開発者として、STT/TTS が外部API無しでローカル動作する (オフライン/コスト無し)

## 3. 受入基準

1. ブラウザのマイクで録音した音声 (WebM/MP4) をバックエンドにアップロードできること
2. Whisper (faster-whisper) でテキストに変換され、`{text}` が返ること
3. 変換テキストが既存のチャット入力 (MessageInput) に反映され、通常の `/chat` フローに渡せること
4. 任意のテキストを Piper で WAV に合成し、ブラウザで再生できること
5. STT/TTS が Ollama/Claude と同様にローカルで完結し、Azure等の外部キーを要さないこと

## 4. 技術アプローチ (実装済み)

### 4.1 依存関係

```
faster-whisper>=1.1.0   # STT (requirements.txt)
piper                   # TTS (CLIバイナリ。コンテナにインストール、subprocessで起動)
```

ピアモデルは `/app/models/piper/ja_JP-amitaro-medium.onnx`(+`.json`) を使用。

### 4.2 バックエンド

**`backend/services/speech_service.py`** (`SpeechService`)
- `transcribe(audio_bytes) -> str`: faster-whisper `WhisperModel` で音声→テキスト。`vad_filter=True`、一時 `.webm` ファイル経由。モデルは遅延ロード (初回のみ)
- `synthesize(text) -> bytes`: `piper --model ... --config ... --output-raw` を subprocess 実行し、RAW PCM を WAV (22050Hz / mono / 16bit) に変換して返す

**`backend/routers/speech.py`**
- `POST /speech-to-text` — `multipart/form-data` の音声ファイル → `{"text": ...}`
- `POST /text-to-speech` — `{"text": ...}` → `audio/wav` バイナリ
- いずれも `asyncio.to_thread` でブロッキング処理をオフロード

### 4.3 フロントエンド

- **`frontend/src/hooks/useAudioRecorder.ts`** — MediaRecorder でマイク録音 (WebM/MP4)、Blob を取得
- **`frontend/src/hooks/useAudioPlayer.ts`** — TTS で返った WAV Blob を再生
- **`frontend/src/pages/Chat.tsx`** — マイクボタンUI。録音 → `speechToText` → 入力欄反映、回答 → `textToSpeech` → 再生
- **`frontend/src/services/api.ts`** — `speechToText(audioBlob)` / `textToSpeech(text)`

### 4.4 設定 (`backend/core/config.py`)

```python
whisper_model_size: str = "base"      # tiny/base/small/medium/large
whisper_language: str = "ja"
whisper_device: str = "cpu"           # GPU環境では "cuda"
whisper_compute_type: str = "int8"
piper_model_path: str = "/app/models/piper/ja_JP-amitaro-medium.onnx"
piper_config_path: str = "/app/models/piper/ja_JP-amitaro-medium.onnx.json"
```

## 5. API変更

| メソッド | パス | リクエスト | レスポンス |
|---------|------|----------|----------|
| POST | `/speech-to-text` | `multipart/form-data` (`audio`: 音声ファイル) | `{ "text": string }` |
| POST | `/text-to-speech` | `{ "text": string }` | `audio/wav` バイナリ |

## 6. DB変更

なし (ステートレス。セッション/イベントテーブルは持たない)。

## 7. リスク・留意事項

- **モデルサイズ vs 精度/速度**: `whisper_model_size` で調整。CPU環境は `base`/`int8` 既定。GPU環境は `whisper_device="cuda"` で高速化可能
- **Piper バイナリ依存**: コンテナに `piper` 実行ファイルと日本語モデルの同梱が必要 (パスは config 参照)
- **録音フォーマット**: ブラウザにより WebM/MP4 が異なる。Whisper 側は一時ファイル経由で吸収
- **TTS は同期 subprocess**: `timeout=30s`。長文は分割を検討
- **将来**: リアルタイム性が必要になれば WebRTC/ストリーミングを別途検討 (現状はターン制で十分)
