output "server_name" {
  value = azurerm_mssql_server.this.name
}

output "database_name" {
  value = azurerm_mssql_database.this.name
}

output "fully_qualified_domain_name" {
  value = azurerm_mssql_server.this.fully_qualified_domain_name
}