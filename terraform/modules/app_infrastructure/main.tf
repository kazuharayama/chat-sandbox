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

variable "entra_client_id" {
  description = "Azure Entra ID クライアントID"
  type        = string
  sensitive   = true
}

variable "entra_tenant_id" {
  description = "Azure Entra ID テナントID"
  type        = string
  sensitive   = true
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

module "network" {
  source = "../vnet"

  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  vnet_name                = "${local.resource_name_prefix}-vnet"
  containerapp_subnet_name = "containerapp"
  containerapp_subnet_prefix = "10.10.0.0/23"
  tags                     = local.tags
}

# Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = replace("${local.resource_name_prefix}acr", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = false
  tags                = local.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "app_identity_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.app_identity.principal_id
}

resource "azurerm_key_vault" "main" {
  name                            = replace("${local.resource_name_prefix}-kv", "-", "")
  location                        = azurerm_resource_group.main.location
  resource_group_name             = azurerm_resource_group.main.name
  tenant_id                       = data.azurerm_client_config.current.tenant_id
  sku_name                        = "standard"
  purge_protection_enabled        = true
  soft_delete_retention_days      = 90
  enabled_for_deployment          = false
  enabled_for_disk_encryption     = false
  enabled_for_template_deployment = false
  public_network_access_enabled   = true
  tags                            = local.tags
}

resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

resource "azurerm_key_vault_access_policy" "app_identity" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.app_identity.principal_id

  secret_permissions = ["Get", "List"]
}

resource "azurerm_key_vault_secret" "entra_client_id" {
  name         = "entra-client-id"
  value        = var.entra_client_id
  key_vault_id = azurerm_key_vault.main.id
  content_type = "Azure Entra ID client id"
}

resource "azurerm_key_vault_secret" "entra_tenant_id" {
  name         = "entra-tenant-id"
  value        = var.entra_tenant_id
  key_vault_id = azurerm_key_vault.main.id
  content_type = "Azure Entra ID tenant id"
}

resource "azurerm_key_vault_secret" "app_insights_connection_string" {
  name         = "app-insights-connection-string"
  value        = azurerm_application_insights.main.connection_string
  key_vault_id = azurerm_key_vault.main.id
  content_type = "Application Insights connection string"
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

resource "azurerm_application_insights" "main" {
  name                = "${local.resource_name_prefix}-appi"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.tags
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "${local.resource_name_prefix}-env"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  infrastructure_subnet_id   = module.network.containerapp_subnet_id
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

      secret {
        name                 = "entra-client-id"
        key_vault_secret_id  = azurerm_key_vault_secret.entra_client_id.id
      }

      secret {
        name                 = "entra-tenant-id"
        key_vault_secret_id  = azurerm_key_vault_secret.entra_tenant_id.id
      }

      env {
        name  = "ENVIRONMENT"
        value = "azure"
      }

      env {
        name  = "AZURE_ENTRA_ID_CLIENT_ID"
        secret_name = "entra-client-id"
      }

      env {
        name  = "AZURE_ENTRA_ID_TENANT_ID"
        secret_name = "entra-tenant-id"
      }

      secret {
        name                = "app-insights-connection-string"
        key_vault_secret_id = azurerm_key_vault_secret.app_insights_connection_string.id
      }

      env {
        name        = "APPINSIGHTS_CONNECTION_STRING"
        secret_name = "app-insights-connection-string"
      }

      env {
        name  = "APPLICATIONINSIGHTS_ROLE_NAME"
        value = "${local.resource_name_prefix}-backend"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport                 = "auto"
    allow_insecure_connections = false
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
    transport                 = "auto"
    allow_insecure_connections = false
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
    transport                 = "auto"
    allow_insecure_connections = false

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

resource "azurerm_monitor_diagnostic_setting" "acr" {
  name                       = "${local.resource_name_prefix}-acr-diag"
  target_resource_id         = azurerm_container_registry.acr.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  log {
    category = "ContainerRegistryLoginEvents"
    enabled  = true
  }

  log {
    category = "ContainerRegistryRepositoryEvents"
    enabled  = true
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  name                       = "${local.resource_name_prefix}-kv-diag"
  target_resource_id         = azurerm_key_vault.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  log {
    category = "AuditEvent"
    enabled  = true
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

resource "azurerm_monitor_diagnostic_setting" "backend_container_app" {
  name                       = "${local.resource_name_prefix}-backend-diag"
  target_resource_id         = azurerm_container_app.backend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  log {
    category = "ContainerAppConsoleLogs"
    enabled  = true
  }

  log {
    category = "ContainerAppSystemLogs"
    enabled  = true
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

output "app_url" {
  value = "https://${azurerm_container_app.nginx.latest_revision_fqdn}"
}
