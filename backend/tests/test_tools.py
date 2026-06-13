"""Tool tests (mock mode): azure_logs, threat_intel priority math, scanner normalization."""

from __future__ import annotations

import pytest

from secops.state import CVEMatch
from secops.tools import azure_logs, scanner
from secops.tools.threat_intel import compute_priority, enrich_cve, to_cve_match


def test_azure_logs_named_detection_returns_rows():
    rows = azure_logs.run_detection("failed_signins_burst")
    assert isinstance(rows, list) and rows
    assert "UserPrincipalName" in rows[0]


def test_azure_logs_unknown_detection_raises():
    with pytest.raises(KeyError):
        azure_logs.run_detection("definitely_not_a_detection")


def test_enrich_cve_priority_math():
    e = enrich_cve("CVE-2026-00000")
    assert e["cvss"] == 9.8
    assert e["epss"] == 0.92
    assert e["in_kev"] is True
    assert e["known_ransomware"] is False
    # 9.8*0.3 + 0.92*10*0.3 + 3 + 0 = 8.7
    assert e["priority"] == 8.7
    assert isinstance(to_cve_match(e), CVEMatch)


def test_compute_priority_formula():
    assert compute_priority(9.8, 0.92, True, False) == 8.7
    assert compute_priority(0.0, 0.0, False, False) == 0.0
    assert compute_priority(5.0, 0.5, True, True) == round(1.5 + 1.5 + 3 + 1, 2)


def test_enrich_cve_missing_fixture_is_zero_stub():
    e = enrich_cve("CVE-0000-99999")  # no NVD fixture
    assert e["cvss"] == 0.0 and e["in_kev"] is False and e["priority"] == 0.0


def test_scanner_normalizes_to_five_keys():
    for target in ("image", "python"):
        results = scanner.scan(target)
        assert results
        assert set(results[0]) == {"id", "package", "installed", "fixed", "severity"}
