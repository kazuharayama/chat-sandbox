"""最初のテスト: LLM を呼ばない。

`models/chat.py` の ChatRequest の既定値が仕様どおりかを検証する。
Pydantic だけに依存し、モデル起動・DB・外部サービスを一切使わない。
本数を増やすのが目的ではなく、pytest が赤/緑を返せる状態を作るのが目的。
"""
from models.chat import ChatRequest


def test_chat_request_defaults():
    req = ChatRequest(message="ping")
    # 実コード backend/models/chat.py の既定値
    assert req.use_rag is True
    assert req.language == "日本語"
    assert req.session_id is None
    assert req.hasAttachment is False
