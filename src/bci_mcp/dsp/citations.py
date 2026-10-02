"""Machine-readable citations for what this pipeline computes.

``METRIC_INFO`` explains each metric in prose; this module gives an agent that
cites its sources something it can resolve and check: DOI-keyed references for
the analysis method and for each metric's literature basis, the software's own
citation and license, and a plain statement of data provenance.

Scope is deliberately narrow. bci-mcp only vouches for sources it actually
implements, so a metric with no single primary source gets an empty list rather
than a plausible-looking citation, and a source that *contests* a metric is
tagged ``caveat`` so it is never cited as support. Dataset licensing is out of
scope: the server bundles no datasets and cannot see where an upstream stream's
samples came from (see ``DATA_PROVENANCE``).

Entries mirror ``paper/paper.bib``; a test keeps the DOIs in sync.
"""
from __future__ import annotations

# Bibliographic records, keyed by the same ids as paper/paper.bib.
REFERENCES: dict[str, dict[str, object]] = {
    "welch1967": {
        "authors": ["Welch, Peter D."],
        "year": 1967,
        "title": "The use of fast Fourier transform for the estimation of power "
                 "spectra: A method based on time averaging over short, modified "
                 "periodograms",
        "journal": "IEEE Transactions on Audio and Electroacoustics",
        "doi": "10.1109/TAU.1967.1161901",
    },
    "virtanen2020": {
        "authors": ["Virtanen, Pauli", "Gommers, Ralf", "Oliphant, Travis E."],
        "et_al": True,  # author list truncated; the DOI record has it in full
        "year": 2020,
        "title": "SciPy 1.0: Fundamental algorithms for scientific computing in "
                 "Python",
        "journal": "Nature Methods",
        "doi": "10.1038/s41592-019-0686-2",
    },
    "pope1995": {
        "authors": ["Pope, Alan T.", "Bogart, Edward H.", "Bartolome, Debbie S."],
        "year": 1995,
        "title": "Biocybernetic system evaluates indices of operator engagement in "
                 "automated task",
        "journal": "Biological Psychology",
        "doi": "10.1016/0301-0511(95)05116-3",
    },
    "lubar1991": {
        "authors": ["Lubar, Joel F."],
        "year": 1991,
        "title": "Discourse on the development of EEG diagnostics and biofeedback "
                 "for attention-deficit/hyperactivity disorders",
        "journal": "Biofeedback and Self-Regulation",
        "doi": "10.1007/BF01000016",
    },
    "monastra1999": {
        "authors": ["Monastra, Vincent J.", "Lubar, Joel F.", "Linden, Michael",
                    "VanDeusen, Peter", "Green, George", "Wing, William",
                    "Phillips, Arthur", "Fenger, T. Nick"],
        "year": 1999,
        "title": "Assessing attention deficit hyperactivity disorder via "
                 "quantitative electroencephalography: An initial validation study",
        "journal": "Neuropsychology",
        "doi": "10.1037/0894-4105.13.3.424",
    },
    "arns2013": {
        "authors": ["Arns, Martijn", "Conners, C. Keith", "Kraemer, Helena C."],
        "year": 2013,
        "title": "A decade of EEG theta/beta ratio research in ADHD: A meta-analysis",
        "journal": "Journal of Attention Disorders",
        "doi": "10.1177/1087054712460087",
    },
    "eoh2005": {
        "authors": ["Eoh, Hong J.", "Chung, Min K.", "Kim, Seong-Han"],
        "year": 2005,
        "title": "Electroencephalographic study of drowsiness in simulated driving "
                 "with sleep deprivation",
        "journal": "International Journal of Industrial Ergonomics",
        "doi": "10.1016/j.ergon.2004.09.006",
    },
    "berger1929": {
        "authors": ["Berger, Hans"],
        "year": 1929,
        "title": "Über das Elektrenkephalogramm des Menschen",
        "journal": "Archiv für Psychiatrie und Nervenkrankheiten",
        "doi": "10.1007/BF01797193",
    },
}

# How a source relates to what it is attached to.
#   basis          — the formula or idea comes from here; cite as support.
#   caveat         — limits or contests the claim; cite alongside, never as support.
#   implementation — the code that computes it.
ROLES = ("basis", "caveat", "implementation")

METHOD_CITATIONS: list[tuple[str, str]] = [
    ("welch1967", "basis"),
    ("virtanen2020", "implementation"),
]

# Mirrors the ``basis`` text in ``metrics.METRIC_INFO``. ``engagement`` is a
# conventional beta/alpha ratio with no single primary source, so it is left
# empty rather than given a borrowed citation.
METRIC_CITATIONS: dict[str, list[tuple[str, str]]] = {
    "focus": [("pope1995", "basis")],
    "calm": [("berger1929", "basis")],
    "attention": [("lubar1991", "basis"), ("monastra1999", "basis"),
                  ("arns2013", "caveat")],
    "engagement": [],
    "fatigue": [("eoh2005", "basis")],
    "meditation": [("berger1929", "basis")],
}

# Mirrors CITATION.cff (which is not shipped in the wheel); a test keeps them in sync.
SOFTWARE_CITATION: dict[str, object] = {
    "title": "BCI-MCP: Plug your brain into any AI",
    "authors": [{"name": "Ganbold, Enkhbold",
                 "orcid": "https://orcid.org/0009-0007-1785-7034"}],
    "license": "MIT",
    "repository": "https://github.com/enkhbold470/bci-mcp",
    "url": "https://enkhbold470.github.io/bci-mcp/",
}

DATA_PROVENANCE: dict[str, object] = {
    "bundled_datasets": [],
    "statement": "bci-mcp bundles no datasets. Readings are computed live from "
                 "the connected source: a headset, an LSL stream, or generated "
                 "synthetic:// signal. The server cannot see where an upstream "
                 "stream's samples came from, so it attaches no dataset, license "
                 "or access terms to readings. If a third-party dataset is "
                 "replayed into it, that dataset's own license and citation still "
                 "apply; cite it directly.",
}

NOTE: str = (
    "DOIs are the stable identifiers; resolve one via its `url` before citing it. "
    "Cite `caveat` sources alongside the metric, never as support for it. An "
    "empty list means the metric has no single primary source (see "
    "get_metric_definitions `basis`)."
)


def _resolve(entries: list[tuple[str, str]]) -> list[dict[str, object]]:
    return [
        {"id": ref_id, "role": role, **REFERENCES[ref_id],
         "url": f"https://doi.org/{REFERENCES[ref_id]['doi']}"}
        for ref_id, role in entries
    ]


def method_citations() -> list[dict[str, object]]:
    """Resolved references for the analysis method (Welch PSD)."""
    return _resolve(METHOD_CITATIONS)


def metric_citations(metric: str) -> list[dict[str, object]]:
    """Resolved references for one metric (empty if it has no primary source)."""
    return _resolve(METRIC_CITATIONS[metric])


def citations() -> dict:
    """Everything an agent needs to cite this server's output."""
    from .. import __version__

    return {
        "software": {**SOFTWARE_CITATION, "version": __version__},
        "method": method_citations(),
        "metrics": {name: metric_citations(name) for name in METRIC_CITATIONS},
        "data_provenance": DATA_PROVENANCE,
        "note": NOTE,
    }
