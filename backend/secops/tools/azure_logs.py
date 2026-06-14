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
    # AzureActivity is real + populated in a fresh workspace (no Entra P1 needed) — the
    # log_monitor agent uses this in live mode so the dashboard shows real rows.
    "azure_activity": (
        "AzureActivity | where TimeGenerated > ago(1d) "
        "| summarize EventCount=count() by OperationNameValue, ActivityStatusValue, "
        "Caller, CallerIpAddress "
        "| order by EventCount desc | take 25"
    ),
}


# Synthetic incidents are pushed to a custom Log Analytics table via the Logs Ingestion
# API (Phase 5b-2); 'synthetic' mode queries that table with the same KQL surface.
SYNTHETIC_TABLE = "SecOpsSynthetic_CL"


def detection_names() -> list[str]:
    return list(DETECTIONS)


def run_detection(
    name: str, data_mode: str = "mock", notices: list[str] | None = None
) -> list[dict]:
    """Run a named detection per ``data_mode`` (mock/live/synthetic).

    Unknown names raise ``KeyError``. Live/synthetic fall back to the mock fixture on any
    failure (e.g. no Azure creds), appending a note to ``notices`` so the run surfaces it.
    """
    if name not in DETECTIONS:
        raise KeyError(f"unknown detection '{name}'; choose from {detection_names()}")

    if data_mode == "mock":
        return _mock(name)

    settings = get_settings()
    try:
        if data_mode == "synthetic":
            return _synthetic(name, settings)
        return _live(name, DETECTIONS[name], settings)
    except Exception as exc:  # noqa: BLE001 — never die on stage; fall back to mock.
        log.warning("azure_logs %s query failed for %s (%s); using mock", data_mode, name, exc)
        _note(notices, data_mode, exc)
        return _mock(name)


def _note(notices: list[str] | None, data_mode: str, exc: Exception) -> None:
    if notices is not None:
        notices.append(
            f"log_monitor: '{data_mode}' source unavailable "
            f"({type(exc).__name__}: {str(exc)[:120]}) — used mock fixtures"
        )


def _mock(name: str) -> list[dict]:
    return load_fixture("azure_logs", f"{name}.json")  # type: ignore[return-value]


def _synthetic(name: str, settings) -> list[dict]:
    """Query recent rows from the synthetic custom table (seeded via the Logs Ingestion API).

    Returns the real seeded incidents projected to the table schema — the agent reasons over
    them regardless of the requested detection ``name``.
    """
    if not settings.azure_workspace_id:
        raise RuntimeError("AZURE_WORKSPACE_ID not set (synthetic table query)")
    kql = (
        f"{SYNTHETIC_TABLE} | where TimeGenerated > ago(7d) "
        "| project TimeGenerated, IncidentId, Title, DetectionName, Severity, "
        "UserPrincipalName, SourceIp, Description, EventCount "
        "| order by TimeGenerated desc | take 50"
    )
    return _live(name, kql, settings)


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
