variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group" {
  type = string
}

variable "tenant_id" {
  type = string
}

variable "sql_admin_password" {
  type      = string
  sensitive = true
}