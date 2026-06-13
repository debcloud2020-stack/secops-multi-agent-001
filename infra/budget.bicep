// Optional spend guardrail — a subscription-scoped Consumption budget with email alerts.
// Subscription-scoped, so deploy separately from main.bicep:
//
//   az deployment sub create -l eastus -f infra/budget.bicep \
//     -p amount=25 contactEmails='["you@example.com"]'
//
// A budget alerts; it does NOT hard-stop spend. Pair it with teardown.sh after demos.
targetScope = 'subscription'

@description('Monthly budget cap in your billing currency.')
param amount int = 25

@description('Emails to notify at the alert thresholds.')
param contactEmails array

@description('First day of the budget period (YYYY-MM-01).')
param startDate string = '2026-06-01'

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'secops-monthly'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: { startDate: startDate }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      forecasted100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        contactEmails: contactEmails
        thresholdType: 'Forecasted'
      }
    }
  }
}
