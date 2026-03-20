resource "azurerm_storage_account" "this" {
  name                     = var.name
  resource_group_name      = var.resource_group
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  is_hns_enabled = true
}

resource "azurerm_storage_container" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.this.id
}

resource "azurerm_storage_container" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.this.id
}

resource "azurerm_storage_container" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.this.id
}