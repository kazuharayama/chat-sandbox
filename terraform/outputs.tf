output "storage_connection_string" {
  description = "Storage account connection string (set as AZURE_STORAGE_CONNECTION_STRING)"
  value       = module.storage.primary_connection_string
  sensitive   = true
}

output "storage_account_name" {
  description = "Storage account name"
  value       = module.storage.storage_account_name
}

output "storage_container_name" {
  description = "Blob container name"
  value       = module.storage.container_name
}

output "storage_blob_endpoint" {
  description = "Blob endpoint URL"
  value       = module.storage.primary_blob_endpoint
}

# --- Entra ID ---

output "entra_tenant_id" {
  description = "Azure AD tenant ID (set as AZURE_TENANT_ID)"
  value       = module.entra_id.tenant_id
}

output "entra_client_id" {
  description = "Application client ID (set as AZURE_CLIENT_ID)"
  value       = module.entra_id.client_id
}

output "entra_client_secret" {
  description = "Client secret (set as AZURE_CLIENT_SECRET)"
  value       = module.entra_id.client_secret
  sensitive   = true
}

output "entra_users_group_id" {
  description = "Users group ID (set as AZURE_ALLOWED_GROUP_ID)"
  value       = module.entra_id.users_group_id
}

output "entra_admins_group_id" {
  description = "Admins group ID"
  value       = module.entra_id.admins_group_id
}
