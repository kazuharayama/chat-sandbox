variable "environment" {
  description = "デプロイ環境 (dev, prod)"
  type        = string
}

variable "location" {
  description = "Azureリージョン"
  type        = string
}

variable "app_name" {
  description = "アプリケーション名"
  type        = string
}

locals {
  resource_name_prefix = "${var.app_name}-${var.environment}"
  tags = {
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "Terraform"
  }
}

# リソースグループ
resource "azurerm_resource_group" "main" {
  name     = "${local.resource_name_prefix}-rg"
  location = var.location
  tags     = local.tags
}

# Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = replace("${local.resource_name_prefix}acr", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = true
  tags                = local.tags
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.resource_name_prefix}-law"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "${local.resource_name_prefix}-env"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.tags
}

# Managed Identity for Container Apps
resource "azurerm_user_assigned_identity" "app_identity" {
  name                = "${local.resource_name_prefix}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "${local.resource_name_prefix}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  template {
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.acr.login_server}/${var.app_name}-backend:latest"
      cpu    = 0.5
      memory = "1Gi"
      
      env {
        name  = "ENVIRONMENT"
        value = "azure"
      }
      
      env {
        name  = "AZURE_ENTRA_ID_CLIENT_ID"
        value = "#{AZURE_ENTRA_ID_CLIENT_ID}#"  # Azure Key Vaultから取得または環境変数から設定
      }
      
      env {
        name  = "AZURE_ENTRA_ID_TENANT_ID"
        value = "#{AZURE_ENTRA_ID_TENANT_ID}#"  # Azure Key Vaultから取得または環境変数から設定
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "${local.resource_name_prefix}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  template {
    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.acr.login_server}/${var.app_name}-frontend:latest"
      cpu    = 0.5
      memory = "1Gi"
      
      env {
        name  = "NODE_ENV"
        value = "production"
      }
      
      env {
        name  = "VITE_API_URL"
        value = "/api"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

# Nginx Container App
resource "azurerm_container_app" "nginx" {
  name                         = "${local.resource_name_prefix}-nginx"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  template {
    container {
      name   = "nginx"
      image  = "${azurerm_container_registry.acr.login_server}/${var.app_name}-nginx:latest"
      cpu    = 0.5
      memory = "1Gi"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"
    
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

output "app_url" {
  value = "https://${azurerm_container_app.nginx.latest_revision_fqdn}"
}
