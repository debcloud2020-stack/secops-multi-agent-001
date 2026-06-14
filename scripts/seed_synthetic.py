"""Seed realistic synthetic incidents into the SecOpsSynthetic_CL custom table.

A data utility (NOT deploy infra). Pushes rows via the Azure Monitor Logs Ingestion API so
``data_mode = "synthetic"`` returns real, queryable data. Rows match the table schema:
TimeGenerated, IncidentId, Title, DetectionName, Severity, UserPrincipalName, SourceIp,
Description, EventCount.

Run with the backend env so .env / settings load:

    az login                                  # needs Monitoring Metrics Publisher on the DCR
    cd backend && uv run python ../scripts/seed_synthetic.py            # upload
    cd backend && uv run python ../scripts/seed_synthetic.py --dry-run  # print rows, no upload

Reads DCE_ENDPOINT / DCR_IMMUTABLE_ID / DCR_STREAM_NAME from backend/.env (settings).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from secops.config import get_settings  # noqa: E402

# (DetectionName, Title, Severity, UserPrincipalName, SourceIp, Description, EventCount)
_INCIDENTS: list[tuple[str, str, str, str, str, str, int]] = [
    ("impossible_travel", "Impossible-travel sign-in for finance user", "high",
     "treasury@contoso.com", "203.0.113.66",
     "Sign-in from Sydney then Frankfurt within 35 minutes; likely credential theft.", 2),
    ("failed_signin_burst", "Password-spray burst on gateway account", "high",
     "svc-gateway@contoso.com", "198.51.100.23",
     "47 failed sign-ins in 4 minutes followed by one success from a new ASN.", 48),
    ("privilege_escalation", "Global Administrator granted after sign-in burst", "critical",
     "svc-gateway@contoso.com", "198.51.100.23",
     "Service account elevated to Global Administrator after a failed-signin burst.", 1),
    ("data_exfiltration", "Large SharePoint download to unmanaged device", "high",
     "j.okoro@contoso.com", "192.0.2.140",
     "2.3 GB downloaded from finance site to an unmanaged device overnight.", 1),
    ("malware_detected", "Defender flagged Cobalt Strike beacon", "critical",
     "host-fin-07@contoso.com", "192.0.2.55",
     "EDR detected a Cobalt Strike beacon on a finance workstation; isolate immediately.", 1),
    ("impossible_travel", "Impossible-travel for HR admin", "medium",
     "hr-admin@contoso.com", "203.0.113.9",
     "Concurrent sessions from two countries; MFA fatigue suspected.", 3),
    ("failed_signin_burst", "Brute-force against VPN appliance", "high",
     "vpn-svc@contoso.com", "198.51.100.77",
     "Sustained brute-force against the VPN appliance admin portal.", 120),
    ("privilege_escalation", "Unexpected owner role on key vault", "high",
     "ops@contoso.com", "192.0.2.201",
     "Owner role assigned on the production key vault outside change window.", 1),
    ("data_exfiltration", "Mailbox auto-forward to external domain", "medium",
     "treasury@contoso.com", "203.0.113.66",
     "Inbox rule created to auto-forward all mail to an external address.", 1),
    ("malware_detected", "Ransomware canary triggered on file server", "critical",
     "backup-svc@contoso.com", "192.0.2.88",
     "Shadow-copy deletion and mass file-rename detected on the nightly backup server.", 1),
]


def _rows() -> list[dict]:
    now = datetime.now(UTC)
    rows: list[dict] = []
    for i, (det, title, sev, upn, ip, desc, count) in enumerate(_INCIDENTS):
        rows.append(
            {
                "TimeGenerated": (now - timedelta(minutes=7 * i)).isoformat(),
                "IncidentId": f"SYN-{1001 + i}",
                "Title": title,
                "DetectionName": det,
                "Severity": sev,
                "UserPrincipalName": upn,
                "SourceIp": ip,
                "Description": desc,
                "EventCount": count,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry_run = "--dry-run" in argv
    rows = _rows()

    if dry_run:
        import json

        print(json.dumps(rows, indent=2))
        print(f"[dry-run] built {len(rows)} synthetic rows (not uploaded).")
        return 0

    s = get_settings()
    keys = ("dce_endpoint", "dcr_immutable_id", "dcr_stream_name")
    missing = [k.upper() for k in keys if not getattr(s, k)]
    if missing:
        print(f"Missing settings: {', '.join(missing)} — set them in backend/.env")
        return 1

    from azure.identity import DefaultAzureCredential
    from azure.monitor.ingestion import LogsIngestionClient

    client = LogsIngestionClient(endpoint=s.dce_endpoint, credential=DefaultAzureCredential())
    client.upload(rule_id=s.dcr_immutable_id, stream_name=s.dcr_stream_name, logs=rows)
    print(f"Uploaded {len(rows)} synthetic incidents to {s.dcr_stream_name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
