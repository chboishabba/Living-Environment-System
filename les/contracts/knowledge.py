"""Regional, versioned ecological evidence catalogue contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class KnowledgeKind(str, Enum):
    FUNCTIONAL_TRAIT = "functional-trait"
    HOST_MYCORRHIZA_COMPATIBILITY = "host-mycorrhiza-compatibility"
    FLOWERING_CALENDAR = "flowering-calendar"
    POLLINATOR_RANGE = "pollinator-range"
    POLLINATOR_COMPETITION = "pollinator-competition"
    THREATENED_HABITAT_REQUIREMENT = "threatened-habitat-requirement"
    CROP_SUITABILITY = "crop-suitability"
    GRAZING_TOLERANCE = "grazing-tolerance"
    REMEDIATION_TRAIT = "remediation-trait"
    ENVIRONMENTAL_ENVELOPE = "environmental-envelope"
    INVASIVE_RISK = "invasive-risk"
    BIOSECURITY_RISK = "biosecurity-risk"


@dataclass(frozen=True)
class RegionContext:
    region_name: str
    jurisdiction: str
    climate_classification: str
    soil_classification: str
    bioregion: str
    custodians_or_communities: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceSource:
    citation_or_dataset: str
    version: str
    geographic_scope: str
    temporal_scope: str
    method_summary: str
    confidence_depth: int
    independently_reviewed: bool


@dataclass(frozen=True)
class KnowledgeEntry:
    entry_id: str
    kind: KnowledgeKind
    subject: str
    functional_groups: tuple[str, ...]
    region: RegionContext
    evidence: tuple[EvidenceSource, ...]
    valid_from: str
    reviewed_at: str
    version: str
    confidence_depth: int
    limitations: tuple[str, ...]
    active: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.entry_id:
            errors.append("knowledge entry id is required")
        if not self.evidence:
            errors.append(f"{self.entry_id}: at least one evidence source is required")
        if self.confidence_depth < 0:
            errors.append(f"{self.entry_id}: confidence depth cannot be negative")
        if not self.region.jurisdiction:
            errors.append(f"{self.entry_id}: jurisdiction is required")
        return errors


@dataclass(frozen=True)
class KnowledgeCatalogue:
    name: str
    version: str
    entries: tuple[KnowledgeEntry, ...]
    schema_reference: str
    provenance_manifest: tuple[str, ...]
    regional_fallback_policy: str
    update_policy: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        ids = [entry.entry_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            errors.append("duplicate knowledge entry ids")
        for entry in self.entries:
            errors.extend(entry.validate())
        if not self.provenance_manifest:
            errors.append("catalogue provenance manifest is required")
        return errors

    def query(
        self,
        kind: KnowledgeKind,
        subject: str,
        jurisdiction: str,
        minimum_confidence_depth: int = 0,
    ) -> tuple[KnowledgeEntry, ...]:
        """Return exact-jurisdiction entries only.

        Regional transfer is intentionally not implicit. Callers must create a
        separate geographic-transfer evidence object before using entries from
        another jurisdiction.
        """

        return tuple(
            entry
            for entry in self.entries
            if entry.active
            and entry.kind is kind
            and entry.subject == subject
            and entry.region.jurisdiction == jurisdiction
            and entry.confidence_depth >= minimum_confidence_depth
        )
