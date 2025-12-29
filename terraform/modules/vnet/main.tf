variable "resource_group_name" {
  description = "Resource group to deploy networking resources"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "vnet_name" {
  description = "Name of the virtual network"
  type        = string
}

variable "address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.10.0.0/16"]
}

variable "containerapp_subnet_name" {
  description = "Name of the subnet delegated to Azure Container Apps"
  type        = string
  default     = "containerapp"
}

variable "containerapp_subnet_prefix" {
  description = "Address prefix for the Container Apps subnet"
  type        = string
  default     = "10.10.0.0/23"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

resource "azurerm_virtual_network" "main" {
  name                = var.vnet_name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
  tags                = var.tags
}

resource "azurerm_subnet" "containerapp" {
  name                 = var.containerapp_subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.containerapp_subnet_prefix]

  delegation {
    name = "containerapp-delegation"

    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

output "vnet_id" {
  description = "ID of the virtual network"
  value       = azurerm_virtual_network.main.id
}

output "containerapp_subnet_id" {
  description = "ID of the delegated subnet for Container Apps"
  value       = azurerm_subnet.containerapp.id
}
