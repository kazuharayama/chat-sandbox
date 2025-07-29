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

# 環境ごとのモジュール呼び出し
module "app_infrastructure" {
  source      = "./modules/app_infrastructure"
  environment = var.environment
  location    = var.location
  app_name    = var.app_name
}

# 出力値
output "app_url" {
  value = module.app_infrastructure.app_url
}
