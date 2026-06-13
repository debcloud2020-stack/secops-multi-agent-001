"""Threat-intel enrichment: NVD 2.0 + CISA KEV + FIRST EPSS → a priority score.

``enrich_cve`` returns ``cvss, epss, in_kev, known_ransomware, summary, priority`` where::

    priority = cvss*0.3 + epss*10*0.3 + (3 if in_kev) + (1 if known_ransomware)

Mock mode reads fixtures; live mode calls the APIs via httpx and falls back to mock.
"""

from __future__ import annotations

import logging

from secops.config import get_settings
from secops.state import CVEMatch
from secops.tools import load_fixture

log = logging.getLogger(__name__)

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"


def compute_priority(cvss: float, epss: float, in_kev: bool, known_ransomware: bool) -> float:
    """Layered prioritization — CVSS alone is insufficient."""
    score = cvss * 0.3 + epss * 10 * 0.3 + (3 if in_kev else 0) + (1 if known_ransomware else 0)
    return round(score, 2)


def enrich_cve(cve_id: str) -> dict:
    """Return enrichment for one CVE (mock fixtures by default)."""
    settings = get_settings()
    if settings.mock_mode:
        return _mock(cve_id)
    try:
        return _live(cve_id, settings)
    except Exception as exc:  # noqa: BLE001 — fall back to mock on any failure.
        log.warning("threat_intel live lookup failed for %s (%s); using mock", cve_id, exc)
        return _mock(cve_id)


def to_cve_match(enrichment: dict) -> CVEMatch:
    return CVEMatch(**enrichment)


def _assemble(cve_id, cvss, epss, summary, in_kev, known_ransomware) -> dict:
    return {
        "cve_id": cve_id,
        "cvss": cvss,
        "epss": epss,
        "summary": summary,
        "in_kev": in_kev,
        "known_ransomware": known_ransomware,
        "priority": compute_priority(cvss, epss, in_kev, known_ransomware),
    }


def _mock(cve_id: str) -> dict:
    kev = load_fixture("threat_intel", "kev.json")
    epss_doc = load_fixture("threat_intel", "epss.json")

    # The NVD fixture is per-CVE; a CVE we don't have a fixture for (e.g. an extra
    # scanner result) gets a zero-score stub, mirroring "no NVD record" on the live path.
    try:
        nvd = load_fixture("threat_intel", f"nvd_{cve_id}.json")
        vuln = nvd["vulnerabilities"][0]["cve"]  # type: ignore[index]
        cvss = float(vuln["metrics"]["cvssMetricV31"][0]["cvssData"]["baseScore"])
        summary = vuln["descriptions"][0]["value"]
    except FileNotFoundError:
        cvss, summary = 0.0, ""

    kev_entry = next((v for v in kev["vulnerabilities"] if v["cveID"] == cve_id), None)  # type: ignore[index]
    in_kev = kev_entry is not None
    known_ransomware = bool(
        kev_entry and str(kev_entry.get("knownRansomwareCampaignUse", "")).lower() == "known"
    )

    epss_entry = next((d for d in epss_doc["data"] if d["cve"] == cve_id), None)  # type: ignore[index]
    epss = float(epss_entry["epss"]) if epss_entry else 0.0

    return _assemble(cve_id, cvss, epss, summary, in_kev, known_ransomware)


def _live(cve_id: str, settings) -> dict:
    import httpx

    headers = {"apiKey": settings.nvd_api_key} if settings.nvd_api_key else {}
    with httpx.Client(timeout=20) as client:
        resp = client.get(NVD_URL, params={"cveId": cve_id}, headers=headers)
        nvd = resp.raise_for_status().json()
        vuln = nvd["vulnerabilities"][0]["cve"]
        metrics = vuln.get("metrics", {})
        cvss_list = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30") or []
        cvss = float(cvss_list[0]["cvssData"]["baseScore"]) if cvss_list else 0.0
        descriptions = vuln.get("descriptions", [])
        summary = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        kev = client.get(KEV_URL).raise_for_status().json()
        kev_entry = next((v for v in kev["vulnerabilities"] if v["cveID"] == cve_id), None)
        in_kev = kev_entry is not None
        known_ransomware = bool(
            kev_entry and str(kev_entry.get("knownRansomwareCampaignUse", "")).lower() == "known"
        )

        epss_doc = client.get(EPSS_URL, params={"cve": cve_id}).raise_for_status().json()
        data = epss_doc.get("data", [])
        epss = float(data[0]["epss"]) if data else 0.0

    return _assemble(cve_id, cvss, epss, summary, in_kev, known_ransomware)
