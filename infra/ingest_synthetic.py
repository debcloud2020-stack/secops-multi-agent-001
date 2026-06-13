"""Push synthetic incidents to the custom Log Analytics table via the Logs Ingestion API.

Feeds ``data_mode = "synthetic"`` (azure_logs._synthetic queries SecOpsSynthetic_CL). Each
mock detection fixture row is wrapped as ``{TimeGenerated, Detection, Row}`` and uploaded to
the DCR stream so the synthetic table mirrors the offline fixtures — queried live like real
data. Run MANUALLY after deploy:

    pip install azure-monitor-ingestion azure-identity
    export DCE_ENDPOINT=<dceLogsIngestionEndpoint output>
    export DCR_IMMUTABLE_ID=<dcrImmutableId output>
    export STREAM_NAME=Custom-SecOpsSynthetic
    az login   # an identity with Monitoring Metrics Publisher on the DCR
    python infra/ingest_synthetic.py
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "backend" / "fixtures" / "azure_logs"


def main() -> int:
    from azure.identity import DefaultAzureCredential
    from azure.monitor.ingestion import LogsIngestionClient

    endpoint = os.environ["DCE_ENDPOINT"]
    rule_id = os.environ["DCR_IMMUTABLE_ID"]
    stream = os.environ.get("STREAM_NAME", "Custom-SecOpsSynthetic")

    client = LogsIngestionClient(endpoint=endpoint, credential=DefaultAzureCredential())
    now = datetime.now(UTC).isoformat()

    logs: list[dict] = []
    for fixture in sorted(FIXTURES.glob("*.json")):
        rows = json.loads(fixture.read_text())
        for row in rows:
            logs.append({"TimeGenerated": now, "Detection": fixture.stem, "Row": row})

    client.upload(rule_id=rule_id, stream_name=stream, logs=logs)
    detections = len(list(FIXTURES.glob("*.json")))
    print(f"Uploaded {len(logs)} synthetic rows across {detections} detections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
