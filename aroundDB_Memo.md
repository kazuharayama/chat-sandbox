● このアプリケーションのDBアクセス関連の場所を調査しました。以下に主要な箇所をまとめます。

  主要なDBアクセス関連ファイル

  1. データベース接続管理

  - backend/agent/utils/db_connection.py - PostgreSQL接続プール管理（psycopg2使用）

  2. データ操作マネージャー

  - backend/core/tasks/task_manager.py - タスクCRUD操作（565行）
  - backend/core/equipments/equipments_manager.py - 機器・ビルディング・フロア管理（712行）
  - backend/core/surveys/survey_manager.py - アンケート管理

  3. グラフDB・ベクター検索

  - backend/agent/core/graph_manager.py - Apache AGE知識グラフ管理（406行）
  - backend/agent/core/cypher_chain_builder.py - Cypherクエリ生成・実行（163行）
  - backend/agent/core/pgvector_manager.py - ベクター埋め込み管理（154行）
  - backend/agent/core/similarity_chain_builder.py - 類似検索（108行）

  4. メモリ管理

  - backend/agent/core/memory_manager.py - LangMem + PostgresStore

  5. スキーマ定義・マイグレーション

  - prisma/schema.prisma - Prismaスキーマ定義（168行）
  - prisma/migrations/ - 7つのマイグレーションファイル

  6. APIエンドポイント

  - backend/routers/tasks.py - タスク関連API
  - backend/routers/equipments.py - 機器関連API

  データベース構成

  - メインDB: PostgreSQL with Apache AGE + pgvector拡張
  - 主要テーブル: tasks, task_surveys, buildings, floors, machines, processes, langchain_pg_*, store
  - 接続方式: psycopg2接続プール（最小1、最大5接続）
  - ORM: Prisma（マイグレーション管理用）

  クエリ実行パターン

  1. 生SQL: TaskManager、EquipmentManagerでpsycopg2直接実行
  2. Cypher: GraphManagerでApache AGEのグラフクエリ実行
  3. ベクター検索: PGVectorでk-nearest neighbor検索（k=4）

  詳細な調査結果を上記に返答として含めましたので、特定のファイルについてさらに詳しく知りたい場合はお知らせください。
