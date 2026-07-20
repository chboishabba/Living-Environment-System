"""Typed spatial and transport graph used by LES planning receipts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections import deque


class SpatialKind(str, Enum):
    RASTER_CELL = "raster-cell"
    PARCEL = "parcel"
    CATCHMENT = "catchment"
    WATERBODY = "waterbody"
    STREAM_REACH = "stream-reach"
    GROUNDWATER_ZONE = "groundwater-zone"
    ROAD_SEGMENT = "road-segment"
    HABITAT_PATCH = "habitat-patch"
    INTERVENTION_FOOTPRINT = "intervention-footprint"


class TransportKind(str, Enum):
    SURFACE_WATER = "surface-water"
    GROUNDWATER = "groundwater"
    SEDIMENT = "sediment"
    DISSOLVED_NITROGEN = "dissolved-nitrogen"
    DISSOLVED_PHOSPHORUS = "dissolved-phosphorus"
    POLLEN = "pollen"
    ANIMAL_MOVEMENT = "animal-movement"
    SEED_DISPERSAL = "seed-dispersal"
    MACHINERY_ACCESS = "machinery-access"
    HUMAN_ACCESS = "human-access"


@dataclass(frozen=True)
class SpatialNode:
    node_id: str
    kind: SpatialKind
    crs: str
    geometry_uri: str
    source_dataset: str


@dataclass(frozen=True)
class TimeWindow:
    start: int
    end: int

    def validate(self) -> list[str]:
        return [] if self.start <= self.end else ["time window start exceeds end"]

    def overlaps(self, other: "TimeWindow") -> bool:
        return self.start <= other.end and other.start <= self.end


@dataclass(frozen=True)
class TransportEdge:
    source_id: str
    target_id: str
    kind: TransportKind
    active_window: TimeWindow
    direction_verified: bool
    capacity_recorded: bool
    evidence_reference: str
    uncertainty_reference: str

    def validate(self, known_nodes: set[str]) -> list[str]:
        errors = self.active_window.validate()
        if self.source_id not in known_nodes:
            errors.append(f"unknown source node {self.source_id}")
        if self.target_id not in known_nodes:
            errors.append(f"unknown target node {self.target_id}")
        if not self.direction_verified:
            errors.append(f"{self.source_id}->{self.target_id}: direction not verified")
        if not self.evidence_reference:
            errors.append(f"{self.source_id}->{self.target_id}: evidence missing")
        return errors


@dataclass(frozen=True)
class SpatialTransportGraph:
    nodes: tuple[SpatialNode, ...]
    edges: tuple[TransportEdge, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        ids = [node.node_id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("duplicate spatial node ids")
        known = set(ids)
        for edge in self.edges:
            errors.extend(edge.validate(known))
        return errors

    def find_path(
        self,
        source_id: str,
        target_id: str,
        kind: TransportKind,
        window: TimeWindow,
    ) -> tuple[TransportEdge, ...] | None:
        """Find an auditable directed path in one transport medium."""

        adjacency: dict[str, list[TransportEdge]] = {}
        for edge in self.edges:
            if (
                edge.kind is kind
                and edge.direction_verified
                and edge.active_window.overlaps(window)
            ):
                adjacency.setdefault(edge.source_id, []).append(edge)

        queue: deque[tuple[str, tuple[TransportEdge, ...]]] = deque(
            [(source_id, ())]
        )
        visited = {source_id}
        while queue:
            node_id, path = queue.popleft()
            if node_id == target_id:
                return path
            for edge in adjacency.get(node_id, []):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, path + (edge,)))
        return None


@dataclass(frozen=True)
class MachineryProfile:
    name: str
    maximum_slope_percent: float
    turning_radius_m: float
    width_m: float
    wet_soil_access_allowed: bool
    fuel_model_reference: str


@dataclass(frozen=True)
class MachineryRouteAssessment:
    machine: MachineryProfile
    edge_ids: tuple[str, ...]
    slope_ok: bool
    turning_ok: bool
    width_ok: bool
    seasonal_access_ok: bool

    @property
    def feasible(self) -> bool:
        return self.slope_ok and self.turning_ok and self.width_ok and self.seasonal_access_ok
