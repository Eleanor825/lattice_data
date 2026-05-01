from __future__ import annotations

from collections import defaultdict

from lattice.targets.artifacts import Artifact, EntityBundle
from lattice.utils import slugify


def build_entity_bundles(base_artifacts: list[Artifact], entity_artifacts: list[Artifact]) -> list[EntityBundle]:
    bundles: dict[str, EntityBundle] = {}
    alias_map: dict[str, str] = {}

    for entity in entity_artifacts:
        entity_id = str(entity.payload["entity_id"])
        bundle = EntityBundle(
            entity_id=entity_id,
            canonical_name=str(entity.payload.get("canonical_name", "")),
            aliases=list(entity.payload.get("aliases", [])),
            record_ids=list(entity.payload.get("record_ids", [])),
            source_ids=list(entity.payload.get("source_ids", [])),
        )
        bundles[entity_id] = bundle
        for alias in bundle.aliases:
            alias_map[slugify(alias)] = entity_id

    property_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for artifact in base_artifacts:
        entity_name = ""
        if artifact.artifact_type == "StructuredRecord":
            entity_name = str(artifact.payload.get("entity", "")).strip()
        elif artifact.artifact_type == "KnowledgeRecord":
            entity_name = str(artifact.payload.get("subject", "")).strip()
        elif artifact.artifact_type == "Document":
            entity_name = str(artifact.payload.get("title", "")).strip()
        entity_id = alias_map.get(slugify(entity_name)) if entity_name else None
        if not entity_id or entity_id not in bundles:
            continue

        bundle = bundles[entity_id]
        source_ref = artifact.source_refs[0] if artifact.source_refs else {}
        bundle.evidence.append(
            {
                "artifact_type": artifact.artifact_type,
                "record_id": artifact.lineage[0] if artifact.lineage else artifact.artifact_id,
                "source_id": source_ref.get("source_id", ""),
                "source_type": source_ref.get("source_type", ""),
            }
        )

        if artifact.artifact_type == "StructuredRecord":
            for key, value in dict(artifact.payload.get("fields", {})).items():
                property_item = {
                    "name": key,
                    "value": str(value),
                    "source_id": source_ref.get("source_id", ""),
                    "source_type": source_ref.get("source_type", ""),
                }
                bundle.properties.append(property_item)
                property_groups[(entity_id, key)].append(property_item)
        elif artifact.artifact_type == "KnowledgeRecord":
            predicate = str(artifact.payload.get("predicate", "")).strip()
            obj = str(artifact.payload.get("object", "")).strip()
            if predicate and obj:
                property_item = {
                    "name": predicate,
                    "value": obj,
                    "source_id": source_ref.get("source_id", ""),
                    "source_type": source_ref.get("source_type", ""),
                }
                bundle.properties.append(property_item)
                property_groups[(entity_id, predicate)].append(property_item)

    for (entity_id, property_name), items in property_groups.items():
        values = {item["value"] for item in items}
        if len(values) > 1:
            bundles[entity_id].conflicts.append(
                {
                    "property": property_name,
                    "values": sorted(values),
                    "sources": sorted({item["source_id"] for item in items}),
                }
            )

    return sorted(bundles.values(), key=lambda bundle: bundle.entity_id)
