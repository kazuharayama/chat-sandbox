terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "azuread" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# VNet
module "vnet" {
  source = "./modules/vnet"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  vnet_name           = "${var.project_name}-vnet"
  tags                = var.tags
}

# Entra ID (認証)
module "entra_id" {
  source = "./modules/entra_id"

  project_name      = var.project_name
  redirect_uris     = ["http://localhost:5174/auth/callback"]
  spa_redirect_uris = ["http://localhost:5174/"]
}

# Storage (ドキュメントアップロード用)
module "storage" {
  source = "./modules/storage"

  resource_group_name  = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  storage_account_name = var.storage_account_name
  container_name       = "documents"
  tags                 = var.tags
}
