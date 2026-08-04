"""pytest ブートストラップ。

`backend/` をインポートパスに含め、テストが `from models... import` の形で
アプリのモジュールを読めるようにする（pytest.ini の pythonpath=. と対）。
最初のテストは LLM を呼ばない（モデル起動不要で走る）方針。
"""
import os
import sys

# backend/ ディレクトリを import パス先頭に追加
sys.path.insert(0, os.path.dirname(__file__))
