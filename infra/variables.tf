variable "location" {
  default = "Central US"
}

variable "resource_group_name" {
  default = "rg-data-engineer-test"
}

variable "storage_account_name" {
  default = "stdataengtest123"
}


variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
}

variable "sql_admin_password" {
  sensitive = true
}