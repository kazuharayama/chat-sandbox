data "azuread_client_config" "current" {}

# --- セキュリティグループ ---

resource "azuread_group" "users" {
  display_name     = "${var.project_name}-users"
  description      = "${var.project_name} アプリのアクセス許可グループ"
  security_enabled = true
  mail_enabled     = false
}

resource "azuread_group" "admins" {
  display_name     = "${var.project_name}-admins"
  description      = "${var.project_name} 管理画面のアクセス許可グループ"
  security_enabled = true
  mail_enabled     = false
}

# 実行ユーザーをadminsグループに追加
resource "azuread_group_member" "current_user_admin" {
  group_object_id  = azuread_group.admins.object_id
  member_object_id = data.azuread_client_config.current.object_id
}

# 実行ユーザーをusersグループにも追加
resource "azuread_group_member" "current_user_users" {
  group_object_id  = azuread_group.users.object_id
  member_object_id = data.azuread_client_config.current.object_id
}

# --- アプリ登録 ---

resource "azuread_application" "app" {
  display_name = var.project_name

  sign_in_audience = "AzureADMyOrg"

  group_membership_claims = ["SecurityGroup"]

  web {
    redirect_uris = var.redirect_uris

    implicit_grant {
      id_token_issuance_enabled     = true
      access_token_issuance_enabled = false
    }
  }

  single_page_application {
    redirect_uris = var.spa_redirect_uris
  }

  api {
    requested_access_token_version = 2
  }

  optional_claims {
    id_token {
      name = "groups"
    }
    access_token {
      name = "groups"
    }
  }
}

# --- サービスプリンシパル ---

resource "azuread_service_principal" "app" {
  client_id = azuread_application.app.client_id
}

# --- クライアントシークレット (バックエンド用) ---

resource "azuread_application_password" "backend" {
  application_id = azuread_application.app.id
  display_name   = "backend-secret"
  end_date       = timeadd(timestamp(), "${var.secret_expiry_hours}h")

  lifecycle {
    ignore_changes = [end_date]
  }
}
