terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "azurerm" {
    # バックエンドの設定はterraform initコマンドで指定または
    # 環境ごとの設定ファイルで上書き
  }
}

provider "azurerm" {
  features {}
}

# 環境変数からの読み込み
variable "environment" {
  description = "デプロイ環境 (dev, prod)"
  type        = string
}

variable "location" {
  description = "Azureリージョン"
  type        = string
  default     = "japaneast"
}

variable "app_name" {
  description = "アプリケーション名"
  type        = string
  default     = "chat-sandbox"
}

variable "entra_client_id" {
  description = "コンテナアプリが使用するAzure Entra ID クライアントID (Key Vaultに格納)"
  type        = string
  sensitive   = true
}

variable "entra_tenant_id" {
  description = "コンテナアプリが使用するAzure Entra ID テナントID (Key Vaultに格納)"
  type        = string
  sensitive   = true
}

# 環境ごとのモジュール呼び出し
module "app_infrastructure" {
  source      = "./modules/app_infrastructure"
  environment = var.environment
  location    = var.location
  app_name    = var.app_name
  entra_client_id = var.entra_client_id
  entra_tenant_id = var.entra_tenant_id
}

# 出力値
output "app_url" {
  value = module.app_infrastructure.app_url
}
