"""Citations must be resolvable, honest about their role, and in sync.

An agent that cites a metric's source will repeat whatever this module says, so
these tests pin the DOIs to the paper's bibliography and the software citation
to CITATION.cff, and assert that a contesting source is never tagged as support.
"""
import asyncio
import json
import re
from pathlib import Path

from bci_mcp import __version__
from bci_mcp.dsp.citations import (
    METHOD_CITATIONS,
    METRIC_CITATIONS,
    REFERENCES,
    ROLES,
    SOFTWARE_CITATION,
    citations,
)
from bci_mcp.dsp.metrics import METRIC_NAMES
from bci_mcp.mcp.service import BrainService

ROOT = Path(__file__).resolve().parent.parent


def test_every_metric_has_a_citation_entry():
    assert set(METRIC_CITATIONS) == set(METRIC_NAMES)


def test_citation_ids_and_roles_are_valid():
    for ref_id, role in METHOD_CITATIONS + [
        entry for entries in METRIC_CITATIONS.values() for entry in entries
    ]:
        assert ref_id in REFERENCES
        assert role in ROLES


def test_dois_match_paper_bibliography():
    bib = (ROOT / "paper" / "paper.bib").read_text()
    for ref_id, ref in REFERENCES.items():
        entry = re.search(rf"@\w+\{{{ref_id},(.*?)\n\}}", bib, re.S)
        assert entry, f"{ref_id} missing from paper.bib"
        assert f"doi     = {{{ref['doi']}}}" in entry.group(1), ref_id
        assert f"year    = {{{ref['year']}}}" in entry.group(1), ref_id


def test_software_citation_matches_citation_cff():
    cff = (ROOT / "CITATION.cff").read_text()
    assert f'title: "{SOFTWARE_CITATION["title"]}"' in cff
    assert f"license: {SOFTWARE_CITATION['license']}" in cff
    assert f'repository-code: "{SOFTWARE_CITATION["repository"]}"' in cff
    for author in SOFTWARE_CITATION["authors"]:
        assert author["orcid"] in cff
    assert "MIT License" in (ROOT / "LICENSE").read_text()


def test_authors_are_people_not_placeholders():
    for ref in REFERENCES.values():
        assert ref["authors"]
        assert not any("et al" in a.lower() for a in ref["authors"])


def test_citations_payload_is_json_and_versioned():
    out = citations()
    assert set(out) == {"software", "method", "metrics", "data_provenance", "note"}
    assert out["software"]["version"] == __version__
    assert out["data_provenance"]["bundled_datasets"] == []
    roundtrip = json.loads(json.dumps(out))
    assert roundtrip["method"][0]["url"] == "https://doi.org/10.1109/TAU.1967.1161901"


def test_contested_source_is_a_caveat_not_support():
    attention = {r["id"]: r["role"] for r in citations()["metrics"]["attention"]}
    assert attention["arns2013"] == "caveat"
    assert attention["lubar1991"] == "basis"


def test_metric_definitions_carry_resolved_references():
    defs = BrainService().get_metric_definitions()
    focus = defs["metrics"]["focus"]
    assert focus["formula"] == "beta / (alpha + theta)"
    assert [r["doi"] for r in focus["references"]] == ["10.1016/0301-0511(95)05116-3"]
    assert defs["metrics"]["engagement"]["references"] == []
    assert defs["method_references"][0]["id"] == "welch1967"


def test_metric_definitions_do_not_mutate_metric_info():
    from bci_mcp.dsp.metrics import METRIC_INFO

    BrainService().get_metric_definitions()
    assert all("references" not in info for info in METRIC_INFO.values())


def test_server_exposes_citations_resource_as_json():
    from bci_mcp.mcp import server

    loop = asyncio.new_event_loop()
    try:
        resources = loop.run_until_complete(server.mcp.list_resources())
        by_uri = {str(r.uri): r for r in resources}
        assert by_uri["brain://citations"].mimeType == "application/json"
        contents = list(loop.run_until_complete(
            server.mcp.read_resource("brain://citations")))
    finally:
        loop.close()
    payload = json.loads(contents[0].content)
    assert payload["metrics"]["focus"][0]["id"] == "pope1995"
    assert "Über" in payload["metrics"]["calm"][0]["title"]
