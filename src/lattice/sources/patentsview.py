from __future__ import annotations


def fetch_patentsview_placeholder() -> tuple[list[dict[str, object]], list[str]]:
    return [], [
        "PatentsView legacy API is discontinued and is migrating to the USPTO Open Data Portal. "
        "Connector kept as optional until a stable ODP query path is integrated."
    ]

