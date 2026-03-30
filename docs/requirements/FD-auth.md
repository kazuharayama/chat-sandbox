# FD: 認証統合 (Entra ID)

| 項目 | 内容 |
|------|------|
| 優先度 | P1 |
| 複雑度 | S |
| 依存 | なし (独立) |

## 1. 目的

`core/auth.py` は既に実装済み (グレースフルスキップ付き)。Entra IDのアプリ登録を行い、フロントエンドにMSALを統合して、エンドツーエンドの認証フローを完成させる。

## 2. ユーザーストーリー

1. ユーザーとして、ブラウザでアプリにアクセスするとMicrosoftログイン画面にリダイレクトされる
2. ユーザーとして、chat-sandbox-usersグループのメンバーであればアプリを使用できる
3. ユーザーとして、グループに所属していない場合はアクセス拒否される
4. 管理者として、管理画面 (`/admin`) は追加のadminグループ所属が必要

## 3. 受入基準

1. 未認証でのAPI呼び出しが 401 を返すこと
2. グループ非所属ユーザーが 403 を返すこと
3. フロントエンドの全API呼び出しにBearerトークンが付与されること
4. トークン期限切れ時にMSALが自動更新すること
5. `/admin/*` エンドポイントにadminグループチェックが追加されること

## 4. 技術アプローチ

### 4.1 フロントエンド (メイン作業)

**新規依存関係**:
```
@azure/msal-browser
@azure/msal-react
```

**新規: `frontend/src/auth/msalConfig.ts`**
- MSAL設定 (clientId, authority, redirectUri)

**変更: `frontend/src/main.tsx`**
- MsalProviderでラップ

**変更: `frontend/src/services/api.ts`**
- 全メソッドにAuthorizationヘッダーを追加

**新規: 認証ガード**
- AuthenticatedTemplate / UnauthenticatedTemplate

### 4.2 バックエンド

`backend/core/auth.py` は既に完成。変更は最小限:
- `/admin/*` エンドポイントにadminグループチェックを追加
- 環境変数未設定時のグレースフルスキップは維持

### 4.3 インフラ

- Entra IDアプリ登録 (手順: `docs/entra-id-setup.md` に記載済み)
- `.env` に追加:
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_ID`
  - `AZURE_CLIENT_SECRET`
  - `AZURE_ALLOWED_GROUP_ID`

## 5. API変更

なし (既存エンドポイントの認証チェックが有効化されるだけ)

## 6. DB変更

なし

## 7. リスク・留意事項

- **ローカル開発体験**: 認証が有効だとローカル開発が面倒になる。環境変数未設定時はスキップする既存のグレースフルフォールバックを維持すること
- **トークンリフレッシュ**: MSALのサイレントリフレッシュが失敗した場合のUI/UXを検討
