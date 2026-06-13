"""Vulnerability scanners: trivy (image/fs) + pip-audit (python), normalized.

Each result is normalized to ``{id, package, installed, fixed, severity}``. Mock mode
reads fixtures (raw tool JSON, run through the same normalizer); live mode shells out to
the tools via subprocess and falls back to mock on failure / missing CLI.
"""

from __future__ import annotations

import json
import logging
import subprocess

from secops.tools import load_fixture

log = logging.getLogger(__name__)

Normalized = dict[str, str | None]


def _normalize_trivy(doc: dict) -> list[Normalized]:
    out: list[Normalized] = []
    for result in doc.get("Results", []):
        for v in result.get("Vulnerabilities") or []:
            out.append(
                {
                    "id": v.get("VulnerabilityID"),
                    "package": v.get("PkgName"),
                    "installed": v.get("InstalledVersion"),
                    "fixed": v.get("FixedVersion"),
                    "severity": (v.get("Severity") or "").lower() or None,
                }
            )
    return out


def _normalize_pip_audit(doc: dict) -> list[Normalized]:
    out: list[Normalized] = []
    for dep in doc.get("dependencies", []):
        for v in dep.get("vulns") or []:
            fixes = v.get("fix_versions") or []
            out.append(
                {
                    "id": v.get("id"),
                    "package": dep.get("name"),
                    "installed": dep.get("version"),
                    "fixed": fixes[0] if fixes else None,
                    "severity": None,  # pip-audit doesn't grade severity
                }
            )
    return out


def scan(
    target: str = "image", data_mode: str = "mock", notices: list[str] | None = None
) -> list[Normalized]:
    """Scan a target per ``data_mode``. 'image'/'fs' → trivy, 'python' → pip-audit.

    ``mock`` reads fixtures; ``live``/``synthetic`` shell out to the real scanner and fall
    back to the mock fixture on failure / missing CLI, appending a note to ``notices``.
    """
    tool = "pip_audit" if target == "python" else "trivy"
    if data_mode == "mock":
        return _mock(tool)
    try:
        return _live(tool, target)
    except Exception as exc:  # noqa: BLE001 — fall back to mock on failure / missing CLI.
        log.warning("scanner %s run failed for %s (%s); falling back to mock", data_mode, tool, exc)
        if notices is not None:
            notices.append(
                f"vuln_scanner: '{data_mode}' scan unavailable "
                f"({type(exc).__name__}); used mock fixtures"
            )
        return _mock(tool)


def _mock(tool: str) -> list[Normalized]:
    doc = load_fixture("scanner", f"{tool}.json")
    return _normalize_trivy(doc) if tool == "trivy" else _normalize_pip_audit(doc)  # type: ignore[arg-type]


def _live(tool: str, target: str) -> list[Normalized]:
    if tool == "trivy":
        kind = "image" if target == "image" else "fs"
        arg = "." if kind == "fs" else target
        proc = subprocess.run(
            ["trivy", kind, "--quiet", "--format", "json", arg],
            capture_output=True, text=True, timeout=300, check=True,
        )
        return _normalize_trivy(json.loads(proc.stdout))
    proc = subprocess.run(
        ["pip-audit", "--format", "json"],
        capture_output=True, text=True, timeout=300, check=True,
    )
    return _normalize_pip_audit(json.loads(proc.stdout))
