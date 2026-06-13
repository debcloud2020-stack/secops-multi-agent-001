"""Azure Monitor / Sentinel log detections.

A **curated** library of named KQL detections — the agent SELECTS a detection by name;
it never invents free-text KQL. Mock mode returns fixtures; live mode runs the KQL via
``azure-monitor-query`` and falls back to the mock fixture on any failure (PLAN.md §7).
"""

from __future__ import annotations

import logging

from secops.config import get_settings
from secops.tools import load_fixture

log = logging.getLogger(__name__)

# Curated detections: name -> KQL. KQL is used only on the live path.
DETECTIONS: dict[str, str] = {
    "failed_signins_burst": (
        "SigninLogs | where ResultType != 0 "
        "| summarize FailureCount=count() by UserPrincipalName, IPAddress "
        "| where FailureCount > 10"
    ),
    "impossible_travel": (
        "SigninLogs | extend loc=tostring(LocationDetails.countryOrRegion) "
        "| summarize Locations=make_set(loc) by UserPrincipalName "
        "| where array_length(Locations) > 1"
    ),
    "open_incidents": (
        "SecurityIncident | where Status == 'Active' "
        "| project IncidentNumber, Title, Severity, Status, CreatedTime, Owner"
    ),
    "privilege_grants": (
        "AuditLogs | where OperationName has 'Add member to role' "
        "| project TimeGenerated, Initiator, Operation=OperationName, Role, Target, Result"
    ),
}


def detection_names() -> list[str]:
    return list(DETECTIONS)


def run_detection(name: str) -> list[dict]:
    """Run a named detection and return rows. Unknown names raise ``KeyError``."""
    if name not in DETECTIONS:
        raise KeyError(f"unknown detection '{name}'; choose from {detection_names()}")

    settings = get_settings()
    if settings.mock_mode:
        return _mock(name)

    try:
        return _live(name, DETECTIONS[name], settings)
    except Exception as exc:  # noqa: BLE001 — never die on stage; fall back to mock.
        log.warning("azure_logs live query failed for %s (%s); falling back to mock", name, exc)
        return _mock(name)


def _mock(name: str) -> list[dict]:
    return load_fixture("azure_logs", f"{name}.json")  # type: ignore[return-value]


def _live(name: str, kql: str, settings) -> list[dict]:
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import LogsQueryClient, LogsQueryStatus

    if not settings.azure_workspace_id:
        raise RuntimeError("AZURE_WORKSPACE_ID not set")
    client = LogsQueryClient(DefaultAzureCredential())
    from datetime import timedelta

    resp = client.query_workspace(settings.azure_workspace_id, kql, timespan=timedelta(days=1))
    if resp.status != LogsQueryStatus.SUCCESS or not resp.tables:
        raise RuntimeError(f"query status {resp.status}")
    table = resp.tables[0]
    return [dict(zip(table.columns, row, strict=False)) for row in table.rows]
