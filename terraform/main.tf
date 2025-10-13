provider "azurerm" {
  subscription_id = var.subscription_id
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = false
    }
  }
}

data "azurerm_client_config" "current" {}

# resource group
resource "azurerm_resource_group" "rg" {
  name     = "group-${random_string.suffix.result}"
  location = "japaneast"
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_log_analytics_workspace" "workspace" {
  name                = "workspace-${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "container_app_environment" {
  name                       = "environment-${random_string.suffix.result}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.workspace.id

  identity {
    type = "SystemAssigned"
  }

}

resource "azurerm_role_assignment" "frontend_acr_pull" {
  principal_id         = azurerm_container_app.frontend.identity[0].principal_id
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acr.id

  depends_on = [azurerm_container_app.frontend, azurerm_container_registry.acr]

}

resource "azurerm_role_assignment" "backend_acr_pull" {
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acr.id

  depends_on = [azurerm_container_app.backend, azurerm_container_registry.acr]
}


# frontend container app

resource "azurerm_container_app" "frontend" {
  name                         = "frontend-251005"
  container_app_environment_id = azurerm_container_app_environment.container_app_environment.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "frontendcontainerapp-${random_string.suffix.result}"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
     cpu    = 0.25
      memory = "0.5Gi"
    }
  }
}
# backend container app
resource "azurerm_container_app" "backend" {
  name                         = "backend-251005"
  container_app_environment_id = azurerm_container_app_environment.container_app_environment.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "backendcontainerapp-${random_string.suffix.result}"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
     cpu    = 0.25
      memory = "0.5Gi"
    }

  }
}

# container registry
resource "azurerm_container_registry" "acr" {
  name                = "acr${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Premium"

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.acr_user_assigned_identity.id
    ]
  }

  encryption {
    key_vault_key_id   = azurerm_key_vault_key.acr_key.id
    identity_client_id = azurerm_user_assigned_identity.acr_user_assigned_identity.client_id
  }


}

resource "azurerm_user_assigned_identity" "acr_user_assigned_identity" {
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  name = "registry-uai-${random_string.suffix.result}"
}

# key vault
resource "azurerm_key_vault" "key_vault" {
  name                        = "keyVault-${random_string.suffix.result}"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true
  sku_name                    = "standard"

  # Terraform 実行者用のアクセス権
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get",
      "Create",
      "Delete",
      "Update",
      "List",
      "GetRotationPolicy",
      "SetRotationPolicy",
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge", "Recover"
    ]

    storage_permissions = [
      "Get", "List", "Delete", "Purge", "Recover"
    ]
  }

  # ACR の User Assigned Identity にもアクセス権を付与
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.acr_user_assigned_identity.principal_id

    key_permissions = [
      "Get", "WrapKey", "UnwrapKey", "Encrypt", "Decrypt"
    ]
  }
}

resource "azurerm_key_vault_key" "acr_key" {
  name         = "super-secret-${random_string.suffix.result}"
  key_vault_id = azurerm_key_vault.key_vault.id
  key_type     = "RSA"
  key_size     = 2048
  key_opts     = ["decrypt", "encrypt", "sign", "unwrapKey", "wrapKey", "verify"]
}


# postgresql
resource "azurerm_postgresql_flexible_server" "postgresql" {
  name                   = "postgresql-${random_string.suffix.result}"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "12"
  administrator_login    = var.postgresql_login_name
  administrator_password = var.postgresql_password
  storage_mb             = 5120
  sku_name               = "B_Standard_B1ms"
  zone                   = "1"

}

resource "azurerm_postgresql_flexible_server_database" "postgresql_database" {
  name      = "database-${random_string.suffix.result}"
  server_id = azurerm_postgresql_flexible_server.postgresql.id
  collation = "ja_JP.utf8"
  charset   = "UTF8"

  # prevent the possibility of accidental data loss
  # lifecycle {
  #   prevent_destroy = true
  # }
}

# storage account
resource "azurerm_storage_account" "storage_account" {
  name                     = "storageaccount${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "storage_container" {
  name                  = "storagecontainer-${random_string.suffix.result}"
  storage_account_id    = azurerm_storage_account.storage_account.id
  container_access_type = "private"
}
