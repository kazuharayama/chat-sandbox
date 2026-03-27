variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rg-chat-sandbox"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "japaneast"
}

variable "project_name" {
  description = "Project name used as prefix for resources"
  type        = string
  default     = "chat-sandbox"
}

variable "storage_account_name" {
  description = "Storage account name (globally unique, 3-24 chars, lowercase alphanumeric)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    project     = "chat-sandbox"
    environment = "dev"
  }
}
