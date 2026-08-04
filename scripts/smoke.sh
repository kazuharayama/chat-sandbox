#!/bin/bash
# smoke.sh — 変更が壊れていないかを 1コマンドで OK / NG を返して確認する道具。
#
# 前提: アプリを起動済みであること。
#   ./scripts/start.sh --cpu
# チャット疎通の工程だけ Ollama の実呼び出しが必要（モデル gemma2:2b が pull 済みであること）。
#
# 終了コード: 全ステップ成功=0、いずれか失敗=1
#
# 確認済みの事実（実コードで確認、2026-08-04）:
#   - ヘルス : GET  http://localhost:8000/       -> backend/main.py:39-41
#   - チャット: POST http://localhost:8000/chat   -> backend/models/chat.py ChatRequest/ChatResponse
#   - ポート 8000 は docker-compose.yml:25 で確認
set -u

BACKEND="http://localhost:8000"
FAIL=0

hr()   { echo "----------------------------------------"; }
check(){ echo ""; echo "[CHECK] $1"; }

# --- Step 1: backend ヘルスチェック（LLM 不要） ---
check "backend health  (GET ${BACKEND}/)"
BODY=$(curl -fsS -m 5 "${BACKEND}/" 2>/dev/null)
if [ $? -eq 0 ] && printf '%s' "$BODY" | grep -q "LangChain RAG"; then
    echo "  -> OK: ${BODY}"
else
    echo "  -> NG: backend が応答しない。'./scripts/start.sh --cpu' で起動したか確認すること"
    hr; echo "RESULT: NG (backend unreachable)"; exit 1
fi

# --- Step 2: チャット疎通（唯一の LLM 実呼び出し工程 / use_rag=false でベクトル検索は経由しない） ---
check "chat roundtrip  (POST ${BACKEND}/chat, use_rag=false)  ※LLM を1回呼ぶ"
RESP=$(curl -fsS -m 180 -X POST "${BACKEND}/chat" \
    -H 'Content-Type: application/json' \
    -d '{"message":"ping","use_rag":false}' 2>/dev/null)
if [ $? -eq 0 ] && printf '%s' "$RESP" | grep -q '"response"'; then
    echo "  -> OK: $(printf '%s' "$RESP" | head -c 200)"
else
    echo "  -> NG: chat が失敗。Ollama とモデルを確認: docker compose exec ollama-cpu ollama list"
    FAIL=1
fi

hr
if [ "$FAIL" -eq 0 ]; then
    echo "RESULT: OK"
    exit 0
else
    echo "RESULT: NG"
    exit 1
fi
