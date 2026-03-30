output "tenant_id" {
  description = "Azure AD tenant ID"
  value       = data.azuread_client_config.current.tenant_id
}

output "client_id" {
  description = "Application (client) ID"
  value       = azuread_application.app.client_id
}

output "client_secret" {
  description = "Client secret for backend"
  value       = azuread_application_password.backend.value
  sensitive   = true
}

output "users_group_id" {
  description = "Security group ID for app users"
  value       = azuread_group.users.object_id
}

output "admins_group_id" {
  description = "Security group ID for app admins"
  value       = azuread_group.admins.object_id
}
