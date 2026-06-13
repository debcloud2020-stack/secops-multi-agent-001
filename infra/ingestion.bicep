// Synthetic-data plumbing: a Data Collection Endpoint, a custom table, and a Data
// Collection Rule so synthetic incidents can be pushed via the Logs Ingestion API and
// queried live (data_mode = "synthetic"). The backend's managed identity is granted
// Monitoring Metrics Publisher on the DCR so it (or the ingest script) can post rows.

param prefix string
param location string
param workspaceName string
@description('Principal (the backend managed identity) allowed to publish to the DCR.')
param ingestPrincipalId string

var dceName = '${prefix}-dce'
var dcrName = '${prefix}-dcr'
var tableName = 'SecOpsSynthetic_CL'
var streamName = 'Custom-SecOpsSynthetic'

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

resource dce 'Microsoft.Insights/dataCollectionEndpoints@2023-03-11' = {
  name: dceName
  location: location
  properties: { networkAcls: { publicNetworkAccess: 'Enabled' } }
}

// Custom table queried by azure_logs._synthetic (columns are used verbatim, no _s suffix).
resource table 'Microsoft.OperationalInsights/workspaces/tables@2022-10-01' = {
  parent: workspace
  name: tableName
  properties: {
    schema: {
      name: tableName
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'Detection', type: 'string' }
        { name: 'Row', type: 'dynamic' }
      ]
    }
  }
}

resource dcr 'Microsoft.Insights/dataCollectionRules@2023-03-11' = {
  name: dcrName
  location: location
  properties: {
    dataCollectionEndpointId: dce.id
    streamDeclarations: {
      '${streamName}': {
        columns: [
          { name: 'TimeGenerated', type: 'datetime' }
          { name: 'Detection', type: 'string' }
          { name: 'Row', type: 'dynamic' }
        ]
      }
    }
    destinations: {
      logAnalytics: [
        { name: 'la', workspaceResourceId: workspace.id }
      ]
    }
    dataFlows: [
      {
        streams: [streamName]
        destinations: ['la']
        outputStream: 'Custom-${tableName}'
        transformKql: 'source'
      }
    ]
  }
  dependsOn: [table]
}

// Monitoring Metrics Publisher on the DCR for the ingest principal.
var metricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'
resource ingestRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(dcr.id, ingestPrincipalId, metricsPublisherRoleId)
  scope: dcr
  properties: {
    principalId: ingestPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', metricsPublisherRoleId)
  }
}

output dceLogsIngestionEndpoint string = dce.properties.logsIngestion.endpoint
output dcrImmutableId string = dcr.properties.immutableId
output streamName string = streamName
