// SecOps Multi-Agent — Azure deploy (Phase 5b-2), resource-group scoped.
//
// Authored as code; provisioned MANUALLY by the owner (see infra/README.md). One
// `az deployment group create` brings up: Log Analytics + Sentinel, ACR, Postgres
// Flexible Server, a Container Apps environment + the backend app (system-assigned
// managed identity granted Log Analytics Reader + AcrPull — no secrets in the image),
// a Static Web App, and the synthetic Logs-Ingestion plumbing (DCE/DCR/custom table).
//
// Secrets (DEMO_PASSWORD, POSTGRES password, OPENROUTER_API_KEY) are passed as secure
// parameters at deploy time and stored as Container App secrets — never committed.

@description('Short prefix for resource names (lowercase, 3-12 chars).')
@minLength(3)
@maxLength(12)
param prefix string = 'secops'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Demo password required on every API request (Container App secret).')
@secure()
param demoPassword string

@description('Postgres administrator password (Container App + server secret).')
@secure()
param postgresAdminPassword string

@description('OpenRouter API key for the live LLM (optional; empty uses the offline stub).')
@secure()
param openRouterApiKey string = ''

@description('Backend container image. First deploy uses a public placeholder; CI then pushes the real ACR image and updates the app.')
param containerImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Allowed CORS origin(s) for the API — set to the Static Web App URL after first deploy.')
param corsOrigins string = 'http://localhost:3000'

var uniq = uniqueString(resourceGroup().id)
var acrName = toLower('${prefix}acr${uniq}')
var workspaceName = '${prefix}-law'
var pgName = toLower('${prefix}-pg-${uniq}')
var pgAdmin = 'secopsadmin'
var pgDatabase = 'secops'
var acaEnvName = '${prefix}-aca-env'
var appName = '${prefix}-backend'
var swaName = '${prefix}-web'
var postgresDsn = 'postgresql://${pgAdmin}:${postgresAdminPassword}@${pgName}.postgres.database.azure.com:5432/${pgDatabase}?sslmode=require'

// --- Observability: Log Analytics + Microsoft Sentinel --------------------------------

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// Onboard Microsoft Sentinel onto the workspace.
resource sentinel 'Microsoft.SecurityInsights/onboardingStates@2024-03-01' = {
  scope: workspace
  name: 'default'
  properties: {}
}

// --- Container Registry ---------------------------------------------------------------

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false } // managed-identity pull, no admin creds
}

// --- Postgres Flexible Server (Burstable) — the checkpointer DSN -----------------------

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: pgName
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: pgAdmin
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
  }
}

resource pgDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: pgDatabase
}

// Allow other Azure services (the Container App) to reach the server.
resource pgFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

// --- Container Apps environment + backend app ----------------------------------------

resource acaEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: acaEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: { type: 'SystemAssigned' } // no secrets: pulls from ACR + queries logs via MI
  properties: {
    managedEnvironmentId: acaEnv.id
    configuration: {
      ingress: { external: true, targetPort: 8000, transport: 'auto' }
      registries: [
        { server: acr.properties.loginServer, identity: 'system' }
      ]
      secrets: [
        { name: 'demo-password', value: demoPassword }
        { name: 'postgres-dsn', value: postgresDsn }
        { name: 'openrouter-api-key', value: openRouterApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: containerImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'MOCK_MODE', value: 'true' }
            { name: 'DEMO_PASSWORD', secretRef: 'demo-password' }
            { name: 'POSTGRES_DSN', secretRef: 'postgres-dsn' }
            { name: 'OPENROUTER_API_KEY', secretRef: 'openrouter-api-key' }
            { name: 'CORS_ORIGINS', value: corsOrigins }
            { name: 'AZURE_WORKSPACE_ID', value: workspace.properties.customerId }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 } // scale-to-zero; set min=1 for a live demo
    }
  }
}

// --- Static Web App (frontend) --------------------------------------------------------

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: swaName
  location: location
  sku: { name: 'Free', tier: 'Free' }
  properties: {}
}

// --- Role assignments for the backend managed identity --------------------------------

var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull
var logReaderRoleId = '73c42c96-874c-492b-b04d-ab87d138a893' // Log Analytics Reader

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, backend.id, acrPullRoleId)
  scope: acr
  properties: {
    principalId: backend.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

resource logReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(workspace.id, backend.id, logReaderRoleId)
  scope: workspace
  properties: {
    principalId: backend.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', logReaderRoleId)
  }
}

// --- Synthetic data: Logs Ingestion (DCE + custom table + DCR) -------------------------

module ingestion 'ingestion.bicep' = {
  name: 'ingestion'
  params: {
    prefix: prefix
    location: location
    workspaceName: workspace.name
    ingestPrincipalId: backend.identity.principalId
  }
}

// --- Outputs (consumed by deploy.sh / the GitHub workflows) ---------------------------

output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
output backendUrl string = 'https://${backend.properties.configuration.ingress.fqdn}'
output backendAppName string = backend.name
output staticWebAppName string = swa.name
output staticWebAppDefaultHostname string = swa.properties.defaultHostname
output workspaceCustomerId string = workspace.properties.customerId
output dceLogsIngestionEndpoint string = ingestion.outputs.dceLogsIngestionEndpoint
output dcrImmutableId string = ingestion.outputs.dcrImmutableId
output syntheticStreamName string = ingestion.outputs.streamName
