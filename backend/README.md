# LangChain オーケストレーションアプリ

このプロジェクトは、LangChainを使用してAIモデルの呼び出しをオーケストレーションするアプリケーションです。

## セットアップ

1. 必要なパッケージをインストールします:
```bash
pip install -r requirements.txt
```

2. `.env`ファイルを作成し、必要なAPIキーを設定します:
```
OPENAI_API_KEY=your_openai_api_key
```

3. アプリケーションを起動します:
```bash
uvicorn app:app --reload
```

## 機能

- 複数のAIモデルを連携させたワークフロー
- APIエンドポイントを通じたアクセス
- シーケンシャルチェーンとツールの使用例
