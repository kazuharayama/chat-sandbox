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
