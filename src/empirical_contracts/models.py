from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthorityLevel(str, Enum):
    L0_LEGACY_INHERITED = "L0"
    L1_NORMALIZED = "L1"
    L2_DERIVED = "L2"
    L3_REBUILT = "L3"
    L4_RESEARCH_VALIDATED = "L4"


class DataLayer(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    LEGACY_COMPAT = "legacy_compat"


class MeasurementStatus(str, Enum):
    OBSERVED = "observed"
    AGGREGATED_FROM_OBSERVED = "aggregated_from_observed"
    INTERPOLATED = "interpolated"
    FORWARD_FILLED = "forward_filled"
    BACKWARD_FILLED = "backward_filled"
    NEAREST_EPOCH = "nearest_epoch"
    STRUCTURAL_ZERO = "structural_zero"
    SOURCE_ABSENT = "source_absent"
    OUTSIDE_COVERAGE = "outside_coverage"
    UNKNOWN = "unknown"


class SourceFileRef(StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class SourceSnapshotRef(StrictModel):
    source: str
    release: str
    snapshot_id: str
    retrieved_at: datetime | None = None
    origin: str | None = None
    storage_mode: Literal["managed", "external_immutable"] = "external_immutable"
    files: tuple[SourceFileRef, ...]

    @field_validator("files")
    @classmethod
    def nonempty_files(cls, value: tuple[SourceFileRef, ...]):
        if not value:
            raise ValueError("a source snapshot must contain at least one file")
        return value


class GrainSpec(StrictModel):
    keys: tuple[str, ...]

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, value: tuple[str, ...]):
        if not value:
            raise ValueError("grain keys must be non-empty")
        if len(set(value)) != len(value):
            raise ValueError("grain keys must be unique")
        return value


class GeographySpec(StrictModel):
    provider: str
    version: str
    scheme: str
    level: str
    scheme_version: str | None = None

    @property
    def id(self) -> str:
        suffix = f":{self.scheme_version}" if self.scheme_version else ""
        return f"{self.provider}:{self.version}:{self.scheme}:{self.level}{suffix}"


class PeriodScheme(StrictModel):
    width_years: int = Field(gt=0)
    anchor_year: int
    calendar: Literal["gregorian_year"] = "gregorian_year"

    @property
    def id(self) -> str:
        return f"T{self.width_years}_y{self.anchor_year}"


class CoverageContract(StrictModel):
    geography_scope: str
    temporal_start: date | None = None
    temporal_end: date | None = None
    observation_semantics: str
    absent_row_semantics: Literal[
        "unknown", "zero_within_verified_coverage", "not_observed", "not_applicable"
    ] = "unknown"
    authority: AuthorityLevel
    basis: str

    @model_validator(mode="after")
    def dates_ordered(self):
        if self.temporal_start and self.temporal_end and self.temporal_end < self.temporal_start:
            raise ValueError("temporal_end must be >= temporal_start")
        return self


class DatasetRef(StrictModel):
    dataset_id: str
    version: str
    schema_version: str
    layer: DataLayer
    authority: AuthorityLevel
    grain: GrainSpec
    geography: GeographySpec | None = None
    period_scheme: PeriodScheme | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MeasurementContract(StrictModel):
    measure_id: str
    description: str
    source_dataset: DatasetRef
    output_grain: GrainSpec
    unit: str | None = None
    aggregation: str | None = None
    coverage: CoverageContract
    geography: GeographySpec | None = None
    period_scheme: PeriodScheme | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class QAResult(StrictModel):
    check_id: str
    state: Literal["GREEN", "YELLOW", "RED"]
    message: str
    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


class RunManifest(StrictModel):
    run_id: str
    package: str
    package_version: str
    code_commit: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    inputs: tuple[SourceSnapshotRef | DatasetRef, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    outputs: tuple[DatasetRef, ...] = ()
    qa: tuple[QAResult, ...] = ()

    @model_validator(mode="after")
    def finish_after_start(self):
        if self.finished_at and self.finished_at < self.started_at:
            raise ValueError("finished_at must be >= started_at")
        return self
