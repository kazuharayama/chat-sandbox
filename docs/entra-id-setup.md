# Entra ID 認証セットアップ手順

chat-sandbox に Microsoft Entra ID (旧 Azure AD) のグループベース認証を導入する手順。

## 前提条件

- Azure CLI (`az`) がインストール済み・ログイン済み
- Entra ID のテナント管理者権限

## 1. セキュリティグループ作成

```bash
# グループ作成
az ad group create \
  --display-name "chat-sandbox-users" \
  --mail-nickname "chat-sandbox-users" \
  --description "chat-sandbox アプリのアクセス許可グループ"

# グループID を控える
az ad group show --group "chat-sandbox-users" --query id -o tsv
```

## 2. メンバー追加

```bash
# 自分を追加
MY_ID=$(az ad signed-in-user show --query id -o tsv)
az ad group member add --group "chat-sandbox-users" --member-id "$MY_ID"

# 他のユーザーを追加（メールアドレスで検索）
USER_ID=$(az ad user show --id "user@rist.co.jp" --query id -o tsv)
az ad group member add --group "chat-sandbox-users" --member-id "$USER_ID"

# メンバー一覧確認
az ad group member list --group "chat-sandbox-users" --query "[].{name:displayName, email:userPrincipalName}" -o table
```

## 3. アプリ登録

```bash
# アプリ登録を作成
az ad app create \
  --display-name "chat-sandbox" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "http://localhost:5174/auth/callback" \
  --enable-id-token-issuance true

# App ID を控える
APP_ID=$(az ad app list --display-name "chat-sandbox" --query "[0].appId" -o tsv)
echo "APP_ID: $APP_ID"

# サービスプリンシパル作成
az ad sp create --id "$APP_ID"

# クライアントシークレット生成（バックエンド用）
az ad app credential reset --id "$APP_ID" --display-name "backend-secret" --years 1
# → password を控える（AZURE_CLIENT_SECRET に設定）
```

## 4. トークンにグループ情報を含める

```bash
# アプリのマニフェストでグループクレームを有効化
az ad app update --id "$APP_ID" --set groupMembershipClaims=SecurityGroup

# オプション: API パーミッション追加（Microsoft Graph - GroupMember.Read.All）
az ad app permission add --id "$APP_ID" \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions 98830695-27a2-44f7-8c18-0c3ebc9698f6=Scope

# 管理者同意
az ad app permission admin-consent --id "$APP_ID"
```

## 5. 環境変数設定

`.env` に以下を追加:

```bash
# Entra ID
AZURE_TENANT_ID=adda649a-0bf8-4b0b-aeab-85168c215b41
AZURE_CLIENT_ID=<APP_ID>
AZURE_CLIENT_SECRET=<生成したシークレット>
AZURE_ALLOWED_GROUP_ID=<chat-sandbox-users のグループID>
```

`docker-compose.yml` の backend に環境変数を追加:

```yaml
environment:
  - AZURE_TENANT_ID=${AZURE_TENANT_ID:-}
  - AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-}
  - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET:-}
  - AZURE_ALLOWED_GROUP_ID=${AZURE_ALLOWED_GROUP_ID:-}
```

## 6. バックエンド実装

### 依存関係追加 (requirements.txt)

```
python-jose[cryptography]==3.3.0
msal==1.28.0
```

### 認証ミドルウェア (backend/core/auth.py)

トークン検証の流れ:
1. Authorization ヘッダーから Bearer トークン取得
2. Entra ID の JWKS でトークン署名を検証
3. トークンの `groups` クレームに許可グループIDが含まれるか確認
4. 含まれない場合は 403 Forbidden

### ルーターへの適用

```python
from core.auth import require_group_member

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    user = Depends(require_group_member),  # ← 追加
    chat_service: ChatService = Depends(get_chat_service),
):
    ...
```

## 7. フロントエンド実装

### 依存関係追加

```bash
npm install @azure/msal-browser @azure/msal-react
```

### MSAL設定 (frontend/src/auth/msalConfig.ts)

```typescript
export const msalConfig = {
  auth: {
    clientId: "<APP_ID>",
    authority: "https://login.microsoftonline.com/<TENANT_ID>",
    redirectUri: "http://localhost:5174/auth/callback",
  },
};
```

### App.tsx を MsalProvider でラップ

```tsx
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";

const msalInstance = new PublicClientApplication(msalConfig);

<MsalProvider instance={msalInstance}>
  <App />
</MsalProvider>
```

### APIリクエストにトークン付与

```typescript
const token = await msalInstance.acquireTokenSilent({ scopes: ["api://<APP_ID>/access"] });
fetch(url, {
  headers: { Authorization: `Bearer ${token.accessToken}` },
});
```

## 8. 動作確認

```bash
# バックエンド再起動
docker compose up -d --build backend

# 認証なしでアクセス → 401
curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" \
  -d '{"message":"test"}' | jq .

# ブラウザでログイン → グループメンバーならアクセス可能
# http://localhost:5174
```

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| トークンに groups が含まれない | マニフェストの groupMembershipClaims 確認 |
| 403 Forbidden | ユーザーがグループに追加されているか確認 |
| CORS エラー | リダイレクトURIがアプリ登録と一致しているか確認 |
| トークン期限切れ | MSAL の acquireTokenSilent が自動更新する |
