variable "project_name" {
  description = "Project name used for app registration and group names"
  type        = string
}

variable "redirect_uris" {
  description = "Web redirect URIs for auth callback"
  type        = list(string)
  default     = ["http://localhost:5174/auth/callback"]
}

variable "spa_redirect_uris" {
  description = "SPA redirect URIs (for MSAL browser)"
  type        = list(string)
  default     = ["http://localhost:5174/"]
}

variable "secret_expiry_hours" {
  description = "Client secret expiry in hours"
  type        = number
  default     = 8760 # 1 year
}
